import pygame
import sys
import math
import random
from menu import run_menu  # <-- Make sure menu.py is in the same directory

# --- Configuration ---
BOARD_SIZE = 15
CELL_SIZE = 40
WIN_LENGTH = 5
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


# --- Functions ---
def draw_board(hover_pos=None):
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
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dx, dy in directions:
        count = 1
        for dir in [1, -1]:
            nx, ny = x + dx * dir, y + dy * dir
            while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == player:
                count += 1
                nx += dx * dir
                ny += dy * dir
        if count >= WIN_LENGTH:
            return True
    return False


AI_PLAYER = "O"
HUMAN_PLAYER = "X"
MAX_DEPTH = 3  # adjustable depending on difficulty
WIN_CONSEC = 5

def ai_move(difficult=0):
    """AI chooses move based on difficulty."""
    empty_cells = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE) if board[y][x] == " "]
    if not empty_cells:
        return None

    if difficult == 0:
        # Easy: random
        return random.choice(empty_cells)
    elif difficult == 1:
        # Medium: heuristic only
        best_score = -math.inf
        best_move = None
        for (x, y) in empty_cells:
            score = evaluate_move(x, y, AI_PLAYER)
            if score > best_score:
                best_score = score
                best_move = (x, y)
        return best_move
    else:
        # Hard: minimax + alpha-beta
        _, move = minimax(board, MAX_DEPTH, -math.inf, math.inf, True)
        return move


def get_candidate_moves(board, radius=2):
    """Return all empty cells within a given distance from existing moves."""
    candidates = set()
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if board[y][x] != " ":
                # Explore a square region around this move
                for dy in range(-radius, radius + 1):
                    for dx in range(-radius, radius + 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE:
                            if board[ny][nx] == " ":
                                candidates.add((nx, ny))
    # If board is empty, fall back to center
    if not candidates:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
    return list(candidates)


# ----------------------- Minimax with Alpha-Beta -----------------------
# ----------------------- Minimax with Alpha-Beta (CORRECTED) -----------------------
def minimax(state, depth, alpha, beta, maximizing):
    """Minimax algorithm with alpha-beta pruning."""
    # Note: check_winner and is_full must use the passed 'state'
    winner = check_winner(state)
    if winner == AI_PLAYER:
        # AI wins: very high score
        return (100000, None)
    elif winner == HUMAN_PLAYER:
        # Human wins: very low score
        return (-100000, None)
    elif depth == 0 or is_full(state):
        # Depth limit or draw: evaluate current board
        return (evaluate_board(state), None)

    # Use get_candidate_moves on the current state
    candidate_moves = get_candidate_moves(state)
    if not candidate_moves:
        return (0, None)

    if maximizing:
        best_score = -math.inf
        best_move = None
        
        for (x, y) in candidate_moves:
            # 1. Create a deep copy of the current state
            new_state = [row[:] for row in state]
            
            # 2. Make the move on the new state
            new_state[y][x] = AI_PLAYER
            
            # 3. Recurse with the new state
            score, _ = minimax(new_state, depth - 1, alpha, beta, False)
            
            # **Removed:** state[y][x] = " " # No need to unmake if using a copy

            if score > best_score:
                best_score = score
                best_move = (x, y)
            
            # Alpha-Beta Pruning update (Maximizer tries to raise alpha)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score, best_move
    
    else: # Minimizing player (HUMAN_PLAYER)
        best_score = math.inf
        best_move = None
        
        for (x, y) in candidate_moves: # **Fix 3:** Use candidate_moves derived from 'state'
            # 1. Create a deep copy of the current state
            new_state = [row[:] for row in state]
            
            # 2. Make the move on the new state
            new_state[y][x] = HUMAN_PLAYER
            
            # 3. Recurse with the new state
            score, _ = minimax(new_state, depth - 1, alpha, beta, True)
            
            # **Removed:** state[y][x] = " " # No need to unmake if using a copy

            if score < best_score:
                best_score = score
                best_move = (x, y)
            
            # Alpha-Beta Pruning update (Minimizer tries to lower beta)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score, best_move


# ----------------------- Heuristic Evaluation -----------------------
def evaluate_board(state):
    """Evaluate the full board heuristically."""
    score = 0
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if state[y][x] == AI_PLAYER:
                score += evaluate_move(x, y, AI_PLAYER)
            elif state[y][x] == HUMAN_PLAYER:
                score -= evaluate_move(x, y, HUMAN_PLAYER)
    return score


def evaluate_move(x, y, player):
    """Heuristic for a move based on consecutive pieces and blocking."""
    opponent = HUMAN_PLAYER if player == AI_PLAYER else AI_PLAYER
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    score = 0

    for dx, dy in directions:
        count = 1
        open_ends = 0

        # forward
        nx, ny = x + dx, y + dy
        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == player:
            count += 1
            nx += dx
            ny += dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == " ":
            open_ends += 1

        # backward
        nx, ny = x - dx, y - dy
        while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == player:
            count += 1
            nx -= dx
            ny -= dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == " ":
            open_ends += 1

        # scoring logic (more aggressive for near-wins)
        if count >= WIN_CONSEC:
            score += 100000
        elif count == 4 and open_ends > 0:
            score += 5000
        elif count == 3 and open_ends > 0:
            score += 500
        elif count == 2 and open_ends > 0:
            score += 50
        elif count == 1 and open_ends > 0:
            score += 10

    return score


# ----------------------- Helper Functions -----------------------
def is_full(state):
    return all(cell != " " for row in state for cell in row)


def check_winner(state):
    """Return 'X' or 'O' if either has 5 in a row, else None."""
    for y in range(BOARD_SIZE):
        for x in range(BOARD_SIZE):
            if state[y][x] == " ":
                continue
            player = state[y][x]
            for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                if all(
                    0 <= x + i * dx < BOARD_SIZE and
                    0 <= y + i * dy < BOARD_SIZE and
                    state[y + i * dy][x + i * dx] == player
                    for i in range(WIN_CONSEC)
                ):
                    return player
    return None


def evaluate_move(x, y, player):
    """Heuristic utility evaluation for a given move."""
    opponent = "X" if player == "O" else "O"

    # Temporarily make move
    board[y][x] = player
    my_score = count_potential(x, y, player)
    board[y][x] = opponent
    opp_score = count_potential(x, y, opponent)
    board[y][x] = " "  # revert

    # Distance bonus: prefer moves near existing pieces
    proximity = proximity_score(x, y)

    # Final weighted score
    return my_score * 2 + opp_score * 1.5 + proximity * 0.5


def count_potential(x, y, player):
    """Count how strong a move is based on connected stones."""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    total = 0
    for dx, dy in directions:
        count = 1  # the current cell
        for dir in [1, -1]:
            nx, ny = x + dx * dir, y + dy * dir
            while 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] == player:
                count += 1
                nx += dx * dir
                ny += dy * dir
        total += count ** 2  # higher weight for longer lines
    return total


