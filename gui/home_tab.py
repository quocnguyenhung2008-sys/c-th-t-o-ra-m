from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt

class MetricCard(QWidget):
    """Widget thành phần hiển thị thẻ số liệu phân tích nhanh (KPI Card)"""
    def __init__(self, title: str, value: str, color_hex: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500;")
        
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"color: {color_hex}; font-size: 26px; font-weight: bold; margin-top: 5px;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        
        self.setStyleSheet("""
            MetricCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
        """)

class HomeTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Tiêu đề Dashboard
        lbl_header = QLabel("Bảng Thống Kê Tổng Quan Hệ Thống")
        lbl_header.setStyleSheet("color: #1E293B; font-size: 22px; font-weight: bold;")
        layout.addWidget(lbl_header)
        
        # Bố cục lưới hiển thị các Thẻ Metric nhanh
        grid_metrics = QGridLayout()
        grid_metrics.setSpacing(15)
        
        grid_metrics.addWidget(MetricCard("TỔNG SỐ TẬP TIN", "1,248 file", "#1E293B"), 0, 0)
        grid_metrics.addWidget(MetricCard("ĐÃ XỬ LÝ THÀNH CÔNG", "1,120 file", "#16A34A"), 0, 1)
        grid_metrics.addWidget(MetricCard("CẦN KIỂM TRA LẠI (LOW CONFIDENCE)", "94 file", "#EA580C"), 0, 2)
        grid_metrics.addWidget(MetricCard("TỐC ĐỘ XỬ LÝ TRUNG BÌNH", "0.45s / file", "#2563EB"), 0, 3)
        
        layout.addLayout(grid_metrics)
        
        # Khu vực tích hợp biểu đồ trực quan (QtCharts)
        lbl_chart_placeholder = QLabel("Khu vực tích hợp Biểu đồ phân bổ môn học (PieChart / BarChart)")
        lbl_chart_placeholder.setAlignment(Qt.AlignCenter)
        lbl_chart_placeholder.setStyleSheet("""
            background-color: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 8px;
            color: #94A3B8;
            font-style: italic;
        """)
        layout.addWidget(lbl_chart_placeholder, stretch=1)