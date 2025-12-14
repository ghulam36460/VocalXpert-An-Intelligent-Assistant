"""
History Panel - Modern Conversation History Viewer

Displays conversation history with a beautiful, modern UI design.
Features: Search, filtering, date grouping, and smooth animations.
"""

import json
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QPushButton, QTextEdit, QSizePolicy,
    QSplitter, QListWidget, QListWidgetItem, QLineEdit,
    QComboBox, QGraphicsDropShadowEffect, QStackedWidget,
    QGridLayout, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QFont, QColor, QIcon

from .components import Card, SectionHeader
from .themes import FONTS, SPACING, get_theme


class ConversationCard(QFrame):
    """A styled card for displaying a single conversation in the list."""
    
    clicked = Signal(dict)
    
    def __init__(self, conversation: dict, parent=None):
        super().__init__(parent)
        self.conversation = conversation
        self.selected = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the conversation card UI."""
        theme = get_theme()
        
        self.setFixedHeight(90)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style(False)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        
        # Top row: timestamp and source badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        # Time icon and timestamp
        timestamp = self.conversation.get('timestamp', '')[:16]
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_display = dt.strftime("%b %d, %Y • %I:%M %p")
        except:
            time_display = timestamp
            
        time_label = QLabel(f"🕐 {time_display}")
        time_label.setStyleSheet(f"""
            color: {theme.text_muted};
            font-size: 11px;
            font-weight: 500;
        """)
        
        # Source badge
        source = self.conversation.get('source', 'chat')
        source_colors = {
            'voice': (theme.success, '🎤'),
            'text': (theme.info, '💬'),
            'chat': (theme.primary, '💭'),
        }
        badge_color, badge_icon = source_colors.get(source, (theme.text_muted, '📝'))
        
        source_badge = QLabel(f"{badge_icon} {source.upper()}")
        source_badge.setStyleSheet(f"""
            background-color: {badge_color}20;
            color: {badge_color};
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
        """)
        
        top_row.addWidget(time_label)
        top_row.addStretch()
        top_row.addWidget(source_badge)
        
        layout.addLayout(top_row)
        
        # Query preview
        user_query = self.conversation.get('user_query', '')[:80]
        if len(self.conversation.get('user_query', '')) > 80:
            user_query += "..."
            
        query_label = QLabel(user_query)
        query_label.setWordWrap(True)
        query_label.setStyleSheet(f"""
            color: {theme.text_primary};
            font-size: 13px;
            font-weight: 500;
            line-height: 1.4;
        """)
        
        layout.addWidget(query_label)
        layout.addStretch()
        
    def _update_style(self, selected: bool):
        """Update the card style based on selection state."""
        theme = get_theme()
        
        if selected:
            self.setStyleSheet(f"""
                ConversationCard {{
                    background-color: {theme.primary}15;
                    border: 2px solid {theme.primary};
                    border-radius: 12px;
                }}
                ConversationCard:hover {{
                    background-color: {theme.primary}20;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ConversationCard {{
                    background-color: {theme.bg_card};
                    border: 1px solid {theme.border};
                    border-radius: 12px;
                }}
                ConversationCard:hover {{
                    background-color: {theme.bg_tertiary};
                    border-color: {theme.primary}50;
                }}
            """)
            
    def set_selected(self, selected: bool):
        """Set the selection state."""
        self.selected = selected
        self._update_style(selected)
        
    def mousePressEvent(self, event):
        """Handle mouse press."""
        self.clicked.emit(self.conversation)
        super().mousePressEvent(event)


class ConversationDetailView(QFrame):
    """Detailed view of a selected conversation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the detail view UI."""
        theme = get_theme()
        
        self.setStyleSheet(f"""
            ConversationDetailView {{
                background-color: {theme.bg_card};
                border: 1px solid {theme.border};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)
        
        # Empty state (shown when no conversation selected)
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        
        empty_icon = QLabel("📋")
        empty_icon.setStyleSheet("font-size: 48px;")
        empty_icon.setAlignment(Qt.AlignCenter)
        
        empty_text = QLabel("Select a conversation to view details")
        empty_text.setStyleSheet(f"""
            color: {theme.text_muted};
            font-size: 14px;
        """)
        empty_text.setAlignment(Qt.AlignCenter)
        
        empty_layout.addStretch()
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_text)
        empty_layout.addStretch()
        
        # Detail content - wrapped in scroll area
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.detail_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {theme.bg_tertiary};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme.border_light};
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.primary};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.detail_content = QWidget()
        detail_layout = QVBoxLayout(self.detail_content)
        detail_layout.setContentsMargins(0, 0, 8, 0)
        detail_layout.setSpacing(16)
        
        # Header with timestamp
        self.header_label = QLabel()
        self.header_label.setStyleSheet(f"""
            color: {theme.text_muted};
            font-size: 12px;
            font-weight: 500;
        """)
        detail_layout.addWidget(self.header_label)
        
        # User query section
        user_section = self._create_message_section("👤 You", theme.chat_user_bg, theme.chat_user_text, True)
        self.user_query_label = user_section['content']
        detail_layout.addWidget(user_section['widget'])
        
        # AI response section
        ai_section = self._create_message_section("🤖 VocalXpert", theme.chat_bot_bg, theme.text_primary, False)
        self.ai_response_label = ai_section['content']
        detail_layout.addWidget(ai_section['widget'])
        
        # Summary section (optional)
        self.summary_section = QFrame()
        self.summary_section.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.info}10;
                border: 1px solid {theme.info}30;
                border-radius: 12px;
            }}
        """)
        summary_layout = QVBoxLayout(self.summary_section)
        summary_layout.setContentsMargins(16, 12, 16, 12)
        
        summary_header = QLabel("📝 Summary")
        summary_header.setStyleSheet(f"""
            color: {theme.info};
            font-size: 12px;
            font-weight: 600;
        """)
        
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(f"""
            color: {theme.text_secondary};
            font-size: 13px;
            line-height: 1.5;
        """)
        
        summary_layout.addWidget(summary_header)
        summary_layout.addWidget(self.summary_label)
        
        detail_layout.addWidget(self.summary_section)
        detail_layout.addStretch()
        
        self.detail_scroll.setWidget(self.detail_content)
        
        # Stacked widget to switch between empty and detail views
        self.stacked = QStackedWidget()
        self.stacked.addWidget(self.empty_state)
        self.stacked.addWidget(self.detail_scroll)
        
        layout.addWidget(self.stacked)
        
    def _create_message_section(self, title: str, bg_color: str, text_color: str, is_user: bool) -> dict:
        """Create a message section widget."""
        theme = get_theme()
        
        section = QFrame()
        if is_user:
            section.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-radius: 16px;
                    border-top-right-radius: 4px;
                }}
            """)
        else:
            section.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-radius: 16px;
                    border-top-left-radius: 4px;
                }}
            """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        if is_user:
            header = QLabel(title)
            header.setStyleSheet(f"""
                color: {text_color};
                font-size: 11px;
                font-weight: 600;
            """)
        else:
            header = QLabel(title)
            header.setStyleSheet(f"""
                color: {theme.primary};
                font-size: 11px;
                font-weight: 600;
            """)
        
        content = QLabel()
        content.setWordWrap(True)
        content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content.setStyleSheet(f"""
            color: {text_color};
            font-size: 14px;
            line-height: 1.6;
        """)
        
        layout.addWidget(header)
        layout.addWidget(content)
        
        return {'widget': section, 'content': content}
        
    def show_conversation(self, conversation: dict):
        """Display a conversation's details."""
        theme = get_theme()
        
        # Parse timestamp
        timestamp = conversation.get('timestamp', '')
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_display = dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except:
            time_display = timestamp
            
        source = conversation.get('source', 'chat')
        self.header_label.setText(f"📅 {time_display}  •  Source: {source.upper()}")
        
        # User query
        self.user_query_label.setText(conversation.get('user_query', 'No query available'))
        
        # AI response
        self.ai_response_label.setText(conversation.get('ai_response', 'No response available'))
        
        # Summary
        summary = conversation.get('summary', '')
        if summary:
            self.summary_label.setText(summary)
            self.summary_section.show()
        else:
            self.summary_section.hide()
            
        self.stacked.setCurrentIndex(1)
        
    def show_empty(self):
        """Show empty state."""
        self.stacked.setCurrentIndex(0)


