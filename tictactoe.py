import pygame
import sys
import math
import random
import os
from menu import run_menu 
from ai import get_best_move_iterative, get_priority_moves, check_winner_fast, clear_eval_cache, WIN_CONSEC

# --- Path Helper for PyInstaller ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Fallback for when running in standard Python environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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
small_font = pygame.font.SysFont("Arial", 18) # 👈 NEW: For clock/status text

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

# AI state flag
ai_is_thinking = False # 👈 NEW: Flag to display "thinking"


# --- Sound Effects Setup --- 👈 NEW
try:
    # Replace these paths with your actual sound file names/paths
    sfx = {
        "place": pygame.mixer.Sound(resource_path("sounds/place_piece.wav")), 
        "win": pygame.mixer.Sound(resource_path("sounds/win_game.wav")),
        # "error": pygame.mixer.Sound("sounds/error.wav") # For clicking an occupied cell
    }
except pygame.error as e:
    print(f"Warning: Could not load sound files. Sounds will be disabled. Error: {e}")
    sfx = {}


    # --- Background Music Setup --- 👈 NEW
MUSIC_FILE = resource_path("sounds/background_music.mp3") # Use an MP3 or Ogg file
# Check if the music file exists before loading (optional, but good practice)
try:
    pygame.mixer.music.load(MUSIC_FILE)
    music_loaded = True
except pygame.error as e:
    print(f"Warning: Could not load background music file. Music will be disabled. Error: {e}")
    music_loaded = False

def play_music(current_settings):
    """Starts playing background music if music is enabled."""
    global music_loaded
    if music_loaded and current_settings.get("music", True) and not pygame.mixer.music.get_busy():
        # Play the music on a loop (-1 means infinite loop)
        pygame.mixer.music.play(-1)

def stop_music():
    """Stops the background music."""
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()

