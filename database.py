import sqlite3
import json
import os
import time

DB_PATH = "chess_trainer.db"
PUZZLE_DB_PATH = "chess_trainer_puzzles.db"

def get_connection(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Main DB
    with get_connection(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT,
            finished_at TEXT,
            player_color TEXT,
            bot_name TEXT,
            bot_elo INTEGER,
            time_control TEXT,
            result TEXT,
            termination TEXT,
            opening_name TEXT,
            pgn TEXT,
            final_fen TEXT,
            player_accuracy REAL,
            bot_accuracy REAL
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS moves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER,
            move_number INTEGER,
            color TEXT,
            uci TEXT,
            san TEXT,
            fen_before TEXT,
            fen_after TEXT,
            time_spent_ms INTEGER,
            eval_before REAL,
            eval_after REAL,
            best_uci TEXT,
            best_san TEXT,
            classification TEXT,
            eval_loss REAL,
            FOREIGN KEY(game_id) REFERENCES games(id)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lichess_cache (
            puzzle_id TEXT PRIMARY KEY,
            data TEXT,
            fetched_at INTEGER
        )""")

        conn.commit()

    # Puzzle DB
    with get_connection(PUZZLE_DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS puzzle_progress (
            puzzle_id TEXT PRIMARY KEY,
            solved INTEGER,
            attempts INTEGER,
            first_solved TEXT,
            last_attempt TEXT
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS puzzle_stats (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        conn.commit()

# --- Settings ---
def get_setting(key, default=None):
    with get_connection(DB_PATH) as conn:
        res = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return res['value'] if res else default

def save_setting(key, value):
    with get_connection(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

# --- Games ---
def save_game(game_data):
    with get_connection(DB_PATH) as conn:
        cursor = conn.cursor()
        keys = game_data.keys()
        placeholders = ", ".join(["?"] * len(keys))
        columns = ", ".join(keys)
        sql = f"INSERT INTO games ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(game_data.values()))
        conn.commit()
        return cursor.lastrowid

def save_move(move_data):
    with get_connection(DB_PATH) as conn:
        keys = move_data.keys()
        placeholders = ", ".join(["?"] * len(keys))
        columns = ", ".join(keys)
        sql = f"INSERT INTO moves ({columns}) VALUES ({placeholders})"
        conn.execute(sql, list(move_data.values()))
        conn.commit()

def get_recent_games(limit=10):
    with get_connection(DB_PATH) as conn:
        return conn.execute("SELECT * FROM games ORDER BY id DESC LIMIT ?", (limit,)).fetchall()

def get_game_moves(game_id):
    with get_connection(DB_PATH) as conn:
        return conn.execute("SELECT * FROM moves WHERE game_id = ? ORDER BY id ASC", (game_id,)).fetchall()

# --- Lichess Cache ---
def get_cached_puzzle(puzzle_id):
    with get_connection(DB_PATH) as conn:
        res = conn.execute("SELECT data, fetched_at FROM lichess_cache WHERE puzzle_id = ?", (puzzle_id,)).fetchone()
        if res:
            # Check TTL (24h = 86400s)
            if time.time() - res['fetched_at'] < 86400:
                return json.loads(res['data'])
        return None

def cache_puzzle(puzzle_id, data):
    with get_connection(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO lichess_cache (puzzle_id, data, fetched_at) VALUES (?, ?, ?)",
                     (puzzle_id, json.dumps(data), int(time.time())))
        conn.commit()

# --- Puzzle Progress ---
def update_puzzle_progress(puzzle_id, solved):
    with get_connection(PUZZLE_DB_PATH) as conn:
        res = conn.execute("SELECT * FROM puzzle_progress WHERE puzzle_id = ?", (puzzle_id,)).fetchone()
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        if res:
            new_solved = 1 if solved or res['solved'] else 0
            attempts = res['attempts'] + 1
            first_solved = res['first_solved'] if res['first_solved'] else (now if solved else None)
            conn.execute("UPDATE puzzle_progress SET solved = ?, attempts = ?, first_solved = ?, last_attempt = ? WHERE puzzle_id = ?",
                         (new_solved, attempts, first_solved, now, puzzle_id))
        else:
            conn.execute("INSERT INTO puzzle_progress (puzzle_id, solved, attempts, first_solved, last_attempt) VALUES (?, ?, ?, ?, ?)",
                         (puzzle_id, 1 if solved else 0, 1, now if solved else None, now))
        conn.commit()

def get_puzzle_progress(puzzle_id):
    with get_connection(PUZZLE_DB_PATH) as conn:
        return conn.execute("SELECT * FROM puzzle_progress WHERE puzzle_id = ?", (puzzle_id,)).fetchone()

# --- Stats ---
def update_stat(key, value, db_path=DB_PATH):
    table = "puzzle_stats" if db_path == PUZZLE_DB_PATH else "stats"
    with get_connection(db_path) as conn:
        conn.execute(f"INSERT OR REPLACE INTO {table} (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

def get_stat(key, default="0", db_path=DB_PATH):
    table = "puzzle_stats" if db_path == PUZZLE_DB_PATH else "stats"
    with get_connection(db_path) as conn:
        res = conn.execute(f"SELECT value FROM {table} WHERE key = ?", (key,)).fetchone()
        return res['value'] if res else default

if __name__ == "__main__":
    init_db()
