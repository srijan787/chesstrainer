# game/analysis.py
# Post-game analysis module.
# Re-evaluates every move the player made and flags significant mistakes.
# A "mistake" is a move that caused a large drop in position evaluation.

from engine.board import Board
from engine.moves import get_legal_moves
from engine.search import find_best_move, make_move
from engine.evaluation import evaluate

# ── Thresholds (in centipawns) ────────────────────────────────
# How much eval must drop to classify a move as a mistake
INACCURACY_THRESHOLD = 50    # small mistake
MISTAKE_THRESHOLD    = 150   # clear mistake
BLUNDER_THRESHOLD    = 300   # serious blunder


def classify_mistake(eval_drop: float) -> str:
    """Classify a move based on how much evaluation dropped."""
    drop = abs(eval_drop)
    if drop >= BLUNDER_THRESHOLD:
        return "blunder"
    elif drop >= MISTAKE_THRESHOLD:
        return "mistake"
    elif drop >= INACCURACY_THRESHOLD:
        return "inaccuracy"
    return "ok"


def analyse_game(move_history: list,
                 player_colour: str = "white",
                 analysis_depth: int = 2) -> list:
    """
    Analyse a completed game and return a list of mistake records.

    move_history:   list of (from_sq, to_sq) tuples in game order
    player_colour:  which side the human played
    analysis_depth: minimax depth used for finding better moves
                    (higher = more accurate but slower)

    Returns a list of dicts, one per player move analysed,
    containing the move, eval before/after, best move, and classification.
    """
    board    = Board()
    results  = []
    move_num = 0

    for move in move_history:
        is_player_move = (
            (player_colour == "white" and move_num % 2 == 0) or
            (player_colour == "black" and move_num % 2 == 1)
        )

        if is_player_move:
            # Evaluate position BEFORE the move
            eval_before = evaluate(board)
            if player_colour == "black":
                eval_before = -eval_before  # flip so positive = good for player

            # Find what the engine considers the best move here
            best_move = find_best_move(board, depth=analysis_depth)

            # Apply the actual move the player made
            legal = get_legal_moves(board)
            if move not in legal:
                move_num += 1
                continue
            make_move(board, move)

            # Evaluate position AFTER the move
            eval_after = evaluate(board)
            if player_colour == "black":
                eval_after = -eval_after

            # From the player's perspective: did their position improve?
            # For white: higher eval = better. For black: lower eval = better.
            if player_colour == "white":
                eval_drop = eval_before - eval_after
            else:
                eval_drop = eval_after - eval_before

            classification = classify_mistake(eval_drop)

            record = {
                "move_number":  move_num // 2 + 1,
                "move":         move,
                "move_name":    _move_name(move),
                "eval_before":  round(eval_before, 1),
                "eval_after":   round(eval_after, 1),
                "eval_drop":    round(eval_drop, 1),
                "best_move":    best_move,
                "best_move_name": _move_name(best_move) if best_move else "none",
                "classification": classification,
            }
            results.append(record)

        else:
            # Engine move — just apply it
            legal = get_legal_moves(board)
            if move not in legal:
                move_num += 1
                continue
            make_move(board, move)

        move_num += 1

    return results


def format_analysis(analysis: list) -> str:
    """Format analysis results as a readable string for display."""
    if not analysis:
        return "No moves to analyse."

    lines  = ["── Post-Game Analysis ──\n"]
    issues = [r for r in analysis if r["classification"] != "ok"]

    if not issues:
        lines.append("Great game! No significant mistakes found.")
        return "\n".join(lines)

    counts = {"blunder": 0, "mistake": 0, "inaccuracy": 0}
    for r in issues:
        counts[r["classification"]] += 1

    lines.append(f"Blunders:     {counts['blunder']}")
    lines.append(f"Mistakes:     {counts['mistake']}")
    lines.append(f"Inaccuracies: {counts['inaccuracy']}\n")

    for r in issues:
        icon = {"blunder": "??", "mistake": "?", "inaccuracy": "!?"}[
            r["classification"]]
        lines.append(
            f"Move {r['move_number']:>2}: {r['move_name']:<6} {icon}  "
            f"eval {r['eval_before']:+.0f} → {r['eval_after']:+.0f}  "
            f"(drop: {r['eval_drop']:+.0f})  "
            f"better: {r['best_move_name']}"
        )

    return "\n".join(lines)


def _move_name(move) -> str:
    """Convert a (from, to) tuple to algebraic notation e.g. (52,36) → 'e2e4'."""
    if move is None:
        return "none"
    files = "abcdefgh"
    from_sq, to_sq = move
    f1 = files[from_sq % 8]
    r1 = 8 - from_sq // 8
    f2 = files[to_sq % 8]
    r2 = 8 - to_sq // 8
    return f"{f1}{r1}{f2}{r2}"