import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from core.config_manager import ConfigManager
from core.theme import get_pixel_qss
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BilibiliPixelDanmaku")
    app.setOrganizationName("LanRhyme")

    font = QFont("Noto Sans CJK SC", 10)
    app.setFont(font)

    qss = get_pixel_qss()
    app.setStyleSheet(qss)

    config_manager = ConfigManager()
    window = MainWindow(config_manager)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
