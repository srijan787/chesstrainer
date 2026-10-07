# engine/search.py
# Minimax with alpha-beta pruning, iterative deepening, and time control.
# Optimisations: move ordering (MVV-LVA), killer moves, time limit.

import math
import random
import time
from engine.board import Board, EMPTY
from engine.moves import get_legal_moves
from engine.evaluation import evaluate, BASE_VALUES

# ── Killer move table ─────────────────────────────────────────
# Stores quiet moves that caused a beta cutoff at each depth.
# These are tried early in sibling nodes — a cheap but effective
# way to improve move ordering without a full history table.
MAX_DEPTH    = 10
killer_moves = [[None, None] for _ in range(MAX_DEPTH)]


def store_killer(move, depth):
    if depth < MAX_DEPTH and move != killer_moves[depth][0]:
        killer_moves[depth][1] = killer_moves[depth][0]
        killer_moves[depth][0] = move


# ── Move application / undo ───────────────────────────────────

def make_move(board: Board, move: tuple):
    """Apply a move to the board and update game state."""
    from_sq, to_sq = move
    piece = board.get(from_sq)

    # En passant capture
    if board.en_passant == to_sq and piece in ("P", "p"):
        if piece == "P":
            board.set(to_sq + 8, EMPTY)
        else:
            board.set(to_sq - 8, EMPTY)

    # Update en passant target
    board.en_passant = -1
    if piece == "P" and from_sq - to_sq == 16:
        board.en_passant = from_sq - 8
    elif piece == "p" and to_sq - from_sq == 16:
        board.en_passant = from_sq + 8

    # Castling — move rook too
    if piece == "K" and from_sq == 60:
        if to_sq == 62:
            board.set(61, board.get(63)); board.set(63, EMPTY)
        elif to_sq == 58:
            board.set(59, board.get(56)); board.set(56, EMPTY)
        board.castling["white_kingside"]  = False
        board.castling["white_queenside"] = False
    elif piece == "k" and from_sq == 4:
        if to_sq == 6:
            board.set(5, board.get(7));  board.set(7, EMPTY)
        elif to_sq == 2:
            board.set(3, board.get(0));  board.set(0, EMPTY)
        board.castling["black_kingside"]  = False
        board.castling["black_queenside"] = False

    # Update castling rights on rook moves
    if from_sq == 63: board.castling["white_kingside"]  = False
    if from_sq == 56: board.castling["white_queenside"] = False
    if from_sq == 7:  board.castling["black_kingside"]  = False
    if from_sq == 0:  board.castling["black_queenside"] = False

    # Pawn promotion (auto-queen)
    if piece == "P" and to_sq // 8 == 0:
        piece = "Q"
    elif piece == "p" and to_sq // 8 == 7:
        piece = "q"

    board.set(to_sq, piece)
    board.set(from_sq, EMPTY)
    board.switch_turn()


def undo_move(board: Board, move: tuple, captured: str,
              old_en_passant: int, old_castling: dict,
              promoted: bool = False):
    """Undo a move, restoring full board state."""
    from_sq, to_sq = move
    board.switch_turn()
    piece = board.get(to_sq)

    if promoted:
        piece = "P" if board.turn == "white" else "p"

    board.set(from_sq, piece)
    board.set(to_sq, captured)
    board.castling   = old_castling.copy()
    board.en_passant = old_en_passant

    # Undo castling rook
    if piece == "K" and from_sq == 60:
        if to_sq == 62:
            board.set(63, board.get(61)); board.set(61, EMPTY)
        elif to_sq == 58:
            board.set(56, board.get(59)); board.set(59, EMPTY)
    elif piece == "k" and from_sq == 4:
        if to_sq == 6:
            board.set(7, board.get(5));  board.set(5, EMPTY)
        elif to_sq == 2:
            board.set(0, board.get(3));  board.set(3, EMPTY)

    # Undo en passant capture
    if old_en_passant == to_sq and piece in ("P", "p"):
        if piece == "P":
            board.set(to_sq + 8, "p")
        else:
            board.set(to_sq - 8, "P")


# ── Move ordering ─────────────────────────────────────────────

def order_moves(board: Board, moves: list, depth: int) -> list:
    """
    Score moves for ordering — higher score = try first.
    Order: captures (MVV-LVA) > killer moves > quiet moves.
    Better ordering = more alpha-beta cutoffs = faster search.
    """
    scores = []
    killers = killer_moves[depth] if depth < MAX_DEPTH else [None, None]

    for move in moves:
        score    = 0
        target   = board.get(move[1])
        attacker = board.get(move[0])

        if target != EMPTY:
            # MVV-LVA: Most Valuable Victim, Least Valuable Attacker
            victim_val   = abs(BASE_VALUES.get(target,   0))
            attacker_val = abs(BASE_VALUES.get(attacker, 0))
            score = 10000 + victim_val * 10 - attacker_val
        elif move in killers:
            # Killer move — quiet move that caused cutoff before
            score = 9000
        # else: quiet move, score 0

        scores.append((score, move))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scores]


# ── Quiescence search ─────────────────────────────────────────

