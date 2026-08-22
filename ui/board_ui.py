# ui/board_ui.py
# Pygame chessboard rendering and mouse input handling

import os
import pygame
from engine.board import Board, EMPTY
from engine.moves import get_legal_moves
from engine.search import find_best_move, make_move

# ── Constants ─────────────────────────────────────────────────
WINDOW_WIDTH  = 640
WINDOW_HEIGHT = 640
SQUARE_SIZE   = WINDOW_WIDTH // 8

# Colours
LIGHT_SQUARE  = (240, 217, 181)
DARK_SQUARE   = (181, 136,  99)
HIGHLIGHT     = (186, 202,  68)
LEGAL_DOT     = (100, 100, 100)
TEXT_COLOUR   = (30,  30,  30)

# Map board piece characters to asset filenames
PIECE_FILES = {
    "K": "wK.svg", "Q": "wQ.svg", "R": "wR.svg",
    "B": "wB.svg", "N": "wN.svg", "P": "wP.svg",
    "k": "bK.svg", "q": "bQ.svg", "r": "bR.svg",
    "b": "bB.svg", "n": "bN.svg", "p": "bP.svg",
}

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "assets", "pieces")


def load_pieces(size: int) -> dict:
    """Load and scale all piece PNGs into Pygame surfaces."""
    pieces = {}
    for piece, filename in PIECE_FILES.items():
        # Load PNG directly
        png_path = os.path.join(ASSETS_DIR,
                                filename.replace(".svg", ".png"))
        surface  = pygame.image.load(png_path).convert_alpha()
        surface  = pygame.transform.smoothscale(surface, (size, size))
        pieces[piece] = surface
    return pieces


def square_to_pixel(square: int):
    """Convert square index to top-left pixel."""
    file = square % 8
    rank = square // 8
    return file * SQUARE_SIZE, rank * SQUARE_SIZE


def pixel_to_square(x: int, y: int):
    """Convert pixel position to square index."""
    file = x // SQUARE_SIZE
    rank = y // SQUARE_SIZE
    if 0 <= file < 8 and 0 <= rank < 8:
        return rank * 8 + file
    return -1


def draw_board(screen: pygame.Surface, selected: int, legal_targets: list):
    """Draw squares, highlights and legal move indicators."""
    for rank in range(8):
        for file in range(8):
            square = rank * 8 + file
            x = file * SQUARE_SIZE
            y = rank * SQUARE_SIZE

            if (rank + file) % 2 == 0:
                colour = LIGHT_SQUARE
            else:
                colour = DARK_SQUARE

            if square == selected:
                colour = HIGHLIGHT

            pygame.draw.rect(screen, colour,
                             (x, y, SQUARE_SIZE, SQUARE_SIZE))

            # Legal move dot
            if square in legal_targets:
                cx = x + SQUARE_SIZE // 2
                cy = y + SQUARE_SIZE // 2
                dot_surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE),
                                          pygame.SRCALPHA)
                pygame.draw.circle(dot_surf, (0, 0, 0, 60),
                                   (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 12)
                screen.blit(dot_surf, (x, y))


def draw_pieces(screen: pygame.Surface, board: Board, pieces: dict):
    """Draw all pieces using loaded SVG images."""
    for square in range(64):
        piece = board.get(square)
        if piece == EMPTY:
            continue
        x, y = square_to_pixel(square)
        screen.blit(pieces[piece], (x, y))


def draw_labels(screen: pygame.Surface, font: pygame.font.Font):
    """Draw rank numbers and file letters."""
    files = "abcdefgh"
    for i in range(8):
        label = font.render(files[i], True, TEXT_COLOUR)
        screen.blit(label, (i * SQUARE_SIZE + SQUARE_SIZE - 14,
                             WINDOW_HEIGHT - 16))
        label = font.render(str(8 - i), True, TEXT_COLOUR)
        screen.blit(label, (2, i * SQUARE_SIZE + 2))


def run_game(depth: int = 2, weights: dict = None,
             imprecision: float = 0.0, player_colour: str = "white"):
    """Main game loop."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("ChessTrainer")
    clock  = pygame.time.Clock()

    font_small = pygame.font.SysFont("Arial", 13)

    # Load piece images
    piece_size = SQUARE_SIZE - 4
    pieces     = load_pieces(piece_size)

    board         = Board()
    selected      = -1
    legal_targets = []
    message       = ""
    running       = True
    game_over     = False
    engine_turn   = False   # flag to trigger engine move on next frame
    engine_delay  = 0       # tick count for delay

    while running:
        # ── Events ──────────────────────────────────────────────
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
                        if (not board.is_empty(clicked) and
                                board.is_friendly(clicked, board.turn)):
                            selected = clicked
                            legal_targets = [to for (fr, to)
                                             in legal_moves if fr == clicked]
                    else:
                        move = (selected, clicked)
                        if move in legal_moves:
                            make_move(board, move)
                            selected = -1
                            legal_targets = []
                            engine_delay  = pygame.time.get_ticks() + 600
                            engine_turn   = True
                        elif (not board.is_empty(clicked) and
                              board.is_friendly(clicked, board.turn)):
                            selected = clicked
                            legal_targets = [to for (fr, to)
                                             in legal_moves if fr == clicked]
                        else:
                            selected = -1
                            legal_targets = []

        # ── Engine move (after delay) ────────────────────────────
        if (engine_turn and not game_over and
                pygame.time.get_ticks() >= engine_delay):
            engine_turn = False
            legal_moves = get_legal_moves(board)
            if not legal_moves:
                message   = "Game over."
                game_over = True
            else:
                pygame.display.set_caption(
                    "ChessTrainer  |  Engine thinking...")
                move = find_best_move(board, depth=depth,
                                      weights=weights,
                                      imprecision=imprecision)
                if move:
                    make_move(board, move)

        # ── Game over check ──────────────────────────────────────
        if not game_over:
            if not get_legal_moves(board) and board.turn == player_colour:
                message   = "Checkmate — engine wins!"
                game_over = True

        # ── Draw ─────────────────────────────────────────────────
        screen.fill((0, 0, 0))
        draw_board(screen, selected, legal_targets)
        draw_pieces(screen, board, pieces)
        draw_labels(screen, font_small)

        if message:
            pygame.display.set_caption(f"ChessTrainer  |  {message}")
        elif not engine_turn and board.turn == player_colour:
            pygame.display.set_caption(
                "ChessTrainer  |  Your turn")

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()