"""
GUI Assistant Module - Main Chat Interface

Provides the main Tkinter-based graphical interface for VocalXpert.
Handles voice recognition input, text-to-speech output, and all
user interactions including:
    - Voice and text command processing
    - Chat display with scrollable history
    - Theme switching (light/dark mode)
    - Integration with all feature modules

Dependencies:
    - pyttsx3: Text-to-speech engine
    - speech_recognition: Voice input processing
    - Custom modules: normal_chat, math_function, web_scrapping, etc.
"""

####################################### IMPORTING MODULES ################
import sys
import os

sys.path.append(os.path.dirname(__file__))

try:
    import dictionary
    import todo_handler
    import file_handler
    import ai_chat
    import normal_chat
    import app_control
    import app_timer
    import game
    import web_scrapping
    import math_function
    from user_handler import UserData
    from face_unlocker import clickPhoto, viewPhoto
    from dotenv import load_dotenv

    load_dotenv()
except Exception as e:
    # Fail fast so the user knows which dependency is missing
    raise e

# System Modules
try:
    import os
    import pyttsx3
    import speech_recognition as sr
    from tkinter import *  # noqa: F401,F403 - Tkinter classes used throughout
    from tkinter import ttk, messagebox, colorchooser
    from PIL import Image, ImageTk, ImageDraw
    from time import sleep, strftime
    from threading import Thread
    import queue
    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("vocalxpert.log"),
            logging.StreamHandler()
        ],
    )
    logger = logging.getLogger("VocalXpert")
    try:
        import playsound

        SOUND_ENABLED = True
    except BaseException:
        SOUND_ENABLED = False
except Exception as e:
    print(e)

# Sound effects utility
SOUND_FILES = {
    "coin": "assets/audios/coin.mp3",
    "dice": "assets/audios/dice.mp3",
    "photo": "assets/audios/photoclick.mp3",
    "suspense": "assets/audios/suspense.mp3",
    "timer": "assets/audios/Timer.mp3",
    "wow": "assets/audios/wow.mp3",
}


def play_sound(sound_name):
    """Play a sound effect in background thread"""
    if SOUND_ENABLED and sound_name in SOUND_FILES:
        try:
            Thread(target=lambda: playsound.playsound(SOUND_FILES[sound_name]),
                   daemon=True).start()
        except BaseException:
            pass


# Accent palette
ACCENT_PRIMARY = "#6366f1"
BTN_PRIMARY_HOVER = "#4f46e5"
ACCENT_SUCCESS = "#22d3ee"
ACCENT_DANGER = "#ef4444"
ACCENT_INFO = "#38bdf8"
ACCENT_SECONDARY = "#10b981"

# Theme presets for dark/light modes
DARK_THEME = {
    "background": "#0b1120",
    "chatBgColor": "#020617",
    "textColor": "#f8fafc",
    "AITaskStatusLblBG": "#111827",
    "SURFACE_DARK": "#111827",
    "SURFACE_LIGHT": "#1f2937",
    "TEXT_SECONDARY": "#e2e8f0",
    "TEXT_MUTED": "#94a3b8",
    "botChatTextBg": "#4f46e5",
    "botChatText": "white",
    "userChatTextBg": "#22d3ee",
    "header_bg": "#1e293b",
    "features_btn_bg": "#243045",
    "features_btn_fg": "#e2e8f0",
    "qa_bg": "#1e293b",
    "qa_btn_bg": "#334155",
    "qa_btn_fg": "#e2e8f0",
    "qa_btn_active_bg": "#475569",
    "qa_btn_active_fg": "#ffffff",
    "send_btn_bg": ACCENT_PRIMARY,
    "send_btn_fg": "white",
    "mic_btn_bg": "#111827",
    "placeholder_fg": "#94a3b8",
}

LIGHT_THEME = {
    "background": "#f8fafc",
    "chatBgColor": "#f1f5f9",
    "textColor": "#0f172a",
    "AITaskStatusLblBG": "#e2e8f0",
    "SURFACE_DARK": "#e2e8f0",
    "SURFACE_LIGHT": "#ffffff",
    "TEXT_SECONDARY": "#1e293b",
    "TEXT_MUTED": "#475569",
    "botChatTextBg": "#6366f1",
    "botChatText": "white",
    "userChatTextBg": "#22d3ee",
    "header_bg": "#e2e8f0",
    "features_btn_bg": "#e2e8f0",
    "features_btn_fg": "#0f172a",
    "qa_bg": "#e2e8f0",
    "qa_btn_bg": "#cbd5f5",
    "qa_btn_fg": "#0f172a",
    "qa_btn_active_bg": "#94a3eb",
    "qa_btn_active_fg": "#0f172a",
    "send_btn_bg": ACCENT_PRIMARY,
    "send_btn_fg": "white",
    "mic_btn_bg": "#e2e8f0",
    "placeholder_fg": "#64748b",
}

# Active theme (defaults to dark)
ACTIVE_THEME = DARK_THEME.copy()

# Background Colors - Deep navy palette (defaults, overridden by theme)
GRADIENT_START = "#020617"
GRADIENT_END = "#0f172a"
background = ACTIVE_THEME["background"]
chatBgColor = ACTIVE_THEME["chatBgColor"]
AITaskStatusLblBG = ACTIVE_THEME["AITaskStatusLblBG"]
SURFACE_DARK = ACTIVE_THEME["SURFACE_DARK"]
SURFACE_LIGHT = ACTIVE_THEME["SURFACE_LIGHT"]

# Text Colors - Hierarchy for readability
textColor = ACTIVE_THEME["textColor"]
TEXT_SECONDARY = ACTIVE_THEME["TEXT_SECONDARY"]
TEXT_MUTED = ACTIVE_THEME["TEXT_MUTED"]

# Chat Bubble Colors
botChatTextBg = ACTIVE_THEME["botChatTextBg"]
botChatText = ACTIVE_THEME["botChatText"]
userChatTextBg = ACTIVE_THEME["userChatTextBg"]

# Legacy compatibility
BUTTON_HOVER = BTN_PRIMARY_HOVER

# UI State
KCS_IMG = 1  # 0 for light, 1 for dark
voice_id = 0  # 0 for female, 1 for male
ass_volume = 1.0  # max volume
ass_voiceRate = 200  # normal voice rate
placeholder_active = True
feature_panel = None
feature_panel_visible = False
feature_cards = []
quick_action_buttons = []
qa_canvas = None
qa_inner = None
UI_ELEMENTS = {}

# Thread-safe UI communication queue
ui_queue = queue.Queue()

# Exit commands for voice loop
EXIT_COMMANDS = [
    "exit",
    "quit",
    "bye",
    "goodbye",
    "close",
    "shut down",
    "shutdown",
    "stop",
    "end",
]

# AI name for logging
ai_name = "VocalXpert"


def safe_ui_update(func):
    """Schedule UI update on main thread - THREAD SAFE."""
    root = UI_ELEMENTS.get("root")
    if root:
        root.after(0, func)
    else:
        func()


def process_ui_queue():
    """Process pending UI updates from queue."""
    try:
        while True:
            func = ui_queue.get_nowait()
            func()
    except queue.Empty:
        pass
    finally:
        root = UI_ELEMENTS.get("root")
        if root:
            root.after(100, process_ui_queue)


# AI Status
AI_ONLINE = False

# Feature discovery data
FEATURE_ITEMS = [
    {
        "icon": "🌤️",
        "title": "Weather",
        "description": "Get the latest weather update",
        "command": "weather",
    },
    {
        "icon": "🔍",
        "title": "Search",
        "description": "Search anything on the web",
        "command": "search ",
    },
    {
        "icon": "🎮",
        "title": "Games",
        "description": "Play dice, toss a coin, or more",
        "command": "games",
    },
    {
        "icon": "📧",
        "title": "Email",
        "description": "Send an email using your voice",
        "command": "send email",
    },
    {
        "icon": "📝",
        "title": "To-Do List",
        "description": "Add or review your task list",
        "command": "show my list",
    },
    {
        "icon": "🕒",
        "title": "Set Timer",
        "description": "Start a countdown timer hands-free",
        "command": "set a timer for ",
    },
    {
        "icon": "📸",
        "title": "Screenshot",
        "description": "Capture your current screen",
        "command": "screenshot",
    },
    {
        "icon": "📰",
        "title": "News",
        "description": "Hear today's top headlines",
        "command": "news",
    },
]

########################################## LOGIN CHECK ###################

try:
    user = UserData()
    user.extractData()
    ownerName = user.getName().split()[0]
    ownerDesignation = "Sir"
    if user.getGender() == "Female":
        ownerDesignation = "Ma'am"
    ownerPhoto = user.getUserPhoto()
except Exception as e:
    print(
        "You're not Registered Yet !\nRun SECURITY.py file to register your face."
    )
    raise SystemExit

######################################### SETTINGS HANDLERS ##############


def apply_theme_from_state():
    """Refresh global color variables from the active theme selection."""
    global ACTIVE_THEME, background, chatBgColor, textColor, TEXT_SECONDARY, TEXT_MUTED
    global AITaskStatusLblBG, SURFACE_DARK, SURFACE_LIGHT, botChatTextBg, botChatText, userChatTextBg
    if KCS_IMG == 1:
        theme = DARK_THEME
    else:
        theme = LIGHT_THEME
    ACTIVE_THEME = theme.copy()
    background = theme["background"]
    chatBgColor = theme["chatBgColor"]
    textColor = theme["textColor"]
    TEXT_SECONDARY = theme["TEXT_SECONDARY"]
    TEXT_MUTED = theme["TEXT_MUTED"]
    AITaskStatusLblBG = theme["AITaskStatusLblBG"]
    SURFACE_DARK = theme["SURFACE_DARK"]
    SURFACE_LIGHT = theme["SURFACE_LIGHT"]
    botChatTextBg = theme["botChatTextBg"]
    botChatText = theme["botChatText"]
    userChatTextBg = theme["userChatTextBg"]


