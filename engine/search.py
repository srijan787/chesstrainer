# engine/search.py
# Minimax search with alpha-beta pruning
# This is the "brain" of the chess engine — it looks ahead
# and picks the best move for the current player.

import math
import random
from engine.board import Board, EMPTY
from engine.moves import get_legal_moves
from engine.evaluation import evaluate


def make_move(board: Board, move: tuple):
    """Apply a move to the board and update game state."""
    from_sq, to_sq = move
    piece = board.get(from_sq)

    # Handle en passant capture
    if board.en_passant == to_sq and piece in ("P", "p"):
        if piece == "P":
            board.set(to_sq + 8, EMPTY)   # remove captured black pawn
        else:
            board.set(to_sq - 8, EMPTY)   # remove captured white pawn

    # Set en passant target square
    board.en_passant = -1
    if piece == "P" and from_sq - to_sq == 16:
        board.en_passant = from_sq - 8
    elif piece == "p" and to_sq - from_sq == 16:
        board.en_passant = from_sq + 8

    # Handle castling — move the rook too
    if piece == "K" and from_sq == 60:
        if to_sq == 62:   # kingside
            board.set(61, board.get(63))
            board.set(63, EMPTY)
        elif to_sq == 58:  # queenside
            board.set(59, board.get(56))
            board.set(56, EMPTY)
        board.castling["white_kingside"]  = False
        board.castling["white_queenside"] = False

    elif piece == "k" and from_sq == 4:
        if to_sq == 6:
            board.set(5, board.get(7))
            board.set(7, EMPTY)
        elif to_sq == 2:
            board.set(3, board.get(0))
            board.set(0, EMPTY)
        board.castling["black_kingside"]  = False
        board.castling["black_queenside"] = False

    # Update castling rights if rook moves
    if from_sq == 63: board.castling["white_kingside"]  = False
    if from_sq == 56: board.castling["white_queenside"] = False
    if from_sq == 7:  board.castling["black_kingside"]  = False
    if from_sq == 0:  board.castling["black_queenside"] = False

    # Pawn promotion (auto-promote to queen)
    if piece == "P" and to_sq // 8 == 0:
        piece = "Q"
    elif piece == "p" and to_sq // 8 == 7:
        piece = "q"

    # Make the move
    board.set(to_sq, piece)
    board.set(from_sq, EMPTY)
    board.switch_turn()


def undo_move(board: Board, move: tuple, captured: str,
              old_en_passant: int, old_castling: dict,
              promoted: bool = False):
    """Undo a move, restoring full board state."""
    from_sq, to_sq = move

    # Restore turn first
    board.switch_turn()
    piece = board.get(to_sq)

    # Undo promotion
    if promoted:
        piece = "P" if board.turn == "white" else "p"

    board.set(from_sq, piece)
    board.set(to_sq, captured)

    # Restore castling state
    board.castling    = old_castling.copy()
    board.en_passant  = old_en_passant

    # Undo rook move for castling
    if piece == "K" and from_sq == 60:
        if to_sq == 62:
            board.set(63, board.get(61))
            board.set(61, EMPTY)
        elif to_sq == 58:
            board.set(56, board.get(59))
            board.set(59, EMPTY)
    elif piece == "k" and from_sq == 4:
        if to_sq == 6:
            board.set(7, board.get(5))
            board.set(5, EMPTY)
        elif to_sq == 2:
            board.set(0, board.get(3))
            board.set(3, EMPTY)

    # Undo en passant capture
    if old_en_passant == to_sq and piece in ("P", "p"):
        if piece == "P":
            board.set(to_sq + 8, "p")
        else:
            board.set(to_sq - 8, "P")


def minimax(board: Board, depth: int, alpha: float, beta: float,
            maximizing: bool, weights: dict = None) -> float:
    """
    Minimax with alpha-beta pruning.

    depth:      how many moves ahead to search
    alpha:      best score White can guarantee (starts at -inf)
    beta:       best score Black can guarantee (starts at +inf)
    maximizing: True if it's White's turn to maximise the score
    weights:    evaluation weight dict passed to evaluate()

    Returns the best score achievable from this position.
    """
    legal_moves = get_legal_moves(board)

    # Terminal conditions
    if depth == 0 or len(legal_moves) == 0:
        return evaluate(board, weights)

    if maximizing:
        max_score = -math.inf
        for move in legal_moves:
            # Save state
            captured      = board.get(move[1])
            old_ep        = board.en_passant
            old_castling  = board.castling.copy()
            piece_before  = board.get(move[0])

            make_move(board, move)

            promoted = (piece_before in ("P","p") and
                        board.get(move[1]) in ("Q","q"))

            score = minimax(board, depth - 1, alpha, beta,
                            False, weights)

            undo_move(board, move, captured, old_ep,
                      old_castling, promoted)

            max_score = max(max_score, score)
            alpha     = max(alpha, score)
            if beta <= alpha:
                break   # Beta cut-off (pruning)
        return max_score

    else:
        min_score = math.inf
        for move in legal_moves:
            captured      = board.get(move[1])
            old_ep        = board.en_passant
            old_castling  = board.castling.copy()
            piece_before  = board.get(move[0])

            make_move(board, move)

            promoted = (piece_before in ("P","p") and
                        board.get(move[1]) in ("Q","q"))

            score = minimax(board, depth - 1, alpha, beta,
                            True, weights)

            undo_move(board, move, captured, old_ep,
                      old_castling, promoted)

            min_score = min(min_score, score)
            beta      = min(beta, score)
            if beta <= alpha:
                break   # Alpha cut-off (pruning)
        return min_score


def find_best_move(board: Board, depth: int = 3,
                   weights: dict = None,
                   imprecision: float = 0.0):
    """
    Find the best move for the current player.

    depth:       search depth (higher = stronger, slower)
    weights:     evaluation weights (for GA-evolved styles)
    imprecision: 0.0 = always pick best move (strongest)
                 0.0–1.0 = occasionally pick a suboptimal move
                 (used to simulate weaker/human-like play)

    Returns the best (or near-best) move as a (from, to) tuple.
    """
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return None

    maximizing = board.turn == "white"
    best_move  = None
    best_score = -math.inf if maximizing else math.inf

    # Score every legal move
    scored_moves = []
    for move in legal_moves:
        captured      = board.get(move[1])
        old_ep        = board.en_passant
        old_castling  = board.castling.copy()
        piece_before  = board.get(move[0])

        make_move(board, move)

        promoted = (piece_before in ("P","p") and
                    board.get(move[1]) in ("Q","q"))

        score = minimax(board, depth - 1, -math.inf, math.inf,
                        not maximizing, weights)

        undo_move(board, move, captured, old_ep,
                  old_castling, promoted)

        scored_moves.append((score, move))

    # Sort: best moves first
    scored_moves.sort(key=lambda x: x[0],
                      reverse=maximizing)

    # Imprecision: pick randomly from top N moves
    # imprecision=0 → always top 1, imprecision=1 → top 10
    if imprecision > 0:
        pool_size = max(1, int(imprecision * len(scored_moves)))
        pool_size = min(pool_size, len(scored_moves))
        return random.choice(scored_moves[:pool_size])[1]

    return scored_moves[0][1]