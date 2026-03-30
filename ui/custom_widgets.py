from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QPainter, QBrush, QPixmap, QColor
from ui.icons import get_icon, SVG_ADD, SVG_LIBRARY

class SongItemWidget(QWidget):
    """Horizontal list item for search results and history."""
    add_to_playlist_clicked = pyqtSignal(object)
    
    def __init__(self, video_data):
        super().__init__()
        self.video_data = video_data
        self.init_ui()
        
    def init_ui(self):
        self.setObjectName("SongItem")
        self.setStyleSheet("""
            #SongItem { 
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 12px;
            }
            #SongItem:hover { 
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(255, 215, 0, 0.2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(15)
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(56, 56)
        self.thumb_label.setStyleSheet("background: #000; border-radius: 8px;")
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumb_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.title_label = QLabel(self.video_data.get('title', 'Unknown'))
        self.title_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #FFF;")
        info_layout.addWidget(self.title_label)
        
        duration = self.video_data.get('duration')
        dur_str = f"{int(duration)//60}:{int(duration)%60:02d}" if isinstance(duration, (int, float)) else str(duration)
        
        self.dur_label = QLabel(dur_str)
        self.dur_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        info_layout.addWidget(self.dur_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Add Button
        self.add_btn = QPushButton()
        self.add_btn.setIcon(get_icon(SVG_ADD, "#94A3B8"))
        self.add_btn.setIconSize(QSize(18, 18))
        self.add_btn.setFixedSize(32, 32)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("""
            QPushButton { background: transparent; border-radius: 16px; }
            QPushButton:hover { background: rgba(255, 215, 0, 0.1); border: 1px solid rgba(255, 215, 0, 0.3); }
        """)
        self.add_btn.clicked.connect(lambda: self.add_to_playlist_clicked.emit(self.video_data))
        layout.addWidget(self.add_btn)

    def set_thumbnail(self, pixmap):
        try:
            scaled = pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
        except: pass

class SongCardWidget(QFrame):
    clicked = pyqtSignal(object)
    def __init__(self, video_data):
        super().__init__()
        self.video_data = video_data; self.setFixedSize(160, 220); self.setObjectName("GlassPanel"); self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 12); layout.setSpacing(10)
        self.thumb_label = QLabel(); self.thumb_label.setFixedSize(140, 140); self.thumb_label.setStyleSheet("background: #111; border-radius: 12px;"); self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(self.thumb_label)
        self.title_label = QLabel(self.video_data.get('title', 'Unknown')); self.title_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #FFF;"); self.title_label.setWordWrap(True); self.title_label.setMaximumHeight(40); layout.addWidget(self.title_label)
        self.muted_label = QLabel("Click to Play"); self.muted_label.setObjectName("MutedText"); layout.addWidget(self.muted_label); layout.addStretch()
    def set_thumbnail(self, pixmap):
        try:
            scaled = pixmap.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)
        except: pass
    def mousePressEvent(self, event): self.clicked.emit(self.video_data); super().mousePressEvent(event)

class ArtistCardWidget(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self, name, image_url=None):
        super().__init__(); self.name = name; self.image_url = image_url; self.setFixedSize(140, 180); self.setObjectName("GlassPanel"); self.setStyleSheet("#GlassPanel { background: transparent; border: none; } #GlassPanel:hover { background: rgba(255, 255, 255, 0.05); border-radius: 15px; }"); self.setCursor(Qt.CursorShape.PointingHandCursor); self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 10, 10, 10); layout.setSpacing(12); layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label = QLabel(); self.img_label.setFixedSize(110, 110); self.img_label.setStyleSheet("background: #1A1A1A; border-radius: 55px; border: 2px solid rgba(255, 215, 0, 0.3);"); self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.img_label.setText(self.name[0]); self.img_label.setStyleSheet(self.img_label.styleSheet() + "font-size: 40px; font-weight: bold; color: #FFF;"); layout.addWidget(self.img_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.name_label = QLabel(self.name); self.name_label.setObjectName("ArtistTitle"); self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(self.name_label)
        self.muted_label = QLabel("Artist"); self.muted_label.setObjectName("MutedText"); self.muted_label.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(self.muted_label)
    def set_image(self, pixmap):
        try:
            size = 110; rounded = QPixmap(size, size); rounded.fill(Qt.GlobalColor.transparent); painter = QPainter(rounded); painter.setRenderHint(QPainter.RenderHint.Antialiasing); painter.setBrush(QBrush(pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(0, 0, size, size); painter.end(); self.img_label.setPixmap(rounded); self.img_label.setText("") 
        except: pass
    def mousePressEvent(self, event): self.clicked.emit(self.name); super().mousePressEvent(event)

class PlaylistCardWidget(QFrame):
    """Modern Grid Card for Playlists."""
    clicked = pyqtSignal(str) # playlist name
    
    def __init__(self, name, count=0):
        super().__init__()
        self.name = name; self.count = count
        self.setFixedSize(180, 220); self.setObjectName("GlassPanel"); self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(12)
        
        # Modern Playlist Icon (Music Library)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(150, 120)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # We use a gradient background for the "Playlist Cover" look
        self.icon_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #0F172A);
            border-radius: 16px;
            border: 1px solid rgba(255, 215, 0, 0.1);
        """)
        self.icon_label.setPixmap(get_icon(SVG_LIBRARY, "#FFD700").pixmap(64, 64))
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet("font-weight: 800; font-size: 15px; color: #FFF;")
        self.name_label.setWordWrap(True); self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)
        
        self.count_label = QLabel(f"{self.count} Songs")
        self.count_label.setStyleSheet("color: #00E5FF; font-weight: 700; font-size: 12px; letter-spacing: 1px;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)
        
        layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        super().mousePressEvent(event)