def refresh_theme_widgets():
    """Apply the active theme colors to existing widgets."""
    theme = ACTIVE_THEME

    def cfg(widget, **kwargs):
        if widget is not None:
            widget.configure(**kwargs)

    cfg(UI_ELEMENTS.get("root"), bg=background)
    cfg(UI_ELEMENTS.get("root1"), bg=chatBgColor)
    cfg(UI_ELEMENTS.get("root2"), bg=background)
    cfg(UI_ELEMENTS.get("root3"), bg=background)
    cfg(UI_ELEMENTS.get("chat_frame"), bg=chatBgColor)
    cfg(UI_ELEMENTS.get("chat_canvas"), bg=chatBgColor)
    cfg(UI_ELEMENTS.get("chat_container"), bg=chatBgColor)
    if UI_ELEMENTS.get("header_frame") is not None:
        UI_ELEMENTS["header_frame"].configure(bg=theme["header_bg"])
        cfg(UI_ELEMENTS.get("app_name_lbl"),
            bg=theme["header_bg"],
            fg=textColor)
        cfg(UI_ELEMENTS.get("ai_status_frame"), bg=theme["header_bg"])
        cfg(UI_ELEMENTS.get("ai_dot"), bg=theme["header_bg"])
        cfg(UI_ELEMENTS.get("ai_status_text"),
            bg=theme["header_bg"],
            fg=TEXT_MUTED)
    if UI_ELEMENTS.get("features_btn") is not None:
        UI_ELEMENTS["features_btn"].configure(
            bg=theme["features_btn_bg"],
            fg=theme["features_btn_fg"],
            activebackground=theme["features_btn_bg"],
            activeforeground=textColor,
        )
    if UI_ELEMENTS.get("quick_actions_frame") is not None:
        UI_ELEMENTS["quick_actions_frame"].configure(bg=theme["qa_bg"])
    if qa_canvas is not None:
        qa_canvas.configure(bg=theme["qa_bg"])
    if qa_inner is not None:
        qa_inner.configure(bg=theme["qa_bg"])
    for btn in quick_action_buttons:
        btn.configure(
            bg=theme["qa_btn_bg"],
            fg=theme["qa_btn_fg"],
            activebackground=theme["qa_btn_active_bg"],
            activeforeground=theme["qa_btn_active_fg"],
        )
    if feature_panel is not None:
        feature_panel.configure(bg=background)
    refresh_feature_panel_theme()
    if UI_ELEMENTS.get("bottomFrame1") is not None:
        UI_ELEMENTS["bottomFrame1"].configure(bg=SURFACE_DARK)
        cfg(UI_ELEMENTS.get("VoiceModeFrame"), bg=SURFACE_DARK)
        cfg(UI_ELEMENTS.get("TextModeFrame"), bg=SURFACE_DARK)
        cbl_widget = UI_ELEMENTS.get("cbl")
        if cbl_widget is not None:
            image_ref = (globals().get("cblDarkImg")
                         if KCS_IMG == 1 else globals().get("cblLightImg"))
            if image_ref is not None:
                cbl_widget.configure(bg=SURFACE_DARK, image=image_ref)
                cbl_widget.image = image_ref
        setting_widget = UI_ELEMENTS.get("settingBtn")
        if setting_widget is not None:
            setting_image = (globals().get("sphDark")
                             if KCS_IMG == 1 else globals().get("sphLight"))
            setting_widget.configure(bg=SURFACE_DARK,
                                     activebackground=SURFACE_LIGHT)
            if setting_image is not None:
                setting_widget.configure(image=setting_image)
                setting_widget.image = setting_image
        kb_widget = UI_ELEMENTS.get("kbBtn")
        if kb_widget is not None:
            kb_image = (globals().get("kbphDark")
                        if KCS_IMG == 1 else globals().get("kbphLight"))
            kb_widget.configure(
                bg=SURFACE_DARK,
                activebackground=SURFACE_LIGHT)
            if kb_image is not None:
                kb_widget.configure(image=kb_image)
                kb_widget.image = kb_image
        cfg(
            UI_ELEMENTS.get("micBtn"),
            bg=theme["mic_btn_bg"],
            activebackground=SURFACE_LIGHT,
        )
        cfg(UI_ELEMENTS.get("AITaskStatusLbl"),
            bg=AITaskStatusLblBG,
            fg=textColor)
    if UI_ELEMENTS.get("input_container") is not None:
        UI_ELEMENTS["input_container"].configure(bg=SURFACE_LIGHT)
        cfg(UI_ELEMENTS.get("input_hint"), bg=SURFACE_DARK, fg=TEXT_MUTED)
        if UI_ELEMENTS.get("UserField") is not None:
            UI_ELEMENTS["UserField"].configure(bg=SURFACE_LIGHT,
                                               insertbackground=ACCENT_PRIMARY)
            if placeholder_active:
                UI_ELEMENTS["UserField"].configure(fg=theme["placeholder_fg"])
            else:
                UI_ELEMENTS["UserField"].configure(fg=textColor)
        cfg(
            UI_ELEMENTS.get("sendBtn"),
            bg=theme["send_btn_bg"],
            fg=theme["send_btn_fg"],
            activebackground=BTN_PRIMARY_HOVER,
            activeforeground="white",
        )
    if UI_ELEMENTS.get("settingsFrame") is not None:
        settings_widgets = [
            "settingsFrame",
            "settingsLbl",
            "userPhoto",
            "userName",
            "assLbl",
            "voiceRateLbl",
            "volumeLbl",
            "themeLbl",
            "chooseChatLbl",
        ]
        for key in settings_widgets:
            widget = UI_ELEMENTS.get(key)
            if widget is not None:
                fg = (textColor if key in {
                    "settingsLbl",
                    "userName",
                    "assLbl",
                    "voiceRateLbl",
                    "volumeLbl",
                    "themeLbl",
                    "chooseChatLbl",
                } else None)
                cfg(widget, bg=background, fg=fg)
        cfg(
            UI_ELEMENTS.get("volumeBar"),
            bg=background,
            fg=textColor,
            highlightbackground=background,
        )
        cfg(UI_ELEMENTS.get("colorbar"), bg=chatBgColor)


def ChangeSettings(write=False):
    """Persist or load assistant settings such as theme, voice, and volume."""
    import pickle

    global KCS_IMG, background, chatBgColor, textColor, AITaskStatusLblBG
    global SURFACE_DARK, SURFACE_LIGHT, botChatTextBg, botChatText, userChatTextBg
    settings_path = "userData/settings.pck"
    data = {
        "background": background,
        "textColor": textColor,
        "chatBgColor": chatBgColor,
        "AITaskStatusLblBG": AITaskStatusLblBG,
        "KCS_IMG": KCS_IMG,
        "botChatText": botChatText,
        "botChatTextBg": botChatTextBg,
        "userChatTextBg": userChatTextBg,
        "voice_id": voice_id,
        "ass_volume": ass_volume,
        "ass_voiceRate": ass_voiceRate,
    }
    if write:
        with open(settings_path, "wb") as file:
            pickle.dump(data, file)
        return
    try:
        with open(settings_path, "rb") as file:
            loadSettings = pickle.load(file)
            KCS_IMG = loadSettings.get("KCS_IMG", KCS_IMG)
            voice_state = loadSettings.get("voice_id", voice_id)
            volume_state = loadSettings.get("ass_volume", ass_volume)
            rate_state = loadSettings.get("ass_voiceRate", ass_voiceRate)
            globals()["voice_id"] = voice_state
            globals()["ass_volume"] = volume_state
            globals()["ass_voiceRate"] = rate_state
    except Exception:
        # Defaults already applied
        pass
    finally:
        apply_theme_from_state()
        # Widget update occurs later once UI is available


def changeTheme():
    """Trigger theme update when user toggles the radio button."""
    global KCS_IMG
    if themeValue.get() == 1:
        KCS_IMG = 1
    else:
        KCS_IMG = 0
    apply_theme_from_state()
    refresh_theme_widgets()
    ChangeSettings(True)


def changeVoice(event=None):
    """Switch between male and female assistant voices."""
    global voice_id
    try:
        voice_id = 0 if assVoiceOption.get() == "Female" else 1
        engine.setProperty("voice", voices[voice_id].id)
        ChangeSettings(True)
    except Exception as e:
        print(e)


def changeVolume(event=None):
    """Adjust assistant speaking volume from slider."""
    global ass_volume
    try:
        ass_volume = volumeBar.get() / 100
        engine.setProperty("volume", ass_volume)
        ChangeSettings(True)
    except Exception as e:
        print(e)


def changeVoiceRate(event=None):
    """Update speaking rate based on dropdown selection."""
    global ass_voiceRate
    rate_map = {
        "Very Low": 100,
        "Low": 150,
        "Normal": 200,
        "Fast": 250,
        "Very Fast": 300,
    }
    selected = voiceOption.get()
    ass_voiceRate = rate_map.get(selected, 200)
    try:
        engine.setProperty("rate", ass_voiceRate)
        ChangeSettings(True)
    except Exception as e:
        print(e)


if not os.path.exists("userData/settings.pck"):
    ChangeSettings(True)

ChangeSettings()

############################################ SET UP VOICE ################

