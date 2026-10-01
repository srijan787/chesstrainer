# game/rating.py
# Tracks each user's ELO rating and game history.
# Each user has their own file in data/users/<username>.json

import json
import os
import hashlib
from datetime import datetime

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
USERS_DIR  = os.path.join(BASE_DIR, "data", "users")

DEFAULT_RATING = 1200
K_FACTOR       = 32


# ── PIN hashing ───────────────────────────────────────────────

def hash_pin(pin: str) -> str:
    """Hash a PIN so we never store it in plain text."""
    return hashlib.sha256(pin.encode()).hexdigest()


# ── ELO math ──────────────────────────────────────────────────

def expected_score(player_elo: float, opponent_elo: float) -> float:
    return 1.0 / (1.0 + 10 ** ((opponent_elo - player_elo) / 400))


def new_rating(player_elo: float, opponent_elo: float,
               result: str) -> float:
    actual = {"win": 1.0, "draw": 0.5, "loss": 0.0}[result]
    exp    = expected_score(player_elo, opponent_elo)
    return round(player_elo + K_FACTOR * (actual - exp), 1)


# ── User file helpers ─────────────────────────────────────────

def user_file(username: str) -> str:
    """Return path to a user's data file."""
    os.makedirs(USERS_DIR, exist_ok=True)
    return os.path.join(USERS_DIR, f"{username.lower()}.json")


def user_exists(username: str) -> bool:
    return os.path.exists(user_file(username))


def get_all_users() -> list:
    """Return list of all registered usernames."""
    os.makedirs(USERS_DIR, exist_ok=True)
    return [f.replace(".json", "")
            for f in os.listdir(USERS_DIR)
            if f.endswith(".json")]


def _default_data(username: str, pin: str) -> dict:
    return {
        "username":       username,
        "pin_hash":       hash_pin(pin),
        "rating":         DEFAULT_RATING,
        "games_played":   0,
        "wins":           0,
        "losses":         0,
        "draws":          0,
        "history":        [],
        "rating_history": [
            {"rating": DEFAULT_RATING, "date": _today()}
        ],
        "completed_rungs": [],
    }


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ── User management ───────────────────────────────────────────

def create_user(username: str, pin: str) -> bool:
    """
    Create a new user. Returns True if successful,
    False if username already exists.
    """
    if user_exists(username):
        return False
    data = _default_data(username, pin)
    with open(user_file(username), "w") as f:
        json.dump(data, f, indent=2)
    return True


def verify_pin(username: str, pin: str) -> bool:
    """Return True if PIN matches stored hash."""
    if not user_exists(username):
        return False
    with open(user_file(username)) as f:
        data = json.load(f)
    return data.get("pin_hash") == hash_pin(pin)


def load_user(username: str) -> dict:
    """Load a user's data. Raises FileNotFoundError if not found."""
    with open(user_file(username)) as f:
        return json.load(f)


def save_user(data: dict):
    """Save user data back to file."""
    with open(user_file(data["username"]), "w") as f:
        json.dump(data, f, indent=2)


# ── Game recording ────────────────────────────────────────────

def record_game(username: str, bot_name: str,
                bot_elo: int, bot_style: str,
                result: str) -> dict:
    """Record a completed game and update player rating."""
    data       = load_user(username)
    old_rating = data["rating"]
    updated    = new_rating(old_rating, bot_elo, result)

    data["rating"]       = updated
    data["games_played"] += 1
    if result == "win":
        data["wins"]   += 1
    elif result == "loss":
        data["losses"] += 1
    else:
        data["draws"]  += 1

    data["history"].append({
        "date":           _today(),
        "bot":            bot_name,
        "bot_elo":        bot_elo,
        "style":          bot_style,
        "result":         result,
        "rating_before":  old_rating,
        "rating_after":   updated,
        "change":         round(updated - old_rating, 1),
    })

    data["rating_history"].append({
        "rating": updated,
        "date":   _today(),
    })

    save_user(data)
    return data


# ── Stats helpers ─────────────────────────────────────────────

def get_stats(username: str) -> dict:
    data = load_user(username)
    return {
        "rating":       data["rating"],
        "games_played": data["games_played"],
        "wins":         data["wins"],
        "losses":       data["losses"],
        "draws":        data["draws"],
        "win_rate":     round(data["wins"] / data["games_played"] * 100, 1)
                        if data["games_played"] > 0 else 0,
    }


def get_rating(username: str) -> float:
    return load_user(username)["rating"]


def get_rating_history(username: str) -> list:
    return load_user(username)["rating_history"]


def get_recent_games(username: str, n: int = 10) -> list:
    return load_user(username)["history"][-n:]


def get_completed_rungs(username: str) -> list:
    return load_user(username).get("completed_rungs", [])


def mark_rung_complete(username: str, rung: int):
    data = load_user(username)
    if "completed_rungs" not in data:
        data["completed_rungs"] = []
    if rung not in data["completed_rungs"]:
        data["completed_rungs"].append(rung)
    save_user(data)