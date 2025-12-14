"""
Custom UI Components for VocalXpert

Reusable, styled widgets for the modern UI.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, 
    QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QPainterPath

from .themes import FONTS, RADIUS, SPACING, get_theme


class Card(QWidget):
    """
    A styled card container with optional shadow and hover effects.
    """
    
    def __init__(self, parent=None, shadow=False, hover=False):
        super().__init__(parent)
        self.setProperty("class", "card")
        # self.setFrameShape(QFrame.StyledPanel)
        
        if shadow:
            # self._add_shadow()
            pass
        
        self._hover_enabled = hover
        if hover:
            self.setCursor(Qt.PointingHandCursor)
    
    # def _add_shadow(self):
    #     """Add drop shadow effect."""
    #     shadow = QGraphicsDropShadowEffect(self)
    #     shadow.setBlurRadius(20)
    #     shadow.setColor(QColor(0, 0, 0, 30))
    #     shadow.setOffset(0, 4)
    #     self.setGraphicsEffect(shadow)
    
    def enterEvent(self, event):
        if self._hover_enabled:
            shadow = self.graphicsEffect()
            if shadow:
                shadow.setBlurRadius(30)
                shadow.setOffset(0, 8)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if self._hover_enabled:
            shadow = self.graphicsEffect()
            if shadow:
                shadow.setBlurRadius(20)
                shadow.setOffset(0, 4)
        super().leaveEvent(event)


class IconButton(QPushButton):
    """
    A circular button with an icon or emoji.
    """
    
    def __init__(self, icon_text: str = "", size: int = 44, parent=None):
        super().__init__(parent)
        self.setProperty("class", "icon")
        self.setText(icon_text)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont(FONTS["family"], size // 2))


class NavButton(QPushButton):
    """
    A sidebar navigation button with icon and text.
    """
    
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.setProperty("class", "nav-item")
        self.setText(f"  {icon}  {text}")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
    
    def set_active(self, active: bool):
        """Set the active state."""
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class MessageBubble(QFrame):
    """
    A chat message bubble with proper styling for user/bot messages.
    """
    
    def __init__(self, text: str, is_user: bool = False, parent=None):
        super().__init__(parent)
        
        self.setProperty("class", "message-user" if is_user else "message-bot")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["sm"], SPACING["md"], SPACING["sm"])
        
        # Message text
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        theme = get_theme()
        if is_user:
            self.label.setStyleSheet(f"color: {theme.chat_user_text}; background: transparent;")
        else:
            self.label.setStyleSheet(f"color: {theme.chat_bot_text}; background: transparent;")
        
        layout.addWidget(self.label)
        
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMaximumWidth(500)


class ChatInput(QWidget):
    """
    A styled chat input with send button and voice button.
    """
    
    message_sent = Signal(str)
    voice_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["sm"])
        
        # Voice button
        self.voice_btn = IconButton("🎤", 44)
        self.voice_btn.setToolTip("Voice Input")
        self.voice_btn.clicked.connect(self.voice_clicked)
        
        # Text input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message or press 🎤 to speak...")
        self.input_field.setMinimumHeight(44)
        self.input_field.returnPressed.connect(self._send_message)
        
        # Send button
        self.send_btn = IconButton("➤", 44)
        self.send_btn.setToolTip("Send Message")
        self.send_btn.clicked.connect(self._send_message)
        
        layout.addWidget(self.voice_btn)
        layout.addWidget(self.input_field, 1)
        layout.addWidget(self.send_btn)
    
    def _send_message(self):
        """Send the current message."""
        text = self.input_field.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_field.clear()
    
    def set_voice_active(self, active: bool):
        """Toggle voice button appearance."""
        if active:
            self.voice_btn.setText("🔴")
            self.voice_btn.setToolTip("Stop Voice Mode")
        else:
            self.voice_btn.setText("🎤")
            self.voice_btn.setToolTip("Voice Mode (Continuous)")
    
    def setEnabled(self, enabled: bool):
        """Enable/disable the input."""
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)


class StatusBar(QFrame):
    """
    A status bar showing AI status, connection state, etc.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["xs"], SPACING["md"], SPACING["xs"])
        
        # Status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setFont(QFont(FONTS["family"], 10))
        
        # Status text
        self.status_text = QLabel("Ready")
        self.status_text.setProperty("class", "muted")
        
        # Connection indicator
        self.connection_label = QLabel("🌐 Online")
        self.connection_label.setProperty("class", "muted")
        
        layout.addWidget(self.status_dot)
        layout.addWidget(self.status_text)
        layout.addStretch()
        layout.addWidget(self.connection_label)
        
        self.set_status("ready")
    
    def set_status(self, status: str, text: str = None):
        """Update status indicator."""
        theme = get_theme()
        
        status_config = {
            "ready": ("●", theme.success, "Ready"),
            "listening": ("●", theme.warning, "Listening..."),
            "processing": ("●", theme.info, "Processing..."),
            "speaking": ("●", theme.info, "Speaking..."),
            "error": ("●", theme.error, "Error"),
            "offline": ("●", theme.text_muted, "Offline"),
        }
        
        config = status_config.get(status, status_config["ready"])
        self.status_dot.setText(config[0])
        self.status_dot.setStyleSheet(f"color: {config[1]}; background: transparent;")
        self.status_text.setText(text or config[2])
    
    def set_connection(self, online: bool):
        """Update connection status."""
        if online:
            self.connection_label.setText("🌐 Online")
        else:
            self.connection_label.setText("📵 Offline")