try:
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[voice_id].id)
    engine.setProperty("volume", ass_volume)
    engine.setProperty("rate", ass_voiceRate)
except Exception as e:
    print(e)
    engine = None
    voices = []

####################################### SPEECH UTILITIES #################


def speak(text, display=False, icon=False):
    """Convert text to speech and optionally render it in the chat window.
    Thread-safe: UI updates scheduled on main thread.
    """
    if text is None:
        return

    def update_status(status_text):
        """Update status label safely."""
        lbl = UI_ELEMENTS.get("AITaskStatusLbl")
        if lbl:
            lbl["text"] = status_text

    def show_bot_message():
        """Display bot icon and message in chat."""
        chat = UI_ELEMENTS.get("chat_frame")
        if chat:
            if icon:
                Label(chat, image=botIcon, bg=chatBgColor).pack(anchor="w",
                                                                pady=0)
            if display:
                attachTOframe(text, True)

    try:
        # Update UI safely from any thread
        safe_ui_update(lambda: update_status("  Speaking..."))
        safe_ui_update(show_bot_message)

        # Log to console
        print(f"\n{ai_name.upper()}: {text}")
        logger.info(f"Speaking: {text[:50]}..." if len(text) >
                    50 else f"Speaking: {text}")

        # Speak (this blocks, but that's OK for TTS)
        if engine is not None:
            engine.say(text)
            engine.runAndWait()

    except Exception as e:
        print(f"TTS error: {e}")
        logger.error(f"TTS error: {e}")
    finally:
        safe_ui_update(lambda: update_status("  Ready"))


def record(clearChat=True, iconDisplay=True):
    """Capture microphone input and transcribe using Google's speech API.

    Features:
    - Timeout to prevent infinite hangs
    - Thread-safe UI updates
    - Proper error handling with user feedback

    Returns:
            str: Transcribed text (lowercase) or 'None' on failure
    """
    print("\nListening...")
    logger.info("Starting voice recording...")

    def update_status(text):
        lbl = UI_ELEMENTS.get("AITaskStatusLbl")
        if lbl:
            lbl["text"] = text

    safe_ui_update(lambda: update_status("  Listening..."))

    r = sr.Recognizer()
    r.dynamic_energy_threshold = True  # Auto-adjust for noise

    try:
        with sr.Microphone() as source:
            # Calibrate for ambient noise
            r.adjust_for_ambient_noise(source, duration=0.5)

            # Listen with TIMEOUT to prevent infinite hang
            audio = r.listen(
                source,
                timeout=10,  # Max wait for speech to start
                phrase_time_limit=10,  # Max duration of speech
            )

            safe_ui_update(lambda: update_status("  Processing..."))

            # Transcribe using Google
            said = r.recognize_google(audio)
            print(f"\nUser said: {said}")
            logger.info(f"Recognized: {said}")

            # Update chat UI safely
            if clearChat:
                safe_ui_update(clearChatScreen)

            if iconDisplay and UI_ELEMENTS.get("chat_frame"):

                def show_user_message():
                    chat = UI_ELEMENTS.get("chat_frame")
                    if chat:
                        Label(chat, image=userIcon,
                              bg=chatBgColor).pack(anchor="e", pady=0)
                        attachTOframe(said)

                safe_ui_update(show_user_message)

            return said.lower()

    except sr.WaitTimeoutError:
        print("Listening timed out - no speech detected")
        logger.warning("Voice timeout - no speech detected")
        safe_ui_update(lambda: update_status("  Ready"))
        return "None"

    except sr.UnknownValueError:
        print("Could not understand audio")
        logger.warning("Could not understand audio")
        safe_ui_update(lambda: update_status("  Ready"))
        return "None"

    except sr.RequestError as e:
        print(f"Google API error: {e}")
        logger.error(f"Speech API error: {e}")
        safe_ui_update(
            lambda: speak("Your system appears to be offline...", True, True))
        return "None"

    except Exception as e:
        print(f"Record error: {e}")
        logger.error(f"Record error: {e}")
        safe_ui_update(lambda: update_status("  Ready"))
        return "None"


def voiceMedium():
    """Continuous voice interaction loop for microphone mode.
    Runs in background thread, uses safe UI updates.
    """
    print("Voice mode started...")
    logger.info("Voice mode loop started")

    while True:
        try:
            query = record()

            if query == "None":
                continue

            # Check for exit commands
            if isContain(query, EXIT_COMMANDS):
                logger.info(f"Exit command received: {query}")
                safe_ui_update(lambda: speak(
                    f"Shutting down the System. Good Bye {ownerDesignation}!",
                    True,
                    True,
                ))
                break

            # Process command in separate thread to keep loop responsive
            Thread(target=lambda q=query: process_input(q.lower()),
                   daemon=True).start()

        except Exception as e:
            print(f"Voice loop error: {e}")
            logger.error(f"Voice loop error: {e}")
            continue

    # Close app safely
    logger.info("Voice mode loop ended, closing app")
    safe_ui_update(lambda: app_control.Win_Opt("close"))


def on_entry_focus_in(event=None):
    """Clear placeholder when the entry gains focus."""
    global placeholder_active
    if UI_ELEMENTS.get("UserField") is None:
        return
    entry = UI_ELEMENTS["UserField"]
    if placeholder_active:
        entry.delete(0, END)
        entry.configure(fg=textColor)
        placeholder_active = False


def on_entry_focus_out(event=None):
    """Restore placeholder text when the entry is empty."""
    global placeholder_active
    if UI_ELEMENTS.get("UserField") is None:
        return
    entry = UI_ELEMENTS["UserField"]
    if entry.get().strip() == "":
        placeholder_active = True
        entry.delete(0, END)
        entry.insert(0, "Ask me anything...")
        entry.configure(fg=ACTIVE_THEME["placeholder_fg"])


def keyboardInput(event=None):
    """Handle text submissions from the input field."""
    global placeholder_active
    if UI_ELEMENTS.get("UserField") is None:
        return
    entry = UI_ELEMENTS["UserField"]
    user_input = entry.get().strip()
    if not user_input or placeholder_active:
        return
    entry.delete(0, END)
    placeholder_active = True
    entry.insert(0, "Ask me anything...")
    entry.configure(fg=ACTIVE_THEME["placeholder_fg"])
    clearChatScreen()
    if UI_ELEMENTS.get("chat_frame") is not None:
        Label(UI_ELEMENTS["chat_frame"], image=userIcon,
              bg=chatBgColor).pack(anchor="e", pady=0)
        attachTOframe(user_input)
    if isContain(user_input.lower(), EXIT_COMMANDS):
        speak("Shutting down the System. Good Bye " + ownerDesignation + "!",
              True, True)
        if UI_ELEMENTS.get("root") is not None:
            UI_ELEMENTS["root"].after(500, UI_ELEMENTS["root"].destroy)
    else:
        Thread(target=process_input, args=(user_input.lower(),)).start()
    if feature_panel_visible:
        toggle_feature_panel(force_hide=True)


