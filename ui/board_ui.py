# ui/board_ui.py
# Pygame chessboard rendering and mouse input handling

import pygame
from engine.board import Board, EMPTY
from engine.moves import get_legal_moves
from engine.search import find_best_move, make_move

# ── Constants ─────────────────────────────────────────────────
WINDOW_WIDTH  = 640
WINDOW_HEIGHT = 640
SQUARE_SIZE   = WINDOW_WIDTH // 8

# Colours (R, G, B)
LIGHT_SQUARE  = (240, 217, 181)
DARK_SQUARE   = (181, 136,  99)
HIGHLIGHT     = (186, 202,  68)   # selected square
LEGAL_DOT     = (100, 100, 100)   # legal move indicator
TEXT_COLOUR   = (30,  30,  30)

# Unicode chess pieces
PIECE_UNICODE = {
    "K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙",
    "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟",
}


def square_to_pixel(square: int):
    """Convert a square index (0–63) to the top-left pixel of that square."""
    file = square % 8
    rank = square // 8
    return file * SQUARE_SIZE, rank * SQUARE_SIZE


def pixel_to_square(x: int, y: int):
    """Convert a pixel position to a square index (0–63)."""
    file = x // SQUARE_SIZE
    rank = y // SQUARE_SIZE
    if 0 <= file < 8 and 0 <= rank < 8:
        return rank * 8 + file
    return -1


def draw_board(screen: pygame.Surface, selected: int, legal_targets: list):
    """Draw the board squares, highlights, and legal move dots."""
    for rank in range(8):
        for file in range(8):
            square = rank * 8 + file
            x = file * SQUARE_SIZE
            y = rank * SQUARE_SIZE

            # Base square colour
            if (rank + file) % 2 == 0:
                colour = LIGHT_SQUARE
            else:
                colour = DARK_SQUARE

            # Highlight selected square
            if square == selected:
                colour = HIGHLIGHT

            pygame.draw.rect(screen, colour,
                             (x, y, SQUARE_SIZE, SQUARE_SIZE))

            # Draw legal move dots
            if square in legal_targets:
                cx = x + SQUARE_SIZE // 2
                cy = y + SQUARE_SIZE // 2
                pygame.draw.circle(screen, LEGAL_DOT, (cx, cy), 10)


def draw_pieces(screen: pygame.Surface, board: Board, font: pygame.font.Font):
    """Draw all pieces on the board using Unicode symbols."""
    for square in range(64):
        piece = board.get(square)
        if piece == EMPTY:
            continue
        symbol = PIECE_UNICODE.get(piece, piece)
        x, y = square_to_pixel(square)
        # Draw piece shadow for readability
        shadow = font.render(symbol, True, (50, 50, 50))
        screen.blit(shadow, (x + 4, y + 4))
        # Draw piece
        colour = (255, 255, 255) if piece.isupper() else (0, 0, 0)
        text = font.render(symbol, True, colour)
        screen.blit(text, (x + 2, y + 2))


def draw_labels(screen: pygame.Surface, font_small: pygame.font.Font):
    """Draw rank numbers and file letters around the board."""
    files = "abcdefgh"
    for i in range(8):
        # File letters (bottom)
        label = font_small.render(files[i], True, TEXT_COLOUR)
        screen.blit(label, (i * SQUARE_SIZE + SQUARE_SIZE - 14,
                             WINDOW_HEIGHT - 16))
        # Rank numbers (left)
        label = font_small.render(str(8 - i), True, TEXT_COLOUR)
        screen.blit(label, (2, i * SQUARE_SIZE + 2))


def draw_status(screen: pygame.Surface, board: Board,
                font_small: pygame.font.Font, message: str = ""):
    """Draw turn indicator and any status message in the title bar."""
    turn_text = f"ChessTrainer  |  {'White' if board.turn == 'white' else 'Black'} to move"
    if message:
        turn_text += f"  |  {message}"
    pygame.display.set_caption(turn_text)


def run_game(depth: int = 2, weights: dict = None,
             imprecision: float = 0.0, player_colour: str = "white"):
    """
    Main game loop.

    depth:          engine search depth
    weights:        evaluation weights (GA-evolved style)
    imprecision:    0.0 = perfect play, higher = weaker/human-like
    player_colour:  which side the human plays ("white" or "black")
    """
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("ChessTrainer")

    # Fonts — use a system font that supports Unicode chess symbols
    font_piece = pygame.font.SysFont("segoeuisymbol,applesymbols,symbola,",
                                     52, bold=False)
    font_small  = pygame.font.SysFont("Arial", 13)

    board    = Board()
    selected = -1          # currently selected square
    legal_targets = []     # legal destination squares for selected piece
    message  = ""
    running  = True
    game_over = False

    while running:
        # ── Event handling ──────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if board.turn == player_colour:
                    x, y = pygame.mouse.get_pos()
                    clicked = pixel_to_square(x, y)

                    if clicked == -1:
                        continue

                    legal_moves = get_legal_moves(board)

                    if selected == -1:
                        # First click: select a piece
                        if (not board.is_empty(clicked) and
                                board.is_friendly(clicked, board.turn)):
                            selected = clicked
                            legal_targets = [to for (fr, to)
                                             in legal_moves if fr == clicked]
                    else:
                        # Second click: try to move
                        move = (selected, clicked)
                        if move in legal_moves:
                            make_move(board, move)
                            selected = -1
                            legal_targets = []
                            message = ""
                        elif (not board.is_empty(clicked) and
                              board.is_friendly(clicked, board.turn)):
                            # Clicked a different own piece — reselect
                            selected = clicked
                            legal_targets = [to for (fr, to)
                                             in legal_moves if fr == clicked]
                        else:
                            # Clicked invalid square — deselect
                            selected = -1
                            legal_targets = []

        # ── Engine move ─────────────────────────────────────────
        if (not game_over and
                board.turn != player_colour):
            legal_moves = get_legal_moves(board)
            if not legal_moves:
                message = "Checkmate! You win!" if board.turn != player_colour else "Checkmate! Engine wins!"
                game_over = True
            else:
                pygame.display.set_caption("ChessTrainer  |  Engine thinking...")
                move = find_best_move(board, depth=depth,
                                      weights=weights,
                                      imprecision=imprecision)
                if move:
                    make_move(board, move)

        # ── Check for game over ──────────────────────────────────
        if not game_over:
            legal_moves = get_legal_moves(board)
            if not legal_moves:
                message   = "No legal moves — game over."
                game_over = True

        # ── Drawing ─────────────────────────────────────────────
        screen.fill((0, 0, 0))
        draw_board(screen, selected, legal_targets)
        draw_pieces(screen, board, font_piece)
        draw_labels(screen, font_small)
        draw_status(screen, board, font_small, message)
        pygame.display.flip()

    pygame.quit()