from PySide6.QtWidgets import QLabel, QHBoxLayout, QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PySide6.QtGui import QColor

class ToastNotification(QWidget):
    def __init__(self, message: str, level: str = "SUCCESS", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Thiết lập màu sắc nền theo trạng thái thông báo
        bg_color = "#10B981" if level == "SUCCESS" else ("#EF4444" if level == "ERROR" else "#3B82F6")
        
        # Giao diện thông báo dạng Card bo góc hiện đại
        layout = QHBoxLayout(self)
        lbl_msg = QLabel(message)
        lbl_msg.setStyleSheet(f"""
            color: white; 
            font-weight: 600; 
            font-size: 13px; 
            padding: 12px 24px; 
            background-color: {bg_color}; 
            border-radius: 8px;
        """)
        layout.addWidget(lbl_msg)
        
        # Bộ đếm thời gian tự hủy sau 3 giây
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._fade_out)
        self.timer.start(3000)

    def show_toast(self):
        """Hiển thị Toast ở góc dưới cùng bên phải của ứng dụng chính"""
        self.show()
        if self.parent():
            p_geom = self.parent().geometry()
            target_pos = QPoint(p_geom.right() - self.width() - 20, p_geom.bottom() - self.height() - 40)
            self.move(target_pos)

    def _fade_out(self):
        self.timer.stop()
        self.close()