from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import chess
from board_widget import ChessBoardWidget

class PuzzleWidget(QWidget):
    puzzle_solved = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.puzzle_engine = None; self.current_puzzle = None; self.solution_index = 0
        layout = QHBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)
        self.sidebar_frame = QFrame(); self.sidebar_frame.setFixedWidth(250); self.sidebar = QVBoxLayout(self.sidebar_frame)
        lbl_puzzles = QLabel("Puzzles"); lbl_puzzles.setFont(QFont("Outfit", 18, QFont.Bold)); lbl_puzzles.setStyleSheet("color: #e8e8e8; margin-bottom: 10px;"); self.sidebar.addWidget(lbl_puzzles)
        self.puzzle_list = QListWidget(); self.puzzle_list.setStyleSheet("QListWidget { background-color: #242424; border: 1px solid #3a3a3a; border-radius: 5px; color: #e8e8e8; } QListWidget::item { padding: 10px; border-bottom: 1px solid #3a3a3a; } QListWidget::item:selected { background-color: #3a3a3a; color: #7fa650; }"); self.puzzle_list.itemClicked.connect(self.load_selected_puzzle); self.sidebar.addWidget(self.puzzle_list); layout.addWidget(self.sidebar_frame)
        self.main_area = QVBoxLayout()
        self.info_bar = QFrame(); self.info_bar.setStyleSheet("background-color: #242424; border-radius: 5px; padding: 10px;"); info_layout = QHBoxLayout(self.info_bar); self.lbl_title = QLabel("Select a puzzle to start"); self.lbl_title.setFont(QFont("Outfit", 12, QFont.Bold)); self.lbl_title.setStyleSheet("color: #e8e8e8;"); info_layout.addWidget(self.lbl_title); self.lbl_rating = QLabel(""); self.lbl_rating.setStyleSheet("color: #888888;"); info_layout.addWidget(self.lbl_rating); self.main_area.addWidget(self.info_bar)
        self.board_widget = ChessBoardWidget(); self.board_widget.move_made.connect(self.handle_move); self.main_area.addWidget(self.board_widget, 1)
        self.controls = QHBoxLayout(); self.btn_hint = QPushButton("Hint"); self.btn_reset = QPushButton("Reset"); self.btn_next = QPushButton("Next")
        for btn in [self.btn_hint, self.btn_reset, self.btn_next]: btn.setStyleSheet("background-color: #3a3a3a; color: white; padding: 10px; border-radius: 5px;"); self.controls.addWidget(btn)
        self.btn_hint.clicked.connect(self.show_hint); self.btn_reset.clicked.connect(self.reset_puzzle); self.btn_next.clicked.connect(self.load_next_puzzle); self.main_area.addLayout(self.controls)
        self.lbl_status = QLabel(""); self.lbl_status.setAlignment(Qt.AlignCenter); self.lbl_status.setFont(QFont("Outfit", 14, QFont.Bold)); self.main_area.addWidget(self.lbl_status); layout.addLayout(self.main_area, 1)

    def set_puzzles(self, puzzles):
        self.puzzles = puzzles; self.puzzle_list.clear()
        for p in puzzles: item = QListWidgetItem(f"Puzzle {p['puzzle']['id']} ({p['puzzle'].get('rating', 'N/A')})"); item.setData(Qt.UserRole, p); self.puzzle_list.addItem(item)
        if puzzles: self.puzzle_list.setCurrentRow(0); self.load_selected_puzzle(self.puzzle_list.item(0))

    def load_selected_puzzle(self, item):
        self.current_puzzle = item.data(Qt.UserRole); self.reset_puzzle()

    def reset_puzzle(self):
        if not self.current_puzzle: return
        self.solution_index = 0; self.lbl_status.setText(""); self.board_widget.highlights = {}; self.board_widget.arrows = []
        board = self.puzzle_engine.get_puzzle_board(self.current_puzzle); self.board_widget.set_board(board); self.board_widget.set_flipped(board.turn == chess.BLACK)
        self.lbl_title.setText(f"Find the best move for {'White' if board.turn == chess.WHITE else 'Black'}"); self.lbl_rating.setText(f"Rating: {self.current_puzzle['puzzle'].get('rating', 'Unknown')}"); self.board_widget.update()

    def handle_move(self, move):
        if not self.current_puzzle: return
        solution = self.current_puzzle['puzzle']['solution']; expected_uci = solution[self.solution_index]
        if move.uci() == expected_uci:
            self.board_widget.board.push(move); self.board_widget.highlights = {move.to_square: QColor(0, 255, 0, 150)}; self.solution_index += 1
            if self.solution_index >= len(solution): self.lbl_status.setText("Solved! ✅"); self.lbl_status.setStyleSheet("color: #7fa650;"); self.puzzle_solved.emit(self.current_puzzle['puzzle']['id']); QTimer.singleShot(2200, self.load_next_puzzle)
            else: QTimer.singleShot(700, self.play_opponent_move)
        else:
            self.lbl_status.setText("Wrong move! ❌"); self.lbl_status.setStyleSheet("color: #e74c3c;"); self.board_widget.highlights = {move.to_square: QColor(255, 0, 0, 150)}; QTimer.singleShot(1000, lambda: self.reset_highlights())
        self.board_widget.update()

    def play_opponent_move(self):
        opp_move = chess.Move.from_uci(self.current_puzzle['puzzle']['solution'][self.solution_index]); self.board_widget.board.push(opp_move); self.board_widget.last_move = opp_move; self.solution_index += 1; self.board_widget.update()
    def reset_highlights(self): self.board_widget.highlights = {}; self.board_widget.update()
    def show_hint(self):
        if not self.current_puzzle: return
        self.board_widget.highlights[chess.parse_square(self.current_puzzle['puzzle']['solution'][self.solution_index][:2])] = QColor(0, 0, 255, 100); self.board_widget.update()
    def load_next_puzzle(self):
        next_row = self.puzzle_list.currentRow() + 1
        if next_row < self.puzzle_list.count(): self.puzzle_list.setCurrentRow(next_row); self.load_selected_puzzle(self.puzzle_list.item(next_row))
