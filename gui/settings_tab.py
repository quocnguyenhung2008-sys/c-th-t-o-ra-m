import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox, 
                             QSpinBox, QPushButton, QMessageBox, QLabel)

# BẮT BUỘC: Tên class phải viết hoa chữ S và T đúng chuẩn PascalCase
class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        lbl_title = QLabel("Cấu Hình Hệ Thống Ứng Dụng")
        lbl_title.setStyleSheet("color: #1E293B; font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.cb_theme = QComboBox()
        self.cb_theme.addItems(["Giao diện sáng (Light Mode)", "Giao diện tối (Dark Mode)"])
        
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 16)
        self.spin_threads.setValue(4)
        
        self.cb_ocr_backend = QComboBox()
        self.cb_ocr_backend.addItems(["EasyOCR", "PaddleOCR", "Tesseract"])
        
        form_layout.addRow("Chủ đề ứng dụng:", self.cb_theme)
        form_layout.addRow("Số luồng CPU tối đa:", self.spin_threads)
        form_layout.addRow("OCR Engine mặc định:", self.cb_ocr_backend)
        layout.addLayout(form_layout)
        
        btn_save = QPushButton("Lưu Toàn Bộ Cấu Hình")
        btn_save.clicked.connect(self._save_config)
        btn_save.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        layout.addWidget(btn_save)
        layout.addStretch()

    def _load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.cb_theme.setCurrentText(cfg.get("theme", "Giao diện sáng (Light Mode)"))
                self.spin_threads.setValue(cfg.get("max_threads", 4))
                self.cb_ocr_backend.setCurrentText(cfg.get("ocr_backend", "EasyOCR"))
            except Exception:
                pass

    def _save_config(self):
        cfg = {
            "theme": self.cb_theme.currentText(),
            "max_threads": self.spin_threads.value(),
            "ocr_backend": self.cb_ocr_backend.currentText()
        }
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Thành công", "Đã lưu thông số cấu hình hệ thống.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu cấu hình: {str(e)}")