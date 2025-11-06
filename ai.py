import math
import time
import random

# --- AI Configuration (Global Constants) ---
# These should match the constants in your main file
WIN_CONSEC = 5 # 5 in a row to win

# Cache for evaluation results (global to the module)
_eval_cache = {}

def clear_eval_cache():
    """Clear the evaluation cache between AI moves."""
    global _eval_cache
    _eval_cache = {}

# ----------------------- Core Utility Functions -----------------------

def is_full(state, board_size):
    """Check if the board is full."""
    return all(cell != " " for row in state for cell in row)

def check_winner_fast(state, board_size):
    """Return 'X' or 'O' if either has 5 in a row, else None."""
    for y in range(board_size):
        for x in range(board_size):
            if state[y][x] == " ":
                continue
            player = state[y][x]
            
            # Only check directions that could form new lines
            for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                if count_line_fast(state, x, y, dx, dy, player, board_size) >= WIN_CONSEC:
                    return player
    return None

def count_line_fast(state, x, y, dx, dy, player, board_size):
    """Fast line counting in both directions from (x, y)."""
    count = 1
    
    # Count forward
    nx, ny = x + dx, y + dy
    while (0 <= nx < board_size and 0 <= ny < board_size and 
           state[ny][nx] == player):
        count += 1
        nx += dx
        ny += dy
    
    # Count backward 
    nx, ny = x - dx, y - dy
    while (0 <= nx < board_size and 0 <= ny < board_size and 
           state[ny][nx] == player):
        count += 1
        nx -= dx
        ny -= dy
    
    return count

# ----------------------- Move Ordering / Priority -----------------------

def evaluate_move_fast(state, x, y, player, opponent, board_size):
    """
    Ultra-fast single move evaluation for move ordering (prioritizing wins/blocks).
    """
    # Place piece temporarily
    state[y][x] = player
    
    # Check immediate win
    max_line = 0
    for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
        line_count = count_line_fast(state, x, y, dx, dy, player, board_size)
        max_line = max(max_line, line_count)
    
    if max_line >= WIN_CONSEC:
        state[y][x] = ' '
        return 10000000 # Win!
    
    # Check defense (opponent's potential if *they* played here instead)
    state[y][x] = opponent # Pretend opponent played here
    def_max = 0
    for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
        line_count = count_line_fast(state, x, y, dx, dy, opponent, board_size)
        def_max = max(def_max, line_count)
    
    state[y][x] = ' '
    
    # Score based on longest line and block potential
    offense_score = score_move_patterns(max_line)
    defense_score = score_move_patterns(def_max)
    
    # Crucial: Prioritize blocking opponent's win/4-in-a-row
    if def_max >= WIN_CONSEC:
         return 9000000 # Block win!
    if def_max == 4:
         return offense_score + 900000 # Block 4 (high priority)
    
    # Return offensive score plus weighted defense score for general move ordering
    return offense_score + defense_score * 1.5 


def score_move_patterns(max_count):
    """Quick pattern scoring based on longest line."""
    if max_count >= WIN_CONSEC:
        return 10000000
    if max_count == 4:
        return 800000
    if max_count == 3:
        return 40000
    if max_count == 2:
        return 800
    return 100


def get_priority_moves(state, player, opponent, board_size, max_moves=15):
    """
    Get prioritized candidate moves (only the best ones) by scoring moves 
    near existing pieces.
    """
    moves_with_scores = []
    
    # First pass: only check cells near existing stones (within 2 spaces)
    candidates = set()
    for y in range(board_size):
        for x in range(board_size):
            if state[y][x] != ' ':
                # Add all empty cells within 2 spaces
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < board_size and 0 <= ny < board_size and
                            state[ny][nx] == ' '):
                            candidates.add((nx, ny))
    
    # If board is empty, start in center
    if not candidates:
        center = board_size // 2
        return [(center, center)]
    
    # Score each candidate
    for x, y in candidates:
        score = evaluate_move_fast(state, x, y, player, opponent, board_size)
        moves_with_scores.append((score, x, y))
    
    # Sort by score and return top moves
    moves_with_scores.sort(reverse=True, key=lambda m: m[0])
    
    # Return only top moves to search
    return [(x, y) for _, x, y in moves_with_scores[:max_moves]]

# ----------------------- Main Evaluation Heuristic -----------------------

def evaluate_board(state, ai_player, human_player, board_size):
    """
    Board evaluation function with caching.
    """
    # Create cache key from board state
    cache_key = tuple(tuple(row) for row in state)
    if cache_key in _eval_cache:
        return _eval_cache[cache_key]
    
    # CRITICAL: Check for immediate wins/losses first
    winner = check_winner_fast(state, board_size)
    if winner == ai_player:
        _eval_cache[cache_key] = 10000000
        return 10000000
    if winner == human_player:
        _eval_cache[cache_key] = -10000000
        return -10000000
    
    # Main heuristic calculation
    ai_score = evaluate_player_fast(state, ai_player, human_player, board_size)
    human_score = evaluate_player_fast(state, human_player, ai_player, board_size)
    
    # Weigh defense (Human score) slightly higher to encourage blocking
    result = ai_score - human_score * 1.5 
    _eval_cache[cache_key] = result
    return result


