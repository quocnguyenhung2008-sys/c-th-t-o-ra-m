from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ocr_engine import OcrUnavailableError, ocr_pdf_pages
from .sampling import sampled_page_indexes


@dataclass(frozen=True)
class PdfExtractionResult:
    text: str
    pages_sampled: list[int]
    engine: str
    ocr_used: bool
    errors: list[str]


def extract_pdf_text(
    path: Path,
    max_pages: int,
    min_chars_before_ocr: int,
    enable_ocr: bool,
    always_ocr_pdf: bool,
    ocr_backend: str,
) -> PdfExtractionResult:
    errors: list[str] = []
    page_count = _get_page_count(path, errors)
    pages = sampled_page_indexes(page_count, max_pages)

    # ── Thứ tự engine: PyMuPDF trước — nhanh hơn pdfplumber 3–8× trên macOS ──
    # pdfplumber chính xác hơn cho bảng biểu nhưng chậm hơn đáng kể;
    # với mục đích phân loại từ khóa, PyMuPDF là đủ và nhanh hơn nhiều.
    for engine_name, extractor in (
        ("pymupdf", _extract_with_pymupdf),
        ("pdfplumber", _extract_with_pdfplumber),
        ("pypdf", _extract_with_pypdf),
    ):
        try:
            text = extractor(path, pages)
        except Exception as exc:
            errors.append(f"{engine_name}: {exc}")
            continue

        if len(text.strip()) >= min_chars_before_ocr:
            if enable_ocr and always_ocr_pdf:
                ocr_text, ocr_errors = _try_ocr(path, pages, ocr_backend)
                errors.extend(ocr_errors)
                if ocr_text.strip():
                    return PdfExtractionResult(
                        text=f"{text}\n{ocr_text}",
                        pages_sampled=pages,
                        engine=f"{engine_name}+{ocr_backend}",
                        ocr_used=True,
                        errors=errors,
                    )
            return PdfExtractionResult(text=text, pages_sampled=pages, engine=engine_name, ocr_used=False, errors=errors)

        errors.append(f"{engine_name}: extracted text too short ({len(text.strip())} chars)")

    if enable_ocr:
        text, ocr_errors = _try_ocr(path, pages, ocr_backend)
        errors.extend(ocr_errors)
        if text.strip():
            return PdfExtractionResult(text=text, pages_sampled=pages, engine=ocr_backend, ocr_used=True, errors=errors)

    return PdfExtractionResult(text="", pages_sampled=pages, engine="none", ocr_used=False, errors=errors)


def _try_ocr(path: Path, pages: list[int], ocr_backend: str) -> tuple[str, list[str]]:
    try:
        return ocr_pdf_pages(path, pages, ocr_backend), []
    except OcrUnavailableError as exc:
        return "", [f"ocr: {exc}"]


def _get_page_count(path: Path, errors: list[str]) -> int:
    # ── PyMuPDF trước để đếm trang — nhanh hơn và ít overhead hơn pypdf ──
    try:
        import fitz  # type: ignore
        with fitz.open(str(path)) as document:
            return document.page_count
    except Exception as exc:
        errors.append(f"page_count_pymupdf: {exc}")

    try:
        import pypdf  # type: ignore
        with path.open("rb") as file:
            return len(pypdf.PdfReader(file).pages)
    except Exception as exc:
        errors.append(f"page_count_pypdf: {exc}")

    return 0


def _extract_with_pymupdf(path: Path, pages: list[int]) -> str:
    import fitz  # type: ignore
    parts: list[str] = []
    with fitz.open(str(path)) as document:
        for page_index in pages:
            if page_index < document.page_count:
                # TEXT_DEHYPHENATE ghép từ bị ngắt dòng — quan trọng cho đề thi in 2 cột
                parts.append(document.load_page(page_index).get_text("text", flags=fitz.TEXT_DEHYPHENATE))
    return "\n".join(parts)


def _extract_with_pdfplumber(path: Path, pages: list[int]) -> str:
    import pdfplumber  # type: ignore
    parts: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_index in pages:
            if page_index < len(pdf.pages):
                parts.append(pdf.pages[page_index].extract_text() or "")
    return "\n".join(parts)


def _extract_with_pypdf(path: Path, pages: list[int]) -> str:
    import pypdf  # type: ignore
    parts: list[str] = []
    with path.open("rb") as file:
        reader = pypdf.PdfReader(file)
        for page_index in pages:
            if page_index < len(reader.pages):
                parts.append(reader.pages[page_index].extract_text() or "")
    return "\n".join(parts)