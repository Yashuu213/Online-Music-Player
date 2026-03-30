# ⚡ Premium Pikachu Modern Design System
# Color Palette:
# - Background: Deep Space Navy (#090B1E, #0F1229)
# - Primary: Electric Pikachu Yellow (#FFD700)
# - Secondary: Neon Cyan (#00E5FF)
# - Surfaces: Translucent Glass (rgba(255, 255, 255, 0.05))
# - Text: Pure White (#FFFFFF), Muted Gray (#94A3B8)

PREMIUM_PIKACHU_THEME = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
        stop:0 #090B1E, stop:0.5 #0F1229, stop:1 #050714);
}

/* --- Scrollbars (Sleek & Minimal) --- */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 215, 0, 0.2);
    min-height: 30px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 215, 0, 0.5);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 6px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: rgba(0, 229, 255, 0.2);
    min-width: 30px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(0, 229, 255, 0.5);
}

/* --- Sidebar Styling --- */
#Sidebar {
    background: rgba(255, 255, 255, 0.03);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

#SidebarItem {
    background: transparent;
    color: #94A3B8;
    border-radius: 12px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 600;
    text-align: left;
    border: 1px solid transparent;
}
#SidebarItem:hover {
    background: rgba(255, 215, 0, 0.05);
    color: #FFD700;
}
#SidebarItem[active="true"] {
    background: rgba(255, 215, 0, 0.1);
    color: #FFD700;
    border: 1px solid rgba(255, 215, 0, 0.2);
}

/* --- Dashboard Section Headers --- */
#SectionHeader {
    font-size: 22px;
    font-weight: 900;
    color: #FFFFFF;
    margin-bottom: 5px;
    letter-spacing: 0.5px;
    border-left: 4px solid #FFD700;
    padding-left: 15px;
}

/* --- Search Result Headers --- */
QLabel#ResultHeader {
    font-size: 12px;
    font-weight: 800;
    color: #00E5FF;
    letter-spacing: 2px;
    margin-top: 20px;
    margin-bottom: 10px;
    padding-left: 5px;
}

/* --- Inputs (Glass Search) --- */
QLineEdit#SearchBar {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 22px;
    padding: 10px 25px;
    color: #FFFFFF;
    font-size: 15px;
}
QLineEdit#SearchBar:focus {
    border: 1px solid #FFD700;
    background: rgba(255, 255, 255, 0.1);
}

/* --- Glass Panels (Cards) --- */
#GlassPanel {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
}
#GlassPanel:hover {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 215, 0, 0.3);
}

/* --- Primary Buttons --- */
QPushButton#PrimaryAction {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD700, stop:1 #FFB000);
    color: #000000;
    font-weight: 800;
    border-radius: 20px;
    padding: 10px 24px;
    border: none;
}
QPushButton#PrimaryAction:hover {
    background: #FFEC5C;
}
QPushButton#PrimaryAction:pressed {
    background: #D4B600;
}

/* --- Secondary Action (Translucent) --- */
QPushButton#SecondaryAction {
    background: rgba(255, 255, 255, 0.05);
    color: #FFFFFF;
    border-radius: 12px;
    padding: 8px 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
QPushButton#SecondaryAction:hover {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* --- Labels --- */
QLabel {
    color: #FFFFFF;
}
QLabel#MutedText {
    color: #94A3B8;
    font-size: 13px;
}
QLabel#ArtistTitle {
    color: #FFFFFF;
    font-weight: 700;
    font-size: 14px;
}

/* --- Simple List widgets --- */
QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    margin-bottom: 8px;
    padding: 2px;
}

/* --- Tab-like container replacement --- */
#ContainerPanel {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 20px;
}

/* --- Progress Slider --- */
QSlider::groove:horizontal {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #FFD700;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FFD700, stop:1 #00E5FF);
    border-radius: 2px;
}
"""
