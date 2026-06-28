import os

class DocumentClassifier:
    """
    LỚP GIAO TIẾP (BRIDGE): Giữ nguyên 100% thuật toán phân loại cũ.
    Bạn chỉ cần import pipeline, hàm tính điểm hoặc regex cũ vào đây.
    """
    @staticmethod
    def classify(file_path: str, options: dict) -> dict:
        # Giữ nguyên logic xử lý cũ của bạn tại đây:
        # score = calculate_regex_score(file_path)
        # label = get_subject_label(score)
        
        # Trả về cấu trúc Dictionary chuẩn hóa để đẩy ngược dữ liệu lên Main Thread GUI hiển thị
        filename = os.path.basename(file_path)
        return {
            "file_name": filename,
            "label": "Toán",
            "score": 92.5,
            "engine": "filename_regex",
            "ocr_used": False
        }