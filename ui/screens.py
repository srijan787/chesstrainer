# ui/screens.py
# All screens except the board itself.
# Main menu, bot selector, post-game, rating history, ladder screen.

import pygame
import sys
import os
from game.rating import get_stats, get_rating_history, record_game, get_rating
from game.analysis import format_analysis
from game.ladder import get_ladder_progress, get_next_rung, check_and_award
from ai.styles import load_all_styles, STYLE_INFO, get_style_description
from ai.calibration import REFERENCE_BOTS

BASE_DIR   = os.path.dirname(os.path.dirname(__file__))
DATA_FILE  = os.path.join(BASE_DIR, "data", "elo_table.json")

# ── Colours ───────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GREY       = (40,  40,  40)
LIGHT_GREY = (80,  80,  80)
ACCENT     = (181, 136,  99)   # matches board dark square
HIGHLIGHT  = (186, 202,  68)
RED        = (180,  60,  60)
GREEN      = (60,  160,  60)
BLUE       = (60,  100, 180)
TEXT_DIM   = (160, 160, 160)

W, H = 640, 640


# ── Font helper ───────────────────────────────────────────────
def fonts():
    return {
        "title":  pygame.font.SysFont("Arial", 42, bold=True),
        "heading":pygame.font.SysFont("Arial", 28, bold=True),
        "body":   pygame.font.SysFont("Arial", 20),
        "small":  pygame.font.SysFont("Arial", 15),
        "bold":   pygame.font.SysFont("Arial", 20, bold=True),
    }


def draw_text(screen, text, font, colour, x, y, center=False):
    surf = font.render(text, True, colour)
    rect = surf.get_rect()
    if center:
        rect.centerx = x
        rect.top     = y
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)
    return rect


