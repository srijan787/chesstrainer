# ui/board_ui.py
# Pygame chessboard rendering and mouse input handling

import os
import sys
import pygame
from engine.board import Board, EMPTY, WK, BK
from engine.moves import get_legal_moves, is_in_check
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
LAST_MOVE     = (205, 210, 106)   # yellow — last move
CAPTURE_HINT  = (220,  80,  80)   # red corners — capture square
CHECK_COLOUR  = (220,  50,  50)   # red — king in check

PIECE_FILES = {
    "K": "wK.svg", "Q": "wQ.svg", "R": "wR.svg",
    "B": "wB.svg", "N": "wN.svg", "P": "wP.svg",
    "k": "bK.svg", "q": "bQ.svg", "r": "bR.svg",
    "b": "bB.svg", "n": "bN.svg", "p": "bP.svg",
}

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "assets", "pieces")


def load_pieces(size: int) -> dict:
    pieces = {}
    for piece, filename in PIECE_FILES.items():
        png_path = os.path.join(ASSETS_DIR, filename.replace(".svg", ".png"))
        surface  = pygame.image.load(png_path).convert_alpha()
        surface  = pygame.transform.smoothscale(surface, (size, size))
        pieces[piece] = surface
    return pieces


def square_to_pixel(square: int):
    file = square % 8
    rank = square // 8
    return file * SQUARE_SIZE, rank * SQUARE_SIZE


def pixel_to_square(x: int, y: int):
    file = x // SQUARE_SIZE
    rank = y // SQUARE_SIZE
    if 0 <= file < 8 and 0 <= rank < 8:
        return rank * 8 + file
    return -1


def find_king_square(board: Board, turn: str) -> int:
    """Return the square index of the given side's king."""
    king = WK if turn == "white" else BK
    for sq in range(64):
        if board.get(sq) == king:
            return sq
    return -1


