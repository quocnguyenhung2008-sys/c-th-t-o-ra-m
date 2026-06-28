"""File queue table widget."""
from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QHeaderView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from gui.utils import format_size, open_file

# Status badge colours
_STATUS_COLORS = {
    "waiting":  ("#f9e2af", "🟡"),
    "done":     ("#a6e3a1", "🟢"),
    "error":    ("#f38ba8", "🔴"),
    "unknown":  ("#cba6f7", "🟣"),
    "conflict": ("#fab387", "🟠"),
}

# Column indices
COL_ICON  = 0
COL_NAME  = 1
COL_TYPE  = 2
COL_SIZE  = 3
COL_STATUS = 4
COL_PATH  = 5


class QueueTable(QTableWidget):
    """Displays the file classification queue with icons and status badges."""

    remove_requested = pyqtSignal(list)   # list of row indices
    clear_requested  = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, 6, parent)
        self.setHorizontalHeaderLabels(["", "Tên File", "Loại", "Kích thước", "Trạng thái", "Đường dẫn"])
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.doubleClicked.connect(self._on_double_click)

        hdr = self.horizontalHeader()
        hdr.setSectionResizeMode(COL_ICON,   QHeaderView.Fixed)
        hdr.setSectionResizeMode(COL_NAME,   QHeaderView.Stretch)
        hdr.setSectionResizeMode(COL_TYPE,   QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_SIZE,   QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(COL_PATH,   QHeaderView.Stretch)
        self.setColumnWidth(COL_ICON, 32)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_file(self, path: Path) -> None:
        row = self.rowCount()
        self.insertRow(row)

        icon = "📄" if path.suffix.lower() == ".pdf" else "📝"
        self._item(row, COL_ICON,  icon,            align=Qt.AlignCenter)
        self._item(row, COL_NAME,  path.name)
        self._item(row, COL_TYPE,  path.suffix.upper().lstrip("."))
        try:
            size_str = format_size(path.stat().st_size)
        except Exception:
            size_str = "—"
        self._item(row, COL_SIZE,  size_str,        align=Qt.AlignRight | Qt.AlignVCenter)
        self.set_status(row, "waiting")
        self._item(row, COL_PATH,  str(path))

    def set_status(self, row: int, status_key: str, label: str = "") -> None:
        """Update the status badge for a row."""
        colour, emoji = _STATUS_COLORS.get(status_key, ("#a6adc8", "⬜"))
        text = f"{emoji} {label}" if label else emoji
        item = QTableWidgetItem(text)
        item.setForeground(QColor(colour))
        item.setTextAlignment(Qt.AlignCenter)
        self.setItem(row, COL_STATUS, item)

    def reset_statuses(self) -> None:
        for row in range(self.rowCount()):
            self.set_status(row, "waiting")

    def selected_rows(self) -> list[int]:
        return sorted({idx.row() for idx in self.selectedIndexes()})

    def path_at(self, row: int) -> Path:
        return Path(self.item(row, COL_PATH).text())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _item(self, row: int, col: int, text: str, align: int = Qt.AlignLeft | Qt.AlignVCenter) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(align)
        self.setItem(row, col, item)

    def _show_context_menu(self, pos) -> None:
        menu = QMenu(self)
        act_open   = QAction("📂  Mở vị trí tệp", self)
        act_remove = QAction("✖  Xóa tệp đã chọn", self)
        act_clear  = QAction("🗑  Xóa tất cả", self)
        menu.addAction(act_open)
        menu.addSeparator()
        menu.addAction(act_remove)
        menu.addAction(act_clear)

        rows = self.selected_rows()
        act_open.setEnabled(len(rows) == 1)

        action = menu.exec_(self.mapToGlobal(pos))
        if action == act_open and rows:
            open_file(self.path_at(rows[0]))
        elif action == act_remove:
            self.remove_requested.emit(rows)
        elif action == act_clear:
            self.clear_requested.emit()

    def _on_double_click(self, index) -> None:
        open_file(self.path_at(index.row()))
