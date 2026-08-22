# main.py
from engine.board import Board
from engine.moves import get_legal_moves
from engine.evaluation import evaluate
from engine.search import find_best_move, make_move


def parse_move(move_str: str, board: Board):
    """Parse a move string like 'e2e4' into a (from, to) tuple."""
    if len(move_str) != 4:
        return None
    files = "abcdefgh"
    try:
        f1 = files.index(move_str[0])
        r1 = 8 - int(move_str[1])
        f2 = files.index(move_str[2])
        r2 = 8 - int(move_str[3])
        from_sq = r1 * 8 + f1
        to_sq   = r2 * 8 + f2
        return (from_sq, to_sq)
    except (ValueError, IndexError):
        return None


def main():
    board = Board()
    print("=== ChessTrainer Terminal Test ===")
    print("You are White. Enter moves like 'e2e4'. Type 'quit' to exit.\n")

    while True:
        board.print_board()
        legal = get_legal_moves(board)

        if not legal:
            print("Game over — no legal moves.")
            break

        if board.turn == "white":
            move_str = input("Your move: ").strip().lower()
            if move_str == "quit":
                break
            move = parse_move(move_str, board)
            if move not in legal:
                print("Illegal move, try again.\n")
                continue
            make_move(board, move)
        else:
            print("Engine thinking...")
            move = find_best_move(board, depth=2)
            if move is None:
                print("Engine has no moves.")
                break
            from_name = board.square_name(move[0])
            to_name   = board.square_name(move[1])
            print(f"Engine plays: {from_name}{to_name}\n")
            make_move(board, move)

        score = evaluate(board)
        print(f"Position score: {score:.1f}\n")


if __name__ == "__main__":
    main()