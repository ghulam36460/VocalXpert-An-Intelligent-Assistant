"""
VocalXpert Modern UI - Main Application

The main window that integrates all panels and manages the application lifecycle.
"""

import sys
import os
import logging
import json
import time
import wave
import tempfile
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStackedWidget, QSplashScreen, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal, QObject
from PySide6.QtGui import QFont, QPixmap, QIcon

# Try to import speech recognition libraries
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

# Try to import requests for API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vocalxpert.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VocalXpert')

# Import frontend modules
from .themes import (
    DARK_THEME, LIGHT_THEME, FONTS, SPACING, RADIUS,
    get_theme, generate_stylesheet
)
from .components import NavButton, Card
from .chat_panel import ChatPanel
from .settings_panel import SettingsPanel
from .games_panel import GamesPanel
from .features_panel import FeaturesPanel
from .history_panel import HistoryPanel
from .workers import (
    VoiceRecognitionWorker, TextToSpeechWorker,
    CommandWorker, ContinuousVoiceWorker
)


class Sidebar(QFrame):
    """
    Modern sidebar navigation.
    """
    
    def __init__(self, parent=None, navigate_callback=None):
        super().__init__(parent)
        self.navigate_callback = navigate_callback
        self._setup_ui()
        self._active_button = None
    
    def _setup_ui(self):
        """Build sidebar UI."""
        self.setFixedWidth(220)
        theme = get_theme()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.sidebar_bg};
                border-right: 1px solid {theme.border};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["lg"], SPACING["md"], SPACING["lg"])
        layout.setSpacing(SPACING["xs"])
        
        # Logo/Brand
        brand = QLabel("🎙️ VocalXpert")
        brand.setFont(QFont(FONTS["family"], FONTS["size_xl"], FONTS["weight_bold"]))
        brand.setAlignment(Qt.AlignCenter)
        layout.addWidget(brand)
        
        layout.addSpacing(SPACING["xl"])
        
        # Navigation buttons
        self.nav_buttons = {}
        
        nav_items = [
            ("chat", "💬", "Chat"),
            ("history", "📚", "History"),
            ("features", "✨", "Features"),
            ("games", "🎮", "Games"),
            ("settings", "⚙️", "Settings"),
        ]
        
        for key, icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked=False, k=key: self._on_nav_click(k))
            self.nav_buttons[key] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Version info
        version = QLabel("v2.0.0")
        version.setProperty("class", "muted")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
    
    def _on_nav_click(self, key: str):
        """Handle navigation click."""
        logger.info(f"Sidebar clicked: {key}")
        if self._active_button:
            self._active_button.set_active(False)
        
        self.nav_buttons[key].set_active(True)
        self._active_button = self.nav_buttons[key]
        
        # Call navigation callback
        if self.navigate_callback:
            self.navigate_callback(key)
    
    def set_active(self, key: str):
        """Set active navigation item programmatically."""
        if self._active_button:
            self._active_button.set_active(False)
        
        if key in self.nav_buttons:
            self.nav_buttons[key].set_active(True)
            self._active_button = self.nav_buttons[key]
    
    def update_theme(self, theme):
        """Update sidebar theme."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.sidebar_bg};
                border-right: 1px solid {theme.border};
            }}
        """)


