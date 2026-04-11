from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame, QSizePolicy,
                             QFileDialog, QCheckBox, QComboBox, QFormLayout, QDialog,
                             QRadioButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

class NavButton(QPushButton):
    def __init__(self, text, icon_text="", parent=None):
        super().__init__(text, parent)
        self.setCheckable(True); self.setMinimumHeight(50); self.setFont(QFont("Outfit", 11))
        self.setStyleSheet("""
            QPushButton { background-color: transparent; color: #e8e8e8; border: none; text-align: left; padding-left: 20px; }
            QPushButton:hover { background-color: #2c2c2c; }
            QPushButton:checked { background-color: #3a3a3a; border-left: 4px solid #7fa650; }
        """)

class BotSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Game"); self.setFixedWidth(450)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select Bot:"))
        self.bot_combo = QComboBox()
        from engine import BOT_PROFILES
        # Add emojis to bots
        self.emojis = ["👶", "🎓", "☕", "🏠", "🧠", "🎯", "🏆", "📜", "👑", "💻"]
        for i, (name, p) in enumerate(BOT_PROFILES.items()):
            emoji = self.emojis[i] if i < len(self.emojis) else "🤖"
            self.bot_combo.addItem(f"{emoji} {name} ({p['elo']} ELO)", name)
        layout.addWidget(self.bot_combo)

        self.lbl_desc = QLabel(BOT_PROFILES["Rookie"]["desc"])
        self.lbl_desc.setStyleSheet("color: #888; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(self.lbl_desc)
        self.bot_combo.currentIndexChanged.connect(self.update_desc)

        layout.addSpacing(10); layout.addWidget(QLabel("Time Control:"))
        self.time_combo = QComboBox(); self.time_combo.addItems(["Unlimited", "1+0", "3+2", "5+0", "10+0", "15+10"]); layout.addWidget(self.time_combo)
        layout.addSpacing(10); layout.addWidget(QLabel("Your Color:"))
        color_group = QHBoxLayout(); self.btn_white = QRadioButton("White"); self.btn_white.setChecked(True); self.btn_black = QRadioButton("Black"); self.btn_random = QRadioButton("Random")
        for b in [self.btn_white, self.btn_black, self.btn_random]: color_group.addWidget(b)
        layout.addLayout(color_group); layout.addSpacing(20)
        btn_start = QPushButton("Start Game"); btn_start.setStyleSheet("background-color: #7fa650; color: white; padding: 10px; font-weight: bold;"); btn_start.clicked.connect(self.accept); layout.addWidget(btn_start)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Trainer"); self.resize(1100, 800)
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        self.main_layout = QHBoxLayout(central_widget); self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        self.init_sidebar(); self.init_content()
        self.setStyleSheet("background-color: #1a1a1a;")

    def init_sidebar(self):
        self.sidebar = QFrame(); self.sidebar.setFixedWidth(200); self.sidebar.setStyleSheet("background-color: #242424; border-right: 1px solid #3a3a3a;")
        self.sidebar_layout = QVBoxLayout(self.sidebar); self.sidebar_layout.setContentsMargins(0, 20, 0, 20); self.sidebar_layout.setSpacing(5)
        logo = QLabel("CHESS TRAINER"); logo.setFont(QFont("Outfit", 14, QFont.Bold)); logo.setStyleSheet("color: #7fa650; margin-bottom: 20px; padding-left: 20px;")
        self.sidebar_layout.addWidget(logo)
        self.btn_play = NavButton("▶  Play"); self.btn_puzzles = NavButton("♟  Puzzles"); self.btn_review = NavButton("📋  Review"); self.btn_stats = NavButton("📊  Stats"); self.btn_settings = NavButton("⚙  Settings")
        self.nav_group = [self.btn_play, self.btn_puzzles, self.btn_review, self.btn_stats, self.btn_settings]
        for i, btn in enumerate(self.nav_group):
            self.sidebar_layout.addWidget(btn); btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
        self.sidebar_layout.addStretch()
        self.engine_status = QLabel("● Engine: Not Loaded"); self.engine_status.setStyleSheet("color: #e74c3c; padding-left: 20px; font-size: 11px;"); self.sidebar_layout.addWidget(self.engine_status)
        self.mini_stats = QLabel("Games: 0 | Wins: 0\nStreak: 0 | Acc: 0%"); self.mini_stats.setStyleSheet("color: #888888; padding-left: 20px; font-size: 11px; margin-top: 10px;"); self.sidebar_layout.addWidget(self.mini_stats)
        self.main_layout.addWidget(self.sidebar)

    def init_content(self):
        self.stack = QStackedWidget()
        self.page_play = self.create_play_page(); self.page_puzzles = QWidget(); self.page_review = QWidget(); self.page_stats = self.create_stats_page(); self.page_settings = self.create_settings_page()
        for p in [self.page_play, self.page_puzzles, self.page_review, self.page_stats, self.page_settings]: self.stack.addWidget(p)
        self.main_layout.addWidget(self.stack); self.btn_play.setChecked(True); self.stack.setCurrentIndex(0)

    def switch_page(self, index):
        for i, btn in enumerate(self.nav_group): btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def set_engine_status(self, loaded):
        if loaded: self.engine_status.setText("● Engine: Loaded"); self.engine_status.setStyleSheet("color: #7fa650; padding-left: 20px; font-size: 11px;")
        else: self.engine_status.setText("● Engine: Not Loaded"); self.engine_status.setStyleSheet("color: #e74c3c; padding-left: 20px; font-size: 11px;")

    def create_settings_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Settings"); title.setFont(QFont("Outfit", 24, QFont.Bold)); title.setStyleSheet("color: #e8e8e8;"); layout.addWidget(title); layout.addSpacing(30)
        form = QFormLayout(); form.setSpacing(20); form.setLabelAlignment(Qt.AlignRight)
        self.engine_path_label = QLabel("None"); self.engine_path_label.setStyleSheet("color: #888888;"); btn_browse = QPushButton("Browse..."); btn_browse.setFixedWidth(100); btn_browse.setStyleSheet("background-color: #3a3a3a; color: #e8e8e8; border: 1px solid #555; padding: 5px;"); btn_browse.clicked.connect(self.browse_engine)
        engine_row = QHBoxLayout(); engine_row.addWidget(self.engine_path_label); engine_row.addWidget(btn_browse); form.addRow(self.create_form_label("Stockfish Path:"), engine_row)
        self.combo_theme = QComboBox(); self.combo_theme.addItems(["Brown", "Blue", "Green"]); self.combo_theme.setStyleSheet("background-color: #3a3a3a; color: #e8e8e8; border: 1px solid #555; padding: 5px;"); form.addRow(self.create_form_label("Board Theme:"), self.combo_theme)
        self.combo_depth = QComboBox(); self.combo_depth.addItems(["12", "16", "18", "20"]); self.combo_depth.setStyleSheet("background-color: #3a3a3a; color: #e8e8e8; border: 1px solid #555; padding: 5px;"); form.addRow(self.create_form_label("Analysis Depth:"), self.combo_depth)
        self.check_sound = QCheckBox("Enable Sound Effects"); self.check_sound.setStyleSheet("color: #e8e8e8;"); self.check_sound.setChecked(True); form.addRow(self.create_form_label("Sound:"), self.check_sound)
        self.check_promote = QCheckBox("Auto-promote to Queen"); self.check_promote.setStyleSheet("color: #e8e8e8;"); self.check_promote.setChecked(True); form.addRow(self.create_form_label("Promotion:"), self.check_promote)
        layout.addLayout(form); layout.addStretch(); return page

    def create_form_label(self, text):
        lbl = QLabel(text); lbl.setFont(QFont("Outfit", 11)); lbl.setStyleSheet("color: #e8e8e8;"); return lbl

    def browse_engine(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Stockfish Binary")
        if path:
            self.engine_path_label.setText(path)
            import database; database.save_setting("stockfish_path", path)

    def create_stats_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Dashboard"); title.setFont(QFont("Outfit", 24, QFont.Bold)); title.setStyleSheet("color: #e8e8e8;"); layout.addWidget(title); layout.addSpacing(30)
        grid = QHBoxLayout(); grid.setSpacing(20)
        self.card_games = self.create_stat_card("GAMES", "0"); self.card_wins = self.create_stat_card("WINS", "0"); self.card_accuracy = self.create_stat_card("AVG ACCURACY", "0%"); self.card_puzzles = self.create_stat_card("PUZZLES", "0")
        for c in [self.card_games, self.card_wins, self.card_accuracy, self.card_puzzles]: grid.addWidget(c)
        layout.addLayout(grid); layout.addSpacing(40)
        hist_title = QLabel("Recent Games"); hist_title.setFont(QFont("Outfit", 14, QFont.Bold)); hist_title.setStyleSheet("color: #e8e8e8;"); layout.addWidget(hist_title)
        self.history_list = QVBoxLayout(); layout.addLayout(self.history_list); layout.addStretch(); return page

    def create_stat_card(self, title, value):
        card = QFrame(); card.setStyleSheet("background-color: #2c2c2c; border-radius: 10px; padding: 20px;"); layout = QVBoxLayout(card)
        t_lbl = QLabel(title); t_lbl.setFont(QFont("Outfit", 9, QFont.Bold)); t_lbl.setStyleSheet("color: #888888;")
        v_lbl = QLabel(value); v_lbl.setFont(QFont("Outfit", 20, QFont.Bold)); v_lbl.setStyleSheet("color: #e8e8e8;")
        layout.addWidget(t_lbl); layout.addWidget(v_lbl); card.value_label = v_lbl; return card

    def update_desc(self, idx):
        from engine import BOT_PROFILES
        name = self.bot_combo.itemData(idx)
        self.lbl_desc.setText(BOT_PROFILES[name]["desc"])

    def update_stats_display(self, games, wins, accuracy, puzzles, streak=0):
        self.card_games.value_label.setText(str(games)); self.card_wins.value_label.setText(str(wins)); self.card_accuracy.value_label.setText(f"{accuracy}%"); self.card_puzzles.value_label.setText(str(puzzles))
        self.mini_stats.setText(f"Games: {games} | Wins: {wins}\nStreak: {streak} | Acc: {accuracy}%")

    def create_play_page(self):
        from board_widget import ChessBoardWidget, EvalBarWidget
        page = QWidget(); layout = QHBoxLayout(page); layout.setContentsMargins(20, 20, 20, 20)
        board_container = QVBoxLayout(); self.opp_bar = self.create_player_bar("Bot (1200)", "🤖"); board_container.addWidget(self.opp_bar)
        mid_layout = QHBoxLayout(); self.eval_bar = EvalBarWidget(); mid_layout.addWidget(self.eval_bar); self.board_widget = ChessBoardWidget(); mid_layout.addWidget(self.board_widget, 1); board_container.addLayout(mid_layout)
        self.player_bar = self.create_player_bar("You", "👤"); board_container.addWidget(self.player_bar); layout.addLayout(board_container, 3)
        sidebar_frame = QFrame(); sidebar_frame.setFixedWidth(300); sidebar = QVBoxLayout(sidebar_frame); sidebar.setSpacing(10)
        info_card = QFrame(); info_card.setStyleSheet("background-color: #242424; border-radius: 5px;"); info_layout = QVBoxLayout(info_card); self.lbl_opening = QLabel("Starting Position"); self.lbl_opening.setStyleSheet("color: #7fa650; font-weight: bold;"); info_layout.addWidget(self.lbl_opening)
        self.move_list = QLabel("Moves will appear here..."); self.move_list.setWordWrap(True); self.move_list.setStyleSheet("color: #e8e8e8; font-family: monospace;"); info_layout.addWidget(self.move_list); info_layout.addStretch(); sidebar.addWidget(info_card, 1)
        self.btn_new_game = QPushButton("New Game"); self.btn_new_game.setStyleSheet("background-color: #7fa650; color: white; padding: 10px; font-weight: bold;")
        self.btn_hint = QPushButton("Hint"); self.btn_hint.setStyleSheet("background-color: #3a3a3a; color: white; padding: 10px;")
        self.btn_draw = QPushButton("Offer Draw"); self.btn_draw.setStyleSheet("background-color: #3a3a3a; color: white; padding: 10px;")
        self.btn_resign = QPushButton("Resign"); self.btn_resign.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
        for b in [self.btn_new_game, self.btn_hint, self.btn_draw, self.btn_resign]: sidebar.addWidget(b)
        layout.addWidget(sidebar_frame); return page

    def create_player_bar(self, name, avatar):
        bar = QFrame(); bar.setFixedHeight(60); bar.setStyleSheet("background-color: #242424; border-radius: 5px;"); layout = QHBoxLayout(bar)
        av = QLabel(avatar); av.setFont(QFont("Segoe UI Emoji", 20)); layout.addWidget(av)
        n = QLabel(name); n.setFont(QFont("Outfit", 12, QFont.Bold)); n.setStyleSheet("color: #e8e8e8;"); layout.addWidget(n)
        layout.addStretch()
        clock = QLabel("10:00"); clock.setFont(QFont("monospace", 18, QFont.Bold)); clock.setStyleSheet("color: #e8e8e8; background-color: #1a1a1a; padding: 5px; border-radius: 3px;"); layout.addWidget(clock)
        bar.name_label = n; bar.clock_label = clock; return bar
