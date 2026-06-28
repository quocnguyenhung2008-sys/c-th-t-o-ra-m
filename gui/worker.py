"""Background classification worker thread."""
from __future__ import annotations

import time
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal

from docsorter.config import ClassificationConfig
from docsorter.classifier import DocumentClassifier, ClassificationStatus
from docsorter.file_ops import place_file


class ClassificationWorker(QThread):
    progress_updated = pyqtSignal(int, int, str)       # current, total, filename
    file_done = pyqtSignal(str, str, float, str, int)  # filename, subject, score, action, row_idx
    log_message = pyqtSignal(str)
    finished = pyqtSignal(list, float)                 # rows, elapsed_seconds

    def __init__(self, files: list[Path], output_dir: Path, config: ClassificationConfig) -> None:
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.config = config
        self.is_running = True

    def run(self) -> None:
        t0 = time.perf_counter()
        classifier = DocumentClassifier(self.config)
        rows = []
        total = len(self.files)

        for idx, file_path in enumerate(self.files):
            if not self.is_running:
                break
            self.progress_updated.emit(idx + 1, total, file_path.name)
            try:
                classification = classifier.classify(file_path)
                if self.config.dry_run:
                    from docsorter.file_ops import MoveResult
                    dest = self.output_dir / classification.target_label / file_path.name
                    move_result = MoveResult(file_path, dest, "dry-run")
                else:
                    move_result = place_file(classification, self.output_dir, self.config)
                rows.append((classification, move_result))
                self.file_done.emit(
                    file_path.name,
                    classification.target_label,
                    classification.score,
                    move_result.action,
                    idx,
                )
            except Exception as e:
                self.log_message.emit(f"[-] Lỗi '{file_path.name}': {e}")
                self.file_done.emit(file_path.name, "Lỗi", 0.0, str(e), idx)

        # Write CSV report
        if not self.config.dry_run and rows:
            try:
                from docsorter.report import write_report
                report_path = self.output_dir / self.config.report_name
                write_report(report_path, rows)
                self.log_message.emit(f"[+] Báo cáo lưu tại: {report_path}")
            except Exception as e:
                self.log_message.emit(f"[-] Lỗi ghi báo cáo: {e}")

        elapsed = time.perf_counter() - t0
        self.finished.emit(rows, elapsed)

    def stop(self) -> None:
        self.is_running = False