def toggle_music(current_settings):
    """Stops or starts music based on the current setting."""
    if current_settings.get("music", True):
        play_music(current_settings)
    else:
        stop_music()


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
def format_time(seconds):
    """Converts seconds to M:SS format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


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
    
    # --- Clock Display ---
    time_color = O_COLOR if data['time_left'] < 60 else TEXT_COLOR # Red if less than 60s
    time_text = ui_font.render(format_time(data['time_left']), True, time_color)
    screen.blit(time_text, (panel_rect.centerx - time_text.get_width() // 2, panel_rect.top + 210))
    
    # --- Status Indicator ---
    status_text = ""
    status_color = (0, 150, 0) # Green for active
    
    if current_player == player_symbol and not popup_active and not pause_active:
        if player_symbol == "O" and data["name"] == "Computer" and ai_is_thinking:
            status_text = "thinking..."
            status_color = (150, 0, 150) # Purple when thinking
        else:
            status_text = "YOUR TURN"
    
    status_surface = small_font.render(status_text, True, status_color)
    screen.blit(status_surface, status_surface.get_rect(center=(panel_rect.centerx, panel_rect.top + 250)))


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
    
    # Draw Turn Info in Center
    if not game_over and not pause_active:
        turn_text_str = f"{players[current_player]['name']}'s Turn"
        turn_text = ui_font.render(turn_text_str, True, players[current_player]["color"])
        screen.blit(turn_text, turn_text.get_rect(center=(SIDE_PANEL_WIDTH // 2, 30)))


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


# Using a simplified check based on the global 'settings' variable:
def play_sfx(sound_key, current_settings):
    """Plays a sound if SFX are enabled in settings."""
    if current_settings.get("sfx", True) and sound_key in sfx:
        sfx[sound_key].play()


# --- Game loop ---
def run_game(vs_ai=False, saved_state=None, difficult=0, human_symbol="X", game_settings=None):
    global board, current_player, game_over, popup_active, pause_active, winner, ai_is_thinking, HUMAN_PLAYER, AI_PLAYER
    
    # Determine the AI player symbol based on the human choice
    AI_PLAYER = "O" if human_symbol == "X" else "X"
    HUMAN_PLAYER = human_symbol
    
    # --- Initialization ---
    if saved_state:
        # Load state
        board = saved_state["board"]
        current_player = saved_state["current_player"]
        players.update(saved_state["players"])
        game_over = saved_state["game_over"]
        popup_active = False
        pause_active = False
        winner = None
        
        # Reset symbols and names based on saved state for display
        players[AI_PLAYER]["name"] = "Computer" if vs_ai else ("Player 1" if AI_PLAYER == "X" else "Player 2")
        players[HUMAN_PLAYER]["name"] = "Player"
        
    else:
        # New Game setup
        board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        game_over = False
        popup_active = False
        pause_active = False
        winner = None
        players["X"]["time_left"] = 300
        players["O"]["time_left"] = 300
        
        # Set initial current player based on standard rules (X goes first)
        current_player = "X" 
        if vs_ai:
            players[AI_PLAYER]["name"] = "Computer"
            players[HUMAN_PLAYER]["name"] = "Player"
        else:
            # PvP mode names
            if human_symbol == "X":
                players["X"]["name"] = f"Player 1 (X)"
                players["O"]["name"] = "Player 2 (O)"
            else:
                players["X"]["name"] = f"Player 2 (X)"
                players["O"]["name"] = "Player 1 (O)"

    # --- Start BGM when game starts/resumes --- 👈 NEW
    if game_settings["music"]:
        toggle_music(game_settings)
        
    clock = pygame.time.Clock()
    running = True
    ai_should_move = False 

    # If the AI player (O or X) is supposed to move first
    if vs_ai and current_player == AI_PLAYER:
        ai_should_move = True
        
    last_tick_time = pygame.time.get_ticks()

    while running:
        # --- Time Calculation (60 FPS tick) ---
        current_time = pygame.time.get_ticks()
        time_elapsed = (current_time - last_tick_time) / 1000.0 # Time elapsed in seconds
        last_tick_time = current_time

        if pause_active or popup_active:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        elif not pygame.mixer.music.get_busy() and game_settings.get("music", True):
            pygame.mixer.music.unpause()
        
        # --- Timer Logic ---
        if not game_over and not popup_active and not pause_active and not ai_is_thinking:
            # Only tick down if the current player is NOT the AI (or if it's PVP)
            if current_player == HUMAN_PLAYER or not vs_ai:
                current_time_left = players[current_player]["time_left"]
                if current_time_left > 0:
                    players[current_player]["time_left"] = max(0, current_time_left - time_elapsed)
                else:
                    # Player runs out of time - opponent wins
                    game_over = True
                    popup_active = True
                    winner = AI_PLAYER if vs_ai else ("O" if current_player == "X" else "X")
                    players[winner]["points"] += 1

        # --- Drawing and UI Updates ---            
        mouse_pos = pygame.mouse.get_pos()
        hover_cell = None
        if SIDE_PANEL_WIDTH < mouse_pos[0] < SIDE_PANEL_WIDTH + BOARD_PIXEL and mouse_pos[1] > TOP_UI_HEIGHT:
            hover_cell = ((mouse_pos[0] - SIDE_PANEL_WIDTH) // CELL_SIZE,
                          (mouse_pos[1] - TOP_UI_HEIGHT) // CELL_SIZE)

        screen.fill(BG_COLOR)
        pause_rect, exit_rect = draw_top_ui(mouse_pos)
        # Player 1 is the human player in AI mode, or 'X' in PvP mode (from menu choice)
        player_1_symbol = human_symbol
        
        # Player 2 is the opponent
        player_2_symbol = "O" if player_1_symbol == "X" else "X"
        
        # Draw Player 1 (the human who chose the symbol) on the left panel
        draw_player_panel("left", player_1_symbol)
        
        # Draw Player 2 (the opponent) on the right panel
        draw_player_panel("right", player_2_symbol)
        
        draw_board(hover_cell)

        if popup_active:
            continue_rect = show_popup(winner)
        elif pause_active:
            cont_rect, menu_rect = show_pause_popup()

        # --- AI TURN ---
        if vs_ai and ai_should_move and not game_over:
            ai_is_thinking = True
            pygame.display.flip()
            pygame.time.wait(200)
            
            clear_eval_cache()
            
            # AI_PLAYER is now dynamic (X or O)
            move = ai_move(difficulty=difficult)
            ai_is_thinking = False
            
            if move:
                x, y = move
                board[y][x] = AI_PLAYER # Use AI_PLAYER for move placement
                if check_win(x, y, AI_PLAYER): # Use AI_PLAYER for win check
                    players[AI_PLAYER]["points"] += 1
                    game_over = True
                    popup_active = True
                    winner = AI_PLAYER
                else:
                    current_player = HUMAN_PLAYER # Switch to human player
            ai_should_move = False      # Reset flag

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_music() # Stop music before quitting
                pygame.quit()
                sys.exit()

            if popup_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if continue_rect.collidepoint(event.pos):
                    # Reset board for next round
                    board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                    game_over = False
                    popup_active = False
                    winner = None
                    
                    # --- NEW: Symbol Swap Logic for PvP ---
                    if not vs_ai:
                        # If the previous round started with 'X', the next round starts with 'O'
                        # and vice versa. We swap the symbol that goes first.
                        human_symbol = "O" if human_symbol == "X" else "X"
                        if human_symbol == "X":
                            players["X"]["name"] = f"Player 1 (X)"
                            players["O"]["name"] = "Player 2 (O)"
                        else:
                            players["X"]["name"] = f"Player 2 (X)"
                            players["O"]["name"] = "Player 1 (O)"
                    else:
                        # In AI mode, 'X' always starts the next round (or whoever is HUMAN_PLAYER)
                        current_player = HUMAN_PLAYER

            elif pause_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cont_rect.collidepoint(event.pos):
                    pause_active = False
                elif menu_rect.collidepoint(event.pos):
                    stop_music() # Stop music when going back to main menu
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
                    
                    if board[y][x] == " ":
                        player_symbol = current_player
                        
                        # Check if it's the human's turn (either human vs AI, or any turn in PvP)
                        is_human_turn = not vs_ai or (vs_ai and current_player == HUMAN_PLAYER)
                        
                        if is_human_turn:
                            
                            board[y][x] = player_symbol

                            # Play sound on successful move
                            play_sfx("place", game_settings) # 👈 SFX: PLACE
                            
                            if check_win(x, y, player_symbol):
                                players[player_symbol]["points"] += 1
                                game_over = True
                                popup_active = True
                                winner = player_symbol
                                play_sfx("win", game_settings) # 👈 SFX: WIN
                            else:
                                # Switch turn
                                if player_symbol == "X":
                                    current_player = "O"
                                elif player_symbol == "O":
                                    current_player = "X"
                                    
                                if vs_ai and current_player == AI_PLAYER:
                                    ai_should_move = True  # Defer AI turn for AI mode
                                    
                            pygame.display.flip()

        pygame.display.flip()
        clock.tick(60)


# --- Entry Point ---
if __name__ == "__main__":
    saved_state = None
    in_progress = False

    # Default settings (used for 'continue' if saved_state exists)
    last_vs_ai = False
    last_difficulty = 0
    last_human_symbol = "X"

    settings = {}

    # Start music immediately when the program starts
    # play_music(game_settings) # 👈 START MUSIC

    while True:
        menu_choice = run_menu(in_progress=in_progress)
        print(menu_choice)

        # After returning from menu, re-apply the music setting if it changed

        if isinstance(menu_choice, tuple):
            settings = menu_choice[1] 
        if isinstance(menu_choice, tuple):
            menu_choice = menu_choice[0] 
        toggle_music(settings) # 👈 RE-APPLY SETTING

        result = None

        # Logic for running the game based on menu choice
        if isinstance(menu_choice, tuple):
            mode = menu_choice[0]
            
            if mode == "ai":
                # menu_choice is ("ai", chosen_symbol, difficulty)
                last_vs_ai = True
                last_human_symbol = menu_choice[1]
                last_difficulty = menu_choice[2]
                
                result = run_game(
                    vs_ai=True, 
                    human_symbol=last_human_symbol, 
                    difficult=last_difficulty,
                    game_settings=settings
                )
                
            elif mode == "pvp":
                # menu_choice is ("pvp", chosen_symbol)
                last_vs_ai = False
                last_human_symbol = menu_choice[1]
                last_difficulty = 0
                
                # The human_symbol determines who starts, but in PvP both are human
                result = run_game(
                    vs_ai=False, 
                    human_symbol=last_human_symbol,
                    game_settings=settings # 'X' or 'O' used to set Player 1/2 names correctly
                )

        elif menu_choice == "continue" and saved_state:
            # Use last settings if continuing a game (difficulty and vs_ai are already saved in state)
            result = run_game(
                vs_ai=last_vs_ai, 
                saved_state=saved_state, 
                human_symbol=last_human_symbol, # Important: pass the symbol back to correctly set names
                difficult=last_difficulty,
                game_settings=settings
            )
        else:
            break

        # Logic for returning to menu
        if isinstance(result, tuple) and result[0] == "menu":
            in_progress = True
            saved_state = result[1]
        else:
            in_progress = False
            saved_state = None # Clear state if game finished normally