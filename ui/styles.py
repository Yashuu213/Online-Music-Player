# Modern Glassmorphism Premium Theme

# Color Palette
# Backgrounds: Deep space/night sky gradients
# Accents: Electric Purple (#BB86FC) to Neon Blue (#03DAC6)
# Text: Pure White (#FFFFFF) and secondary Gray (#B0B0B0)

PREMIUM_THEME = """
QMainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
}

/* --- Scrollbars --- */
QScrollBar:vertical {
    border: none;
    background: rgba(0, 0, 0, 0.1);
    width: 8px;
    margin: 0px 0px 0px 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: rgba(187, 134, 252, 0.3);
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(187, 134, 252, 0.6);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: rgba(0, 0, 0, 0.1);
    height: 8px;
    margin: 0px 0px 0px 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: rgba(187, 134, 252, 0.3);
    min-width: 20px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(187, 134, 252, 0.6);
}

/* --- Tabs --- */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.05);
    background: rgba(0, 0, 0, 0.2);
    border-radius: 12px;
    margin-top: -1px; /* seamless look */
}

QTabBar::tab {
    background: transparent;
    color: #B0B0B0;
    padding: 10px 25px;
    font-size: 14px;
    font-weight: 600;
    border-bottom: 3px solid transparent;
    margin-right: 5px;
}

QTabBar::tab:hover {
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.05);
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    color: #BB86FC;
    border-bottom: 3px solid #BB86FC;
    background: rgba(187, 134, 252, 0.05);
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

/* --- LineEdits (Search) --- */
QLineEdit {
    background-color: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 8px 20px;
    color: #FFFFFF;
    font-size: 14px;
    selection-background-color: #BB86FC;
}
QLineEdit:focus {
    border: 2px solid #BB86FC;
    background-color: rgba(255, 255, 255, 0.1);
}

/* --- List Widgets --- */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 5px;
    margin: 3px 10px;
    border-radius: 10px;
    border: 1px solid transparent;
}
QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
QListWidget::item:selected {
    background-color: rgba(187, 134, 252, 0.15);
    border: 1px solid #BB86FC;
}

/* --- Buttons --- */
QPushButton {
    background-color: rgba(255, 255, 255, 0.05);
    color: #FFFFFF;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
}
QPushButton:pressed {
    background-color: rgba(187, 134, 252, 0.2);
}

/* --- Primary Action Button (Gradient) --- */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #BB86FC, stop:1 #985EFF);
    border: none;
    color: #000000;
}
QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
        stop:0 #C495FD, stop:1 #A673FF);
    margin-top: -1px; /* subtle lift */
}

/* --- Sliders --- */
QSlider::groove:horizontal {
    border: 1px solid rgba(255, 255, 255, 0.1);
    height: 6px;
    background: rgba(0, 0, 0, 0.3);
    margin: 2px 0;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #BB86FC;
    border: 2px solid #FFFFFF;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    color: #BB86FC;
    border-bottom: 2px solid #BB86FC;
}

QTabBar::tab:hover {
    color: #FFF;
}
"""