def draw_board(screen: pygame.Surface, selected: int,
               legal_targets: list, last_move: tuple = None,
               board: Board = None, king_in_check: int = -1):
    """Draw squares with highlights, legal moves, last move, and check."""
    for rank in range(8):
        for file in range(8):
            square = rank * 8 + file
            x = file * SQUARE_SIZE
            y = rank * SQUARE_SIZE

            # Base colour
            if (rank + file) % 2 == 0:
                colour = LIGHT_SQUARE
            else:
                colour = DARK_SQUARE

            # Last move highlight
            if last_move is not None and square in (last_move[0], last_move[1]):
                colour = LAST_MOVE

            # King in check — override with red
            if square == king_in_check:
                colour = CHECK_COLOUR

            # Selected square
            if square == selected:
                colour = HIGHLIGHT

            pygame.draw.rect(screen, colour,
                             (x, y, SQUARE_SIZE, SQUARE_SIZE))

            # Legal move indicators
            if square in legal_targets:
                is_capture = (board is not None and
                              not board.is_empty(square) and
                              board.is_enemy(square, board.turn))
                if is_capture:
                    corner = 10
                    pygame.draw.rect(screen, CAPTURE_HINT,
                                     (x, y, corner, corner))
                    pygame.draw.rect(screen, CAPTURE_HINT,
                                     (x + SQUARE_SIZE - corner, y,
                                      corner, corner))
                    pygame.draw.rect(screen, CAPTURE_HINT,
                                     (x, y + SQUARE_SIZE - corner,
                                      corner, corner))
                    pygame.draw.rect(screen, CAPTURE_HINT,
                                     (x + SQUARE_SIZE - corner,
                                      y + SQUARE_SIZE - corner,
                                      corner, corner))
                else:
                    dot_surf = pygame.Surface(
                        (SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(dot_surf, (0, 0, 0, 60),
                                       (SQUARE_SIZE // 2,
                                        SQUARE_SIZE // 2), 12)
                    screen.blit(dot_surf, (x, y))


def draw_pieces(screen: pygame.Surface, board: Board, pieces: dict):
    for square in range(64):
        piece = board.get(square)
        if piece == EMPTY:
            continue
        x, y = square_to_pixel(square)
        screen.blit(pieces[piece], (x, y))


def draw_labels(screen: pygame.Surface, font: pygame.font.Font):
    files = "abcdefgh"
    for i in range(8):
        label = font.render(files[i], True, TEXT_COLOUR)
        screen.blit(label, (i * SQUARE_SIZE + SQUARE_SIZE - 14,
                             WINDOW_HEIGHT - 16))
        label = font.render(str(8 - i), True, TEXT_COLOUR)
        screen.blit(label, (2, i * SQUARE_SIZE + 2))

def draw_pause_menu(screen: pygame.Surface) -> str:
    """
    Draw pause overlay. Returns:
    'resume'  — continue the game
    'resign'  — forfeit (counts as a loss)
    'menu'    — go to main menu without recording result
    """
    font_big  = pygame.font.SysFont("Arial", 36, bold=True)
    font_med  = pygame.font.SysFont("Arial", 22)
    clock     = pygame.time.Clock()

    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.blit(overlay, (0, 0))

        # Title
        title = font_big.render("Game Paused", True, (255, 255, 255))
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 210)))

        # Buttons
        resume_rect = pygame.Rect(220, 265, 200, 48)
        resign_rect = pygame.Rect(220, 330, 200, 48)
        menu_rect   = pygame.Rect(220, 395, 200, 48)

        for rect, label, colour in [
            (resume_rect, "Resume",       (60, 160, 60)),
            (resign_rect, "Resign (Loss)",(180, 100, 40)),
            (menu_rect,   "Quit to Menu", (180,  60, 60)),
        ]:
            hover  = rect.collidepoint(mx, my)
            col    = tuple(min(255, c + 30) for c in colour) if hover else colour
            pygame.draw.rect(screen, col,          rect, border_radius=8)
            pygame.draw.rect(screen, (181, 136, 99), rect, 2, border_radius=8)
            txt = font_med.render(label, True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=rect.center))

        hint = font_med.render("Press ESC to resume", True, (120, 120, 120))
        screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 460)))

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "resume"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_rect.collidepoint(mx, my):
                    return "resume"
                if resign_rect.collidepoint(mx, my):
                    return "resign"
                if menu_rect.collidepoint(mx, my):
                    return "menu"

