"""About dialog."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Về ứng dụng")
        self.setFixedSize(420, 300)
        self.setModal(True)

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(30, 30, 30, 30)

        title = QLabel("📄 Offline Vietnamese Document Sorter")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #89b4fa;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        version = QLabel("Phiên bản 2.0 — GUI Edition")
        version.setStyleSheet("color: #a6adc8; font-size: 12px;")
        version.setAlignment(Qt.AlignCenter)
        lay.addWidget(version)

        desc = QLabel(
            "Phần mềm phân loại tài liệu học tập Tiếng Việt theo môn học,\n"
            "hoạt động hoàn toàn offline, không cần kết nối mạng.\n\n"
            "Hỗ trợ PDF, DOCX với tùy chọn OCR."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        lay.addWidget(desc)

        lay.addStretch()

        btn_ok = QPushButton("Đóng")
        btn_ok.clicked.connect(self.accept)
        lay.addWidget(btn_ok)
