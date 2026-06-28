import time
from typing import Dict, Any
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QProgressBar, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog)
from PySide6.QtCore import QThread, Signal, Slot, Qt
from PySide6.QtGui import QColor

# Giả lập hoặc import từ core hiện tại của bạn
# from core.classifier import DocumentClassifier 

class ClassificationWorker(QThread):
    """Worker luồng nền đảm nhiệm việc gọi logic core, không gây treo giao diện"""
    progress_signal = Signal(dict)  # Truyền thông tin file đang xử lý
    finished_signal = Signal(int)   # Truyền tổng số file hoàn thành

    def __init__(self, input_folder: str, options: Dict[str, Any]):
        super().__init__()
        self.input_folder = input_folder
        self.options = options
        self.is_running = True

    def run(self):
        # Giả lập danh sách file đọc được từ input_folder của bạn
        mock_files = ["Toan_Hinh_Hoc_12.pdf", "De_Thi_Vat_Ly_Giu_Ky.docx", "Document_Unkown.pdf"]
        total_files = len(mock_files)
        
        for index, file_name in enumerate(mock_files):
            if not self.is_running:
                break
                
            time.sleep(1.5) # Giả lập thời gian xử lý thực tế của module core
            
            # ĐÂY LÀ NƠI BẠN GỌI LOGIC TỪ CORE:
            # result = DocumentClassifier.classify(file_name, **self.options)
            
            # Mock dữ liệu trả về từ Core để đẩy lên GUI hiển thị
            mock_result = {
                "file_name": file_name,
                "subject": "Toán Học" if "Toan" in file_name else ("Vật Lý" if "Ly" in file_name else "Không Xác Định"),
                "score": 95.0 if "Toan" in file_name else (75.5 if "Ly" in file_name else 45.0),
                "engine": "Filename" if "Toan" in file_name else "OCR (EasyOCR)",
                "progress": int(((index + 1) / total_files) * 100)
            }
            
            self.progress_signal.emit(mock_result)
            
        self.finished_signal.emit(total_files)

    def stop(self):
        self.is_running = False


class ClassifyTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. Khu vực cấu hình đường dẫn (Input/Output Folder)
        path_layout = QHBoxLayout()
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Đường dẫn thư mục đầu vào (Input Folder)...")
        btn_browse = QPushButton("Chọn Thư Mục")
        btn_browse.clicked.connect(self._browse_folder)
        path_layout.addWidget(self.txt_input)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)
        
        # 2. Khu vực tùy chọn cấu hình nhanh (Checkboxes)
        options_layout = QHBoxLayout()
        self.chk_ocr = QCheckBox("Bật nhận diện hình ảnh (OCR)")
        self.chk_move = QCheckBox("Di chuyển file (Move thay vì Copy)")
        self.chk_accuracy = QCheckBox("Chế độ chính xác cao (Accuracy Mode)")
        options_layout.addWidget(self.chk_ocr)
        options_layout.addWidget(self.chk_move)
        options_layout.addWidget(self.chk_accuracy)
        layout.addLayout(options_layout)
        
        # 3. Thanh tiến trình xử lý
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                text-align: center;
                background-color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 4. Bảng hiển thị kết quả Real-time chuyên nghiệp
        self.table_results = QTableWidget(0, 4)
        self.table_results.setHorizontalHeaderLabels(["Tên Tập Tin", "Môn Học Định Danh", "Độ Tin Cậy", "Nguồn Phân Tích"])
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_results.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #E2E8F0; }")
        layout.addWidget(self.table_results)
        
        # 5. Thanh điều khiển Action điều hướng dưới cùng
        action_layout = QHBoxLayout()
        self.btn_start = QPushButton("Bắt Đầu Tiến Trình")
        self.btn_start.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        self.btn_start.clicked.connect(self._start_classification)
        
        self.btn_stop = QPushButton("Dừng Lại")
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        self.btn_stop.clicked.connect(self._stop_classification)
        
        action_layout.addStretch()
        action_layout.addWidget(self.btn_start)
        action_layout.addWidget(self.btn_stop)
        layout.addLayout(action_layout)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn Thư Mục Chứa Tài Liệu")
        if folder:
            self.txt_input.setText(folder)

    def _start_classification(self):
        options = {
            "ocr": self.chk_ocr.isChecked(),
            "move": self.chk_move.isChecked(),
            "accuracy": self.chk_accuracy.isChecked()
        }
        
        # Khởi tạo luồng Worker tách biệt UI
        self.worker = ClassificationWorker(self.txt_input.text(), options)
        self.worker.progress_signal.connect(self._update_realtime_row)
        self.worker.finished_signal.connect(self._classification_finished)
        
        self.worker.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def _stop_classification(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self._classification_finished(0)

    @Slot(dict)
    def _update_realtime_row(self, data: dict):
        # Cập nhật thanh tiến trình tổng quát
        self.progress_bar.setValue(data["progress"])
        
        # Thêm dòng dữ liệu mới vào bảng
        row_idx = self.table_results.rowCount()
        self.table_results.insertRow(row_idx)
        
        item_name = QTableWidgetItem(data["file_name"])
        item_subject = QTableWidgetItem(data["subject"])
        item_score = QTableWidgetItem(f"{data['score']}%")
        item_engine = QTableWidgetItem(data["engine"])
        
        # Định màu sắc dựa theo mức độ tin cậy (Confidence Score)
        score = data["score"]
        if score >= 90.0:
            bg_color = QColor("#DCFCE7")  # Xanh lá nhạt (An toàn)
        elif score >= 70.0:
            bg_color = QColor("#FEF9C3")  # Vàng nhạt (Cần kiểm tra)
        else:
            bg_color = QColor("#FEE2E2")  # Đỏ nhạt (Nguy cơ / Kém chính xác)
            
        for item in [item_name, item_subject, item_score, item_engine]:
            item.setBackground(bg_color)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            
        self.table_results.setItem(row_idx, 0, item_name)
        self.table_results.setItem(row_idx, 1, item_subject)
        self.table_results.setItem(row_idx, 2, item_score)
        self.table_results.setItem(row_idx, 3, item_engine)
        self.table_results.scrollToBottom()

    @Slot(int)
    def _classification_finished(self, total: int):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.setValue(100)