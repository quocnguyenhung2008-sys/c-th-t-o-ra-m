from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
_LINEBREAK_RE = re.compile(r"\n{3,}")

# MỞ RỘNG: Thay thế các ký tự nhiễu toán học và dấu đặc biệt phổ biến trong đề thi THPT
_PUNCTUATION_REPLACEMENTS = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",  # Dấu trừ toán học
        "\u00a0": " ",  # Non-breaking space
        "\u200b": "",   # Zero-width space
        "\ufeff": "",   # Byte order mark
        "–": "-",
        "—": "-",
        "―": "-",
        "．": ".",
        "，": ",",
    }
)

# TỐI ƯU SIÊU QUAN TRỌNG: Sửa lỗi Word Boundary (\b) không nhận diện được hỗn hợp Chữ-Số.
# Giúp sửa sai lỗi OCR phổ biến: c02 -> co2, h2s04 -> h2so4, lớp l0 -> lớp 10, vên l2 -> vên 12
_OCR_REPLACEMENTS = (
    # Sửa số 0 thành chữ o trong công thức hóa học (ví dụ: c02, h2s04, o2)
    (re.compile(r"(?<=[a-zA-Z])0(?=\d)"), "o"),
    (re.compile(r"(?<=\d)0(?=[a-zA-Z])"), "o"),
    (re.compile(r"(?<=[a-zA-Z])0(?=[a-zA-Z])"), "o"),
    # Sửa chữ l/i thành số 1 trong tên lớp hoặc năm học (ví dụ: l0 -> 10, l1 -> 11, l2 -> 12)
    (re.compile(r"(?<=[a-zA-Z])l(?=\d)"), "1"),
    (re.compile(r"\bl(?=\d)"), "1"),
    (re.compile(r"(?<=\d)l\b"), "1"),
    (re.compile(r"\bi(?=\d)"), "1"),
)


@dataclass(frozen=True)
class NormalizedText:
    original: str
    normalized: str
    accentless: str


def strip_vietnamese_accents(text: str) -> str:
    """
    Gỡ bỏ hoàn toàn dấu tiếng Việt một cách triệt để nhất.
    Đảm bảo xử lý đúng cả chữ đ/Đ bất kể cấu trúc bảng mã Unicode nào.
    """
    if not text:
        return ""
    
    # Ép chuỗi về dạng NFD để tách các dấu thanh (Mn) ra khỏi chữ cái gốc
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    
    # Thay thế thủ công ký tự đ/Đ đặc trưng của tiếng Việt (hỗ trợ cả dạng đã dựng sẵn hoặc tổ hợp)
    # Thực hiện thay thế trên cả chữ hoa lẫn chữ thường để an toàn tuyệt đối
    stripped = stripped.replace("đ", "d").replace("Đ", "D")
    stripped = stripped.replace("\u0111", "d").replace("\u0110", "D")  # Unicode khối của đ/Đ
    
    return stripped


def normalize_text(text: str) -> NormalizedText:
    original = text or ""
    
    # 1. Đưa về dạng Unicode Dựng Sẵn chuẩn (NFC) ngay từ đầu để đồng bộ dữ liệu
    normalized = unicodedata.normalize("NFC", original)
    
    # 2. Thay thế dấu punctuation nhiễu
    normalized = normalized.translate(_PUNCTUATION_REPLACEMENTS)
    
    # 3. Hạ font chữ thường trước khi áp dụng bộ lọc sửa lỗi OCR
    normalized = normalized.lower()
    
    # 4. Áp dụng bộ lọc OCR sửa lỗi Chữ-Số hỗn hợp nâng cấp
    for pattern, replacement in _OCR_REPLACEMENTS:
        normalized = pattern.sub(replacement, normalized)
        
    # 5. Dọn dẹp khoảng trắng thừa và dòng trống liên tiếp
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    normalized = _LINEBREAK_RE.sub("\n\n", normalized).strip()
    
    # 6. Tạo phiên bản không dấu phục vụ so khớp alias/tên file không dấu
    accentless = strip_vietnamese_accents(normalized)
    
    return NormalizedText(original=original, normalized=normalized, accentless=accentless)