# main.py
import pygame
import sys
from ui.screens import (main_menu, bot_selector, post_game_screen,
                        history_screen, ladder_screen,
                        user_login_screen, fonts)
from ui.board_ui import run_game


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 640))
    pygame.display.set_caption("ChessTrainer")
    f = fonts()

    # Login first
    username = user_login_screen(screen, f)

    while True:
        action = main_menu(screen, f, username)

        if action == "quit":
            break

        elif action == "history":
            history_screen(screen, f, username)

        elif action == "switch":
            username = user_login_screen(screen, f)

        elif action == "ladder":
            result = ladder_screen(screen, f, username)
            if isinstance(result, tuple) and result[0] == "play":
                cfg = result[1]
                game_result, move_history = run_game(
                    depth=cfg["depth"],
                    weights=cfg["weights"],
                    imprecision=cfg["imprecision"],
                    return_result=True
                )
                if game_result:
                    post_game_screen(screen, f, game_result,
                                     cfg["bot_name"], cfg["bot_elo"],
                                     cfg["style"], move_history, username)

        elif action == "play":
            cfg = bot_selector(screen, f)
            if cfg:
                bot_name, style, bot_elo, weights, depth, imprecision = cfg
                game_result, move_history = run_game(
                    depth=depth,
                    weights=weights,
                    imprecision=imprecision,
                    return_result=True
                )
                if game_result:
                    post_game_screen(screen, f, game_result,
                                     bot_name, bot_elo,
                                     style, move_history, username)

    pygame.quit()


if __name__ == "__main__":
    main()