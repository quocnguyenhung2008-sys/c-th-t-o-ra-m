from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from docsorter.classifier import DocumentClassifier
from docsorter.config import ClassificationConfig
from docsorter.file_ops import discover_files, place_file
from docsorter.report import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Phan loai tai lieu THPT Viet Nam .docx/.pdf hoan toan offline bang tu khoa tinh."
    )
    parser.add_argument("input_dir", type=Path, help="Thu muc chua file can phan loai.")
    parser.add_argument("output_dir", type=Path, help="Thu muc dich de tao cac thu muc mon hoc.")
    parser.add_argument("--copy", action="store_true", help="Copy file thay vi di chuyen.")
    parser.add_argument("--dry-run", action="store_true", help="Chi xem ket qua du kien, khong tao/copy/move file.")
    parser.add_argument("--overwrite", action="store_true", help="Ghi de file da ton tai trong thu muc dich.")
    parser.add_argument("--recursive", action="store_true", help="Quet ca thu muc con.")
    parser.add_argument(
        "--accuracy-mode",
        action="store_true",
        help="Uu tien do chinh xac: doc nhieu trang PDF hon, tat fast path ten file, va bat OCR neu chon backend.",
    )
    parser.add_argument("--no-pdf", action="store_true", help="Khong xu ly PDF.")
    parser.add_argument("--no-docx", action="store_true", help="Khong xu ly DOCX.")
    parser.add_argument("--max-pdf-pages", type=int, default=6, help="So trang PDF lay mau toi da.")
    parser.add_argument("--min-score", type=float, default=8.0, help="Diem toi thieu de chap nhan mot mon.")
    parser.add_argument("--min-margin", type=float, default=3.0, help="Khoang cach diem toi thieu voi mon dung thu hai.")
    parser.add_argument("--filename-weight", type=float, default=2.5, help="He so uu tien tu khoa trong ten file.")
    parser.add_argument("--body-weight", type=float, default=1.0, help="He so tu khoa trong noi dung file.")
    parser.add_argument(
        "--filename-alias-weight",
        type=float,
        default=12.0,
        help="Diem co so cho alias ten mon trong ten file, vi du Anh, TA, Hoa, Sinh.",
    )
    parser.add_argument(
        "--filename-fast-path-score",
        type=float,
        default=22.0,
        help="Neu ten file dat diem nay va khong bi tranh chap, bo qua doc noi dung de tiet kiem thoi gian.",
    )
    parser.add_argument("--enable-ocr", action="store_true", help="Bat OCR cho PDF scan neu engine text that bai.")
    parser.add_argument(
        "--always-ocr",
        action="store_true",
        help="OCR cac trang PDF da lay mau va ghep voi text trich xuat de tang do chinh xac.",
    )
    parser.add_argument(
        "--ocr-backend",
        choices=["none", "easyocr", "paddleocr"],
        default="none",
        help="Backend OCR tuy chon. Mac dinh tat de khong cai them goi nang.",
    )
    parser.add_argument(
        "--no-ocr-retry-unknown",
        action="store_true",
        help="Khong OCR lai PDF roi vao _Khong_xac_dinh. Mac dinh se thu lai neu da chon OCR backend.",
    )
    parser.add_argument("--keywords", type=Path, default=None, help="Duong dan keywords.json tuy chinh.")
    parser.add_argument("--negative-keywords", type=Path, default=None, help="Duong dan negative_keywords.json tuy chinh.")
    parser.add_argument("--aliases", type=Path, default=None, help="Duong dan aliases.json tuy chinh cho ten file.")
    parser.add_argument(
        "--include-dia-gdcd",
        action="store_true",
        help="Bat lai phan loai Dia_ly va GDCD. Mac dinh tat theo yeu cau hien tai.",
    )
    parser.add_argument(
        "--exclude-subject",
        action="append",
        default=[],
        help="Loai mot mon khoi ket qua, vi du --exclude-subject Dia_ly. Co the dung nhieu lan.",
    )
    parser.add_argument("--report-name", default="classification_report.csv", help="Ten file bao cao CSV.")
    return parser


