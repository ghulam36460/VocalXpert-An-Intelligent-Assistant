"""
Features Panel - Quick access to all features

Dashboard with feature cards for weather, news, system controls, etc.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .components import Card, FeatureCard
from .themes import FONTS, SPACING, get_theme


class FeaturesPanel(QWidget):
    """
    Features dashboard panel.
    """

    feature_clicked = Signal(str)  # Emits command string

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Build the features interface."""
        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)

        # Content
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"],
                                  SPACING["xl"])
        layout.setSpacing(SPACING["xl"])

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Weather card (larger)
        weather_card = self._create_weather_card()
        layout.addWidget(weather_card)

        # Information section
        info_label = QLabel("📚 Information")
        info_label.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(info_label)

        info_grid = self._create_info_grid()
        layout.addWidget(info_grid)

        # Productivity section
        productivity_label = QLabel("📝 Productivity")
        productivity_label.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(productivity_label)

        productivity_grid = self._create_productivity_grid()
        layout.addWidget(productivity_grid)

        # Media section
        media_label = QLabel("🎬 Media & Entertainment")
        media_label.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(media_label)

        media_grid = self._create_media_grid()
        layout.addWidget(media_grid)

        # System controls
        system_label = QLabel("⚙️ System Controls")
        system_label.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(system_label)

        system_grid = self._create_system_grid()
        layout.addWidget(system_grid)

        # Applications section
        apps_label = QLabel("📱 Applications")
        apps_label.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        layout.addWidget(apps_label)

        apps_grid = self._create_apps_grid()
        layout.addWidget(apps_grid)

        layout.addStretch()

        scroll.setWidget(content)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_header(self) -> QWidget:
        """Create features header."""
        header = QFrame()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, SPACING["lg"])

        title = QLabel("✨ Features")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_2xl"], FONTS["weight_bold"]))

        subtitle = QLabel(
            "Quick access to all VocalXpert capabilities - click any card or use voice commands"
        )
        subtitle.setProperty("class", "muted")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        return header

    def _create_weather_card(self) -> Card:
        """Create weather display card."""
        card = Card(hover=True)
        card.setCursor(Qt.PointingHandCursor)
        card.mousePressEvent = lambda e: self.feature_clicked.emit("weather")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"],
                                  SPACING["xl"])

        # Weather icon
        icon = QLabel("🌤️")
        icon.setFont(QFont(FONTS["family"], 48))

        # Weather info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(SPACING["xs"])

        title = QLabel("Weather")
        title.setFont(
            QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))

        self.weather_text = QLabel("Click to check current weather")
        self.weather_text.setProperty("class", "muted")

        info_layout.addWidget(title)
        info_layout.addWidget(self.weather_text)

        layout.addWidget(icon)
        layout.addSpacing(SPACING["lg"])
        layout.addLayout(info_layout, 1)

        return card

    def _create_info_grid(self) -> QWidget:
        """Create information features grid."""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(SPACING["md"])
        layout.setContentsMargins(0, 0, 0, 0)

        features = [
            ("📰", "News", "Latest headlines", "latest news"),
            ("🔍", "Google Search", "Search the web", "search google for"),
            ("📖", "Wikipedia", "Knowledge lookup", "wikipedia"),
            ("⏰", "Time", "Current time", "what time is it"),
            ("📅", "Date", "this date", "what is the date"),
            ("📚", "Dictionary", "Word definitions",
             "dictionary meaning of word"),
            ("😂", "Jokes", "Tell me a joke", "tell me a joke"),
            ("🗺️", "Maps", "Open Google Maps", "open maps"),
            ("📍", "Directions", "Get directions", "directions to"),
        ]

        for i, (icon, title, desc, cmd) in enumerate(features):
            card = FeatureCard(icon, title, desc)
            card.clicked.connect(self._make_handler(cmd))
            layout.addWidget(card, i // 3, i % 3)

        return container

    def _create_productivity_grid(self) -> QWidget:
        """Create productivity features grid."""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(SPACING["md"])
        layout.setContentsMargins(0, 0, 0, 0)

        features = [
            ("📝", "To-Do List", "View your tasks", "show my to do list"),
            ("➕", "Add Task", "Add to your list", "add to my list"),
            ("⏲️", "Set Timer", "Set a timer", "set timer for 5 minutes"),
            ("🧮", "Calculator", "Math operations", "calculate 5 plus 3"),
            ("📄", "Create File", "Make new files", "create text file"),
            ("🌐", "HTML Project", "Create web project", "create html project"),
            ("✉️", "Send Email", "Compose email", "send email"),
            ("💬", "WhatsApp", "Send message", "send whatsapp"),
            ("🌍", "Translate", "Translate text", "translate hello to spanish"),
        ]

        for i, (icon, title, desc, cmd) in enumerate(features):
            card = FeatureCard(icon, title, desc)
            card.clicked.connect(self._make_handler(cmd))
            layout.addWidget(card, i // 3, i % 3)

        return container

    def _create_media_grid(self) -> QWidget:
        """Create media features grid."""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(SPACING["md"])
        layout.setContentsMargins(0, 0, 0, 0)

        features = [
            ("▶️", "YouTube", "Play videos", "play on youtube"),
            ("🎲", "Dice Roll", "Roll the dice", "roll a dice"),
            ("🪙", "Coin Flip", "Flip a coin", "flip a coin"),
            ("✊", "Rock Paper Scissors", "Play RPS",
             "play rock paper scissors"),
            ("🖼️", "Download Images", "Get images", "download images of"),
            ("🎵", "Music", "Play music", "open spotify"),
        ]

        for i, (icon, title, desc, cmd) in enumerate(features):
            card = FeatureCard(icon, title, desc)
            card.clicked.connect(self._make_handler(cmd))
            layout.addWidget(card, i // 3, i % 3)

        return container

    def _create_system_grid(self) -> QWidget:
        """Create system controls grid."""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(SPACING["md"])
        layout.setContentsMargins(0, 0, 0, 0)

        controls = [
            ("🔊", "Volume Up", "Increase volume", "volume up"),
            ("🔉", "Volume Down", "Decrease volume", "volume down"),
            ("🔇", "Mute", "Toggle mute", "mute"),
            ("📸", "Screenshot", "Capture screen", "take screenshot"),
            ("🔒", "Lock PC", "Lock computer", "lock pc"),
            ("💻", "System Info", "View specs", "system info"),
            ("🔋", "Battery", "Battery status", "battery status"),
            ("😴", "Sleep", "Sleep computer", "sleep pc"),
            ("🔄", "Restart", "Restart PC", "restart pc"),
        ]

        for i, (icon, title, desc, cmd) in enumerate(controls):
            card = FeatureCard(icon, title, desc)
            card.clicked.connect(self._make_handler(cmd))
            layout.addWidget(card, i // 3, i % 3)

        return container

    def _create_apps_grid(self) -> QWidget:
        """Create applications grid."""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setSpacing(SPACING["md"])
        layout.setContentsMargins(0, 0, 0, 0)

        apps = [
            ("📁", "File Explorer", "Open files", "open explorer"),
            ("🌐", "Chrome", "Web browser", "open chrome"),
            ("📝", "Notepad", "Text editor", "open notepad"),
            ("🖥️", "VS Code", "Code editor", "open vs code"),
            ("🎨", "Paint", "Drawing app", "open paint"),
            ("📊", "Excel", "Spreadsheets", "open excel"),
            ("📄", "Word", "Documents", "open word"),
            ("💼", "PowerPoint", "Presentations", "open powerpoint"),
            ("🧮", "Calculator", "Calculator app", "open calculator"),
        ]

        for i, (icon, title, desc, cmd) in enumerate(apps):
            card = FeatureCard(icon, title, desc)
            card.clicked.connect(self._make_handler(cmd))
            layout.addWidget(card, i // 3, i % 3)

        return container

    def _make_handler(self, cmd: str):
        """Create a handler function for the given command."""

        def handler():
            self.feature_clicked.emit(cmd)

        return handler

    def update_weather(self, weather_text: str):
        """Update weather display."""
        self.weather_text.setText(weather_text)
