# main.py
import pygame
from ui.screens import (main_menu, bot_selector, post_game_screen,
                        history_screen, ladder_screen, fonts)
from ui.board_ui import run_game
from game.analysis import analyse_game


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 640))
    pygame.display.set_caption("ChessTrainer")
    f = fonts()

    while True:
        action = main_menu(screen, f)

        if action == "quit":
            break

        elif action == "history":
            history_screen(screen, f)

        elif action == "ladder":
            result = ladder_screen(screen, f)
            if isinstance(result, tuple) and result[0] == "play":
                cfg = result[1]
                game_result, move_history = run_game(
                    depth=cfg["depth"],
                    weights=cfg["weights"],
                    imprecision=cfg["imprecision"],
                    return_result=True
                )
                if game_result:
                    analysis = analyse_game(move_history,
                                            player_colour="white")
                    post_game_screen(screen, f, game_result,
                                     cfg["bot_name"], cfg["bot_elo"],
                                     cfg["style"], analysis)

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
                    analysis = analyse_game(move_history,
                                            player_colour="white")
                    post_game_screen(screen, f, game_result,
                                     bot_name, bot_elo,
                                     style, analysis)

    pygame.quit()


if __name__ == "__main__":
    main()