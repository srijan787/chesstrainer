# ai/styles.py
# Loads trained weight vectors from data/weights/
# and provides them to the bot selector at runtime.

import json
import os

BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
WEIGHTS_DIR = os.path.join(BASE_DIR, "data", "weights")

# Style metadata — displayed in the UI
STYLE_INFO = {
    "aggressive": {
        "name":        "Aggressive",
        "description": "Seeks captures and active piece play. "
                       "Attacks relentlessly and sacrifices material for initiative.",
        "emoji":       "⚔️",
    },
    "defensive": {
        "name":        "Defensive",
        "description": "Prioritises king safety and solid structure. "
                       "Avoids unnecessary risks and waits for opponent mistakes.",
        "emoji":       "🛡️",
    },
    "positional": {
        "name":        "Positional",
        "description": "Focuses on piece placement and long-term advantages. "
                       "Controls the centre and outmanoeuvres opponents slowly.",
        "emoji":       "♟️",
    },
}


def load_style(style: str) -> dict:
    """
    Load a trained weight vector for the given style.
    Returns the weights dict, or default weights if file not found.
    """
    path = os.path.join(WEIGHTS_DIR, f"{style}.json")
    if not os.path.exists(path):
        print(f"[styles] Warning: no trained weights found for "
              f"'{style}'. Using defaults.")
        return {"material": 1.0, "position": 1.0, "mobility": 1.0}

    with open(path, "r") as f:
        data = json.load(f)
    return data["weights"]


def load_all_styles() -> dict:
    """Load all three style weight vectors. Returns dict keyed by style name."""
    return {style: load_style(style) for style in STYLE_INFO}


def get_style_names() -> list:
    """Return list of available style names."""
    return list(STYLE_INFO.keys())


def get_style_display_name(style: str) -> str:
    """Return the human-readable name for a style."""
    return STYLE_INFO.get(style, {}).get("name", style.title())


def get_style_description(style: str) -> str:
    """Return the description for a style."""
    return STYLE_INFO.get(style, {}).get("description", "")