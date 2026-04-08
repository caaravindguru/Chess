from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPolygonF
import chess
from board_widget import ChessBoardWidget

class EvalGraph(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.scores = []; self.setMinimumHeight(150)
    def set_scores(self, scores): self.scores = scores; self.update()
    def paintEvent(self, event):
        if not self.scores: return
        painter = QPainter(self); painter.setRenderHint(QPainter.Antialiasing); w = self.width(); h = self.height(); mid_y = h // 2
        painter.fillRect(self.rect(), QColor("#242424")); painter.setPen(QColor("#3a3a3a")); painter.drawLine(0, mid_y, w, mid_y)
        if len(self.scores) < 2: return
        points = []; step_x = w / (len(self.scores) - 1)
        import math
        for i, score in enumerate(self.scores):
            white_fraction = 1.0 / (1.0 + math.exp(-score / 350.0))
            y = h - (white_fraction * h)
            points.append(QPoint(int(i * step_x), int(y)))
        poly_white = QPolygonF(); poly_white.append(QPoint(0, mid_y))
        for p in points: poly_white.append(p)
        poly_white.append(QPoint(w, mid_y)); painter.setBrush(QColor(127, 166, 80, 50)); painter.setPen(Qt.NoPen); painter.drawPolygon(poly_white)
        painter.setPen(QPen(QColor("#7fa650"), 2))
        for i in range(len(points) - 1): painter.drawLine(points[i], points[i+1])

class ReviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.analyzed_moves = []; self.current_idx = -1
        layout = QHBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)
        left_layout = QVBoxLayout(); self.board_widget = ChessBoardWidget(); left_layout.addWidget(self.board_widget); self.graph = EvalGraph(); left_layout.addWidget(self.graph); layout.addLayout(left_layout, 2)
        right_frame = QFrame(); right_frame.setFixedWidth(350); right_layout = QVBoxLayout(right_frame)
        self.info_card = QFrame(); self.info_card.setStyleSheet("background-color: #242424; border-radius: 5px; padding: 15px;"); self.info_layout = QVBoxLayout(self.info_card); self.lbl_move = QLabel("Select a move"); self.lbl_move.setFont(QFont("Outfit", 16, QFont.Bold)); self.lbl_move.setStyleSheet("color: #e8e8e8;"); self.info_layout.addWidget(self.lbl_move)
        self.lbl_eval = QLabel(""); self.lbl_eval.setStyleSheet("color: #888888;"); self.info_layout.addWidget(self.lbl_eval); self.lbl_best = QLabel(""); self.lbl_best.setStyleSheet("color: #7fa650;"); self.info_layout.addWidget(self.lbl_best); right_layout.addWidget(self.info_card)
        self.move_list = QListWidget(); self.move_list.setStyleSheet("QListWidget { background-color: #242424; color: #e8e8e8; border: none; } QListWidget::item { padding: 5px; } QListWidget::item:selected { background-color: #3a3a3a; }"); self.move_list.currentRowChanged.connect(self.show_move); right_layout.addWidget(self.move_list); layout.addWidget(right_frame)

    def set_data(self, analyzed_moves):
        self.analyzed_moves = analyzed_moves; self.move_list.clear(); scores = []
        for i, m in enumerate(analyzed_moves):
            text = f"{i//2 + 1}. {m['san'] if m['color']=='white' else '... ' + m['san']}"
            if 'symbol' in m and m['symbol']: text += f" {m['symbol']} [{m['classification'].upper()}]"
            item = QListWidgetItem(text)
            if m.get('classification') == 'Blunder': item.setForeground(QColor("#e74c3c"))
            elif m.get('classification') == 'Mistake': item.setForeground(QColor("#e67e22"))
            elif m.get('classification') == 'Inaccuracy': item.setForeground(QColor("#f4d03f"))
            elif m.get('classification') == 'Best': item.setForeground(QColor("#7fa650"))
            self.move_list.addItem(item)
            score = m['eval_after']; scores.append(score if m['color'] == 'white' else -score)
        self.graph.set_scores(scores)
        if analyzed_moves: self.move_list.setCurrentRow(0)

    def show_move(self, idx):
        if idx < 0 or idx >= len(self.analyzed_moves): return
        self.current_idx = idx; move_data = self.analyzed_moves[idx]; board = chess.Board(move_data['fen_after']); self.board_widget.set_board(board); self.board_widget.last_move = chess.Move.from_uci(move_data['uci'])
        self.lbl_move.setText(f"Move {idx//2 + 1}: {move_data['san']} {move_data.get('symbol', '')}")
        self.lbl_eval.setText(f"Eval: {move_data['eval_after']/100.0:+.2f} ({move_data.get('classification', 'Good')})")
        self.lbl_best.setText(f"Best: {move_data.get('best_uci', 'N/A')}")
        self.board_widget.arrows = []
        if move_data.get('best_uci') and move_data['best_uci'] != move_data['uci']:
            best_move = chess.Move.from_uci(move_data['best_uci'])
            color = QColor("#f4d03f"); cls = move_data.get('classification')
            if cls == 'Mistake': color = QColor("#e67e22")
            elif cls == 'Blunder': color = QColor("#e74c3c")
            self.board_widget.arrows.append((best_move.from_square, best_move.to_square, color))
        self.board_widget.update()
