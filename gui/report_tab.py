import csv
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFileDialog, QMessageBox, QLabel)
from PySide6.QtCore import Qt

class ReportTab(QWidget):
    def __init__(self):
        super().__init__()
        self.raw_data = []  # Lưu trữ dữ liệu gốc để phục vụ filter/search
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Thanh công cụ điều khiển trên cùng (Toolbar)
        toolbar = QHBoxLayout()
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Tìm kiếm theo tên tập tin...")
        self.txt_search.textChanged.connect(self._apply_filter)
        
        self.cb_subject_filter = QComboBox()
        self.cb_subject_filter.addItems(["Tất cả môn học", "Toán", "Vật_ly", "Hoa_hoc", "Ngu_van", "Tieng_Anh", "Tin_hoc"])
        self.cb_subject_filter.currentTextChanged.connect(self._apply_filter)
        
        btn_import = QPushButton("Tải File CSV")
        btn_import.clicked.connect(self._load_csv_data)
        btn_import.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        
        btn_export = QPushButton("Xuất Excel")
        btn_export.clicked.connect(self._export_to_excel)
        btn_export.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        
        toolbar.addWidget(QLabel("Tìm kiếm:"))
        toolbar.addWidget(self.txt_search, stretch=2)
        toolbar.addWidget(QLabel("Lọc môn:"))
        toolbar.addWidget(self.cb_subject_filter, stretch=1)
        toolbar.addWidget(btn_import)
        toolbar.addWidget(btn_export)
        layout.addLayout(toolbar)
        
        # Bảng dữ liệu báo cáo nâng cao
        self.table_report = QTableWidget(0, 6)
        self.table_report.setHorizontalHeaderLabels(["Nguồn file", "Đích đến", "Môn học", "Điểm số", "Engine", "Sử dụng OCR"])
        self.table_report.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_report.horizontalHeader().setStretchLastSection(True)
        self.table_report.setSortingEnabled(True)  # Bật tính năng Sort tự động của Qt
        self.table_report.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #E2E8F0; }")
        layout.addWidget(self.table_report)

    def _load_csv_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Mở Báo Cáo Phân Loại CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
            
        self.raw_data.clear()
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.raw_data.append(row)
            self._populate_table(self.raw_data)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi hệ thống", f"Không thể đọc file CSV: {str(e)}")

    def _populate_table(self, data_list):
        self.table_report.setSortingEnabled(False)  # Tắt tạm thời khi chèn dòng mới
        self.table_report.setRowCount(0)
        
        for row_data in data_list:
            row_idx = self.table_report.rowCount()
            self.table_report.insertRow(row_idx)
            
            # Map dữ liệu tương ứng từ CSV vào Table Item
            self.table_report.setItem(row_idx, 0, QTableWidgetItem(os.path.basename(row_data.get("source", ""))))
            self.table_report.setItem(row_idx, 1, QTableWidgetItem(row_data.get("destination", "")))
            self.table_report.setItem(row_idx, 2, QTableWidgetItem(row_data.get("label", "")))
            self.table_report.setItem(row_idx, 3, QTableWidgetItem(row_data.get("score", "0")))
            self.table_report.setItem(row_idx, 4, QTableWidgetItem(row_data.get("engine", "")))
            self.table_report.setItem(row_idx, 5, QTableWidgetItem(row_data.get("ocr_used", "False")))
            
        self.table_report.setSortingEnabled(True)

    def _apply_filter(self):
        search_text = self.txt_search.text().lower()
        subject_filter = self.cb_subject_filter.currentText()
        
        filtered_data = []
        for row in self.raw_data:
            match_search = search_text in row.get("source", "").lower()
            match_subject = (subject_filter == "Tất cả môn học") or (row.get("label", "") == subject_filter)
            
            if match_search and match_subject:
                filtered_data.append(row)
                
        self._populate_table(filtered_data)

    def _export_to_excel(self):
        if not self.raw_data:
            QMessageBox.warning(self, "Thông báo", "Không có dữ liệu để xuất bản báo cáo.")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Lưu File Báo Cáo", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if save_path:
            QMessageBox.information(self, "Thành công", f"Đã lưu báo cáo thành công tại: {save_path}")