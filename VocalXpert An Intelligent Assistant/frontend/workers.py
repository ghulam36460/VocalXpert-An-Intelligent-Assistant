"""
Worker Threads for VocalXpert

Thread-safe background workers using Qt's QThread and signals.
Handles voice recognition, TTS, and AI processing.
"""

import sys
import os
import re
import logging
import json
from typing import Optional, Callable
from pathlib import Path
import time
import queue

from PySide6.QtCore import QThread, Signal, QObject, QTimer

# Import state machine for centralized state management
try:
    from modules.state_machine import (
        get_state_machine,
        AssistantState,
        StateEvent,
        CommandPipeline,
        CommandState,
        InvalidStateTransition,
    )

    STATE_MACHINE_AVAILABLE = True
except ImportError:
    STATE_MACHINE_AVAILABLE = False
    logger.warning("State machine module not available")

# Import speech recognition libraries
try:
    import speech_recognition as sr

    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    sr = None

# Import Vosk for offline speech recognition
try:
    from vosk import Model, KaldiRecognizer
    import pyaudio

    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

# Configure logging
logger = logging.getLogger("VocalXpert.Workers")

# Define project root for model loading
_project_root = Path(__file__).parent.parent

# Try to import advanced scraper module
try:
    from modules import advanced_scraper

    SCRAPER_AVAILABLE = True
except ImportError:
    try:
        import advanced_scraper

        SCRAPER_AVAILABLE = True
    except ImportError:
        SCRAPER_AVAILABLE = False


