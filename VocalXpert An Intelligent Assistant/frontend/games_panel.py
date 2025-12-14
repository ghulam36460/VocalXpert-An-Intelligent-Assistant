"""
Games Panel - Fun interactive games

Rock Paper Scissors, Dice Roll, Coin Flip, and more.
"""

import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QStackedWidget,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from .components import Card, FeatureCard, IconButton
from .themes import FONTS, SPACING, get_theme


class GamesPanel(QWidget):
    """
    Games selection and play panel.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the games interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["xl"])
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Games stack (selection / game)
        self.stack = QStackedWidget()
        
        # Game selection page
        selection_page = self._create_selection_page()
        self.stack.addWidget(selection_page)
        
        # RPS game page
        self.rps_game = RPSGame()
        self.rps_game.back_clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.rps_game)
        
        # Dice game page
        self.dice_game = DiceGame()
        self.dice_game.back_clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.dice_game)
        
        # Coin game page
        self.coin_game = CoinGame()
        self.coin_game.back_clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.coin_game)
        
        layout.addWidget(self.stack, 1)
    
    def _create_header(self) -> QWidget:
        """Create games header."""
        header = QFrame()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, SPACING["lg"])
        
        title = QLabel("🎮 Games")
        title.setFont(QFont(FONTS["family"], FONTS["size_2xl"], FONTS["weight_bold"]))
        
        subtitle = QLabel("Take a break and have some fun!")
        subtitle.setProperty("class", "muted")
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header
    
    def _create_selection_page(self) -> QWidget:
        """Create game selection grid."""
        page = QWidget()
        layout = QGridLayout(page)
        layout.setSpacing(SPACING["lg"])
        
        games = [
            ("✊✋✌️", "Rock Paper Scissors", "Classic hand game", 1),
            ("🎲", "Dice Roll", "Roll the dice!", 2),
            ("🪙", "Coin Flip", "Heads or tails?", 3),
        ]
        
        for i, (icon, title, desc, idx) in enumerate(games):
            card = FeatureCard(icon, title, desc)
            card.clicked.connect(self._make_game_handler(idx))
            layout.addWidget(card, i // 3, i % 3)
        
        layout.setRowStretch(1, 1)
        
        return page
    
    def _make_game_handler(self, index: int):
        """Create a handler function for opening a game."""
        def handler():
            self.stack.setCurrentIndex(index)
        return handler
    
    def open_rps(self):
        """Open Rock Paper Scissors game."""
        self.stack.setCurrentIndex(1)
        self.rps_game.reset()


class RPSGame(QWidget):
    """
    Rock Paper Scissors game.
    """
    
    back_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._user_score = 0
        self._bot_score = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """Build RPS game UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["xl"])
        
        # Back button
        back_row = QHBoxLayout()
        back_btn = QPushButton("← Back to Games")
        back_btn.setProperty("class", "ghost")
        back_btn.clicked.connect(self.back_clicked)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)
        
        # Title
        title = QLabel("✊✋✌️ Rock Paper Scissors")
        title.setFont(QFont(FONTS["family"], FONTS["size_xl"], FONTS["weight_bold"]))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Score card
        score_card = Card()
        score_layout = QHBoxLayout(score_card)
        score_layout.setContentsMargins(SPACING["xl"], SPACING["lg"], SPACING["xl"], SPACING["lg"])
        
        # User score
        user_score_layout = QVBoxLayout()
        user_label = QLabel("You")
        user_label.setAlignment(Qt.AlignCenter)
        self.user_score_label = QLabel("0")
        self.user_score_label.setFont(QFont(FONTS["family"], 48, FONTS["weight_bold"]))
        self.user_score_label.setAlignment(Qt.AlignCenter)
        theme = get_theme()
        self.user_score_label.setStyleSheet(f"color: {theme.success};")
        user_score_layout.addWidget(user_label)
        user_score_layout.addWidget(self.user_score_label)
        
        # VS
        vs_label = QLabel("VS")
        vs_label.setFont(QFont(FONTS["family"], FONTS["size_xl"], FONTS["weight_bold"]))
        vs_label.setAlignment(Qt.AlignCenter)
        vs_label.setProperty("class", "muted")
        
        # Bot score
        bot_score_layout = QVBoxLayout()
        bot_label = QLabel("Bot")
        bot_label.setAlignment(Qt.AlignCenter)
        self.bot_score_label = QLabel("0")
        self.bot_score_label.setFont(QFont(FONTS["family"], 48, FONTS["weight_bold"]))
        self.bot_score_label.setAlignment(Qt.AlignCenter)
        self.bot_score_label.setStyleSheet(f"color: {theme.error};")
        bot_score_layout.addWidget(bot_label)
        bot_score_layout.addWidget(self.bot_score_label)
        
        score_layout.addLayout(user_score_layout, 1)
        score_layout.addWidget(vs_label)
        score_layout.addLayout(bot_score_layout, 1)
        
        layout.addWidget(score_card)
        
        # Result area
        self.result_label = QLabel("Choose your move!")
        self.result_label.setFont(QFont(FONTS["family"], FONTS["size_lg"]))
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)
        
        # Emoji display
        emoji_layout = QHBoxLayout()
        
        self.user_emoji = QLabel("❓")
        self.user_emoji.setFont(QFont(FONTS["family"], 72))
        self.user_emoji.setAlignment(Qt.AlignCenter)
        
        self.vs_emoji = QLabel("⚔️")
        self.vs_emoji.setFont(QFont(FONTS["family"], 32))
        self.vs_emoji.setAlignment(Qt.AlignCenter)
        
        self.bot_emoji = QLabel("❓")
        self.bot_emoji.setFont(QFont(FONTS["family"], 72))
        self.bot_emoji.setAlignment(Qt.AlignCenter)
        
        emoji_layout.addWidget(self.user_emoji, 1)
        emoji_layout.addWidget(self.vs_emoji)
        emoji_layout.addWidget(self.bot_emoji, 1)
        
        layout.addLayout(emoji_layout)
        
        # Choice buttons
        choice_layout = QHBoxLayout()
        choice_layout.setSpacing(SPACING["lg"])
        
        choices = [("✊", "Rock"), ("✋", "Paper"), ("✌️", "Scissors")]
        
        for emoji, name in choices:
            btn = QPushButton(emoji)
            btn.setFont(QFont(FONTS["family"], 32))
            btn.setFixedSize(100, 100)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(self._make_play_handler(name))
            choice_layout.addWidget(btn)
        
        layout.addLayout(choice_layout)
        layout.addStretch()
    
    def _make_play_handler(self, choice: str):
        """Create handler for play button."""
        def handler():
            self._play(choice)
        return handler
    
    def _play(self, user_choice: str):
        """Play a round."""
        choices = ["Rock", "Paper", "Scissors"]
        emojis = {"Rock": "✊", "Paper": "✋", "Scissors": "✌️"}
        
        bot_choice = random.choice(choices)
        
        # Update emojis
        self.user_emoji.setText(emojis[user_choice])
        self.bot_emoji.setText(emojis[bot_choice])
        
        # Determine winner
        if user_choice == bot_choice:
            result = "It's a tie! 🤝"
        elif (
            (user_choice == "Rock" and bot_choice == "Scissors") or
            (user_choice == "Paper" and bot_choice == "Rock") or
            (user_choice == "Scissors" and bot_choice == "Paper")
        ):
            result = "You win! 🎉"
            self._user_score += 1
            self.user_score_label.setText(str(self._user_score))
        else:
            result = "Bot wins! 🤖"
            self._bot_score += 1
            self.bot_score_label.setText(str(self._bot_score))
        
        self.result_label.setText(f"{user_choice} vs {bot_choice} - {result}")
    
    def reset(self):
        """Reset the game."""
        self._user_score = 0
        self._bot_score = 0
        self.user_score_label.setText("0")
        self.bot_score_label.setText("0")
        self.result_label.setText("Choose your move!")
        self.user_emoji.setText("❓")
        self.bot_emoji.setText("❓")


