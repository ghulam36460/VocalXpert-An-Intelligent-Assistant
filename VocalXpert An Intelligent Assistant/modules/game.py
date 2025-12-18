"""
Game Module - Interactive Games for VocalXpert

Provides game logic for:
    - Dice Roll
    - Coin Flip
    - Rock Paper Scissors

The GUI is handled by the PySide6 frontend.
"""

from random import randint, choice
import os

# Game moves
MOVES = ["rock", "paper", "scissors"]
MOVE_EMOJIS = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}


class DiceGame:
    """Simple dice rolling game."""

    def roll(self):
        """Roll a dice and return result."""
        result = randint(1, 6)
        return result, f"🎲 You rolled a {result}!"


class CoinGame:
    """Simple coin flip game."""

    def flip(self):
        """Flip a coin and return result."""
        result = choice(["Heads", "Tails"])
        emoji = "🪙"
        return result, f"{emoji} You got {result}!"


class RockPaperScissors:
    """Rock Paper Scissors game logic."""

    def __init__(self):
        self.player_score = 0
        self.bot_score = 0
        self.rounds_played = 0

    def get_winner(self, player_move, bot_move):
        """Determine the winner of a round."""
        player_move = player_move.lower()
        bot_move = bot_move.lower()

        if player_move == bot_move:
            return "tie"

        wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

        if wins.get(player_move) == bot_move:
            return "player"
        return "bot"

    def play_round(self, player_move):
        """Play a single round.

        Args:
            player_move: 'rock', 'paper', or 'scissors'

        Returns:
            tuple: (bot_move, winner, result_text)
        """
        bot_move = choice(MOVES)
        winner = self.get_winner(player_move, bot_move)
        self.rounds_played += 1

        if winner == "player":
            self.player_score += 1
            result_text = f"You chose {MOVE_EMOJIS.get(player_move, player_move)}, I chose {MOVE_EMOJIS.get(bot_move, bot_move)}. You win! 🎉"
        elif winner == "bot":
            self.bot_score += 1
            result_text = f"You chose {MOVE_EMOJIS.get(player_move, player_move)}, I chose {MOVE_EMOJIS.get(bot_move, bot_move)}. I win! 😎"
        else:
            result_text = f"We both chose {MOVE_EMOJIS.get(player_move, player_move)}. It's a tie! 🤝"

        return bot_move, winner, result_text

    def get_score(self):
        """Get current score."""
        return self.player_score, self.bot_score

    def reset(self):
        """Reset the game."""
        self.player_score = 0
        self.bot_score = 0
        self.rounds_played = 0


# Singleton instances for easy access
_dice = DiceGame()
_coin = CoinGame()
_rps = RockPaperScissors()


def play(query):
    """
    Play a game based on the query.

    Args:
        query: String like "roll dice", "flip coin", etc.

    Returns:
        tuple: (result_value, result_text)
    """
    query = query.lower()

    if any(word in query for word in ["dice", "roll"]):
        return _dice.roll()

    if any(word in query for word in ["coin", "flip", "toss"]):
        return _coin.flip()

    if any(word in query for word in ["rock", "paper", "scissors"]):
        # Extract player move
        player_move = None
        for move in MOVES:
            if move in query:
                player_move = move
                break

        if player_move:
            bot_move, winner, result_text = _rps.play_round(player_move)
            return winner, result_text
        else:
            return None, "Choose rock, paper, or scissors!"

    return (
        None,
        "I don't know that game. Try 'roll dice', 'flip coin', or 'rock paper scissors'!",
    )


def play_rps(player_move):
    """Play a round of Rock Paper Scissors.

    Args:
        player_move: 'rock', 'paper', or 'scissors'

    Returns:
        tuple: (bot_move, winner, result_text, player_score, bot_score)
    """
    bot_move, winner, result_text = _rps.play_round(player_move)
    player_score, bot_score = _rps.get_score()
    return bot_move, winner, result_text, player_score, bot_score


def reset_rps():
    """Reset Rock Paper Scissors scores."""
    _rps.reset()


def get_rps_score():
    """Get current RPS score."""
    return _rps.get_score()
