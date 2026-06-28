import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from gui.main_window import MainWindow

def main():
    # Khởi tạo ứng dụng Qt
    app = QApplication(sys.argv)
    
    # Thiết lập Font hệ thống đồng bộ phong cách Modern UI
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Khởi tạo cửa sổ chính
    window = MainWindow()
    window.show()
    
    # Thực thi vòng lặp sự kiện
    sys.exit(app.exec())

if __name__ == "__main__":
    main()