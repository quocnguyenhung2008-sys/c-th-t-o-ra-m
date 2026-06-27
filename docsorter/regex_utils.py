from __future__ import annotations

import re
import unicodedata

from .normalize import strip_vietnamese_accents


# Tối ưu Tokenizer: Nhận diện token chữ bao gồm cả tiếng Việt có dấu một cách chính xác
_TOKEN_RE = re.compile(r"[a-zA-Z0-9àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]+", re.UNICODE)

_VIETNAMESE_DIACRITIC_RE = re.compile(
    r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệ"
    r"ìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
    r"ùúủũụưừứửữựỳýỷỹỵđ"
    r"ÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆ"
    r"ÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢ"
    r"ÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ]"
)


def normalize_vietnamese_unicode(text: str) -> str:
    """
    Chuẩn hóa toàn bộ chuỗi về dạng Unicode Dựng Sẵn (NFC).
    Giải quyết triệt để lỗi PaddleOCR trả về Unicode tổ hợp khiến Regex không khớp từ khóa.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


def keyword_to_regex(keyword: str) -> re.Pattern[str]:
    """Tạo Regex tối ưu cho từ khóa không dấu, chấp nhận nhiễu khoảng trắng từ OCR."""
    cleaned = strip_vietnamese_accents(normalize_vietnamese_unicode(keyword.lower()))
    return compile_keyword_regex(cleaned)


def keyword_to_accented_regex(keyword: str) -> re.Pattern[str]:
    """Tạo Regex tối ưu cho từ khóa có dấu, bảo toàn cấu trúc dấu chuẩn hóa NFC."""
    cleaned = normalize_vietnamese_unicode(keyword.lower())
    return compile_keyword_regex(cleaned)


def compile_keyword_regex(keyword: str) -> re.Pattern[str]:
    # Chuẩn hóa từ khóa trước khi trích xuất token
    keyword = normalize_vietnamese_unicode(keyword)
    tokens = _TOKEN_RE.findall(keyword)
    
    if not tokens:
        return re.compile(r"a\Ab")
    
    # NÂNG CẤP SIÊU QUAN TRỌNG: 
    # Thay vì dùng [\s\-_...]+ (bắt buộc phải có khoảng trắng), chuyển sang [\s\-_.,;:/\\(){}\[\]<>|*]* # Dấu * cho phép khớp cả khi OCR đọc dính chữ vào nhau HOẶC cho phép dấu cách linh hoạt giữa các token.
    separator = r"[\s\-_.,;:/\\(){}\[\]<>|*]*"
    
    # Cho phép OCR bị lỗi chèn khoảng trắng rời rạc bên trong từng token (ví dụ: "t o á n")
    token_patterns = []
    for token in tokens:
        # Tách nhỏ từng chữ cái trong 1 token và cho phép cách nhau bằng khoảng trắng tùy chọn (0 hoặc nhiều)
        spaced_token = r"\s*".join(re.escape(char) for char in token)
        token_patterns.append(spaced_token)
        
    pattern = separator.join(token_patterns)
    
    # SỬA LỖI WORD BOUNDARY CHO TIẾNG VIỆT:
    # (?<!\w) thông thường sẽ hoạt động sai với ký tự Unicode có dấu.
    # Sử dụng Lookbehind/Lookahead phủ định bằng tập ký tự tường minh giúp nhận diện chính xác ranh giới từ.
    vietnamese_chars = r"a-zA-Z0-9àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ"
    
    return re.compile(rf"(?<![{vietnamese_chars}]){pattern}(?![{vietnamese_chars}])", re.IGNORECASE | re.UNICODE)


def has_vietnamese_diacritics(text: str) -> bool:
    if not text:
        return False
    return bool(_VIETNAMESE_DIACRITIC_RE.search(normalize_vietnamese_unicode(text)))