def main(text):
    try:
        AITaskStatusLbl["text"] = "  Processing..."
        AITaskStatusLbl["fg"] = ACCENT_INFO
    except BaseException:
        pass

    try:
        if "project" in text and isContain(text, ["make", "create"]):
            speak("What do you want to give the project name ?", True, True)
            projectName = record(False, False)
            if projectName != "None":
                speak(file_handler.CreateHTMLProject(projectName.capitalize()),
                      True)
            return

        if "create" in text and "file" in text:
            speak(file_handler.createFile(text), True, True)
            return

        if "translate" in text:
            speak("What do you want to translate?", True, True)
            sentence = record(False, False)
            speak("Which langauage to translate ?", True)
            langauage = record(False, False)
            result = normal_chat.lang_translate(sentence, langauage)
            if result == "None":
                speak("This language doesn't exist", True, True)
            else:
                speak(f"In {langauage.capitalize()} you would say:", True)
                if langauage == "hindi":
                    attachTOframe(result.text, True)
                    speak(result.pronunciation)
                else:
                    speak(result.text, True)
            return

        if "list" in text:
            if isContain(text, ["add", "create", "make"]):
                speak("What do you want to add?", True, True)
                item = record(False, False)
                if item != "None":
                    todo_handler.toDoList(item)
                    speak("Alright, I added that to your list.", True, True)
                return
            if isContain(text, ["show", "my list"]):
                items = todo_handler.showtoDoList()
                if len(items) == 1:
                    speak(items[0], True, True)
                else:
                    attachTOframe("\n".join(items), True)
                    speak(items[0])
                return

        if isContain(text, ["battery", "system info"]):
            result = app_control.OSHandler(text)
            if isinstance(result, (list, tuple)) and len(result) == 2:
                speak(result[0], True, True)
                attachTOframe(result[1], True)
            else:
                speak(result, True, True)
            return

        if isContain(text, ["meaning", "dictionary", "definition", "define"]):
            definition = dictionary.translate(text)
            speak(definition[0], True, True)
            if definition[1]:
                speak(definition[1], True)
            return

        if "selfie" in text or ("click" in text and "photo" in text):
            speak("Sure " + ownerDesignation + "...", True, True)
            clickPhoto()
            speak("Do you want to view your clicked photo?", True)
            query = record(False)
            if isContain(query, ["yes", "sure", "yeah", "show me"]):
                Thread(target=viewPhoto).start()
                speak("Ok, here you go...", True, True)
            else:
                speak("No Problem " + ownerDesignation, True, True)
            return

        if "volume" in text:
            app_control.volumeControl(text)
            Label(chat_frame, image=botIcon, bg=chatBgColor).pack(anchor="w",
                                                                  pady=0)
            attachTOframe("Volume settings updated.", True)
            return

        if isContain(text, ["timer", "countdown"]):
            Thread(target=app_timer.startTimer, args=(text,)).start()
            speak("Timer started!", True, True)
            return

        if "whatsapp" in text:
            speak("Sure " + ownerDesignation + "...", True, True)
            speak("Whom do you want to send the message?", True)
            WAEMPOPUP("WhatsApp", "Phone Number")
            attachTOframe(rec_phoneno)
            speak("What is the message?", True)
            message = record(False, False)
            Thread(
                target=web_scrapping.sendWhatsapp,
                args=(
                    rec_phoneno,
                    message,
                ),
            ).start()
            speak("Message is on the way. Do not move away from the screen.")
            attachTOframe("Message Sent", True)
            return

        if "email" in text:
            speak("Whom do you want to send the email?", True, True)
            WAEMPOPUP("Email", "E-mail Address")
            attachTOframe(rec_email)
            speak("What is the Subject?", True)
            subject = record(False, False)
            speak("What message you want to send ?", True)
            message = record(False, False)
            Thread(
                target=web_scrapping.email,
                args=(
                    rec_email,
                    message,
                    subject,
                ),
            ).start()
            speak("Email has been Sent", True)
            return

        if isContain(text, ["youtube", "video"]):
            speak("Ok " + ownerDesignation + ", here is a video for you...",
                  True, True)
            try:
                speak(web_scrapping.youtube(text), True)
            except Exception as e:
                print(e)
                speak("Desired result not found", True)
            return

        if isContain(text, ["search", "image"]):
            if "image" in text and "show" in text:
                Thread(target=showImages, args=(text,)).start()
                speak("Here are the images...", True, True)
                return
            speak(web_scrapping.googleSearch(text), True, True)
            return

        if isContain(text, ["map", "direction"]):
            if "direction" in text:
                speak("What is your starting location?", True, True)
                startingPoint = record(False, False)
                speak("Ok " + ownerDesignation + ", Where you want to go?",
                      True)
                destinationPoint = record(False, False)
                speak("Ok " + ownerDesignation + ", Getting Directions...",
                      True)
                try:
                    distance = web_scrapping.giveDirections(
                        startingPoint, destinationPoint)
                    speak("You have to cover a distance of " + distance, True)
                except BaseException:
                    speak("I think the location is not proper, try again!",
                          True, True)
            else:
                web_scrapping.maps(text)
                speak("Here you go...", True, True)
            return

        if isContain(
                text,
            [
                "factorial",
                "log",
                "value of",
                "math",
                " + ",
                " - ",
                " x ",
                "multiply",
                "divided by",
                "binary",
                "hexadecimal",
                "octal",
                "shift",
                "sin ",
                "cos ",
                "tan ",
            ],
        ):
            try:
                speak("Result is: " + math_function.perform(text), True, True)
            except Exception as e:
                print(f"Math error: {e}")
            return

        if "joke" in text:
            speak("Here is a joke...", True, True)
            speak(web_scrapping.jokes(), True)
            return

        if isContain(text, ["news"]):
            speak("Getting the latest news...", True, True)
            headlines, headlineLinks = web_scrapping.latestNews(2)
            for head in headlines:
                speak(head, True)
            speak("Do you want to read the full news?", True)
            followup = record(False, False)
            if isContain(followup, ["no", "don't"]):
                speak("No problem " + ownerDesignation, True)
            else:
                speak("Ok " + ownerDesignation + ", opening browser...", True)
                web_scrapping.openWebsite(
                    "https://indianexpress.com/latest-news/")
                speak("You can now read the full news from this website.")
            return

        if isContain(text, ["weather"]):
            data = web_scrapping.weather()
            speak("", False, True)
            showSingleImage("weather", data[:-1])
            speak(data[-1])
            return

        if isContain(text, ["screenshot"]):
            Thread(target=app_control.Win_Opt, args=("screenshot",)).start()
            speak("Screenshot taken", True, True)
            return

        if isContain(text, ["window", "close that"]):
            app_control.Win_Opt(text)
            return

        if isContain(text, ["tab"]):
            app_control.Tab_Opt(text)
            return

        if isContain(text, ["setting"]):
            raise_frame(root2)
            clearChatScreen()
            return

        if isContain(
                text,
            [
                "open",
                "launch",
                "type",
                "save",
                "delete",
                "select",
                "press enter",
                "open site",
                "start",
                "run",
            ],
        ):
            speak("Working on it...", True, True)
            try:
                result = app_control.System_Opt(text)
                if result:
                    speak(str(result), True)
            except Exception as e:
                speak("Could not complete that action. Try again.", True, True)
                print(f"App control error: {e}")
            return

        if isContain(text, ["wiki", "who is"]):
            Thread(
                target=web_scrapping.downloadImage,
                args=(
                    text,
                    1,
                ),
            ).start()
            speak("Searching...", True, True)
            result = web_scrapping.wikiResult(text)
            showSingleImage("wiki")
            speak(result, True)
            return

        if isContain(text, ["game", "games"]):
            speak("Which game do you want to play?", True, True)
            attachTOframe(game.show_games(), True)
            choice = record(False)
            if choice == "None":
                speak("Didn't understand what you said?", True, True)
                return
            if "online" in choice:
                speak(
                    "Ok " +
                    ownerDesignation +
                    ", let's play some online games",
                    True,
                    True,
                )
                web_scrapping.openWebsite(
                    "https://www.agame.com/games/mini-games/")
                return
            if isContain(choice, ["don't", "no", "cancel", "back", "never"]):
                speak(
                    "No problem " + ownerDesignation +
                    ", we'll play next time.",
                    True,
                    True,
                )
            else:
                result_val, result_text = game.play(choice)
                speak(result_text, True, True)
            return

        if isContain(text, ["coin", "dice", "die", "roll", "flip", "toss"]):
            speak("Ok " + ownerDesignation, True, True)
            result_val, result_text = game.play(text)
            if result_val:
                if "head" in result_val.lower():
                    showSingleImage("head")
                elif "tail" in result_val.lower():
                    showSingleImage("tail")
                elif result_val.isdigit():
                    showSingleImage(result_val)
            speak(result_text, True)
            return

        if isContain(text, ["rock paper", "paper scissors", "rps"]):
            speak("Opening Rock Paper Scissors game!", True, True)
            game.play(text)
            return

        if isContain(text, ["time", "date"]):
            speak(normal_chat.chat(text), True, True)
            return

        if "my name" in text:
            speak("Your name is, " + ownerName, True, True)
            return

        if isContain(text, ["voice"]):
            global voice_id
            try:
                if "female" in text:
                    voice_id = 0
                elif "male" in text:
                    voice_id = 1
                else:
                    voice_id = 1 - voice_id
                engine.setProperty("voice", voices[voice_id].id)
                ChangeSettings(True)
                speak(
                    "Hello " + ownerDesignation +
                    ", I have changed my voice. How may I help you?",
                    True,
                    True,
                )
                assVoiceOption.current(voice_id)
            except Exception as e:
                print(e)
            return

        if isContain(text, ["morning", "evening", "noon"]) and "good" in text:
            speak(normal_chat.chat("good"), True, True)
            return

        result = normal_chat.reply(text)
        if result != "None":
            speak(result, True, True)
            return

        speak(
            "I don't know anything about this. Do you want to search it on web?",
            True,
            True,
        )
        response = record(False, True)
        if isContain(response, ["no", "don't"]):
            speak("Ok " + ownerDesignation, True)
        else:
            speak("Here's what I found on the web... ", True, True)
            web_scrapping.googleSearch(text)
    finally:
        try:
            if chatMode == 1:
                AITaskStatusLbl["text"] = "  Listening..."
                AITaskStatusLbl["fg"] = ACCENT_INFO
            else:
                AITaskStatusLbl["text"] = "  Ready"
                AITaskStatusLbl["fg"] = TEXT_SECONDARY
        except BaseException:
            pass
    if UserField.get() == "":
        UserField.insert(0, "Ask me anything...")
        placeholder_color = "#64748b" if KCS_IMG == 0 else "#94a3b8"
        UserField.config(fg=placeholder_color)
        placeholder_active = True


def process_input(text):
    """Process input and schedule GUI updates on main thread"""
    try:
        main(text)
    except Exception as e:
        print(f"Error processing input: {e}")


def ensure_text_mode():
    if chatMode == 1:
        changeChatMode()
    UserField.focus_set()


def prepare_text_command(command_text, auto_send=False):
    global placeholder_active
    ensure_text_mode()
    UserField.delete(0, END)
    UserField.insert(0, command_text)
    UserField.config(fg=textColor)
    placeholder_active = False
    if auto_send:
        keyboardInput()


def feature_card_click(command_text):
    prepare_text_command(command_text)
    if feature_panel is not None:
        toggle_feature_panel(force_hide=True)


def toggle_feature_panel(force_hide=False):
    global feature_panel_visible
    if feature_panel is None:
        return
    if feature_panel_visible or force_hide:
        feature_panel.pack_forget()
        feature_panel_visible = False
        if features_btn is not None:
            features_btn.config(text="Features ▾")
    else:
        feature_panel.pack(fill=X, padx=12, pady=(4, 10))
        feature_panel_visible = True
        if features_btn is not None:
            features_btn.config(text="Features ▴")


