import sys
import os

# Fix for VLC loading on Windows if bundled
if getattr(sys, 'frozen', False):
    # If running as executable
    application_path = sys._MEIPASS
    # Add potential VLC paths in bundled dir
    os.environ['PYTHON_VLC_MODULE_PATH'] = application_path
    os.environ['PYTHON_VLC_LIB_PATH'] = os.path.join(application_path, 'libvlc.dll')


from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
