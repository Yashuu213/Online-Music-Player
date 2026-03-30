from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QSlider, QListWidgetItem, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from ui.icons import get_icon, SVG_PLAY, SVG_PAUSE, SVG_STOP, SVG_NEXT, SVG_PREV, SVG_CHEVRON_LEFT
from ui.visualizer import RotatingAlbumArt, BarVisualizer
from ui.custom_widgets import SongItemWidget

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main Glass Container
        self.main_container = QFrame()
        # Full screen gradient matching the Pikachu theme
        self.main_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #090B1E, stop:0.5 #0F1229, stop:1 #050714);
            }
        """)
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(40, 20, 40, 40)
        
        # Top Bar
        top_bar = QHBoxLayout()
        back_btn = QPushButton()
        back_btn.setIcon(get_icon(SVG_CHEVRON_LEFT, "#FFD700"))
        back_btn.setIconSize(QSize(30, 30))
        back_btn.setFixedSize(50, 50)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 25px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QPushButton:hover {
                background: rgba(255, 215, 0, 0.1);
                border: 1px solid #FFD700;
            }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        top_bar.addWidget(back_btn)
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)
        
        # Middle Section: Art & Info
        content_layout = QHBoxLayout()
        content_layout.setSpacing(60)
        
        # Left: Rotating Art
        art_container = QVBoxLayout()
        self.visualizer = RotatingAlbumArt()
        art_container.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Bar Visualizer below art
        self.bar_vis = BarVisualizer()
        self.bar_vis.setFixedWidth(300)
        art_container.addWidget(self.bar_vis, alignment=Qt.AlignmentFlag.AlignCenter)
        
        content_layout.addLayout(art_container)
        
        # Right: Info & Queue
        info_queue_layout = QVBoxLayout()
        info_queue_layout.setSpacing(20)
        
        self.title_label = QLabel("No Song Playing")
        self.title_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #FFD700;")
        self.title_label.setWordWrap(True)
        info_queue_layout.addWidget(self.title_label)
        
        self.artist_label = QLabel("Select a track to start listening")
        self.artist_label.setObjectName("MutedText")
        self.artist_label.setStyleSheet("font-size: 18px; color: #94A3B8;")
        info_queue_layout.addWidget(self.artist_label)
        
        info_queue_layout.addSpacing(20)
        
        # Up Next List (Modernized)
        queue_header = QLabel("UP NEXT")
        queue_header.setStyleSheet("font-weight: 800; font-size: 14px; letter-spacing: 2px; color: #00E5FF;")
        info_queue_layout.addWidget(queue_header)
        
        self.up_next_list = QListWidget()
        self.up_next_list.setObjectName("QueueList")
        self.up_next_list.setStyleSheet("""
            QListWidget { background: transparent; }
            QListWidget::item { margin-bottom: 10px; }
        """)
        info_queue_layout.addWidget(self.up_next_list)
        
        content_layout.addLayout(info_queue_layout, stretch=1)
        main_layout.addLayout(content_layout, stretch=1)
        
        # Bottom: Player Controls
        controls_container = QVBoxLayout()
        controls_container.setSpacing(10)
        
        # Progress
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.current_time_label.setObjectName("MutedText")
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setObjectName("ProgressSlider") # Styled in styles.py
        self.progress_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.progress_slider.sliderMoved.connect(self.seek_requested.emit)
        
        self.total_time_label = QLabel("0:00")
        self.total_time_label.setObjectName("MutedText")
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)
        controls_container.addLayout(progress_layout)
        
        # Buttons
        btns_layout = QHBoxLayout()
        btns_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btns_layout.setSpacing(30)
        
        # Sub-buttons style
        sub_btn_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 25px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid #00E5FF;
            }
        """
        
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(get_icon(SVG_PREV, "#FFF"))
        self.prev_btn.setIconSize(QSize(24, 24))
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.setStyleSheet(sub_btn_style)
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        btns_layout.addWidget(self.prev_btn)
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(get_icon(SVG_PLAY, "#000"))
        self.play_btn.setIconSize(QSize(36, 36))
        self.play_btn.setFixedSize(80, 80)
        self.play_btn.setObjectName("PrimaryAction") # Styled in styles.py
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self.play_pause_clicked.emit)
        btns_layout.addWidget(self.play_btn)
        
        self.next_btn = QPushButton()
        self.next_btn.setIcon(get_icon(SVG_NEXT, "#FFF"))
        self.next_btn.setIconSize(QSize(24, 24))
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.setStyleSheet(sub_btn_style)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        btns_layout.addWidget(self.next_btn)
        
        controls_container.addLayout(btns_layout)
        main_layout.addLayout(controls_container)
        
        layout.addWidget(self.main_container)

    def update_info(self, video, pixmap=None):
        self.title_label.setText(video.get('title', 'Unknown'))
        
        # Try to parse artist from title "Artist - Title"
        title = video.get('title', '')
        if ' - ' in title:
            self.artist_label.setText(title.split(' - ')[0])
        else:
            self.artist_label.setText("YouTube Audio")
            
        if pixmap:
            self.visualizer.set_pixmap(pixmap)
        else:
            self.visualizer.set_pixmap(None)
            
        duration = video.get('duration')
        if isinstance(duration, (int, float)):
            m, s = divmod(int(duration), 60)
            self.total_time_label.setText(f"{m}:{s:02d}")
            self.progress_slider.setRange(0, int(duration * 1000))

    def update_play_btn(self, is_playing):
        icon = get_icon(SVG_PAUSE if is_playing else SVG_PLAY, "#000")
        self.play_btn.setIcon(icon)
        self.visualizer.set_playing(is_playing)
        self.bar_vis.set_playing(is_playing)

    def update_progress(self, current_ms):
        self.progress_slider.setValue(current_ms)
        m, s = divmod(current_ms // 1000, 60)
        self.current_time_label.setText(f"{m}:{s:02d}")

    def set_ambient_color(self, color):
        """Sets the ambient glow background based on the extracted color."""
        # We use a dark version of the color to keep contrast high
        dark_color = color.darker(150)
        hex_color = dark_color.name()
        
        self.main_container.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:1.2, fx:0.5, fy:0.5, 
                    stop:0 {hex_color}, stop:1 #090B1E);
            }}
        """)
