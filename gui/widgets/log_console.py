from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor
from PySide6.QtCore import QDateTime, Qt

class LogConsole(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(1000) # Tránh tràn bộ nhớ (Virtual Scrolling / Buffer)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0F172A;
                color: #E2E8F0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
            }
        """)

    def log(self, level: str, message: str):
        """Ghi log có timestamp và màu sắc tương ứng với cấp độ"""
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.moveCursor(QTextCursor.End)
        
        # Định dạng màu sắc dựa trên Cấp độ Log
        fmt = QTextCharFormat()
        level = level.upper()
        
        if level == "SUCCESS":
            fmt.setForeground(QColor("#4ADE80")) # Xanh lá
        elif level == "WARNING":
            fmt.setForeground(QColor("#FBBF24")) # Vàng
        elif level == "ERROR":
            fmt.setForeground(QColor("#F87171")) # Đỏ
        else: # INFO
            fmt.setForeground(QColor("#38BDF8")) # Xanh dương nhạt

        # Chèn thẻ Level và nội dung log
        self.setCurrentCharFormat(fmt)
        self.insertPlainText(f"[{timestamp}] [{level}] {message}\n")
        
        # Tự động cuộn xuống dưới cùng
        self.ensureCursorVisible()