from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QSlider, QListWidgetItem, QFrame, QScrollArea, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QVariantAnimation, QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QPixmap, QIcon, QColor, QBrush, QLinearGradient, QRadialGradient, QPalette
from ui.icons import get_icon, SVG_PLAY, SVG_PAUSE, SVG_STOP, SVG_NEXT, SVG_PREV, SVG_CHEVRON_LEFT, SVG_BACKWARD_10, SVG_FORWARD_10
from ui.visualizer import RotatingAlbumArt, BarVisualizer
from ui.custom_widgets import SongItemWidget

class NowPlayingWidget(QWidget):
    back_clicked = pyqtSignal()
    add_to_playlist_clicked = pyqtSignal(dict) # Emit the current video data
    next_song_requested = pyqtSignal(dict) # video dict
    play_pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    skip_backward_clicked = pyqtSignal()
    skip_forward_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.current_base_color = QColor("#090B1E")
        self.init_ui()
        self.setup_animations()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main Glass Container
        self.main_container = QFrame()
        self.main_container.setObjectName("NowPlayingContainer")
        self.main_container.setStyleSheet("background: #090B1E;") # Initial
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(40, 20, 40, 40)
        
        # Top Bar
        top_bar = QHBoxLayout()
        back_btn = QPushButton()
        back_btn.setIcon(get_icon(SVG_CHEVRON_LEFT, "#FFD700"))
        back_btn.setIconSize(QSize(30, 30))
        back_btn.setFixedSize(50, 50)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("QPushButton { background: rgba(255,255,255,0.05); border-radius: 25px; border: 1px solid rgba(255,255,255,0.1); } QPushButton:hover { background: rgba(255,215,0,0.1); border: 1px solid #FFD700; }")
        back_btn.clicked.connect(self.back_clicked.emit)
        top_bar.addWidget(back_btn)
        
        top_bar.addStretch()
        
        # Mode Toggle (Art vs Lyrics)
        self.mode_toggle = QPushButton("Lyrics ✨")
        self.mode_toggle.setFixedSize(100, 40)
        self.mode_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_toggle.setStyleSheet("QPushButton { background: rgba(0, 229, 255, 0.1); color: #00E5FF; border-radius: 20px; font-weight: 800; border: 1px solid #00E5FF; } QPushButton:hover { background: #00E5FF; color: #000; }")
        self.mode_toggle.clicked.connect(self.toggle_mode)
        top_bar.addWidget(self.mode_toggle)
        
        main_layout.addLayout(top_bar)
        
        # Middle Section Container (Adaptive)
        self.content_container = QWidget()
        self.content_layout = QHBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0); self.content_layout.setSpacing(60)
        
        self.art_lyrics_stack = QStackedWidget()
        
        # Slide 1: Art View
        self.art_container_w = QWidget(); self.art_container_l = QVBoxLayout(self.art_container_w)
        self.art_container_l.setContentsMargins(0, 0, 0, 0)
        self.visualizer = RotatingAlbumArt()
        self.art_container_l.addWidget(self.visualizer, alignment=Qt.AlignmentFlag.AlignCenter)
        self.bar_vis = BarVisualizer(); self.bar_vis.setFixedWidth(300)
        self.art_container_l.addWidget(self.bar_vis, alignment=Qt.AlignmentFlag.AlignCenter)
        self.art_lyrics_stack.addWidget(self.art_container_w)
        
        # Slide 2: Lyrics View
        lyrics_container_w = QWidget(); lyrics_container = QVBoxLayout(lyrics_container_w)
        lyrics_header = QLabel("LYRICS"); lyrics_header.setStyleSheet("font-weight: 800; color: #00E5FF; letter-spacing: 4px; font-size: 16px;")
        lyrics_container.addWidget(lyrics_header)
        self.lyrics_scroll = QScrollArea(); self.lyrics_scroll.setWidgetResizable(True); self.lyrics_scroll.setStyleSheet("background: transparent; border: none;")
        self.lyrics_label = QLabel("Loading magical words..."); self.lyrics_label.setWordWrap(True)
        self.lyrics_label.setStyleSheet("font-size: 32px; font-weight: 900; line-height: 1.5; color: #E2E8F0; padding-right: 20px;")
        self.lyrics_scroll.setWidget(self.lyrics_label)
        lyrics_container.addWidget(self.lyrics_scroll)
        self.art_lyrics_stack.addWidget(lyrics_container_w)
        
        self.content_layout.addWidget(self.art_lyrics_stack)
        
        # Right/Bottom Section: Info & Queue
        self.info_queue_widget = QWidget()
        self.info_queue_layout = QVBoxLayout(self.info_queue_widget); self.info_queue_layout.setSpacing(15)
        self.info_queue_layout.setContentsMargins(0, 0, 0, 0)
        
        title_hl = QHBoxLayout(); title_hl.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("No Song Playing"); self.title_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #FFD700;"); self.title_label.setWordWrap(True)
        title_hl.addWidget(self.title_label, stretch=1)
        
        self.add_btn = QPushButton()
        from ui.icons import SVG_ADD
        self.add_btn.setIcon(get_icon(SVG_ADD, "#00E5FF")); self.add_btn.setIconSize(QSize(24, 24)); self.add_btn.setFixedSize(40, 40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("QPushButton { background: rgba(0, 229, 255, 0.1); border-radius: 20px; border: 1px solid rgba(0, 229, 255, 0.2); } QPushButton:hover { background: #00E5FF; }")
        self.add_btn.clicked.connect(lambda: self.add_to_playlist_clicked.emit(self.current_video) if hasattr(self, 'current_video') and self.current_video else None)
        title_hl.addWidget(self.add_btn)
        
        self.info_queue_layout.addLayout(title_hl)
        
        self.artist_label = QLabel("Select a track to start listening"); self.artist_label.setObjectName("MutedText"); self.artist_label.setStyleSheet("font-size: 18px; color: #94A3B8;"); self.info_queue_layout.addWidget(self.artist_label)
        
        self.queue_header = QLabel("UP NEXT"); self.queue_header.setStyleSheet("font-weight: 800; font-size: 14px; letter-spacing: 2px; color: #00E5FF; margin-top: 10px;"); self.info_queue_layout.addWidget(self.queue_header)
        self.up_next_list = QListWidget(); self.up_next_list.setObjectName("QueueList"); self.up_next_list.setStyleSheet("QListWidget { background: transparent; } QListWidget::item { margin-bottom: 10px; }")
        self.info_queue_layout.addWidget(self.up_next_list)
        
        self.content_layout.addWidget(self.info_queue_widget)
        main_layout.addWidget(self.content_container, stretch=1)
        
        # Bottom Controls (Always visible in fixed position)
        self.controls_widget = QWidget(); self.controls_layout = QVBoxLayout(self.controls_widget); self.controls_layout.setSpacing(10)
        self.controls_layout.setContentsMargins(0, 20, 0, 0)
        
        progress_layout = QHBoxLayout(); self.current_time_label = QLabel("0:00"); self.current_time_label.setObjectName("MutedText")
        self.progress_slider = QSlider(Qt.Orientation.Horizontal); self.progress_slider.setObjectName("ProgressSlider"); self.progress_slider.setCursor(Qt.CursorShape.PointingHandCursor); self.progress_slider.sliderMoved.connect(self.seek_requested.emit)
        self.total_time_label = QLabel("0:00"); self.total_time_label.setObjectName("MutedText"); progress_layout.addWidget(self.current_time_label); progress_layout.addWidget(self.progress_slider); progress_layout.addWidget(self.total_time_label); self.controls_layout.addLayout(progress_layout)
        
        btns_layout = QHBoxLayout(); btns_layout.setAlignment(Qt.AlignmentFlag.AlignCenter); btns_layout.setSpacing(25)
        sub_btn_style = "QPushButton { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 25px; } QPushButton:hover { background: rgba(255, 255, 255, 0.1); border: 1px solid #00E5FF; }"
        self.prev_btn = QPushButton(); self.prev_btn.setIcon(get_icon(SVG_PREV, "#FFF")); self.prev_btn.setIconSize(QSize(24, 24)); self.prev_btn.setFixedSize(50, 50); self.prev_btn.setStyleSheet(sub_btn_style); self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.prev_btn.clicked.connect(self.prev_clicked.emit); btns_layout.addWidget(self.prev_btn)
        self.skip_back_btn = QPushButton(); self.skip_back_btn.setIcon(get_icon(SVG_BACKWARD_10, "#FFF")); self.skip_back_btn.setIconSize(QSize(24, 24)); self.skip_back_btn.setFixedSize(50, 50); self.skip_back_btn.setStyleSheet(sub_btn_style); self.skip_back_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.skip_back_btn.clicked.connect(self.skip_backward_clicked.emit); btns_layout.addWidget(self.skip_back_btn)
        self.play_btn = QPushButton(); self.play_btn.setIcon(get_icon(SVG_PLAY, "#000")); self.play_btn.setIconSize(QSize(36, 36)); self.play_btn.setFixedSize(80, 80); self.play_btn.setObjectName("PrimaryAction"); self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.play_btn.clicked.connect(self.play_pause_clicked.emit); btns_layout.addWidget(self.play_btn)
        self.skip_fwd_btn = QPushButton(); self.skip_fwd_btn.setIcon(get_icon(SVG_FORWARD_10, "#FFF")); self.skip_fwd_btn.setIconSize(QSize(24, 24)); self.skip_fwd_btn.setFixedSize(50, 50); self.skip_fwd_btn.setStyleSheet(sub_btn_style); self.skip_fwd_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.skip_fwd_btn.clicked.connect(self.skip_forward_clicked.emit); btns_layout.addWidget(self.skip_fwd_btn)
        self.next_btn = QPushButton(); self.next_btn.setIcon(get_icon(SVG_NEXT, "#FFF")); self.next_btn.setIconSize(QSize(24, 24)); self.next_btn.setFixedSize(50, 50); self.next_btn.setStyleSheet(sub_btn_style); self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.next_btn.clicked.connect(self.next_clicked.emit); btns_layout.addWidget(self.next_btn)
        self.controls_layout.addLayout(btns_layout); main_layout.addWidget(self.controls_widget)
        
        layout.addWidget(self.main_container)
        self.is_mobile = False

    def setup_animations(self):
        # Background Pulse Animation
        self.bg_anim = QVariantAnimation()
        self.bg_anim.setStartValue(1.0); self.bg_anim.setEndValue(1.5)
        self.bg_anim.setDuration(12000); self.bg_anim.setDirection(QVariantAnimation.Direction.Forward)
        self.bg_anim.setLoopCount(-1); self.bg_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.bg_anim.valueChanged.connect(self.on_bg_pulse)
        self.bg_anim.start()
        self.current_pulse_val = 1.0

    def on_bg_pulse(self, val):
        self.current_pulse_val = val
        self.update_bg_stylesheet()

    def update_bg_stylesheet(self):
        hex_color = self.current_base_color.name()
        # Create a "Glowing Liquid" radial gradient
        self.main_container.setStyleSheet(f"""
            QFrame#NowPlayingContainer {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:{self.current_pulse_val}, fx:0.5, fy:0.5, 
                    stop:0 {hex_color}, stop:1 #090B1E);
            }}
        """)

    def set_ambient_color(self, color):
        self.current_base_color = color.darker(150)
        self.update_bg_stylesheet()

    def toggle_mode(self):
        if self.art_lyrics_stack.currentIndex() == 0: self.art_lyrics_stack.setCurrentIndex(1); self.mode_toggle.setText("Album Art 💿")
        else: self.art_lyrics_stack.setCurrentIndex(0); self.mode_toggle.setText("Lyrics ✨")

    def update_lyrics(self, text):
        if not text or text.strip() == "": self.lyrics_label.setText("\n\n\nNo lyrics found for this track. 🎵")
        else: self.lyrics_label.setText(text)

    def update_info(self, video, pixmap=None):
        self.current_video = video # Store for the '+' button signal
        self.title_label.setText(video.get('title', 'Unknown'))
        title = video.get('title', ''); self.artist_label.setText(title.split(' - ')[0] if ' - ' in title else "YouTube Audio")
        if pixmap: self.visualizer.set_pixmap(pixmap)
        else: self.visualizer.set_pixmap(None)
        duration = video.get('duration')
        if isinstance(duration, (int, float)):
            m, s = divmod(int(duration), 60); self.total_time_label.setText(f"{m}:{s:02d}"); self.progress_slider.setRange(0, int(duration * 1000))
        self.lyrics_label.setText("Fetching magical words for you...")

    def update_play_btn(self, is_playing):
        icon = get_icon(SVG_PAUSE if is_playing else SVG_PLAY, "#000"); self.play_btn.setIcon(icon); self.visualizer.set_playing(is_playing); self.bar_vis.set_playing(is_playing)

    def resizeEvent(self, event):
        """Responsive layout shift for Spotify-grade mobile experience."""
        w = event.size().width()
        is_mobile = w < 720
        
        if is_mobile != self.is_mobile:
            self.is_mobile = is_mobile
            # Re-architecture content layout
            old_l = self.content_container.layout()
            if old_l:
                old_l.removeWidget(self.art_lyrics_stack)
                old_l.removeWidget(self.info_queue_widget)
                # Cleanup old layout manually (PyQt requires this for clean reconstruction)
                from PyQt6 import sip; sip.delete(old_l)
            
            if is_mobile:
                new_l = QVBoxLayout(self.content_container)
                new_l.setContentsMargins(0, 10, 0, 0); new_l.setSpacing(20)
                new_l.addWidget(self.art_lyrics_stack, alignment=Qt.AlignmentFlag.AlignCenter)
                new_l.addWidget(self.info_queue_widget)
                self.queue_header.hide(); self.up_next_list.hide()
                self.visualizer.set_size(min(w - 100, 280))
                self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFD700;")
                self.main_container.layout().setContentsMargins(20, 10, 20, 20)
            else:
                new_l = QHBoxLayout(self.content_container)
                new_l.setContentsMargins(0, 0, 0, 0); new_l.setSpacing(60)
                new_l.addWidget(self.art_lyrics_stack, stretch=1)
                new_l.addWidget(self.info_queue_widget, stretch=1)
                self.queue_header.show(); self.up_next_list.show()
                self.visualizer.set_size(380)
                self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                self.artist_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                self.title_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #FFD700;")
                self.main_container.layout().setContentsMargins(40, 20, 40, 40)
        
        super().resizeEvent(event)

    def update_progress(self, current_ms):
        self.progress_slider.setValue(current_ms); m, s = divmod(current_ms // 1000, 60); self.current_time_label.setText(f"{m}:{s:02d}")
