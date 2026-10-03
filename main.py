import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow
from styles import DARK_STYLESHEET

def main():
    # Enable high-DPI scaling
    app = QApplication(sys.argv)
    app.setApplicationName("USB Port Watcher")
    app.setOrganizationName("HomelabOps")
    
    # Apply modern dark stylesheet
    app.setStyleSheet(DARK_STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
