# ai/calibration.py
# ELO calibration engine.
# Runs a tournament between our evolved bots (at various depths/imprecision)
# and fixed-depth "reference bots" to estimate real-world ELO ratings.
#
# Reference ELO anchors (approximate, based on community testing):
#   depth=1, imprecision=1.0  ≈  800  ELO  (very weak, random-ish)
#   depth=1, imprecision=0.5  ≈  1000 ELO
#   depth=1, imprecision=0.0  ≈  1200 ELO
#   depth=2, imprecision=0.5  ≈  1400 ELO
#   depth=2, imprecision=0.0  ≈  1600 ELO
#   depth=3, imprecision=0.0  ≈  1800 ELO  (strong for a simple engine)

import json
import os
import math
import random
from engine.board import Board
from engine.moves import get_legal_moves
from engine.search import find_best_move, make_move
from engine.evaluation import evaluate
from ai.styles import load_all_styles

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
ELO_TABLE  = os.path.join(DATA_DIR, "elo_table.json")

# ── ELO math ──────────────────────────────────────────────────

def expected_score(rating_a: float, rating_b: float) -> float:
    """Expected score for player A against player B using ELO formula."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))


def update_elo(rating: float, expected: float,
               actual: float, k: float = 32) -> float:
    """Return updated ELO rating after one game."""
    return rating + k * (actual - expected)


# ── Bot configuration ─────────────────────────────────────────

# Reference bots: fixed configs with known approximate ELO anchors
REFERENCE_BOTS = [
    {"name": "ref_800",  "depth": 1, "imprecision": 1.0,
     "weights": None, "elo": 800},
    {"name": "ref_1000", "depth": 1, "imprecision": 0.5,
     "weights": None, "elo": 1000},
    {"name": "ref_1200", "depth": 1, "imprecision": 0.0,
     "weights": None, "elo": 1200},
    {"name": "ref_1400", "depth": 2, "imprecision": 0.5,
     "weights": None, "elo": 1400},
    {"name": "ref_1600", "depth": 2, "imprecision": 0.0,
     "weights": None, "elo": 1600},
]

# Our evolved bots: each style at several strength settings
def build_bot_configs(styles: dict) -> list:
    """Build all bot configurations to calibrate."""
    configs = []
    for style_name, weights in styles.items():
        for depth, imprecision, label in [
            (1, 0.8, "easy"),
            (1, 0.4, "medium"),
            (1, 0.0, "hard"),
            (2, 0.2, "expert"),
        ]:
            configs.append({
                "name":        f"{style_name}_{label}",
                "style":       style_name,
                "depth":       depth,
                "imprecision": imprecision,
                "weights":     weights,
                "elo":         1200.0,  # starting ELO estimate
            })
    return configs


# ── Game simulation ───────────────────────────────────────────

def play_calibration_game(bot_a: dict, bot_b: dict,
                           max_moves: int = 60) -> str:
    """
    Play a game between two bot configs.
    bot_a plays White, bot_b plays Black.
    Returns 'white', 'black', or 'draw'.
    """
    board = Board()
    for move_num in range(max_moves):
        legal = get_legal_moves(board)
        if not legal:
            return "black" if board.turn == "white" else "white"

        bot    = bot_a if board.turn == "white" else bot_b
        move   = find_best_move(
            board,
            depth=bot["depth"],
            weights=bot["weights"],
            imprecision=bot["imprecision"]
        )
        if move is None:
            break
        make_move(board, move)

    score = evaluate(board)
    if score > 50:
        return "white"
    elif score < -50:
        return "black"
    return "draw"


# ── Tournament ────────────────────────────────────────────────

def run_calibration(games_per_pair: int = 4):
    """
    Run a calibration tournament.
    Each evolved bot plays against each reference bot N times.
    ELO ratings are updated after every game.
    Results saved to data/elo_table.json.

    games_per_pair: how many games per matchup (higher = more accurate,
                    but slower. 4 is reasonable for a student project.)
    """
    styles      = load_all_styles()
    bot_configs = build_bot_configs(styles)

    # Start reference bots with their anchor ELOs
    ref_bots = [b.copy() for b in REFERENCE_BOTS]

    all_bots = bot_configs + ref_bots
    total    = len(bot_configs) * len(ref_bots) * games_per_pair
    played   = 0

    print(f"\n=== ELO Calibration Tournament ===")
    print(f"Evolved bots:    {len(bot_configs)}")
    print(f"Reference bots:  {len(ref_bots)}")
    print(f"Games per pair:  {games_per_pair}")
    print(f"Total games:     {total}\n")

    for bot in bot_configs:
        for ref in ref_bots:
            for game_num in range(games_per_pair):
                # Alternate colours
                if game_num % 2 == 0:
                    white, black = bot, ref
                else:
                    white, black = ref, bot

                result = play_calibration_game(white, black)

                # Determine actual scores
                if result == "white":
                    score_white, score_black = 1.0, 0.0
                elif result == "black":
                    score_white, score_black = 0.0, 1.0
                else:
                    score_white, score_black = 0.5, 0.5

                # Update ELOs
                exp_white = expected_score(white["elo"], black["elo"])
                exp_black = expected_score(black["elo"], white["elo"])

                white["elo"] = update_elo(white["elo"], exp_white,
                                          score_white)
                black["elo"] = update_elo(black["elo"], exp_black,
                                          score_black)

                played += 1
                if played % 10 == 0 or played == total:
                    print(f"  Games played: {played}/{total}")

    # ── Print results ─────────────────────────────────────────
    print("\n── Calibration Results ──")
    print(f"{'Bot':<25} {'ELO':>6}")
    print("─" * 33)

    elo_table = {}
    for bot in sorted(bot_configs, key=lambda x: x["elo"], reverse=True):
        print(f"{bot['name']:<25} {bot['elo']:>6.0f}")
        elo_table[bot["name"]] = {
            "style":       bot["style"],
            "depth":       bot["depth"],
            "imprecision": bot["imprecision"],
            "elo":         round(bot["elo"]),
        }

    # ── Save results ──────────────────────────────────────────
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ELO_TABLE, "w") as f:
        json.dump(elo_table, f, indent=2)

    print(f"\nELO table saved → {ELO_TABLE}")
    return elo_table