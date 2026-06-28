"""Collapsible log panel widget."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.styles import SUBTEXT


class LogWidget(QWidget):
    """A collapsible log panel with a QTextEdit for messages."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel("📋 Logs")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        header.addWidget(lbl)
        header.addStretch()

        self._btn_toggle = QPushButton("▲ Thu gọn")
        self._btn_toggle.setStyleSheet(
            f"background: transparent; border: none; color: {SUBTEXT}; font-size: 12px; padding: 2px 6px;"
        )
        self._btn_toggle.setFixedHeight(24)
        self._btn_toggle.clicked.connect(self._toggle)
        header.addWidget(self._btn_toggle)

        layout.addLayout(header)

        # Log text area
        self._txt = QTextEdit()
        self._txt.setObjectName("TxtLogs")
        self._txt.setReadOnly(True)
        self._txt.setMinimumHeight(100)
        layout.addWidget(self._txt)

        self._collapsed = False

    # ------------------------------------------------------------------
    def append(self, message: str) -> None:
        self._txt.append(message)
        sb = self._txt.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self) -> None:
        self._txt.clear()

    def _toggle(self) -> None:
        self._collapsed = not self._collapsed
        self._txt.setVisible(not self._collapsed)
        self._btn_toggle.setText("▼ Mở rộng" if self._collapsed else "▲ Thu gọn")
