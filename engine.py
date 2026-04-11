import chess
import chess.engine
import os
import threading
import math
from PyQt5.QtCore import QThread, pyqtSignal

class EngineManager:
    def __init__(self, stockfish_path=None):
        self.engine = None
        self.stockfish_path = stockfish_path
        self._load_engine()

    def _load_engine(self):
        if self.stockfish_path and os.path.exists(self.stockfish_path):
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            except Exception as e:
                print(f"Failed to load engine: {e}")
                self.engine = None

    def set_path(self, path):
        self.stockfish_path = path
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
        self._load_engine()

    def is_loaded(self):
        return self.engine is not None

    def get_best_move(self, board, time_limit=0.1, depth=None):
        if not self.engine:
            return None
        try:
            result = self.engine.play(board, chess.engine.Limit(time=time_limit, depth=depth))
            return result.move
        except Exception:
            return None

    def get_analysis(self, board, depth=12):
        if not self.engine:
            return None
        try:
            info = self.engine.analyse(board, chess.engine.Limit(depth=depth))
            return info
        except Exception:
            return None

    def configure_bot(self, profile_name):
        if not self.engine or profile_name not in BOT_PROFILES:
            return
        profile = BOT_PROFILES[profile_name]
        self.engine.configure({
            "UCI_LimitStrength": True,
            "UCI_Elo": profile["elo"],
            "Skill Level": profile["skill"]
        })

    def quit(self):
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass

BOT_PROFILES = {
    "Rookie": {"elo": 800, "skill": 1, "depth": 3, "desc": "Frequent blunders"},
    "Beginner": {"elo": 1000, "skill": 3, "depth": 4, "desc": "Misses simple tactics"},
    "Casual": {"elo": 1200, "skill": 5, "depth": 5, "desc": "Occasional errors"},
    "Club Player": {"elo": 1400, "skill": 8, "depth": 7, "desc": "Solid club chess"},
    "Intermediate": {"elo": 1600, "skill": 11, "depth": 9, "desc": "Strong tactics"},
    "Advanced": {"elo": 1800, "skill": 14, "depth": 11, "desc": "Near-expert"},
    "Expert": {"elo": 2000, "skill": 17, "depth": 13, "desc": "Tournament level"},
    "Master": {"elo": 2200, "skill": 18, "depth": 16, "desc": "Very strong"},
    "Grandmaster": {"elo": 2500, "skill": 19, "depth": 18, "desc": "Near-perfect"},
    "Stockfish MAX": {"elo": 3200, "skill": 20, "depth": 22, "desc": "Unbeatable"},
}

def configure_bot(engine, profile_name):
    if not engine or profile_name not in BOT_PROFILES:
        return
    profile = BOT_PROFILES[profile_name]
    engine.configure({
        "UCI_LimitStrength": True,
        "UCI_Elo": profile["elo"],
        "Skill Level": profile["skill"]
    })

