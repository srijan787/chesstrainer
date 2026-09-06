# game/rating.py
# Tracks the player's ELO rating over time.
# Updates rating after each game using the standard ELO formula.
# Stores history in data/player_data.json

import json
import os
from datetime import datetime

BASE_DIR         = os.path.dirname(os.path.dirname(__file__))
PLAYER_DATA_FILE = os.path.join(BASE_DIR, "data", "player_data.json")

# Starting ELO for a new player
DEFAULT_RATING = 1200
K_FACTOR       = 32   # how much each game affects rating


# ── ELO math ──────────────────────────────────────────────────

def expected_score(player_elo: float, opponent_elo: float) -> float:
    """Expected score for player against opponent."""
    return 1.0 / (1.0 + 10 ** ((opponent_elo - player_elo) / 400))


def new_rating(player_elo: float, opponent_elo: float,
               result: str) -> float:
    """
    Calculate new player ELO after a game.
    result: 'win', 'loss', or 'draw'
    """
    actual = {"win": 1.0, "draw": 0.5, "loss": 0.0}[result]
    exp    = expected_score(player_elo, opponent_elo)
    return round(player_elo + K_FACTOR * (actual - exp), 1)


# ── Player data ───────────────────────────────────────────────

def load_player_data() -> dict:
    """Load player data from file. Creates default if not found."""
    if not os.path.exists(PLAYER_DATA_FILE):
        return _default_player_data()
    with open(PLAYER_DATA_FILE, "r") as f:
        data = json.load(f)
    # Handle empty file
    if not data:
        return _default_player_data()
    return data


def save_player_data(data: dict):
    """Save player data to file."""
    os.makedirs(os.path.dirname(PLAYER_DATA_FILE), exist_ok=True)
    with open(PLAYER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _default_player_data() -> dict:
    """Return a fresh player data structure."""
    return {
        "rating":       DEFAULT_RATING,
        "games_played": 0,
        "wins":         0,
        "losses":       0,
        "draws":        0,
        "history":      [],   # list of game records
        "rating_history": [   # for plotting progress chart
            {"rating": DEFAULT_RATING, "date": _today()}
        ],
    }


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── Record a game ─────────────────────────────────────────────

def record_game(bot_name: str, bot_elo: int,
                bot_style: str, result: str) -> dict:
    """
    Record a completed game and update player rating.

    bot_name:  e.g. 'aggressive_hard'
    bot_elo:   calibrated ELO of the bot
    bot_style: 'aggressive', 'defensive', or 'positional'
    result:    'win', 'loss', or 'draw'

    Returns updated player data dict.
    """
    data       = load_player_data()
    old_rating = data["rating"]
    updated    = new_rating(old_rating, bot_elo, result)

    # Update counters
    data["rating"]       = updated
    data["games_played"] += 1
    if result == "win":
        data["wins"]    += 1
    elif result == "loss":
        data["losses"]  += 1
    else:
        data["draws"]   += 1

    # Add game record
    data["history"].append({
        "date":       _today(),
        "bot":        bot_name,
        "bot_elo":    bot_elo,
        "style":      bot_style,
        "result":     result,
        "rating_before": old_rating,
        "rating_after":  updated,
        "change":     round(updated - old_rating, 1),
    })

    # Add to rating history for chart
    data["rating_history"].append({
        "rating": updated,
        "date":   _today(),
    })

    save_player_data(data)
    return data


# ── Display helpers ───────────────────────────────────────────

def get_rating() -> float:
    """Return current player rating."""
    return load_player_data()["rating"]


def get_stats() -> dict:
    """Return player stats summary."""
    data = load_player_data()
    return {
        "rating":       data["rating"],
        "games_played": data["games_played"],
        "wins":         data["wins"],
        "losses":       data["losses"],
        "draws":        data["draws"],
        "win_rate":     round(data["wins"] / data["games_played"] * 100, 1)
                        if data["games_played"] > 0 else 0,
    }


def get_rating_history() -> list:
    """Return list of rating history entries for charting."""
    return load_player_data()["rating_history"]


def get_recent_games(n: int = 10) -> list:
    """Return the N most recent game records."""
    history = load_player_data()["history"]
    return history[-n:]


def reset_player_data():
    """Reset all player data back to defaults."""
    save_player_data(_default_player_data())
    print("Player data reset.")