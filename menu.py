import pygame
import sys

pygame.init()

# --- Window setup ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Main Menu")

# --- Colors ---
BG_COLOR = (240, 245, 255)
BUTTON_COLOR = (120, 180, 255)
BUTTON_HOVER = (100, 160, 240)
TEXT_COLOR = (20, 20, 20)
DISABLED_COLOR = (200, 200, 200)
TITLE_COLOR = (40, 70, 140)

# --- Fonts ---
title_font = pygame.font.SysFont("Arial", 60, bold=True)
button_font = pygame.font.SysFont("Arial", 28, bold=True)
info_font = pygame.font.SysFont("Arial", 22)

# --- Settings ---
settings = {
    "sfx": True,
    "music": True,
}

# --- Menu State ---
menu_state = "main"  # "main", "settings", "howto", "mode_select", "difficulty_select"
game_in_progress = False


# --- Utility Functions ---
def draw_text_center(text, font, color, surface, y):
    text_obj = font.render(text, True, color)
    rect = text_obj.get_rect(center=(WIDTH // 2, y))
    surface.blit(text_obj, rect)
    return rect


def draw_button(text, y, enabled=True):
    mouse = pygame.mouse.get_pos()
    button_rect = pygame.Rect(WIDTH // 2 - 150, y, 300, 60)

    color = DISABLED_COLOR if not enabled else (
        BUTTON_HOVER if button_rect.collidepoint(mouse) else BUTTON_COLOR
    )

    pygame.draw.rect(screen, color, button_rect, border_radius=10)
    text_color = (150, 150, 150) if not enabled else TEXT_COLOR
    label = button_font.render(text, True, text_color)
    screen.blit(label, label.get_rect(center=button_rect.center))
    return button_rect


def difficulty_menu():
    """Choose difficulty after selecting 'Player vs Computer'."""
    screen.fill(BG_COLOR)
    draw_text_center("Select Difficulty", title_font, TITLE_COLOR, screen, 120)

    easy_btn = draw_button("Easy", 240)
    normal_btn = draw_button("Normal", 320)
    hard_btn = draw_button("Hard", 400)
    back_btn = draw_button("Back", 500)

    return {
        "easy": easy_btn,
        "normal": normal_btn,
        "hard": hard_btn,
        "back": back_btn
    }


# --- Screens ---
def main_menu():
    screen.fill(BG_COLOR)
    draw_text_center("Five in a Row", title_font, TITLE_COLOR, screen, 100)

    continue_btn = draw_button("Continue", 200, enabled=game_in_progress)
    new_game_btn = draw_button("New Game", 280)
    settings_btn = draw_button("Settings", 360)
    howto_btn = draw_button("How to Play", 440)
    exit_btn = draw_button("Exit", 520)

    return {
        "continue": continue_btn,
        "new": new_game_btn,
        "settings": settings_btn,
        "howto": howto_btn,
        "exit": exit_btn
    }


def mode_select_menu():
    """Mode selection popup after pressing New Game"""
    screen.fill(BG_COLOR)
    draw_text_center("Select Game Mode", title_font, TITLE_COLOR, screen, 120)

    pvp_btn = draw_button("Player vs Player", 260)
    ai_btn = draw_button("Player vs Computer", 340)
    back_btn = draw_button("Back", 460)

    return {
        "pvp": pvp_btn,
        "ai": ai_btn,
        "back": back_btn
    }


def settings_menu():
    screen.fill(BG_COLOR)
    draw_text_center("Settings", title_font, TITLE_COLOR, screen, 100)

    sfx_text = f"SFX: {'ON' if settings['sfx'] else 'OFF'}"
    music_text = f"Music: {'ON' if settings['music'] else 'OFF'}"

    sfx_btn = draw_button(sfx_text, 240)
    music_btn = draw_button(music_text, 320)
    back_btn = draw_button("Back", 460)

    return {
        "sfx": sfx_btn,
        "music": music_btn,
        "back": back_btn
    }


def how_to_play_menu():
    screen.fill(BG_COLOR)
    draw_text_center("How to Play", title_font, TITLE_COLOR, screen, 80)

    lines = [
        "1. The game is played on a 15x15 grid.",
        "2. Players take turns placing X or O.",
        "3. The first to get 5 in a row (horizontally, vertically, or diagonally)",
        "   wins the game.",
        "4. Use the mouse to click and place your symbol.",
        "5. You can restart or exit from the top buttons.",
    ]

    y = 180
    for line in lines:
        draw_text_center(line, info_font, TEXT_COLOR, screen, y)
        y += 40

    back_btn = draw_button("Back", 520)
    return {"back": back_btn}


# --- Main Menu Loop ---
def run_menu(in_progress=False):
    global menu_state, game_in_progress
    game_in_progress = in_progress
    clock = pygame.time.Clock()

    while True:
        screen.fill(BG_COLOR)

        # --- Draw current screen ---
        if menu_state == "main":
            buttons = main_menu()
        elif menu_state == "settings":
            buttons = settings_menu()
        elif menu_state == "howto":
            buttons = how_to_play_menu()
        elif menu_state == "mode_select":
            buttons = mode_select_menu()
        elif menu_state == "difficulty_select":
            buttons = difficulty_menu()

        # --- Handle Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_state == "main":
                    if buttons["continue"].collidepoint(event.pos) and game_in_progress:
                        return "continue"
                    elif buttons["new"].collidepoint(event.pos):
                        menu_state = "mode_select"
                    elif buttons["settings"].collidepoint(event.pos):
                        menu_state = "settings"
                    elif buttons["howto"].collidepoint(event.pos):
                        menu_state = "howto"
                    elif buttons["exit"].collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

                elif menu_state == "settings":
                    if buttons["sfx"].collidepoint(event.pos):
                        settings["sfx"] = not settings["sfx"]
                    elif buttons["music"].collidepoint(event.pos):
                        settings["music"] = not settings["music"]
                    elif buttons["back"].collidepoint(event.pos):
                        menu_state = "main"

                elif menu_state == "howto":
                    if buttons["back"].collidepoint(event.pos):
                        menu_state = "main"

                elif menu_state == "mode_select":
                    if buttons["pvp"].collidepoint(event.pos):
                        return "pvp"
                    elif buttons["ai"].collidepoint(event.pos):
                        menu_state = "difficulty_select"  # ✅ FIXED: go to difficulty selection
                    elif buttons["back"].collidepoint(event.pos):
                        menu_state = "main"

                elif menu_state == "difficulty_select":
                    if buttons["easy"].collidepoint(event.pos):
                        return ("ai", 0)
                    elif buttons["normal"].collidepoint(event.pos):
                        return ("ai", 1)
                    elif buttons["hard"].collidepoint(event.pos):
                        return ("ai", 2)
                    elif buttons["back"].collidepoint(event.pos):
                        menu_state = "mode_select"

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    result = run_menu(in_progress=True)
    print("Menu selection:", result)
