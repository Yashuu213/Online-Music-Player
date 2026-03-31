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
        main_layout.setContentsMargins(0, 0, 0, 0) # Managed by inner containers
        main_layout.setSpacing(0)
        
        # 1. Top Bar Wrapper (Fixed)
        self.top_wrapper = QWidget(); self.top_wrapper_l = QVBoxLayout(self.top_wrapper)
        self.top_wrapper_l.setContentsMargins(40, 20, 40, 10)
        
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
        
        self.top_wrapper_l.addLayout(top_bar)
        main_layout.addWidget(self.top_wrapper)
        
        # 2. MIDDLE SCROLL AREA (The Core)
        self.middle_scroll = QScrollArea()
        self.middle_scroll.setWidgetResizable(True)
        self.middle_scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.middle_scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.middle_scroll, stretch=1)
        
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
        
        # Center Column: Pure Song Info (Huge Space Utilization)
        self.info_center_widget = QWidget()
        self.info_center_layout = QVBoxLayout(self.info_center_widget); self.info_center_layout.setSpacing(15)
        self.info_center_layout.setContentsMargins(0, 0, 0, 0)
        self.info_center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title_label = QLabel("No Song Playing"); self.title_label.setStyleSheet("font-size: 48px; font-weight: 900; color: #FFD700; text-align: center;"); self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.info_center_layout.addStretch(1) # Top Spacer
        self.info_center_layout.addWidget(self.title_label)
        
        self.artist_label = QLabel("Select a track to start listening"); self.artist_label.setObjectName("MutedText"); self.artist_label.setStyleSheet("font-size: 24px; color: #94A3B8;"); self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.info_center_layout.addWidget(self.artist_label)
        self.info_center_layout.addStretch(1) # Bottom Spacer
        
        # Right Column: Pure Queue (Filling the side gap)
        self.queue_widget = QWidget(); self.queue_layout = QVBoxLayout(self.queue_widget); self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_header = QLabel("UP NEXT"); self.queue_header.setStyleSheet("font-weight: 800; font-size: 14px; letter-spacing: 2px; color: #00E5FF; margin-top: 10px;"); self.queue_layout.addWidget(self.queue_header)
        self.up_next_list = QListWidget(); self.up_next_list.setObjectName("QueueList"); self.up_next_list.setStyleSheet("QListWidget { background: transparent; } QListWidget::item { margin-bottom: 10px; }")
        self.queue_layout.addWidget(self.up_next_list)
        
        self.content_layout.addWidget(self.info_center_widget) # Added for mobile initially
        self.scroll_layout.addWidget(self.content_container)
        
        # 3. Bottom Controls Wrapper (Fixed at bottom)
        self.controls_wrapper = QWidget()
        self.controls_wrapper.setObjectName("ControlsWrapper")
        self.controls_wrapper_l = QVBoxLayout(self.controls_wrapper)
        self.controls_wrapper_l.setContentsMargins(40, 0, 40, 20)
        
        progress_layout = QHBoxLayout(); self.current_time_label = QLabel("0:00"); self.current_time_label.setObjectName("MutedText")
        self.controls_widget = QWidget(); self.controls_layout = QVBoxLayout(self.controls_widget); self.controls_layout.setSpacing(10)
        self.controls_layout.setContentsMargins(0, 20, 0, 0)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal); self.progress_slider.setObjectName("ProgressSlider"); self.progress_slider.setCursor(Qt.CursorShape.PointingHandCursor); self.progress_slider.sliderMoved.connect(self.seek_requested.emit)
        self.total_time_label = QLabel("0:00"); self.total_time_label.setObjectName("MutedText"); progress_layout.addWidget(self.current_time_label); progress_layout.addWidget(self.progress_slider); progress_layout.addWidget(self.total_time_label); self.controls_layout.addLayout(progress_layout)
        
        btns_layout = QHBoxLayout(); btns_layout.setAlignment(Qt.AlignmentFlag.AlignCenter); btns_layout.setSpacing(25)
        sub_btn_style = "QPushButton { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 25px; } QPushButton:hover { background: rgba(255, 255, 255, 0.1); border: 1px solid #00E5FF; }"
        self.prev_btn = QPushButton(); self.prev_btn.setIcon(get_icon(SVG_PREV, "#FFF")); self.prev_btn.setIconSize(QSize(24, 24)); self.prev_btn.setFixedSize(50, 50); self.prev_btn.setStyleSheet(sub_btn_style); self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.prev_btn.clicked.connect(self.prev_clicked.emit); btns_layout.addWidget(self.prev_btn)
        self.skip_back_btn = QPushButton(); self.skip_back_btn.setIcon(get_icon(SVG_BACKWARD_10, "#FFF")); self.skip_back_btn.setIconSize(QSize(24, 24)); self.skip_back_btn.setFixedSize(50, 50); self.skip_back_btn.setStyleSheet(sub_btn_style); self.skip_back_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.skip_back_btn.clicked.connect(self.skip_backward_clicked.emit); btns_layout.addWidget(self.skip_back_btn)
        self.play_btn = QPushButton(); self.play_btn.setIcon(get_icon(SVG_PLAY, "#000")); self.play_btn.setIconSize(QSize(36, 36)); self.play_btn.setFixedSize(80, 80); self.play_btn.setObjectName("PrimaryAction"); self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.play_btn.clicked.connect(self.play_pause_clicked.emit); btns_layout.addWidget(self.play_btn)
        self.skip_fwd_btn = QPushButton(); self.skip_fwd_btn.setIcon(get_icon(SVG_FORWARD_10, "#FFF")); self.skip_fwd_btn.setIconSize(QSize(24, 24)); self.skip_fwd_btn.setFixedSize(50, 50); self.skip_fwd_btn.setStyleSheet(sub_btn_style); self.skip_fwd_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.skip_fwd_btn.clicked.connect(self.skip_forward_clicked.emit); btns_layout.addWidget(self.skip_fwd_btn)
        self.next_btn = QPushButton(); self.next_btn.setIcon(get_icon(SVG_NEXT, "#FFF")); self.next_btn.setIconSize(QSize(24, 24)); self.next_btn.setFixedSize(50, 50); self.next_btn.setStyleSheet(sub_btn_style); self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor); self.next_btn.clicked.connect(self.next_clicked.emit); btns_layout.addWidget(self.next_btn)
        self.controls_layout.addLayout(btns_layout)
        
        self.controls_layout.addLayout(btns_layout)
        self.controls_wrapper_l.addWidget(self.controls_widget)
        main_layout.addWidget(self.controls_wrapper)
        
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
        # Full-Screen Immersive Radial Glow
        self.main_container.setStyleSheet(f"""
            QFrame#NowPlayingContainer {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, 
                    stop:0 {hex_color}, stop:1 #05070A);
            }}
        """)

    def set_ambient_color(self, color):
        self.current_base_color = color.darker(150)
        self.update_bg_stylesheet()

    def toggle_mode(self):
        if self.art_lyrics_stack.currentIndex() == 0: 
            self.art_lyrics_stack.setCurrentIndex(1)
            self.mode_toggle.setChecked(True)
        else: 
            self.art_lyrics_stack.setCurrentIndex(0)
            self.mode_toggle.setChecked(False)

    def update_lyrics(self, text):
        if not text or text.strip() == "": self.lyrics_label.setText("\n\n\nNo lyrics found for this track. 🎵")
        else: self.lyrics_label.setText(text)

    def update_info(self, video, pixmap=None):
        self.current_video = video # Store for the '+' button signal
        title = video.get('title', 'Unknown')
        self.title_label.setText(title)
        # Clean artist name - Use uploader but filter out generic YouTube names
        artist = str(video.get('uploader', 'Pikachu Music'))
        if "youtube" in artist.lower(): artist = "Pikachu Music"
        self.artist_label.setText(artist)
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
            # Re-architecture content layout with ZERO VOID Tri-Column logic
            old_l = self.content_container.layout()
            if old_l:
                old_l.removeWidget(self.art_lyrics_stack)
                old_l.removeWidget(self.info_center_widget)
                old_l.removeWidget(self.queue_widget)
                # Cleanup old layout manually (PyQt requires this for clean reconstruction)
                from PyQt6 import sip; sip.delete(old_l)
            
            if is_mobile:
                new_l = QVBoxLayout(self.content_container)
                new_l.setContentsMargins(40, 10, 40, 0); new_l.setSpacing(20)
                new_l.addWidget(self.art_lyrics_stack, alignment=Qt.AlignmentFlag.AlignCenter)
                new_l.addWidget(self.info_center_widget)
                new_l.addWidget(self.queue_widget)
                self.queue_header.show(); self.up_next_list.show()
                self.up_next_list.setMinimumHeight(400)
                self.visualizer.set_size(min(w - 100, 280))
                self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.title_label.setStyleSheet("font-size: 24px; font-weight: 800; color: #FFD700;")
                self.controls_wrapper_l.setContentsMargins(20, 0, 20, 20)
                self.top_wrapper_l.setContentsMargins(20, 10, 20, 0)
            else:
                new_l = QHBoxLayout(self.content_container)
                new_l.setContentsMargins(40, 0, 40, 0); new_l.setSpacing(50) # Reduced side margins for MORE SPACE
                
                # Column 1: Art (Left) - Flush against side
                new_l.addWidget(self.art_lyrics_stack, stretch=1)
                
                # Column 2: THE CORE HERO INFO (MAX SPACE UTILIZATION) - 4x Stretch for CENTER DOMINANCE
                new_l.addWidget(self.info_center_widget, stretch=4)
                
                # Column 3: THE QUEUE (Right Flush filling the void) - 1x Stretch
                new_l.addWidget(self.queue_widget, stretch=1)
                
                # Final Typography Polish for Full Space
                self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.title_label.setStyleSheet("font-size: 52px; font-weight: 900; color: #FFD700; text-align: center; line-height: 1.2;") # Monster 52px Typography
                
                self.queue_header.show(); self.up_next_list.show()
                self.up_next_list.setMinimumHeight(350)
                self.up_next_list.setFixedWidth(min(w // 4, 400)) 
                self.visualizer.set_size(min(w // 3, 500)) # Larger Art too!
                
                self.controls_wrapper_l.setContentsMargins(40, 0, 40, 40)
                self.top_wrapper_l.setContentsMargins(40, 10, 40, 10)
        
        super().resizeEvent(event)

    def update_progress(self, current_ms):
        self.progress_slider.setValue(current_ms); m, s = divmod(current_ms // 1000, 60); self.current_time_label.setText(f"{m}:{s:02d}")