def build_feature_panel(parent):
    global feature_panel
    feature_panel = Frame(parent, bg=background)
    cols = 2
    for idx, item in enumerate(FEATURE_ITEMS):
        card = Frame(
            feature_panel,
            bg=SURFACE_DARK,
            highlightbackground="#1f2937",
            highlightthickness=1,
            bd=0,
            cursor="hand2",
        )
        card.grid(row=idx // cols,
                  column=idx % cols,
                  padx=6,
                  pady=6,
                  sticky="nsew")
        card.columnconfigure(0, weight=1)
        icon_lbl = Label(
            card,
            text=item["icon"],
            font=("Segoe UI Emoji", 20),
            bg=SURFACE_DARK,
            fg=textColor,
        )
        icon_lbl.pack(pady=(10, 2))
        title_lbl = Label(
            card,
            text=item["title"],
            font=("Segoe UI", 12, "bold"),
            bg=SURFACE_DARK,
            fg=textColor,
        )
        title_lbl.pack()
        desc_lbl = Label(
            card,
            text=item["description"],
            font=("Segoe UI", 10),
            bg=SURFACE_DARK,
            fg=TEXT_MUTED,
            wraplength=150,
            justify="center",
        )
        desc_lbl.pack(padx=12, pady=(2, 12))
        for widget in (card, icon_lbl, title_lbl, desc_lbl):
            widget.bind("<Button-1>",
                        lambda e, cmd=item["command"]: feature_card_click(cmd))

    for col in range(cols):
        feature_panel.columnconfigure(col, weight=1)
    refresh_feature_panel_theme()


def refresh_feature_panel_theme():
    if feature_panel is None:
        return
    panel_bg = background if KCS_IMG == 1 else "#f8fafc"
    card_bg = SURFACE_DARK if KCS_IMG == 1 else "#ffffff"
    border_color = "#1f2937" if KCS_IMG == 1 else "#cbd5f5"
    primary_fg = textColor if KCS_IMG == 1 else "#0f172a"
    desc_fg = TEXT_MUTED if KCS_IMG == 1 else "#475569"
    feature_panel.configure(bg=panel_bg)
    for card in feature_panel.winfo_children():
        card.configure(bg=card_bg, highlightbackground=border_color)
        children = card.winfo_children()
        for idx, child in enumerate(children):
            if idx < 2:
                child.configure(bg=card_bg, fg=primary_fg)
            else:
                child.configure(bg=card_bg, fg=desc_fg)


###################################### TASK/COMMAND HANDLER ##############
def isContain(txt, lst):
    for word in lst:
        if word in txt:
            return True
    return False


##################################### DELETE USER ACCOUNT ################
def deleteUserData():
    result = messagebox.askquestion(
        "Alert", "Are you sure you want to delete your Face Data ?")
    if result == "no":
        return
    messagebox.showinfo(
        "Clear Face Data",
        "Your face has been cleared\nRegister your face again to use.",
    )
    import shutil

    shutil.rmtree("userData")
    root.destroy()

    #####################
    ####### GUI #########
    #####################


