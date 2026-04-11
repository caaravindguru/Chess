import chess
import time
from datetime import datetime

class GameController:
    def __init__(self):
        self.board = chess.Board()
        self.move_history = []
        self.start_time = None
        self.player_color = chess.WHITE
        self.bot_name = "Rookie"
        self.bot_elo = 800
        self.time_control = "Unlimited"
        self.clocks = {chess.WHITE: 0, chess.BLACK: 0}
        self.last_move_time = None

    def start_new_game(self, player_color=chess.WHITE, bot_name="Rookie", bot_elo=800, time_control="Unlimited"):
        self.board = chess.Board()
        self.move_history = []
        self.start_time = datetime.now()
        self.player_color = player_color
        self.bot_name = bot_name
        self.bot_elo = bot_elo
        self.time_control = time_control
        self.last_move_time = time.time()
        if time_control == "Unlimited": self.clocks = {chess.WHITE: float('inf'), chess.BLACK: float('inf')}
        else:
            try: base = int(time_control.split('+')[0]) * 60; self.clocks = {chess.WHITE: base, chess.BLACK: base}
            except Exception: self.clocks = {chess.WHITE: 600, chess.BLACK: 600}

    def make_move(self, move):
        if move in self.board.legal_moves:
            fen_before = self.board.fen()
            now = time.time(); time_spent_ms = int((now - self.last_move_time) * 1000); self.last_move_time = now
            if self.time_control != "Unlimited":
                self.clocks[self.board.turn] -= (time_spent_ms / 1000.0)
                if '+' in self.time_control: inc = int(self.time_control.split('+')[1]); self.clocks[self.board.turn] += inc
            san = self.board.san(move); uci = move.uci(); color = "white" if self.board.turn == chess.WHITE else "black"; move_number = self.board.fullmove_number
            self.board.push(move); fen_after = self.board.fen()
            move_info = {"move_number": move_number, "color": color, "uci": uci, "san": san, "fen_before": fen_before, "fen_after": fen_after, "time_spent_ms": time_spent_ms}
            self.move_history.append(move_info)
            return True, move_info
        return False, None

    def is_game_over(self): return self.board.is_game_over() or self.is_timeout()
    def get_result(self):
        if self.is_timeout(): return "0-1" if self.clocks[chess.WHITE] <= 0 else "1-0"
        return self.board.result()
    def get_termination(self):
        if self.is_timeout(): return "Timeout"
        for t in ["Checkmate", "Stalemate", "Insufficient Material", "75-move Rule", "Fivefold Repetition"]:
            if getattr(self.board, f"is_{t.lower().replace(' ', '_').replace('-', '_')}")(): return t
        return "Unknown"
    def is_timeout(self):
        if self.time_control == "Unlimited": return False
        return self.clocks[chess.WHITE] <= 0 or self.clocks[chess.BLACK] <= 0
    def get_pgn(self):
        import chess.pgn
        game = chess.pgn.Game()
        game.headers["White"] = "Player" if self.player_color == chess.WHITE else self.bot_name
        game.headers["Black"] = "Player" if self.player_color == chess.BLACK else self.bot_name
        game.headers["Result"] = self.get_result()
        node = game
        for move_info in self.move_history: node = node.add_main_variation(chess.Move.from_uci(move_info["uci"]))
        return str(game)
