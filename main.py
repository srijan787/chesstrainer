#main.py
from engine.board import Board
from engine.moves import get_legal_moves

board = Board()
board.print_board()

moves = get_legal_moves(board)
print(f"Legal moves available: {len(moves)}")
print("first five moves:")

