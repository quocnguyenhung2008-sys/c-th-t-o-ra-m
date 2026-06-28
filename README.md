# Offline Vietnamese THPT Document Sorter

Công cụ phân loại file `.docx` và `.pdf` theo môn học THPT Việt Nam bằng từ khóa tĩnh, chạy offline trên macOS, không cần API và không tốn phí sử dụng.

## Tính năng chính

- Phân loại: Toán, Vật lý, Hóa học, Sinh học, Ngữ văn, Lịch sử, Địa lý, Tiếng Anh, Tin học, GDCD.
- Hỗ trợ DOCX và PDF.
- Ưu tiên tên file bằng hệ số riêng để phân loại nhanh và tốt hơn.
- PDF nặng không bị quét hết: mặc định lấy mẫu trang đầu, giữa, cuối.
- Nếu tên file đã đủ chắc chắn, công cụ phân loại ngay và không mở file PDF nặng.
- Tên file là tên môn hoặc viết tắt như `Anh`, `TA`, `Hóa`, `Sinh`, `Văn`, `Sử`, `Địa`, `Tin`, `GDCD` được nhận diện bằng `data/aliases.json`.
- Mặc định không phân loại `Địa_lý` và `GDCD` theo yêu cầu hiện tại. Dùng `--include-dia-gdcd` nếu muốn bật lại.
- Alias ngắn trong filename chỉ được tính khi dùng như tên môn rõ ràng. Ví dụ `Pham Van Trong.pdf` không bị nhầm thành `Ngữ_văn`, còn `Van 12.pdf` vẫn được nhận diện.
- PDF extraction nhiều lớp: `pdfplumber` -> `PyMuPDF` -> `pypdf`.
- OCR tùy chọn cho PDF scan bằng EasyOCR hoặc PaddleOCR.
- PDF rơi vào `_Không_xác_định` sẽ được OCR thử lại một lần nếu đã chọn `--ocr-backend`.
- Từ khóa có trọng số, match bằng regex, hỗ trợ dấu gạch nối, dấu câu, nhiều khoảng trắng và văn bản không dấu.
- Matcher ưu tiên tiếng Việt có dấu khi văn bản có dấu, chỉ fallback không dấu khi an toàn. Các từ đơn dễ nhiễu như `van`, `ly`, `hoa`, `tin`, `su`, `tuong` bị chặn nếu thiếu ngữ cảnh.
- File không rõ môn học vào `_Không_xác_định`.
- File có dấu hiệu không phải tài liệu môn học vào `_Không_phải_môn_học`.
- File bị gán điểm quá sát nhau vào `_Cần_kiểm_tra`.
- Xuất báo cáo CSV.

## Cài đặt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

OCR là tùy chọn và có thể nặng. Nếu cần OCR:

```bash
pip install easyocr pillow
```

hoặc:

```bash
pip install paddleocr pillow numpy
```

## Sử dụng

Copy file vào thư mục đích, không làm thay đổi thư mục gốc:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --copy
```

Xem thử kết quả trước khi chạy thật:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --dry-run
```

Quét cả thư mục con:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --copy --recursive
```

Bật OCR cho PDF scan:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --copy --enable-ocr --ocr-backend easyocr
```

Chỉ OCR lại các PDF chưa xác định được sau lượt đọc text thường:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --copy --ocr-backend easyocr
```

Chế độ ưu tiên độ chính xác hơn tốc độ, đọc nhiều trang PDF hơn và OCR các trang đã lấy mẫu:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --copy --recursive --accuracy-mode --ocr-backend easyocr --always-ocr
```

