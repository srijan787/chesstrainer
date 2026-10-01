# game/ladder.py
# Challenge ladder logic

import os
from game.rating import get_rating, get_completed_rungs, mark_rung_complete

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

LADDER = [
    {
        "rung":        1,
        "bot":         "aggressive_easy",
        "style":       "aggressive",
        "bot_elo":     1091,
        "label":       "The Brawler",
        "description": "An aggressive bot that loves to attack. Beat it to get started.",
        "unlock_at":   0,
        "reward":      "You beat The Brawler! Next challenge unlocked.",
    },
    {
        "rung":        2,
        "bot":         "defensive_easy",
        "style":       "defensive",
        "bot_elo":     1130,
        "label":       "The Turtle",
        "description": "A cautious bot that waits for your mistakes. Patience is key.",
        "unlock_at":   1100,
        "reward":      "You cracked The Turtle! Keep going.",
    },
    {
        "rung":        3,
        "bot":         "positional_easy",
        "style":       "positional",
        "bot_elo":     1106,
        "label":       "The Schemer",
        "description": "A positional bot that slowly outmanoeuvres you. Control the centre.",
        "unlock_at":   1100,
        "reward":      "The Schemer is beaten! Your positional play is improving.",
    },
    {
        "rung":        4,
        "bot":         "aggressive_medium",
        "style":       "aggressive",
        "bot_elo":     1150,
        "label":       "The Berserker",
        "description": "A stronger aggressive bot. It will sacrifice material for attacks.",
        "unlock_at":   1150,
        "reward":      "The Berserker falls! Your defence is solid.",
    },
    {
        "rung":        5,
        "bot":         "defensive_medium",
        "style":       "defensive",
        "bot_elo":     1124,
        "label":       "The Fortress",
        "description": "A solid defensive bot. You need to find weaknesses in its structure.",
        "unlock_at":   1150,
        "reward":      "The Fortress is breached! Excellent play.",
    },
    {
        "rung":        6,
        "bot":         "positional_medium",
        "style":       "positional",
        "bot_elo":     1161,
        "label":       "The Strategist",
        "description": "A medium positional bot. It will slowly squeeze you if you let it.",
        "unlock_at":   1200,
        "reward":      "The Strategist is outplayed! You are improving fast.",
    },
    {
        "rung":        7,
        "bot":         "aggressive_hard",
        "style":       "aggressive",
        "bot_elo":     1293,
        "label":       "The Blitzer",
        "description": "A strong aggressive bot. Expect sharp, tactical games.",
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
        "description": "The strongest positional bot. Every move must count.",
        "unlock_at":   1250,
        "reward":      "The Grandmaster is defeated! You have mastered ChessTrainer.",
    },
]


def get_available_rungs(username: str) -> list:
    rating = get_rating(username)
    return [r for r in LADDER if rating >= r["unlock_at"]]


def get_next_rung(username: str) -> dict:
    completed = get_completed_rungs(username)
    available = get_available_rungs(username)
    incomplete = [r for r in available if r["rung"] not in completed]
    return incomplete[0] if incomplete else None


def get_ladder_progress(username: str) -> dict:
    completed = get_completed_rungs(username)
    rating    = get_rating(username)
    available = get_available_rungs(username)
    return {
        "total":           len(LADDER),
        "completed":       len(completed),
        "available":       len(available),
        "locked":          len(LADDER) - len(available),
        "rungs":           LADDER,
        "completed_rungs": completed,
    }


def check_and_award(username: str, bot_name: str,
                    result: str) -> str:
    if result != "win":
        return ""
    for rung in LADDER:
        if rung["bot"] == bot_name:
            completed = get_completed_rungs(username)
            if rung["rung"] not in completed:
                mark_rung_complete(username, rung["rung"])
                return rung["reward"]
    return ""