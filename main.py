# main.py
from engine.board import Board
from engine.moves import get_legal_moves
from engine.evaluation import evaluate

board = Board()
board.print_board()

moves = get_legal_moves(board)
print(f"Legal moves: {len(moves)}")

score = evaluate(board)
print(f"Position score: {score}")
print("(0 = perfectly equal, positive = White better, negative = Black better)")