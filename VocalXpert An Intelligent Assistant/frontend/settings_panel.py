"""
Settings Panel - Application configuration

User preferences, theme selection, voice settings, and more.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QFrame,
    QComboBox,
    QSlider,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import Card, AnimatedToggle, SectionHeader
from .themes import FONTS, SPACING, get_theme


class SettingsPanel(QWidget):
    """
    Settings configuration panel.
    """

    theme_changed = Signal(str)
    voice_settings_changed = Signal(dict)
    setting_changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Build the settings interface."""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        # Content container
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"],
                                  SPACING["xl"])
        layout.setSpacing(SPACING["xl"])

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Appearance settings
        appearance = self._create_appearance_section()
        layout.addWidget(appearance)

        # Voice settings
        voice = self._create_voice_section()
        layout.addWidget(voice)

        # AI settings
        ai_settings = self._create_ai_section()
        layout.addWidget(ai_settings)

        # Web scraping settings
        web_settings = self._create_web_section()
        layout.addWidget(web_settings)

        # About section
        about = self._create_about_section()
        layout.addWidget(about)

        layout.addStretch()

        scroll.setWidget(content)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_header(self) -> QWidget:
        """Create settings header."""
        header = QFrame()
        theme = get_theme()

        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, SPACING["lg"])

        title = QLabel("⚙️ Settings")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_2xl"], FONTS["weight_bold"]))

        subtitle = QLabel("Customize your VocalXpert experience")
        subtitle.setProperty("class", "muted")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        return header

    def _create_appearance_section(self) -> Card:
        """Create appearance settings section."""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"],
                                  SPACING["lg"])
        layout.setSpacing(SPACING["lg"])

        # Section title
        title = QLabel("🎨 Appearance")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(title)

        # Theme toggle
        theme_row = QWidget()
        theme_layout = QHBoxLayout(theme_row)
        theme_layout.setContentsMargins(0, 0, 0, 0)

        theme_label = QLabel("Dark Mode")
        theme_desc = QLabel("Switch between light and dark theme")
        theme_desc.setProperty("class", "muted")

        theme_text = QVBoxLayout()
        theme_text.setSpacing(2)
        theme_text.addWidget(theme_label)
        theme_text.addWidget(theme_desc)

        self.dark_mode_toggle = AnimatedToggle()
        self.dark_mode_toggle.setChecked(True)  # Default to dark
        self.dark_mode_toggle.toggled.connect(
            lambda checked: self.theme_changed.emit("dark"
                                                    if checked else "light"))

        theme_layout.addLayout(theme_text)
        theme_layout.addStretch()
        theme_layout.addWidget(self.dark_mode_toggle)

        layout.addWidget(theme_row)

        # Accent color (future feature)
        accent_row = QWidget()
        accent_layout = QHBoxLayout(accent_row)
        accent_layout.setContentsMargins(0, 0, 0, 0)

        accent_label = QLabel("Accent Color")
        accent_desc = QLabel("Primary color for buttons and highlights")
        accent_desc.setProperty("class", "muted")

        accent_text = QVBoxLayout()
        accent_text.setSpacing(2)
        accent_text.addWidget(accent_label)
        accent_text.addWidget(accent_desc)

        self.accent_combo = QComboBox()
        self.accent_combo.addItems(
            ["Indigo", "Purple", "Blue", "Green", "Pink"])
        self.accent_combo.setFixedWidth(120)

        accent_layout.addLayout(accent_text)
        accent_layout.addStretch()
        accent_layout.addWidget(self.accent_combo)

        layout.addWidget(accent_row)

        return card

    def _create_voice_section(self) -> Card:
        """Create voice settings section."""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"],
                                  SPACING["lg"])
        layout.setSpacing(SPACING["lg"])

        # Section title
        title = QLabel("🎤 Voice Settings")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(title)

        # Voice enabled toggle
        voice_row = QWidget()
        voice_layout = QHBoxLayout(voice_row)
        voice_layout.setContentsMargins(0, 0, 0, 0)

        voice_label = QLabel("Voice Input")
        voice_desc = QLabel("Enable microphone input for commands")
        voice_desc.setProperty("class", "muted")

        voice_text = QVBoxLayout()
        voice_text.setSpacing(2)
        voice_text.addWidget(voice_label)
        voice_text.addWidget(voice_desc)

        self.voice_toggle = AnimatedToggle()
        self.voice_toggle.setChecked(True)

        voice_layout.addLayout(voice_text)
        voice_layout.addStretch()
        voice_layout.addWidget(self.voice_toggle)

        layout.addWidget(voice_row)

        # Speech rate
        rate_row = QWidget()
        rate_layout = QHBoxLayout(rate_row)
        rate_layout.setContentsMargins(0, 0, 0, 0)

        rate_label = QLabel("Speech Rate")
        rate_desc = QLabel("How fast the assistant speaks")
        rate_desc.setProperty("class", "muted")

        rate_text = QVBoxLayout()
        rate_text.setSpacing(2)
        rate_text.addWidget(rate_label)
        rate_text.addWidget(rate_desc)

        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(100, 250)
        self.rate_slider.setValue(175)
        self.rate_slider.setFixedWidth(150)

        self.rate_value = QLabel("175")
        self.rate_value.setFixedWidth(40)
        self.rate_slider.valueChanged.connect(
            lambda v: self.rate_value.setText(str(v)))

        rate_layout.addLayout(rate_text)
        rate_layout.addStretch()
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_value)

        layout.addWidget(rate_row)

        # Voice output toggle
        tts_row = QWidget()
        tts_layout = QHBoxLayout(tts_row)
        tts_layout.setContentsMargins(0, 0, 0, 0)

        tts_label = QLabel("Voice Output")
        tts_desc = QLabel("Speak responses aloud")
        tts_desc.setProperty("class", "muted")

        tts_text = QVBoxLayout()
        tts_text.setSpacing(2)
        tts_text.addWidget(tts_label)
        tts_text.addWidget(tts_desc)

        self.tts_toggle = AnimatedToggle()
        self.tts_toggle.setChecked(True)

        tts_layout.addLayout(tts_text)
        tts_layout.addStretch()
        tts_layout.addWidget(self.tts_toggle)

        layout.addWidget(tts_row)

        return card

    def _create_ai_section(self) -> Card:
        """Create AI settings section."""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"],
                                  SPACING["lg"])
        layout.setSpacing(SPACING["lg"])

        # Section title
        title = QLabel("🤖 AI Settings")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(title)

        # AI enabled
        ai_row = QWidget()
        ai_layout = QHBoxLayout(ai_row)
        ai_layout.setContentsMargins(0, 0, 0, 0)

        ai_label = QLabel("AI Responses")
        ai_desc = QLabel("Use Groq AI for intelligent responses")
        ai_desc.setProperty("class", "muted")

        ai_text = QVBoxLayout()
        ai_text.setSpacing(2)
        ai_text.addWidget(ai_label)
        ai_text.addWidget(ai_desc)

        self.ai_toggle = AnimatedToggle()
        self.ai_toggle.setChecked(True)

        ai_layout.addLayout(ai_text)
        ai_layout.addStretch()
        ai_layout.addWidget(self.ai_toggle)

        layout.addWidget(ai_row)

        # API Key input
        api_row = QWidget()
        api_layout = QVBoxLayout(api_row)
        api_layout.setContentsMargins(0, 0, 0, 0)
        api_layout.setSpacing(SPACING["sm"])

        api_label = QLabel("Groq API Key")
        api_desc = QLabel("Enter your API key from console.groq.com")
        api_desc.setProperty("class", "muted")

        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("gsk_...")
        self.api_input.setEchoMode(QLineEdit.Password)

        api_layout.addWidget(api_label)
        api_layout.addWidget(api_desc)
        api_layout.addWidget(self.api_input)

        layout.addWidget(api_row)

        return card

    def _create_web_section(self) -> Card:
        """Create web scraping settings section."""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"],
                                  SPACING["lg"])
        layout.setSpacing(SPACING["lg"])

        # Section title
        title = QLabel("🌐 Web Features")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(title)

        # Web scraping mode toggle
        web_row = QWidget()
        web_layout = QHBoxLayout(web_row)
        web_layout.setContentsMargins(0, 0, 0, 0)

        web_label = QLabel("Web Scraping Mode")
        web_desc = QLabel(
            "Enable advanced web features (Wikipedia, weather, news, YouTube, etc.)"
        )
        web_desc.setProperty("class", "muted")

        web_text = QVBoxLayout()
        web_text.setSpacing(2)
        web_text.addWidget(web_label)
        web_text.addWidget(web_desc)

        self.web_scraping_toggle = AnimatedToggle()
        self.web_scraping_toggle.setChecked(True)  # Default to enabled

        web_layout.addLayout(web_text)
        web_layout.addStretch()
        web_layout.addWidget(self.web_scraping_toggle)

        layout.addWidget(web_row)

        return card

    def _create_about_section(self) -> Card:
        """Create about section."""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"],
                                  SPACING["lg"])
        layout.setSpacing(SPACING["md"])

        # Section title
        title = QLabel("ℹ️ About")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(title)

        # App info
        info = QLabel("<b>VocalXpert</b> v2.0.0<br><br>"
                      "An intelligent AI voice assistant.<br><br>"
                      "<b>Created by:</b><br>"
                      "• Ghulam Murtaza<br>"
                      "• Capt. Asim Iqbal<br>"
                      "• Capt. Bilal Zaib<br>"
                      "• Huzaifa Kahut<br><br>"
                      "<b>Technologies:</b><br>"
                      "Python, PySide6, Groq AI, SpeechRecognition")
        info.setProperty("class", "muted")
        info.setWordWrap(True)
        info.setOpenExternalLinks(True)

        layout.addWidget(info)

        return card

    def get_settings(self) -> dict:
        """Get all current settings."""
        return {
            "dark_mode": self.dark_mode_toggle.isChecked(),
            "voice_input": self.voice_toggle.isChecked(),
            "voice_output": self.tts_toggle.isChecked(),
            "speech_rate": self.rate_slider.value(),
            "ai_enabled": self.ai_toggle.isChecked(),
            "api_key": self.api_input.text(),
            "web_scraping_enabled": self.web_scraping_toggle.isChecked(),
        }

    def load_settings(self, settings: dict):
        """Load settings from dict."""
        if "dark_mode" in settings:
            self.dark_mode_toggle.setChecked(settings["dark_mode"])
        if "voice_input" in settings:
            self.voice_toggle.setChecked(settings["voice_input"])
        if "voice_output" in settings:
            self.tts_toggle.setChecked(settings["voice_output"])
        if "speech_rate" in settings:
            self.rate_slider.setValue(settings["speech_rate"])
        if "ai_enabled" in settings:
            self.ai_toggle.setChecked(settings["ai_enabled"])
        if "api_key" in settings:
            self.api_input.setText(settings["api_key"])
        if "web_scraping_enabled" in settings:
            self.web_scraping_toggle.setChecked(
                settings["web_scraping_enabled"])
