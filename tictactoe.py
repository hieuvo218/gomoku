import pygame
import sys
import math
import random
from menu import run_menu 
from ai import get_best_move_iterative, get_priority_moves, check_winner_fast, clear_eval_cache, WIN_CONSEC

# --- Configuration ---
BOARD_SIZE = 15
CELL_SIZE = 40
# WIN_LENGTH = 5 # No longer needed here, uses ai.WIN_CONSEC
SIDE_PANEL_WIDTH = 220
TOP_UI_HEIGHT = 60
BOARD_PIXEL = BOARD_SIZE * CELL_SIZE
WINDOW_WIDTH = BOARD_PIXEL + SIDE_PANEL_WIDTH * 2
WINDOW_HEIGHT = BOARD_PIXEL + TOP_UI_HEIGHT

# Colors
BG_COLOR = (245, 245, 245)
GRID_COLOR = (180, 180, 180)
HOVER_COLOR = (210, 230, 255)
X_COLOR = (30, 30, 30)
O_COLOR = (200, 50, 50)
BUTTON_COLOR = (100, 180, 255)
BUTTON_HOVER = (80, 160, 240)
EXIT_COLOR = (255, 120, 120)
EXIT_HOVER = (255, 100, 100)
TEXT_COLOR = (30, 30, 30)
PANEL_COLOR = (225, 225, 225)
SEPARATOR_COLOR = (180, 180, 180)

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Five in a Row")

font = pygame.font.SysFont("Arial", int(CELL_SIZE / 1.3), bold=True)
ui_font = pygame.font.SysFont("Arial", 24, bold=True)
msg_font = pygame.font.SysFont("Arial", 40, bold=True)

# Game state
board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
current_player = "X"
game_over = False
popup_active = False
winner = None
pause_active = False

players = {
    "X": {"name": "Player 1", "color": X_COLOR, "points": 0},
    "O": {"name": "Player 2", "color": O_COLOR, "points": 0},
}


# --- Core Game Functions ---
def draw_board(hover_pos=None):
    # ... (Keep this function as is)
    board_left = SIDE_PANEL_WIDTH
    board_top = TOP_UI_HEIGHT
    pygame.draw.rect(screen, BG_COLOR, (board_left, board_top, BOARD_PIXEL, BOARD_PIXEL))

    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            rect = pygame.Rect(board_left + x * CELL_SIZE, board_top + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if hover_pos == (x, y) and board[y][x] == " " and not game_over and not popup_active:
                pygame.draw.rect(screen, HOVER_COLOR, rect)
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)
            symbol = board[y][x]
            if symbol != " ":
                color = X_COLOR if symbol == "X" else O_COLOR
                text = font.render(symbol, True, color)
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)


def check_win(x, y, player):
    # This is a redundant function now, but keep for compatibility with player move
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dx, dy in directions:
        count = 1
        for dir in [1, -1]:
            nx, ny = x + dx * dir, y + dy * dir
            while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == player:
                count += 1
                nx += dx * dir
                ny += dy * dir
        if count >= WIN_CONSEC:
            return True
    return False

# --- AI Integration (Constants and Function) ---
AI_PLAYER = "O"
HUMAN_PLAYER = "X"

def ai_move(difficulty=0):
    """Delegates AI move selection based on difficulty."""
    if difficulty == 0:
        # Simple Random Move
        empty_cells = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE) if board[y][x] == " "]
        return random.choice(empty_cells) if empty_cells else None
    
    # Minimax based moves
    if difficulty == 1:
        # Easy/Medium: Use move ordering and depth 1 search for speed
        moves = get_priority_moves(board, AI_PLAYER, HUMAN_PLAYER, BOARD_SIZE, max_moves=5)
        if moves:
            # Check the best move without full minimax for speed
            return moves[0]
        
    elif difficulty >= 2:
        # Hard: Use iterative deepening minimax (up to 4 seconds, max depth 6)
        # We pass the board by reference (mutating is fine since minimax_optimized handles unmaking moves)
        return get_best_move_iterative(
            board, AI_PLAYER, HUMAN_PLAYER, BOARD_SIZE, 
            max_time=4.0 if difficulty == 3 else 2.0, 
            max_depth=6 if difficulty == 3 else 4
        )
    
    # Fallback
    empty_cells = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE) if board[y][x] == " "]
    return random.choice(empty_cells) if empty_cells else None

