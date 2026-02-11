from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QSlider, QListWidgetItem, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from ui.icons import get_icon, SVG_PLAY, SVG_PAUSE, SVG_STOP, SVG_NEXT, SVG_PREV, SVG_CHEVRON_LEFT
from ui.visualizer import RotatingAlbumArt, BarVisualizer

class NowPlayingWidget(QWidget):
    back_clicked = pyqtSignal()
    next_song_requested = pyqtSignal(dict) # video dict
    play_pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(10, 10, 10, 0)
        
        back_btn = QPushButton()
        back_btn.setIcon(get_icon(SVG_CHEVRON_LEFT))
        back_btn.setIconSize(QSize(28, 28))
        back_btn.setFixedSize(40, 40)
        back_btn.setToolTip("Back to Library")
        back_btn.clicked.connect(self.back_clicked.emit)
        # Circular transparent button
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1); 
                border-radius: 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2); 
            }
        """)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        layout.addLayout(top_bar)
        
        # Main Info Area (Centered)
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Rotating Visualizer
        self.visualizer = RotatingAlbumArt()
        info_layout.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.title_label = QLabel("No Song Playing")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label)
        
        self.duration_label = QLabel("--:--")
        self.duration_label.setStyleSheet("color: #aaa;")
        info_layout.addWidget(self.duration_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(info_layout, stretch=2)
        
        # Controls
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        
        # Bar Visualizer
        self.bar_vis = BarVisualizer()
        controls_layout.addWidget(self.bar_vis)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.progress_slider.sliderMoved.connect(self.seek_requested.emit)
        controls_layout.addWidget(self.progress_slider)
        
        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(25)
        btns_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        # Common Button Style
        btn_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(187, 134, 252, 0.5);
            }
        """
        
        # Prev Button
        prev_btn = QPushButton()
        prev_btn.setIcon(get_icon(SVG_PREV))
        prev_btn.setIconSize(QSize(24, 24))
        prev_btn.setFixedSize(50, 50)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet(btn_style)
        prev_btn.clicked.connect(self.prev_clicked.emit)
        btns_layout.addWidget(prev_btn)
        
        # Play/Pause (Primary Gradient)
        self.play_btn = QPushButton()
        self.play_btn.setIcon(get_icon(SVG_PLAY, "black"))
        self.play_btn.setIconSize(QSize(32, 32))
        self.play_btn.setFixedSize(70, 70)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #BB86FC, stop:1 #985EFF);
                border-radius: 35px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C495FD, stop:1 #A673FF);
                margin-top: -2px;
            }
        """)
        self.play_btn.clicked.connect(self.play_pause_clicked.emit)
        btns_layout.addWidget(self.play_btn)
        
        # Next Button
        next_btn = QPushButton()
        next_btn.setIcon(get_icon(SVG_NEXT))
        next_btn.setIconSize(QSize(24, 24))
        next_btn.setFixedSize(50, 50)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet(btn_style)
        next_btn.clicked.connect(self.next_clicked.emit)
        btns_layout.addWidget(next_btn)
        
        controls_layout.addLayout(btns_layout)
        
        layout.addLayout(controls_layout, stretch=1)

        # Up Next / Recommendations
        layout.addWidget(QLabel("UP NEXT"))
        self.up_next_list = QListWidget() 
        self.up_next_list.setFixedHeight(180)
        layout.addWidget(self.up_next_list, stretch=1)

    def update_info(self, video, pixmap=None):
        self.title_label.setText(video.get('title', 'Unknown'))
        if pixmap:
            self.visualizer.set_pixmap(pixmap)
        else:
            self.visualizer.set_pixmap(None)
            
        duration = video.get('duration')
        if isinstance(duration, (int, float)):
            m, s = divmod(int(duration), 60)
            self.duration_label.setText(f"{m}:{s:02d}")

    def update_play_btn(self, is_playing):
        icon = get_icon(SVG_PAUSE if is_playing else SVG_PLAY)
        self.play_btn.setIcon(icon)
        self.visualizer.set_playing(is_playing)
        self.bar_vis.set_playing(is_playing)

    def on_item_double_clicked(self, item):
        video = item.data(Qt.ItemDataRole.UserRole)
        self.next_song_requested.emit(video)