def quiescence(board: Board, alpha: float, beta: float,
               weights: dict, time_up: list) -> float:
    """
    Search capture moves beyond the horizon to avoid the horizon effect.
    Without this, the engine misses obvious captures/recaptures at depth boundary.
    Only searches captures, not all moves — stays fast.
    """
    if time_up[0]:
        return evaluate(board, weights)

    stand_pat = evaluate(board, weights)

    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    # Generate only capture moves
    legal_moves = get_legal_moves(board)
    captures    = [m for m in legal_moves
                   if board.get(m[1]) != EMPTY]

    captures = order_moves(board, captures, 0)

    for move in captures:
        if time_up[0]:
            break
        captured     = board.get(move[1])
        old_ep       = board.en_passant
        old_castling = board.castling.copy()
        piece_before = board.get(move[0])

        make_move(board, move)
        promoted = (piece_before in ("P","p") and
                    board.get(move[1]) in ("Q","q"))

        score = -quiescence(board, -beta, -alpha, weights, time_up)

        undo_move(board, move, captured, old_ep, old_castling, promoted)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


# ── Core minimax ──────────────────────────────────────────────

def minimax(board: Board, depth: int, alpha: float, beta: float,
            maximizing: bool, weights: dict,
            time_up: list) -> float:
    """
    Minimax with alpha-beta pruning, killer moves, and quiescence.
    time_up is a single-element list used as a mutable flag.
    """
    if time_up[0]:
        return evaluate(board, weights)

    legal_moves = get_legal_moves(board)

    if depth == 0 or not legal_moves:
        if depth == 0:
            # Drop into quiescence instead of plain eval
            return quiescence(board, alpha, beta, weights, time_up)
        return evaluate(board, weights)

    ordered = order_moves(board, legal_moves, depth)

    if maximizing:
        max_score = -math.inf
        for move in ordered:
            if time_up[0]:
                break
            captured     = board.get(move[1])
            old_ep       = board.en_passant
            old_castling = board.castling.copy()
            piece_before = board.get(move[0])

            make_move(board, move)
            promoted = (piece_before in ("P","p") and
                        board.get(move[1]) in ("Q","q"))

            score = minimax(board, depth - 1, alpha, beta,
                            False, weights, time_up)

            undo_move(board, move, captured, old_ep,
                      old_castling, promoted)

            if score > max_score:
                max_score = score
            if score > alpha:
                alpha = score
            if beta <= alpha:
                # Beta cutoff — store as killer if quiet move
                if board.get(move[1]) == EMPTY:
                    store_killer(move, depth)
                break

        return max_score

    else:
        min_score = math.inf
        for move in ordered:
            if time_up[0]:
                break
            captured     = board.get(move[1])
            old_ep       = board.en_passant
            old_castling = board.castling.copy()
            piece_before = board.get(move[0])

            make_move(board, move)
            promoted = (piece_before in ("P","p") and
                        board.get(move[1]) in ("Q","q"))

            score = minimax(board, depth - 1, alpha, beta,
                            True, weights, time_up)

            undo_move(board, move, captured, old_ep,
                      old_castling, promoted)

            if score < min_score:
                min_score = score
            if score < beta:
                beta = score
            if beta <= alpha:
                if board.get(move[1]) == EMPTY:
                    store_killer(move, depth)
                break

        return min_score


# ── Iterative deepening root search ──────────────────────────

def find_best_move(board: Board, depth: int = 3,
                   weights: dict = None,
                   imprecision: float = 0.0,
                   time_limit: float = 2.0):
    """
    Find the best move using iterative deepening with a time limit.

    Searches depth 1, then 2, then 3... up to max depth.
    If time runs out mid-search, returns the best move from the
    last fully completed depth — so the bot always responds quickly.

    time_limit: max seconds to spend thinking (default 2.0)
    depth:      max depth ceiling (won't exceed this even with time left)
    imprecision: 0.0 = always best move, higher = picks from top N moves
    """
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return None
    if len(legal_moves) == 1:
        return legal_moves[0]  # only one legal move — play it instantly

    maximizing = board.turn == "white"
    best_move  = legal_moves[0]  # safe fallback
    start_time = time.time()
    time_up    = [False]          # mutable flag passed into recursion

    for current_depth in range(1, depth + 1):
        # Check time before starting a new depth
        elapsed = time.time() - start_time
        if elapsed >= time_limit:
            break

        time_up[0]   = False
        scored_moves = []
        alpha        = -math.inf
        beta         = math.inf

        # Order moves using result from previous iteration
        ordered = order_moves(board, legal_moves, current_depth)

        for move in ordered:
            # Check time mid-search
            if time.time() - start_time >= time_limit:
                time_up[0] = True
                break

            captured     = board.get(move[1])
            old_ep       = board.en_passant
            old_castling = board.castling.copy()
            piece_before = board.get(move[0])

            make_move(board, move)
            promoted = (piece_before in ("P","p") and
                        board.get(move[1]) in ("Q","q"))

            score = minimax(board, current_depth - 1,
                            alpha, beta,
                            not maximizing, weights, time_up)

            undo_move(board, move, captured, old_ep,
                      old_castling, promoted)

            scored_moves.append((score, move))

            # Update alpha at root for better ordering next iteration
            if maximizing and score > alpha:
                alpha = score
            elif not maximizing and score < beta:
                beta = score

        # Only update best_move if this depth completed fully
        if not time_up[0] and scored_moves:
            scored_moves.sort(key=lambda x: x[0], reverse=maximizing)
            best_move = scored_moves[0][1]
            last_scored = scored_moves
        elif time_up[0]:
            break  # time ran out mid-depth — use previous depth's result

    # Apply imprecision — pick from top N moves
    if imprecision > 0 and 'last_scored' in dir():
        try:
            pool_size = max(1, int(imprecision * len(last_scored)))
            pool_size = min(pool_size, len(last_scored))
            return random.choice(last_scored[:pool_size])[1]
        except Exception:
            pass

    return best_move