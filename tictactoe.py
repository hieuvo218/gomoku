import sys
import math
import random
import os

import pygame

from network import NetworkGame
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


def run_game_ai(saved_state=None, difficult=0, human_symbol="X", game_settings=None):
    """
    Play vs AI. human_symbol is "X" or "O". game_settings is a dict { 'sfx': bool, 'music': bool }.
    """
    global board, current_player, game_over, popup_active, pause_active, winner, ai_is_thinking, HUMAN_PLAYER, AI_PLAYER
    start_symbol = "X"

    if game_settings is None:
        game_settings = {"sfx": True, "music": True}

    # assign dynamic symbols
    HUMAN_PLAYER = human_symbol
    AI_PLAYER = "O" if HUMAN_PLAYER == "X" else "X"

    # --- Restore or new game setup ---
    if saved_state:
        board = [row[:] for row in saved_state["board"]]
        current_player = saved_state["current_player"]
        players.update(saved_state["players"])
        game_over = saved_state["game_over"]
        popup_active = False
        pause_active = False
        winner = None
    else:
        board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        current_player = "X"  # X starts by default
        game_over = False
        popup_active = False
        pause_active = False
        winner = None
        players["X"]["time_left"] = 300
        players["O"]["time_left"] = 300
        players["X"]["name"] = "Player"
        players["O"]["name"] = "Computer"

    # start/restore music
    if game_settings.get("music", True):
        toggle_music(game_settings)

    clock = pygame.time.Clock()
    running = True
    ai_should_move = False
    ai_is_thinking = False
    last_tick_time = pygame.time.get_ticks()


    while running:
        # If AI should move first (human chose O)
        if current_player == AI_PLAYER:
            ai_should_move = True
        # --- Time (delta) ---
        now = pygame.time.get_ticks()
        dt = (now - last_tick_time) / 1000.0
        last_tick_time = now

        # pause music when popup/pause
        if pause_active or popup_active:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        elif game_settings.get("music", True) and not pygame.mixer.music.get_busy():
            pygame.mixer.music.unpause()

        # --- Timer countdown (only for human when appropriate) ---
        if not game_over and not popup_active and not pause_active and not ai_is_thinking:
            # only decrement the current player's timer; if it's AI's turn, don't subtract human's time
            if current_player in players:
                # in AI mode we only decrement human's timer when it's their turn
                if (current_player == HUMAN_PLAYER) or (current_player != AI_PLAYER and not True):
                    players[current_player]["time_left"] = max(0, players[current_player]["time_left"] - dt)
                    if players[current_player]["time_left"] <= 0:
                        # human ran out of time -> AI wins
                        game_over = True
                        popup_active = True
                        winner = AI_PLAYER
                        players[winner]["points"] += 1

        # --- Draw UI ---
        mouse_pos = pygame.mouse.get_pos()
        hover_cell = None
        if SIDE_PANEL_WIDTH < mouse_pos[0] < SIDE_PANEL_WIDTH + BOARD_PIXEL and mouse_pos[1] > TOP_UI_HEIGHT:
            hover_cell = ((mouse_pos[0] - SIDE_PANEL_WIDTH) // CELL_SIZE,
                          (mouse_pos[1] - TOP_UI_HEIGHT) // CELL_SIZE)

        screen.fill(BG_COLOR)
        pause_rect, exit_rect = draw_top_ui(mouse_pos)
        # left panel should show the human_symbol
        draw_player_panel("left", HUMAN_PLAYER)
        draw_player_panel("right", AI_PLAYER)
        draw_board(hover_cell)

        if popup_active:
            continue_rect = show_popup(winner)
        elif pause_active:
            cont_rect, menu_rect = show_pause_popup()

        # --- AI logic (deferred to main loop so UI updates before compute) ---
        if ai_should_move and not game_over:
            ai_is_thinking = True
            pygame.display.flip()
            pygame.time.wait(150)  # small breathing room

            clear_eval_cache()
            move = ai_move(difficulty=difficult)
            ai_is_thinking = False

            if move:
                mx, my = move
                board[my][mx] = AI_PLAYER
                if check_win(mx, my, AI_PLAYER):
                    players[AI_PLAYER]["points"] += 1
                    game_over = True
                    popup_active = True
                    winner = AI_PLAYER
                    if game_settings.get("sfx", True):
                        play_sfx("win", game_settings)
                else:
                    current_player = HUMAN_PLAYER
            ai_should_move = False

        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if game_settings.get("music", True):
                    stop_music()
                pygame.quit()
                sys.exit()

            if popup_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if continue_rect.collidepoint(event.pos):
                    # reset for next round — keep human/ai symbols stable
                    board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                    game_over = False
                    popup_active = False
                    winner = None
                    start_symbol = "O" if start_symbol == "X" else "X"
                    current_player = start_symbol
                    ai_should_move = False
                    players["X"]["time_left"] = 300
                    players["O"]["time_left"] = 300

            elif pause_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cont_rect.collidepoint(event.pos):
                    pause_active = False
                elif menu_rect.collidepoint(event.pos):
                    if game_settings.get("music", True):
                        stop_music()
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
                    if game_settings.get("music", True):
                        stop_music()
                    pygame.quit()
                    sys.exit()
                elif not game_over and not popup_active and not pause_active and hover_cell:
                    x, y = hover_cell
                    # Only allow human to play on their turns
                    if board[y][x] == " " and current_player == HUMAN_PLAYER:
                        board[y][x] = HUMAN_PLAYER
                        if game_settings.get("sfx", True):
                            play_sfx("place", game_settings)
                        if check_win(x, y, HUMAN_PLAYER):
                            players[HUMAN_PLAYER]["points"] += 1
                            game_over = True
                            popup_active = True
                            winner = HUMAN_PLAYER
                            if game_settings.get("sfx", True):
                                play_sfx("win", game_settings)
                        else:
                            current_player = AI_PLAYER
                            ai_should_move = True  # AI will move next

        pygame.display.flip()
        clock.tick(60)


def run_game_pvp(saved_state=None, human_symbol="X", game_settings=None):
    """
    Two players on the same computer. human_symbol is the symbol to display on the left panel (informational).
    game_settings controls SFX/music (used if you want sounds in PvP).
    """
    global board, current_player, game_over, popup_active, pause_active, winner
    start_symbol = "X"

    if game_settings is None:
        game_settings = {"sfx": True, "music": True}

    # initialize or restore
    if saved_state:
        board = [row[:] for row in saved_state["board"]]
        current_player = saved_state["current_player"]
        players.update(saved_state["players"])
        game_over = saved_state["game_over"]
        popup_active = False
        pause_active = False
        winner = None
    else:
        board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        current_player = start_symbol
        game_over = False
        popup_active = False
        pause_active = False
        winner = None
        players["X"]["time_left"] = 300
        players["O"]["time_left"] = 300
        # set display names
        players["X"]["name"] = "Player 1 (X)" if human_symbol == "X" else "Player 2 (X)"
        players["O"]["name"] = "Player 2 (O)" if human_symbol == "X" else "Player 1 (O)"

    # music
    if game_settings.get("music", True):
        toggle_music(game_settings)

    clock = pygame.time.Clock()
    running = True
    last_tick_time = pygame.time.get_ticks()

    while running:
        # --- Time delta ---
        now = pygame.time.get_ticks()
        dt = (now - last_tick_time) / 1000.0
        last_tick_time = now

        # pause/unpause music
        if pause_active or popup_active:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        elif game_settings.get("music", True) and not pygame.mixer.music.get_busy():
            pygame.mixer.music.unpause()

        # --- Timer countdown for current player ---
        if not game_over and not popup_active and not pause_active:
            if current_player in players:
                players[current_player]["time_left"] = max(0, players[current_player]["time_left"] - dt)
                if players[current_player]["time_left"] <= 0:
                    game_over = True
                    popup_active = True
                    winner = "O" if current_player == "X" else "X"
                    players[winner]["points"] += 1

        # --- Draw UI ---
        mouse_pos = pygame.mouse.get_pos()
        hover_cell = None
        if SIDE_PANEL_WIDTH < mouse_pos[0] < SIDE_PANEL_WIDTH + BOARD_PIXEL and mouse_pos[1] > TOP_UI_HEIGHT:
            hover_cell = ((mouse_pos[0] - SIDE_PANEL_WIDTH) // CELL_SIZE,
                          (mouse_pos[1] - TOP_UI_HEIGHT) // CELL_SIZE)

        screen.fill(BG_COLOR)
        pause_rect, exit_rect = draw_top_ui(mouse_pos)
        # left panel shows the player assigned to human_symbol for clarity
        draw_player_panel("left", human_symbol)
        draw_player_panel("right", "O" if human_symbol == "X" else "X")
        draw_board(hover_cell)

        if popup_active:
            continue_rect = show_popup(winner)
        elif pause_active:
            cont_rect, menu_rect = show_pause_popup()

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if game_settings.get("music", True):
                    stop_music()
                pygame.quit()
                sys.exit()

            if popup_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if continue_rect.collidepoint(event.pos):
                    board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                    start_symbol = "O" if start_symbol == "X" else "X"
                    current_player = start_symbol
                    game_over = False
                    popup_active = False
                    winner = None
                    players["X"]["time_left"] = 300
                    players["O"]["time_left"] = 300

            elif pause_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cont_rect.collidepoint(event.pos):
                    pause_active = False
                elif menu_rect.collidepoint(event.pos):
                    if game_settings.get("music", True):
                        stop_music()
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
                    if game_settings.get("music", True):
                        stop_music()
                    pygame.quit()
                    sys.exit()
                elif not game_over and not popup_active and not pause_active and hover_cell:
                    x, y = hover_cell
                    if board[y][x] == " ":
                        board[y][x] = current_player
                        if game_settings.get("sfx", True):
                            play_sfx("place", game_settings)
                        if check_win(x, y, current_player):
                            players[current_player]["points"] += 1
                            game_over = True
                            popup_active = True
                            winner = current_player
                            if game_settings.get("sfx", True):
                                play_sfx("win", game_settings)
                            
                        else:
                            current_player = "O" if current_player == "X" else "X"

        pygame.display.flip()
        clock.tick(60)


import pygame
import sys
import socket
from network import NetworkGame


def play_online(is_host=False, host_ip=None, username=None, game_settings=None):
    """
    Play Gomoku online between two computers in the same local network.
    - Host waits for connection (shows waiting screen)
    - Client connects and starts once connected
    """
    import socket, threading, time
    global board, current_player, game_over, popup_active, pause_active, winner

    if game_settings is None:
        game_settings = {"sfx": True, "music": True}

    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()

    def get_local_ip():
        """Get LAN IP reliably even if gethostname() fails."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # --- Setup network ---
    if is_host and (host_ip is None):
        host_ip = get_local_ip()

    from network import NetworkGame
    net = NetworkGame(is_host=is_host, host_ip=host_ip)

    connected = False
    opponent_name = None
    name_received = False
    
    # Continue tracking
    i_pressed_continue = False
    opponent_pressed_continue = False
    waiting_for_opponent = False

    # Disconnect tracking
    opponent_disconnected = False
    disconnect_reason = ""
    disconnect_time = None
    auto_return_delay = 15.0

    def network_thread():
        nonlocal connected
        try:
            net.start()
            connected = True
        except Exception as e:
            print(f"[NETWORK THREAD ERROR] {e}")

    def on_name_received(name):
        nonlocal opponent_name, name_received
        opponent_name = name
        name_received = True
        print(f"[NETWORK] Opponent's name: {opponent_name}")
    
    # Continue callback
    def on_continue_received():
        nonlocal opponent_pressed_continue
        opponent_pressed_continue = True
        print("[GAME] Opponent pressed continue!")

    # Disconnect callback
    def on_disconnect(reason):
        nonlocal opponent_disconnected, disconnect_reason, disconnect_time
        opponent_disconnected = True
        disconnect_reason = reason
        disconnect_time = time.time()
        print(f"[NETWORK] Disconnected: {reason}")

    net.name_callback = on_name_received
    net.continue_callback = on_continue_received  
    net.disconnect_callback = on_disconnect

    # Start networking in a background thread
    t = threading.Thread(target=network_thread, daemon=True)
    t.start()

    # --- Waiting screen (host only) ---
    if is_host:
        waiting = True
        font = pygame.font.SysFont("Arial", 36)
        small_font = pygame.font.SysFont("Arial", 28)

        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    net.close()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    net.close()
                    return

            screen.fill((230, 240, 255))
            text = font.render("Waiting for another player to join...", True, (0, 0, 0))
            ip_text = small_font.render(f"Your IP: {host_ip}", True, (40, 40, 100))
            cancel_text = small_font.render("Press ESC to cancel", True, (120, 120, 120))
            
            screen.blit(text, (100, 200))
            screen.blit(ip_text, (100, 300))
            screen.blit(cancel_text, (100, 400))
            pygame.display.flip()

            if connected or net.is_connected:
                time.sleep(0.5)
                net.send_name(username)
                waiting = False

            clock.tick(30)

    else:
        # --- Client mode ---
        font = pygame.font.SysFont("Arial", 36, bold=True)
        small_font = pygame.font.SysFont("Arial", 24)
        sent_name = False

        while True:
            screen.fill((230, 240, 255))
            text = font.render(f"Connecting to host {host_ip}...", True, (40, 40, 100))
            screen.blit(text, text.get_rect(center=(400, 260)))

            cancel_text = small_font.render("Press ESC to cancel", True, (120, 120, 120))
            screen.blit(cancel_text, cancel_text.get_rect(center=(400, 360)))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    net.close()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    net.close()
                    return

            if (net.is_connected or connected) and not sent_name:
                time.sleep(0.5)
                net.send_name(username)
                sent_name = True
                break

            clock.tick(30)

    # Wait a moment for name exchange
    print("[GAME] Waiting for name exchange...")
    wait_start = time.time()
    while not name_received and (time.time() - wait_start < 3):
        time.sleep(0.1)
    
    if not name_received:
        print("[GAME] Name exchange timeout, using default name")
        opponent_name = "Opponent"

    # --- Connected! Start the online game ---
    print("[GAME] Both players connected! Starting game...")
    print(f"[GAME] Your name: {username}")
    print(f"[GAME] Opponent's name: {opponent_name}")
    
    # Initialize game state
    board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    current_player = "X"
    start_symbol = "X"
    game_over = False
    popup_active = False
    pause_active = False
    winner = None
    players["X"]["time_left"] = 300
    players["O"]["time_left"] = 300

    # music
    if game_settings.get("music", True):
        toggle_music(game_settings)

    clock = pygame.time.Clock()
    running = True
    last_tick_time = pygame.time.get_ticks()
    
    # Decide which player is X and O
    if is_host:
        my_symbol = "X"
        opponent_symbol = "O"
    else:
        my_symbol = "O"
        opponent_symbol = "X"

    # Set display names
    players["X"]["name"] = f"{username} (X)" if my_symbol == "X" else f"{opponent_name} (X)"
    players["O"]["name"] = f"{username} (O)" if my_symbol == "O" else f"{opponent_name} (O)"
    
    print(f"[GAME] You are player: {my_symbol}")

    # Track if it's my turn
    my_turn = (my_symbol == "X")  # X always goes first
    
    def on_move_received(move):
        """Callback when opponent moves."""
        global current_player, game_over, winner, popup_active
        nonlocal my_turn
        try:
            x, y = move["x"], move["y"]
            
            if board[y][x] != ' ':
                print(f"[ERROR] Opponent tried invalid move at ({x}, {y})")
                return
            
            board[y][x] = opponent_symbol
            play_sfx("place", game_settings)
            print(f"[GAME] Opponent placed {opponent_symbol} at ({x}, {y})")
            
            if check_win(x, y, opponent_symbol):
                game_over = True
                popup_active = True
                winner = opponent_symbol
                print(f"[GAME] {opponent_symbol} wins!")
                players[opponent_symbol]["points"] += 1
                if game_settings.get("sfx", True):
                    play_sfx("win", game_settings)
            else:
                current_player = my_symbol
                my_turn = True
                print(f"[GAME] Now it's your turn! my_turn={my_turn}")
                
        except Exception as e:
            print(f"[MOVE RECEIVED ERROR] {e}")
            import traceback
            traceback.print_exc()

    net.callback = on_move_received

    # --- Main online game loop ---
    running = True
    
    while running:
        # Check for disconnection
        if opponent_disconnected and disconnect_time:
            elapsed = time.time() - disconnect_time
            if elapsed >= auto_return_delay:
                print("[GAME] Opponent disconnected, returning to menu.")
                net.close()
                return ("menu", None)

        # --- Time delta ---
        now = pygame.time.get_ticks()
        dt = (now - last_tick_time) / 1000.0
        last_tick_time = now

        # pause/unpause music
        if pause_active or popup_active or opponent_disconnected:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        elif game_settings.get("music", True) and not pygame.mixer.music.get_busy():
            pygame.mixer.music.unpause()

        # --- Timer countdown for current player ---
        if not game_over and not popup_active and not pause_active and not opponent_disconnected:
            if current_player in players:
                players[current_player]["time_left"] = max(0, players[current_player]["time_left"] - dt)
                if players[current_player]["time_left"] <= 0:
                    game_over = True
                    popup_active = True
                    winner = "O" if current_player == "X" else "X"
                    players[winner]["points"] += 1

        # --- Draw UI ---
        mouse_pos = pygame.mouse.get_pos()
        hover_cell = None
        if not opponent_disconnected:
            if SIDE_PANEL_WIDTH < mouse_pos[0] < SIDE_PANEL_WIDTH + BOARD_PIXEL and mouse_pos[1] > TOP_UI_HEIGHT:
                hover_cell = ((mouse_pos[0] - SIDE_PANEL_WIDTH) // CELL_SIZE,
                            (mouse_pos[1] - TOP_UI_HEIGHT) // CELL_SIZE)

        screen.fill(BG_COLOR)
        pause_rect, exit_rect = draw_top_ui(mouse_pos)
        draw_player_panel("left", "X")
        draw_player_panel("right", "O")
        draw_board(hover_cell)

        if popup_active and not opponent_disconnected:
            continue_rect = show_popup(winner)
            
            # Show waiting message if player pressed continue
            if waiting_for_opponent:
                waiting_font = pygame.font.SysFont("Arial", 28, bold=True)
                waiting_text = waiting_font.render("Waiting for opponent...", True, (50, 50, 150))
                waiting_rect = waiting_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 120))
                
                # Draw semi-transparent background for text
                bg_rect = waiting_rect.inflate(40, 20)
                s = pygame.Surface((bg_rect.width, bg_rect.height))
                s.set_alpha(200)
                s.fill((255, 255, 255))
                screen.blit(s, bg_rect.topleft)
                
                screen.blit(waiting_text, waiting_rect)
                
        elif pause_active and not opponent_disconnected:
            cont_rect, menu_rect = show_pause_popup()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if net.is_connected:
                    net.send_disconnect("quit")
                net.close()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if opponent_disconnected:
                    print("[GAME] ESC pressed, returning to menu.")
                    net.close()
                    return
                else:
                    if net.is_connected:
                        net.send_disconnect("exit_to_menu")
                    net.close()
                    return

            if not opponent_disconnected:   
                if popup_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if continue_rect.collidepoint(event.pos):
                        # ✅ NEW: Handle synchronized continue
                        if not i_pressed_continue:
                            i_pressed_continue = True
                            waiting_for_opponent = True
                            net.send_continue()
                            print("[GAME] You pressed continue, waiting for opponent...")
                            
                            # Check if opponent already pressed
                            if opponent_pressed_continue:
                                print("[GAME] Both players ready, restarting game...")
                                # Reset game
                                board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                                start_symbol = "O" if start_symbol == "X" else "X"
                                current_player = start_symbol
                                my_turn = (my_symbol == current_player)
                                game_over = False
                                popup_active = False
                                winner = None
                                players["X"]["time_left"] = 300
                                players["O"]["time_left"] = 300
                                i_pressed_continue = False
                                opponent_pressed_continue = False
                                waiting_for_opponent = False
                    elif exit_rect.collidepoint(event.pos):
                        if game_settings.get("music", True):
                            stop_music()
                        pygame.quit()
                        sys.exit()

                elif pause_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if cont_rect.collidepoint(event.pos):
                        pause_active = False
                    elif menu_rect.collidepoint(event.pos):
                        if game_settings.get("music", True):
                            stop_music()
                        if net.is_connected:
                            net.send_disconnect("return_to_menu")
                        net.close()
                        saved_state = {
                            "board": [row[:] for row in board],
                            "current_player": current_player,
                            "players": {p: data.copy() for p, data in players.items()},
                            "game_over": game_over,
                        }
                        return ("menu", saved_state)
                    
                elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    if my_turn and hover_cell is not None:
                        x, y = hover_cell
                        if board[y][x] == ' ':
                            # Make the move
                            board[y][x] = my_symbol
                            if game_settings.get("sfx", True):
                                play_sfx("place", game_settings)
                            print(f"[GAME] You placed {my_symbol} at ({x}, {y})")
                            
                            # Send to opponent
                            net.send_move(x, y)
                            
                            # Check win
                            if check_win(x, y, my_symbol):
                                players[current_player]["points"] += 1
                                game_over = True
                                popup_active = True
                                winner = my_symbol
                                if game_settings.get("sfx", True):
                                    play_sfx("win", game_settings)
                                print(f"[GAME] You win!")
                            else:
                                current_player = opponent_symbol
                                my_turn = False
                                print(f"[GAME] Switched to opponent's turn. my_turn={my_turn}")
                    elif pause_rect.collidepoint(event.pos):
                        pause_active = True
                    elif exit_rect.collidepoint(event.pos):
                        if game_settings.get("music", True):
                            stop_music()
                        pygame.quit()
                        sys.exit()
                    else:
                        if not my_turn:
                            print("[GAME] Not your turn!")
        
        # Check if opponent pressed continue while we're waiting
        if not opponent_disconnected:
            if waiting_for_opponent and opponent_pressed_continue:
                print("[GAME] Both players ready, restarting game...")
                # Reset game
                board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                start_symbol = "O" if start_symbol == "X" else "X"
                current_player = start_symbol
                my_turn = (my_symbol == current_player)
                game_over = False
                popup_active = False
                winner = None
                players["X"]["time_left"] = 300
                players["O"]["time_left"] = 300
                i_pressed_continue = False
                opponent_pressed_continue = False
                waiting_for_opponent = False

        if opponent_disconnected:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Draw disconnect message
            disconnect_font = pygame.font.SysFont("Arial", 44, bold=True)
            medium_font = pygame.font.SysFont("Arial", 28)
            small_font = pygame.font.SysFont("Arial", 22)
            
            disconnect_text = disconnect_font.render("Opponent Disconnected", True, (255, 100, 100))
            disconnect_rect = disconnect_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
            
            reason_messages = {
                "quit": "Opponent quit the game",
                "exit_to_menu": "Opponent returned to menu",
                "return_to_menu": "Opponent returned to menu",
                "connection_reset": "Connection lost",
                "connection_aborted": "Connection aborted",
                "connection_closed": "Connection closed",
                "error": "Connection error",
                "opponent_disconnected": "Opponent left the game"
            }
            reason_text = medium_font.render(
                reason_messages.get(disconnect_reason, "Connection lost"),
                True, (220, 220, 220)
            )
            reason_rect = reason_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            
            # ✅ Calculate time remaining
            if disconnect_time:
                elapsed = time.time() - disconnect_time
                remaining = max(0, auto_return_delay - elapsed)
                
                if remaining > 0:
                    returning_text = medium_font.render(
                        f"Returning to menu in {remaining:.1f}s...",
                        True, (180, 180, 255)
                    )
                else:
                    returning_text = medium_font.render(
                        "Returning to menu...",
                        True, (180, 180, 255)
                    )
                returning_rect = returning_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
            
            instruction_text = small_font.render("Press ESC to return immediately", True, (150, 150, 150))
            instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 110))
            
            screen.blit(disconnect_text, disconnect_rect)
            screen.blit(reason_text, reason_rect)
            if disconnect_time:
                screen.blit(returning_text, returning_rect)
            screen.blit(instruction_text, instruction_rect)
        else:
            # Draw connection status
            small_font = pygame.font.SysFont("Arial", 18)
            status_text = small_font.render(
                f"Connected to {host_ip}" if not is_host else f"Hosting on {host_ip}",
                True, (100, 100, 100)
            )
            screen.blit(status_text, (30, WINDOW_HEIGHT - 30))

        pygame.display.flip()
        clock.tick(60)

    net.close()
    print("[GAME] Game ended, connection closed")


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
                
                result = run_game_ai(
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
                result = run_game_pvp( 
                    human_symbol=last_human_symbol,
                    game_settings=settings # 'X' or 'O' used to set Player 1/2 names correctly
                )
            
            elif mode == "host_online":
                last_vs_ai = False
                last_human_symbol = "X"  # Host is always X
                last_difficulty = 0
                username = menu_choice[1]  # menu_choice is ("host_online", username)
                
                play_online(is_host=True, username=username, game_settings=settings)
            
            elif mode == "join_online":
                last_vs_ai = False
                last_human_symbol = "O"  # Client is always O
                last_difficulty = 0
                
                host_ip = menu_choice[1]  # menu_choice is ("join_online", host_ip)
                username = menu_choice[2]
                play_online(is_host=False, host_ip=host_ip, username=username, game_settings=settings)

        elif menu_choice == "continue" and saved_state:
            # Use last settings if continuing a game (difficulty and vs_ai are already saved in state)
            if last_vs_ai:
                result = run_game_ai(
                    saved_state=saved_state, 
                    difficult=last_difficulty,
                    human_symbol=last_human_symbol,
                    game_settings=settings
                )
            else:
                result = run_game_pvp( 
                    saved_state=saved_state, 
                    human_symbol=last_human_symbol, # Important: pass the symbol back to correctly set names
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