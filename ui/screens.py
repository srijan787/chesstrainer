# ui/screens.py
# All screens except the board itself.

import pygame
import sys
import os
import json

from game.rating import (get_stats, get_rating_history, record_game,
                          get_rating, get_recent_games)
from game.analysis import format_analysis
from game.ladder import get_ladder_progress, check_and_award
from ai.styles import load_all_styles, STYLE_INFO, get_style_description

BASE_DIR  = os.path.dirname(os.path.dirname(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "elo_table.json")

# ── Colours ───────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREY       = (40,  40,  40)
LIGHT_GREY = (80,  80,  80)
ACCENT     = (181, 136,  99)
HIGHLIGHT  = (186, 202,  68)
RED        = (180,  60,  60)
GREEN      = (60,  160,  60)
BLUE       = (60,  100, 180)
TEXT_DIM   = (160, 160, 160)

W, H = 640, 640


# ── Helpers ───────────────────────────────────────────────────

def fonts():
    return {
        "title":   pygame.font.SysFont("Arial", 42, bold=True),
        "heading": pygame.font.SysFont("Arial", 28, bold=True),
        "body":    pygame.font.SysFont("Arial", 20),
        "small":   pygame.font.SysFont("Arial", 15),
        "bold":    pygame.font.SysFont("Arial", 20, bold=True),
    }


def draw_text(screen, text, font, colour, x, y, center=False):
    surf = font.render(str(text), True, colour)
    rect = surf.get_rect()
    if center:
        rect.centerx = x
        rect.top     = y
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)
    return rect


