from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.icons import get_icon, SVG_ADD

class SongItemWidget(QWidget):
    add_to_playlist_clicked = pyqtSignal(object)
    
    def __init__(self, video_data):
        super().__init__()
        self.video_data = video_data
        self.init_ui()
        
    def init_ui(self):
        # Premium Card Layout
        self.setStyleSheet("""
            QWidget { 
                background-color: transparent; 
            }
            QLabel { 
                color: #FFFFFF; 
                border: none; 
                background: transparent;
            }
            QPushButton { 
                border: none; 
                background: rgba(187, 134, 252, 0.1); 
                border-radius: 16px;
                border: 1px solid rgba(187, 134, 252, 0.3);
            }
            QPushButton:hover { 
                background: #BB86FC;
                color: black;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(20)
        
        # Thumbnail with better styling
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(70, 70)
        self.thumb_label.setStyleSheet("""
            background: #111;
            border-radius: 10px;
            border: 1px solid #333;
        """)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumb_label)
        
        # Info Container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Title
        self.title_label = QLabel(self.video_data.get('title', 'Unknown'))
        self.title_label.setStyleSheet("font-weight: 700; font-size: 15px; color: #FFFFFF;")
        self.title_label.setWordWrap(False)
        info_layout.addWidget(self.title_label)
        
        # Duration / Sub-info
        duration = self.video_data.get('duration')
        if isinstance(duration, (int, float)):
             m, s = divmod(int(duration), 60)
             dur_str = f"{m}:{s:02d}"
        else:
             dur_str = str(duration) if duration else "N/A"
             
        self.dur_label = QLabel(dur_str)
        self.dur_label.setStyleSheet("color: #BB86FC; font-size: 13px; font-weight: 500;")
        info_layout.addWidget(self.dur_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Add Button - Perfectly Centered
        self.add_btn = QPushButton()
        self.add_btn.setIcon(get_icon(SVG_ADD, "#FFFFFF"))
        self.add_btn.setIconSize(QSize(20, 20))
        self.add_btn.setFixedSize(36, 36)
        self.add_btn.setToolTip("Add to Playlist")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.on_add_click)
        layout.addWidget(self.add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def set_thumbnail(self, pixmap):
        try:
            # High quality scaling for premium feel
            scaled = pixmap.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
            
            # center crop effect (simple approximation by re-aligning)
            # For now, just setting pixmap is fine as aspect ratio is usually 16:9 
            # and we are putting it in a square box, but 'KeepAspectRatioByExpanding' fills the box.
        except RuntimeError:
            pass

    def on_add_click(self):
        self.add_to_playlist_clicked.emit(self.video_data)