############ HELPER: CREATE ROUNDED RECTANGLE IMAGE ###########
def create_rounded_rectangle(width, height, radius, color):
    """Create a rounded rectangle image for chat bubbles"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Convert hex color to RGB
    if color.startswith("#"):
        color = color.lstrip("#")
        color_rgb = tuple(int(color[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    else:
        color_rgb = (99, 102, 241, 255)  # Default indigo

    # Draw rounded rectangle
    draw.rounded_rectangle([(0, 0), (width - 1, height - 1)],
                           radius=radius,
                           fill=color_rgb)
    return ImageTk.PhotoImage(img)


############ ATTACHING BOT/USER CHAT ON CHAT SCREEN ###########
# Store references to prevent garbage collection
chat_images = []


def attachTOframe(text, bot=False):
    global chat_images
    if bot:
        # Bot message with modern styling and timestamp
        msg_container = Frame(chat_frame, bg=chatBgColor)
        msg_container.pack(anchor="w", pady=6, padx=8)

        # Message bubble with gradient effect
        msg_frame = Frame(msg_container, bg=botChatTextBg, padx=2, pady=2)
        msg_frame.pack()

        botchat = Label(
            msg_frame,
            text=text,
            bg=botChatTextBg,
            fg=botChatText,
            justify=LEFT,
            wraplength=280,
            font=("Segoe UI", 11),
            padx=14,
            pady=10,
        )
        botchat.pack()

        # Add timestamp
        timestamp = Label(
            msg_container,
            text=strftime("%I:%M %p"),
            bg=chatBgColor,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        )
        timestamp.pack(anchor="w", pady=(2, 0))
    else:
        # User message with modern styling
        msg_container = Frame(chat_frame, bg=chatBgColor)
        msg_container.pack(anchor="e", pady=6, padx=8)

        # Message bubble
        msg_frame = Frame(msg_container, bg=userChatTextBg, padx=2, pady=2)
        msg_frame.pack()

        userchat = Label(
            msg_frame,
            text=text,
            bg=userChatTextBg,
            fg="white",
            justify=RIGHT,
            wraplength=280,
            font=("Segoe UI", 11),
            padx=14,
            pady=10,
        )
        userchat.pack()

        # Add timestamp
        timestamp = Label(
            msg_container,
            text=strftime("%I:%M %p"),
            bg=chatBgColor,
            fg=TEXT_MUTED,
            font=("Segoe UI", 8),
        )
        timestamp.pack(anchor="e", pady=(2, 0))


def clearChatScreen():
    for wid in chat_frame.winfo_children():
        wid.destroy()


### SWITCHING BETWEEN FRAMES ###
def raise_frame(frame):
    frame.tkraise()
    clearChatScreen()


################# SHOWING DOWNLOADED IMAGES ###############
# Use LANCZOS instead of deprecated ANTIALIAS
try:
    RESAMPLE_MODE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE_MODE = Image.LANCZOS  # Fallback for older Pillow versions

img0, img1, img2, img3, img4 = None, None, None, None, None


def showSingleImage(type, data=None):
    global img0, img1, img2, img3, img4
    try:
        img0 = ImageTk.PhotoImage(
            Image.open("Downloads/0.jpg").resize((90, 110), RESAMPLE_MODE))
    except BaseException:
        pass
    img1 = ImageTk.PhotoImage(Image.open(
        "assets/images/heads.jpg").resize((220, 200), RESAMPLE_MODE))
    img2 = ImageTk.PhotoImage(Image.open(
        "assets/images/tails.jpg").resize((220, 200), RESAMPLE_MODE))
    img4 = ImageTk.PhotoImage(Image.open("assets/images/WeatherImage.png"))

    if type == "weather":
        weather = Frame(chat_frame)
        weather.pack(anchor="w")
        Label(weather, image=img4, bg=chatBgColor).pack()
        Label(weather,
              text=data[0],
              font=("Arial Bold", 45),
              fg="white",
              bg="#3F48CC").place(x=65, y=45)
        Label(weather,
              text=data[1],
              font=("Montserrat", 15),
              fg="white",
              bg="#3F48CC").place(x=78, y=110)
        Label(weather,
              text=data[2],
              font=("Montserrat", 10),
              fg="white",
              bg="#3F48CC").place(x=78, y=140)
        Label(weather,
              text=data[3],
              font=("Arial Bold", 12),
              fg="white",
              bg="#3F48CC").place(x=60, y=160)

    elif type == "wiki":
        Label(chat_frame, image=img0, bg=chatBgColor).pack(anchor="w")
    elif type == "head":
        Label(chat_frame, image=img1, bg=chatBgColor).pack(anchor="w")
    elif type == "tail":
        Label(chat_frame, image=img2, bg=chatBgColor).pack(anchor="w")
    else:
        img3 = ImageTk.PhotoImage(
            Image.open("assets/images/dice/" + type + ".jpg").resize(
                (200, 200), RESAMPLE_MODE))
        Label(chat_frame, image=img3, bg=chatBgColor).pack(anchor="w")


def showImages(query):
    global img0, img1, img2, img3
    web_scrapping.downloadImage(query)
    w, h = 150, 110
    # Showing Images
    imageContainer = Frame(chat_frame, bg=chatBgColor)
    imageContainer.pack(anchor="w")
    # loading images
    img0 = ImageTk.PhotoImage(
        Image.open("Downloads/0.jpg").resize((w, h), RESAMPLE_MODE))
    img1 = ImageTk.PhotoImage(
        Image.open("Downloads/1.jpg").resize((w, h), RESAMPLE_MODE))
    img2 = ImageTk.PhotoImage(
        Image.open("Downloads/2.jpg").resize((w, h), RESAMPLE_MODE))
    img3 = ImageTk.PhotoImage(
        Image.open("Downloads/3.jpg").resize((w, h), RESAMPLE_MODE))
    # Displaying
    Label(imageContainer, image=img0, bg=chatBgColor).grid(row=0, column=0)
    Label(imageContainer, image=img1, bg=chatBgColor).grid(row=0, column=1)
    Label(imageContainer, image=img2, bg=chatBgColor).grid(row=1, column=0)
    Label(imageContainer, image=img3, bg=chatBgColor).grid(row=1, column=1)


############################# WAEM - WhatsApp Email ######################
def sendWAEM():
    global rec_phoneno, rec_email
    data = WAEMEntry.get()
    rec_email, rec_phoneno = data, data
    WAEMEntry.delete(0, END)
    app_control.Win_Opt("close")


def send(e):
    sendWAEM()


def WAEMPOPUP(Service="None", rec="Reciever"):
    global WAEMEntry
    PopUProot = Tk()
    PopUProot.title(f"{Service} Service")
    PopUProot.configure(bg="white")

    if Service == "WhatsApp":
        PopUProot.iconbitmap("assets/images/whatsapp.ico")
    else:
        PopUProot.iconbitmap("assets/images/email.ico")
    w_width, w_height = 410, 200
    s_width, s_height = PopUProot.winfo_screenwidth(
    ), PopUProot.winfo_screenheight()
    x, y = (s_width / 2) - (w_width / 2), (s_height / 2) - (w_height / 2)
    PopUProot.geometry(
        "%dx%d+%d+%d" %
        (w_width, w_height, x, y - 30))  # center location of the screen
    Label(PopUProot, text=f"Reciever {rec}", font=("Arial", 16),
          bg="white").pack(pady=(20, 10))
    WAEMEntry = Entry(
        PopUProot,
        bd=10,
        relief=FLAT,
        font=("Arial", 12),
        justify="center",
        bg="#DCDCDC",
        width=30,
    )
    WAEMEntry.pack()
    WAEMEntry.focus()

    SendBtn = Button(
        PopUProot,
        text="Send",
        font=("Arial", 12),
        relief=FLAT,
        bg="#14A769",
        fg="white",
        command=sendWAEM,
    )
    SendBtn.pack(pady=20, ipadx=10)
    PopUProot.bind("<Return>", send)
    PopUProot.mainloop()


######################## CHANGING CHAT BACKGROUND COLOR ##################
def getChatColor():
    global chatBgColor
    myColor = colorchooser.askcolor()
    if myColor[1] is None:
        return
    chatBgColor = myColor[1]
    colorbar["bg"] = chatBgColor
    chat_frame["bg"] = chatBgColor
    chat_canvas["bg"] = chatBgColor
    chat_container["bg"] = chatBgColor
    root1["bg"] = chatBgColor
    ChangeSettings(True)


chatMode = 1


def changeChatMode():
    global chatMode
    if chatMode == 1:
        # appControl.volumeControl('mute')
        VoiceModeFrame.pack_forget()
        TextModeFrame.pack(fill=BOTH)
        UserField.focus()
        chatMode = 0
    else:
        # appControl.volumeControl('full')
        TextModeFrame.pack_forget()
        VoiceModeFrame.pack(fill=BOTH)
        root.focus()
        chatMode = 1


############################################## GUI #######################


def onhover(e):
    userPhoto["image"] = chngPh


def onleave(e):
    userPhoto["image"] = userProfileImg


def UpdateIMAGE():
    global ownerPhoto, userProfileImg, userIcon

    os.system("python modules/avatar_selection.py")
    u = UserData()
    u.extractData()
    ownerPhoto = u.getUserPhoto()
    userProfileImg = ImageTk.PhotoImage(
        Image.open(
            "assets/images/avatars/a" +
            str(ownerPhoto) +
            ".png").resize(
            (120,
             120),
            RESAMPLE_MODE))

    userPhoto["image"] = userProfileImg
    userIcon = PhotoImage(file="assets/images/avatars/ChatIcons/a" +
                          str(ownerPhoto) + ".png")


def SelectAvatar():
    Thread(target=UpdateIMAGE).start()


def show_welcome_message():
    """Display a welcome message when the app starts"""
    global ownerName, ownerDesignation

    # Get current hour for appropriate greeting
    current_hour = int(strftime("%H"))
    if current_hour < 12:
        greeting = "Good Morning"
    elif current_hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    welcome_text = f"{greeting}, {ownerName}! 👋"
    help_text = "How can I help you today? You can ask me to:\n• Open applications\n• Search the web\n• Control your system\n• Answer questions using AI"

    # Display bot icon
    Label(chat_frame, image=botIcon, bg=chatBgColor).pack(anchor="w", pady=0)
    attachTOframe(welcome_text, True)
    attachTOframe(help_text, True)


#####################################  MAIN GUI ##########################


#### SPLASH/LOADING SCREEN ####
def progressbar():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure(
        "modern.Horizontal.TProgressbar",
        foreground="#6366f1",
        background="#6366f1",
        troughcolor="#1e293b",
        bordercolor="#1e293b",
        lightcolor="#818cf8",
        darkcolor="#4f46e5",
    )

    progress_bar = ttk.Progressbar(
        splash_root,
        style="modern.Horizontal.TProgressbar",
        orient="horizontal",
        mode="determinate",
        length=350,
    )
    progress_bar.pack(pady=10)
    splash_root.update()
    progress_bar["value"] = 0

    loading_messages = [
        "Initializing AI modules...",
        "Loading voice recognition...",
        "Connecting to services...",
        "Preparing interface...",
        "Almost ready...",
    ]

    msg_idx = 0
    while progress_bar["value"] < 100:
        progress_bar["value"] += 4
        if progress_bar["value"] % 20 == 0 and msg_idx < len(loading_messages):
            splash_label["text"] = loading_messages[msg_idx]
            msg_idx += 1
        splash_root.update()
        sleep(0.08)

    splash_label["text"] = "✓ Ready!"


def destroySplash():
    splash_root.destroy()


if __name__ == "__main__":
    splash_root = Tk()
    splash_root.configure(bg="#0f172a")
    splash_root.overrideredirect(True)

    # Create gradient-like effect with layered frames
    gradient_frame = Frame(splash_root, bg="#0f172a")
    gradient_frame.pack(fill=BOTH, expand=True, padx=2, pady=2)

    # Logo/Icon area
    Label(gradient_frame, text="🎙️", font=("Segoe UI Emoji", 40),
          bg="#0f172a").pack(pady=(25, 5))

    # App title with modern styling
    title_label = Label(
        gradient_frame,
        text="VocalXpert",
        font=("Segoe UI", 32, "bold"),
        bg="#0f172a",
        fg="#6366f1",
    )
    title_label.pack(pady=(5, 2))

    subtitle_label = Label(
        gradient_frame,
        text="Your Intelligent AI Assistant",
        font=("Segoe UI", 12),
        bg="#0f172a",
        fg="#94a3b8",
    )
    subtitle_label.pack(pady=(0, 15))

    splash_label = Label(
        gradient_frame,
        text="Starting...",
        font=("Segoe UI", 10),
        bg="#0f172a",
        fg="#64748b",
    )
    splash_label.pack(pady=(10, 8))

    w_width, w_height = 450, 280
    s_width, s_height = (
        splash_root.winfo_screenwidth(),
        splash_root.winfo_screenheight(),
    )
    x, y = (s_width / 2) - (w_width / 2), (s_height / 2) - (w_height / 2)
    splash_root.geometry("%dx%d+%d+%d" % (w_width, w_height, x, y - 30))

    progressbar()
    splash_root.after(800, destroySplash)
    splash_root.mainloop()

    root = Tk()
    root.title("VocalXpert - AI Assistant")
    w_width, w_height = 420, 700
    s_width, s_height = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (s_width / 2) - (w_width / 2), (s_height / 2) - (w_height / 2)
    root.geometry("%dx%d+%d+%d" % (w_width, w_height, x, y - 30))
    root.configure(bg=background)
    root.minsize(380, 600)

    # Make root window responsive
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    UI_ELEMENTS["root"] = root

    root1 = Frame(root, bg=chatBgColor)
    root2 = Frame(root, bg=background)
    root3 = Frame(root, bg=background)
    UI_ELEMENTS["root1"] = root1
    UI_ELEMENTS["root2"] = root2
    UI_ELEMENTS["root3"] = root3

    for f in (root1, root2, root3):
        f.grid(row=0, column=0, sticky="news")
        f.rowconfigure(0, weight=0)  # Header
        f.rowconfigure(1, weight=1)  # Main content area
        f.columnconfigure(0, weight=1)

    ################################
    ########  CHAT SCREEN  #########
    ################################

    # Modern Header Bar
    header_frame = Frame(root1, bg=ACTIVE_THEME["header_bg"], height=55)
    header_frame.pack(fill=X)
    header_frame.pack_propagate(0)
    UI_ELEMENTS["header_frame"] = header_frame

    # App name in header
    app_name_lbl = Label(
        header_frame,
        text="🎙️ VocalXpert",
        font=("Segoe UI", 15, "bold"),
        bg=ACTIVE_THEME["header_bg"],
        fg=textColor,
    )
    app_name_lbl.pack(side=LEFT, padx=(18, 12), pady=10)
    UI_ELEMENTS["app_name_lbl"] = app_name_lbl

    features_btn = Button(
        header_frame,
        text="Features ▾",
        font=("Segoe UI", 10, "bold"),
        bg=ACTIVE_THEME["features_btn_bg"],
        fg=ACTIVE_THEME["features_btn_fg"],
        activebackground=ACTIVE_THEME["features_btn_bg"],
        activeforeground=textColor,
        relief=FLAT,
        padx=12,
        pady=4,
        cursor="hand2",
        command=toggle_feature_panel,
    )
    features_btn.pack(side=LEFT, pady=10)
    UI_ELEMENTS["features_btn"] = features_btn

    # AI Status indicator in header
    ai_status_frame = Frame(header_frame, bg=ACTIVE_THEME["header_bg"])
    ai_status_frame.pack(side=RIGHT, padx=15, pady=10)
    ai_dot = Label(
        ai_status_frame,
        text="●",
        font=("Segoe UI", 8),
        bg=ACTIVE_THEME["header_bg"],
        fg="#f59e0b",
    )
    ai_dot.pack(side=LEFT)
    ai_status_text = Label(
        ai_status_frame,
        text=" Offline",
        font=("Segoe UI", 9),
        bg=ACTIVE_THEME["header_bg"],
        fg=TEXT_MUTED,
    )
    ai_status_text.pack(side=LEFT)
    UI_ELEMENTS["ai_status_frame"] = ai_status_frame
    UI_ELEMENTS["ai_dot"] = ai_dot
    UI_ELEMENTS["ai_status_text"] = ai_status_text

    # ========================================
    # QUICK ACTIONS TOOLBAR - Feature Buttons
    # ========================================
    quick_actions_frame = Frame(root1, bg=ACTIVE_THEME["qa_bg"], height=50)
    quick_actions_frame.pack(fill=X, pady=(0, 2))
    UI_ELEMENTS["quick_actions_frame"] = quick_actions_frame

    # Define quick action functions
    def quick_weather():
        Thread(target=lambda: main("weather")).start()

    def quick_youtube():
        Label(chat_frame, image=botIcon, bg=chatBgColor).pack(anchor="w",
                                                              pady=0)
        attachTOframe("What would you like to play on YouTube?", True)
        prepare_text_command("play ")
        UserField.icursor(END)

    def quick_google():
        Label(chat_frame, image=botIcon, bg=chatBgColor).pack(anchor="w",
                                                              pady=0)
        attachTOframe("What would you like to search?", True)
        prepare_text_command("search ")
        UserField.icursor(END)

    def quick_games():
        Thread(target=lambda: main("games")).start()

    def quick_screenshot():
        Thread(target=lambda: main("screenshot")).start()

    def quick_joke():
        Thread(target=lambda: main("tell me a joke")).start()

    def quick_email():
        prepare_text_command("send email", auto_send=True)

    def quick_apps():
        Label(chat_frame, image=botIcon, bg=chatBgColor).pack(anchor="w",
                                                              pady=0)
        attachTOframe(
            "Which app would you like to open? (e.g., 'open chrome', 'open notepad', 'open calculator')",
            True,
        )
        prepare_text_command("open ")
        UserField.icursor(END)

    # Quick action button style
    qa_btn_style = {
        "font": ("Segoe UI", 9),
        "bg": ACTIVE_THEME["qa_btn_bg"],
        "fg": ACTIVE_THEME["qa_btn_fg"],
        "bd": 0,
        "relief": FLAT,
        "activebackground": ACTIVE_THEME["qa_btn_active_bg"],
        "activeforeground": ACTIVE_THEME["qa_btn_active_fg"],
        "cursor": "hand2",
        "padx": 8,
        "pady": 4,
    }

    # Create scrollable quick actions
    qa_canvas = Canvas(quick_actions_frame,
                       bg=ACTIVE_THEME["qa_bg"],
                       height=40,
                       highlightthickness=0)
    qa_canvas.pack(fill=X, padx=5, pady=5)
    UI_ELEMENTS["qa_canvas"] = qa_canvas

    qa_inner = Frame(qa_canvas, bg=ACTIVE_THEME["qa_bg"])
    qa_canvas.create_window((0, 0), window=qa_inner, anchor="nw")
    UI_ELEMENTS["qa_inner"] = qa_inner

    # Quick action buttons with icons
    quick_buttons = [
        ("🌤️ Weather", quick_weather),
        ("▶️ YouTube", quick_youtube),
        ("🔍 Search", quick_google),
        ("🎮 Games", quick_games),
        ("📸 Screenshot", quick_screenshot),
        ("😂 Joke", quick_joke),
        ("📧 Email", quick_email),
        ("📂 Apps", quick_apps),
    ]

    for btn_text, btn_cmd in quick_buttons:
        btn = Button(qa_inner, text=btn_text, command=btn_cmd, **qa_btn_style)
        btn.pack(side=LEFT, padx=3)
        quick_action_buttons.append(btn)

    # Update scroll region
    qa_inner.update_idletasks()
    qa_canvas.configure(scrollregion=qa_canvas.bbox("all"))

    # Mouse wheel horizontal scroll for quick actions
    def qa_scroll(event):
        qa_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    qa_canvas.bind_all("<Shift-MouseWheel>", qa_scroll)

    build_feature_panel(root1)

    # Scrollable Chat Container
    chat_container = Frame(root1, width=400, height=480, bg=chatBgColor)
    chat_container.pack(padx=5, pady=5)
    chat_container.pack_propagate(0)
    UI_ELEMENTS["chat_container"] = chat_container

    # Canvas for scrolling
    chat_canvas = Canvas(chat_container,
                         bg=chatBgColor,
                         highlightthickness=0,
                         width=385,
                         height=480)
    chat_scrollbar = Scrollbar(
        chat_container,
        orient="vertical",
        command=chat_canvas.yview,
        bg="#334155",
        troughcolor=chatBgColor,
    )
    UI_ELEMENTS["chat_canvas"] = chat_canvas

    # Chat Frame inside Canvas
    chat_frame = Frame(chat_canvas, bg=chatBgColor, width=375)
    UI_ELEMENTS["chat_frame"] = chat_frame

    # Create window in canvas
    chat_canvas_window = chat_canvas.create_window((0, 0),
                                                   window=chat_frame,
                                                   anchor="nw")

    # Configure scrolling
    chat_canvas.configure(yscrollcommand=chat_scrollbar.set)

    def on_chat_frame_configure(event):
        chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))
        # Auto-scroll to bottom when new content added
        chat_canvas.yview_moveto(1.0)

    def on_canvas_configure(event):
        chat_canvas.itemconfig(chat_canvas_window, width=event.width - 10)

    chat_frame.bind("<Configure>", on_chat_frame_configure)
    chat_canvas.bind("<Configure>", on_canvas_configure)

    # Mouse wheel scrolling
    def on_mousewheel(event):
        chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    chat_canvas.bind_all("<MouseWheel>", on_mousewheel)

    # Pack scrollbar and canvas
    chat_scrollbar.pack(side=RIGHT, fill=Y)
    chat_canvas.pack(side=LEFT, fill=BOTH, expand=True)

    # Modern bottom control bar
    bottomFrame1 = Frame(root1, bg=SURFACE_DARK, height=120)
    bottomFrame1.pack(fill=X, side=BOTTOM)
    VoiceModeFrame = Frame(bottomFrame1, bg=SURFACE_DARK)
    VoiceModeFrame.pack(fill=BOTH)
    TextModeFrame = Frame(bottomFrame1, bg=SURFACE_DARK)
    TextModeFrame.pack(fill=BOTH)
    UI_ELEMENTS["bottomFrame1"] = bottomFrame1
    UI_ELEMENTS["VoiceModeFrame"] = VoiceModeFrame
    UI_ELEMENTS["TextModeFrame"] = TextModeFrame

    TextModeFrame.pack_forget()

    cblLightImg = PhotoImage(file="assets/images/centralButton.png")
    cblDarkImg = PhotoImage(file="assets/images/centralButton1.png")
    cbl = Label(
        VoiceModeFrame,
        fg="white",
        image=cblDarkImg if KCS_IMG == 1 else cblLightImg,
        bg=SURFACE_DARK,
    )
    cbl.pack(pady=(14, 6))
    AITaskStatusLbl = Label(
        VoiceModeFrame,
        text="    Offline",
        fg=textColor,
        bg=AITaskStatusLblBG,
        font=("Segoe UI", 13, "bold"),
    )
    AITaskStatusLbl.pack()
    UI_ELEMENTS["cbl"] = cbl
    UI_ELEMENTS["AITaskStatusLbl"] = AITaskStatusLbl

    # Settings Button
    sphLight = PhotoImage(file="assets/images/setting.png")
    sphLight = sphLight.subsample(2, 2)
    sphDark = PhotoImage(file="assets/images/setting1.png")
    sphDark = sphDark.subsample(2, 2)
    settingBtn = Button(
        VoiceModeFrame,
        image=sphDark if KCS_IMG == 1 else sphLight,
        height=30,
        width=30,
        bg=SURFACE_DARK,
        borderwidth=0,
        activebackground=SURFACE_LIGHT,
        command=lambda: raise_frame(root2),
    )
    settingBtn.place(relx=1.0, y=22, x=-20, anchor="ne")
    UI_ELEMENTS["settingBtn"] = settingBtn

    # Keyboard Button
    kbphLight = PhotoImage(file="assets/images/keyboard.png")
    kbphLight = kbphLight.subsample(2, 2)
    kbphDark = PhotoImage(file="assets/images/keyboard1.png")
    kbphDark = kbphDark.subsample(2, 2)
    kbBtn = Button(
        VoiceModeFrame,
        image=kbphDark if KCS_IMG == 1 else kbphLight,
        height=30,
        width=30,
        bg=SURFACE_DARK,
        borderwidth=0,
        activebackground=SURFACE_LIGHT,
        command=changeChatMode,
    )
    kbBtn.place(x=25, y=22)
    UI_ELEMENTS["kbBtn"] = kbBtn

    # Text-mode hint & container
    TextModeFrame.columnconfigure(0, weight=1)
    TextModeFrame.columnconfigure(1, weight=0)
    input_hint = Label(
        TextModeFrame,
        text="Type a command, then press Enter or Send",
        font=("Segoe UI", 10),
        bg=SURFACE_DARK,
        fg=TEXT_MUTED,
    )
    input_hint.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")
    UI_ELEMENTS["input_hint"] = input_hint

    input_container = Frame(TextModeFrame, bg=SURFACE_LIGHT, bd=0, relief=FLAT)
    input_container.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
    input_container.columnconfigure(0, weight=1)
    UI_ELEMENTS["input_container"] = input_container

    UserFieldLBL = input_container
    UserField = Entry(
        input_container,
        fg=ACTIVE_THEME["placeholder_fg"],
        bg=SURFACE_LIGHT,
        font=("Segoe UI", 13),
        bd=0,
        relief=FLAT,
        insertbackground=ACCENT_PRIMARY,
    )
    UserField.grid(row=0, column=0, padx=(14, 8), pady=12, sticky="ew")
    UserField.insert(0, "Ask me anything...")
    UserField.bind("<Return>", keyboardInput)
    UserField.bind("<FocusIn>", on_entry_focus_in)
    UserField.bind("<FocusOut>", on_entry_focus_out)
    UI_ELEMENTS["UserField"] = UserField

    sendBtn = Button(
        input_container,
        text="Send",
        font=("Segoe UI", 11, "bold"),
        bg=ACTIVE_THEME["send_btn_bg"],
        fg=ACTIVE_THEME["send_btn_fg"],
        activebackground=BTN_PRIMARY_HOVER,
        activeforeground="white",
        relief=FLAT,
        padx=14,
        pady=6,
        cursor="hand2",
        command=keyboardInput,
    )
    sendBtn.grid(row=0, column=1, padx=(0, 12), pady=8)
    UI_ELEMENTS["sendBtn"] = sendBtn

    micImg = PhotoImage(file="assets/images/mic.png")
    micImg = micImg.subsample(2, 2)
    micBtn = Button(
        TextModeFrame,
        image=micImg,
        height=30,
        width=30,
        bg=ACTIVE_THEME["mic_btn_bg"],
        borderwidth=0,
        activebackground=SURFACE_LIGHT,
        command=changeChatMode,
    )
    micBtn.grid(row=0, column=1, padx=(0, 18), pady=(8, 0), sticky="e")
    UI_ELEMENTS["micBtn"] = micBtn

    # User and Bot Icon
    userIcon = PhotoImage(file="assets/images/avatars/ChatIcons/a" +
                          str(ownerPhoto) + ".png")
    botIcon = PhotoImage(file="assets/images/assistant2.png")
    botIcon = botIcon.subsample(2, 2)

    ###########################
    ########  SETTINGS  #######
    ###########################

    # Settings header with modern styling
    settingsLbl = Label(
        root2,
        text="⚙ Settings",
        font=("Segoe UI", 18, "bold"),
        bg=background,
        fg=textColor,
    )
    settingsLbl.pack(pady=15)
    separator = ttk.Separator(root2, orient="horizontal")
    separator.pack(fill=X, padx=20)
    # User Photo
    userProfileImg = Image.open("assets/images/avatars/a" + str(ownerPhoto) +
                                ".png")
    userProfileImg = ImageTk.PhotoImage(
        userProfileImg.resize((120, 120), RESAMPLE_MODE))
    userPhoto = Button(
        root2,
        image=userProfileImg,
        bg=background,
        bd=0,
        relief=FLAT,
        activebackground=background,
        command=SelectAvatar,
    )
    userPhoto.pack(pady=(20, 5))

    # Change Photo
    chngPh = ImageTk.PhotoImage(
        Image.open("assets/images/avatars/changephoto2.png").resize(
            (120, 120), RESAMPLE_MODE))

    userPhoto.bind("<Enter>", onhover)
    userPhoto.bind("<Leave>", onleave)

    # Username
    userName = Label(root2,
                     text=ownerName,
                     font=("Arial Bold", 15),
                     fg=textColor,
                     bg=background)
    userName.pack()

    # Settings Frame
    settingsFrame = Frame(root2, width=300, height=300, bg=background)
    settingsFrame.pack(pady=20)

    assLbl = Label(
        settingsFrame,
        text="🔊 Assistant Voice",
        font=("Segoe UI", 12),
        fg=textColor,
        bg=background,
    )
    assLbl.place(x=0, y=20)
    n = StringVar()
    assVoiceOption = ttk.Combobox(
        settingsFrame,
        values=("Female", "Male"),
        font=("Segoe UI", 11),
        width=13,
        textvariable=n,
    )
    assVoiceOption.current(voice_id)
    assVoiceOption.place(x=150, y=20)
    assVoiceOption.bind("<<ComboboxSelected>>", changeVoice)

    voiceRateLbl = Label(
        settingsFrame,
        text="⚡ Voice Rate",
        font=("Segoe UI", 12),
        fg=textColor,
        bg=background,
    )
    voiceRateLbl.place(x=0, y=60)
    n2 = StringVar()
    voiceOption = ttk.Combobox(settingsFrame,
                               font=("Segoe UI", 11),
                               width=13,
                               textvariable=n2)
    voiceOption["values"] = ("Very Low", "Low", "Normal", "Fast", "Very Fast")
    voiceOption.current(ass_voiceRate // 50 - 2)  # 100 150 200 250 300
    voiceOption.place(x=150, y=60)
    voiceOption.bind("<<ComboboxSelected>>", changeVoiceRate)

    volumeLbl = Label(
        settingsFrame,
        text="🔉 Volume",
        font=("Segoe UI", 12),
        fg=textColor,
        bg=background,
    )
    volumeLbl.place(x=0, y=105)
    volumeBar = Scale(
        settingsFrame,
        bg=background,
        fg=textColor,
        sliderlength=30,
        length=135,
        width=16,
        highlightbackground=background,
        troughcolor="#334155",
        activebackground="#6366f1",
        orient="horizontal",
        from_=0,
        to=100,
        command=changeVolume,
    )
    volumeBar.set(int(ass_volume * 100))
    volumeBar.place(x=150, y=85)

    themeLbl = Label(
        settingsFrame,
        text="🎨 Theme",
        font=("Segoe UI", 12),
        fg=textColor,
        bg=background,
    )
    themeLbl.place(x=0, y=143)
    themeValue = IntVar()
    s = ttk.Style()
    s.configure(
        "Wild.TRadiobutton",
        font=("Segoe UI", 10),
        background=background,
        foreground=textColor,
        focuscolor=s.configure(".")["background"],
    )
    darkBtn = ttk.Radiobutton(
        settingsFrame,
        text="Dark",
        value=1,
        variable=themeValue,
        style="Wild.TRadiobutton",
        command=changeTheme,
        takefocus=False,
    )
    darkBtn.place(x=150, y=145)
    lightBtn = ttk.Radiobutton(
        settingsFrame,
        text="Light",
        value=2,
        variable=themeValue,
        style="Wild.TRadiobutton",
        command=changeTheme,
        takefocus=False,
    )
    lightBtn.place(x=230, y=145)
    themeValue.set(1)
    if KCS_IMG == 0:
        themeValue.set(2)

    chooseChatLbl = Label(
        settingsFrame,
        text="💬 Chat Background",
        font=("Segoe UI", 12),
        fg=textColor,
        bg=background,
    )
    chooseChatLbl.place(x=0, y=180)
    cimg = PhotoImage(file="assets/images/colorchooser.png")
    cimg = cimg.subsample(3, 3)
    colorbar = Label(settingsFrame, bd=3, width=18, height=1, bg=chatBgColor)
    colorbar.place(x=150, y=180)
    if KCS_IMG == 0:
        colorbar["bg"] = "#E8EBEF"
    Button(settingsFrame, image=cimg, relief=FLAT,
           command=getChatColor).place(x=261, y=180)

    backBtn = Button(
        settingsFrame,
        text="  ← Back  ",
        bd=0,
        font=("Segoe UI", 11, "bold"),
        fg="white",
        bg="#6366f1",
        relief=FLAT,
        activebackground="#4f46e5",
        activeforeground="white",
        cursor="hand2",
        command=lambda: raise_frame(root1),
    )
    clearFaceBtn = Button(
        settingsFrame,
        text="  🗑 Clear Facial Data  ",
        bd=0,
        font=("Segoe UI", 11, "bold"),
        fg="white",
        bg="#ef4444",
        relief=FLAT,
        activebackground="#dc2626",
        activeforeground="white",
        cursor="hand2",
        command=deleteUserData,
    )
    backBtn.place(x=5, y=250)
    clearFaceBtn.place(x=100, y=250)

    # Function to check and update AI status
    def check_ai_status():
        global AI_ONLINE
        try:
            AI_ONLINE = normal_chat.is_ai_online()
            if AI_ONLINE:
                AITaskStatusLbl["text"] = "  🤖 AI Online"
                AITaskStatusLbl["fg"] = "#10b981"  # Green
                # Update header status
                ai_dot["fg"] = "#10b981"
                ai_status_text["text"] = " AI Online"
                ai_status_text["fg"] = "#10b981"
            else:
                AITaskStatusLbl["text"] = "  📴 Offline Mode"
                AITaskStatusLbl["fg"] = "#f59e0b"  # Amber
                ai_dot["fg"] = "#f59e0b"
                ai_status_text["text"] = " Offline"
                ai_status_text["fg"] = "#94a3b8"
        except BaseException:
            AITaskStatusLbl["text"] = "  📴 Offline Mode"
            AITaskStatusLbl["fg"] = "#f59e0b"
            ai_dot["fg"] = "#f59e0b"
            ai_status_text["text"] = " Offline"
            ai_status_text["fg"] = "#94a3b8"
        # Re-check every 30 seconds
        root.after(30000, check_ai_status)

    try:
        # pass
        Thread(target=voiceMedium).start()
    except BaseException:
        pass
    try:
        # pass
        Thread(target=web_scrapping.dataUpdate).start()
    except Exception as e:
        print("System is Offline...")

    # Initial AI status check
    root.after(2000, check_ai_status)

    # Show welcome message after a short delay
    root.after(500, show_welcome_message)

    # Start UI queue processor for thread-safe updates
    root.after(100, process_ui_queue)
    logger.info("VocalXpert started successfully")

    root.iconbitmap("assets/images/assistant2.ico")
    raise_frame(root1)
    root.mainloop()