def draw_button(screen, text, font, x, y, w, h,
                colour=None, text_colour=WHITE, hover=False):
    if colour is None:
        colour = LIGHT_GREY
    col = tuple(min(255, c + 30) for c in colour) if hover else colour
    pygame.draw.rect(screen, col,    (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, ACCENT, (x, y, w, h), 2, border_radius=8)
    surf = font.render(str(text), True, text_colour)
    rect = surf.get_rect(center=(x + w // 2, y + h // 2))
    screen.blit(surf, rect)
    return pygame.Rect(x, y, w, h)


def load_elo_table() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)


def confirm_dialog(screen, f, message: str) -> bool:
    """Show a simple Yes/No confirmation dialog. Returns True if Yes."""
    clock = pygame.time.Clock()
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    while True:
        mx, my = pygame.mouse.get_pos()
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, GREY, (120, 220, 400, 180), border_radius=12)
        pygame.draw.rect(screen, ACCENT, (120, 220, 400, 180), 2, border_radius=12)
        draw_text(screen, message, f["body"], WHITE, W // 2, 255, center=True)
        yes_rect = draw_button(screen, "Yes", f["bold"], 160, 330, 140, 48,
                               RED, hover=(160<=mx<=300 and 330<=my<=378))
        no_rect  = draw_button(screen, "No",  f["bold"], 340, 330, 140, 48,
                               GREEN, hover=(340<=mx<=480 and 330<=my<=378))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if yes_rect.collidepoint(mx, my):
                    return True
                if no_rect.collidepoint(mx, my):
                    return False
        pygame.display.flip()
        clock.tick(30)


# ── User login / register / delete screen ─────────────────────

def user_login_screen(screen, f):
    """Show user selection. Returns username string."""
    from game.rating import get_all_users, create_user, verify_pin, user_exists
    clock       = pygame.time.Clock()
    mode        = "select"
    username    = ""
    pin         = ""
    error       = ""
    input_field = "username"
    delete_mode = False   # True when user clicked delete on a profile

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)
        draw_text(screen, "ChessTrainer", f["title"],
                  ACCENT, W // 2, 40, center=True)

        # ── SELECT ───────────────────────────────────────────
        if mode == "select":
            draw_text(screen, "Select a profile or create one",
                      f["body"], TEXT_DIM, W // 2, 100, center=True)

            users = get_all_users()
            user_rects  = []
            delete_rects = []

            if users:
                draw_text(screen, "Existing profiles:",
                          f["bold"], WHITE, 60, 145)
                for i, u in enumerate(users):
                    y = 175 + i * 56
                    # Profile button
                    r = draw_button(screen, u.title(), f["body"],
                                    60, y, 300, 44, LIGHT_GREY,
                                    hover=(60<=mx<=360 and y<=my<=y+44))
                    user_rects.append((r, u))
                    # Delete button next to profile
                    dr = draw_button(screen, "Delete", f["small"],
                                     370, y, 80, 44, RED,
                                     hover=(370<=mx<=450 and y<=my<=y+44))
                    delete_rects.append((dr, u))
            else:
                draw_text(screen, "No profiles yet — create one below.",
                          f["body"], TEXT_DIM, W // 2, 200, center=True)

            new_rect  = draw_button(screen, "+ New Profile", f["bold"],
                                    170, H - 120, 300, 48, ACCENT,
                                    hover=(170<=mx<=470 and H-120<=my<=H-72))
            quit_rect = draw_button(screen, "Quit", f["bold"],
                                    170, H - 60, 300, 44, RED,
                                    hover=(170<=mx<=470 and H-60<=my<=H-16))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if quit_rect.collidepoint(mx, my):
                        pygame.quit(); sys.exit()
                    if new_rect.collidepoint(mx, my):
                        mode        = "register"
                        username    = ""
                        pin         = ""
                        error       = ""
                        input_field = "username"
                    # Profile click — go to login
                    for r, u in user_rects:
                        if r.collidepoint(mx, my):
                            mode        = "login"
                            username    = u
                            pin         = ""
                            error       = ""
                            input_field = "pin"
                    # Delete click — go to delete confirm
                    for dr, u in delete_rects:
                        if dr.collidepoint(mx, my):
                            mode        = "delete"
                            username    = u
                            pin         = ""
                            error       = ""
                            input_field = "pin"

        # ── LOGIN ────────────────────────────────────────────
        elif mode == "login":
            draw_text(screen, f"Login as: {username.title()}",
                      f["heading"], WHITE, W // 2, 110, center=True)
            draw_text(screen, "Enter your PIN:",
                      f["body"], TEXT_DIM, W // 2, 165, center=True)

            box_col = ACCENT if input_field == "pin" else LIGHT_GREY
            pygame.draw.rect(screen, box_col, (170, 200, 300, 48),
                             border_radius=8)
            draw_text(screen, "●" * len(pin), f["heading"],
                      WHITE, W // 2, 208, center=True)

            if error:
                draw_text(screen, error, f["body"],
                          RED, W // 2, 270, center=True)

            login_rect = draw_button(screen, "Login", f["bold"],
                                     170, 310, 300, 48, GREEN,
                                     hover=(170<=mx<=470 and 310<=my<=358))
            back_rect  = draw_button(screen, "Back", f["bold"],
                                     170, 375, 300, 44, LIGHT_GREY,
                                     hover=(170<=mx<=470 and 375<=my<=419))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        pin = pin[:-1]
                    elif event.key == pygame.K_RETURN:
                        if verify_pin(username, pin):
                            return username
                        error = "Incorrect PIN. Try again."
                        pin   = ""
                    elif event.unicode.isdigit() and len(pin) < 6:
                        pin += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if login_rect.collidepoint(mx, my):
                        if verify_pin(username, pin):
                            return username
                        error = "Incorrect PIN. Try again."
                        pin   = ""
                    if back_rect.collidepoint(mx, my):
                        mode  = "select"
                        error = ""

        # ── DELETE (PIN confirm then delete) ─────────────────
        elif mode == "delete":
            draw_text(screen, f"Delete profile: {username.title()}",
                      f["heading"], RED, W // 2, 110, center=True)
            draw_text(screen, "Enter your PIN to confirm deletion:",
                      f["body"], TEXT_DIM, W // 2, 165, center=True)

            box_col = ACCENT if input_field == "pin" else LIGHT_GREY
            pygame.draw.rect(screen, box_col, (170, 200, 300, 48),
                             border_radius=8)
            draw_text(screen, "●" * len(pin), f["heading"],
                      WHITE, W // 2, 208, center=True)

            draw_text(screen, "This will permanently delete all your",
                      f["small"], TEXT_DIM, W // 2, 268, center=True)
            draw_text(screen, "game history and rating. Cannot be undone.",
                      f["small"], RED, W // 2, 286, center=True)

            if error:
                draw_text(screen, error, f["body"],
                          RED, W // 2, 310, center=True)

            del_rect  = draw_button(screen, "Delete Profile", f["bold"],
                                    170, 340, 300, 48, RED,
                                    hover=(170<=mx<=470 and 340<=my<=388))
            back_rect = draw_button(screen, "Cancel", f["bold"],
                                    170, 405, 300, 44, LIGHT_GREY,
                                    hover=(170<=mx<=470 and 405<=my<=449))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        pin = pin[:-1]
                    elif event.unicode.isdigit() and len(pin) < 6:
                        pin += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if del_rect.collidepoint(mx, my):
                        if verify_pin(username, pin):
                            # Delete the user file
                            from game.rating import user_file
                            fp = user_file(username)
                            if os.path.exists(fp):
                                os.remove(fp)
                            mode     = "select"
                            pin      = ""
                            error    = ""
                            username = ""
                        else:
                            error = "Incorrect PIN."
                            pin   = ""
                    if back_rect.collidepoint(mx, my):
                        mode  = "select"
                        error = ""
                        pin   = ""

        # ── REGISTER ─────────────────────────────────────────
        elif mode == "register":
            draw_text(screen, "Create New Profile",
                      f["heading"], WHITE, W // 2, 100, center=True)

            draw_text(screen, "Username:", f["body"], TEXT_DIM, 170, 150)
            un_col = ACCENT if input_field == "username" else LIGHT_GREY
            pygame.draw.rect(screen, un_col, (170, 175, 300, 44),
                             border_radius=8)
            draw_text(screen, username, f["body"], WHITE, 184, 185)

            draw_text(screen, "PIN (digits only, max 6):",
                      f["body"], TEXT_DIM, 170, 235)
            pin_col = ACCENT if input_field == "pin" else LIGHT_GREY
            pygame.draw.rect(screen, pin_col, (170, 260, 300, 44),
                             border_radius=8)
            draw_text(screen, "●" * len(pin), f["body"], WHITE, 184, 270)

            if error:
                draw_text(screen, error, f["small"],
                          RED, W // 2, 320, center=True)

            create_rect = draw_button(screen, "Create Profile", f["bold"],
                                      170, 355, 300, 48, GREEN,
                                      hover=(170<=mx<=470 and 355<=my<=403))
            back_rect   = draw_button(screen, "Back", f["bold"],
                                      170, 420, 300, 44, LIGHT_GREY,
                                      hover=(170<=mx<=470 and 420<=my<=464))

            def try_register():
                if len(username) < 2:
                    return "Username must be at least 2 characters."
                if len(pin) < 4:
                    return "PIN must be at least 4 digits."
                if user_exists(username):
                    return "Username already taken."
                create_user(username, pin)
                return None

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 170 <= mx <= 470 and 175 <= my <= 219:
                        input_field = "username"
                    if 170 <= mx <= 470 and 260 <= my <= 304:
                        input_field = "pin"
                    if create_rect.collidepoint(mx, my):
                        err = try_register()
                        if err:
                            error = err
                        else:
                            return username
                    if back_rect.collidepoint(mx, my):
                        mode  = "select"
                        error = ""
                if event.type == pygame.KEYDOWN:
                    if input_field == "username":
                        if event.key == pygame.K_BACKSPACE:
                            username = username[:-1]
                        elif event.key == pygame.K_TAB:
                            input_field = "pin"
                        elif event.unicode.isalnum() and len(username) < 16:
                            username += event.unicode.lower()
                    elif input_field == "pin":
                        if event.key == pygame.K_BACKSPACE:
                            pin = pin[:-1]
                        elif event.key == pygame.K_RETURN:
                            err = try_register()
                            if err:
                                error = err
                            else:
                                return username
                        elif event.unicode.isdigit() and len(pin) < 6:
                            pin += event.unicode

        pygame.display.flip()
        clock.tick(30)


# ── Main Menu ─────────────────────────────────────────────────

def main_menu(screen, f, username: str):
    """Returns: 'play', 'ladder', 'history', 'switch', 'quit'"""
    clock = pygame.time.Clock()
    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "ChessTrainer", f["title"],
                  ACCENT, W // 2, 60, center=True)
        draw_text(screen, f"Welcome, {username.title()}",
                  f["body"], TEXT_DIM, W // 2, 115, center=True)

        stats = get_stats(username)
        draw_text(screen, f"Rating: {stats['rating']}",
                  f["heading"], WHITE, W // 2, 150, center=True)
        draw_text(screen,
                  f"W {stats['wins']}  D {stats['draws']}  "
                  f"L {stats['losses']}  ({stats['games_played']} games)",
                  f["small"], TEXT_DIM, W // 2, 190, center=True)

        buttons = {
            "play":    draw_button(screen, "Play vs Bot", f["bold"],
                                   170, 240, 300, 50,
                                   hover=(170<=mx<=470 and 240<=my<=290)),
            "ladder":  draw_button(screen, "Challenge Ladder", f["bold"],
                                   170, 305, 300, 50,
                                   hover=(170<=mx<=470 and 305<=my<=355)),
            "history": draw_button(screen, "Rating History", f["bold"],
                                   170, 370, 300, 50,
                                   hover=(170<=mx<=470 and 370<=my<=420)),
            "switch":  draw_button(screen, "Switch User", f["bold"],
                                   170, 435, 300, 50, LIGHT_GREY,
                                   hover=(170<=mx<=470 and 435<=my<=485)),
            "quit":    draw_button(screen, "Quit", f["bold"],
                                   170, 500, 300, 50, RED,
                                   hover=(170<=mx<=470 and 500<=my<=550)),
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for action, rect in buttons.items():
                    if rect.collidepoint(mx, my):
                        return action

        pygame.display.flip()
        clock.tick(30)


# ── Bot Selector ──────────────────────────────────────────────

def bot_selector(screen, f):
    """Returns (bot_name, style, bot_elo, weights, depth, imprecision) or None."""
    elo_table   = load_elo_table()
    styles      = list(STYLE_INFO.keys())
    sel_style   = 0
    sel_bot_idx = 0
    clock       = pygame.time.Clock()

    def bots_for_style(style):
        return sorted(
            [(k, v) for k, v in elo_table.items() if v["style"] == style],
            key=lambda x: x[1]["elo"]
        )

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "Choose Your Opponent",
                  f["heading"], ACCENT, W // 2, 30, center=True)

        tab_w = W // 3
        for i, style in enumerate(styles):
            colour = ACCENT if i == sel_style else LIGHT_GREY
            draw_button(screen, STYLE_INFO[style]["name"], f["bold"],
                        i * tab_w, 75, tab_w, 44, colour,
                        hover=(my < 119 and i * tab_w <= mx < (i+1) * tab_w))

        style_name = styles[sel_style]
        draw_text(screen, get_style_description(style_name),
                  f["small"], TEXT_DIM, 20, 135)

        bot_list  = bots_for_style(style_name)
        draw_text(screen, "Select difficulty / ELO:",
                  f["body"], WHITE, 20, 175)

        bot_rects = []
        for i, (bot_key, bot_data) in enumerate(bot_list):
            y      = 210 + i * 52
            colour = HIGHLIGHT if i == sel_bot_idx else LIGHT_GREY
            label  = (f"{bot_key.split('_')[1].title():<10}  "
                      f"ELO {bot_data['elo']}")
            rect   = draw_button(screen, label, f["body"],
                                 20, y, 600, 44, colour,
                                 hover=(20<=mx<=620 and y<=my<=y+44))
            bot_rects.append((rect, i))

        if bot_list and sel_bot_idx < len(bot_list):
            sel_key, sel_data = bot_list[sel_bot_idx]
            draw_text(screen,
                      f"Depth: {sel_data['depth']}  |  "
                      f"Imprecision: {sel_data['imprecision']}  |  "
                      f"ELO: {sel_data['elo']}",
                      f["small"], TEXT_DIM, 20, H - 100)

        go_rect   = draw_button(screen, "Play!", f["bold"],
                                370, H - 60, 120, 44, GREEN,
                                hover=(370<=mx<=490 and H-60<=my<=H-16))
        back_rect = draw_button(screen, "Back", f["bold"],
                                150, H - 60, 120, 44, RED,
                                hover=(150<=mx<=270 and H-60<=my<=H-16))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i in range(3):
                    if my < 119 and i * tab_w <= mx < (i+1) * tab_w:
                        sel_style   = i
                        sel_bot_idx = 0
                for rect, idx in bot_rects:
                    if rect.collidepoint(mx, my):
                        sel_bot_idx = idx
                if go_rect.collidepoint(mx, my) and bot_list:
                    sel_key, sel_data = bot_list[sel_bot_idx]
                    from ai.styles import load_style
                    weights = load_style(sel_data["style"])
                    return (sel_key, sel_data["style"], sel_data["elo"],
                            weights, sel_data["depth"],
                            sel_data["imprecision"])
                if back_rect.collidepoint(mx, my):
                    return None

        pygame.display.flip()
        clock.tick(30)


# ── Post-Game Screen ──────────────────────────────────────────

def post_game_screen(screen, f, result: str, bot_name: str,
                     bot_elo: int, bot_style: str,
                     move_history: list, username: str):
    """
    Ask user if they want analysis, then show result and optional analysis.
    Returns 'menu'.
    """
    # Record game first
    data   = record_game(username, bot_name, bot_elo, bot_style, result)
    reward = check_and_award(username, bot_name, result)
    clock  = pygame.time.Clock()

    result_colour = {"win": GREEN, "loss": RED, "draw": ACCENT}[result]
    result_text   = {"win": "You Win!", "loss": "You Lose",
                     "draw": "Draw"}[result]

    # ── Ask if user wants game review ────────────────────────
    want_analysis = False
    asking        = True
    while asking:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)
        draw_text(screen, result_text, f["title"],
                  result_colour, W // 2, 80, center=True)

        if data["history"]:
            last   = data["history"][-1]
            change = last["change"]
            sign   = "+" if change > 0 else ""
            draw_text(screen,
                      f"Rating: {last['rating_before']} → "
                      f"{last['rating_after']}  ({sign}{change})",
                      f["heading"], WHITE, W // 2, 155, center=True)

        if reward:
            draw_text(screen, reward, f["small"],
                      HIGHLIGHT, W // 2, 200, center=True)

        draw_text(screen, "Would you like to review your game?",
                  f["body"], TEXT_DIM, W // 2, 270, center=True)

        yes_rect = draw_button(screen, "Yes — Review", f["bold"],
                               100, 320, 180, 50, GREEN,
                               hover=(100<=mx<=280 and 320<=my<=370))
        no_rect  = draw_button(screen, "No — Main Menu", f["bold"],
                               360, 320, 180, 50, LIGHT_GREY,
                               hover=(360<=mx<=540 and 320<=my<=370))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if yes_rect.collidepoint(mx, my):
                    want_analysis = True
                    asking        = False
                if no_rect.collidepoint(mx, my):
                    want_analysis = False
                    asking        = False

        pygame.display.flip()
        clock.tick(30)

    if not want_analysis:
        return "menu"

    # ── Run analysis and show it ─────────────────────────────
    # Show loading message while analysis runs
    screen.fill(GREY)
    draw_text(screen, "Analysing your game...",
              f["heading"], TEXT_DIM, W // 2, H // 2 - 20, center=True)
    draw_text(screen, "This may take a few seconds.",
              f["small"], TEXT_DIM, W // 2, H // 2 + 20, center=True)
    pygame.display.flip()

    from game.analysis import analyse_game, format_analysis
    analysis      = analyse_game(move_history, player_colour="white",
                                 analysis_depth=2)
    analysis_text = format_analysis(analysis)
    lines         = analysis_text.split("\n")
    scroll        = 0

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "Game Review", f["heading"],
                  ACCENT, W // 2, 20, center=True)
        draw_text(screen, result_text, f["bold"],
                  result_colour, W // 2, 58, center=True)

        y = 90 + scroll
        for line in lines:
            if 80 < y < H - 60:
                colour = WHITE if line.startswith("Move") else TEXT_DIM
                if "??" in line:
                    colour = RED
                elif "!?" in line:
                    colour = ACCENT
                elif "Great game" in line or "No significant" in line:
                    colour = GREEN
                draw_text(screen, line, f["small"], colour, 20, y)
            y += 22

        draw_text(screen, "↑↓ to scroll",
                  f["small"], TEXT_DIM, W // 2, H - 46, center=True)
        menu_rect = draw_button(screen, "Main Menu", f["bold"],
                                220, H - 40, 200, 36, LIGHT_GREY,
                                hover=(220<=mx<=420 and H-40<=my<=H-4))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    scroll = min(0, scroll + 22)
                if event.key == pygame.K_DOWN:
                    scroll -= 22
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_rect.collidepoint(mx, my):
                    return "menu"

        pygame.display.flip()
        clock.tick(30)


# ── Rating History Screen ─────────────────────────────────────

def history_screen(screen, f, username: str):
    """Show rating chart and recent games. Returns 'menu'."""
    clock   = pygame.time.Clock()
    history = get_rating_history(username)
    stats   = get_stats(username)

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, f"{username.title()}'s Rating History",
                  f["heading"], ACCENT, W // 2, 20, center=True)
        draw_text(screen,
                  f"Rating: {stats['rating']}   "
                  f"W:{stats['wins']} D:{stats['draws']} "
                  f"L:{stats['losses']}   Win rate: {stats['win_rate']}%",
                  f["small"], TEXT_DIM, W // 2, 58, center=True)

        chart_x, chart_y = 40, 85
        chart_w, chart_h = 560, 200

        pygame.draw.rect(screen, LIGHT_GREY,
                         (chart_x, chart_y, chart_w, chart_h),
                         border_radius=6)
        pygame.draw.rect(screen, ACCENT,
                         (chart_x, chart_y, chart_w, chart_h),
                         2, border_radius=6)

        if len(history) >= 2:
            ratings = [h["rating"] for h in history]
            min_r   = max(600, min(ratings) - 50)
            max_r   = max(ratings) + 50
            r_range = max_r - min_r if max_r != min_r else 1

            points = []
            for i, h in enumerate(history):
                x = chart_x + int(i / (len(history) - 1) * chart_w)
                y = (chart_y + chart_h -
                     int((h["rating"] - min_r) / r_range * chart_h))
                points.append((x, y))

            pygame.draw.lines(screen, HIGHLIGHT, False, points, 2)
            for p in points:
                pygame.draw.circle(screen, WHITE, p, 3)

            draw_text(screen, str(int(max_r)), f["small"],
                      TEXT_DIM, chart_x + chart_w + 5, chart_y)
            draw_text(screen, str(int(min_r)), f["small"],
                      TEXT_DIM, chart_x + chart_w + 5,
                      chart_y + chart_h - 15)
        else:
            draw_text(screen, "Play some games to see your chart!",
                      f["body"], TEXT_DIM,
                      chart_x + chart_w // 2,
                      chart_y + chart_h // 2, center=True)

        draw_text(screen, "Recent games:", f["bold"], WHITE, 40, 305)
        recent = get_recent_games(username, 8)
        for i, game in enumerate(reversed(recent)):
            y      = 330 + i * 28
            colour = (GREEN if game["result"] == "win" else
                      RED   if game["result"] == "loss" else ACCENT)
            sign   = "+" if game["change"] > 0 else ""
            draw_text(screen,
                      f"{game['result'].upper():<5} vs "
                      f"{game['bot']:<22} "
                      f"{sign}{game['change']:>6}  →  "
                      f"{game['rating_after']}",
                      f["small"], colour, 40, y)

        back_rect = draw_button(screen, "Back", f["bold"],
                                220, H - 50, 200, 40, LIGHT_GREY,
                                hover=(220<=mx<=420 and H-50<=my<=H-10))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(mx, my):
                    return "menu"

        pygame.display.flip()
        clock.tick(30)


# ── Ladder Screen ─────────────────────────────────────────────

def ladder_screen(screen, f, username: str):
    """Show challenge ladder. Returns ('play', cfg) or 'menu'."""
    clock    = pygame.time.Clock()
    rating   = get_rating(username)
    progress = get_ladder_progress(username)
    scroll   = 0

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "Challenge Ladder",
                  f["heading"], ACCENT, W // 2, 20, center=True)
        draw_text(screen,
                  f"Completed: {progress['completed']}/{progress['total']}"
                  f"  |  Your rating: {rating}",
                  f["small"], TEXT_DIM, W // 2, 58, center=True)

        completed  = progress["completed_rungs"]
        y_start    = 90 + scroll
        rung_rects = []

        for rung in progress["rungs"]:
            y         = y_start + (rung["rung"] - 1) * 64
            is_done   = rung["rung"] in completed
            is_locked = rating < rung["unlock_at"]

            if is_done:
                colour = GREEN
                icon   = "Done"
            elif is_locked:
                colour = LIGHT_GREY
                icon   = "Locked"
            else:
                colour = ACCENT
                icon   = "Play"

            rect = draw_button(
                screen,
                f"[{icon}]  Rung {rung['rung']}: {rung['label']}  "
                f"({rung['style'].title()}, {rung['bot_elo']} ELO)",
                f["body"], 20, y, 600, 52, colour,
                hover=(not is_locked and 20<=mx<=620 and y<=my<=y+52)
            )

            if not is_locked:
                rung_rects.append((rect, rung))

            if 90 < y < H - 80:
                draw_text(screen, rung["description"],
                          f["small"], TEXT_DIM, 30, y + 36)

        back_rect = draw_button(screen, "Back", f["bold"],
                                220, H - 46, 200, 38, RED,
                                hover=(220<=mx<=420 and H-46<=my<=H-8))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    scroll = min(0, scroll + 22)
                if event.key == pygame.K_DOWN:
                    scroll -= 22
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(mx, my):
                    return "menu"
                for rect, rung in rung_rects:
                    if rect.collidepoint(mx, my):
                        from ai.styles import load_style
                        weights   = load_style(rung["style"])
                        elo_table = load_elo_table()
                        bot_data  = elo_table.get(rung["bot"], {})
                        return ("play", {
                            "bot_name":    rung["bot"],
                            "style":       rung["style"],
                            "bot_elo":     rung["bot_elo"],
                            "weights":     weights,
                            "depth":       bot_data.get("depth", 1),
                            "imprecision": bot_data.get("imprecision", 0.0),
                        })

        pygame.display.flip()
        clock.tick(30)