def draw_button(screen, text, font, x, y, w, h,
                colour=LIGHT_GREY, text_colour=WHITE,
                hover=False):
    col = tuple(min(255, c + 30) for c in colour) if hover else colour
    pygame.draw.rect(screen, col, (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, ACCENT, (x, y, w, h), 2, border_radius=8)
    surf = font.render(text, True, text_colour)
    rect = surf.get_rect(center=(x + w // 2, y + h // 2))
    screen.blit(surf, rect)
    return pygame.Rect(x, y, w, h)


def load_elo_table() -> dict:
    import json
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)


# ── Main Menu ─────────────────────────────────────────────────
def main_menu(screen, f):
    """Returns: 'play', 'ladder', 'history', 'quit'"""
    clock = pygame.time.Clock()
    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "ChessTrainer", f["title"], ACCENT, W//2, 80, center=True)
        draw_text(screen, "Improve your chess against AI opponents",
                  f["small"], TEXT_DIM, W//2, 135, center=True)

        stats = get_stats()
        draw_text(screen, f"Your rating: {stats['rating']}",
                  f["heading"], WHITE, W//2, 185, center=True)
        draw_text(screen,
                  f"W {stats['wins']}  D {stats['draws']}  L {stats['losses']}  "
                  f"({stats['games_played']} games)",
                  f["small"], TEXT_DIM, W//2, 220, center=True)

        buttons = {
            "play":    draw_button(screen, "Play vs Bot", f["bold"],
                                   170, 290, 300, 52, hover=(170<=mx<=470 and 290<=my<=342)),
            "ladder":  draw_button(screen, "Challenge Ladder", f["bold"],
                                   170, 360, 300, 52, hover=(170<=mx<=470 and 360<=my<=412)),
            "history": draw_button(screen, "Rating History", f["bold"],
                                   170, 430, 300, 52, hover=(170<=mx<=470 and 430<=my<=482)),
            "quit":    draw_button(screen, "Quit", f["bold"],
                                   170, 500, 300, 52, RED,
                                   hover=(170<=mx<=470 and 500<=my<=552)),
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
    """
    Let the player choose a style and ELO level.
    Returns (bot_config_name, style, bot_elo, weights, depth, imprecision)
    or None if cancelled.
    """
    elo_table  = load_elo_table()
    styles     = list(STYLE_INFO.keys())
    sel_style  = 0   # index into styles
    clock      = pygame.time.Clock()

    # Group bots by style
    def bots_for_style(style):
        return sorted(
            [(k, v) for k, v in elo_table.items() if v["style"] == style],
            key=lambda x: x[1]["elo"]
        )

    sel_bot_idx = 0

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "Choose Your Opponent",
                  f["heading"], ACCENT, W//2, 30, center=True)

        # Style tabs
        tab_w = W // 3
        for i, style in enumerate(styles):
            colour = ACCENT if i == sel_style else LIGHT_GREY
            rect   = draw_button(screen, STYLE_INFO[style]["name"],
                                 f["bold"], i * tab_w, 75, tab_w, 44,
                                 colour, hover=(my < 119 and
                                               i * tab_w <= mx < (i+1)*tab_w))
            if rect:
                pass

        # Style description
        style_name = styles[sel_style]
        draw_text(screen, get_style_description(style_name),
                  f["small"], TEXT_DIM, 20, 135)

        # Bot list for selected style
        bot_list = bots_for_style(style_name)
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

        # Selected bot info
        if bot_list and sel_bot_idx < len(bot_list):
            sel_key, sel_data = bot_list[sel_bot_idx]
            draw_text(screen,
                      f"Depth: {sel_data['depth']}  |  "
                      f"Imprecision: {sel_data['imprecision']}  |  "
                      f"ELO: {sel_data['elo']}",
                      f["small"], TEXT_DIM, 20, H - 100)

        # Buttons
        go_rect  = draw_button(screen, "Play!", f["bold"],
                               370, H-60, 120, 44, GREEN,
                               hover=(370<=mx<=490 and H-60<=my<=H-16))
        back_rect = draw_button(screen, "Back", f["bold"],
                                150, H-60, 120, 44, RED,
                                hover=(150<=mx<=270 and H-60<=my<=H-16))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Tab clicks
                for i in range(3):
                    if my < 119 and i * tab_w <= mx < (i+1)*tab_w:
                        sel_style   = i
                        sel_bot_idx = 0

                # Bot list clicks
                for rect, idx in bot_rects:
                    if rect.collidepoint(mx, my):
                        sel_bot_idx = idx

                # Play button
                if go_rect.collidepoint(mx, my) and bot_list:
                    sel_key, sel_data = bot_list[sel_bot_idx]
                    from ai.styles import load_style
                    weights = load_style(sel_data["style"])
                    return (sel_key, sel_data["style"],
                            sel_data["elo"],
                            weights,
                            sel_data["depth"],
                            sel_data["imprecision"])

                # Back button
                if back_rect.collidepoint(mx, my):
                    return None

        pygame.display.flip()
        clock.tick(30)


# ── Post-Game Screen ──────────────────────────────────────────
def post_game_screen(screen, f, result: str,
                     bot_name: str, bot_elo: int,
                     bot_style: str, analysis: list):
    """Show result, rating change, analysis summary. Returns 'menu'."""
    # Record game and update rating
    data   = record_game(bot_name, bot_elo, bot_style, result)
    reward = check_and_award(bot_name, result, data["rating"])
    clock  = pygame.time.Clock()
    scroll = 0

    result_colour = {
        "win":  GREEN,
        "loss": RED,
        "draw": ACCENT,
    }[result]
    result_text = {"win": "You Win!", "loss": "You Lose",
                   "draw": "Draw"}[result]

    analysis_text = format_analysis(analysis)
    lines         = analysis_text.split("\n")

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, result_text, f["title"],
                  result_colour, W//2, 30, center=True)

        # Rating change
        history = data["history"]
        if history:
            last   = history[-1]
            change = last["change"]
            sign   = "+" if change > 0 else ""
            draw_text(screen,
                      f"Rating: {last['rating_before']} → "
                      f"{last['rating_after']}  ({sign}{change})",
                      f["heading"], WHITE, W//2, 90, center=True)

        # Reward message
        if reward:
            draw_text(screen, reward, f["small"],
                      HIGHLIGHT, W//2, 130, center=True)

        # Analysis lines
        y = 165 + scroll
        for line in lines:
            if 155 < y < H - 60:
                colour = WHITE if line.startswith("Move") else TEXT_DIM
                if "??" in line:
                    colour = RED
                elif "!?" in line:
                    colour = ACCENT
                draw_text(screen, line, f["small"], colour, 20, y)
            y += 22

        # Scroll hint
        draw_text(screen, "↑↓ scroll analysis",
                  f["small"], TEXT_DIM, W//2, H-48, center=True)

        menu_rect = draw_button(screen, "Main Menu", f["bold"],
                                220, H-40, 200, 36, LIGHT_GREY,
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
def history_screen(screen, f):
    """Show rating history chart and recent games. Returns 'menu'."""
    clock   = pygame.time.Clock()
    history = get_rating_history()
    stats   = get_stats()

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "Rating History", f["heading"],
                  ACCENT, W//2, 20, center=True)

        # Stats row
        draw_text(screen,
                  f"Rating: {stats['rating']}   "
                  f"W:{stats['wins']} D:{stats['draws']} L:{stats['losses']}   "
                  f"Win rate: {stats['win_rate']}%",
                  f["small"], TEXT_DIM, W//2, 58, center=True)

        # Rating chart
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
                y = chart_y + chart_h - int(
                    (h["rating"] - min_r) / r_range * chart_h)
                points.append((x, y))

            if len(points) >= 2:
                pygame.draw.lines(screen, HIGHLIGHT, False, points, 2)
            for p in points:
                pygame.draw.circle(screen, WHITE, p, 3)

            # Y axis labels
            draw_text(screen, str(int(max_r)), f["small"],
                      TEXT_DIM, chart_x + chart_w + 5, chart_y)
            draw_text(screen, str(int(min_r)), f["small"],
                      TEXT_DIM, chart_x + chart_w + 5,
                      chart_y + chart_h - 15)
        else:
            draw_text(screen, "Play some games to see your chart!",
                      f["body"], TEXT_DIM,
                      chart_x + chart_w//2, chart_y + chart_h//2,
                      center=True)

        # Recent games list
        draw_text(screen, "Recent games:", f["bold"], WHITE, 40, 305)
        from game.rating import get_recent_games
        recent = get_recent_games(8)
        for i, game in enumerate(reversed(recent)):
            y      = 330 + i * 28
            colour = (GREEN if game["result"] == "win" else
                      RED   if game["result"] == "loss" else ACCENT)
            sign   = "+" if game["change"] > 0 else ""
            draw_text(screen,
                      f"{game['result'].upper():<5} vs {game['bot']:<22} "
                      f"{sign}{game['change']:>6}  →  {game['rating_after']}",
                      f["small"], colour, 40, y)

        back_rect = draw_button(screen, "Back", f["bold"],
                                220, H-50, 200, 40, LIGHT_GREY,
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
def ladder_screen(screen, f):
    """Show challenge ladder progress. Returns ('play', bot_config) or 'menu'."""
    clock    = pygame.time.Clock()
    rating   = get_rating()
    progress = get_ladder_progress(rating)
    scroll   = 0

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill(GREY)

        draw_text(screen, "Challenge Ladder",
                  f["heading"], ACCENT, W//2, 20, center=True)
        draw_text(screen,
                  f"Completed: {progress['completed']}/{progress['total']}  |  "
                  f"Your rating: {rating}",
                  f["small"], TEXT_DIM, W//2, 58, center=True)

        completed = progress["completed_rungs"]
        y_start   = 90 + scroll

        rung_rects = []
        for rung in progress["rungs"]:
            y          = y_start + (rung["rung"] - 1) * 64
            is_done    = rung["rung"] in completed
            is_locked  = rating < rung["unlock_at"]
            is_next    = (not is_done and not is_locked)

            if is_done:
                colour = GREEN
                icon   = "✓"
            elif is_locked:
                colour = LIGHT_GREY
                icon   = "🔒"
            else:
                colour = ACCENT if is_next else LIGHT_GREY
                icon   = "▶"

            rect = draw_button(
                screen,
                f"{icon}  Rung {rung['rung']}: {rung['label']:<18} "
                f"({rung['style'].title()}, {rung['bot_elo']} ELO)",
                f["body"], 20, y, 600, 52, colour,
                hover=(not is_locked and 20<=mx<=620 and y<=my<=y+52)
            )

            if not is_locked:
                rung_rects.append((rect, rung))

            # Description
            if 90 < y < H - 80:
                draw_text(screen, rung["description"],
                          f["small"], TEXT_DIM, 30, y + 36)

        back_rect = draw_button(screen, "Back", f["bold"],
                                220, H-46, 200, 38, RED,
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
                        weights = load_style(rung["style"])
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