# ----------------------- REMOVED MINIMAX AND HEURISTIC FUNCTIONS -----------------------
# The following functions have been moved to ai.py and are now imported or replaced:
# * get_candidate_moves
# * minimax (replaced by minimax_optimized logic in ai.py)
# * is_full (moved to ai.py)
# * check_winner (replaced by check_winner_fast in ai.py)
# * evaluate_board (moved to ai.py)
# * ... and all other evaluation/priority helpers

# --- UI Functions ---
# ... (Keep all UI functions like draw_player_panel, draw_top_ui, show_popup, show_pause_popup as is)

def draw_player_panel(side, player_symbol):
    data = players[player_symbol]
    panel_rect = pygame.Rect(0, TOP_UI_HEIGHT, SIDE_PANEL_WIDTH, BOARD_PIXEL) if side == "left" else \
                 pygame.Rect(WINDOW_WIDTH - SIDE_PANEL_WIDTH, TOP_UI_HEIGHT, SIDE_PANEL_WIDTH, BOARD_PIXEL)

    pygame.draw.rect(screen, PANEL_COLOR, panel_rect)
    pygame.draw.rect(screen, SEPARATOR_COLOR, panel_rect, 2)

    name_text = ui_font.render(data["name"], True, data["color"])
    screen.blit(name_text, (panel_rect.centerx - name_text.get_width() // 2, panel_rect.top + 40))
    symbol_text = font.render(player_symbol, True, data["color"])
    screen.blit(symbol_text, (panel_rect.centerx - symbol_text.get_width() // 2, panel_rect.top + 90))
    points_text = ui_font.render(f"Points: {data['points']}", True, TEXT_COLOR)
    screen.blit(points_text, (panel_rect.centerx - points_text.get_width() // 2, panel_rect.top + 150))

    if current_player == player_symbol and not popup_active:
        pygame.draw.circle(screen, (255, 200, 80), (panel_rect.centerx, panel_rect.top + 200), 12)


def draw_top_ui(mouse_pos):
    pygame.draw.rect(screen, (220, 220, 220), (0, 0, WINDOW_WIDTH, TOP_UI_HEIGHT))
    pause_rect = pygame.Rect(WINDOW_WIDTH // 2 - 60, 10, 120, 40)
    exit_rect = pygame.Rect(WINDOW_WIDTH - SIDE_PANEL_WIDTH + 20, 10, 120, 40)

    pause_color = BUTTON_HOVER if pause_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    exit_color = EXIT_HOVER if exit_rect.collidepoint(mouse_pos) else EXIT_COLOR

    pygame.draw.rect(screen, pause_color, pause_rect, border_radius=10)
    pygame.draw.rect(screen, exit_color, exit_rect, border_radius=10)

    pause_text = ui_font.render("Pause", True, TEXT_COLOR)
    exit_text = ui_font.render("Exit", True, TEXT_COLOR)

    screen.blit(pause_text, pause_text.get_rect(center=pause_rect.center))
    screen.blit(exit_text, exit_text.get_rect(center=exit_rect.center))

    return pause_rect, exit_rect


def show_popup(winner):
    overlay = pygame.Surface((BOARD_PIXEL, BOARD_PIXEL))
    overlay.set_alpha(200)
    overlay.fill((255, 255, 255))
    screen.blit(overlay, (SIDE_PANEL_WIDTH, TOP_UI_HEIGHT))

    title = msg_font.render(f"🎉 {players[winner]['name']} Wins! 🎉", True, TEXT_COLOR)
    title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
    screen.blit(title, title_rect)

    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 10, 200, 60)
    mouse_pos = pygame.mouse.get_pos()
    color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, button_rect, border_radius=10)
    btn_text = ui_font.render("Continue", True, TEXT_COLOR)
    screen.blit(btn_text, btn_text.get_rect(center=button_rect.center))
    return button_rect


def show_pause_popup():
    """Pause overlay with Continue / Main Menu choices"""
    overlay = pygame.Surface((BOARD_PIXEL, BOARD_PIXEL))
    overlay.set_alpha(220)
    overlay.fill((250, 250, 250))
    screen.blit(overlay, (SIDE_PANEL_WIDTH, TOP_UI_HEIGHT))

    title = msg_font.render("⏸ Paused", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80)))

    cont_btn = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 10, 200, 60)
    menu_btn = pygame.Rect(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 70, 200, 60)
    mouse_pos = pygame.mouse.get_pos()

    for rect, text in [(cont_btn, "Continue"), (menu_btn, "Main Menu")]:
        color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=10)
        txt = ui_font.render(text, True, TEXT_COLOR)
        screen.blit(txt, txt.get_rect(center=rect.center))

    return cont_btn, menu_btn


# --- Game loop ---
def run_game(vs_ai=False, saved_state=None, difficult=0):
    global board, current_player, game_over, popup_active, pause_active, winner

    # ... (Keep game state setup as is)
    if saved_state:
        board = saved_state["board"]
        current_player = saved_state["current_player"]
        players.update(saved_state["players"])
        game_over = saved_state["game_over"]
        popup_active = False
        pause_active = False
        winner = None
    else:
        board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        current_player = "X"
        game_over = False
        popup_active = False
        pause_active = False
        winner = None

    if vs_ai:
        players["O"]["name"] = "Computer"
    else:
        players["O"]["name"] = "Player 2"

    clock = pygame.time.Clock()
    running = True
    ai_should_move = False 

    while running:
        mouse_pos = pygame.mouse.get_pos()
        hover_cell = None
        if SIDE_PANEL_WIDTH < mouse_pos[0] < SIDE_PANEL_WIDTH + BOARD_PIXEL and mouse_pos[1] > TOP_UI_HEIGHT:
            hover_cell = ((mouse_pos[0] - SIDE_PANEL_WIDTH) // CELL_SIZE,
                          (mouse_pos[1] - TOP_UI_HEIGHT) // CELL_SIZE)

        screen.fill(BG_COLOR)
        pause_rect, exit_rect = draw_top_ui(mouse_pos)
        draw_player_panel("left", "X")
        draw_player_panel("right", "O")
        draw_board(hover_cell)

        if popup_active:
            continue_rect = show_popup(winner)
        elif pause_active:
            cont_rect, menu_rect = show_pause_popup()

        # --- AI TURN ---
        if vs_ai and ai_should_move and not game_over:
            pygame.display.flip()       # Update before thinking
            pygame.time.wait(200)       # Small pause for realism
            
            # Reset cache before AI search starts
            clear_eval_cache()
            
            move = ai_move(difficulty=difficult)
            if move:
                x, y = move
                board[y][x] = "O"
                if check_win(x, y, "O"):
                    players["O"]["points"] += 1
                    game_over = True
                    popup_active = True
                    winner = "O"
                else:
                    current_player = "X"
            ai_should_move = False      # Reset flag

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if popup_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if continue_rect.collidepoint(event.pos):
                    board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                    current_player = "X"
                    game_over = False
                    popup_active = False
                    winner = None

            elif pause_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cont_rect.collidepoint(event.pos):
                    pause_active = False
                elif menu_rect.collidepoint(event.pos):
                    saved_state = {
                        "board": [row[:] for row in board],
                        "current_player": current_player,
                        "players": {p: data.copy() for p, data in players.items()},
                        "game_over": game_over,
                    }
                    return ("menu", saved_state)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pause_rect.collidepoint(event.pos):
                    pause_active = True
                elif exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif not game_over and not popup_active and not pause_active and hover_cell:
                    x, y = hover_cell
                    if board[y][x] == " " and current_player == "X":
                        board[y][x] = "X"
                        if check_win(x, y, "X"):
                            players["X"]["points"] += 1
                            game_over = True
                            popup_active = True
                            winner = "X"
                        else:
                            current_player = "O"
                            if vs_ai:
                                ai_should_move = True  # Defer AI turn to next loop
                        pygame.display.flip()

        pygame.display.flip()
        clock.tick(60)


# --- Entry Point ---
if __name__ == "__main__":
    saved_state = None
    in_progress = False

    while True:
        menu_choice = run_menu(in_progress=in_progress)

        # Logic for running the game based on menu choice
        if isinstance(menu_choice, tuple) and menu_choice[0] == "ai":
            difficulty = menu_choice[1]
            result = run_game(vs_ai=True, difficult=difficulty)
        elif menu_choice == "pvp":
            result = run_game(vs_ai=False)
        elif menu_choice == "continue" and saved_state:
            # Check if vs_ai was enabled in the saved state (simple check based on Player 2 name)
            vs_ai_setting = players.get("O", {}).get("name") == "Computer"
            # Since difficulty isn't saved, we default to the highest if it was an AI game
            difficulty_setting = 3 if vs_ai_setting else 0 
            
            result = run_game(vs_ai=vs_ai_setting, saved_state=saved_state, difficult=difficulty_setting)
        else:
            break

        # Logic for returning to menu
        if isinstance(result, tuple) and result[0] == "menu":
            in_progress = True
            saved_state = result[1]
        else:
            in_progress = False