def run_game(depth: int = 2, weights: dict = None,
             imprecision: float = 0.0, player_colour: str = "white",
             return_result: bool = False,     paused = False):
    """Main game loop."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("ChessTrainer")
    clock  = pygame.time.Clock()

    font_small = pygame.font.SysFont("Arial", 13)
    piece_size = SQUARE_SIZE - 4
    pieces     = load_pieces(piece_size)

    board         = Board()
    selected      = -1
    legal_targets = []
    message       = ""
    running       = True
    game_over     = False
    move_history  = []
    final_result  = None
    last_move     = None
    king_in_check = -1   # square of king in check, -1 if not in check
    engine_turn   = False
    engine_delay  = 0

    while running:
        # ── Check detection ──────────────────────────────────
        # Update king_in_check every frame so it always reflects
        # the current board state
        if not game_over:
            if is_in_check(board, board.turn):
                king_in_check = find_king_square(board, board.turn)
            else:
                king_in_check = -1

        # ── Events ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and not game_over:
                    # Draw current board first so it shows behind the overlay
                    screen.fill((0, 0, 0))
                    draw_board(screen, selected, legal_targets,
                               last_move, board, king_in_check)
                    draw_pieces(screen, board, pieces)
                    draw_labels(screen, font_small)
                    pygame.display.flip()

                    pause_result = draw_pause_menu(screen)

                    if pause_result == "resign":
                        final_result = "loss"
                        message      = "You resigned."
                        game_over    = True
                    elif pause_result == "menu":
                        # Exit without recording result
                        if return_result:
                            return None, move_history
                        return None, []
                    # "resume" — just continue

            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if board.turn == player_colour:
                    x, y    = pygame.mouse.get_pos()
                    clicked = pixel_to_square(x, y)
                    if clicked == -1:
                        continue

                    legal_moves = get_legal_moves(board)

                    if selected == -1:
                        if (not board.is_empty(clicked) and
                                board.is_friendly(clicked, board.turn)):
                            selected      = clicked
                            legal_targets = [to for (fr, to)
                                             in legal_moves if fr == clicked]
                    else:
                        move = (selected, clicked)
                        if move in legal_moves:
                            make_move(board, move)
                            move_history.append(move)
                            last_move     = move
                            selected      = -1
                            legal_targets = []
                            engine_delay  = pygame.time.get_ticks() + 600
                            engine_turn   = True
                        elif (not board.is_empty(clicked) and
                              board.is_friendly(clicked, board.turn)):
                            selected      = clicked
                            legal_targets = [to for (fr, to)
                                             in legal_moves if fr == clicked]
                        else:
                            selected      = -1
                            legal_targets = []

        # ── Engine move ──────────────────────────────────────────
        if (engine_turn and not game_over and
                pygame.time.get_ticks() >= engine_delay):
            engine_turn = False
            legal_moves = get_legal_moves(board)
            if not legal_moves:
                game_over = True
            else:
                pygame.display.set_caption(
                    "ChessTrainer  |  Engine thinking...")
                move = find_best_move(board, depth=depth,
                                      weights=weights,
                                      imprecision=imprecision)
                if move:
                    make_move(board, move)
                    move_history.append(move)
                    last_move = move

        # ── Game over check ──────────────────────────────────────
        if not game_over:
            legal = get_legal_moves(board)
            if not legal:
                if board.turn == player_colour:
                    final_result = "loss"
                    message      = "Checkmate — Engine wins!"
                else:
                    final_result = "win"
                    message      = "Checkmate — You win!"
                game_over = True

        # ── Draw ─────────────────────────────────────────────────
        screen.fill((0, 0, 0))
        draw_board(screen, selected, legal_targets,
                   last_move, board, king_in_check)
        draw_pieces(screen, board, pieces)
        draw_labels(screen, font_small)

        # Check warning in title bar
        if king_in_check != -1 and not game_over:
            pygame.display.set_caption("ChessTrainer  |  CHECK!")
        elif message:
            pygame.display.set_caption(f"ChessTrainer  |  {message}")
        elif not engine_turn and board.turn == player_colour:
            pygame.display.set_caption("ChessTrainer  |  Your turn")

        pygame.display.flip()
        clock.tick(30)

        # ── Game over overlay ────────────────────────────────────
        if game_over and final_result:
            overlay   = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT),
                                       pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            font_big = pygame.font.SysFont("Arial", 42, bold=True)
            font_med = pygame.font.SysFont("Arial", 22)

            colour = ((60, 160, 60)  if final_result == "win"  else
                      (180, 60, 60)  if final_result == "loss" else
                      (181, 136, 99))
            text      = font_big.render(message, True, colour)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, 240))
            screen.blit(text, text_rect)

            btn_rect = pygame.Rect(220, 320, 200, 50)
            hover    = btn_rect.collidepoint(pygame.mouse.get_pos())
            btn_col  = (100, 100, 100) if hover else (60, 60, 60)
            pygame.draw.rect(screen, btn_col,  btn_rect, border_radius=8)
            pygame.draw.rect(screen, (181, 136, 99), btn_rect, 2,
                             border_radius=8)
            btn_text      = font_med.render("Continue", True, (255, 255, 255))
            btn_text_rect = btn_text.get_rect(center=btn_rect.center)
            screen.blit(btn_text, btn_text_rect)

            pygame.display.flip()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if btn_rect.collidepoint(pygame.mouse.get_pos()):
                            waiting = False

            if return_result:
                return final_result, move_history
            return None, []

    if return_result:
        return final_result, move_history
    return None, []