class DiceGame(QWidget):
    """
    Dice rolling game.
    """
    
    back_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build dice game UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["xl"])
        
        # Back button
        back_row = QHBoxLayout()
        back_btn = QPushButton("← Back to Games")
        back_btn.setProperty("class", "ghost")
        back_btn.clicked.connect(self.back_clicked)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)
        
        # Title
        title = QLabel("🎲 Dice Roll")
        title.setFont(QFont(FONTS["family"], FONTS["size_xl"], FONTS["weight_bold"]))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Dice display
        self.dice_label = QLabel("🎲")
        self.dice_label.setFont(QFont(FONTS["family"], 120))
        self.dice_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.dice_label)
        
        # Result
        self.result_label = QLabel("Click to roll!")
        self.result_label.setFont(QFont(FONTS["family"], FONTS["size_xl"]))
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)
        
        layout.addStretch()
        
        # Roll button
        roll_btn = QPushButton("🎲  Roll Dice")
        roll_btn.setFont(QFont(FONTS["family"], FONTS["size_lg"]))
        roll_btn.setMinimumHeight(60)
        roll_btn.clicked.connect(self._roll)
        layout.addWidget(roll_btn)
    
    def _roll(self):
        """Roll the dice with animation."""
        dice_faces = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        
        # Animate
        self._animation_count = 0
        self._final_value = random.randint(1, 6)
        
        def animate():
            self._animation_count += 1
            if self._animation_count < 10:
                self.dice_label.setText(random.choice(dice_faces))
                QTimer.singleShot(100, animate)
            else:
                self.dice_label.setText(dice_faces[self._final_value - 1])
                self.result_label.setText(f"You rolled: {self._final_value}!")
        
        animate()


class CoinGame(QWidget):
    """
    Coin flip game.
    """
    
    back_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Build coin game UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING["xl"])
        
        # Back button
        back_row = QHBoxLayout()
        back_btn = QPushButton("← Back to Games")
        back_btn.setProperty("class", "ghost")
        back_btn.clicked.connect(self.back_clicked)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)
        
        # Title
        title = QLabel("🪙 Coin Flip")
        title.setFont(QFont(FONTS["family"], FONTS["size_xl"], FONTS["weight_bold"]))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Coin display
        self.coin_label = QLabel("🪙")
        self.coin_label.setFont(QFont(FONTS["family"], 120))
        self.coin_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.coin_label)
        
        # Result
        self.result_label = QLabel("Click to flip!")
        self.result_label.setFont(QFont(FONTS["family"], FONTS["size_xl"]))
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)
        
        layout.addStretch()
        
        # Flip button
        flip_btn = QPushButton("🪙  Flip Coin")
        flip_btn.setFont(QFont(FONTS["family"], FONTS["size_lg"]))
        flip_btn.setMinimumHeight(60)
        flip_btn.clicked.connect(self._flip)
        layout.addWidget(flip_btn)
    
    def _flip(self):
        """Flip the coin with animation."""
        # Animate
        self._animation_count = 0
        self._final_value = random.choice(["Heads", "Tails"])
        
        def animate():
            self._animation_count += 1
            if self._animation_count < 10:
                self.coin_label.setText(random.choice(["🪙", "⭕"]))
                QTimer.singleShot(100, animate)
            else:
                if self._final_value == "Heads":
                    self.coin_label.setText("👑")
                else:
                    self.coin_label.setText("🦅")
                self.result_label.setText(f"It's {self._final_value}!")
        
        animate()