Giảm/tăng số trang PDF lấy mẫu:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --copy --max-pdf-pages 8
```

Nếu tên file của bạn rất chuẩn, có thể giảm ngưỡng fast path để xử lý PDF nặng nhanh hơn:

```bash
python main.py "/đường/dẫn/tài-liệu" "/đường/dẫn/đã-phân-loại" --copy --filename-fast-path-score 15
```

## Mở rộng từ khóa

Sửa `data/keywords.json`. Mỗi môn là một danh sách rule:

```json
{
  "Toán": [
    {"keyword": "đạo hàm", "weight": 10},
    {"keyword": "nguyên hàm", "weight": 10}
  ]
}
```

Từ khóa càng đặc trưng thì weight càng cao. Ví dụ `đạo hàm` nên cao hơn `phương trình`, vì `phương trình` có thể xuất hiện trong Vật lý/Hóa học.

Sửa `data/negative_keywords.json` để nhận diện file hành chính, hợp đồng, hóa đơn, bảng lương... không phải tài liệu môn học.

Sửa `data/aliases.json` để bổ sung cách gọi tên môn trong tên file. Alias chỉ áp dụng cho tên file, không áp dụng cho nội dung, để tránh trường hợp từ ngắn như `anh`, `văn`, `sử` làm lệch kết quả.

Từ khóa trong `data/keywords.json` đã được mở rộng theo các mạch nội dung của Chương trình GDPT 2018 cho các môn đang bật: Toán, Vật lý, Hóa học, Sinh học, Ngữ văn, Tiếng Anh, Tin học, Lịch sử.

Nên thêm keyword bằng tiếng Việt có dấu khi có thể. Ví dụ thêm `tuồng` thay vì chỉ thêm `tuong`; engine sẽ khớp `tuồng` với Ngữ văn nhưng không khớp nhầm `ý tưởng`, `tương tác`, hay `đối tượng`.

## Ghi chú về PDF nặng

Công cụ không đọc toàn bộ PDF theo mặc định. Nó lấy mẫu theo thứ tự:

- trang 1
- trang 2
- trang giữa
- trang giữa + 1
- trang gần cuối
- trang cuối

Cách này tránh trường hợp bìa/mục lục không có nội dung môn học, nhưng vẫn giữ thời gian xử lý thấp.

| Filename                                            | Được phân loại | Nhận xét                                                                |
| --------------------------------------------------- | -------------- | ----------------------------------------------------------------------- |
| `10. HĐ PHÍ MG.docx`                                | Toán           | Đây có vẻ là hợp đồng, không phải tài liệu Toán.                        |
| `2 DS niem yet THPT hoan chinh 2023 2024 Ct.pdf`    | Ngữ văn        | Danh sách niêm yết, không phải Ngữ văn.                                 |
| `2022_2023 KQ HSG cap tinh THCS khoa 01_3_2023.pdf` | Tiếng Anh      | Là kết quả kỳ thi HSG, không thể suy ra Tiếng Anh từ tên file.          |
| `2024 2025_KQ thi chon doi tuyen.pdf`               | Hóa học        | Kết quả chọn đội tuyển, không phải tài liệu Hóa học.                    |
| `20_11.docx`                                        | Lịch sử        | Tên quá chung, không đủ căn cứ.                                         |
| `30. VB TỪ CHỐI QUYỀN ƯU TIÊN MUA NHÀ...docx`        | Ngữ văn        | Đây là văn bản pháp lý.                                                 |
| `BỘ GIÁO DỤC VÀ ĐÀO TẠO.docx`                        | Tiếng Anh      | Khả năng rất thấp là tài liệu Tiếng Anh.                                |
| `GCN Nguyễn Quốc Đạt.pdf`                           | Toán           | Giấy chứng nhận, không phải Toán.                                       |
| `Hệ thống tuyển sinh trực tuyến (1).pdf`            | Ngữ văn        | Không phải tài liệu môn học.                                            |
| `NGUYỄN QUỐC ĐẠT.pdf`                               | Ngữ văn        | Tên cá nhân, khó liên quan Ngữ văn.                                     |
| `OLP23 Solution Khối Không chuyên.pdf`              | Lịch sử        | "Solution" thường là lời giải Olympic, khả năng cao không phải Lịch sử. |
| `PHIẾU ĐĂNG KÝ DỰ THI.pdf`                           | Toán           | Biểu mẫu hành chính.                                                    |
| `Sa01-HKD.pdf`                                      | Hóa học        | Tên file không liên quan Hóa học.                                       |