from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
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

    # === macOS / Apple Silicon optimization ===
    _default_workers = max(1, (os.cpu_count() or 4) - 1)
    parser.add_argument(
        "--workers",
        type=int,
        default=_default_workers,
        help=f"So worker song song (mac dinh: {_default_workers}). Apple M-series co the tang len 8+.",
    )
    parser.add_argument(
        "--no-parallel",
        action="store_true",
        help="Tat xu ly song song. Dung khi debug hoac OCR backend co xung dot.",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Hien thi tien trinh don gian khi xu ly nhieu file.",
    )
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


<<<<<<< HEAD
def _detect_hardware_info(ocr_backend: str) -> str:
    """Phát hiện GPU/MPS/CPU và trả về chuỗi mô tả để log. Hỗ trợ Apple Silicon MPS."""
    if ocr_backend == "none":
        return ""
    try:
        import torch
        if torch.backends.mps.is_available():
            # Apple Silicon M-series: dùng Metal Performance Shaders thay CUDA
            return f"[+] Apple Silicon MPS (Metal) sẵn sàng cho EasyOCR — {torch.backends.mps.is_built()}"
        if torch.cuda.is_available():
            return f"[+] GPU CUDA: {torch.cuda.get_device_name(0)}"
        return "[-] Không có GPU phù hợp — chạy bằng CPU (chậm hơn)."
    except ImportError:
        return "[!] Thư viện torch chưa được cài đặt."


def _classify_one(args_tuple: tuple) -> tuple:
    """Worker function cho ProcessPoolExecutor — mỗi process tự khởi tạo classifier riêng."""
    path, config = args_tuple
    classifier = DocumentClassifier(config)
    return classifier.classify(path)


def _print_progress(done: int, total: int, width: int = 30) -> None:
    """In thanh tiến trình đơn giản kiểu macOS terminal."""
    if total == 0:
        return
    ratio = done / total
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    pct = ratio * 100
    sys.stdout.write(f"\r  [{bar}] {done}/{total} ({pct:.0f}%)")
    sys.stdout.flush()
    if done == total:
        sys.stdout.write("\n")
=======
def _classify_worker(args: tuple) -> tuple:
    """Worker chạy trong subprocess riêng — không chia sẻ state với main process."""
    path_str, config = args
    from docsorter.classifier import DocumentClassifier
    from pathlib import Path
    classifier = DocumentClassifier(config)
    path = Path(path_str)
    classification = classifier.classify(path)
    return (path_str, classification)


def _detect_hardware() -> None:
    """In thông tin phần cứng tăng tốc hiện có (MPS / CUDA / CPU)."""
    try:
        import torch
        if torch.backends.mps.is_available() and torch.backends.mps.is_built():
            print("[+] Apple Silicon MPS (Metal Performance Shaders) sẵn sàng.")
        elif torch.cuda.is_available():
            print(f"[+] GPU CUDA: {torch.cuda.get_device_name(0)}")
        else:
            print("[-] Không tìm thấy MPS/CUDA — OCR sẽ chạy bằng CPU.")
    except ImportError:
        print("[!] torch chưa cài — không kiểm tra được backend phần cứng.")
>>>>>>> 5b3bdbabfd60b865131af56e2475b81128580357


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = config_from_args(args)

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        parser.error(f"Input directory does not exist: {input_dir}")

