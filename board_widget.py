import chess
from PyQt5.QtWidgets import QWidget, QMenu, QAction
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QSize, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QRadialGradient, QBrush

PIECE_SYMBOLS = {
    chess.PAWN: "♙",
    chess.KNIGHT: "♘",
    chess.BISHOP: "♗",
    chess.ROOK: "♖",
    chess.QUEEN: "♕",
    chess.KING: "♔"
}

COLORS = {
    "light_sq": QColor("#f0d9b5"),
    "dark_sq": QColor("#b58863"),
    "highlight": QColor(255, 255, 0, 100),
    "last_move": QColor(155, 199, 0, 100),
    "selected": QColor(20, 85, 30, 100),
    "legal_dot": QColor(0, 0, 0, 30),
    "check_gradient": QColor(255, 0, 0, 150),
    "wrong_move": QColor(255, 0, 0, 150),
    "correct_move": QColor(0, 255, 0, 150),
    "white_piece": QColor("#ffffff"),
    "black_piece": QColor("#222222"),
    "piece_outline_white": QColor("#000000"),
    "piece_outline_black": QColor("#ffffff"),
}

class ChessBoardWidget(QWidget):
    move_made = pyqtSignal(chess.Move)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.flipped = False
        self.selected_sq = None
        self.last_move = None
        self.legal_moves = []
        self.highlights = {}
        self.arrows = []
        self.auto_promote_queen = True
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)

    def set_board(self, board):
        self.board = board
        self.update()

    def set_flipped(self, flipped):
        self.flipped = flipped
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        sq_size = min(self.width(), self.height()) // 8
        offset_x = (self.width() - sq_size * 8) // 2
        offset_y = (self.height() - sq_size * 8) // 2
        self.sq_size = sq_size
        self.offset_x = offset_x
        self.offset_y = offset_y
        for rank in range(8):
            for file in range(8):
                sq = self._get_square(rank, file)
                rect = self._get_sq_rect(rank, file)
                color = COLORS["light_sq"] if (rank + file) % 2 == 0 else COLORS["dark_sq"]
                painter.fillRect(rect, color)
                if sq == self.selected_sq:
                    painter.fillRect(rect, COLORS["selected"])
                elif self.last_move and (sq == self.last_move.from_square or sq == self.last_move.to_square):
                    painter.fillRect(rect, COLORS["last_move"])
                if sq in self.highlights:
                    painter.fillRect(rect, self.highlights[sq])
                piece = self.board.piece_at(sq)
                if piece:
                    self._draw_piece(painter, piece, rect)
                if sq in self.legal_moves:
                    center = rect.center()
                    if self.board.piece_at(sq):
                        painter.setPen(QPen(COLORS["legal_dot"], sq_size // 10))
                        painter.drawEllipse(center, sq_size // 2.5, sq_size // 2.5)
                    else:
                        painter.setBrush(COLORS["legal_dot"])
                        painter.setPen(Qt.NoPen)
                        painter.drawEllipse(center, sq_size // 6, sq_size // 6)
        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                rect = self._get_sq_rect_from_sq(king_sq)
                grad = QRadialGradient(rect.center(), sq_size // 2)
                grad.setColorAt(0, COLORS["check_gradient"])
                grad.setColorAt(1, Qt.transparent)
                painter.fillRect(rect, QBrush(grad))
        self._draw_coordinates(painter)
        for from_sq, to_sq, color in self.arrows:
            self._draw_arrow(painter, from_sq, to_sq, color)

    def _get_square(self, rank, file):
        if self.flipped: return chess.square(file, rank)
        else: return chess.square(file, 7 - rank)

    def _get_sq_rect(self, rank, file):
        return QRect(self.offset_x + file * self.sq_size, self.offset_y + rank * self.sq_size, self.sq_size, self.sq_size)

    def _get_sq_rect_from_sq(self, sq):
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        if self.flipped: return self._get_sq_rect(rank, file)
        else: return self._get_sq_rect(7 - rank, file)

    def _draw_piece(self, painter, piece, rect):
        font = QFont("Arial", int(self.sq_size * 0.8))
        painter.setFont(font)
        symbol = PIECE_SYMBOLS[piece.piece_type]
        is_white = piece.color == chess.WHITE
        color = COLORS["white_piece"] if is_white else COLORS["black_piece"]
        outline = COLORS["piece_outline_white"] if is_white else COLORS["piece_outline_black"]
        painter.setPen(outline)
        for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1), (0,-1), (0,1), (-1,0), (1,0)]:
            painter.drawText(rect.translated(dx, dy), Qt.AlignCenter, symbol)
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignCenter, symbol)

    def _draw_coordinates(self, painter):
        painter.setPen(QColor("#888888"))
        painter.setFont(QFont("Arial", 10))
        for i in range(8):
            file_char = chr(ord('a') + (7 - i if self.flipped else i))
            painter.drawText(self.offset_x + i * self.sq_size + 2, self.offset_y + 8 * self.sq_size - 2, file_char)
            rank_char = str(i + 1 if self.flipped else 8 - i)
            painter.drawText(self.offset_x + 8 * self.sq_size - 10, self.offset_y + i * self.sq_size + 12, rank_char)

    def _draw_arrow(self, painter, from_sq, to_sq, color):
        p1 = self._get_sq_rect_from_sq(from_sq).center()
        p2 = self._get_sq_rect_from_sq(to_sq).center()
        painter.setPen(QPen(color, self.sq_size // 6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(p1, p2)
        import math
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        dist = 15
        arrow_p1 = p2 - QPoint(int(dist * math.cos(angle - math.pi/6)), int(dist * math.sin(angle - math.pi/6)))
        arrow_p2 = p2 - QPoint(int(dist * math.cos(angle + math.pi/6)), int(dist * math.sin(angle + math.pi/6)))
        painter.drawLine(p2, arrow_p1)
        painter.drawLine(p2, arrow_p2)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        x, y = event.x() - self.offset_x, event.y() - self.offset_y
        if x < 0 or y < 0 or x >= 8 * self.sq_size or y >= 8 * self.sq_size:
            self.selected_sq = None; self.legal_moves = []; self.update(); return
        file = x // self.sq_size; rank = y // self.sq_size; sq = self._get_square(rank, file)
        if self.selected_sq is not None:
            move = self._get_move(self.selected_sq, sq)
            if move in self.board.legal_moves: self.move_made.emit(move); self.selected_sq = None; self.legal_moves = []
            elif self.board.piece_at(sq) and self.board.piece_at(sq).color == self.board.turn:
                self.selected_sq = sq; self._update_legal_moves()
            else: self.selected_sq = None; self.legal_moves = []
        else:
            piece = self.board.piece_at(sq)
            if piece and piece.color == self.board.turn: self.selected_sq = sq; self._update_legal_moves()
        self.update()

    def _get_move(self, from_sq, to_sq):
        move = chess.Move(from_sq, to_sq)
        piece = self.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN:
            if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
                if self.auto_promote_queen: move.promotion = chess.QUEEN
                else: move.promotion = self._show_promotion_dialog()
        return move

    def _update_legal_moves(self):
        self.legal_moves = [m.to_square for m in self.board.legal_moves if m.from_square == self.selected_sq]

    def _show_promotion_dialog(self):
        menu = QMenu(self)
        q = menu.addAction("Queen"); r = menu.addAction("Rook"); b = menu.addAction("Bishop"); n = menu.addAction("Knight")
        action = menu.exec_(self.mapToGlobal(self._get_sq_rect_from_sq(self.selected_sq).center()))
        if action == q: return chess.QUEEN
        if action == r: return chess.ROOK
        if action == b: return chess.BISHOP
        if action == n: return chess.KNIGHT
        return chess.QUEEN

class EvalBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedWidth(24); self.eval = 0.0; self.is_mate = False
    def set_eval(self, cp, is_mate=False):
        self.eval = cp; self.is_mate = is_mate; self.update()
    def paintEvent(self, event):
        painter = QPainter(self); import math
        if self.is_mate: white_fraction = 1.0 if self.eval > 0 else 0.0
        else: white_fraction = 1.0 / (1.0 + math.exp(-self.eval / 350.0))
        h = self.height(); white_h = int(h * white_fraction)
        painter.fillRect(0, 0, self.width(), h - white_h, QColor("#222222"))
        painter.fillRect(0, h - white_h, self.width(), white_h, QColor("#e8e8e8"))
        painter.setPen(Qt.black if white_fraction > 0.5 else Qt.white)
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        txt = f"{self.eval/100.0:+.1f}" if not self.is_mate else f"M{abs(int(self.eval))}"
        painter.drawText(self.rect(), Qt.AlignHCenter | (Qt.AlignBottom if white_fraction > 0.5 else Qt.AlignTop), txt)
