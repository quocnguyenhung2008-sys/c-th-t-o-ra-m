from __future__ import annotations

import gc
from pathlib import Path
from typing import Any


class OcrUnavailableError(RuntimeError):
    pass


class PdfOcrEngine:
    def __init__(self):
        # Bộ đệm (Cache) lưu trữ các mô hình AI sau khi nạp vào GPU
        self._easyocr_reader: Any = None
        self._paddleocr_engine: Any = None
        self._system_torch_backup: Any = None

    def _get_easyocr_reader(self) -> Any:
        """Nạp EasyOCR vào GPU một lần duy nhất (Lazy Loading)"""
        if self._easyocr_reader is None:
            try:
                # Khôi phục module torch nếu trước đó bị PaddleOCR ẩn đi
                import sys
                if self._system_torch_backup and 'torch' in sys.modules and sys.modules['torch'] is None:
                    sys.modules['torch'] = self._system_torch_backup
                
                import easyocr  # type: ignore
            except ImportError as exc:
                raise OcrUnavailableError("easyocr is required for EasyOCR.") from exc
            
            # Kích hoạt GPU=True cho EasyOCR với cặp ngôn ngữ tối ưu cho THPT Việt Nam
            self._easyocr_reader = easyocr.Reader(["vi", "en"], gpu=True)
        return self._easyocr_reader

    def _get_paddleocr_engine(self) -> Any:
        """Nạp PaddleOCR 3.x và xử lý các lỗi xung đột hệ thống trên Windows"""
        if self._paddleocr_engine is None:
            try:
                # 1. Ép Python cô lập PyTorch để tránh lỗi shm.dll nhưng có sao lưu
                import sys
                if 'torch' in sys.modules and sys.modules['torch'] is not None:
                    self._system_torch_backup = sys.modules['torch']
                sys.modules['torch'] = None
                
                import paddle  # type: ignore
                
                # 2. MONKEY PATCH: Sửa lỗi thiếu thuộc tính set_optimization_level của Paddle Core trên Windows
                if hasattr(paddle, 'base') and hasattr(paddle.base, 'libpaddle') and hasattr(paddle.base.libpaddle, 'AnalysisConfig'):
                    cfg_cls = paddle.base.libpaddle.AnalysisConfig
                    if not hasattr(cfg_cls, 'set_optimization_level'):
                        cfg_cls.set_optimization_level = lambda self, level: None

                from paddleocr import PaddleOCR  # type: ignore
            except ImportError as exc:
                raise OcrUnavailableError("paddleocr is required for PaddleOCR.") from exc
            
            # Khởi tạo mô hình mượt mà
            self._paddleocr_engine = PaddleOCR(lang="vi")
            
        return self._paddleocr_engine

    def _render_pdf_pages(self, path: Path, page_indexes: list[int]) -> list[Any]:
        try:
            import fitz  # type: ignore
        except ImportError as exc:
            raise OcrUnavailableError("PyMuPDF is required to render PDF pages.") from exc

        images: list[Any] = []
        with fitz.open(str(path)) as document:
            for page_index in page_indexes:
                if 0 <= page_index < len(document):
                    page = document.load_page(page_index)
                    # TỐI ƯU ĐỘ PHÂN GIẢI: Matrix 2x2 tương đương 144 DPI là điểm ngọt (Sweet Spot)
                    # Giúp EasyOCR đọc chữ nhỏ trong bảng biểu đề thi rõ nét mà không làm tràn VRAM GPU.
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    images.append(pixmap)
        return images

    def ocr_with_easyocr(self, path: Path, page_indexes: list[int]) -> str:
        reader = self._get_easyocr_reader()
        parts: list[str] = []
        
        for pixmap in self._render_pdf_pages(path, page_indexes):
            image_bytes = pixmap.tobytes("png")
            
            # TỐI ƯU BỘ ĐỌC EASYOCR:
            # - Bỏ `paragraph=True` hoặc tinh chỉnh tham số chặn khoảng cách ranh giới.
            # - Thêm `decoder='greedy'` để tăng tốc độ phản hồi text thô của đề thi.
            bounds = reader.readtext(image_bytes, decoder='greedy', detail=1)
            
            # Sắp xếp các khối văn bản theo tọa độ từ trên xuống dưới, từ trái sang phải
            # Điều này ngăn chặn việc EasyOCR đọc lộn xộn các đáp án trắc nghiệm A, B, C, D dính vào nhau
            bounds.sort(key=lambda x: (x[0][0][1], x[0][0][0]))
            
            extracted_text = [text_res[1] for text_res in bounds if text_res[1]]
            parts.extend(extracted_text)
            
        # DỌN DẸP VRAM: Ép giải phóng bộ nhớ đệm ngay sau khi quét xong 1 file PDF nặng
        gc.collect()
        
        return "\n".join(parts)

    def ocr_with_paddleocr(self, path: Path, page_indexes: list[int]) -> str:
        try:
            import numpy as np  # type: ignore
        except ImportError as exc:
            raise OcrUnavailableError("numpy is required for PaddleOCR.") from exc

        engine = self._get_paddleocr_engine()
        parts: list[str] = []
        
        for pixmap in self._render_pdf_pages(path, page_indexes):
            img_np = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
                (pixmap.height, pixmap.width, 3)
            )
            
            result = engine.ocr(img_np, cls=True)
            for page_result in result or []:
                for line in page_result or []:
                    if len(line) >= 2 and line[1]:
                        parts.append(str(line[1][0]))
                        
        gc.collect()
        return "\n".join(parts)


# Khởi tạo một global instance duy nhất để các module khác gọi dùng chung.
_global_engine = PdfOcrEngine()


def ocr_pdf_pages(path: Path, page_indexes: list[int], backend: str) -> str:
    """Hàm interface giữ nguyên tên cũ để các module tầng trên không bị lỗi"""
    if backend == "none":
        raise OcrUnavailableError("OCR is disabled.")
    if backend == "easyocr":
        return _global_engine.ocr_with_easyocr(path, page_indexes)
    if backend == "paddleocr":
        return _global_engine.ocr_with_paddleocr(path, page_indexes)
    raise OcrUnavailableError(f"Unsupported OCR backend: {backend}")