class VoiceRecognitionWorker(QThread):
    """
    Background thread for speech-to-text processing using Vosk (offline).

    Uses StateMachine to enforce valid state transitions:
    - IDLE -> LISTENING (on start)
    - LISTENING -> PROCESSING (on voice recognized)
    - LISTENING -> IDLE (on cancel/timeout)
    - LISTENING -> ERROR (on failure)

    Signals:
        status_changed: Emits status updates ("Listening...", "Processing...", etc.)
        result_ready: Emits transcribed text when complete
        error_occurred: Emits error message on failure
    """

    status_changed = Signal(str)
    result_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, timeout: int = 10, phrase_limit: int = 10):
        super().__init__()
        self.timeout = timeout
        self.phrase_limit = phrase_limit
        self._is_running = True
        self._vosk_model = None
        self._recognizer = None
        self._audio_stream = None
        self._audio = None
        self._state_machine = get_state_machine(
        ) if STATE_MACHINE_AVAILABLE else None

    def _init_vosk(self):
        """Initialize Vosk model and recognizer."""
        try:
            model_path = _project_root / "model"
            if not model_path.exists():
                raise Exception("Vosk model not found")

            logger.info("Loading Vosk model...")
            self._vosk_model = Model(str(model_path))

            logger.info("Creating Vosk recognizer...")
            self._recognizer = KaldiRecognizer(self._vosk_model, 16000)

            logger.info("Initializing PyAudio...")
            self._audio = pyaudio.PyAudio()

            logger.info("Opening audio stream...")
            self._audio_stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000,
            )

            # Ensure stream is started and active
            if not self._audio_stream.is_active():
                self._audio_stream.start_stream()

            logger.info("Vosk initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Vosk initialization failed: {e}")
            self._cleanup()
            return False

    def _cleanup(self):
        """Clean up audio resources."""
        try:
            if self._audio_stream:
                self._audio_stream.stop_stream()
                self._audio_stream.close()
                self._audio_stream = None
        except BaseException:
            pass

        try:
            if self._audio:
                self._audio.terminate()
                self._audio = None
        except BaseException:
            pass

    def run(self):
        """Execute speech recognition in background using Vosk."""
        logger.info("VoiceRecognitionWorker.run() started")

        if not VOSK_AVAILABLE:
            logger.error("Vosk not available")
            self.status_changed.emit(
                "❌ Offline speech recognition not available")
            self.error_occurred.emit("Vosk library not installed")
            return

        if not self._init_vosk():
            self.status_changed.emit(
                "❌ Could not initialize speech recognition")
            self.error_occurred.emit("Failed to load Vosk model")
            return

        try:
            # State machine: transition to LISTENING
            if self._state_machine and STATE_MACHINE_AVAILABLE:
                try:
                    self._state_machine.trigger(StateEvent.START_LISTENING)
                except InvalidStateTransition as e:
                    logger.warning(f"State transition blocked: {e}")
                    self.error_occurred.emit(
                        "Cannot start listening in current state")
                    return

            self.status_changed.emit("🎤 Listening...")
            logger.info("Starting voice recognition (Vosk offline)")

            start_time = time.time()
            recognized_text = ""

            while self._is_running and (time.time() -
                                        start_time) < self.timeout:
                # Check both running flag and stream validity before reading
                if not self._is_running or not self._audio_stream:
                    break

                try:
                    # Read audio data
                    data = self._audio_stream.read(2000,
                                                   exception_on_overflow=False)

                    # Process with Vosk
                    if self._recognizer.AcceptWaveform(data):
                        result = json.loads(self._recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            recognized_text = text
                            logger.info(f"Recognized: {text}")
                            break

                except OSError as e:
                    # Stream closed error (-9988) - exit gracefully
                    if e.errno == -9988 or "Stream closed" in str(e):
                        logger.debug(
                            "Audio stream closed, stopping recognition")
                        break
                    logger.warning(f"Audio I/O error: {e}")
                    if not self._is_running:
                        break
                    break  # Exit on OSError to prevent error flood
                except Exception as e:
                    logger.warning(f"Audio read error: {e}")
                    if not self._is_running:
                        break
                    continue

            # Get final result if any
            if not recognized_text:
                final_result = json.loads(self._recognizer.FinalResult())
                recognized_text = final_result.get("text", "").strip()

            if recognized_text and recognized_text.strip():
                # State machine: transition to PROCESSING
                if self._state_machine and STATE_MACHINE_AVAILABLE:
                    self._state_machine.try_trigger(
                        StateEvent.VOICE_RECOGNIZED, {
                            "text": recognized_text})
                self.result_ready.emit(recognized_text)
                self.status_changed.emit("✓ Ready")
                logger.info(f"Final result: {recognized_text}")
            else:
                # State machine: back to IDLE on no speech
                if self._state_machine and STATE_MACHINE_AVAILABLE:
                    self._state_machine.try_trigger(StateEvent.STOP_LISTENING)
                self.error_occurred.emit("empty")
                self.status_changed.emit("❓ No speech detected")
                logger.info("No speech detected")

        except Exception as e:
            # State machine: transition to ERROR
            if self._state_machine and STATE_MACHINE_AVAILABLE:
                self._state_machine.try_trigger(StateEvent.ERROR_OCCURRED,
                                                {"error": str(e)})
            logger.error(f"Voice recognition error: {e}")
            self.status_changed.emit("❌ Error occurred")
            self.error_occurred.emit(str(e))

        finally:
            self._cleanup()
            logger.info("VoiceRecognitionWorker exiting")

    def stop(self):
        """Stop the worker."""
        if not self._is_running:
            return  # Already stopped

        logger.info("Stopping voice recognition worker...")
        self._is_running = False

        # Give the loop a moment to detect the flag change
        time.sleep(0.05)

        # State machine: cancel listening
        if STATE_MACHINE_AVAILABLE:
            sm = get_state_machine()
            if sm.is_listening:
                sm.try_trigger(StateEvent.CANCEL)

        # Cleanup audio resources
        self._cleanup()


class TextToSpeechWorker(QThread):
    """
    Background thread for text-to-speech.
    Creates a fresh engine each time to avoid run loop issues.

    Uses StateMachine to enforce valid state transitions:
    - Any -> SPEAKING (on TTS start)
    - SPEAKING -> IDLE (on TTS finish)
    - SPEAKING -> LISTENING (in continuous mode)

    Signals:
        status_changed: Emits status updates
        finished: Emits when speech is complete
        error_occurred: Emits on error
    """

    status_changed = Signal(str)
    finished = Signal()
    error_occurred = Signal(str)

    def __init__(self, text: str, volume: float = 1.0):
        super().__init__()
        self.text = text
        self.volume = volume
        self._should_stop = False
        self._engine = None
        self._state_machine = get_state_machine(
        ) if STATE_MACHINE_AVAILABLE else None

    def run(self):
        """Execute text-to-speech in background."""
        try:
            if self._should_stop:
                self.finished.emit()
                return

            self.status_changed.emit("🔊 Speaking...")
            logger.info(f"TTS Speaking: {self.text[:50]}...")

            # State machine: transition to SPEAKING
            if self._state_machine and STATE_MACHINE_AVAILABLE:
                self._state_machine.try_trigger(StateEvent.TTS_STARTED)

            # Create a fresh engine for each speech to avoid run loop issues
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 175)
            self._engine.setProperty("volume", self.volume)

            if self._should_stop:
                self._cleanup_engine()
                self.finished.emit()
                return

            self._engine.say(self.text)
            self._engine.runAndWait()

            self._cleanup_engine()

            # State machine: transition from SPEAKING
            if self._state_machine and STATE_MACHINE_AVAILABLE:
                self._state_machine.try_trigger(StateEvent.TTS_FINISHED)

            if not self._should_stop:
                self.status_changed.emit("✓ Ready")

            self.finished.emit()

        except Exception as e:
            logger.error(f"TTS error: {e}")
            # State machine: transition to ERROR
            if self._state_machine and STATE_MACHINE_AVAILABLE:
                self._state_machine.try_trigger(StateEvent.ERROR_OCCURRED,
                                                {"error": str(e)})
            self._cleanup_engine()
            self.status_changed.emit("✓ Ready")
            self.error_occurred.emit(str(e))
            self.finished.emit()

    def _cleanup_engine(self):
        """Clean up the TTS engine."""
        try:
            if self._engine:
                self._engine.stop()
                self._engine = None
        except BaseException:
            self._engine = None

    def stop(self):
        """Stop speaking."""
        self._should_stop = True
        self._cleanup_engine()


