# engine/evaluation.py
# Evaluates a board position and returns a score
# Positive = good for White, Negative = good for Black

from engine.board import Board, EMPTY, WP, WN, WB, WR, WQ, WK, BP, BN, BB, BR, BQ, BK

# ── Piece base values ─────────────────────────────────────────
BASE_VALUES = {
    WP: 100,  WN: 320,  WB: 330,  WR: 500,  WQ: 900,  WK: 20000,
    BP: -100, BN: -320, BB: -330, BR: -500, BQ: -900, BK: -20000,
    EMPTY: 0
}

# ── Positional bonus tables ───────────────────────────────────
# Each table is 64 values (one per square, a8 to h1)
# Positive = good square for that piece, negative = bad square
# These are for White pieces — we mirror for Black

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

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

# Map piece type to its positional table
PIECE_TABLES = {
    WP: PAWN_TABLE,
    WN: KNIGHT_TABLE,
    WB: BISHOP_TABLE,
    WR: ROOK_TABLE,
    WQ: QUEEN_TABLE,
    WK: KING_TABLE,
}


def get_positional_bonus(piece: str, square: int) -> int:
    """Return the positional bonus for a piece on a given square."""
    if piece in PIECE_TABLES:
        # White piece: use table directly
        return PIECE_TABLES[piece][square]
    # Black piece: mirror the square vertically
    mirrored = {
        BP: PAWN_TABLE,
        BN: KNIGHT_TABLE,
        BB: BISHOP_TABLE,
        BR: ROOK_TABLE,
        BQ: QUEEN_TABLE,
        BK: KING_TABLE,
    }
    if piece in mirrored:
        mirror_square = (7 - square // 8) * 8 + (square % 8)
        return -mirrored[piece][mirror_square]
    return 0


def evaluate(board: Board, weights: dict = None) -> float:
    """
    Evaluate the board position and return a score.
    Positive = White is better, Negative = Black is better.

    weights: optional dict to scale feature contributions.
             Used by the GA to evolve different playing styles.
             Keys: 'material', 'position', 'mobility'
             Default: all weights = 1.0
    """
    if weights is None:
        weights = {
            "material": 1.0,
            "position": 1.0,
            "mobility": 1.0,
        }

    material_score    = 0
    positional_score  = 0

    for square in range(64):
        piece = board.get(square)
        if piece == EMPTY:
            continue
        # Material score
        material_score   += BASE_VALUES[piece]
        # Positional bonus
        positional_score += get_positional_bonus(piece, square)

    # Mobility score: more legal moves = better position
    from engine.moves import get_legal_moves
    current_turn = board.turn
    white_moves  = 0
    black_moves  = 0

    board.turn = "white"
    white_moves = len(get_legal_moves(board))
    board.turn = "black"
    black_moves = len(get_legal_moves(board))
    board.turn  = current_turn  # restore

    mobility_score = white_moves - black_moves

    # Combine with weights
    total = (weights["material"] * material_score +
             weights["position"] * positional_score +
             weights["mobility"] * mobility_score)

    return total