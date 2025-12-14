"""
Chat Panel - Main conversation interface

The primary chat interface with message history, input, and quick actions.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from .components import (
    Card, MessageBubble, ChatInput, StatusBar,
    QuickActionButton, SectionHeader
)
from .themes import FONTS, SPACING, get_theme

# Import system prompt from ai_chat module
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.ai_chat import SYSTEM_PROMPT


class ChatPanel(QWidget):
    """
    Main chat interface panel.
    """
    
    message_sent = Signal(str)
    voice_clicked = Signal()
    quick_action = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._messages = []
    
    def _setup_ui(self):
        """Build the chat interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Chat area
        chat_container = self._create_chat_area()
        layout.addWidget(chat_container, 1)
        
        # Quick actions
        quick_actions = self._create_quick_actions()
        layout.addWidget(quick_actions)
        
        # Input area
        input_area = self._create_input_area()
        layout.addWidget(input_area)
        
        # Status bar
        self.status_bar = StatusBar()
        layout.addWidget(self.status_bar)
    
    def _create_header(self) -> QWidget:
        """Create the chat header."""
        header = QFrame()
        theme = get_theme()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.bg_secondary};
                border-bottom: 1px solid {theme.border};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(SPACING["xl"], SPACING["md"], SPACING["xl"], SPACING["md"])
        
        # Title
        title = QLabel("💬 Chat")
        title.setFont(QFont(FONTS["family"], FONTS["size_xl"], FONTS["weight_bold"]))
        
        # Subtitle
        subtitle = QLabel("Ask me anything!")
        subtitle.setProperty("class", "muted")
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        layout.addStretch()
        
        return header
    
    def _create_chat_area(self) -> QScrollArea:
        """Create the scrollable chat message area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Message container
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        self.message_layout.setSpacing(SPACING["md"])
        self.message_layout.addStretch()
        
        scroll.setWidget(self.message_container)
        self.scroll_area = scroll
        
        # Add welcome message
        self._add_system_prompt()
        
        return scroll
    
    def _add_system_prompt(self):
        """Add system prompt display."""
        prompt_card = Card()
        prompt_layout = QVBoxLayout(prompt_card)
        prompt_layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])

        # System prompt icon
        icon = QLabel("🤖")
        icon.setFont(QFont(FONTS["family"], 48))
        icon.setAlignment(Qt.AlignCenter)

        # System prompt title
        title = QLabel("System Prompt")
        title.setFont(QFont(FONTS["family"], FONTS["size_2xl"], FONTS["weight_bold"]))
        title.setAlignment(Qt.AlignCenter)

        # System prompt text (truncated for display)
        prompt_text = SYSTEM_PROMPT[:500] + "..." if len(SYSTEM_PROMPT) > 500 else SYSTEM_PROMPT
        text = QLabel(prompt_text)
        text.setProperty("class", "muted")
        text.setAlignment(Qt.AlignLeft)
        text.setWordWrap(True)
        text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 10px; line-height: 1.4;")

        prompt_layout.addWidget(icon)
        prompt_layout.addWidget(title)
        prompt_layout.addSpacing(SPACING["md"])
        prompt_layout.addWidget(text)

        # Insert before the stretch
        self.message_layout.insertWidget(self.message_layout.count() - 1, prompt_card)
        self.system_prompt_card = prompt_card
    
    def _create_quick_actions(self) -> QWidget:
        """Create quick action buttons."""
        container = QWidget()
        theme = get_theme()
        container.setStyleSheet(f"background-color: {theme.bg_primary};")
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(SPACING["xl"], SPACING["sm"], SPACING["xl"], SPACING["sm"])
        layout.setSpacing(SPACING["sm"])
        
        actions = [
            ("⏰", "Time", "what time is it"),
            ("🌤️", "Weather", "what's the weather"),
            ("📰", "News", "latest news"),
            ("🎲", "Dice", "roll a dice"),
            ("🎮", "RPS", "play rock paper scissors"),
        ]
        
        for icon, text, command in actions:
            btn = QuickActionButton(icon, text)
            # Use a helper to create proper handler
            btn.clicked.connect(self._make_quick_action_handler(command))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        return container
    
    def _make_quick_action_handler(self, command: str):
        """Create handler for quick action button."""
        def handler():
            self.quick_action.emit(command)
        return handler
    
    def _create_input_area(self) -> QWidget:
        """Create the message input area."""
        container = QWidget()
        theme = get_theme()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.bg_secondary};
                border-top: 1px solid {theme.border};
            }}
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(SPACING["xl"], SPACING["md"], SPACING["xl"], SPACING["md"])
        
        self.chat_input = ChatInput()
        self.chat_input.message_sent.connect(self.message_sent)
        self.chat_input.voice_clicked.connect(self.voice_clicked)
        
        layout.addWidget(self.chat_input)
        
        return container
    
    def add_message(self, text: str, is_user: bool = False):
        """Add a message to the chat."""
        # Hide welcome card after first real message
        if hasattr(self, 'welcome_card') and self.welcome_card.isVisible():
            self.welcome_card.hide()
        
        # Create message bubble
        bubble = MessageBubble(text, is_user)
        
        # Create container for alignment
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()
        
        # Insert before the stretch
        self.message_layout.insertWidget(self.message_layout.count() - 1, container)
        self._messages.append(container)
        
        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)
    
    def _scroll_to_bottom(self):
        """Scroll chat to the bottom."""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_status(self, status: str, text: str = None):
        """Update the status bar."""
        self.status_bar.set_status(status, text)
    
    def set_voice_active(self, active: bool):
        """Toggle voice button state."""
        self.chat_input.set_voice_active(active)
    
    def clear_chat(self):
        """Clear all messages."""
        for msg in self._messages:
            msg.deleteLater()
        self._messages.clear()
        
        # Show welcome card again
        if hasattr(self, 'welcome_card'):
            self.welcome_card.show()
