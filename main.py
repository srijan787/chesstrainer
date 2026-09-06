# main.py
from engine.board import Board
from engine.search import find_best_move, make_move
from engine.moves import get_legal_moves
from game.analysis import analyse_game, format_analysis

# Play a quick 10-move game, recording all moves
board        = Board()
move_history = []

print("Playing a quick test game...\n")
for i in range(10):
    legal = get_legal_moves(board)
    if not legal:
        break
    move = find_best_move(board, depth=1)
    if move is None:
        break
    move_history.append(move)
    make_move(board, move)

print(f"Moves played: {len(move_history)}")

# Analyse the game as if the human played White
analysis = analyse_game(move_history, player_colour="white",
                        analysis_depth=2)

print(format_analysis(analysis))