def evaluate_player_fast(state, player, opponent, board_size):
    """Calculates the combined strength of threats for a single player."""
    score = 0
    threat_levels = []
    
    # Scan for starting points of lines (only need to scan 1/4 of the board for each direction)
    for y in range(board_size):
        for x in range(board_size):
            if state[y][x] != player:
                continue
            
            # Check each direction (horizontal, vertical, two diagonals)
            for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                # Ensure we only count a line once (from its leftmost/topmost end)
                if (0 <= x - dx < board_size and 0 <= y - dy < board_size and 
                    state[y - dy][x - dx] == player):
                    continue
                
                line_score, threat_level = evaluate_line_fast(
                    state, x, y, dx, dy, player, board_size
                )
                score += line_score
                if threat_level >= 4:
                    threat_levels.append(threat_level)
    
    # Bonus for multiple strong threats (double-three, etc.)
    if len([t for t in threat_levels if t >= 4]) >= 2:
        score += 500000
    
    return score


def evaluate_line_fast(state, x, y, dx, dy, player, board_size):
    """Detailed line evaluation for open/closed 2, 3, 4."""
    count = 0
    # Find the contiguous block of 'player' stones
    
    # Go backwards to find the start of the block
    start_x, start_y = x, y
    while (0 <= start_x - dx < board_size and 0 <= start_y - dy < board_size and 
           state[start_y - dy][start_x - dx] == player):
        start_x -= dx
        start_y -= dy

    # Go forward from the start to count the block
    current_x, current_y = start_x, start_y
    while (0 <= current_x < board_size and 0 <= current_y < board_size and 
           state[current_y][current_x] == player):
        count += 1
        current_x += dx
        current_y += dy

    if count >= WIN_CONSEC:
        return 10000000, WIN_CONSEC
    
    # Check the immediate spaces outside the block
    end_x, end_y = current_x, current_y
    
    # Check backward end (before start_x, start_y)
    open_start = (0 <= start_x - dx < board_size and 0 <= start_y - dy < board_size and 
                  state[start_y - dy][start_x - dx] == ' ')
    
    # Check forward end (at end_x, end_y)
    open_end = (0 <= end_x < board_size and 0 <= end_y < board_size and 
                state[end_y][end_x] == ' ')

    open_ends = open_start + open_end
    
    # --- Scoring ---
    if count == 4:
        if open_ends == 2: return 1000000, 4 # Live Four (win threat)
        if open_ends == 1: return 50000, 4   # Sleep Four
        return 0, 4 # Closed Four
    
    if count == 3:
        if open_ends == 2: return 50000, 3  # Live Three (high threat)
        if open_ends == 1: return 1000, 3   # Sleep Three
        return 100, 3
    
    if count == 2:
        if open_ends == 2: return 1000, 2 # Live Two
        return 100, 2
    
    if count == 1:
        return 1, 1
    
    return 0, count

# ----------------------- Minimax with Iterative Deepening -----------------------

def minimax_optimized(state, depth, alpha, beta, maximizing, ai_player, human_player, board_size):
    """Optimized minimax with move ordering and pruning."""
    
    winner = check_winner_fast(state, board_size)
    if winner == ai_player:
        return (10000000, None)
    elif winner == human_player:
        return (-10000000, None)
    elif depth == 0 or is_full(state, board_size):
        return (evaluate_board(state, ai_player, human_player, board_size), None)
    
    # Get prioritized moves (Crucial for speed)
    moves = get_priority_moves(state, player=ai_player if maximizing else human_player, 
                                  opponent=human_player if maximizing else ai_player, 
                                  board_size=board_size, 
                                  max_moves=12 if depth > 2 else 8)
    
    if not moves:
        return (0, None)
    
    current_player = ai_player if maximizing else human_player
    
    if maximizing:
        best_score = -math.inf
        best_move = None
        
        for x, y in moves:
            # Note: We are mutating the state here and unmaking the move later (faster than copying)
            state[y][x] = current_player 
            score, _ = minimax_optimized(state, depth - 1, alpha, beta, False, ai_player, human_player, board_size)
            state[y][x] = ' ' # Unmake the move
            
            if score > best_score:
                best_score = score
                best_move = (x, y)
            
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        
        return best_score, best_move
    else: # Minimizing
        best_score = math.inf
        best_move = None
        
        for x, y in moves:
            state[y][x] = current_player
            score, _ = minimax_optimized(state, depth - 1, alpha, beta, True, ai_player, human_player, board_size)
            state[y][x] = ' ' # Unmake the move
            
            if score < best_score:
                best_score = score
                best_move = (x, y)
            
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        
        return best_score, best_move


def get_best_move_iterative(state, ai_player, human_player, board_size, max_time=3.0, max_depth=6):
    """
    Iterative deepening AI move caller.
    """
    start_time = time.time()
    best_move = None
    
    # --- Quick Check for Immediate Win/Block ---
    # Max depth for move ordering must be sufficient to check 5 in a row
    priority_moves = get_priority_moves(state, ai_player, human_player, board_size, max_moves=20)
    
    # Check top 5 moves for instant win/block
    for x, y in priority_moves[:5]:
        # 1. Check for immediate AI win
        state[y][x] = ai_player
        if check_winner_fast(state, board_size) == ai_player:
            state[y][x] = ' '
            return (x, y) 
        state[y][x] = ' '
        
        # 2. Check for immediate Human win (must block!)
        state[y][x] = human_player
        if check_winner_fast(state, board_size) == human_player:
            state[y][x] = ' '
            return (x, y) 
        state[y][x] = ' '

    # --- Iterative Deepening Search ---
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > max_time:
            break
        
        # Must clear the cache before each new depth search
        clear_eval_cache() 
        
        score, move = minimax_optimized(
            state, depth, -math.inf, math.inf, True, 
            ai_player, human_player, board_size
        )
        
        if move:
            best_move = move
        
        # Stop early if we found a guaranteed win (score > WINNING_SCORE)
        if score >= 9000000:
            break
    
    return best_move