<<<<<<< HEAD
    # ── Thông tin phần cứng ──────────────────────────────────────────────────
    hw_info = _detect_hardware_info(config.ocr_backend)
    if hw_info:
        print(f"[*] OCR Backend: {config.ocr_backend.upper()}")
        print(hw_info)

    # ── Khám phá file ────────────────────────────────────────────────────────
    files = discover_files(input_dir, config, exclude_roots=(output_dir,))
    total = len(files)
    if total == 0:
        print("Không tìm thấy file nào để phân loại.")
        return 0

    # ── Quyết định chế độ xử lý ──────────────────────────────────────────────
    # OCR backend không an toàn với multiprocessing do model nặng → fallback tuần tự
    use_parallel = (
        not args.no_parallel
        and config.ocr_backend == "none"   # OCR backends không fork-safe
        and total > 1
        and args.workers > 1
    )

    n_workers = min(args.workers, total)
    show_progress = args.show_progress or (total >= 10 and sys.stdout.isatty())

    t0 = time.perf_counter()

    if use_parallel:
        print(f"[*] Chạy song song với {n_workers} worker(s) / {total} file(s)...")
        rows = _run_parallel(files, config, output_dir, n_workers, show_progress)
    else:
        if not args.no_parallel and config.ocr_backend != "none":
            print("[*] OCR đang bật → chạy tuần tự để tránh xung đột bộ nhớ GPU.")
        else:
            print(f"[*] Chạy tuần tự / {total} file(s)...")
        rows = _run_sequential(files, config, output_dir, show_progress)

    elapsed = time.perf_counter() - t0

    # ── Báo cáo kết quả ──────────────────────────────────────────────────────
    report_path = output_dir / config.report_name
    if not config.dry_run:
        write_report(report_path, rows)

    # Thống kê phân loại
    from docsorter.classifier import ClassificationStatus
    by_status: dict[str, int] = {}
    for cls, _ in rows:
        key = cls.target_label if cls.status == ClassificationStatus.SUBJECT else f"_{cls.status.value}"
        by_status[key] = by_status.get(key, 0) + 1

    print(f"\n{'─'*50}")
    print(f"  Hoàn thành: {total} file(s) trong {elapsed:.1f}s "
          f"({total/elapsed:.1f} file/s)" if elapsed > 0 else f"  Hoàn thành: {total} file(s)")
    print(f"  Kết quả:")
    for label, count in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"    {label}: {count}")
    if not config.dry_run:
        print(f"  Báo cáo: {report_path}")
    print(f"{'─'*50}")
