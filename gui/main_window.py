<<<<<<< HEAD
"""Main application window – assembles all widgets."""
from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from docsorter.classifier import ClassificationStatus
from docsorter.config import ClassificationConfig
from docsorter.file_ops import discover_files

from gui.styles import QSS, SIDEBAR_W, PRIMARY, SUCCESS, WARNING, ERROR, SUBTEXT, CARD, BG
from gui.utils import format_size, format_eta, open_directory
from gui.widgets.drop_area import DropArea
from gui.widgets.queue_table import QueueTable
from gui.widgets.dashboard import DashboardCards
from gui.widgets.progress_panel import ProgressPanel
from gui.widgets.log_widget import LogWidget
from gui.widgets.settings_panel import SettingsPanel
from gui.widgets.keyword_editor import KeywordEditor
from gui.worker import ClassificationWorker
from gui.dialogs.about_dialog import AboutDialog


# ---------------------------------------------------------------------------
# Header widget
# ---------------------------------------------------------------------------
class _Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Header")
        self.setFixedHeight(62)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(10)

        icon = QLabel("📄")
        icon.setStyleSheet("font-size: 26px; background: transparent;")
        lay.addWidget(icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel("Offline Vietnamese Document Sorter")
        title.setObjectName("AppTitle")
        subtitle = QLabel("AI Document Classification — v2.0")
        subtitle.setObjectName("AppSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        lay.addLayout(title_col)

        lay.addStretch()

        self.status_lbl = QLabel("● Sẵn sàng")
        self.status_lbl.setObjectName("StatusReady")
        lay.addWidget(self.status_lbl)

    def set_status(self, text: str, busy: bool = False) -> None:
        self.status_lbl.setText(f"● {text}")
        name = "StatusBusy" if busy else "StatusReady"
        self.status_lbl.setObjectName(name)
        self.style().polish(self.status_lbl)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.files_queue: list[Path] = []
        self.worker: ClassificationWorker | None = None

        self.setWindowTitle("Offline Vietnamese Document Sorter")
        self.resize(1280, 820)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(QSS)

        self._build_ui()
        self._load_keywords()

    # -----------------------------------------------------------------------
    # UI building
    # -----------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # Header
        self._header = _Header()
        root_lay.addWidget(self._header)

        # Toolbar
        self._build_toolbar()

        # Body: sidebar + stacked content
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # Sidebar
        self._sidebar = QListWidget()
        self._sidebar.setObjectName("Sidebar")
        self._sidebar.setFixedWidth(SIDEBAR_W)
        self._sidebar.setFocusPolicy(Qt.NoFocus)
        for icon, label in [
            ("📂", "Phân loại tài liệu"),
            ("⚙", "Cài đặt"),
            ("📚", "Từ khóa & Môn học"),
            ("ℹ", "Giới thiệu"),
        ]:
            item = QListWidgetItem(f"  {icon}  {label}")
            item.setSizeHint(item.sizeHint().__class__(SIDEBAR_W, 44))
            self._sidebar.addItem(item)
        self._sidebar.setCurrentRow(0)
        self._sidebar.currentRowChanged.connect(self._on_nav)
        body_lay.addWidget(self._sidebar)

        # Stacked content
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_classifier_page())  # 0
        self._stack.addWidget(self._build_settings_page())    # 1
        self._stack.addWidget(self._build_keywords_page())    # 2
        self._stack.addWidget(self._build_about_page())       # 3
        body_lay.addWidget(self._stack, 1)

        root_lay.addWidget(body, 1)

        # Status bar
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._sb_files = QLabel("0 tệp")
        self._sb_ocr   = QLabel("OCR: none")
        self._sb_mode  = QLabel("Mode: copy")
        for lbl in (self._sb_files, self._sb_ocr, self._sb_mode):
            self._statusbar.addPermanentWidget(lbl)
        self._statusbar.showMessage("Sẵn sàng")

    def _build_toolbar(self) -> None:
        tb = QToolBar("Toolbar", self)
        tb.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, tb)

        def act(icon: str, text: str, slot) -> QAction:
            a = QAction(f"{icon}  {text}", self)
            a.triggered.connect(slot)
            tb.addAction(a)
            return a

        act("📂", "Mở tệp",      self._browse_files)
        act("📁", "Mở thư mục",  self._browse_directory)
        tb.addSeparator()
        act("🗑", "Xóa hàng chờ", self._clear_queue)
        tb.addSeparator()
        act("ℹ", "Giới thiệu",   self._show_about)

    def _build_classifier_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        # Dashboard cards
        self._dashboard = DashboardCards()
        lay.addWidget(self._dashboard)

        # Main area: drop/queue on left | right column on right
        splitter = QSplitter(Qt.Horizontal)

        # ── Left: drop area + queue ──
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)

        self._drop_area = DropArea()
        self._drop_area.files_dropped.connect(self._handle_dropped)
        self._drop_area.clicked.connect(self._browse_files)
        left_lay.addWidget(self._drop_area)

        # Queue label + search
        q_top = QHBoxLayout()
        qlbl = QLabel("Hàng chờ phân loại:")
        qlbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        q_top.addWidget(qlbl)
        q_top.addStretch()
        btn_add_f = QPushButton("+ File")
        btn_add_f.setObjectName("BtnSmall")
        btn_add_f.clicked.connect(self._browse_files)
        btn_add_d = QPushButton("+ Thư mục")
        btn_add_d.setObjectName("BtnSmall")
        btn_add_d.clicked.connect(self._browse_directory)
        btn_rm = QPushButton("Xóa chọn")
        btn_rm.setObjectName("BtnSmall")
        btn_rm.clicked.connect(self._remove_selected)
        btn_clr = QPushButton("Xóa tất cả")
        btn_clr.setObjectName("BtnSmall")
        btn_clr.clicked.connect(self._clear_queue)
        for b in (btn_add_f, btn_add_d, btn_rm, btn_clr):
            q_top.addWidget(b)
        left_lay.addLayout(q_top)

        self._queue_table = QueueTable()
        self._queue_table.remove_requested.connect(self._remove_rows)
        self._queue_table.clear_requested.connect(self._clear_queue)
        left_lay.addWidget(self._queue_table, 1)

        splitter.addWidget(left)

        # ── Right: progress + logs + start ──
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(12)

        self._progress = ProgressPanel()
        right_lay.addWidget(self._progress)

        self._log = LogWidget()
        right_lay.addWidget(self._log, 1)

        # Start / Open buttons
        self._btn_start = QPushButton("▶  BẮT ĐẦU PHÂN LOẠI")
        self._btn_start.setObjectName("BtnPrimary")
        self._btn_start.clicked.connect(self._toggle_classification)
        right_lay.addWidget(self._btn_start)

        self._btn_open = QPushButton("📂  Mở thư mục kết quả")
        self._btn_open.setObjectName("BtnSuccess")
        self._btn_open.setVisible(False)
        self._btn_open.clicked.connect(self._open_output_dir)
        right_lay.addWidget(self._btn_open)

        splitter.addWidget(right)
        splitter.setSizes([700, 420])
        lay.addWidget(splitter, 1)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 16, 20, 16)
        lbl = QLabel("⚙  Cài đặt phân loại")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        lay.addWidget(lbl)
        self._settings = SettingsPanel()
        self._settings.output_dir_changed.connect(self._on_output_dir_changed)
        lay.addWidget(self._settings)
        return page

    def _build_keywords_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 16, 20, 16)
        lbl = QLabel("📚  Quản lý Môn học & Từ khóa")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        lay.addWidget(lbl)
        self._kw_editor = KeywordEditor()
        lay.addWidget(self._kw_editor, 1)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(14)

        icon = QLabel("📄")
        icon.setStyleSheet("font-size: 72px;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        title = QLabel("Offline Vietnamese Document Sorter")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #89b4fa;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        ver = QLabel("GUI Edition — v2.0")
        ver.setStyleSheet("font-size: 13px; color: #a6adc8;")
        ver.setAlignment(Qt.AlignCenter)
        lay.addWidget(ver)

        desc = QLabel(
            "Phân loại tài liệu học tập Tiếng Việt theo môn học.\n"
            "Hoạt động hoàn toàn offline — Hỗ trợ PDF & DOCX.\n"
            "Sử dụng từ khóa có trọng số, nhận dạng không dấu, và regex."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cdd6f4; font-size: 13px; line-height: 1.6;")
        lay.addWidget(desc)
        lay.addStretch()
        return page

    # -----------------------------------------------------------------------
    # Navigation
    # -----------------------------------------------------------------------
    def _on_nav(self, row: int) -> None:
        self._stack.setCurrentIndex(row)

    def _show_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec_()

    # -----------------------------------------------------------------------
    # File management
    # -----------------------------------------------------------------------
    def _browse_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn tệp tài liệu", "", "Tài liệu (*.pdf *.docx)"
        )
        if files:
            self._add_paths(files)

    def _browse_directory(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục")
        if d:
            self._add_paths([d])

    def _handle_dropped(self, paths: list[str]) -> None:
        self._log_msg(f"[+] Kéo thả: {len(paths)} đường dẫn")
        self._add_paths(paths)

    def _add_paths(self, paths: list[str]) -> None:
        recursive = True
        try:
            recursive = self._settings.chk_recursive.isChecked()
        except Exception:
            pass

        to_add: list[Path] = []
        for p in paths:
            path = Path(p)
            if path.is_file() and path.suffix.lower() in (".pdf", ".docx"):
                to_add.append(path)
            elif path.is_dir():
                cfg = ClassificationConfig(include_pdf=True, include_docx=True, recursive=recursive)
                to_add.extend(discover_files(path, cfg))

        added = 0
        for fp in to_add:
            if fp not in self.files_queue:
                self.files_queue.append(fp)
                self._queue_table.add_file(fp)
                added += 1

        if added:
            self._log_msg(f"[+] Thêm {added} tệp. Hàng chờ: {len(self.files_queue)} tệp")
        else:
            self._log_msg("[-] Không có tệp PDF/DOCX mới.")
        self._update_dashboard()

    def _remove_selected(self) -> None:
        rows = self._queue_table.selected_rows()
        self._remove_rows(rows)

    def _remove_rows(self, rows: list[int]) -> None:
        for r in sorted(rows, reverse=True):
            if r < len(self.files_queue):
                self.files_queue.pop(r)
            self._queue_table.removeRow(r)
        self._log_msg(f"[-] Đã xóa {len(rows)} tệp. Còn lại: {len(self.files_queue)}")
        self._update_dashboard()

    def _clear_queue(self) -> None:
        self.files_queue.clear()
        self._queue_table.setRowCount(0)
        self._progress.reset()
        self._btn_open.setVisible(False)
        self._log_msg("[*] Đã xóa toàn bộ hàng chờ.")
        self._update_dashboard()

    def _update_dashboard(self) -> None:
        total_bytes = sum(
            p.stat().st_size for p in self.files_queue if p.exists()
        )
        try:
            out = self._settings.output_dir()
        except Exception:
            out = "outputs"
        self._dashboard.update_queue(len(self.files_queue), total_bytes, out)
        self._sb_files.setText(f"{len(self.files_queue)} tệp")

    def _on_output_dir_changed(self, _: str) -> None:
        self._update_dashboard()

    # -----------------------------------------------------------------------
    # Classification
    # -----------------------------------------------------------------------
    def _toggle_classification(self) -> None:
        if self.worker and self.worker.isRunning():
            self._log_msg("[!] Đang yêu cầu dừng…")
            self.worker.stop()
            self._btn_start.setEnabled(False)
            return

        if not self.files_queue:
            QMessageBox.warning(self, "Cảnh báo", "Hàng chờ trống. Thêm tệp trước khi phân loại.")
            return

        out_str = self._settings.output_dir()
        if not out_str:
            QMessageBox.warning(self, "Cảnh báo", "Chọn thư mục đầu ra trước.")
            return

        out_dir = Path(out_str)
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo thư mục:\n{e}")
            return

        excluded = () if self._settings.chk_dia_gdcd.isChecked() else ("Dia_ly", "GDCD")
        ocr_backend = self._settings.cmb_ocr.currentText()

        config = ClassificationConfig(
            dry_run=self._settings.chk_dry_run.isChecked(),
            copy=self._settings.rad_copy.isChecked(),
            overwrite=self._settings.chk_overwrite.isChecked(),
            recursive=self._settings.chk_recursive.isChecked(),
            ocr_backend=ocr_backend,
            enable_ocr=ocr_backend != "none" or self._settings.chk_accuracy.isChecked(),
            always_ocr_pdf=self._settings.chk_always_ocr.isChecked(),
            excluded_subjects=excluded,
        )
        if self._settings.chk_accuracy.isChecked():
            config = replace(
                config,
                max_pdf_pages=max(config.max_pdf_pages, 12),
                filename_fast_path_score=9999.0,
            )

        # Reset table statuses
        self._queue_table.reset_statuses()
        self._btn_open.setVisible(False)
        self._log.clear()

        self._log_msg(f"[*] Bắt đầu phân loại {len(self.files_queue)} tệp…")
        self._log_msg(f"[*] Đầu ra: {out_dir}")
        self._log_msg(f"[*] DryRun={config.dry_run} | Copy={config.copy} | OCR={config.ocr_backend}")

        self._set_ui_enabled(False)
        self._btn_start.setObjectName("BtnStop")
        self._btn_start.setText("⏹  DỪNG PHÂN LOẠI")
        self._btn_start.setEnabled(True)
        self.style().polish(self._btn_start)
        self._header.set_status("Đang phân loại…", busy=True)

        self._progress.start(len(self.files_queue))

        self.worker = ClassificationWorker(self.files_queue[:], out_dir, config)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.file_done.connect(self._on_file_done)
        self.worker.log_message.connect(self._log_msg)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_progress(self, current: int, total: int, filename: str) -> None:
        self._progress.update(current, filename)
        self._statusbar.showMessage(f"Đang xử lý ({current}/{total}): {filename}")

    def _on_file_done(self, filename: str, subject: str, score: float, action: str, row_idx: int) -> None:
        if subject == "Lỗi":
            status_key = "error"
            label = action[:30]
        elif subject in ("_Khong_xac_dinh", "_Can_kiem_tra"):
            status_key = "unknown"
            label = subject
        elif subject == "_Khong_phai_mon_hoc":
            status_key = "conflict"
            label = subject
        else:
            status_key = "done"
            label = subject
        self._queue_table.set_status(row_idx, status_key, label)

    def _on_finished(self, rows: list, elapsed: float) -> None:
        self._set_ui_enabled(True)
        self._btn_start.setObjectName("BtnPrimary")
        self._btn_start.setText("▶  BẮT ĐẦU PHÂN LOẠI")
        self._btn_start.setEnabled(True)
        self.style().polish(self._btn_start)
        self._header.set_status("Hoàn thành", busy=False)
        self._progress.finish(elapsed)

        # Summarise
        by_label: dict[str, int] = {}
        for cls, _ in rows:
            k = cls.target_label
            by_label[k] = by_label.get(k, 0) + 1

        self._log_msg("\n" + "=" * 50)
        self._log_msg("🏆 HOÀN THÀNH PHÂN LOẠI TÀI LIỆU")
        self._log_msg(f"⏱  Thời gian: {format_eta(elapsed)}")
        for label, count in sorted(by_label.items(), key=lambda x: -x[1]):
            self._log_msg(f"   {label}: {count} tệp")
        self._log_msg("=" * 50 + "\n")

        self._statusbar.showMessage(f"Hoàn thành {len(rows)} tệp trong {elapsed:.1f}s")

        if not self._settings.chk_dry_run.isChecked():
            self._btn_open.setVisible(True)
        self.worker = None

    def _set_ui_enabled(self, enabled: bool) -> None:
        self._settings.set_enabled_all(enabled)
        self._sidebar.setEnabled(enabled)
        self._drop_area.setEnabled(enabled)

    def _open_output_dir(self) -> None:
        open_directory(self._settings.output_dir())

    # -----------------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------------
    def _log_msg(self, msg: str) -> None:
        self._log.append(msg)

    # -----------------------------------------------------------------------
    # Keywords
    # -----------------------------------------------------------------------
    def _load_keywords(self) -> None:
        kw_file = Path("data/keywords.json")
        if not kw_file.exists():
            from docsorter.config import DATA_DIR
            kw_file = DATA_DIR / "keywords.json"
        self._kw_editor.load_from_file(kw_file)
=======
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
>>>>>>> 5b3bdbabfd60b865131af56e2475b81128580357
