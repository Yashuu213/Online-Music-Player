from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtSvg import QSvgRenderer

# Simple SVG Paths
SVG_PLAY = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M8 5v14l11-7z"/>
</svg>
"""

SVG_PAUSE = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
</svg>
"""

SVG_STOP = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M6 6h12v12H6z"/>
</svg>
"""

SVG_ADD = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
</svg>
"""

SVG_SEARCH = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
</svg>
"""

SVG_NEXT = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
</svg>
"""

SVG_PREV = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
</svg>
"""

SVG_BACKWARD_10 = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M12 5V19L3 12L12 5ZM13 5V19L22 12L13 5Z" opacity="0.5"/>
  <path d="M10 10H9V14H10V10Z M13 10H12V14H13V10Z" fill="white"/>
  <path d="M8 11V14H7V11H6V10H8V11Z" fill="white"/>
</svg>
"""

SVG_FORWARD_10 = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M12 5V19L21 12L12 5ZM11 5V19L2 12L11 5Z" opacity="0.5"/>
  <path d="M14 10H13V14H14V10Z M17 10H16V14H17V10Z" fill="white"/>
  <path d="M12 11V14H11V11H10V10H12V11Z" fill="white"/>
</svg>
"""

SVG_CHEVRON_LEFT = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
</svg>
"""

SVG_HOME = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
</svg>
"""

SVG_LIBRARY = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9H9V9h10v2zm-4 4H9v-2h6v2zm4-8H9V5h10v2z"/>
</svg>
"""

SVG_TRENDING = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M13.5 2C13.5 2 13.5 2 13.5 2C12.83 2 12.21 2.3 11.83 2.81C10.5 4.67 9.83 6.64 9.5 8.16C8.67 11.5 9.5 13.5 9.5 13.5C9.5 13.5 7.5 11.5 7.5 8.5C7.5 7.59 7.03 6.78 6.33 6.31C5.63 5.84 4.75 5.75 3.97 6.06C2.17 6.75 1 8.5 1 10.5C1 15.19 4.81 19 9.5 19C10.5 19 11.5 18.8 12.42 18.45C11.5 17.5 11 16.27 11 14.92C11 11.36 13.5 8.86 13.5 4.5V2ZM13.5 7C13.5 10.86 11 12.86 11 14.92C11 16.5 12.25 17.75 13.84 17.75C15.42 17.75 16.67 16.5 16.67 14.92C16.67 13.83 16.08 12.89 15.17 12.33C14.41 11.87 13.78 11.16 13.78 10.15C13.78 8.87 14.65 7.82 15.82 7.53C17.03 7.23 18.25 7.78 19.04 8.71C20.25 10.14 21 11.96 21 14C21 18.42 17.42 22 13 22C8.58 22 5 18.42 5 14C5 12.92 5.22 11.89 5.61 10.96C5.61 10.96 5.61 10.96 5.61 10.96C6.18 11.5 7 11.5 7.5 11.5C7.5 11.5 7.5 11.5 7.5 11.5C7.5 12.33 8.17 13 9 13C9.83 13 10.5 12.33 10.5 11.5C10.5 10.67 9.83 10 9 10C8.17 10 7.5 10.67 7.5 11.5C7.5 11.5 7.5 11.5 7.5 11.5C7.5 10.5 7.5 9.5 7.85 8.5C8.08 7.81 8.5 7.15 9.07 6.64C9.55 6.2 10.22 6 10.92 6H11V4.5C11 3.12 12.12 2 13.5 2Z"/>
</svg>
"""
SVG_DELETE = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
</svg>
"""

SVG_SHUFFLE = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.45 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/>
</svg>
"""

SVG_REPEAT = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z"/>
</svg>
"""

def get_icon(svg_data, color="#FFFFFF"):
    renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    if color != "#FFFFFF":
        mask = pixmap.createMaskFromColor(Qt.GlobalColor.transparent, Qt.MaskMode.MaskInColor)
        pixmap.fill(QColor(color))
        pixmap.setMask(mask)
    return QIcon(pixmap)
