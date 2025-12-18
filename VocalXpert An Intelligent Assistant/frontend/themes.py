"""
Modern Theme System for VocalXpert

Defines color schemes, fonts, and styling constants for the application.
Supports dark/light mode with smooth transitions.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """Theme configuration container."""

    name: str

    # Main colors
    primary: str
    primary_hover: str
    primary_light: str
    secondary: str
    accent: str

    # Background colors
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    bg_card: str
    bg_input: str

    # Text colors
    text_primary: str
    text_secondary: str
    text_muted: str
    text_inverse: str

    # Status colors
    success: str
    warning: str
    error: str
    info: str

    # Border and shadow
    border: str
    border_light: str
    shadow: str

    # Sidebar
    sidebar_bg: str
    sidebar_hover: str
    sidebar_active: str

    # Chat
    chat_user_bg: str
    chat_bot_bg: str
    chat_user_text: str
    chat_bot_text: str


# Dark Theme - Modern Deep Purple/Blue
DARK_THEME = Theme(
    name="dark",
    # Main colors
    primary="#6366f1",  # Indigo
    primary_hover="#818cf8",
    primary_light="#4f46e5",
    secondary="#8b5cf6",  # Violet
    accent="#f472b6",  # Pink
    # Background colors
    bg_primary="#0f0f1a",  # Very dark blue-black
    bg_secondary="#1a1a2e",  # Dark blue
    bg_tertiary="#16213e",  # Navy
    bg_card="#1e1e32",  # Card background
    bg_input="#252540",  # Input background
    # Text colors
    text_primary="#f8fafc",  # Almost white
    text_secondary="#cbd5e1",  # Light gray
    text_muted="#64748b",  # Muted gray
    text_inverse="#0f172a",  # Dark for light backgrounds
    # Status colors
    success="#22c55e",  # Green
    warning="#f59e0b",  # Amber
    error="#ef4444",  # Red
    info="#3b82f6",  # Blue
    # Border and shadow
    border="#2d2d4a",
    border_light="#3d3d5c",
    shadow="rgba(0, 0, 0, 0.3)",
    # Sidebar
    sidebar_bg="#12121f",
    sidebar_hover="#1e1e32",
    sidebar_active="#6366f1",
    # Chat
    chat_user_bg="#6366f1",
    chat_bot_bg="#1e1e32",
    chat_user_text="#ffffff",
    chat_bot_text="#f8fafc",
)

# Light Theme - Clean and Modern
LIGHT_THEME = Theme(
    name="light",
    # Main colors
    primary="#6366f1",
    primary_hover="#4f46e5",
    primary_light="#818cf8",
    secondary="#8b5cf6",
    accent="#ec4899",
    # Background colors
    bg_primary="#ffffff",
    bg_secondary="#f8fafc",
    bg_tertiary="#f1f5f9",
    bg_card="#ffffff",
    bg_input="#f1f5f9",
    # Text colors
    text_primary="#1e293b",
    text_secondary="#475569",
    text_muted="#2c3b4f",
    text_inverse="#1c3249",
    # Status colors
    success="#16a34a",
    warning="#d97706",
    error="#dc2626",
    info="#2563eb",
    # Border and shadow
    border="#e2e8f0",
    border_light="#f1f5f9",
    shadow="rgba(0, 0, 0, 0.1)",
    # Sidebar
    sidebar_bg="#f8fafc",
    sidebar_hover="#e2e8f0",
    sidebar_active="#6366f1",
    # Chat
    chat_user_bg="#6366f1",
    chat_bot_bg="#7b7e80",
    chat_user_text="#ffffff",
    chat_bot_text="#1e293b",
)

# Font configuration
FONTS = {
    "family": "Segoe UI, SF Pro Display, -apple-system, sans-serif",
    "family_mono": "Consolas, Monaco, 'Courier New', monospace",
    "size_xs": 11,
    "size_sm": 12,
    "size_md": 14,
    "size_lg": 16,
    "size_xl": 18,
    "size_2xl": 24,
    "size_3xl": 32,
    "weight_normal": 400,
    "weight_medium": 500,
    "weight_semibold": 600,
    "weight_bold": 700,
}

# Animation durations (ms)
ANIMATIONS = {
    "fast": 150,
    "normal": 250,
    "slow": 400,
}

# Border radius
RADIUS = {
    "sm": 4,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "full": 9999,
}

# Spacing
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
    "3xl": 48,
}


def get_theme(theme_name: str = "dark") -> Theme:
    """Get theme by name."""
    return DARK_THEME if theme_name == "dark" else LIGHT_THEME


def generate_stylesheet(theme: Theme) -> str:
    """Generate complete QSS stylesheet for the theme."""
    return f"""
    /* ============================================= */
    /* VocalXpert Modern Theme - {theme.name.upper()} */
    /* ============================================= */

    /* Global styles */
    * {{
        font-family: {FONTS['family']};
        font-size: {FONTS['size_md']}px;
    }}

    QMainWindow, QWidget {{
        background-color: {theme.bg_primary};
        color: {theme.text_primary};
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {theme.bg_secondary};
        width: 8px;
        margin: 0;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical {{
        background: {theme.border_light};
        min-height: 30px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {theme.text_muted};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background: {theme.bg_secondary};
        height: 8px;
        margin: 0;
        border-radius: 4px;
    }}

    QScrollBar::handle:horizontal {{
        background: {theme.border_light};
        min-width: 30px;
        border-radius: 4px;
    }}

    /* Labels */
    QLabel {{
        color: {theme.text_primary};
        background: transparent;
    }}

    QLabel[class="title"] {{
        font-size: {FONTS['size_2xl']}px;
        font-weight: {FONTS['weight_bold']};
    }}

    QLabel[class="subtitle"] {{
        font-size: {FONTS['size_lg']}px;
        color: {theme.text_secondary};
    }}

    QLabel[class="muted"] {{
        color: {theme.text_muted};
        font-size: {FONTS['size_sm']}px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {theme.primary};
        color: {theme.text_inverse};
        border: none;
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['sm']}px {SPACING['lg']}px;
        font-weight: {FONTS['weight_semibold']};
        font-size: {FONTS['size_md']}px;
    }}

    QPushButton:hover {{
        background-color: {theme.primary_hover};
    }}

    QPushButton:pressed {{
        background-color: {theme.primary_light};
    }}

    QPushButton:disabled {{
        background-color: {theme.bg_tertiary};
        color: {theme.text_muted};
    }}

    QPushButton[class="secondary"] {{
        background-color: {theme.bg_tertiary};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
    }}

    QPushButton[class="secondary"]:hover {{
        background-color: {theme.bg_secondary};
        border-color: {theme.primary};
    }}

    QPushButton[class="ghost"] {{
        background-color: transparent;
        color: {theme.text_primary};
    }}

    QPushButton[class="ghost"]:hover {{
        background-color: {theme.bg_tertiary};
    }}

    QPushButton[class="icon"] {{
        background-color: transparent;
        border-radius: {RADIUS['full']}px;
        padding: {SPACING['sm']}px;
        min-width: 40px;
        min-height: 40px;
    }}

    QPushButton[class="icon"]:hover {{
        background-color: {theme.bg_tertiary};
    }}

    QPushButton[class="danger"] {{
        background-color: {theme.error};
    }}

    QPushButton[class="danger"]:hover {{
        background-color: #dc2626;
    }}

    /* Line Edit / Input */
    QLineEdit {{
        background-color: {theme.bg_input};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        font-size: {FONTS['size_md']}px;
        selection-background-color: {theme.primary};
    }}

    QLineEdit:focus {{
        border-color: {theme.primary};
        background-color: {theme.bg_card};
    }}

    QLineEdit:disabled {{
        background-color: {theme.bg_tertiary};
        color: {theme.text_muted};
    }}

    /* Text Edit / Text Area */
    QTextEdit, QPlainTextEdit {{
        background-color: {theme.bg_input};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['sm']}px;
        selection-background-color: {theme.primary};
    }}

    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {theme.primary};
    }}

    /* Combo Box */
    QComboBox {{
        background-color: {theme.bg_input};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['sm']}px {SPACING['md']}px;
        min-width: 120px;
    }}

    QComboBox:hover {{
        border-color: {theme.primary};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {theme.text_secondary};
        margin-right: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {theme.bg_card};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['md']}px;
        selection-background-color: {theme.primary};
        padding: {SPACING['xs']}px;
    }}

    /* Checkbox */
    QCheckBox {{
        color: {theme.text_primary};
        spacing: {SPACING['sm']}px;
    }}

    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 2px solid {theme.border};
        border-radius: {RADIUS['sm']}px;
        background-color: {theme.bg_input};
    }}

    QCheckBox::indicator:checked {{
        background-color: {theme.primary};
        border-color: {theme.primary};
    }}

    QCheckBox::indicator:hover {{
        border-color: {theme.primary};
    }}

    /* Slider */
    QSlider::groove:horizontal {{
        background: {theme.bg_tertiary};
        height: 6px;
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: {theme.primary};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {theme.primary_hover};
    }}

    QSlider::sub-page:horizontal {{
        background: {theme.primary};
        border-radius: 3px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {theme.bg_tertiary};
        border: none;
        border-radius: {RADIUS['sm']}px;
        height: 8px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {theme.primary};
        border-radius: {RADIUS['sm']}px;
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['md']}px;
    }}

    QTabBar::tab {{
        background-color: {theme.bg_tertiary};
        color: {theme.text_secondary};
        padding: {SPACING['sm']}px {SPACING['lg']}px;
        margin-right: 2px;
        border-top-left-radius: {RADIUS['md']}px;
        border-top-right-radius: {RADIUS['md']}px;
    }}

    QTabBar::tab:selected {{
        background-color: {theme.bg_card};
        color: {theme.primary};
        font-weight: {FONTS['weight_semibold']};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {theme.bg_secondary};
    }}

    /* Group Box */
    QGroupBox {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['md']}px;
        margin-top: 16px;
        padding-top: 16px;
        font-weight: {FONTS['weight_semibold']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        padding: 0 8px;
        color: {theme.text_primary};
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {theme.bg_card};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['sm']}px;
        padding: {SPACING['xs']}px {SPACING['sm']}px;
    }}

    /* Menu */
    QMenu {{
        background-color: {theme.bg_card};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['xs']}px;
    }}

    QMenu::item {{
        padding: {SPACING['sm']}px {SPACING['lg']}px;
        border-radius: {RADIUS['sm']}px;
    }}

    QMenu::item:selected {{
        background-color: {theme.primary};
        color: {theme.text_inverse};
    }}

    /* Sidebar Navigation Button */
    QPushButton[class="nav-item"] {{
        background-color: transparent;
        color: {theme.text_secondary};
        border: none;
        border-radius: {RADIUS['md']}px;
        padding: {SPACING['md']}px;
        text-align: left;
        font-size: {FONTS['size_md']}px;
    }}

    QPushButton[class="nav-item"]:hover {{
        background-color: {theme.sidebar_hover};
        color: {theme.text_primary};
    }}

    QPushButton[class="nav-item"][active="true"] {{
        background-color: {theme.sidebar_active};
        color: {theme.text_inverse};
        font-weight: {FONTS['weight_semibold']};
    }}

    /* Chat Message Bubble */
    QWidget[class="message-user"] {{
        background-color: {theme.chat_user_bg};
        border-radius: {RADIUS['lg']}px;
        border-bottom-right-radius: {RADIUS['sm']}px;
    }}

    QWidget[class="message-bot"] {{
        background-color: {theme.chat_bot_bg};
        border-radius: {RADIUS['lg']}px;
        border-bottom-left-radius: {RADIUS['sm']}px;
    }}

    /* Card */
    QWidget[class="card"] {{
        background-color: {theme.bg_card};
        border: 1px solid {theme.border};
        border-radius: {RADIUS['lg']}px;
    }}

    /* Status Indicator */
    QLabel[class="status-online"] {{
        color: {theme.success};
    }}

    QLabel[class="status-offline"] {{
        color: {theme.error};
    }}

    QLabel[class="status-listening"] {{
        color: {theme.warning};
    }}
    """
