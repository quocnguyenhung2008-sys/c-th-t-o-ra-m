from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget, QStatusBar, QListWidgetItem
from PySide6.QtCore import QSize, Qt

# Import toàn bộ 7 Tab chức năng từ các module con
from gui.home_tab import HomeTab
from gui.classify_tab import ClassifyTab
from gui.history_tab import HistoryTab
from gui.report_tab import ReportTab
from gui.keyword_tab import KeywordTab
from gui.settings_tab import SettingsTab
from gui.about_tab import AboutTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ Thống Phân Loại Tài Liệu Thông Minh - Chuyên Nghiệp")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 720)
        
        self._init_ui()
        self._apply_stylesheet()
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Khởi tạo Sidebar điều hướng bên trái
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setIconSize(QSize(20, 20))
        self.sidebar.setSpacing(4)
        
        # 2. Khởi tạo Stacked Widget chứa nội dung các trang bên phải
        self.stacked_widget = QStackedWidget()
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget)
        
        # Khởi tạo instance cho toàn bộ 7 Tab chuyên biệt
        self.tabs = [
            HomeTab(),
            ClassifyTab(),
            HistoryTab(),
            ReportTab(),
            KeywordTab(),
            SettingsTab(),
            AboutTab()
        ]
        
        # Thêm các Tab vào Stacked Widget và đăng ký mục tương ứng trên Sidebar
        sidebar_menus = [
            "📊 Trang Chủ Dashboard",
            "📂 Phân Loại Tài Liệu",
            "📜 Lịch Sử Phiên Chạy",
            "📋 Báo Cáo Phân Tích",
            "🔑 Quản Lý Từ Khóa",
            "⚙️ Cài Đặt Hệ Thống",
            "ℹ️ Giới Thiệu Phần Mềm"
        ]
        
        for index, tab_widget in enumerate(self.tabs):
            self.stacked_widget.addWidget(tab_widget)
            item = QListWidgetItem(sidebar_menus[index])
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.sidebar.addItem(item)
            
        # Kết nối sự kiện nhấp chuột đổi trang giữa Sidebar và Stacked Widget
        self.sidebar.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        self.sidebar.setCurrentRow(0) # Đặt Trang chủ làm mặc định khi mở app
        
        # Thanh trạng thái (Status Bar) dưới cùng ứng dụng
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hệ thống hoạt động Offline an toàn.")

    def _apply_stylesheet(self):
        # Đồng bộ thiết kế Modern UI / Fluent Design cho toàn bộ khung ứng dụng
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8FAFC;
            }
            QListWidget {
                background-color: #1E293B;
                color: #94A3B8;
                border: none;
                padding-top: 15px;
            }
            QListWidget::item {
                height: 50px;
                padding-left: 20px;
                border-left: 4px solid transparent;
                font-size: 13px;
                font-weight: 500;
            }
            QListWidget::item:hover {
                background-color: #334155;
                color: #F8FAFC;
            }
            QListWidget::item:selected {
                background-color: #2563EB;
                border-left: 4px solid #3B82F6;
                color: #FFFFFF;
                font-weight: bold;
            }
            QStatusBar {
                background-color: #EFF6FF;
                color: #1E293B;
                font-size: 12px;
                border-top: 1px solid #E2E8F0;
            }
        """)