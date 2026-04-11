import requests
import json
import chess
import database
import time

LICHESS_API_URL = "https://lichess.org/api/puzzle/next"
LICHESS_DAILY_URL = "https://lichess.org/api/puzzle/daily"

class PuzzleEngine:
    def __init__(self):
        self.current_puzzle = None

    def fetch_lichess_puzzles(self, count=5, themes=None):
        puzzles = []
        url = LICHESS_API_URL
        if themes: url += f"?themes={themes}"
        for _ in range(count):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if self.validate_puzzle(data): database.cache_puzzle(data['puzzle']['id'], data); puzzles.append(data)
            except Exception: break
        return puzzles

    def fetch_daily_puzzle(self):
        try:
            response = requests.get(LICHESS_DAILY_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if self.validate_puzzle(data): database.cache_puzzle(data['puzzle']['id'], data); return data
        except Exception: pass
        return None

    def validate_puzzle(self, data):
        try:
            fen = data['game']['fen']; moves = data['game']['moves'].split(); solution = data['puzzle']['solution']
            board = chess.Board(fen)
            for m in moves: board.push_uci(m)
            if not board.is_valid(): return False
            temp_board = board.copy()
            for m in solution:
                move = chess.Move.from_uci(m)
                if move not in temp_board.legal_moves: return False
                temp_board.push(move)
            return True
        except Exception: return False

    def get_built_in_puzzles(self):
        puzzles = [
            {"puzzle": {"id": "built_in_1", "solution": ["f1e1"], "rating": 600, "themes": ["mateIn1", "backRank"]}, "game": {"fen": "4r1k1/5ppp/8/8/8/8/5PPP/5RK1 w - - 0 1", "moves": ""}},
            {"puzzle": {"id": "built_in_2", "solution": ["d1d8"], "rating": 700, "themes": ["mateIn1"]}, "game": {"fen": "k7/pp6/8/8/8/8/8/3R2K1 w - - 0 1", "moves": ""}}
        ]
        return [p for p in puzzles if self.validate_puzzle(p)]

    def get_puzzle_board(self, puzzle_data):
        board = chess.Board(puzzle_data['game']['fen']); moves = puzzle_data['game']['moves'].split()
        for m in moves:
            if m: board.push_uci(m)
        return board
