"""Keyword editor widget – comma-separated text input per subject."""
from __future__ import annotations

import json
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gui.styles import PRIMARY, SUBTEXT


class KeywordEditor(QWidget):
    """Two-pane keyword editor: subject list (left) + comma-separated text input (right)."""

    data_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: dict[str, list[dict]] = {}
        self._file: Path | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Splitter: subject list | keyword editor
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, 1)

        # ── Left: subject list ──
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(8)

        lbl_list = QLabel("📚 Danh sách Môn học:")
        lbl_list.setStyleSheet("font-weight: bold; font-size: 13px;")
        left_lay.addWidget(lbl_list)

        self._subject_list = QListWidget()
        self._subject_list.currentItemChanged.connect(self._on_subject_changed)
        left_lay.addWidget(self._subject_list, 1)

        btn_row = QHBoxLayout()
        btn_add_sub = QPushButton("+ Thêm môn")
        btn_add_sub.clicked.connect(self._add_subject)
        btn_del_sub = QPushButton("− Xóa môn")
        btn_del_sub.clicked.connect(self._del_subject)
        btn_row.addWidget(btn_add_sub)
        btn_row.addWidget(btn_del_sub)
        left_lay.addLayout(btn_row)

        splitter.addWidget(left)

        # ── Right: keyword text editor ──
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(10)

        self._subject_title = QLabel("Chọn môn học")
        self._subject_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {PRIMARY};"
        )
        right_lay.addWidget(self._subject_title)

        right_lay.addWidget(QLabel("Từ khóa (phân cách bằng dấu phẩy):"))

        self._kw_edit = QTextEdit()
        self._kw_edit.setPlaceholderText(
            "Nhập từ khóa, phân cách bằng dấu phẩy…\n"
            "Ví dụ: đại số, toán học, nguyên hàm, tích phân, đạo hàm"
        )
        right_lay.addWidget(self._kw_edit, 1)

        # Hint
        hint = QLabel(
            "💡  Từ khóa cũ được giữ nguyên trọng số ban đầu.\n"
            "     Từ khóa mới thêm vào nhận trọng số mặc định 10.0.\n"
            "     Hệ thống hỗ trợ so khớp không dấu và regex tự động."
        )
        hint.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")
        hint.setWordWrap(True)
        right_lay.addWidget(hint)

        # Save button
        self._btn_save = QPushButton("💾  Lưu từ khóa & Cập nhật")
        self._btn_save.setObjectName("BtnSuccess")
        self._btn_save.clicked.connect(self._save_current)
        right_lay.addWidget(self._btn_save)

        splitter.addWidget(right)
        splitter.setSizes([220, 700])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load_from_file(self, path: Path) -> None:
        self._file = path
        if not path.exists():
            self._data = {}
            return
        try:
            with open(path, encoding="utf-8") as f:
                self._data = json.load(f)
            self._populate_subjects()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi tải dữ liệu", f"Không thể đọc keywords.json:\n{e}")

    def save_to_file(self) -> bool:
        if not self._file:
            return False
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Lỗi lưu", f"Không thể ghi keywords.json:\n{e}")
            return False

    # ------------------------------------------------------------------
    # Subject management
    # ------------------------------------------------------------------
    def _populate_subjects(self) -> None:
        current_text = (
            self._subject_list.currentItem().text()
            if self._subject_list.currentItem()
            else None
        )
        self._subject_list.clear()
        for name in sorted(self._data.keys()):
            self._subject_list.addItem(name)
        # Restore selection
        if current_text:
            items = self._subject_list.findItems(current_text, Qt.MatchExact)
            if items:
                self._subject_list.setCurrentItem(items[0])

    def _on_subject_changed(self, current: QListWidgetItem, _prev) -> None:
        if not current:
            self._subject_title.setText("Chọn môn học")
            self._kw_edit.clear()
            return
        subject = current.text()
        self._subject_title.setText(f"Môn học: {subject}")
        entries = self._data.get(subject, [])
        kw_text = ", ".join(e["keyword"] for e in entries)
        self._kw_edit.setPlainText(kw_text)

    def _add_subject(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Thêm môn học mới",
            "Tên môn học (không dấu, vd: Tin_hoc, GDCD):"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._data:
            QMessageBox.warning(self, "Cảnh báo", f"Môn học '{name}' đã tồn tại.")
            return
        self._data[name] = []
        self.save_to_file()
        self._populate_subjects()
        items = self._subject_list.findItems(name, Qt.MatchExact)
        if items:
            self._subject_list.setCurrentItem(items[0])

    def _del_subject(self) -> None:
        item = self._subject_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Cảnh báo", "Chọn môn học muốn xóa.")
            return
        name = item.text()
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            f"Xóa môn '{name}' và toàn bộ từ khóa?\nThao tác không thể hoàn tác.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            del self._data[name]
            self.save_to_file()
            self._kw_edit.clear()
            self._subject_title.setText("Chọn môn học")
            self._populate_subjects()

    # ------------------------------------------------------------------
    # Save keywords
    # ------------------------------------------------------------------
    def _save_current(self) -> None:
        item = self._subject_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Cảnh báo", "Chọn môn học trước khi lưu.")
            return

        subject = item.text()
        raw = self._kw_edit.toPlainText().strip()

        # Parse comma-separated keywords, de-duplicate preserving order
        seen: set[str] = set()
        keywords: list[str] = []
        for kw in raw.split(","):
            kw = kw.strip()
            if kw and kw.lower() not in seen:
                seen.add(kw.lower())
                keywords.append(kw)

        # Preserve existing weights; assign default 10.0 for new ones
        existing: dict[str, float] = {
            e["keyword"].lower(): e["weight"]
            for e in self._data.get(subject, [])
        }
        new_entries = [
            {"keyword": kw, "weight": existing.get(kw.lower(), 10.0)}
            for kw in keywords
        ]

        self._data[subject] = new_entries
        if self.save_to_file():
            QMessageBox.information(
                self, "Đã lưu",
                f"Đã cập nhật {len(new_entries)} từ khóa cho môn '{subject}'."
            )
            self.data_changed.emit()
            self._populate_subjects()
