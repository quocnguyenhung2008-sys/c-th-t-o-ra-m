"""Enhanced progress panel widget."""
from __future__ import annotations

import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.styles import PRIMARY, SUCCESS, WARNING, TEXT, SUBTEXT
from gui.utils import format_eta


class ProgressPanel(QWidget):
    """Progress bar with detailed counters, current file label, and ETA."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Top row: percentage text + counter
        top_row = QHBoxLayout()

        self._lbl_pct = QLabel("0%")
        self._lbl_pct.setStyleSheet(f"color: {PRIMARY}; font-weight: bold; font-size: 15px;")
        top_row.addWidget(self._lbl_pct)

        top_row.addStretch()

        self._lbl_counter = QLabel("0 / 0")
        self._lbl_counter.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")
        top_row.addWidget(self._lbl_counter)

        layout.addLayout(top_row)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

        # Bottom row: current file + ETA
        bot_row = QHBoxLayout()

        self._lbl_file = QLabel("Sẵn sàng")
        self._lbl_file.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
        self._lbl_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._lbl_file.setMaximumWidth(400)
        bot_row.addWidget(self._lbl_file)

        bot_row.addStretch()

        self._lbl_eta = QLabel("ETA: —")
        self._lbl_eta.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")
        bot_row.addWidget(self._lbl_eta)

        layout.addLayout(bot_row)

        # Runtime tracking for ETA
        self._start_time: float | None = None
        self._total: int = 0

    # ------------------------------------------------------------------
    def start(self, total: int) -> None:
        self._total = total
        self._start_time = time.perf_counter()
        self._bar.setValue(0)
        self._bar.setRange(0, 100)
        self._lbl_pct.setText("0%")
        self._lbl_counter.setText(f"0 / {total}")
        self._lbl_file.setText("Đang bắt đầu…")
        self._lbl_eta.setText("ETA: —")

    def update(self, current: int, filename: str) -> None:
        if self._total == 0:
            return
        pct = int(current / self._total * 100)
        self._bar.setValue(pct)
        self._lbl_pct.setText(f"{pct}%")
        self._lbl_counter.setText(f"{current} / {self._total}")
        name = filename if len(filename) <= 40 else "…" + filename[-38:]
        self._lbl_file.setText(f"Đang xử lý: {name}")

        # ETA calculation
        if self._start_time and current > 0:
            elapsed = time.perf_counter() - self._start_time
            remaining = (elapsed / current) * (self._total - current)
            self._lbl_eta.setText(f"ETA: {format_eta(remaining)}")

    def finish(self, elapsed: float) -> None:
        self._bar.setValue(100)
        self._lbl_pct.setText("100%")
        self._lbl_file.setText(f"✅ Hoàn thành trong {format_eta(elapsed)}")
        self._lbl_eta.setText("")

    def reset(self) -> None:
        self._bar.setValue(0)
        self._lbl_pct.setText("0%")
        self._lbl_counter.setText("0 / 0")
        self._lbl_file.setText("Sẵn sàng")
        self._lbl_eta.setText("ETA: —")
        self._start_time = None
        self._total = 0
