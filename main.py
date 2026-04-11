import sys
import os
import chess
import database
import threading
import random
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMessageBox, QProgressDialog, QDialog,
                             QVBoxLayout, QLabel, QHBoxLayout, QPushButton)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from main_window import MainWindow, BotSelectionDialog
from engine import EngineManager, AnalysisWorker, LiveAnalysisWorker, detect_opening, BOT_PROFILES
from game_controller import GameController
from puzzles import PuzzleEngine
from sounds import SoundManager

class GameOverDialog(QDialog):
    def __init__(self, result, termination, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Over"); self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        from PyQt5.QtGui import QFont
        lbl_res = QLabel(f"Result: {result}"); lbl_res.setFont(QFont("Outfit", 16, QFont.Bold)); lbl_res.setAlignment(Qt.AlignCenter); layout.addWidget(lbl_res)
        lbl_term = QLabel(termination); lbl_term.setAlignment(Qt.AlignCenter); layout.addWidget(lbl_term)
        layout.addSpacing(20)
        self.btn_review = QPushButton("Review Game"); self.btn_again = QPushButton("Play Again"); self.btn_menu = QPushButton("Menu")
        for b in [self.btn_review, self.btn_again, self.btn_menu]: layout.addWidget(b)
        self.btn_review.clicked.connect(lambda: self.done(1)); self.btn_again.clicked.connect(lambda: self.done(2)); self.btn_menu.clicked.connect(lambda: self.done(3))

class ChessTrainerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        database.init_db()
        stockfish_path = database.get_setting("stockfish_path")
        self.engine_manager = EngineManager(stockfish_path)
        self.game_controller = GameController()
        self.puzzle_engine = PuzzleEngine()
        self.sound_manager = SoundManager()
        self.main_window = MainWindow()
        self.main_window.set_engine_status(self.engine_manager.is_loaded())
        self.init_puzzle_page()
        self.init_play_page()
        self.init_review_page()
        self.init_settings()
        self.update_stats()
        self.live_worker = None
        self.main_window.show()

    def init_puzzle_page(self):
        from puzzle_widget import PuzzleWidget
        self.puzzle_ui = PuzzleWidget(); self.puzzle_ui.puzzle_engine = self.puzzle_engine
        self.main_window.stack.removeWidget(self.main_window.page_puzzles)
        self.main_window.stack.insertWidget(1, self.puzzle_ui); self.main_window.page_puzzles = self.puzzle_ui
        def fetch_puzzles():
            p_list = self.puzzle_engine.get_built_in_puzzles()
            themes = ["fork", "pin", "mate", "backRank", "skewer", "endgame"]
            for t in themes:
                lichess = self.puzzle_engine.fetch_lichess_puzzles(3, themes=t)
                if lichess: p_list.extend(lichess)
            daily = self.puzzle_engine.fetch_daily_puzzle()
            if daily: p_list.insert(0, daily)
            QTimer.singleShot(0, lambda: self.puzzle_ui.set_puzzles(p_list))
        threading.Thread(target=fetch_puzzles, daemon=True).start()
        self.puzzle_ui.puzzle_solved.connect(self.on_puzzle_solved)
        self.puzzle_ui.puzzle_attempted.connect(self.on_puzzle_attempted)

    def on_puzzle_solved(self, puzzle_id):
        self.sound_manager.play("game_end")
        self.update_stats()

    def on_puzzle_attempted(self, puzzle_id, solved):
        database.update_puzzle_progress(puzzle_id, solved)
        if not solved: self.sound_manager.play("illegal")

    def init_play_page(self):
        self.main_window.board_widget.move_made.connect(self.handle_player_move)
        self.main_window.btn_new_game.clicked.connect(self.start_new_game)
        self.main_window.btn_hint.clicked.connect(self.show_hint)
        self.main_window.btn_draw.clicked.connect(self.handle_draw_offer)
        self.main_window.btn_resign.clicked.connect(self.handle_resign)
        self.bot_timer = QTimer(); self.bot_timer.setSingleShot(True); self.bot_timer.timeout.connect(self.make_bot_move)
        self.clock_timer = QTimer(); self.clock_timer.timeout.connect(self.update_clocks); self.clock_timer.start(1000)

    def start_new_game(self):
        dlg = BotSelectionDialog(self.main_window)
        if dlg.exec_():
            bot_name = dlg.bot_combo.currentData()
            bot_elo = BOT_PROFILES[bot_name]['elo']
            tc = dlg.time_combo.currentText()
            color = chess.WHITE
            if dlg.btn_black.isChecked(): color = chess.BLACK
            elif dlg.btn_random.isChecked(): color = random.choice([chess.WHITE, chess.BLACK])
            self.game_controller.start_new_game(player_color=color, bot_name=bot_name, bot_elo=bot_elo, time_control=tc)
            self.main_window.board_widget.set_board(self.game_controller.board)
            self.main_window.board_widget.set_flipped(color == chess.BLACK)
            self.main_window.board_widget.last_move = None
            self.main_window.board_widget.arrows = []
            self.main_window.lbl_opening.setText("Starting Position"); self.main_window.move_list.setText(""); self.main_window.eval_bar.set_eval(0)
            self.main_window.opp_bar.name_label.setText(f"{bot_name} ({bot_elo})")
            self.sound_manager.play("start")
            if color == chess.BLACK: self.bot_timer.start(500)

    def handle_player_move(self, move):
        if self.game_controller.is_game_over(): return
        success, move_info = self.game_controller.make_move(move)
        if success:
            self.sound_manager.play("capture" if "x" in move_info["san"] else "move")
            self.update_ui_after_move()
            if not self.game_controller.is_game_over(): self.bot_timer.start(800)
            else: self.handle_game_over()

    def make_bot_move(self):
        if self.game_controller.is_game_over(): return
        if self.engine_manager.is_loaded():
            self.engine_manager.configure_bot(self.game_controller.bot_name)

            # Draw logic: Bot accepts draw if losing by >50cp
            if self.game_controller.draw_offered:
                info = self.engine_manager.get_analysis(self.game_controller.board, depth=10)
                if info:
                    score = info[0]['score'].relative.score(mate_score=10000)
                    if score < -50: # Bot is losing
                        self.game_controller.board.set_result("1/2-1/2") # Force draw
                        self.handle_game_over(); return

            bot_move = self.engine_manager.get_best_move(self.game_controller.board)
            if bot_move:
                success, move_info = self.game_controller.make_move(bot_move)
                if success:
                    self.sound_manager.play("capture" if "x" in move_info["san"] else "move")
                    self.update_ui_after_move()
                    if self.game_controller.is_game_over(): self.handle_game_over()

    def update_ui_after_move(self):
        self.main_window.board_widget.update()
        op = detect_opening(self.game_controller.board)
        if op: self.main_window.lbl_opening.setText(op)
        m_list = ""
        for i, m in enumerate(self.game_controller.move_history):
            if i % 2 == 0: m_list += f"{i//2 + 1}. {m['san']} "
            else: m_list += f"{m['san']}  "
        self.main_window.move_list.setText(m_list)
        if self.engine_manager.is_loaded():
            if self.live_worker and self.live_worker.isRunning(): return
            self.live_worker = LiveAnalysisWorker(self.engine_manager, self.game_controller.board)
            self.live_worker.analysis_ready.connect(self.on_live_analysis); self.live_worker.start()

    def on_live_analysis(self, info):
        score = info['score'].white().score(mate_score=10000)
        self.main_window.eval_bar.set_eval(score)

    def handle_game_over(self):
        res = self.game_controller.get_result(); term = self.game_controller.get_termination()
        game_id = database.save_game({
            "started_at": self.game_controller.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "player_color": "white" if self.game_controller.player_color == chess.WHITE else "black",
            "bot_name": self.game_controller.bot_name, "bot_elo": self.game_controller.bot_elo,
            "result": res, "termination": term, "pgn": self.game_controller.get_pgn(), "final_fen": self.game_controller.board.fen()
        })
        for m in self.game_controller.move_history: m["game_id"] = game_id; database.save_move(m)
        self.update_stats(); self.sound_manager.play("game_end")
        dlg = GameOverDialog(res, term, self.main_window); choice = dlg.exec_()
        if choice == 1: self.load_game_for_review(game_id)
        elif choice == 2: self.start_new_game()

    def handle_resign(self):
        if not self.game_controller.is_game_over():
            self.game_controller.clocks[self.game_controller.player_color] = 0; self.handle_game_over()

    def handle_draw_offer(self):
        if self.game_controller.is_game_over(): return
        self.game_controller.offer_draw()
        self.main_window.btn_draw.setEnabled(False)
        self.sound_manager.play("move")

    def show_hint(self):
        if not self.engine_manager.is_loaded(): return
        mv = self.engine_manager.get_best_move(self.game_controller.board)
        if mv: self.main_window.board_widget.arrows = [(mv.from_square, mv.to_square, Qt.blue)]; self.main_window.board_widget.update()

    def init_review_page(self):
        from review_panel import ReviewPanel
        self.review_ui = ReviewPanel(); self.main_window.stack.removeWidget(self.main_window.page_review)
        self.main_window.stack.insertWidget(2, self.review_ui); self.main_window.page_review = self.review_ui
        self.main_window.btn_review.clicked.connect(lambda: self.load_game_for_review())

    def load_game_for_review(self, game_id=None):
        if game_id is None:
            recent = database.get_recent_games(1)
            if not recent: return
            game_id = recent[0]['id']
        moves = database.get_game_moves(game_id)
        if not self.engine_manager.is_loaded():
            self.review_ui.set_data(moves); self.main_window.switch_page(2); return
        self.analysis_dialog = QProgressDialog("Analyzing game...", "Cancel", 0, len(moves), self.main_window)
        self.analysis_worker = AnalysisWorker(self.engine_manager, moves)
        self.analysis_worker.progress.connect(self.analysis_dialog.setValue)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_dialog.canceled.connect(self.analysis_worker.cancel); self.analysis_worker.start()

    def on_analysis_finished(self, analyzed_moves):
        if hasattr(self, 'analysis_dialog'): self.analysis_dialog.close()
        self.review_ui.set_data(analyzed_moves); self.main_window.switch_page(2)

    def init_settings(self):
        self.main_window.check_sound.stateChanged.connect(lambda s: setattr(self.sound_manager, 'enabled', s == Qt.Checked))
        self.main_window.check_promote.stateChanged.connect(lambda s: setattr(self.main_window.board_widget, 'auto_promote_queen', s == Qt.Checked))
        # Add connection for theme/depth changes if needed

    def update_stats(self):
        recent = database.get_recent_games(100); wins = sum(1 for g in recent if (g['player_color'] == 'white' and g['result'] == '1-0') or (g['player_color'] == 'black' and g['result'] == '0-1'))
        with database.get_connection(database.PUZZLE_DB_PATH) as conn:
            p_solved = conn.execute("SELECT COUNT(*) FROM puzzle_progress WHERE solved = 1").fetchone()[0]
        self.main_window.update_stats_display(len(recent), wins, 0, p_solved)

    def update_clocks(self):
        if self.game_controller.time_control == "Unlimited" or self.game_controller.is_game_over(): return
        self.game_controller.clocks[self.game_controller.board.turn] -= 1
        if self.game_controller.clocks[self.game_controller.board.turn] <= 0:
            self.game_controller.clocks[self.game_controller.board.turn] = 0; self.handle_game_over()
        self.main_window.player_bar.clock_label.setText(self.format_time(self.game_controller.clocks[chess.WHITE]))
        self.main_window.opp_bar.clock_label.setText(self.format_time(self.game_controller.clocks[chess.BLACK]))

    def format_time(self, s):
        if s == float('inf'): return "∞"
        m, sec = divmod(max(0, int(s)), 60); return f"{m:02d}:{sec:02d}"

    def run(self): return self.app.exec_()

if __name__ == "__main__":
    app = ChessTrainerApp(); sys.exit(app.run())
