# engine/moves.py
# Legal move generation for all piece types

from engine.board import (Board, EMPTY, WP, WN, WB, WR, WQ, WK,
                                         BP, BN, BB, BR, BQ, BK)

# ── Direction vectors ─────────────────────────────────────────
# Used by sliding pieces (bishop, rook, queen)
DIAGONAL_DIRS   = [-9, -7, 7, 9]   # bishop directions
STRAIGHT_DIRS   = [-8, -1, 1, 8]   # rook directions
ALL_DIRS        = [-9, -8, -7, -1, 1, 7, 8, 9]  # queen/king

# Knight move offsets (L-shapes)
KNIGHT_OFFSETS  = [-17, -15, -10, -6, 6, 10, 15, 17]


def get_legal_moves(board: Board):
    """Return all legal moves for the current player as (from, to) tuples."""
    pseudo = get_pseudo_legal_moves(board)
    legal  = []
    for move in pseudo:
        if not leaves_king_in_check(board, move):
            legal.append(move)
    return legal


def get_pseudo_legal_moves(board: Board):
    """Return all moves ignoring whether they leave the king in check."""
    moves = []
    for square in range(64):
        piece = board.get(square)
        if piece == EMPTY:
            continue
        # Only generate moves for the current player's pieces
        if board.turn == "white" and not board.is_white_piece(square):
            continue
        if board.turn == "black" and not board.is_black_piece(square):
            continue

        if piece in (WP, BP):
            moves += pawn_moves(board, square)
        elif piece in (WN, BN):
            moves += knight_moves(board, square)
        elif piece in (WB, BB):
            moves += bishop_moves(board, square)
        elif piece in (WR, BR):
            moves += rook_moves(board, square)
        elif piece in (WQ, BQ):
            moves += queen_moves(board, square)
        elif piece in (WK, BK):
            moves += king_moves(board, square)
    return moves


# ── Individual piece move generators ─────────────────────────

def pawn_moves(board: Board, square: int):
    moves = []
    piece = board.get(square)
    file  = square % 8
    rank  = square // 8

    if piece == WP:
        # White pawns move UP the board (decreasing index)
        # Single step forward
        fwd = square - 8
        if 0 <= fwd < 64 and board.is_empty(fwd):
            moves.append((square, fwd))
            # Double step from starting rank (rank 6 in 0-indexed)
            if rank == 6:
                fwd2 = square - 16
                if board.is_empty(fwd2):
                    moves.append((square, fwd2))
        # Captures (diagonal)
        if file > 0 and board.is_enemy(square - 9, "white"):
            moves.append((square, square - 9))
        if file < 7 and board.is_enemy(square - 7, "white"):
            moves.append((square, square - 7))
        # En passant
        if board.en_passant != -1:
            if file > 0 and board.en_passant == square - 9:
                moves.append((square, square - 9))
            if file < 7 and board.en_passant == square - 7:
                moves.append((square, square - 7))

    elif piece == BP:
        # Black pawns move DOWN the board (increasing index)
        fwd = square + 8
        if 0 <= fwd < 64 and board.is_empty(fwd):
            moves.append((square, fwd))
            # Double step from starting rank (rank 1 in 0-indexed)
            if rank == 1:
                fwd2 = square + 16
                if board.is_empty(fwd2):
                    moves.append((square, fwd2))
        # Captures
        if file < 7 and board.is_enemy(square + 9, "black"):
            moves.append((square, square + 9))
        if file > 0 and board.is_enemy(square + 7, "black"):
            moves.append((square, square + 7))
        # En passant
        if board.en_passant != -1:
            if file < 7 and board.en_passant == square + 9:
                moves.append((square, square + 9))
            if file > 0 and board.en_passant == square + 7:
                moves.append((square, square + 7))

    return moves