def proximity_score(x, y):
    """Encourage moves closer to existing stones."""
    nearby_bonus = 0
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and board[ny][nx] != " ":
                nearby_bonus += 1 / (1 + abs(dx) + abs(dy))
    return nearby_bonus


# def ai_take_turn():
#     move = random_ai_move()
#     if move:
#         x, y = move
#         board[y][x] = "O"
#         if check_win(x, y, "O"):
#             players["O"]["points"] += 1
#             return True, "O"
#     return False, None


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
    import random
    global board, current_player, game_over, popup_active, pause_active, winner

    # Restore from saved state if exists
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

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- Winner popup ---
            if popup_active and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if continue_rect.collidepoint(event.pos):
                    # Reset after win
                    board = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
                    current_player = "X"
                    game_over = False
                    popup_active = False
                    winner = None

            # --- Pause popup ---
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

            # --- Main interactions ---
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
                            current_player = "O" if vs_ai else "O" if current_player == "X" else "X"

                            if vs_ai and current_player == "O" and not game_over:
                                move = ai_move(difficult=difficult)
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

        # --- AI Turn ---
        if vs_ai and not game_over and not popup_active and current_player == "O":
            pygame.time.delay(300)  # small delay for realism
            empty_cells = [(x, y) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE) if board[y][x] == " "]
            if empty_cells:
                x, y = random.choice(empty_cells)
                board[y][x] = "O"
                if check_win(x, y, "O"):
                    players["O"]["points"] += 1
                    game_over = True
                    popup_active = True
                    winner = "O"
                else:
                    current_player = "X"

        pygame.display.flip()
        clock.tick(60)


# --- Entry Point ---
if __name__ == "__main__":
    saved_state = None
    in_progress = False

    while True:
        menu_choice = run_menu(in_progress=in_progress)

        if isinstance(menu_choice, tuple) and menu_choice[0] == "ai":
            difficulty = menu_choice[1]
            result = run_game(vs_ai=True, difficult=difficulty)
            if isinstance(result, tuple) and result[0] == "menu":
                in_progress = True
                saved_state = result[1]
                continue
            else:
                in_progress = False
        elif menu_choice == "pvp":
            result = run_game(vs_ai=False)
            if isinstance(result, tuple) and result[0] == "menu":
                in_progress = True
                saved_state = result[1]
                continue
            else:
                in_progress = False
        elif menu_choice == "continue" and saved_state:
            result = run_game(saved_state)
            if isinstance(result, tuple) and result[0] == "menu":
                in_progress = True
                saved_state = result[1]
                continue
            else:
                in_progress = False
        else:
            break
