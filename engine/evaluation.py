# engine/evaluation.py
# Enhanced position evaluation with pawn structure, king safety,
# rook bonuses, and bishop pair detection.

from engine.board import (Board, EMPTY,
                           WP, WN, WB, WR, WQ, WK,
                           BP, BN, BB, BR, BQ, BK)

# ── Base piece values ─────────────────────────────────────────
BASE_VALUES = {
    WP: 100,  WN: 320,  WB: 330,  WR: 500,  WQ: 900,  WK: 20000,
    BP: -100, BN: -320, BB: -330, BR: -500, BQ: -900, BK: -20000,
    EMPTY: 0
}

# ── Piece-square tables ───────────────────────────────────────
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]
ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]
KING_MIDDLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]
KING_ENDGAME = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

PIECE_TABLES = {
    WP: PAWN_TABLE, WN: KNIGHT_TABLE, WB: BISHOP_TABLE,
    WR: ROOK_TABLE, WQ: QUEEN_TABLE,  WK: KING_MIDDLE,
}
BLACK_TABLES = {
    BP: PAWN_TABLE, BN: KNIGHT_TABLE, BB: BISHOP_TABLE,
    BR: ROOK_TABLE, BQ: QUEEN_TABLE,  BK: KING_MIDDLE,
}


def _mirror(square: int) -> int:
    return (7 - square // 8) * 8 + (square % 8)


def _is_endgame(board: Board) -> bool:
    """Endgame: queens gone or very little material."""
    queens = sum(1 for sq in range(64)
                 if board.get(sq) in (WQ, BQ))
    minor  = sum(1 for sq in range(64)
                 if board.get(sq) in (WN, WB, BN, BB))
    return queens == 0 or (queens <= 2 and minor <= 2)


def _pawn_structure(board: Board) -> int:
    """
    Evaluate pawn structure.
    Penalise doubled, isolated, and backward pawns.
    Reward passed pawns.
    """
    score = 0
    white_pawns = [sq for sq in range(64) if board.get(sq) == WP]
    black_pawns = [sq for sq in range(64) if board.get(sq) == BP]

    white_files = [sq % 8 for sq in white_pawns]
    black_files = [sq % 8 for sq in black_pawns]

    for sq in white_pawns:
        f = sq % 8
        r = sq // 8
        # Doubled pawn penalty
        if white_files.count(f) > 1:
            score -= 20
        # Isolated pawn penalty
        neighbours = [f-1, f+1]
        if not any(n in white_files for n in neighbours if 0 <= n <= 7):
            score -= 15
        # Passed pawn bonus (no black pawn in front on same or adjacent files)
        blocking = [bsq for bsq in black_pawns
                    if bsq % 8 in [f-1, f, f+1]
                    and bsq // 8 < r]
        if not blocking:
            # Bonus increases the further advanced the pawn is
            score += (7 - r) * 10

    for sq in black_pawns:
        f = sq % 8
        r = sq // 8
        if black_files.count(f) > 1:
            score += 20
        neighbours = [f-1, f+1]
        if not any(n in black_files for n in neighbours if 0 <= n <= 7):
            score += 15
        blocking = [wsq for wsq in white_pawns
                    if wsq % 8 in [f-1, f, f+1]
                    and wsq // 8 > r]
        if not blocking:
            score -= (r) * 10

    return score


def _king_safety(board: Board) -> int:
    """
    Penalise exposed kings.
    Reward pawn shields in front of castled king.
    """
    score = 0

    # Find kings
    wk_sq = next((sq for sq in range(64) if board.get(sq) == WK), -1)
    bk_sq = next((sq for sq in range(64) if board.get(sq) == BK), -1)

    if wk_sq != -1:
        wk_file = wk_sq % 8
        wk_rank = wk_sq // 8
        # Pawn shield — check pawns directly in front of king
        for df in [-1, 0, 1]:
            f = wk_file + df
            if 0 <= f <= 7:
                # Check one and two squares in front
                shield1 = (wk_rank - 1) * 8 + f
                shield2 = (wk_rank - 2) * 8 + f
                if 0 <= shield1 < 64 and board.get(shield1) == WP:
                    score += 10
                elif 0 <= shield2 < 64 and board.get(shield2) == WP:
                    score += 5  # pawn moved one step, partial shield
                else:
                    score -= 15  # open file in front of king

    if bk_sq != -1:
        bk_file = bk_sq % 8
        bk_rank = bk_sq // 8
        for df in [-1, 0, 1]:
            f = bk_file + df
            if 0 <= f <= 7:
                shield1 = (bk_rank + 1) * 8 + f
                shield2 = (bk_rank + 2) * 8 + f
                if 0 <= shield1 < 64 and board.get(shield1) == BP:
                    score -= 10
                elif 0 <= shield2 < 64 and board.get(shield2) == BP:
                    score -= 5
                else:
                    score += 15

    return score


def _rook_bonuses(board: Board) -> int:
    """Bonus for rooks on open and semi-open files."""
    score = 0
    white_pawn_files = {sq % 8 for sq in range(64) if board.get(sq) == WP}
    black_pawn_files = {sq % 8 for sq in range(64) if board.get(sq) == BP}

    for sq in range(64):
        piece = board.get(sq)
        f     = sq % 8
        if piece == WR:
            if f not in white_pawn_files and f not in black_pawn_files:
                score += 20   # open file
            elif f not in white_pawn_files:
                score += 10   # semi-open file
        elif piece == BR:
            if f not in white_pawn_files and f not in black_pawn_files:
                score -= 20
            elif f not in black_pawn_files:
                score -= 10
    return score


def _bishop_pair(board: Board) -> int:
    """Bonus for having both bishops."""
    wb = sum(1 for sq in range(64) if board.get(sq) == WB)
    bb = sum(1 for sq in range(64) if board.get(sq) == BB)
    score = 0
    if wb >= 2:
        score += 30
    if bb >= 2:
        score -= 30
    return score


def get_positional_bonus(piece: str, square: int,
                          endgame: bool = False) -> int:
    if piece in PIECE_TABLES:
        if piece == WK and endgame:
            return KING_ENDGAME[square]
        return PIECE_TABLES[piece][square]
    if piece in BLACK_TABLES:
        m = _mirror(square)
        if piece == BK and endgame:
            return -KING_ENDGAME[m]
        return -BLACK_TABLES[piece][m]
    return 0

def _hanging_pieces(board: Board) -> int:
    """
    Penalise pieces that are attacked but not defended.
    This directly discourages the bot from leaving pieces en prise.
    """
    from engine.moves import get_legal_moves

    score = 0

    # Get all squares attacked by each side
    # We do this by temporarily switching turn and generating moves
    original_turn = board.turn

    board.turn    = "white"
    white_moves   = get_legal_moves(board)
    white_attacks = {to for (_, to) in white_moves}

    board.turn    = "black"
    black_moves   = get_legal_moves(board)
    black_attacks = {to for (_, to) in black_moves}

    board.turn    = original_turn

    for sq in range(64):
        piece = board.get(sq)
        if piece == EMPTY:
            continue
        val = BASE_VALUES.get(piece, 0)

        if piece.isupper():  # White piece
            if sq in black_attacks and sq not in white_attacks:
                # White piece is attacked and undefended — hanging
                score -= abs(val) // 2   # penalty proportional to piece value
        else:  # Black piece
            if sq in white_attacks and sq not in black_attacks:
                # Black piece is attacked and undefended
                score += abs(val) // 2

    return score

def evaluate(board: Board, weights: dict = None) -> float:
    """
    Enhanced evaluation combining:
    - Material
    - Piece-square positional bonuses
    - Mobility
    - Pawn structure (doubled, isolated, passed pawns)
    - King safety (pawn shield)
    - Rook bonuses (open/semi-open files)
    - Bishop pair bonus
    """
    if weights is None:
        weights = {
            "material": 1.0,
            "position": 1.0,
            "mobility": 1.0,
        }

    endgame          = _is_endgame(board)
    material_score   = 0
    positional_score = 0

    for square in range(64):
        piece = board.get(square)
        if piece == EMPTY:
            continue
        material_score   += BASE_VALUES[piece]
        positional_score += get_positional_bonus(piece, square, endgame)

    # Mobility
    from engine.moves import get_legal_moves
    current_turn = board.turn
    board.turn   = "white"
    white_moves  = len(get_legal_moves(board))
    board.turn   = "black"
    black_moves  = len(get_legal_moves(board))
    board.turn   = current_turn

    mobility_score = white_moves - black_moves

    # Structural bonuses (not weighted by GA — fixed knowledge)
    structural = (
            _pawn_structure(board) +
            _king_safety(board) +
            _rook_bonuses(board) +
            _bishop_pair(board) +
            _hanging_pieces(board)
    )

    total = (weights["material"] * material_score  +
             weights["position"] * positional_score +
             weights["mobility"] * mobility_score   +
             structural)

    return total