=======
    # ── Thông báo trạng thái OCR & phần cứng ────────────────────────────────
    if config.ocr_backend != "none":
        print(f"[*] OCR Backend: {config.ocr_backend.upper()}")
        if config.ocr_backend == "paddleocr":
            try:
                import paddle
                if paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
                    print("[+] PaddleOCR: GPU CUDA sẵn sàng.")
                else:
                    print("[-] PaddleOCR: không có CUDA — chạy CPU (MPS không được hỗ trợ bởi Paddle).")
            except ImportError:
                print("[!] paddleocr chưa được cài đặt.")
        else:
            _detect_hardware()

    # ── Khám phá file ────────────────────────────────────────────────────────
    files = list(discover_files(input_dir, config, exclude_roots=(output_dir,)))
    rows = []

    # ── Chọn chiến lược xử lý ────────────────────────────────────────────────
    # Dùng ProcessPoolExecutor khi có đủ file và không phải dry-run / OCR batch.
    # OCR nặng (easyocr/paddleocr) không song song hoá vì model nạp vào GPU 1 lần;
    # spawn nhiều process sẽ tranh chấp VRAM / Unified Memory → chậm hơn.
    use_parallel = (
        len(files) >= 4
        and not config.dry_run
        and config.ocr_backend == "none"   # OCR: giữ tuần tự để dùng chung model
    )

    if use_parallel:
        import multiprocessing
        import os
        from concurrent.futures import ProcessPoolExecutor, as_completed

        # Tính số worker tối ưu: giữ 1 core cho main + I/O, tối đa 8
        p_count = (
            len(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity")
            else (os.cpu_count() or 4)
        )
        max_workers = max(2, min(p_count - 1, 8))
        print(f"[*] Song song hoá: {max_workers} workers (spawn) cho {len(files)} file.")

        # spawn bắt buộc trên macOS — fork deadlock với PyMuPDF & CoreFoundation
        ctx = multiprocessing.get_context("spawn")
        worker_args = [(str(p), config) for p in files]

        with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as pool:
            future_map = {pool.submit(_classify_worker, arg): arg[0] for arg in worker_args}
            for future in as_completed(future_map):
                try:
                    _path_str, classification = future.result()
                    # place_file luôn chạy trên main process để tránh race condition I/O
                    move_result = place_file(classification, output_dir, config)
                    rows.append((classification, move_result))
                    print(
                        f"{classification.source_path.name} -> {classification.target_label} "
                        f"({classification.status.value}, score={classification.score:.1f}, action={move_result.action})"
                    )
                except Exception as exc:
                    print(f"[!] Lỗi: {future_map[future]}: {exc}")
    else:
        # ── Tuần tự: dry-run, ít file, hoặc đang dùng OCR ──────────────────
        classifier = DocumentClassifier(config)
        for path in files:
            classification = classifier.classify(path)
            move_result = place_file(classification, output_dir, config)
            rows.append((classification, move_result))
            print(
                f"{path.name} -> {classification.target_label} "
                f"({classification.status.value}, score={classification.score:.1f}, action={move_result.action})"
            )

    # ── Xuất báo cáo ─────────────────────────────────────────────────────────
    report_path = output_dir / config.report_name
    if not config.dry_run:
        write_report(report_path, rows)
        print(f"Report: {report_path}")
    else:
        print(f"Dry run complete. {len(files)} files evaluated.")
>>>>>>> 5b3bdbabfd60b865131af56e2475b81128580357
    return 0


def _run_sequential(
    files: list[Path],
    config: ClassificationConfig,
    output_dir: Path,
    show_progress: bool,
) -> list[tuple]:
    """Chạy tuần tự — an toàn với OCR, debug dễ hơn."""
    classifier = DocumentClassifier(config)
    rows = []
    for i, path in enumerate(files, 1):
        classification = classifier.classify(path)
        move_result = place_file(classification, output_dir, config)
        rows.append((classification, move_result))
        if show_progress:
            _print_progress(i, len(files))
        else:
            print(
                f"  {path.name} → {classification.target_label} "
                f"(score={classification.score:.1f}, {move_result.action})"
            )
    return rows


def _run_parallel(
    files: list[Path],
    config: ClassificationConfig,
    output_dir: Path,
    n_workers: int,
    show_progress: bool,
) -> list[tuple]:
    """
    Chạy song song dùng ProcessPoolExecutor.
    Mỗi worker là process độc lập → tận dụng tối đa Apple Silicon Performance Cores.
    Spawn context an toàn hơn fork trên macOS (tránh lỗi Objective-C runtime).
    """
    # macOS dùng "spawn" thay "fork" — quan trọng vì fork + ObjC runtime = crash
    ctx = multiprocessing.get_context("spawn")
    args_list = [(path, config) for path in files]
    results: dict[Path, object] = {}

    with ProcessPoolExecutor(max_workers=n_workers, mp_context=ctx) as executor:
        future_to_path = {
            executor.submit(_classify_one, arg): arg[0]
            for arg in args_list
        }
        done_count = 0
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            done_count += 1
            try:
                classification = future.result()
                results[path] = classification
            except Exception as exc:
                # Worker crash → fallback classification với status ERROR
                from docsorter.classifier import ClassificationStatus, DocumentClassification
                results[path] = DocumentClassification(
                    path=path,
                    status=ClassificationStatus.ERROR,
                    target_label="_Khong_xac_dinh",
                    score=0.0,
                    runner_up_score=0.0,
                    negative_score=0.0,
                    evidence=[],
                    pages_sampled=[],
                    extraction_engine="error",
                    ocr_used=False,
                    error=str(exc),
                )
            if show_progress:
                _print_progress(done_count, len(files))
            else:
                cls = results[path]
                print(
                    f"  {path.name} → {cls.target_label} "
                    f"(score={cls.score:.1f})"
                )

    # Ghi file sau khi tất cả worker xong (tránh race condition)
    rows = []
    for path in files:
        classification = results[path]
        move_result = place_file(classification, output_dir, config)
        rows.append((classification, move_result))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())