class FeatureCard(Card):
    """
    A feature card with icon, title, and description.
    """
    
    clicked = Signal()
    
    def __init__(self, icon: str, title: str, description: str, parent=None):
        super().__init__(parent, shadow=True, hover=True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont(FONTS["family"], 32))
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel(title)
        title_label.setProperty("class", "subtitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        
        # Description
        desc_label = QLabel(description)
        desc_label.setProperty("class", "muted")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
        self.setFixedSize(180, 160)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class AnimatedToggle(QWidget):
    """
    A modern animated toggle switch.
    """
    
    toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._checked = False
        self._handle_position = 3
        
        self.setFixedSize(52, 28)
        self.setCursor(Qt.PointingHandCursor)
        
        # Animation
        self._animation = QPropertyAnimation(self, b"handle_position", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def get_handle_position(self):
        return self._handle_position
    
    def set_handle_position(self, pos):
        self._handle_position = pos
        self.update()
    
    handle_position = Property(float, get_handle_position, set_handle_position)
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, checked: bool):
        if checked != self._checked:
            self._checked = checked
            self._animate_toggle()
            self.toggled.emit(checked)
    
    def _animate_toggle(self):
        self._animation.setStartValue(self._handle_position)
        self._animation.setEndValue(27 if self._checked else 3)
        self._animation.start()
    
    def mousePressEvent(self, event):
        self.setChecked(not self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        theme = get_theme()
        
        # Background
        bg_color = QColor(theme.primary) if self._checked else QColor(theme.bg_tertiary)
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, 52, 28, 14, 14)
        
        # Handle
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(int(self._handle_position), 3, 22, 22)


class SectionHeader(QWidget):
    """
    A section header with title and optional action button.
    """
    
    action_clicked = Signal()
    
    def __init__(self, title: str, action_text: str = None, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, SPACING["md"], 0, SPACING["sm"])
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(FONTS["family"], FONTS["size_lg"], FONTS["weight_semibold"]))
        
        layout.addWidget(title_label)
        layout.addStretch()
        
        if action_text:
            action_btn = QPushButton(action_text)
            action_btn.setProperty("class", "ghost")
            action_btn.setCursor(Qt.PointingHandCursor)
            action_btn.clicked.connect(self.action_clicked)
            layout.addWidget(action_btn)


class QuickActionButton(QPushButton):
    """
    A quick action button with icon for the chat interface.
    """
    
    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}  {text}")
        self.setProperty("class", "secondary")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)


class FeatureCard(Card):
    """
    A feature card with icon, title, description, and click handling.
    """
    
    clicked = Signal()
    
    def __init__(self, icon: str, title: str, description: str, parent=None):
        super().__init__(parent, shadow=False, hover=True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"])
        layout.setSpacing(SPACING["sm"])
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont(FONTS["family"], FONTS["size_2xl"]))
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(FONTS["family"], FONTS["size_md"], FONTS["weight_semibold"]))
        title_label.setAlignment(Qt.AlignCenter)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setProperty("class", "muted")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
    
    def mousePressEvent(self, event):
        """Handle click events."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
