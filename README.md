# Offline Vietnamese THPT Document Sorter

Cong cu phan loai file `.docx` va `.pdf` theo mon hoc THPT Viet Nam bang tu khoa tinh, chay offline tren macOS, khong can API va khong ton phi su dung.

## Tinh nang chinh

- Phan loai: Toan, Vat ly, Hoa hoc, Sinh hoc, Ngu van, Lich su, Dia ly, Tieng Anh, Tin hoc, GDCD.
- Ho tro DOCX va PDF.
- Uu tien ten file bang he so rieng de phan loai nhanh va tot hon.
- PDF nang khong bi quet het: mac dinh lay mau trang dau, giua, cuoi.
- Neu ten file da du chac chan, cong cu phan loai ngay va khong mo file PDF nang.
- Ten file la ten mon hoac viet tat nhu `Anh`, `TA`, `Hoa`, `Sinh`, `Van`, `Su`, `Dia`, `Tin`, `GDCD` duoc nhan dien bang `data/aliases.json`.
- Mac dinh khong phan loai `Dia_ly` va `GDCD` theo yeu cau hien tai. Dung `--include-dia-gdcd` neu muon bat lai.
- Alias ngan trong filename chi duoc tinh khi dung nhu ten mon ro rang. Vi du `Pham Van Trong.pdf` khong bi nham thanh `Ngu_van`, con `Van 12.pdf` van duoc nhan dien.
- PDF extraction nhieu lop: `pdfplumber` -> `PyMuPDF` -> `pypdf`.
- OCR tuy chon cho PDF scan bang EasyOCR hoac PaddleOCR.
- Tu khoa co trong so, match bang regex, ho tro dau gach noi, dau cau, nhieu khoang trang va van ban khong dau.
- File khong ro mon hoc vao `_Khong_xac_dinh`.
- File co dau hieu khong phai tai lieu mon hoc vao `_Khong_phai_mon_hoc`.
- File bi gan diem qua sat nhau vao `_Can_kiem_tra`.
- Xuat bao cao CSV.

## Cai dat

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

OCR la tuy chon va co the nang. Neu can OCR:

```bash
pip install easyocr pillow
```

hoac:

```bash
pip install paddleocr pillow numpy
```

## Su dung

Copy file vao thu muc dich, khong lam thay doi thu muc goc:

```bash
python main.py "/duong/dan/tai-lieu" "/duong/dan/da-phan-loai" --copy
```

Xem thu ket qua truoc khi chay that:

```bash
python main.py "/duong/dan/tai-lieu" "/duong/dan/da-phan-loai" --dry-run
```

Quet ca thu muc con:

```bash
python main.py "/duong/dan/tai-lieu" "/duong/dan/da-phan-loai" --copy --recursive
```

Bat OCR cho PDF scan:

```bash
python main.py "/duong/dan/tai-lieu" "/duong/dan/da-phan-loai" --copy --enable-ocr --ocr-backend easyocr
```

Che do uu tien do chinh xac hon toc do, doc nhieu trang PDF hon va OCR cac trang da lay mau:

```bash
python main.py "/duong/dan/tai-lieu" "/duong/dan/da-phan-loai" --copy --recursive --accuracy-mode --ocr-backend easyocr --always-ocr
```

Giam/tang so trang PDF lay mau:

```bash
python main.py "/duong/dan/tai-lieu" "/duong/dan/da-phan-loai" --copy --max-pdf-pages 8
```

Neu ten file cua ban rat chuan, co the giam nguong fast path de xu ly PDF nang nhanh hon:

```bash
python main.py "/duong/dan/tai-lieu" "/duong/dan/da-phan-loai" --copy --filename-fast-path-score 15
```

## Mo rong tu khoa

Sua `data/keywords.json`. Moi mon la mot danh sach rule:

```json
{
  "Toan": [
    {"keyword": "dao ham", "weight": 10},
    {"keyword": "nguyen ham", "weight": 10}
  ]
}
```

Tu khoa cang dac trung thi weight cang cao. Vi du `dao ham` nen cao hon `phuong trinh`, vi `phuong trinh` co the xuat hien trong Vat ly/Hoa hoc.

Sua `data/negative_keywords.json` de nhan dien file hanh chinh, hop dong, hoa don, bang luong... khong phai tai lieu mon hoc.

Sua `data/aliases.json` de bo sung cach goi ten mon trong ten file. Alias chi ap dung cho ten file, khong ap dung cho noi dung, de tranh truong hop tu ngan nhu `anh`, `van`, `su` lam lech ket qua.

Tu khoa trong `data/keywords.json` da duoc mo rong theo cac mach noi dung cua Chuong trinh GDPT 2018 cho cac mon dang bat: Toan, Vat ly, Hoa hoc, Sinh hoc, Ngu van, Tieng Anh, Tin hoc, Lich su.

## Ghi chu ve PDF nang

Cong cu khong doc toan bo PDF theo mac dinh. No lay mau theo thu tu:

- trang 1
- trang 2
- trang giua
- trang giua + 1
- trang gan cuoi
- trang cuoi

Cach nay tranh truong hop bia/muc luc khong co noi dung mon hoc, nhung van giu thoi gian xu ly thap.