class AIResponseWorker(QThread):
    """
    Background thread for AI/chat response generation.

    Signals:
        status_changed: Emits status updates
        response_ready: Emits AI response text
        error_occurred: Emits on error
    """

    status_changed = Signal(str)
    response_ready = Signal(str, bool)  # (response, is_ai_response)
    error_occurred = Signal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        """Get AI response in background."""
        try:
            self.status_changed.emit("🤖 Thinking...")
            logger.info(f"Processing query: {self.query}")

            # Import backend modules
            import sys
            import os

            sys.path.insert(
                0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            from modules import normal_chat

            response = normal_chat.reply(self.query)

            if response and response != "None":
                is_ai = (normal_chat.is_ai_online() if hasattr(
                    normal_chat, "is_ai_online") else False)
                self.response_ready.emit(response, is_ai)
                self.status_changed.emit("✓ Ready")
            else:
                self.response_ready.emit(
                    "I'm not sure how to respond to that.", False)
                self.status_changed.emit("✓ Ready")

        except Exception as e:
            logger.error(f"AI response error: {e}")
            self.status_changed.emit("❌ Error")
            self.error_occurred.emit(str(e))


class CommandWorker(QThread):
    """
    Background thread for executing system commands.

    Uses CommandPipeline state machine for processing stages:
    - RECEIVED -> PARSING: Command text received
    - PARSING -> OFFLINE_CHECK: Determine command type
    - OFFLINE_CHECK -> AI_ROUTING or EXECUTING: Check local sources
    - AI_ROUTING -> EXECUTING: AI parses command
    - EXECUTING -> COMPLETE: Action completed

    Signals:
        status_changed: Emits status updates
        result_ready: Emits command result (response_text, action_type)
        error_occurred: Emits on error
    """

    status_changed = Signal(str)
    result_ready = Signal(str, str)  # (response, action_type)
    open_game = Signal(str)  # Signal to open specific game UI
    error_occurred = Signal(str)

    def __init__(self, command: str, settings: dict = None):
        super().__init__()
        self.command = command.lower().strip()
        self.settings = settings or {}
        # Initialize command pipeline state machine
        self._pipeline = (CommandPipeline(self.command)
                          if STATE_MACHINE_AVAILABLE else None)
        self._state_machine = get_state_machine(
        ) if STATE_MACHINE_AVAILABLE else None

    def _complete_command(self, result: str, action_type: str):
        """
        Complete command processing with proper state transitions.

        Args:
            result: The response text to emit
            action_type: The type of action performed
        """
        # Pipeline: Complete the command
        if self._pipeline:
            self._pipeline.complete(result, action_type)
            logger.debug(
                f"Command pipeline completed in {self._pipeline.get_duration_ms():.2f}ms"
            )

        # Global state machine: Command complete
        if self._state_machine and STATE_MACHINE_AVAILABLE:
            self._state_machine.try_trigger(StateEvent.COMMAND_COMPLETE)

        self.result_ready.emit(result, action_type)
        self.status_changed.emit("✓ Ready")

    def _fail_command(self, error: str, action_type: str = "error"):
        """
        Handle command failure with proper state transitions.

        Args:
            error: The error message
            action_type: The type of action that failed
        """
        # Pipeline: Fail the command
        if self._pipeline:
            self._pipeline.fail(error)

        # Global state machine: Error occurred
        if self._state_machine and STATE_MACHINE_AVAILABLE:
            self._state_machine.try_trigger(StateEvent.ERROR_OCCURRED,
                                            {"error": error})
            # Try to recover immediately
            self._state_machine.try_trigger(StateEvent.ERROR_RECOVERED)

        self.result_ready.emit(error, action_type)
        self.status_changed.emit("✓ Ready")

    def _try_offline_first(self, cmd, exact_only=True):
        """
        OFFLINE-FIRST: Try to get response from offline sources before going online.

        Args:
            cmd: The command/query to search for
            exact_only: If True, only return exact matches (for online mode)
                       If False, also return fuzzy matches (for offline mode)

        Returns:
            tuple: (response, source, is_exact) or (None, None, False) if not found offline
        """
        try:
            from modules import normal_chat

            # Get the offline knowledge base
            offline_kb = normal_chat.get_offline_knowledge_base()

            # Search all offline sources with exact_only parameter
            response, source, is_exact = offline_kb.unified_search(
                cmd, exact_only=exact_only)

            if response:
                return response, source, is_exact
        except Exception as e:
            logger.warning(f"Offline search failed: {e}")

        return None, None, False

    def _try_ai_command_parsing(self, cmd):
        """Try to use AI to parse command and route to appropriate action."""
        try:
            # Import AI chat module
            from modules import ai_chat

            if ai_chat.is_online():
                # Get AI response with command routing
                ai_response, is_ai = ai_chat.get_ai_response(cmd)

                if is_ai and ai_response:
                    # Check if response contains command tags
                    import re

                    command_match = re.search(
                        r"\[COMMAND:([^]]+)\](.*?)\[/COMMAND\]",
                        ai_response,
                        re.IGNORECASE,
                    )

                    if command_match:
                        action = command_match.group(1).lower()
                        params = command_match.group(2).strip()

                        # Route to appropriate handler
                        return self._execute_ai_command(action, params,
                                                        ai_response)

                    # No command tag, but we have AI response - use it directly
                    self.result_ready.emit(ai_response, "ai_chat")
                    return True

        except Exception as e:
            logger.warning(f"AI command parsing failed: {e}")

        return False

    def _execute_ai_command(self, action, params, original_response):
        """Execute command based on AI-parsed action."""
        try:
            # System control
            if action == "open_app":
                from modules import app_control

                result = app_control.openApp(params)
                self.result_ready.emit(f"Opening {params}...", "system")
                return True

            elif action in ["volume_up", "volume_down", "volume_mute"]:
                from modules import app_control

                if action == "volume_up":
                    app_control.volumeUp()
                    self.result_ready.emit("Volume increased", "system")
                elif action == "volume_down":
                    app_control.volumeDown()
                    self.result_ready.emit("Volume decreased", "system")
                else:
                    app_control.volumeMute()
                    self.result_ready.emit("Volume muted", "system")
                return True

            elif action == "system_info":
                from modules import app_control

                result = app_control.OSHandler(params)
                if isinstance(result, list):
                    self.result_ready.emit("\n".join(result), "system")
                else:
                    self.result_ready.emit(result, "system")
                return True

            elif action in ["shutdown", "restart", "sleep", "lock_pc"]:
                from modules import app_control

                if action == "shutdown":
                    result = app_control.shutdown()
                elif action == "restart":
                    result = app_control.restart()
                elif action == "sleep":
                    result = app_control.sleep_pc()
                else:
                    result = app_control.lockPC()
                self.result_ready.emit(result, "system")
                return True

            # Web & Search
            elif action == "search":
                if not self.settings.get("web_scraping_enabled", True):
                    # If web scraping disabled, fallback to AI/local reply
                    try:
                        from modules import normal_chat

                        reply = normal_chat.reply(params)
                        self.result_ready.emit(
                            reply if reply else "I'm not sure.", "chat")
                        return True
                    except Exception:
                        self.result_ready.emit(
                            "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                        return True
                from modules import web_scrapping

                try:
                    results = web_scrapping.enhanced_google_search(
                        params, num_results=5)
                    if isinstance(results, list):
                        # Format a concise reply with title and link
                        lines = []
                        for i, r in enumerate(results[:5]):
                            title = r.get("title", "No title")
                            link = r.get("link", "")
                            lines.append(f"{i+1}. {title} - {link}")
                        reply = "Top search results:\n" + "\n".join(lines)
                        self.result_ready.emit(reply, "search")
                    else:
                        # Fallback: open browser and notify
                        web_scrapping.googleSearch(params)
                        self.result_ready.emit(str(results), "search")
                except Exception as e:
                    # On error, fall back to opening the browser search
                    try:
                        web_scrapping.googleSearch(params)
                    except BaseException:
                        pass
                    self.result_ready.emit("Opening search results...",
                                           "search")
                return True

            elif action == "open_website":
                from modules import app_control

                app_control.open_website(params)
                self.result_ready.emit("Opening website...", "web")
                return True

            elif action == "wikipedia":
                if not self.settings.get("web_scraping_enabled", True):
                    try:
                        from modules import normal_chat

                        reply = normal_chat.reply(params)
                        self.result_ready.emit(
                            (reply if reply else
                             "I couldn't fetch Wikipedia results right now."),
                            "wiki",
                        )
                        return True
                    except Exception:
                        self.result_ready.emit(
                            "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                        return True
                from modules import web_scrapping

                result = web_scrapping.wikiResult(params)
                self.result_ready.emit(result, "wiki")
                return True

            elif action == "youtube":
                if not self.settings.get("web_scraping_enabled", True):
                    try:
                        from modules import normal_chat

                        reply = normal_chat.reply(params)
                        self.result_ready.emit(
                            reply
                            if reply else "I can't access YouTube right now.",
                            "youtube",
                        )
                        return True
                    except Exception:
                        self.result_ready.emit(
                            "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                        return True
                from modules import web_scrapping

                video_name = (params.replace("play ",
                                             "").replace("on youtube",
                                                         "").strip())
                web_scrapping.playonYT(video_name)
                self.result_ready.emit(f"Playing {video_name} on YouTube...",
                                       "youtube")
                return True

            elif action == "weather":
                from modules import web_scrapping

                if not self.settings.get("web_scraping_enabled", True):
                    try:
                        from modules import normal_chat

                        reply = normal_chat.reply(params or
                                                  "what is the weather")
                        self.result_ready.emit(
                            reply
                            if reply else "I can't fetch weather right now.",
                            "weather",
                        )
                        return True
                    except Exception:
                        self.result_ready.emit(
                            "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                        return True
                data = web_scrapping.weather()
                self.result_ready.emit(data[-1], "weather")
                return True

            elif action == "news":
                if not self.settings.get("web_scraping_enabled", True):
                    try:
                        from modules import normal_chat

                        reply = normal_chat.reply("latest news")
                        self.result_ready.emit(
                            reply if reply else "I can't fetch news right now.", "news")
                        return True
                    except Exception:
                        self.result_ready.emit(
                            "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                        return True
                from modules import web_scrapping

                headlines, links = web_scrapping.latestNews()
                news_text = "Here are the latest headlines:\n" + "\n".join(
                    [f"• {n}" for n in headlines[:5]])
                self.result_ready.emit(news_text, "news")
                return True

            elif action == "maps":
                if not self.settings.get("web_scraping_enabled", True):
                    self.result_ready.emit(
                        "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                    return True
                from modules import web_scrapping

                web_scrapping.maps(params)
                self.result_ready.emit("Opening Google Maps...", "maps")
                return True

            elif action == "directions":
                if not self.settings.get("web_scraping_enabled", True):
                    self.result_ready.emit(
                        "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                    return True
                from modules import web_scrapping

                web_scrapping.giveDirections("current location", params)
                self.result_ready.emit("Opening directions in Google Maps...",
                                       "maps")
                return True

            elif action == "email":
                import webbrowser

                webbrowser.open("https://mail.google.com")
                self.result_ready.emit("Opening Gmail...", "email")
                return True

            # Productivity
            elif action == "calculate":
                from modules import math_function

                result = math_function.perform(params)
                self.result_ready.emit(f"The result is: {result}", "math")
                return True

            elif action == "timer":
                from modules import app_timer

                result = app_timer.startTimer(params)
                self.result_ready.emit(result, "timer")
                return True

            elif action in ["todo_add", "todo_show", "todo_remove"]:
                from modules import todo_handler

                if action == "todo_add":
                    result = todo_handler.toDoList(params)
                    self.result_ready.emit(result, "todo")
                elif action == "todo_show":
                    todos = todo_handler.showtoDoList()
                    if todos:
                        todo_text = "\n".join([f"• {t}" for t in todos])
                        self.result_ready.emit(todo_text, "todo")
                    else:
                        self.result_ready.emit("Your to-do list is empty!",
                                               "todo")
                else:
                    result = todo_handler.removeFromList(params)
                    self.result_ready.emit(result, "todo")
                return True

            elif action == "create_file":
                from modules import file_handler

                result = file_handler.createFile(params)
                self.result_ready.emit(result, "file")
                return True

            elif action == "create_project":
                from modules import file_handler

                result = file_handler.CreateHTMLProject(params)
                self.result_ready.emit(result, "file")
                return True

            # Games
            elif action in ["dice", "coin", "rps"]:
                from modules import game

                if action == "dice":
                    result_val, result_text = game.play("roll dice")
                elif action == "coin":
                    result_val, result_text = game.play("flip coin")
                else:
                    self.open_game.emit("rps")
                    self.result_ready.emit("Opening Rock Paper Scissors!",
                                           "game")
                    return True
                self.result_ready.emit(result_text, "game")
                return True

            elif action == "joke":
                from modules import web_scrapping

                joke = web_scrapping.jokes()
                self.result_ready.emit(joke, "joke")
                return True

            # Information
            elif action == "time":
                from modules.normal_chat import DateTime

                dt = DateTime()
                self.result_ready.emit(
                    f"The current time is {dt.currentTime()}", "time")
                return True

            elif action == "date":
                from modules.normal_chat import DateTime

                dt = DateTime()
                self.result_ready.emit(f"Today is {dt.currentDate()}", "date")
                return True

            elif action == "dictionary":
                from modules import dictionary

                result = dictionary.translate(params)
                response = (f"{result[0]}\n{result[1]}" if isinstance(
                    result, list) else str(result))
                self.result_ready.emit(response, "dictionary")
                return True

            elif action == "translate":
                from modules import normal_chat

                result = normal_chat.lang_translate(params,
                                                    "es")  # Default to Spanish
                self.result_ready.emit(str(result), "translate")
                return True

            # If action not recognized, fall back to AI response
            self.result_ready.emit(
                original_response.replace(
                    f"[COMMAND:{action}]{params}[/COMMAND]", "").strip(),
                "ai_chat",
            )
            return True

        except Exception as e:
            logger.error(f"AI command execution failed: {e}")
            return False

    def run(self):
        """Process command in background with OFFLINE-FIRST approach using state machine."""
        try:
            self.status_changed.emit("⚙️ Processing...")

            # State machine: Start processing
            if self._state_machine and STATE_MACHINE_AVAILABLE:
                self._state_machine.try_trigger(StateEvent.SUBMIT_TEXT,
                                                {"command": self.command})

            # Pipeline: Move to PARSING state
            if self._pipeline:
                self._pipeline.transition(CommandState.PARSING)

            cmd_lower = self.command.lower()

            # ================================================================
            # STEP 1: Handle explicit web scraper commands (always online)
            # ================================================================
            if SCRAPER_AVAILABLE and (cmd_lower.startswith("web scrapper") or
                                      cmd_lower.startswith("web scraper")):
                try:
                    if self._pipeline:
                        self._pipeline.transition(CommandState.EXECUTING)
                    from modules import normal_chat

                    result = normal_chat.handle_web_scraping_command(
                        self.command)
                    self._complete_command(result, "web_scraping")
                    return
                except Exception as e:
                    self.result_ready.emit(f"Web scraping failed: {str(e)}",
                                           "error")
                    self.status_changed.emit("✓ Ready")
                    return

            # ================================================================
            # STEP 2: OFFLINE-FIRST with EXACT MATCH logic
            # ================================================================

            # Check if this is a simple query that can be answered offline
            is_system_command = any(word in cmd_lower for word in [
                "open ",
                "launch ",
                "start ",
                "volume",
                "screenshot",
                "shutdown",
                "restart",
                "sleep",
                "lock",
            ])

            # Check internet connectivity
            from modules import ai_chat

            is_online = ai_chat.is_online()

            # For non-system commands, try offline sources first
            if not is_system_command:
                # ONLINE MODE: Only use exact matches from offline
                # OFFLINE MODE: Use both exact and fuzzy matches
                exact_only = is_online  # True when online, False when offline
                offline_response, offline_source, is_exact = self._try_offline_first(
                    self.command, exact_only=exact_only)

                if offline_response:
                    if is_online and is_exact:
                        # Online + Exact match → Use offline response (no emoji
                        # to avoid encoding issues)
                        self.result_ready.emit(offline_response, "offline")
                        self.status_changed.emit("Ready (offline exact match)")
                        logger.info(
                            f"Exact offline response from {offline_source}")
                        return
                    elif not is_online:
                        # Offline mode → Use any match (exact or fuzzy)
                        match_type = "exact" if is_exact else "fuzzy"
                        self.result_ready.emit(offline_response, "offline")
                        self.status_changed.emit(
                            f"Ready (offline {match_type})")
                        logger.info(
                            f"Offline {match_type} response from {offline_source}"
                        )
                        return

            # ================================================================
            # STEP 3: Try AI command parsing (online) for commands
            # ================================================================
            ai_command_result = self._try_ai_command_parsing(self.command)
            if ai_command_result:
                self.status_changed.emit("✓ Ready")
                return

            # ================================================================
            # STEP 4: Fallback to traditional keyword matching
            # ================================================================
            cmd = self.command

            # Weather
            if "weather" in cmd:
                try:
                    from modules import web_scrapping

                    data = web_scrapping.weather()
                    self.result_ready.emit(data[-1], "weather")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not fetch weather: {str(e)[:30]}", "error")
                self.status_changed.emit("✓ Ready")
                return

            # Time
            if "time" in cmd:
                from modules.normal_chat import DateTime

                dt = DateTime()
                self.result_ready.emit(
                    f"The current time is {dt.currentTime()}", "time")
                return

            # Date
            if any(word in cmd for word in ["date", "today", "day"]):
                from modules.normal_chat import DateTime

                dt = DateTime()
                self.result_ready.emit(f"Today is {dt.currentDate()}", "date")
                return

            # Wikipedia
            if "wikipedia" in cmd or "wiki" in cmd:
                from modules import web_scrapping

                result = web_scrapping.wikiResult(cmd)
                self.result_ready.emit(result, "wiki")
                return

            # Games
            if any(word in cmd for word in ["game", "play"]):
                if any(word in cmd
                       for word in ["rock", "paper", "scissor", "rps"]):
                    self.open_game.emit("rps")
                    self.result_ready.emit("Opening Rock Paper Scissors!",
                                           "game")
                elif any(word in cmd for word in ["dice", "roll"]):
                    from modules import game

                    result_val, result_text = game.play(cmd)
                    self.result_ready.emit(result_text, "game")
                elif any(word in cmd for word in ["coin", "flip", "toss"]):
                    from modules import game

                    result_val, result_text = game.play(cmd)
                    self.result_ready.emit(result_text, "game")
                else:
                    self.result_ready.emit(
                        "Available games: Rock Paper Scissors, Dice Roll, Coin Flip", "game", )
                return

            # Search
            if "search" in cmd:
                if not self.settings.get("web_scraping_enabled", True):
                    self.result_ready.emit(
                        "Web scraping mode is disabled. Enable it in Settings > Web Features.", "error", )
                    return
                from modules import web_scrapping

                try:
                    results = web_scrapping.enhanced_google_search(
                        cmd, num_results=5)
                    if isinstance(results, list):
                        lines = []
                        for i, r in enumerate(results[:5]):
                            title = r.get("title", "No title")
                            link = r.get("link", "")
                            lines.append(f"{i+1}. {title} - {link}")
                        reply = "Top search results:\n" + "\n".join(lines)
                        self.result_ready.emit(reply, "search")
                    else:
                        web_scrapping.googleSearch(cmd)
                        self.result_ready.emit(str(results), "search")
                except Exception as e:
                    try:
                        web_scrapping.googleSearch(cmd)
                    except BaseException:
                        pass
                    self.result_ready.emit("Opening search results...",
                                           "search")
                return

            # News
            if "news" in cmd:
                from modules import web_scrapping

                headlines, links = web_scrapping.latestNews()
                news_text = "Here are the latest headlines:\n" + "\n".join(
                    [f"• {n}" for n in headlines[:5]])
                self.result_ready.emit(news_text, "news")
                return

            # Calculator / Math
            if any(
                word in cmd for word in [
                    "calculate",
                    "math",
                    "plus",
                    "minus",
                    "multiply",
                    "divide"]):
                from modules import math_function

                result = math_function.perform(cmd)
                self.result_ready.emit(f"The result is: {result}", "math")
                return

            # System commands
            if any(word in cmd for word in ["open", "launch", "start"]):
                from modules import app_control

                # Extract app name
                for prefix in ["open", "launch", "start"]:
                    if prefix in cmd:
                        app_name = cmd.replace(prefix, "").strip()
                        break

                # If command includes writing text, handle combined action
                try:
                    import re

                    write_match = None
                    if " and write " in app_name:
                        parts = app_name.split(" and write ", 1)
                        app_name = parts[0].strip()
                        write_text = parts[1].strip().strip("\"'")
                        write_match = write_text
                    elif " write " in app_name:
                        parts = app_name.split(" write ", 1)
                        app_name = parts[0].strip()
                        write_text = parts[1].strip().strip("\"'")
                        write_match = write_text

                    result = app_control.openApp(app_name)
                    if write_match:
                        # Small delay might be necessary in real runs; we just
                        # call helper
                        resp = app_control.write_text(write_text)
                        self.result_ready.emit(
                            f"Opened {app_name} and typed your text.", "system")
                    else:
                        self.result_ready.emit(f"Opening {app_name}...",
                                               "system")
                except Exception as e:
                    self.result_ready.emit(f"Opening {app_name}...", "system")
                return

            # Volume control
            if "volume" in cmd:
                from modules import app_control

                if "up" in cmd or "increase" in cmd:
                    app_control.volumeUp()
                    self.result_ready.emit("Volume increased", "system")
                elif "down" in cmd or "decrease" in cmd:
                    app_control.volumeDown()
                    self.result_ready.emit("Volume decreased", "system")
                elif "mute" in cmd:
                    app_control.volumeMute()
                    self.result_ready.emit("Volume muted", "system")
                return

            # Screenshot
            if "screenshot" in cmd:
                from modules import app_control

                app_control.screenshot()
                self.result_ready.emit("Screenshot captured!", "system")
                return

            # Dictionary
            if "dictionary" in cmd or "meaning of" in cmd or "definition" in cmd:
                try:
                    from modules import dictionary

                    result = dictionary.translate(cmd)
                    response = (f"{result[0]}\n{result[1]}" if isinstance(
                        result, list) else str(result))
                    self.result_ready.emit(response, "dictionary")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not get definition: {str(e)[:30]}", "error")
                return

            # File creation
            if "create file" in cmd or "new file" in cmd or "make file" in cmd:
                try:
                    from modules import file_handler

                    result = file_handler.createFile(cmd)
                    self.result_ready.emit(result, "file")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not create file: {str(e)[:30]}", "error")
                return

            # HTML Project
            if "create project" in cmd or "html project" in cmd or "web project" in cmd:
                try:
                    from modules import file_handler

                    result = file_handler.CreateHTMLProject("NewProject")
                    self.result_ready.emit(result, "file")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not create project: {str(e)[:30]}", "error")
                return

            # System info
            if "system info" in cmd or "specs" in cmd or "specification" in cmd:
                from modules import app_control

                result = app_control.OSHandler(cmd)
                if isinstance(result, list):
                    self.result_ready.emit("\n".join(result), "system")
                else:
                    self.result_ready.emit(result, "system")
                return

            # Battery
            if "battery" in cmd:
                from modules import app_control

                result = app_control.batteryInfo()
                self.result_ready.emit(result, "system")
                return

            # Lock PC
            if "lock" in cmd and ("pc" in cmd or "computer" in cmd):
                from modules import app_control

                result = app_control.lockPC()
                self.result_ready.emit(result, "system")
                return

            # Shutdown/Restart/Sleep
            if "shutdown" in cmd:
                from modules import app_control

                result = app_control.shutdown()
                self.result_ready.emit(result, "system")
                return

            if "restart" in cmd:
                from modules import app_control

                result = app_control.restart()
                self.result_ready.emit(result, "system")
                return

            if "sleep" in cmd:
                from modules import app_control

                result = app_control.sleep_pc()
                self.result_ready.emit(result, "system")
                return

            # Translation
            if "translate" in cmd:
                try:
                    from modules import normal_chat

                    # Extract language and text from command
                    result = normal_chat.lang_translate(
                        cmd, "es")  # Default to Spanish
                    self.result_ready.emit(str(result), "translate")
                except Exception as e:
                    self.result_ready.emit(
                        f"Translation failed: {str(e)[:30]}", "error")
                return

            # Maps/Directions
            if "map" in cmd or "direction" in cmd:
                try:
                    from modules import web_scrapping

                    if "direction" in cmd:
                        # Try to extract start and end points
                        web_scrapping.giveDirections(
                            "current location",
                            cmd.replace("direction", "").replace("to",
                                                                 "").strip(),
                        )
                        self.result_ready.emit(
                            "Opening directions in Google Maps...", "maps")
                    else:
                        web_scrapping.maps(cmd)
                        self.result_ready.emit(
                            "Opening Google Maps...", "maps")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not open maps: {str(e)[:30]}", "error")
                return

            # Jokes
            if "joke" in cmd:
                try:
                    from modules import web_scrapping

                    joke = web_scrapping.jokes()
                    self.result_ready.emit(joke, "joke")
                except Exception as e:
                    self.result_ready.emit(
                        "Why did the programmer quit? Because he didn't get arrays! 😄", "joke", )
                return

            # YouTube
            if "youtube" in cmd or "play video" in cmd:
                try:
                    from modules import web_scrapping

                    video_name = (cmd.replace("youtube", "").replace(
                        "play video", "").replace("play", "").strip())
                    web_scrapping.playonYT(video_name)
                    self.result_ready.emit(
                        f"Playing {video_name} on YouTube...", "youtube")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not open YouTube: {str(e)[:30]}", "error")
                return

            # Timer
            if "timer" in cmd or "remind" in cmd or "alarm" in cmd:
                try:
                    from modules import app_timer

                    # startTimer expects a query string like "set timer 5
                    # minutes"
                    result = app_timer.startTimer(cmd)
                    self.result_ready.emit(result, "timer")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not set timer: {str(e)[:50]}", "error")
                return

            # Todo List operations
            if "todo" in cmd or "task" in cmd:
                try:
                    from modules import todo_handler

                    if any(word in cmd for word in ["add", "create", "new"]):
                        # Extract task text after the action word
                        task_text = cmd
                        for word in ["add", "create", "new", "todo", "task"]:
                            task_text = task_text.replace(word, "").strip()
                        result = todo_handler.toDoList(
                            task_text if task_text else "New task")
                        self.result_ready.emit(result, "todo")
                    elif any(word in cmd
                             for word in ["show", "list", "view", "get"]):
                        todos = todo_handler.showtoDoList()
                        if todos:
                            todo_text = "\n".join([f"• {t}" for t in todos])
                            self.result_ready.emit(todo_text, "todo")
                        else:
                            self.result_ready.emit("Your to-do list is empty!",
                                                   "todo")
                    elif any(word in cmd for word in
                             ["delete", "remove", "done", "complete", "clear"]):
                        if "clear" in cmd or "all" in cmd:
                            result = todo_handler.clearToDoList()
                            self.result_ready.emit(result, "todo")
                        else:
                            # Remove by text match
                            remove_text = cmd
                            for word in [
                                    "delete",
                                    "remove",
                                    "done",
                                    "complete",
                                    "todo",
                                    "task",
                                    "from list",
                            ]:
                                remove_text = remove_text.replace(word,
                                                                  "").strip()
                            result = todo_handler.removeFromList(remove_text)
                            self.result_ready.emit(result, "todo")
                    else:
                        # Default: show todos
                        todos = todo_handler.showtoDoList()
                        if todos:
                            todo_text = "\n".join([f"• {t}" for t in todos])
                            self.result_ready.emit(todo_text, "todo")
                        else:
                            self.result_ready.emit("Your to-do list is empty!",
                                                   "todo")
                except Exception as e:
                    self.result_ready.emit(f"Todo error: {str(e)[:50]}",
                                           "error")
                return

            # Email (open email client)
            if "email" in cmd or "mail" in cmd:
                try:
                    import webbrowser

                    webbrowser.open("https://mail.google.com")
                    self.result_ready.emit("Opening Gmail...", "email")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not open email: {str(e)[:30]}", "error")
                return

            # Website opening
            if ("website" in cmd or "open" in cmd and any(
                    site in cmd for site in
                    ["google", "youtube", "facebook", "twitter", "github"])):
                try:
                    from modules import app_control

                    app_control.open_website(cmd)
                    self.result_ready.emit("Opening website...", "web")
                except Exception as e:
                    self.result_ready.emit(
                        f"Could not open website: {str(e)[:30]}", "error")
                return

            # Default: Use AI chat
            if self._pipeline:
                self._pipeline.transition(CommandState.AI_ROUTING)
            from modules import normal_chat

            response = normal_chat.reply(cmd)
            if response and response != "None":
                self._complete_command(response, "chat")
            else:
                self._complete_command(
                    "I'm not sure how to help with that. Try asking me about weather, time, or to play a game!",
                    "chat",
                )

        except Exception as e:
            logger.error(f"Command processing error: {e}")
            self._fail_command(str(e))


class ContinuousVoiceWorker(QObject):
    """
    Manages continuous voice listening mode.
    Restarts voice recognition after each command.
    """

    status_changed = Signal(str)
    result_ready = Signal(str)
    stopped = Signal()

    def __init__(self):
        super().__init__()
        self._is_active = False
        self._current_worker: Optional[VoiceRecognitionWorker] = None
        self._waiting_for_tts = False

    def start_listening(self):
        """Start continuous listening mode."""
        self._is_active = True
        self._waiting_for_tts = False
        logger.info("ContinuousVoiceWorker: Starting listening mode")
        self._start_recognition()

    def stop_listening(self):
        """Stop continuous listening mode."""
        logger.info("ContinuousVoiceWorker: Stopping listening mode")
        self._is_active = False
        self._waiting_for_tts = False
        if self._current_worker:
            logger.info("Stopping current voice recognition worker...")
            try:
                # Disconnect signals first to prevent callbacks during shutdown
                self._current_worker.status_changed.disconnect()
                self._current_worker.result_ready.disconnect()
                self._current_worker.error_occurred.disconnect()
                self._current_worker.finished.disconnect()
            except (RuntimeError, TypeError):
                pass

            self._current_worker.stop()
            # Wait for the worker to finish
            if self._current_worker.isRunning():
                if not self._current_worker.wait(2000):  # Wait up to 2 seconds
                    logger.warning(
                        "Voice recognition worker didn't stop gracefully")
                    self._current_worker.terminate()
            self._current_worker.deleteLater()
            self._current_worker = None
        self.stopped.emit()

    def on_tts_finished(self):
        """Called when TTS finishes speaking - restart voice recognition."""
        logger.info(
            f"ContinuousVoiceWorker: TTS finished, active={self._is_active}")
        self._waiting_for_tts = False
        if self._is_active:
            logger.info(
                "ContinuousVoiceWorker: Restarting recognition after TTS")
            QTimer.singleShot(500,
                              self._start_recognition)  # Small delay after TTS

    def _start_recognition(self):
        """Start a new recognition cycle."""
        if not self._is_active or self._waiting_for_tts:
            logger.debug(
                f"_start_recognition skipped: active={self._is_active}, waiting_for_tts={self._waiting_for_tts}"
            )
            return

        # Clean up previous worker if it exists
        if self._current_worker:
            try:
                # Disconnect old signals to prevent duplicate connections
                self._current_worker.status_changed.disconnect()
                self._current_worker.result_ready.disconnect()
                self._current_worker.error_occurred.disconnect()
                self._current_worker.finished.disconnect()
            except (RuntimeError, TypeError):
                pass  # Signals may already be disconnected

            # Wait for old worker to finish if still running
            if self._current_worker.isRunning():
                self._current_worker.stop()
                self._current_worker.wait(1000)
            self._current_worker.deleteLater()
            self._current_worker = None

        logger.info("Starting new voice recognition cycle")
        self._current_worker = VoiceRecognitionWorker()
        self._current_worker.status_changed.connect(self.status_changed)
        self._current_worker.result_ready.connect(self._on_result)
        self._current_worker.error_occurred.connect(self._on_error)
        self._current_worker.finished.connect(self._on_finished)
        self._current_worker.start()

    def _on_result(self, text: str):
        """Handle recognition result."""
        logger.info(f"ContinuousVoiceWorker got result: {text}")
        self.result_ready.emit(text)
        # After getting a result, wait for TTS to finish before restarting
        self._waiting_for_tts = True

    def _on_error(self, error: str):
        """Handle recognition error - restart if still active."""
        logger.debug(
            f"ContinuousVoiceWorker error: {error}, active={self._is_active}")
        # Restart for both timeout and empty (no speech detected) errors
        if self._is_active and error in ("timeout", "empty"):
            QTimer.singleShot(500, self._start_recognition)

    def _on_finished(self):
        """Handle recognition finished - restart if still active and not waiting for TTS."""
        logger.debug(
            f"ContinuousVoiceWorker finished: active={self._is_active}, waiting_for_tts={self._waiting_for_tts}"
        )
        if self._is_active and not self._waiting_for_tts:
            QTimer.singleShot(1000, self._start_recognition)
