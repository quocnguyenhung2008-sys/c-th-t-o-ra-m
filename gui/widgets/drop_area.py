"""Drag-and-drop file area widget."""
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class DropArea(QFrame):
    """A styled frame that accepts file/folder drops and emits `files_dropped`."""

    files_dropped = pyqtSignal(list)  # list[str]
    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropArea")
        self.setAcceptDrops(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        self._icon = QLabel("📥", self)
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setStyleSheet("font-size: 46px; background: transparent;")
        layout.addWidget(self._icon)

        self._text = QLabel(
            "KÉO THẢ TỆP / THƯ MỤC VÀO ĐÂY\n"
            "hoặc click để chọn tệp…",
            self,
        )
        self._text.setAlignment(Qt.AlignCenter)
        self._text.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #a6adc8; background: transparent;"
        )
        layout.addWidget(self._text)

    # ------------------------------------------------------------------
    # Drag & Drop handlers
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragOver", "true")
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("dragOver", "false")
        self.style().polish(self)

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        self.setProperty("dragOver", "false")
        self.style().polish(self)
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.toLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
        event.acceptProposedAction()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