# Opening detection
OPENINGS = [
    ("Ruy Lopez", "e4 e5 Nf3 Nc6 Bb5"),
    ("Italian Game", "e4 e5 Nf3 Nc6 Bc4"),
    ("Sicilian Defense", "e4 c5"),
    ("Sicilian Najdorf", "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6"),
    ("Sicilian Dragon", "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 g6"),
    ("Sicilian Scheveningen", "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 e6"),
    ("Sicilian Kan", "e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6"),
    ("Sicilian Classical", "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Nf6 Nc3 d6"),
    ("Sicilian Alapin", "e4 c5 c3"),
    ("Closed Sicilian", "e4 c5 Nc3"),
    ("French Defense", "e4 e6"),
    ("French Classical", "e4 e6 d4 d5 Nc3 Nf6"),
    ("French Advance", "e4 e6 d4 d5 e5"),
    ("French Tarrasch", "e4 e6 d4 d5 Nd2"),
    ("French Exchange", "e4 e6 d4 d5 exd5"),
    ("Caro-Kann Defense", "e4 c6"),
    ("Caro-Kann Classical", "e4 c6 d4 d5 Nc3 dxe4 Nxe4 Bf5"),
    ("Caro-Kann Advance", "e4 c6 d4 d5 e5"),
    ("Caro-Kann Exchange", "e4 c6 d4 d5 exd5 cxd5"),
    ("Queen's Gambit", "d4 d5 c4"),
    ("Queen's Gambit Accepted", "d4 d5 c4 dxc4"),
    ("Queen's Gambit Declined", "d4 d5 c4 e6"),
    ("Slav Defense", "d4 d5 c4 c6"),
    ("King's Indian Defense", "d4 Nf6 c4 g6 Nc3 Bg7 e4 d6"),
    ("Nimzo-Indian Defense", "d4 Nf6 c4 e6 Nc3 Bb4"),
    ("Queen's Indian Defense", "d4 Nf6 c4 e6 Nf3 b6"),
    ("English Opening", "c4"),
    ("Reti Opening", "Nf3"),
    ("Dutch Defense", "d4 f5"),
    ("Scandinavian Defense", "e4 d5"),
    ("Petrov Defense", "e4 e5 Nf3 Nf6"),
    ("King's Gambit", "e4 e5 f4"),
    ("Vienna Game", "e4 e5 Nc3"),
    ("Bird's Opening", "f4"),
    ("Polish Opening", "b4"),
    ("Ruy Lopez: Marshall Attack", "e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 O-O c3 d5"),
    ("Ruy Lopez: Berlin Defense", "e4 e5 Nf3 Nc6 Bb5 Nf6"),
    ("Ruy Lopez: Exchange Variation", "e4 e5 Nf3 Nc6 Bb5 a6 Bxc6"),
    ("Italian Game: Giuoco Piano", "e4 e5 Nf3 Nc6 Bc4 Bc5"),
    ("Italian Game: Evans Gambit", "e4 e5 Nf3 Nc6 Bc4 Bc5 b4"),
    ("Italian Game: Two Knights Defense", "e4 e5 Nf3 Nc6 Bc4 Nf6"),
    ("Sicilian: Richter-Rauzer", "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Nf6 Nc3 d6 Bg5"),
    ("Sicilian: Sveshnikov", "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Nf6 Nc3 e5"),
    ("Sicilian: Taimanov", "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 Nxd4 e6"),
    ("Sicilian: Smith-Morra Gambit", "e4 c5 d4 cxd4 c3"),
    ("French: Winawer Variation", "e4 e6 d4 d5 Nc3 Bb4"),
    ("French: Burn Variation", "e4 e6 d4 d5 Nc3 Nf6 Bg5 dxe4"),
    ("French: MacCutcheon Variation", "e4 e6 d4 d5 Nc3 Nf6 Bg5 Bb4"),
    ("Caro-Kann: Panov Attack", "e4 c6 d4 d5 exd5 cxd5 c4"),
    ("Caro-Kann: Two Knights Variation", "e4 c6 Nc3 d5 Nf3"),
    ("Slav: Semi-Slav", "d4 d5 c4 c6 Nf3 Nf6 Nc3 e6"),
    ("Slav: Chebanenko Variation", "d4 d5 c4 c6 Nf3 Nf6 Nc3 a6"),
    ("King's Indian: Saemisch Variation", "d4 Nf6 c4 g6 Nc3 Bg7 e4 d6 f3"),
    ("King's Indian: Classical Variation", "d4 Nf6 c4 g6 Nc3 Bg7 e4 d6 Nf3 O-O Be2 e5"),
    ("King's Indian: Four Pawns Attack", "d4 Nf6 c4 g6 Nc3 Bg7 e4 d6 f4"),
    ("Nimzo-Indian: Rubinstein System", "d4 Nf6 c4 e6 Nc3 Bb4 e3"),
    ("Nimzo-Indian: Classical Variation", "d4 Nf6 c4 e6 Nc3 Bb4 Qc2"),
    ("Queen's Gambit Declined: Tartakower Variation", "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 h6 Bh4 b6"),
    ("Queen's Gambit Declined: Lasker Defense", "d4 d5 c4 e6 Nc3 Nf6 Bg5 Be7 e3 O-O Nf3 h6 Bh4 Ne4"),
    ("Queen's Gambit Declined: Cambridge Springs", "d4 d5 c4 e6 Nc3 Nf6 Bg5 Nbd7 e3 c6 Nf3 Qa5"),
    ("Catalan Opening", "d4 Nf6 c4 e6 g3 d5 Bg2"),
    ("Grünfeld Defense", "d4 Nf6 c4 g6 Nc3 d5"),
    ("Grünfeld: Exchange Variation", "d4 Nf6 c4 g6 Nc3 d5 cxd5 Nxd5 e4"),
    ("London System", "d4 Nf6 Nf3 d5 Bf4"),
    ("Trompowsky Attack", "d4 Nf6 Bg5"),
    ("Alekhine's Defense", "e4 Nf6"),
    ("Modern Defense", "e4 g6"),
    ("Pirc Defense", "e4 d6 d4 Nf6 Nc3 g6"),
    ("Benoni Defense", "d4 Nf6 c4 c5 d5 e6"),
    ("Benko Gambit", "d4 Nf6 c4 c5 d5 b5"),
    ("Nimzowitsch Defense", "e4 Nc6"),
    ("Center Game", "e4 e5 d4 exd4 Qxd4"),
    ("Scotch Game", "e4 e5 Nf3 Nc6 d4"),
]

