"""Application bootstrap."""
from __future__ import annotations

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow


def launch() -> None:
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setApplicationName("Offline Vietnamese Document Sorter")
    app.setOrganizationName("DocSorter")

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch()