class StatsCard(QFrame):
    """A card displaying statistics."""
    
    def __init__(self, icon: str, value: str, label: str, color: str, parent=None):
        super().__init__(parent)
        theme = get_theme()
        
        self.setFixedSize(140, 90)
        self.setStyleSheet(f"""
            StatsCard {{
                background-color: {theme.bg_card};
                border: 1px solid {theme.border};
                border-radius: 12px;
            }}
            StatsCard:hover {{
                border-color: {color};
                background-color: {color}08;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon and value
        value_row = QHBoxLayout()
        value_row.setSpacing(8)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            color: {color};
            font-size: 22px;
            font-weight: 700;
        """)
        
        value_row.addWidget(icon_label)
        value_row.addWidget(value_label)
        value_row.addStretch()
        
        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            color: {theme.text_muted};
            font-size: 11px;
            font-weight: 500;
        """)
        
        layout.addLayout(value_row)
        layout.addWidget(label_widget)


class HistoryPanel(QWidget):
    """
    Modern panel for viewing conversation history with search and filtering.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_data = []
        self.filtered_data = []
        self.conversation_cards = []
        self.selected_card = None
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        """Build the history interface."""
        theme = get_theme()
        
        self.setStyleSheet(f"background-color: {theme.bg_primary};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Stats bar
        stats_bar = self._create_stats_bar()
        layout.addWidget(stats_bar)

        # Main content area
        content = self._create_content()
        layout.addWidget(content, 1)

    def _create_header(self) -> QWidget:
        """Create the modern history header."""
        theme = get_theme()
        
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.bg_secondary};
                border-bottom: 1px solid {theme.border};
            }}
        """)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        layout.setSpacing(16)

        # Top row: Title and actions
        top_row = QHBoxLayout()
        
        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title = QLabel("📚 Conversation History")
        title.setStyleSheet(f"""
            color: {theme.text_primary};
            font-size: 24px;
            font-weight: 700;
        """)
        
        subtitle = QLabel("Browse and search your past conversations")
        subtitle.setStyleSheet(f"""
            color: {theme.text_muted};
            font-size: 13px;
        """)
        
        title_section.addWidget(title)
        title_section.addWidget(subtitle)
        
        top_row.addLayout(title_section)
        top_row.addStretch()

        # Action buttons
        action_row = QHBoxLayout()
        action_row.setSpacing(12)
        
        # Export button
        export_btn = QPushButton("📥 Export")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.bg_tertiary};
                color: {theme.text_secondary};
                border: 1px solid {theme.border};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {theme.bg_input};
                border-color: {theme.primary}50;
            }}
        """)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.primary};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {theme.primary_hover};
            }}
        """)
        refresh_btn.clicked.connect(self._load_history)
        
        action_row.addWidget(export_btn)
        action_row.addWidget(refresh_btn)
        
        top_row.addLayout(action_row)
        layout.addLayout(top_row)
        
        # Search and filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search conversations...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.bg_input};
                border: 1px solid {theme.border};
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 13px;
                color: {theme.text_primary};
            }}
            QLineEdit:focus {{
                border-color: {theme.primary};
            }}
        """)
        self.search_input.textChanged.connect(self._filter_conversations)
        
        # Source filter
        self.source_filter = QComboBox()
        self.source_filter.addItems(["All Sources", "💭 Chat", "🎤 Voice", "💬 Text"])
        self.source_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {theme.bg_input};
                border: 1px solid {theme.border};
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 13px;
                color: {theme.text_primary};
                min-width: 130px;
            }}
            QComboBox:focus {{
                border-color: {theme.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme.bg_card};
                border: 1px solid {theme.border};
                border-radius: 8px;
                selection-background-color: {theme.primary}30;
                color: {theme.text_primary};
            }}
        """)
        self.source_filter.currentIndexChanged.connect(self._filter_conversations)
        
        # Date filter
        self.date_filter = QComboBox()
        self.date_filter.addItems(["All Time", "Today", "Last 7 Days", "Last 30 Days"])
        self.date_filter.setStyleSheet(self.source_filter.styleSheet())
        self.date_filter.currentIndexChanged.connect(self._filter_conversations)
        
        filter_row.addWidget(self.search_input, 1)
        filter_row.addWidget(self.source_filter)
        filter_row.addWidget(self.date_filter)
        
        layout.addLayout(filter_row)

        return header

    def _create_stats_bar(self) -> QWidget:
        """Create the statistics bar."""
        theme = get_theme()
        
        stats_bar = QFrame()
        stats_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.bg_secondary};
                border-bottom: 1px solid {theme.border};
            }}
        """)
        
        layout = QHBoxLayout(stats_bar)
        layout.setContentsMargins(SPACING["xl"], SPACING["md"], SPACING["xl"], SPACING["md"])
        layout.setSpacing(16)
        
        # Stats cards will be added dynamically
        self.stats_container = QHBoxLayout()
        self.stats_container.setSpacing(12)
        
        layout.addLayout(self.stats_container)
        layout.addStretch()
        
        return stats_bar

    def _create_content(self) -> QWidget:
        """Create the main content area with conversation list and details."""
        theme = get_theme()
        
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        layout.setSpacing(20)

        # Left panel: Conversations list
        left_panel = QFrame()
        left_panel.setMinimumWidth(360)
        left_panel.setMaximumWidth(420)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.bg_secondary};
                border: 1px solid {theme.border};
                border-radius: 16px;
            }}
        """)
        
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)
        
        # List header
        list_header = QHBoxLayout()
        
        self.list_title = QLabel("💬 Recent Conversations")
        self.list_title.setStyleSheet(f"""
            color: {theme.text_primary};
            font-size: 14px;
            font-weight: 600;
        """)
        
        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet(f"""
            background-color: {theme.primary}20;
            color: {theme.primary};
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
        """)
        
        list_header.addWidget(self.list_title)
        list_header.addStretch()
        list_header.addWidget(self.count_badge)
        
        left_layout.addLayout(list_header)
        
        # Scrollable conversation list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {theme.bg_tertiary};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme.border_light};
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.primary};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 8, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.list_container)
        left_layout.addWidget(scroll_area)
        
        # Right panel: Conversation details
        self.detail_view = ConversationDetailView()
        
        layout.addWidget(left_panel)
        layout.addWidget(self.detail_view, 1)

        return content

    def _load_history(self):
        """Load conversation history from JSON file."""
        try:
            history_file = os.path.join("userData", "conversation_history.json")

            if not os.path.exists(history_file):
                self._show_empty_state()
                return

            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            conversations = data.get('conversations', [])
            # Reverse to show newest first
            self.history_data = list(reversed(conversations[-100:]))
            self.filtered_data = self.history_data.copy()

            # Update UI
            self._update_conversation_list()
            self._update_stats(data.get('metadata', {}), len(conversations))

        except Exception as e:
            self._show_error_state(f"Error loading history: {str(e)}")

    def _update_conversation_list(self):
        """Update the conversation list with current filtered data."""
        theme = get_theme()
        
        # Clear existing cards
        for card in self.conversation_cards:
            card.deleteLater()
        self.conversation_cards.clear()
        self.selected_card = None
        
        # Clear layout
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.filtered_data:
            # Show empty state in list
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignCenter)
            
            empty_icon = QLabel("🔍")
            empty_icon.setStyleSheet("font-size: 32px;")
            empty_icon.setAlignment(Qt.AlignCenter)
            
            empty_label = QLabel("No conversations found")
            empty_label.setStyleSheet(f"""
                color: {theme.text_muted};
                font-size: 13px;
            """)
            empty_label.setAlignment(Qt.AlignCenter)
            
            empty_hint = QLabel("Try adjusting your filters")
            empty_hint.setStyleSheet(f"""
                color: {theme.text_muted};
                font-size: 11px;
            """)
            empty_hint.setAlignment(Qt.AlignCenter)
            
            empty_layout.addSpacing(40)
            empty_layout.addWidget(empty_icon)
            empty_layout.addWidget(empty_label)
            empty_layout.addWidget(empty_hint)
            empty_layout.addStretch()
            
            self.list_layout.addWidget(empty_widget)
            self.detail_view.show_empty()
            self.count_badge.setText("0")
            return
        
        # Add conversation cards
        for i, conv in enumerate(self.filtered_data):
            card = ConversationCard(conv)
            card.clicked.connect(self._on_conversation_selected)
            self.conversation_cards.append(card)
            self.list_layout.addWidget(card)
            
            # Select first card by default
            if i == 0:
                card.set_selected(True)
                self.selected_card = card
                self.detail_view.show_conversation(conv)
        
        self.list_layout.addStretch()
        self.count_badge.setText(str(len(self.filtered_data)))

    def _on_conversation_selected(self, conversation: dict):
        """Handle conversation selection."""
        # Find and update the selected card
        for card in self.conversation_cards:
            if card.conversation == conversation:
                if self.selected_card:
                    self.selected_card.set_selected(False)
                card.set_selected(True)
                self.selected_card = card
                break
        
        self.detail_view.show_conversation(conversation)

    def _filter_conversations(self):
        """Filter conversations based on search and filter criteria."""
        search_text = self.search_input.text().lower()
        source_filter = self.source_filter.currentText()
        date_filter = self.date_filter.currentText()
        
        self.filtered_data = []
        
        for conv in self.history_data:
            # Search filter
            if search_text:
                query = conv.get('user_query', '').lower()
                response = conv.get('ai_response', '').lower()
                if search_text not in query and search_text not in response:
                    continue
            
            # Source filter
            if source_filter != "All Sources":
                source = conv.get('source', '')
                if source_filter == "💭 Chat" and source != 'chat':
                    continue
                elif source_filter == "🎤 Voice" and source != 'voice':
                    continue
                elif source_filter == "💬 Text" and source != 'text':
                    continue
            
            # Date filter
            if date_filter != "All Time":
                try:
                    timestamp = conv.get('timestamp', '')
                    conv_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    now = datetime.now()
                    
                    if date_filter == "Today":
                        if conv_date.date() != now.date():
                            continue
                    elif date_filter == "Last 7 Days":
                        if (now - conv_date).days > 7:
                            continue
                    elif date_filter == "Last 30 Days":
                        if (now - conv_date).days > 30:
                            continue
                except:
                    pass
            
            self.filtered_data.append(conv)
        
        self._update_conversation_list()

    def _update_stats(self, metadata: dict, total_count: int):
        """Update statistics display."""
        theme = get_theme()
        
        # Clear existing stats
        while self.stats_container.count():
            item = self.stats_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Calculate stats
        total_convs = total_count
        
        # Count by source
        voice_count = sum(1 for c in self.history_data if c.get('source') == 'voice')
        text_count = sum(1 for c in self.history_data if c.get('source') in ['text', 'chat'])
        
        # Today's count
        today = datetime.now().date()
        today_count = 0
        for conv in self.history_data:
            try:
                timestamp = conv.get('timestamp', '')
                conv_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                if conv_date == today:
                    today_count += 1
            except:
                pass
        
        # Add stats cards
        stats = [
            ("📊", str(total_convs), "Total Chats", theme.primary),
            ("📅", str(today_count), "Today", theme.success),
            ("🎤", str(voice_count), "Voice", theme.warning),
            ("💬", str(text_count), "Text", theme.info),
        ]
        
        for icon, value, label, color in stats:
            card = StatsCard(icon, value, label, color)
            self.stats_container.addWidget(card)

    def _show_empty_state(self):
        """Show empty state when no history is available."""
        self.history_data = []
        self.filtered_data = []
        self._update_conversation_list()
        self._update_stats({}, 0)

    def _show_error_state(self, error_msg: str):
        """Show error state."""
        theme = get_theme()
        self.history_data = []
        self.filtered_data = []
        self._update_conversation_list()
        
        # Show error in detail view
        self.detail_view.show_empty()
