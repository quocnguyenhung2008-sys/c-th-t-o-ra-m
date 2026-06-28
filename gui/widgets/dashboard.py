"""Dashboard summary cards widget."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from gui.styles import PRIMARY, SUCCESS, WARNING, ERROR


class _Card(QFrame):
    def __init__(self, icon: str, value: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumWidth(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setObjectName("CardIcon")
        self._icon_lbl.setAlignment(Qt.AlignLeft)
        layout.addWidget(self._icon_lbl)

        self._value_lbl = QLabel(value)
        self._value_lbl.setObjectName("CardValue")
        layout.addWidget(self._value_lbl)

        self._label_lbl = QLabel(label)
        self._label_lbl.setObjectName("CardLabel")
        layout.addWidget(self._label_lbl)

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(value)

    def set_color(self, color: str) -> None:
        self._value_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold; background: transparent;")


class DashboardCards(QWidget):
    """Row of summary cards showing queue size, total size, output folder, and ETA."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._card_files  = _Card("📁", "0",  "Tệp trong hàng chờ")
        self._card_size   = _Card("💾", "0 B", "Tổng dung lượng")
        self._card_eta    = _Card("⏱", "—",  "Thời gian ước tính")
        self._card_output = _Card("📂", "outputs", "Thư mục đầu ra")

        for card in (self._card_files, self._card_size, self._card_eta, self._card_output):
            layout.addWidget(card, 1)

    # ------------------------------------------------------------------
    def update_queue(self, count: int, total_bytes: int, output_dir: str) -> None:
        from gui.utils import format_size
        self._card_files.set_value(str(count))
        self._card_size.set_value(format_size(total_bytes))
        # Truncate long paths
        if len(output_dir) > 22:
            output_dir = "…" + output_dir[-20:]
        self._card_output.set_value(output_dir)

    def update_eta(self, eta_str: str) -> None:
        self._card_eta.set_value(eta_str)