def config_from_args(args: argparse.Namespace) -> ClassificationConfig:
    config = ClassificationConfig()
    excluded_subjects = tuple(args.exclude_subject) if args.include_dia_gdcd else tuple(
        dict.fromkeys((*config.excluded_subjects, *args.exclude_subject))
    )
    max_pdf_pages = args.max_pdf_pages
    filename_fast_path_score = args.filename_fast_path_score
    enable_ocr = args.enable_ocr
    always_ocr_pdf = args.always_ocr
    if args.accuracy_mode:
        max_pdf_pages = max(max_pdf_pages, 12)
        filename_fast_path_score = max(filename_fast_path_score, 9999.0)
        enable_ocr = args.enable_ocr or args.ocr_backend != "none"
        always_ocr_pdf = args.always_ocr or args.ocr_backend != "none"
    return replace(
        config,
        keywords_path=args.keywords or config.keywords_path,
        negative_keywords_path=args.negative_keywords or config.negative_keywords_path,
        aliases_path=args.aliases or config.aliases_path,
        dry_run=args.dry_run,
        copy=args.copy,
        overwrite=args.overwrite,
        recursive=args.recursive,
        include_pdf=not args.no_pdf,
        include_docx=not args.no_docx,
        max_pdf_pages=max_pdf_pages,
        min_score=args.min_score,
        min_margin=args.min_margin,
        filename_weight_multiplier=args.filename_weight,
        body_weight_multiplier=args.body_weight,
        filename_alias_weight=args.filename_alias_weight,
        filename_fast_path_score=filename_fast_path_score,
        enable_ocr=enable_ocr,
        always_ocr_pdf=always_ocr_pdf,
        retry_unknown_with_ocr=not args.no_ocr_retry_unknown,
        ocr_backend=args.ocr_backend,
        excluded_subjects=excluded_subjects,
        report_name=args.report_name,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = config_from_args(args)

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        parser.error(f"Input directory does not exist: {input_dir}")

    # TỐI ƯU HIỂN THỊ: Kiểm tra và thông báo trạng thái phần cứng lúc khởi động app
    if config.ocr_backend != "none":
        print(f"[*] OCR Backend đang chọn: {config.ocr_backend.upper()}")
        try:
            if config.ocr_backend == "easyocr":
                import torch
                if torch.cuda.is_available():
                    print(f"[+] Đã kích hoạt tăng tốc phần cứng GPU: {torch.cuda.get_device_name(0)}")
                else:
                    print("[-] CẢNH BÁO: Không tìm thấy GPU CUDA thích hợp. Hệ thống sẽ chạy chậm bằng CPU.")
            elif config.ocr_backend == "paddleocr":
                import paddle
                if paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
                    print("[+] Đã kích hoạt tăng tốc phần cứng GPU thành công cho PaddleOCR.")
                else:
                    print("[-] CẢNH BÁO: PaddlePaddle chưa kích hoạt CUDA. Hệ thống sẽ chạy chậm bằng CPU.")
        except ImportError:
            print("[!] Thư viện OCR chưa được cài đặt hoàn chỉnh.")

    classifier = DocumentClassifier(config)
    rows = []
    files = discover_files(input_dir, config, exclude_roots=(output_dir,))
    
    # Bắt đầu vòng lặp quét qua danh sách file
    for path in files:
        classification = classifier.classify(path)
        move_result = place_file(classification, output_dir, config)
        rows.append((classification, move_result))
        print(
            f"{path.name} -> {classification.target_label} "
            f"({classification.status.value}, score={classification.score:.1f}, action={move_result.action})"
        )

    report_path = output_dir / config.report_name
    if not config.dry_run:
        write_report(report_path, rows)
        print(f"Report: {report_path}")
    else:
        print(f"Dry run complete. {len(rows)} files evaluated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())