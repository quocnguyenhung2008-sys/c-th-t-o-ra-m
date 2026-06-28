from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

# BẮT BUỘC: Tên class phải viết hoa đúng ký tự đầu 'AboutTab'
class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        lbl_logo = QLabel("📁")
        lbl_logo.setStyleSheet("font-size: 72px;")
        lbl_logo.setAlignment(Qt.AlignCenter)
        
        lbl_app_name = QLabel("Smart Document Classifier")
        lbl_app_name.setStyleSheet("font-size: 24px; font-weight: bold; color: #2563EB;")
        
        lbl_version = QLabel("Phiên bản thương mại: v2.0.0 (Bản dựng ổn định)\nPython 3.11 + PySide6 Fluent Engine")
        lbl_version.setStyleSheet("color: #64748B; font-size: 14px;")
        lbl_version.setAlignment(Qt.AlignCenter)
        
        lbl_license = QLabel("Sản phẩm hoạt động hoàn toàn Offline bảo mật dữ liệu tuyệt đối.\nBản quyền © 2026. Toàn quyền bảo lưu.")
        lbl_license.setStyleSheet("color: #94A3B8; font-style: italic;")
        lbl_license.setAlignment(Qt.AlignCenter)
        
        btn_update = QPushButton("Kiểm tra bản cập nhật mới (Check Update)")
        btn_update.setStyleSheet("background-color: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1; padding: 8px 16px; border-radius: 4px;")
        
        layout.addWidget(lbl_logo)
        layout.addWidget(lbl_app_name, alignment=Qt.AlignCenter)
        layout.addWidget(lbl_version)
        layout.addWidget(lbl_license)
        layout.addWidget(btn_update, alignment=Qt.AlignCenter)