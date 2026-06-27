from __future__ import annotations

from pathlib import Path


class OcrUnavailableError(RuntimeError):
    pass


def ocr_pdf_pages(path: Path, page_indexes: list[int], backend: str) -> str:
    if backend == "none":
        raise OcrUnavailableError("OCR is disabled.")
    if backend == "easyocr":
        return _ocr_with_easyocr(path, page_indexes)
    if backend == "paddleocr":
        return _ocr_with_paddleocr(path, page_indexes)
    raise OcrUnavailableError(f"Unsupported OCR backend: {backend}")


def _render_pdf_pages(path: Path, page_indexes: list[int]) -> list[object]:
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise OcrUnavailableError("PyMuPDF is required to render PDF pages for OCR.") from exc

    images: list[object] = []
    with fitz.open(str(path)) as document:
        for page_index in page_indexes:
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            images.append(pixmap)
    return images


def _ocr_with_easyocr(path: Path, page_indexes: list[int]) -> str:
    try:
        import easyocr  # type: ignore
        from PIL import Image  # type: ignore
        import io
    except ImportError as exc:
        raise OcrUnavailableError("easyocr and pillow are required for EasyOCR.") from exc

    reader = easyocr.Reader(["vi", "en"], gpu=False)
    parts: list[str] = []
    for pixmap in _render_pdf_pages(path, page_indexes):
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
        parts.extend(reader.readtext(image, detail=0, paragraph=True))
    return "\n".join(parts)


def _ocr_with_paddleocr(path: Path, page_indexes: list[int]) -> str:
    try:
        from paddleocr import PaddleOCR  # type: ignore
        from PIL import Image  # type: ignore
        import io
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise OcrUnavailableError("paddleocr, pillow, and numpy are required for PaddleOCR.") from exc

    engine = PaddleOCR(use_angle_cls=True, lang="vi")
    parts: list[str] = []
    for pixmap in _render_pdf_pages(path, page_indexes):
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
        result = engine.ocr(np.array(image), cls=True)
        for page_result in result or []:
            for line in page_result or []:
                if len(line) >= 2 and line[1]:
                    parts.append(str(line[1][0]))
    return "\n".join(parts)
