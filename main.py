#main.py
from engine.board import Board

board = Board()
board.print_board()
print(f"Squares 0(a8):{board.get(0)}")
print(f"Squares 63(h1):{board.get(63)}")
print(f"Squares name 0:{board.square_name(0)}")
print(f"Squares name 63:{board.square_name(63)}")
