# game/ladder.py
# Challenge ladder — a structured sequence of bots to beat in order.
# Unlocks as the player's rating climbs.
# Each rung is a specific bot config the player must beat to advance.

import json
import os
from game.rating import load_player_data, save_player_data

BASE_DIR         = os.path.dirname(os.path.dirname(__file__))
PLAYER_DATA_FILE = os.path.join(BASE_DIR, "data", "player_data.json")

# ── Ladder definition ─────────────────────────────────────────
# Each rung: bot to beat, rating required to unlock, reward message
LADDER = [
    {
        "rung":        1,
        "bot":         "aggressive_easy",
        "style":       "aggressive",
        "bot_elo":     1091,
        "label":       "The Brawler",
        "description": "An aggressive bot that loves to attack. "
                       "Beat it to get started.",
        "unlock_at":   0,       # always unlocked
        "reward":      "You beat The Brawler! Next challenge unlocked.",
    },
    {
        "rung":        2,
        "bot":         "defensive_easy",
        "style":       "defensive",
        "bot_elo":     1130,
        "label":       "The Turtle",
        "description": "A cautious bot that waits for your mistakes. "
                       "Patience is key.",
        "unlock_at":   1100,
        "reward":      "You cracked The Turtle! Keep going.",
    },
    {
        "rung":        3,
        "bot":         "positional_easy",
        "style":       "positional",
        "bot_elo":     1106,
        "label":       "The Schemer",
        "description": "A positional bot that slowly outmanoeuvres you. "
                       "Control the centre.",
        "unlock_at":   1100,
        "reward":      "The Schemer is beaten! Your positional play is improving.",
    },
    {
        "rung":        4,
        "bot":         "aggressive_medium",
        "style":       "aggressive",
        "bot_elo":     1150,
        "label":       "The Berserker",
        "description": "A stronger aggressive bot. It will sacrifice "
                       "material for attacks.",
        "unlock_at":   1150,
        "reward":      "The Berserker falls! Your defence is solid.",
    },
    {
        "rung":        5,
        "bot":         "defensive_medium",
        "style":       "defensive",
        "bot_elo":     1124,
        "label":       "The Fortress",
        "description": "A solid defensive bot. You need to find "
                       "weaknesses in its structure.",
        "unlock_at":   1150,
        "reward":      "The Fortress is breached! Excellent play.",
    },
    {
        "rung":        6,
        "bot":         "positional_medium",
        "style":       "positional",
        "bot_elo":     1161,
        "label":       "The Strategist",
        "description": "A medium positional bot. It will slowly "
                       "squeeze you if you let it.",
        "unlock_at":   1200,
        "reward":      "The Strategist is outplayed! You are improving fast.",
    },
    {
        "rung":        7,
        "bot":         "aggressive_hard",
        "style":       "aggressive",
        "bot_elo":     1293,
        "label":       "The Blitzer",
        "description": "A strong aggressive bot. Expect sharp, "
                       "tactical games.",
        "unlock_at":   1200,
        "reward":      "The Blitzer is stopped! Your tactics are sharp.",
    },
    {
        "rung":        8,
        "bot":         "defensive_hard",
        "style":       "defensive",
        "bot_elo":     1291,
        "label":       "The Ironwall",
        "description": "A strong defensive bot. Very hard to break down.",
        "unlock_at":   1250,
        "reward":      "The Ironwall crumbles! Outstanding endgame play.",
    },
    {
        "rung":        9,
        "bot":         "positional_hard",
        "style":       "positional",
        "bot_elo":     1232,
        "label":       "The Grandmaster",
        "description": "The strongest positional bot. "
                       "Every move must count.",
        "unlock_at":   1250,
        "reward":      "The Grandmaster is defeated! You have mastered ChessTrainer.",
    },
]


# ── Ladder state helpers ──────────────────────────────────────

def get_completed_rungs() -> list:
    """Return list of completed rung numbers from player data."""
    data = load_player_data()
    return data.get("completed_rungs", [])


def mark_rung_complete(rung: int):
    """Mark a ladder rung as completed."""
    data = load_player_data()
    if "completed_rungs" not in data:
        data["completed_rungs"] = []
    if rung not in data["completed_rungs"]:
        data["completed_rungs"].append(rung)
    save_player_data(data)


def get_available_rungs(player_rating: float) -> list:
    """Return all rungs the player has unlocked based on their rating."""
    return [r for r in LADDER if player_rating >= r["unlock_at"]]


def get_next_rung(player_rating: float) -> dict:
    """Return the next uncompleted rung the player should attempt."""
    completed  = get_completed_rungs()
    available  = get_available_rungs(player_rating)
    incomplete = [r for r in available if r["rung"] not in completed]
    return incomplete[0] if incomplete else None


def get_ladder_progress(player_rating: float) -> dict:
    """Return a summary of ladder progress."""
    completed = get_completed_rungs()
    available = get_available_rungs(player_rating)
    locked    = [r for r in LADDER if r not in available]
    return {
        "total":     len(LADDER),
        "completed": len(completed),
        "available": len(available),
        "locked":    len(locked),
        "rungs":     LADDER,
        "completed_rungs": completed,
    }


def check_and_award(bot_name: str, result: str,
                    player_rating: float) -> str:
    """
    Check if a completed game finishes a ladder rung.
    If so, mark it complete and return the reward message.
    Returns empty string if no rung was completed.
    """
    if result != "win":
        return ""
    for rung in LADDER:
        if rung["bot"] == bot_name:
            completed = get_completed_rungs()
            if rung["rung"] not in completed:
                mark_rung_complete(rung["rung"])
                return rung["reward"]
    return ""