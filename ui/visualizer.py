from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QRadialGradient, QPainterPath, QPixmap
import math

class RotatingAlbumArt(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.pulse = 0.0
        self.is_playing = False
        self.pixmap = None
        
        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.setInterval(50) # 20 FPS
        
        self.setFixedSize(300, 300)

    def set_size(self, size):
        self.setFixedSize(size, size)
        self.update()

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def set_playing(self, playing):
        self.is_playing = playing
        if playing:
            self.timer.start()
        else:
            self.timer.stop()
            self.angle = 0
            self.pulse = 0.0
        self.update()

    def animate(self):
        self.angle = (self.angle + 2) % 360
        # Pulse between 0.0 and 1.0 using sine wave
        self.pulse = (math.sin(math.radians(self.angle * 2)) + 1) / 2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        center = rect.center()
        # Default radius
        base_radius = min(rect.width(), rect.height()) / 2 - 20
        
        # Draw "Wave" Ring (Outer Glow)
        if self.is_playing:
            # Vary radius size with pulse (expand and contract)
            wave_radius = base_radius + 10 + (self.pulse * 10) 
            
            gradient = QRadialGradient(QPointF(center), wave_radius)
            # Rotating colors based on angle
            c1 = QColor("#FFD700")  # Pikachu Yellow
            c2 = QColor("#00E5FF")  # Electric Cyan
            
            gradient.setColorAt(0.7, Qt.GlobalColor.transparent)
            gradient.setColorAt(0.9, c1 if (self.angle // 45) % 2 == 0 else c2)
            gradient.setColorAt(1.0, Qt.GlobalColor.transparent)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Rotate painter for the ring effect
            painter.translate(QPointF(center))
            painter.rotate(self.angle)
            painter.translate(-QPointF(center))
            
            painter.drawEllipse(QPointF(center), wave_radius, wave_radius)
            
            # Reset Transform
            painter.resetTransform()

        # Draw Circular Album Art
        path = QPainterPath()
        path.addEllipse(QPointF(center), base_radius, base_radius)
        painter.setClipPath(path)
        
        if self.pixmap:
            # Scale pixmap to cover the circle
            scaled = self.pixmap.scaled(
                int(base_radius * 2), int(base_radius * 2),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Center the pixmap
            x = center.x() - scaled.width() / 2
            y = center.y() - scaled.height() / 2
            painter.drawPixmap(int(x), int(y), scaled)
        else:
            # Placeholder
            painter.setBrush(QColor("#1E1E1E"))
            painter.drawRect(rect)
            
        # Draw Border Ring
        painter.setClipping(False)
        pen = QPen(QColor("#333"), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(center), base_radius, base_radius)

import random

class BarVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bar_count = 40
        self.values = [0.0] * self.bar_count
        self.is_playing = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.setInterval(50)
        
        self.setFixedHeight(60) 

    def set_size(self, size):
        self.setFixedWidth(size)
        self.update()

    def set_playing(self, playing):
        self.is_playing = playing
        if playing:
            self.timer.start()
        else:
            self.timer.stop()
            self.values = [0.0] * self.bar_count
            self.update()

    def animate(self):
        # Simulate spectrum data
        for i in range(self.bar_count):
            # value based on sine wave + random noise for "beat" look
            target = (math.sin(self.timer.remainingTime() * 0.01 + i * 0.2) + 1) / 2
            target *= random.uniform(0.5, 1.0)
            
            # Smooth transition
            self.values[i] = self.values[i] * 0.6 + target * 0.4
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        bar_width = w / self.bar_count
        
        c1 = QColor("#FFD700")
        
        painter.setBrush(QBrush(c1))
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i, val in enumerate(self.values):
            bar_h = val * h * 0.8 # Max 80% height
            x = i * bar_width
            y = h - bar_h 
            
            # Draw bar with rounded top
            painter.drawRoundedRect(QRectF(x + 1, y, bar_width - 2, bar_h), 2, 2)