_opening_index = {}

def build_opening_index():
    global _opening_index
    if _opening_index:
        return
    for name, moves in OPENINGS:
        board = chess.Board()
        try:
            for move_str in moves.split():
                if move_str.endswith('.'): continue
                board.push_san(move_str)
                fen_key = " ".join(board.fen().split()[:4])
                _opening_index[fen_key] = name
        except Exception:
            continue

def detect_opening(board):
    build_opening_index()
    if board.fullmove_number > 15:
        return None
    fen_key = " ".join(board.fen().split()[:4])
    return _opening_index.get(fen_key)

def win_prob(cp):
    return 1.0 / (1.0 + math.exp(-cp / 350.0))

class AnalysisWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)

    def __init__(self, engine_manager, game_moves, depth=12):
        super().__init__()
        self.em = engine_manager
        self.moves = game_moves
        self.depth = depth
        self.is_cancelled = False

    def run(self):
        analyzed_moves = []
        total = len(self.moves)
        for i, move_data in enumerate(self.moves):
            if self.is_cancelled: break
            board = chess.Board(move_data['fen_before'])
            move = chess.Move.from_uci(move_data['uci'])
            info = self.em.get_analysis(board, self.depth)
            best_move = info[0]['pv'][0] if info and 'pv' in info[0] else None
            best_score = info[0]['score'].relative.score(mate_score=10000) if info else 0
            board.push(move)
            info_played = self.em.get_analysis(board, self.depth)
            played_score = -info_played[0]['score'].relative.score(mate_score=10000) if info_played else best_score
            loss = best_score - played_score
            wp_best = win_prob(best_score)
            wp_played = win_prob(played_score)
            accuracy = 100 * (1 - (wp_best - wp_played))
            cls = "Good"; sym = ""
            if loss > 150: cls, sym = "Blunder", "??"
            elif loss > 80: cls, sym = "Mistake", "?"
            elif loss > 30: cls, sym = "Inaccuracy", "?!"
            elif loss < 10: cls, sym = "Best", "!"
            move_data = dict(move_data)
            move_data.update({'eval_before': best_score, 'eval_after': played_score, 'best_uci': best_move.uci() if best_move else "", 'classification': cls, 'symbol': sym, 'eval_loss': loss, 'accuracy': accuracy})
            analyzed_moves.append(move_data)
            self.progress.emit(i + 1, total)
        self.finished.emit(analyzed_moves)

    def cancel(self):
        self.is_cancelled = True

class LiveAnalysisWorker(QThread):
    analysis_ready = pyqtSignal(dict)
    def __init__(self, engine_manager, board, depth=12):
        super().__init__()
        self.em = engine_manager; self.board = board.copy(); self.depth = depth
    def run(self):
        info = self.em.get_analysis(self.board, self.depth)
        if info: self.analysis_ready.emit(info[0])
