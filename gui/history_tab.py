from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PySide6.QtCore import Qt

class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("Lịch Sử Các Phiên Phân Loại")
        lbl_title.setStyleSheet("color: #1E293B; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)
        
        self.table_history = QTableWidget(3, 5)
        self.table_history.setHorizontalHeaderLabels(["Mã Phiên", "Thời Gian", "Thư Mục Quét", "Tổng Số File", "Trạng Thái"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_history.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #E2E8F0; }")
        
        # Insert một vài dữ liệu demo mẫu lịch sử hệ thống
        self._add_history_row(0, "SESSION_001", "2026-06-25 09:15", "D:/Documents/Input", "150 file", "Hoàn thành")
        self._add_history_row(1, "SESSION_002", "2026-06-26 14:30", "C:/User/Downloads", "1,024 file", "Hoàn thành")
        self._add_history_row(2, "SESSION_003", "2026-06-28 10:05", "D:/Documents/Test_Bio", "45 file", "Đã hủy")
        
        layout.addWidget(self.table_history)
        
    def _add_history_row(self, row, s_id, time, folder, total, status):
        self.table_history.setItem(row, 0, QTableWidgetItem(s_id))
        self.table_history.setItem(row, 1, QTableWidgetItem(time))
        self.table_history.setItem(row, 2, QTableWidgetItem(folder))
        self.table_history.setItem(row, 3, QTableWidgetItem(total))
        self.table_history.setItem(row, 4, QTableWidgetItem(status))