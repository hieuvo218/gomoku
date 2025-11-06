
# 🧩 Five-in-a-Row (Gomoku)

This is an implementation of the classic board game **Gomoku** (also known as *Five-in-a-Row* or *Gobang*), built using **Python** and **Pygame**.  
It features both **Player vs. Player (PvP)** and challenging **Player vs. AI** modes with adjustable difficulty.

## How to Run:
- Clone the repository then run the executable file located in folder dist.
---

## 🕹️ Game Rules

- **Board Size:** 15×15  
- **Objective:** Be the first player to get an unbroken line of **five** of your own symbols (`X` or `O`) horizontally, vertically, or diagonally.  
- **Gameplay:** Players take turns placing their symbol on an empty intersection.  
- **Forbidden Moves:** This implementation does **not** include “three-and-three” or “overlines” rules, making it a simple, pure Gomoku experience.

---

## 🎮 Controls

| **Action** | **Control** | **Description** |
|-------------|-------------|------------------|
| **Place Symbol** | Left Click | Click on any empty cell on the board to place your symbol. |
| **Pause Game** | Left Click on Pause Button | Pauses the game, halting the timer and showing menu options. |
| **Menu Navigation** | Left Click | Select options in the Main Menu and Settings. |
| **Continue Game** | Left Click on Continue | Available after pausing or returning to the Main Menu. |

---

## ⚙️ Features

- **PvP Mode:** Two players compete. The game automatically alternates the starting symbol (`X` and `O`) each round to ensure fairness. Player 1 is always displayed on the left panel, regardless of their current symbol.  
- **Player vs. AI:** Challenge the computer with adjustable difficulty levels. The human player can choose to play as either `X` or `O`.  
- **Settings:** Adjust volume for background **music** and **sound effects (SFX)**.  
- **Timer:** Each player has **5 minutes** to complete the match, adding a competitive time limit.  
- **Responsive Assets:** All assets (sounds, music) are properly bundled via **PyInstaller**’s `sys._MEIPASS` for smooth execution as a standalone `.exe`.

---

## 🤖 AI Method: Minimax with Iterative Deepening and Heuristics

The AI opponent employs a combination of **Minimax**, **Alpha-Beta Pruning**, and **move prioritization heuristics** to find the optimal move efficiently.

### 1. Core Algorithm: Minimax
The AI recursively explores possible board states to a certain depth, aiming to:
- **Maximize** its own score.
- **Minimize** the opponent’s best possible score.

### 2. Performance Enhancement: Alpha-Beta Pruning
To improve speed, the algorithm prunes (skips) branches that cannot influence the final decision.  
This drastically reduces unnecessary evaluations.

### 3. Move Prioritization (Ordering)
Instead of checking every cell, the AI focuses on **high-potential moves** near existing stones or promising sequences.  
This optimization enables deeper searches while maintaining strong tactical awareness.

### 4. Difficulty Levels

| **Difficulty** | **Search Depth** | **Description** |
|----------------|------------------|-----------------|
| **Easy (1)** | Shallow | Fast but prone to mistakes. |
| **Medium (2)** | Moderate | Balanced speed and strategy. |
| **Hard (3)** | Deep | Slower but highly strategic and defensive. |

---

Made with ❤️ using **Python**, **Pygame**, and a passion for AI board games.
