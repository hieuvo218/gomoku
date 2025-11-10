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
menu_state = "main"  # "main", "settings", "howto", "mode_select", "difficulty_select", "symbol_select"
game_in_progress = False

# --- Global Variable to track chosen symbol for AI mode ---
selected_mode = None
selected_symbol_for_game = "X"


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

    pvp_btn = draw_button("Player vs Player (Local)", 220)
    ai_btn = draw_button("Player vs Computer", 300)
    host_btn = draw_button("Host Online Game", 380)
    join_btn = draw_button("Join Online Game", 460)
    back_btn = draw_button("Back", 540)

    return {
        "pvp": pvp_btn,
        "ai": ai_btn,
        "host": host_btn,
        "join": join_btn,
        "back": back_btn
    }



# --- New Screen: Symbol Selection ---
def symbol_select_menu():
    """Choose which symbol ('X' or 'O') the human player will use."""
    screen.fill(BG_COLOR)
    draw_text_center("Choose Your Symbol", title_font, TITLE_COLOR, screen, 120)
    draw_text_center("(X goes first, O goes second)", info_font, TEXT_COLOR, screen, 180)

    x_btn = draw_button("Play as X (Go First)", 280)
    o_btn = draw_button("Play as O (Go Second)", 360)
    back_btn = draw_button("Back", 500)

    return {
        "x": x_btn,
        "o": o_btn,
        "back": back_btn
    }


def host_join_menu():
    """Screen for joining a host by entering IP address."""
    import pygame_textinput
    screen.fill(BG_COLOR)
    draw_text_center("Join Game", title_font, TITLE_COLOR, screen, 100)
    draw_text_center("Enter Host IP:", info_font, TEXT_COLOR, screen, 200)

    # --- Input box setup ---
    textinput = pygame_textinput.TextInputVisualizer(font=button_font, cursor_color=(0, 0, 0))
    back_btn = draw_button("Back", 480)
    join_btn = draw_button("Connect", 400)

    clock = pygame.time.Clock()
    user_ip = ""

    while True:
        screen.fill(BG_COLOR)
        draw_text_center("Join Game", title_font, TITLE_COLOR, screen, 100)
        draw_text_center("Enter Host IP:", info_font, TEXT_COLOR, screen, 200)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.collidepoint(event.pos):
                    return None  # Return to previous menu
                elif join_btn.collidepoint(event.pos):
                    return user_ip.strip()

        textinput.update(events)
        user_ip = textinput.value
        screen.blit(textinput.surface, (WIDTH // 2 - 100, 280))

        back_btn = draw_button("Back", 480)
        join_btn = draw_button("Connect", 400)

        pygame.display.flip()
        clock.tick(30)



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
    global menu_state, game_in_progress, selected_mode, selected_symbol_for_game
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
        elif menu_state == "symbol_select":
            buttons = symbol_select_menu()
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
                    # ... (rest of main menu logic)
                    elif buttons["settings"].collidepoint(event.pos):
                        menu_state = "settings"
                    elif buttons["howto"].collidepoint(event.pos):
                        menu_state = "howto"
                    elif buttons["exit"].collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

                elif menu_state == "settings":
                    # ... (settings logic)
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
                        selected_mode = "pvp"
                        menu_state = "symbol_select"
                    elif buttons["ai"].collidepoint(event.pos):
                        selected_mode = "ai"
                        menu_state = "symbol_select"
                    elif buttons["host"].collidepoint(event.pos):
                        # Host game mode selected
                        return ("host_online", "X"), settings  # Host always starts as X
                    elif buttons["join"].collidepoint(event.pos):
                        # Ask for IP
                        ip = host_join_menu()
                        if ip:
                            return ("join_online", "O", ip), settings  # Joining player is O
                    elif buttons["back"].collidepoint(event.pos):
                        menu_state = "main"


                elif menu_state == "symbol_select":
                    if buttons["x"].collidepoint(event.pos):
                        selected_symbol_for_game = "X"
                        if selected_mode == "pvp":
                            return ("pvp", "X"), settings
                        elif selected_mode == "ai":
                            menu_state = "difficulty_select" # Next for AI
                    elif buttons["o"].collidepoint(event.pos):
                        selected_symbol_for_game = "O"
                        if selected_mode == "pvp":
                            return ("pvp", "O"), settings
                        elif selected_mode == "ai":
                            menu_state = "difficulty_select" # Next for AI
                    elif buttons["back"].collidepoint(event.pos):
                        menu_state = "mode_select"

                elif menu_state == "difficulty_select":
                    # Return (mode, symbol, difficulty)
                    difficulty = -1
                    if buttons["easy"].collidepoint(event.pos):
                        difficulty = 0
                    elif buttons["normal"].collidepoint(event.pos):
                        difficulty = 1
                    elif buttons["hard"].collidepoint(event.pos):
                        difficulty = 2

                    if difficulty != -1:
                        # Return mode, the human player's chosen symbol, and difficulty level
                        return ("ai", selected_symbol_for_game, difficulty), settings
                    elif buttons["back"].collidepoint(event.pos):
                        menu_state = "symbol_select"

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    result = run_menu(in_progress=True)
    print("Menu selection:", result)
