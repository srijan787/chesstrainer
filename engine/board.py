# engine/board.py
# Represents the chess board and state of the game

#---Piece constants---
#Uppercase = White, Lowercase= Black, "."= empty
EMPTY = "."

WP="P"
WN="N"
WB="B"
WR="R"
WQ="Q"
WK="K"

BP="p"
BN="n"
BB="b"
BR="r"
BQ="q"
BK="k"

#--Piece values---
PIECE_VALUES ={
    WP:100, WN:320, WB:330, WR:500, WQ:900, WK:20000,
    BP:-100, BN:-320, BB:-330, BR:-500, BQ:-900, BK:-20000,
    EMPTY:0
}

#Starting position
#Index 0=a8(top left), index 63= h1(bottom right)
STARTING_FEN=[
    BR, BN, BB, BQ, BK, BB, BN, BR, #R8
    BP, BP, BP, BP, BP, BP, BP, BP, #R7
    ".", ".", ".", ".", ".", ".", ".", ".", #R6
    ".", ".", ".", ".", ".", ".", ".", ".", #R5
    ".", ".", ".", ".", ".", ".", ".", ".", #R4
    ".", ".", ".", ".", ".", ".", ".", ".", #R3
    WP, WP, WP, WP, WP, WP, WP, WP,  # R2
    WR, WN, WB, WQ, WK, WB, WN, WR,  # R1
]

class Board:
    def __init__(self):
        #the board: a flat list of 64 squares
        self.squares = STARTING_FEN.copy()

        #whose turn it is:"white" or black
        self.turn = "white"

        #CASTLING RIGHT
        self.castling = {
            "white_kingside": True,
            "black_kingside": True,
            "white_queenside": True,
            "black_queenside": True,
        }

        #En passant (-1 means not available)
        self.en_passant = -1

        #movee counter(for fifty move rule)
        self.halfmove_clock = 0
        self.fullmove_number = 1

    def get(self, square):
            """Return the piece on a given square(0-63)."""
            return self.squares[square]

    def set(self, square, piece):
            """Set the piece on a given square(0-63)."""
            self.squares[square] = piece

    def is_empty(self, square):
            """Return True if the given square is empty."""
            return self.squares[square] == EMPTY

    def is_white_piece(self, square):
            """Return True if the given square is white piece."""
            return self.squares[square].isupper()

    def is_black_piece(self, square):
            """Return True if the given square is black piece."""
            return self.squares[square].islower()

    def is_enemy(self, square, turn):
            """Return True if the square has an enemy piece."""
            if self.is_empty(square):
                return False
            if turn == "white":
                return self.is_black_piece(square)
            return self.is_white_piece(square)

    def is_friendly(self, square, turn):
            """Return True if the given square is friendly piece."""
            if self.is_empty(square):
                return False
            if turn == "white":
                return self.is_white_piece(square)
            return self.is_black_piece(square)

    def print_board(self):
            """Print the current board state."""
            print("\n   a b c d e f g h")
            print("   -----------------")
            for rank in range(8):
                row = f"{8-rank} |"
                for file in range(8):
                    square = rank * 8 + file
                    row += f" {self.squares[square]}"
                print(row)
            print("  -------------------")
            print(f"   Turn: {self.turn}\n")

    def switch_turn(self):
            """Switch turn state."""
            self.turn = "black" if self.turn == "white" else "white"

    @staticmethod
    def square_index(file, rank):
            """Return the index of the given square(0-63)."""
            return rank * 8 + file

    @staticmethod
    def index_to_coords(square):
            """Convert square index to (file, rank) tuple."""
            return square % 8, square // 8

    @staticmethod
    def square_name(square):
            """Convert square  index to algebraic notation e.g. 0 → 'a8'."""
            file, rank = square % 8, square//8
            return f"{'abcdefgh'[file]}{8-rank}"