class MainWindow(QMainWindow):
    """
    Main application window.
    """
    
    def __init__(self):
        super().__init__()
        
        self._current_theme = DARK_THEME
        self._voice_mode_active = False  # Changed from _voice_active
        self._continuous_voice_worker = None
        self._settings = {}
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._apply_theme(self._current_theme)
        
        # Set initial page
        self.sidebar.set_active("chat")
        
        logger.info("VocalXpert UI initialized")
    
    def _setup_window(self):
        """Configure main window."""
        self.setWindowTitle("VocalXpert - AI Assistant")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)
        
        # Try to set icon
        icon_path = Path(__file__).parent.parent / "assets" / "images" / "assistant2.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def _setup_ui(self):
        """Build the main UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        central.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar(self, self.navigate_to)
        main_layout.addWidget(self.sidebar)
        
        # Content stack
        self.content_stack = QStackedWidget()

        # Create panels
        self.chat_panel = ChatPanel()
        self.history_panel = HistoryPanel()
        self.features_panel = FeaturesPanel()
        self.games_panel = GamesPanel()
        self.settings_panel = SettingsPanel()

        # Add to stack (order matters for index)
        self.content_stack.addWidget(self.chat_panel)      # 0
        self.content_stack.addWidget(self.history_panel)   # 1
        self.content_stack.addWidget(self.features_panel)  # 2
        self.content_stack.addWidget(self.games_panel)     # 3
        self.content_stack.addWidget(self.settings_panel)  # 4

        main_layout.addWidget(self.content_stack, 1)

        # Page index mapping
        self._page_indices = {
            "chat": 0,
            "history": 1,
            "features": 2,
            "games": 3,
            "settings": 4,
        }
    
    def _connect_signals(self):
        """Connect all signals and slots."""
        # Ensure panels are created
        if not hasattr(self, 'chat_panel'):
            self.chat_panel = ChatPanel()
        if not hasattr(self, 'history_panel'):
            self.history_panel = HistoryPanel()
        if not hasattr(self, 'features_panel'):
            self.features_panel = FeaturesPanel()
        if not hasattr(self, 'games_panel'):
            self.games_panel = GamesPanel()
        if not hasattr(self, 'settings_panel'):
            self.settings_panel = SettingsPanel()
        
        # content_stack and panels are created in _setup_ui; nothing to do here
        
        # Chat panel
        self.chat_panel.message_sent.connect(self._on_message_sent)
        self.chat_panel.voice_clicked.connect(self._on_voice_clicked)
        self.chat_panel.quick_action.connect(self._on_command)
        
        # Features panel
        self.features_panel.feature_clicked.connect(self._on_command)
        
        # Settings panel
        self.settings_panel.theme_changed.connect(self._on_theme_changed)
    
    def navigate_to(self, page: str):
        """Navigate to a specific page."""
        logger.info(f"Navigating to page: {page}")
        if page in self._page_indices:
            index = self._page_indices[page]
            logger.info(f"Setting content stack to index {index}")
            self.content_stack.setCurrentIndex(index)
            logger.info(f"Navigated to {page}")
        else:
            logger.error(f"Unknown page: {page}")
    
    def _apply_theme(self, theme):
        """Apply theme to application."""
        self._current_theme = theme
        stylesheet = generate_stylesheet(theme)
        self.setStyleSheet(stylesheet)
        self.sidebar.update_theme(theme)
        logger.info(f"Applied {theme.name} theme")
    
    def _on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        theme = DARK_THEME if theme_name == "dark" else LIGHT_THEME
        self._apply_theme(theme)
    
    def _on_message_sent(self, text: str):
        """Handle user message."""
        logger.info(f"User message: {text}")
        
        # Add user message to chat
        self.chat_panel.add_message(text, is_user=True)
        
        # Process command
        self._on_command(text)
    
    def _on_command(self, command: str):
        """Process a command."""
        logger.info(f"Processing command: {command}")
        self.chat_panel.set_status("processing", "Processing...")
        
        # Create worker thread
        settings = self.settings_panel.get_settings()
        self._command_worker = CommandWorker(command, settings)
        self._command_worker.status_changed.connect(
            lambda s: self.chat_panel.set_status("processing", s)
        )
        self._command_worker.result_ready.connect(self._on_command_result)
        self._command_worker.open_game.connect(self._on_open_game)
        self._command_worker.error_occurred.connect(self._on_command_error)
        self._command_worker.start()
    
    def _on_command_result(self, response: str, action_type: str):
        """Handle command result."""
        logger.info(f"Command result ({action_type}): {response[:50]}...")
        
        # Add bot response
        self.chat_panel.add_message(response, is_user=False)
        self.chat_panel.set_status("ready")
        
        # Speak response if TTS enabled (always speak in voice mode for feedback)
        settings = self.settings_panel.get_settings()
        if settings.get("voice_output", True):
            self._speak(response)
        
        # Update weather display if weather command
        if action_type == "weather":
            self.features_panel.update_weather(response)
    
    def _on_command_error(self, error: str):
        """Handle command error."""
        logger.error(f"Command error: {error}")
        self.chat_panel.add_message(f"Sorry, I encountered an error: {error}", is_user=False)
        self.chat_panel.set_status("ready")
    
    def _on_open_game(self, game_name: str):
        """Open a game panel."""
        if game_name == "rps":
            self.navigate_to("games")
            self.sidebar.set_active("games")
            self.games_panel.open_rps()
    
    def _on_voice_clicked(self):
        """Handle voice button click - toggle voice mode."""
        if self._voice_mode_active:
            self._stop_voice_mode()
        else:
            self._start_voice_mode()
    
    def _start_voice_mode(self):
        """Start continuous voice mode."""
        self._voice_mode_active = True
        self.chat_panel.set_voice_active(True)
        self.chat_panel.set_status("listening", "Voice mode active")
        self.chat_panel.add_message("🎤 Voice mode activated! Speak naturally and I'll respond automatically.", is_user=False)

        logger.info("Starting continuous voice mode")

        # Check if speech recognition is available
        if not SR_AVAILABLE:
            self.chat_panel.add_message("❌ Speech recognition library not available. Please install: pip install SpeechRecognition", is_user=False)
            self._stop_voice_mode()
            return

        if not PYAUDIO_AVAILABLE:
            self.chat_panel.add_message("❌ PyAudio not available. Please install: pip install pyaudio", is_user=False)
            self._stop_voice_mode()
            return

        # Start continuous voice worker
        self._continuous_voice_worker = ContinuousVoiceWorker()
        self._continuous_voice_worker.status_changed.connect(
            lambda s: self.chat_panel.set_status("listening", s)
        )
        self._continuous_voice_worker.result_ready.connect(self._on_voice_result)
        self._continuous_voice_worker.stopped.connect(self._on_voice_mode_stopped)
        
        self._continuous_voice_worker.start_listening()
    
    def _stop_voice_mode(self):
        """Stop continuous voice mode."""
        self._voice_mode_active = False
        self.chat_panel.set_voice_active(False)
        self.chat_panel.set_status("ready")
        self.chat_panel.add_message("🎤 Voice mode deactivated.", is_user=False)

        if self._continuous_voice_worker:
            self._continuous_voice_worker.stop_listening()
            self._continuous_voice_worker = None

        logger.info("Stopped continuous voice mode")
    
    def _on_voice_result(self, text: str):
        """Handle voice recognition result."""
        logger.info(f"Voice result: '{text}'")
        
        if text and text.strip():
            # Process as message - don't stop voice mode
            self._on_message_sent(text)
        else:
            self.chat_panel.add_message("Voice recognition returned empty result. Please try speaking more clearly.", is_user=False)
    
    def _on_voice_error(self, error: str):
        """Handle voice recognition error."""
        logger.warning(f"Voice error: {error}")
        
        if error == "timeout":
            # In continuous mode, timeout just means no speech detected - don't show error
            if not self._voice_mode_active:
                self.chat_panel.set_status("ready", "No speech detected")
                self.chat_panel.add_message("Voice recognition timed out. Please speak louder or closer to the microphone, then try again.", is_user=False)
        elif error == "empty":
            # Don't show empty result errors in continuous mode
            if not self._voice_mode_active:
                self.chat_panel.set_status("ready", "No speech detected")
                self.chat_panel.add_message("🎤 No speech detected. Please speak clearly into your microphone and try again.", is_user=False)
        elif error == "network":
            self.chat_panel.add_message("Network error. Please check your connection.", is_user=False)
        else:
            self.chat_panel.add_message(f"Voice recognition error: {error}", is_user=False)
        
        # Only stop voice mode for serious errors
        if error not in ["timeout", "empty"] and self._voice_mode_active:
            self._stop_voice_mode()
    
    def _on_voice_mode_stopped(self):
        """Handle voice mode stopped."""
        self._voice_mode_active = False
        self.chat_panel.set_voice_active(False)
        self.chat_panel.set_status("ready")
    
    def _speak(self, text: str):
        """Speak text using TTS."""
        logger.info(f"Speaking: {text[:30]}...")
        
        # Stop previous TTS worker if still running
        if hasattr(self, '_tts_worker') and self._tts_worker:
            if self._tts_worker.isRunning():
                self._tts_worker.stop()
                self._tts_worker.wait(1000)  # Wait up to 1 second
        
        # Use louder volume when voice mode is active
        volume = 1.0 if getattr(self, '_voice_mode_active', False) else 0.8
        self._tts_worker = TextToSpeechWorker(text, volume=volume)
        self._tts_worker.status_changed.connect(
            lambda s: self.chat_panel.set_status("speaking", s)
        )
        self._tts_worker.finished.connect(
            lambda: self.chat_panel.set_status("ready")
        )
        # Notify continuous voice worker when TTS finishes
        if self._continuous_voice_worker:
            self._tts_worker.finished.connect(self._continuous_voice_worker.on_tts_finished)
        self._tts_worker.start()
    
    def closeEvent(self, event):
        """Handle window close."""
        logger.info("Application closing - cleaning up threads...")

        # Stop voice mode if active
        if self._voice_mode_active:
            self._stop_voice_mode()

        # Synchronous cleanup - no timers needed
        self._cleanup_all_threads()
        event.accept()

    def _cleanup_all_threads(self):
        """Synchronously clean up all threads."""
        try:
            # Stop continuous voice worker first
            if hasattr(self, '_continuous_voice_worker') and self._continuous_voice_worker:
                logger.info("Stopping continuous voice worker...")
                self._continuous_voice_worker.stop_listening()
                # Give it a moment to stop its current thread
                QTimer.singleShot(200, self._cleanup_individual_threads)

        except Exception as e:
            logger.error(f"Error stopping continuous voice worker: {e}")
            self._cleanup_individual_threads()

    def _cleanup_individual_threads(self):
        """Clean up individual worker threads."""
        try:
            # Stop TTS worker
            if hasattr(self, '_tts_worker') and self._tts_worker:
                logger.info("Stopping TTS worker...")
                if self._tts_worker.isRunning():
                    self._tts_worker.stop()
                    if not self._tts_worker.wait(3000):  # Wait up to 3 seconds
                        logger.warning("TTS worker didn't stop gracefully, terminating...")
                        self._tts_worker.terminate()
                        self._tts_worker.wait(1000)
                self._tts_worker = None

            # Stop command worker
            if hasattr(self, '_command_worker') and self._command_worker:
                logger.info("Stopping command worker...")
                if self._command_worker.isRunning():
                    # CommandWorker doesn't have a stop method, so just terminate
                    self._command_worker.terminate()
                    if not self._command_worker.wait(2000):
                        logger.warning("Command worker didn't terminate gracefully")
                self._command_worker = None

            # Force cleanup of any remaining threads by processing events
            QTimer.singleShot(100, self._force_thread_cleanup)
            logger.info("All threads cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during thread cleanup: {e}")

    def _force_thread_cleanup(self):
        """Force cleanup of any remaining threads."""
        try:
            # Process any pending events to ensure thread cleanup
            app = QApplication.instance()
            if app:
                app.processEvents()
            logger.info("Forced thread cleanup completed")
        except Exception as e:
            logger.error(f"Error during forced cleanup: {e}")


def create_splash_screen(app: QApplication) -> QSplashScreen:
    """Create and show splash screen."""
    # Create splash pixmap with gradient
    from PySide6.QtGui import QPainter, QLinearGradient, QColor
    
    pixmap = QPixmap(400, 300)
    pixmap.fill(QColor("#0f0f1a"))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Draw text
    painter.setPen(QColor("#f8fafc"))
    font = QFont("Segoe UI", 32, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "🎙️ VocalXpert")
    
    # Subtitle
    font.setPointSize(12)
    font.setBold(False)
    painter.setFont(font)
    painter.setPen(QColor("#64748b"))
    painter.drawText(
        0, 180, 400, 50, 
        Qt.AlignCenter, 
        "Loading..."
    )
    
    painter.end()
    
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()
    
    return splash


def main():
    """Main entry point."""
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("VocalXpert")
    app.setApplicationVersion("2.0.0")
    
    # Show splash screen
    splash = create_splash_screen(app)
    
    # Create main window
    window = MainWindow()
    
    # Hide splash and show main window
    def show_main():
        splash.finish(window)
        window.show()
    
    QTimer.singleShot(1500, show_main)
    
    logger.info("VocalXpert started")
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
