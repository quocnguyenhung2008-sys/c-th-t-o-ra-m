"""Classification settings panel widget."""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)
from PyQt5.QtCore import pyqtSignal
from pathlib import Path


class SettingsPanel(QWidget):
    """Panel containing all classification configuration controls."""

    output_dir_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # ── Output directory ──
        out_group = QGroupBox("📂 Thư mục đầu ra")
        out_lay = QHBoxLayout(out_group)
        self.txt_output = QLineEdit()
        self.txt_output.setPlaceholderText("Chọn thư mục kết quả…")
        self.txt_output.setText(str(Path.cwd() / "outputs"))
        self.txt_output.textChanged.connect(self.output_dir_changed.emit)
        out_lay.addWidget(self.txt_output)
        btn_browse = QPushButton("…")
        btn_browse.setMaximumWidth(36)
        btn_browse.clicked.connect(self._browse_output)
        out_lay.addWidget(btn_browse)
        layout.addWidget(out_group)

        # ── File action ──
        action_group = QGroupBox("⚙  Hành động với tệp")
        action_lay = QHBoxLayout(action_group)
        self.rad_copy = QRadioButton("📋 Sao chép (Khuyến dùng)")
        self.rad_copy.setChecked(True)
        self.rad_move = QRadioButton("✂ Di chuyển")
        action_lay.addWidget(self.rad_copy)
        action_lay.addWidget(self.rad_move)
        action_lay.addStretch()
        layout.addWidget(action_group)

        # ── Options ──
        opts_group = QGroupBox("🔧 Tùy chọn")
        opts_lay = QVBoxLayout(opts_group)
        self.chk_overwrite = QCheckBox("Ghi đè nếu tệp đã tồn tại")
        self.chk_dry_run   = QCheckBox("Chạy thử  (không copy/move thực sự)")
        self.chk_recursive = QCheckBox("Quét thư mục con đệ quy")
        self.chk_recursive.setChecked(True)
        self.chk_accuracy  = QCheckBox("Ưu tiên chính xác  (đọc nhiều trang, tắt Fast Path)")
        self.chk_dia_gdcd  = QCheckBox("Bật phân loại Địa lý & GDCD")
        for chk in (self.chk_overwrite, self.chk_dry_run, self.chk_recursive,
                    self.chk_accuracy, self.chk_dia_gdcd):
            opts_lay.addWidget(chk)
        layout.addWidget(opts_group)

        # ── OCR ──
        ocr_group = QGroupBox("🔍 OCR Engine")
        ocr_lay = QHBoxLayout(ocr_group)
        ocr_lay.addWidget(QLabel("Engine:"))
        self.cmb_ocr = QComboBox()
        self.cmb_ocr.addItems(["none", "easyocr", "paddleocr"])
        ocr_lay.addWidget(self.cmb_ocr)
        self.chk_always_ocr = QCheckBox("Always OCR PDF")
        ocr_lay.addWidget(self.chk_always_ocr)
        ocr_lay.addStretch()
        layout.addWidget(ocr_group)

        layout.addStretch()

    # ------------------------------------------------------------------
    def _browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Chọn thư mục đầu ra")
        if directory:
            self.txt_output.setText(directory)

    def output_dir(self) -> str:
        return self.txt_output.text().strip()

    def set_enabled_all(self, enabled: bool) -> None:
        for w in (self.txt_output, self.rad_copy, self.rad_move,
                  self.chk_overwrite, self.chk_dry_run, self.chk_recursive,
                  self.chk_accuracy, self.chk_dia_gdcd,
                  self.cmb_ocr, self.chk_always_ocr):
            w.setEnabled(enabled)
