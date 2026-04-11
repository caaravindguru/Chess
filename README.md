# Chess Trainer ♟️

A comprehensive Python desktop application for chess improvement, featuring a **Puzzle Trainer**, **Play vs Bots**, and **Game Review** mode.

## Features

### ♟️ Play vs Bots
- **10 Bot Profiles**: Challenge bots ranging from Rookie (800 ELO) to Stockfish MAX (3200 ELO).
- **Time Controls**: Blitz, Rapid, Classical, and Unlimited modes.
- **Real-time Evaluation**: A dynamic advantage bar powered by Stockfish.
- **Hints & Opening Detection**: Get tactical hints and see the name of the opening you're playing (70+ openings recognized).

### 🧩 Puzzle Trainer
- **Lichess Integration**: Fetches theme-based puzzles (Mate, Fork, Pin, Skewer, etc.) directly from the Lichess Open Database.
- **Daily Puzzle**: Solve the official Lichess daily puzzle every morning.
- **Offline Mode**: Includes 30+ built-in puzzles for training without an internet connection.
- **Progress Tracking**: Statistics on your solved puzzles, attempts, and streaks.

### 📋 Post-Game Review
- **Deep Analysis**: Review your games with Stockfish to identify every Mistake, Blunder, and Brilliant move.
- **Interactive Eval Graph**: Visualize the flow of the game with a win-probability graph.
- **Board Reconstruction**: Accurate state replay using FEN history.

### 🎨 Modern UI & Sound
- **Dark Theme**: A sleek, dark interface inspired by modern chess platforms.
- **Custom Board**: High-quality piece rendering with legal move indicators.
- **Standalone Audio**: Programmatically generated sound effects for a fully immersive experience.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/caaravindguru/Chess.git
   cd Chess
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Stockfish**:
   Download the Stockfish engine for your OS from [stockfishchess.org](https://stockfishchess.org/download/).

4. **Launch the App**:
   ```bash
   python main.py
   ```

5. **Configure Engine**:
   Go to **Settings** → **Browse for Stockfish...** and select the binary you downloaded.

## Tech Stack
- **Language**: Python 3.8+
- **GUI Framework**: PyQt5
- **Chess Logic**: `python-chess`
- **Engine Protocol**: UCI (Universal Chess Interface)
- **Database**: SQLite3

## License
MIT License. See [LICENSE](LICENSE) for details.
