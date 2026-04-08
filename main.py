import sys
import chess
import database
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from main_window import MainWindow
from engine import EngineManager, AnalysisWorker, configure_bot, detect_opening
from game_controller import GameController
from puzzles import PuzzleEngine
from sounds import SoundManager

class ChessTrainerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        database.init_db()

        # Load settings
        stockfish_path = database.get_setting("stockfish_path")
        self.engine_manager = EngineManager(stockfish_path)

        self.game_controller = GameController()
        self.puzzle_engine = PuzzleEngine()
        self.sound_manager = SoundManager()

        self.main_window = MainWindow()
        self.main_window.set_engine_status(self.engine_manager.is_loaded())

        # Inject puzzle engine
        self.main_window.puzzle_widget = self.main_window.page_puzzles # Wait, I didn't set it in MainWindow yet
        # I need to properly initialize pages in MainWindow or here.
        # Let's fix MainWindow initialization first or just replace the placeholders.

        self.init_puzzle_page()
        self.init_play_page()
        self.init_review_page()
        self.init_settings()
        self.update_stats()

        self.main_window.show()

    def init_puzzle_page(self):
        from puzzle_widget import PuzzleWidget
        self.puzzle_ui = PuzzleWidget()
        self.puzzle_ui.puzzle_engine = self.puzzle_engine
        self.main_window.stack.removeWidget(self.main_window.page_puzzles)
        self.main_window.stack.insertWidget(1, self.puzzle_ui)
        self.main_window.page_puzzles = self.puzzle_ui

        # Fetch Lichess puzzles on startup
        import threading
        def fetch_puzzles():
            puzzles_list = self.puzzle_engine.get_built_in_puzzles()
            lichess = self.puzzle_engine.fetch_lichess_puzzles(10)
            if lichess:
                puzzles_list.extend(lichess)
            # Use singleShot to update UI safely
            QTimer.singleShot(0, lambda: self.puzzle_ui.set_puzzles(puzzles_list))

        threading.Thread(target=fetch_puzzles, daemon=True).start()

        self.puzzle_ui.puzzle_solved.connect(self.on_puzzle_solved)

    def on_puzzle_solved(self, puzzle_id):
        database.update_puzzle_progress(puzzle_id, True)
        self.sound_manager.play("game_end")
        self.update_stats()

    def init_play_page(self):
        self.play_ui = self.main_window
        self.main_window.board_widget.move_made.connect(self.handle_player_move)
        self.main_window.btn_new_game.clicked.connect(self.start_new_game)
        self.main_window.btn_hint.clicked.connect(self.show_hint)

        # Bot timer
        self.bot_timer = QTimer()
        self.bot_timer.setSingleShot(True)
        self.bot_timer.timeout.connect(self.make_bot_move)

        # Clock timer (1s)
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clocks)
        self.clock_timer.start(1000)

    def start_new_game(self):
        # Default for now
        self.game_controller.start_new_game()
        self.main_window.board_widget.set_board(self.game_controller.board)
        self.main_window.board_widget.last_move = None
        self.main_window.lbl_opening.setText("Starting Position")
        self.main_window.move_list.setText("")
        self.sound_manager.play("start")
        self.update_clocks()

        if self.game_controller.player_color == chess.BLACK:
            self.bot_timer.start(500)

    def handle_player_move(self, move):
        success, move_info = self.game_controller.make_move(move)
        if success:
            self.sound_manager.play("capture" if "x" in move_info["san"] else "move")
            self.update_ui_after_move()

            if not self.game_controller.is_game_over():
                self.bot_timer.start(1000)
            else:
                self.handle_game_over()

    def make_bot_move(self):
        if self.game_controller.is_game_over(): return

        # Configure engine for current bot
        configure_bot(self.engine_manager.engine, self.game_controller.bot_name)

        bot_move = self.engine_manager.get_best_move(self.game_controller.board)
        if bot_move:
            success, move_info = self.game_controller.make_move(bot_move)
            if success:
                self.sound_manager.play("capture" if "x" in move_info["san"] else "move")
                self.update_ui_after_move()
                if self.game_controller.is_game_over():
                    self.handle_game_over()

    def update_ui_after_move(self):
        self.main_window.board_widget.update()
        opening = detect_opening(self.game_controller.board)
        if opening:
            self.main_window.lbl_opening.setText(opening)

        # Update move list
        moves_text = ""
        for i, m in enumerate(self.game_controller.move_history):
            if i % 2 == 0:
                moves_text += f"{i//2 + 1}. {m['san']} "
            else:
                moves_text += f"{m['san']}  "
        self.main_window.move_list.setText(moves_text)

        # Update eval
        if self.engine_manager.is_loaded():
            info = self.engine_manager.get_analysis(self.game_controller.board, depth=10)
            if info:
                score = info[0]['score'].white().score(mate_score=10000)
                self.main_window.eval_bar.set_eval(score)

    def handle_game_over(self):
        result = self.game_controller.get_result()
        term = self.game_controller.get_termination()
        QMessageBox.information(self.main_window, "Game Over", f"Result: {result}\nReason: {term}")

        # Save to DB
        game_data = {
            "started_at": self.game_controller.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "finished_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "player_color": "white" if self.game_controller.player_color == chess.WHITE else "black",
            "bot_name": self.game_controller.bot_name,
            "bot_elo": self.game_controller.bot_elo,
            "result": result,
            "termination": term,
            "pgn": self.game_controller.get_pgn(),
            "final_fen": self.game_controller.board.fen()
        }
        game_id = database.save_game(game_data)
        for m in self.game_controller.move_history:
            m["game_id"] = game_id
            database.save_move(m)

        self.update_stats()
        self.sound_manager.play("game_end")

    def show_hint(self):
        if not self.engine_manager.is_loaded(): return
        hint_move = self.engine_manager.get_best_move(self.game_controller.board)
        if hint_move:
            self.main_window.board_widget.arrows = [(hint_move.from_square, hint_move.to_square, QColor(0, 0, 255, 150))]
            self.main_window.board_widget.update()

    def init_review_page(self):
        from review_panel import ReviewPanel
        self.review_ui = ReviewPanel()
        self.main_window.stack.removeWidget(self.main_window.page_review)
        self.main_window.stack.insertWidget(2, self.review_ui)
        self.main_window.page_review = self.review_ui

        self.main_window.btn_review.clicked.connect(self.load_last_game_for_review)

    def load_last_game_for_review(self):
        recent = database.get_recent_games(1)
        if recent:
            moves = database.get_game_moves(recent[0]['id'])
            if not self.engine_manager.is_loaded():
                self.review_ui.set_data(moves)
                return

            # Start analysis
            from PyQt5.QtWidgets import QProgressDialog
            self.analysis_dialog = QProgressDialog("Analyzing game...", "Cancel", 0, len(moves), self.main_window)
            self.analysis_dialog.setWindowModality(Qt.WindowModal)

            self.analysis_worker = AnalysisWorker(self.engine_manager, moves)
            self.analysis_worker.progress.connect(self.analysis_dialog.setValue)
            self.analysis_worker.finished.connect(self.on_analysis_finished)
            self.analysis_dialog.canceled.connect(self.analysis_worker.cancel)
            self.analysis_worker.start()

    def on_analysis_finished(self, analyzed_moves):
        self.analysis_dialog.close()
        self.review_ui.set_data(analyzed_moves)
        self.main_window.switch_page(2) # Switch to review page

    def init_settings(self):
        # Connect settings UI to logic
        self.main_window.check_sound.stateChanged.connect(self.on_sound_toggle)
        self.main_window.check_promote.stateChanged.connect(self.on_promote_toggle)
        # Browsing is already connected in MainWindow, but we need to react
        # We can poll or use a signal. Let's add a signal to MainWindow.

    def on_sound_toggle(self, state):
        self.sound_manager.enabled = (state == Qt.Checked)

    def on_promote_toggle(self, state):
        self.main_window.board_widget.auto_promote_queen = (state == Qt.Checked)

    def update_stats(self):
        recent = database.get_recent_games(100)
        games_count = len(recent)
        wins = sum(1 for g in recent if (g['player_color'] == 'white' and g['result'] == '1-0') or (g['player_color'] == 'black' and g['result'] == '0-1'))

        # Puzzles
        with database.get_connection(database.PUZZLE_DB_PATH) as conn:
            p_solved = conn.execute("SELECT COUNT(*) FROM puzzle_progress WHERE solved = 1").fetchone()[0]

        self.main_window.update_stats_display(games_count, wins, 0, p_solved)

    def update_clocks(self):
        if self.game_controller.time_control == "Unlimited" or self.game_controller.is_game_over():
            return

        turn = self.game_controller.board.turn
        # Approximate decrement
        self.game_controller.clocks[turn] -= 1

        if self.game_controller.clocks[turn] <= 0:
            self.game_controller.clocks[turn] = 0
            self.handle_game_over()

        # Update UI labels
        self.main_window.player_bar.clock_label.setText(self.format_time(self.game_controller.clocks[chess.WHITE]))
        self.main_window.opp_bar.clock_label.setText(self.format_time(self.game_controller.clocks[chess.BLACK]))

    def format_time(self, seconds):
        if seconds == float('inf'): return "∞"
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def run(self):
        return self.app.exec_()

if __name__ == "__main__":
    from datetime import datetime
    app = ChessTrainerApp()
    sys.exit(app.run())