def knight_moves(board: Board, square: int):
    moves = []
    file  = square % 8
    rank  = square // 8
    turn  = board.turn

    for offset in KNIGHT_OFFSETS:
        target = square + offset
        if not (0 <= target < 64):
            continue
        # Prevent wrapping around the board edges
        t_file = target % 8
        t_rank = target // 8
        if abs(t_file - file) > 2 or abs(t_rank - rank) > 2:
            continue
        if not board.is_friendly(target, turn):
            moves.append((square, target))
    return moves


def bishop_moves(board: Board, square: int):
    return sliding_moves(board, square, DIAGONAL_DIRS)


def rook_moves(board: Board, square: int):
    return sliding_moves(board, square, STRAIGHT_DIRS)


def queen_moves(board: Board, square: int):
    return sliding_moves(board, square, ALL_DIRS)


def sliding_moves(board: Board, square: int, directions: list):
    """Generate moves for sliding pieces (bishop, rook, queen)."""
    moves = []
    turn  = board.turn
    file  = square % 8

    for direction in directions:
        current = square
        while True:
            next_sq = current + direction
            # Stay within board bounds
            if not (0 <= next_sq < 64):
                break
            # Prevent horizontal wrapping
            next_file = next_sq % 8
            if direction in (-1, 1) and abs(next_file - (current % 8)) != 1:
                break
            if direction in (-9, -7, 7, 9):
                if abs(next_file - (current % 8)) != 1:
                    break
            if board.is_friendly(next_sq, turn):
                break  # Blocked by own piece
            moves.append((square, next_sq))
            if board.is_enemy(next_sq, turn):
                break  # Can capture but not go further
            current = next_sq
    return moves


def king_moves(board: Board, square: int):
    moves = []
    turn  = board.turn
    file  = square % 8

    for direction in ALL_DIRS:
        target = square + direction
        if not (0 <= target < 64):
            continue
        # Prevent wrapping
        t_file = target % 8
        if abs(t_file - file) > 1:
            continue
        if not board.is_friendly(target, turn):
            moves.append((square, target))

    # Castling
    moves += castling_moves(board, square)
    return moves


def castling_moves(board: Board, square: int):
    moves = []
    turn  = board.turn

    if turn == "white" and square == 60:  # e1
        # Kingside: squares f1(61), g1(62) must be empty
        if (board.castling.get("white_kingside") and
                board.is_empty(61) and board.is_empty(62)):
            moves.append((60, 62))
        # Queenside: squares d1(59), c1(58), b1(57) must be empty
        if (board.castling.get("white_queenside") and
                board.is_empty(59) and board.is_empty(58) and board.is_empty(57)):
            moves.append((60, 58))

    elif turn == "black" and square == 4:  # e8
        if (board.castling.get("black_kingside") and
                board.is_empty(5) and board.is_empty(6)):
            moves.append((4, 6))
        if (board.castling.get("black_queenside") and
                board.is_empty(3) and board.is_empty(2) and board.is_empty(1)):
            moves.append((4, 2))

    return moves


# ── Check detection ───────────────────────────────────────────

def is_in_check(board: Board, turn: str):
    """Return True if the given side's king is currently in check."""
    king = WK if turn == "white" else BK
    # Find the king's square
    king_square = None
    for sq in range(64):
        if board.get(sq) == king:
            king_square = sq
            break
    if king_square is None:
        return False
    # Temporarily switch turn to generate opponent's moves
    board.turn = "black" if turn == "white" else "white"
    opponent_moves = get_pseudo_legal_moves(board)
    board.turn = turn  # restore
    # If any opponent move lands on the king's square, we're in check
    return any(to == king_square for _, to in opponent_moves)


def leaves_king_in_check(board: Board, move):
    """Return True if making this move would leave our king in check."""
    from_sq, to_sq = move
    # Make the move temporarily
    captured = board.get(to_sq)
    moving_piece = board.get(from_sq)
    board.set(to_sq, moving_piece)
    board.set(from_sq, EMPTY)
    # Check if our king is now in check
    in_check = is_in_check(board, board.turn)
    # Undo the move
    board.set(from_sq, moving_piece)
    board.set(to_sq, captured)
    return in_check