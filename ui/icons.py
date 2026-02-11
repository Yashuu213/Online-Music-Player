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

SVG_CHEVRON_LEFT = """
<svg viewBox="0 0 24 24" fill="white">
  <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
</svg>
"""

def get_icon(svg_data, color="#FFFFFF"):
    # Render SVG to Pixmap
    renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    # Simple recolor if needed (SVG fill is white by default)
    if color != "#FFFFFF":
        mask = pixmap.createMaskFromColor(Qt.GlobalColor.transparent, Qt.MaskMode.MaskInColor)
        pixmap.fill(QColor(color))
        pixmap.setMask(mask)
        
    return QIcon(pixmap)
