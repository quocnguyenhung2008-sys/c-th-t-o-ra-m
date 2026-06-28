import json
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPlainTextEdit, QPushButton, QLabel, QMessageBox)
from PySide6.QtGui import QFont

class KeywordTab(QWidget):
    def __init__(self):
        super().__init__()
        # Đường dẫn giả định tương đối tới các file cấu hình từ khóa của core
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self._init_ui()
        self._on_file_changed() # Load file mặc định khi khởi động
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Chọn cấu hình tệp tin từ khóa
        top_layout = QHBoxLayout()
        self.cb_file_selector = QComboBox()
        self.cb_file_selector.addItems(["aliases.json", "keywords.json", "negative_keywords.json"])
        self.cb_file_selector.currentTextChanged.connect(self._on_file_changed)
        
        top_layout.addWidget(QLabel("Chọn Tệp Từ Khóa Cần Sửa:"))
        top_layout.addWidget(self.cb_file_selector, stretch=1)
        top_layout.addStretch(2)
        layout.addLayout(top_layout)
        
        # Trình Editor thô (Mã JSON)
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setStyleSheet("background-color: #1E293B; color: #38BDF8; border-radius: 6px; padding: 10px;")
        layout.addWidget(self.editor)
        
        # Thanh điều khiển hành động lưu trữ/backup
        bottom_layout = QHBoxLayout()
        btn_validate = QPushButton("Kiểm tra định dạng (Validate)")
        btn_validate.clicked.connect(self._validate_json)
        btn_validate.setStyleSheet("background-color: #475569; color: white; padding: 8px 16px; border-radius: 4px;")
        
        btn_save = QPushButton("Lưu Thay Đổi (Cập nhật Core)")
        btn_save.clicked.connect(self._save_json_file)
        btn_save.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 8px 24px; border-radius: 4px;")
        
        bottom_layout.addWidget(btn_validate)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_save)
        layout.addLayout(bottom_layout)

    def _get_current_file_path(self):
        filename = self.cb_file_selector.currentText()
        os.makedirs(self.config_dir, exist_ok=True)
        return os.path.join(self.config_dir, filename)

    def _on_file_changed(self):
        file_path = self._get_current_file_path()
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                self.editor.setPlainText(json.dumps(content, indent=2, ensure_ascii=False))
            except Exception:
                self.editor.setPlainText("{\n  // File bị lỗi định dạng hoặc trống\n}")
        else:
            # Tạo dữ liệu mẫu nếu file chưa tồn tại
            self.editor.setPlainText("{\n  \n}")

    def _validate_json(self) -> bool:
        try:
            json.loads(self.editor.toPlainText())
            QMessageBox.information(self, "Hợp lệ", "Định dạng cấu trúc JSON hoàn toàn chính xác!")
            return True
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Lỗi Định Dạng", f"JSON không hợp lệ. Chi tiết lỗi:\n{str(e)}")
            return False

    def _save_json_file(self):
        if not self._validate_json():
            return
        
        file_path = self._get_current_file_path()
        try:
            parsed_data = json.loads(self.editor.toPlainText())
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Thành công", f"Đã cập nhật hệ thống từ khóa thành công vào {os.path.basename(file_path)}.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi ghi file", f"Không thể lưu file: {str(e)}")