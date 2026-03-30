from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor
from ui.icons import get_icon, SVG_ADD

class ModernInputDialog(QDialog):
    def __init__(self, title, label, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 220)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui(title, label)
        
    def init_ui(self, title_text, label_text):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.bg_frame = QGraphicsDropShadowEffect()
        self.bg_frame.setBlurRadius(20)
        self.bg_frame.setColor(QColor(0, 0, 0, 150))
        self.bg_frame.setOffset(0, 0)
        
        from PyQt6.QtWidgets import QFrame
        container = QFrame()
        container.setObjectName("ModalContainer")
        container.setGraphicsEffect(self.bg_frame)
        container.setStyleSheet("""
            QFrame#ModalContainer {
                background: #0F1229;
                border: 2px solid #00E5FF;
                border-radius: 20px;
            }
        """)
        
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(30, 25, 30, 25)
        c_layout.setSpacing(15)
        
        title_l = QLabel(title_text)
        title_l.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFD700;")
        c_layout.addWidget(title_l)
        
        desc_l = QLabel(label_text)
        desc_l.setStyleSheet("color: #94A3B8; font-weight: 600;")
        c_layout.addWidget(desc_l)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type here...")
        self.input_field.setFixedHeight(45)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 0 15px;
                color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #FFD700;
            }
        """)
        c_layout.addWidget(self.input_field)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("QPushButton { background: transparent; color: #94A3B8; font-weight: 800; } QPushButton:hover { color: #FFF; }")
        cancel_btn.clicked.connect(self.reject)
        
        confirm_btn = QPushButton("Done ✨")
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setFixedHeight(40)
        confirm_btn.setFixedWidth(120)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: #FFD700;
                color: #000;
                border-radius: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: #FFEE58;
            }
        """)
        confirm_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        c_layout.addLayout(btn_layout)
        
        layout.addWidget(container)

    def get_text(self):
        return self.input_field.text()

class ModernSelectionDialog(QDialog):
    def __init__(self, title, label, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 260)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.items = items
        self.init_ui(title, label)
        
    def init_ui(self, title_text, label_text):
        from PyQt6.QtWidgets import QFrame, QComboBox
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        
        container = QFrame(); container.setObjectName("ModalContainer")
        container.setStyleSheet("""
            QFrame#ModalContainer {
                background: #0F1229;
                border: 2px solid #00E5FF;
                border-radius: 20px;
            }
        """)
        
        c_layout = QVBoxLayout(container); c_layout.setContentsMargins(30, 25, 30, 25); c_layout.setSpacing(15)
        
        title_l = QLabel(title_text); title_l.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFD700;"); c_layout.addWidget(title_l)
        desc_l = QLabel(label_text); desc_l.setStyleSheet("color: #94A3B8; font-weight: 600;"); c_layout.addWidget(desc_l)
        
        self.combo = QComboBox()
        self.combo.addItems(self.items)
        self.combo.setFixedHeight(45)
        self.combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 0 15px;
                color: #FFFFFF;
                font-size: 14px;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-left: 2px solid #FFD700; border-bottom: 2px solid #FFD700; width: 6px; height: 6px; margin-right: 15px; }
            QComboBox QAbstractItemView {
                background-color: #0F1229;
                color: #FFFFFF;
                selection-background-color: #FFD700;
                selection-color: #000;
                outline: none;
                border: 1px solid #00E5FF;
            }
        """)
        c_layout.addWidget(self.combo)
        
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(15)
        cancel_btn = QPushButton("Cancel"); cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor); cancel_btn.setFixedHeight(40); cancel_btn.setStyleSheet("color: #94A3B8; font-weight: 800; background: transparent;"); cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton("Confirm ⚡"); confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor); confirm_btn.setFixedHeight(40); confirm_btn.setFixedWidth(120); confirm_btn.setStyleSheet("QPushButton { background: #FFD700; color: #000; border-radius: 12px; font-weight: 800; } QPushButton:hover { background: #FFEE58; }"); confirm_btn.clicked.connect(self.accept)
        
        btn_layout.addStretch(); btn_layout.addWidget(cancel_btn); btn_layout.addWidget(confirm_btn)
        c_layout.addLayout(btn_layout); layout.addWidget(container)

    def get_selection(self):
        return self.combo.currentText()
