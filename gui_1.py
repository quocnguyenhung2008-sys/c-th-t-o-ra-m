"""
gui_app.py — Giao diện đồ họa cho công cụ Phân loại Tài liệu THPT
Yêu cầu: pip install customtkinter tkinterdnd2
Chạy: python gui_app.py
"""
from __future__ import annotations

import csv
import json
import re
import threading
import time
import unicodedata
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

# ── Thiết lập giao diện toàn cục ─────────────────────────────────────────────
ctk.set_appearance_mode("System")          # Tự động theo Dark/Light của hệ điều hành
ctk.set_default_color_theme("blue")


# ═════════════════════════════════════════════════════════════════════════════
# PALETTE & TYPOGRAPHY
# Ngôn ngữ thiết kế: "Phòng lab tối giản" — nền xám lạnh, accent xanh điện,
# font monospace cho dữ liệu, không bo góc quá mức.
# ═════════════════════════════════════════════════════════════════════════════
PAL = {
    "accent":       "#3B82F6",   # blue-500
    "accent_dark":  "#2563EB",   # blue-600
    "success":      "#22C55E",   # green-500
    "warning":      "#F59E0B",   # amber-500
    "danger":       "#EF4444",   # red-500
    "card_light":   "#F1F5F9",
    "card_dark":    "#1E293B",
    "text_muted":   "#64748B",
    "drop_bg_light": "#F8FAFC",
    "drop_bg_dark":  "#0F172A"
}

FONT_DISPLAY = ("SF Pro Display", 22, "bold")
FONT_LABEL   = ("SF Pro Text",   13)
FONT_MONO    = ("JetBrains Mono", 12)
FONT_SMALL   = ("SF Pro Text",   11)


# ═════════════════════════════════════════════════════════════════════════════
# ADVANCED LOGIC — Xử lý Chuẩn hóa & Khớp phân tầng chuyên sâu
# ═════════════════════════════════════════════════════════════════════════════

def has_vietnamese_accent(text: str) -> bool:
    """Kiểm tra chuỗi có chứa ký tự tiếng Việt có dấu hay không."""
    viet_chars = "àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
    return any(c in text for c in viet_chars)


def remove_accents(text: str) -> str:
    """Chuẩn hóa loại bỏ toàn bộ dấu tiếng Việt về dạng ký tự ASCII sạch."""
    text = text.replace('đ', 'd').replace('Đ', 'D')
    nfkd_form = unicodedata.normalize('NFKD', text)
    clean_str = "".join([c for c in nfkd_form if unicodedata.category(c) != 'Mn'])
    return unicodedata.normalize('NFC', clean_str)


def load_aliases(path: Path) -> dict[str, list[str]]:
    """Nạp file aliases.json → dict {môn: [alias1, alias2, ...]}"""
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    result: dict[str, list[str]] = {}
    for subject, values in raw.items():
        if isinstance(values, list):
            result[subject] = [str(v).strip().lower() for v in values if str(v).strip()]
        elif isinstance(values, dict):
            result[subject] = [str(k).strip().lower() for k in values if str(k).strip()]
    return result


def save_aliases(path: Path, data: dict[str, list[str]]) -> None:
    """Ghi dict aliases về file JSON (giữ nguyên định dạng list)."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_report(path: Path) -> list[dict[str, str]]:
    """Đọc classification_report.csv → list[dict]"""
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def match_subject_advanced(stem: str, aliases: dict[str, list[str]], mode: str) -> str | None:
    """
    Thuật toán cốt lõi nhận diện môn học dựa trên ranh giới từ và cơ chế phân tầng.
    Giải quyết triệt để lỗi trùng lặp từ đơn không dấu (ví dụ: tuồng -> tuong).
    """
    stem_lower = stem.lower()

    # CHẾ ĐỘ 1: Khớp chuỗi con linh hoạt (Cơ chế cũ)
    if mode == "Linh hoạt (Substring)":
        for subject, alias_list in aliases.items():
            for alias in alias_list:
                if alias.lower() in stem_lower:
                    return subject
        return None

    # CHẾ ĐỘ 2: Phân tầng nghiêm ngặt (Chống nhiễu từ đơn)
    # TẦNG 1: Khớp nguyên từ có dấu (Chỉ kích hoạt nếu file có dấu tiếng Việt)
    if has_vietnamese_accent(stem_lower):
        for subject, alias_list in aliases.items():
            for alias in alias_list:
                alias_lbl = alias.lower()
                if has_vietnamese_accent(alias_lbl):
                    # Sử dụng Regex Lookbehind/Lookahead để cô lập ranh giới từ độc lập
                    pattern = rf"(?<!\w){re.escape(alias_lbl)}(?!\w)"
                    if re.search(pattern, stem_lower):
                        return subject

    # TẦNG 2: Khớp nguyên từ không dấu (Hạ cấp chuỗi để đối chiếu diện rộng)
    stem_no_accent = remove_accents(stem_lower)
    for subject, alias_list in aliases.items():
        for alias in alias_list:
            alias_no_accent = remove_accents(alias.lower())
            pattern = rf"(?<!\w){re.escape(alias_no_accent)}(?!\w)"
            
            if re.search(pattern, stem_no_accent):
                # ── BỘ LỌC ĐẶC BIỆT CHỐNG COLLISION (Ví dụ: tuồng -> tuong) ──
                # Nếu từ khóa gốc có chứa chữ "tuồng", nhưng tên file thực tế lại là "tương tác" hoặc "đối tượng"
                if alias_no_accent == "tuong" and "tuồng" in alias.lower():
                    if "tương" in stem_lower or "tượng" in stem_lower:
                        continue  # Bỏ qua không nhận nhầm môn văn
                return subject

    return None


def analyse_report(
    rows: list[dict[str, str]],
    aliases: dict[str, list[str]],
    mode: str,
    progress_cb=None,
) -> tuple[list[dict], float, int]:
    """Phân tích báo cáo CSV và đề xuất nhãn mới dựa trên thuật toán lựa chọn."""
    changes: list[dict] = []
    total = len(rows)
    correct = 0

    for idx, row in enumerate(rows):
        if progress_cb:
            progress_cb((idx + 1) / total)

        filename   = row.get("filename") or row.get("file") or row.get("Filename") or ""
        old_label  = row.get("target_label") or row.get("label") or row.get("Label") or ""
        status     = row.get("status") or row.get("Status") or ""

        stem = Path(filename).stem
        matched_subject = match_subject_advanced(stem, aliases, mode)
        new_label = matched_subject or old_label

        if new_label == old_label:
            correct += 1
        else:
            changes.append({
                "filename":  filename,
                "old_label": old_label,
                "new_label": new_label,
                "status":    status,
            })

        time.sleep(0.002)

    accuracy = (correct / total * 100) if total else 0.0
    return changes, accuracy, len(changes)


# ═════════════════════════════════════════════════════════════════════════════
# COMPONENT: MetricCard — Thẻ chỉ số đơn
# ═════════════════════════════════════════════════════════════════════════════

class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str = "—", accent: str = PAL["accent"], **kw):
        super().__init__(master, corner_radius=12, **kw)
        self._accent = accent

        self._title_lbl = ctk.CTkLabel(
            self, text=title.upper(),
            font=("SF Pro Text", 10, "bold"),
            text_color=PAL["text_muted"],
        )
        self._title_lbl.pack(anchor="w", padx=16, pady=(14, 0))

        self._value_lbl = ctk.CTkLabel(
            self, text=value,
            font=("SF Pro Display", 28, "bold"),
            text_color=accent,
        )
        self._value_lbl.pack(anchor="w", padx=16, pady=(2, 14))

    def set_value(self, value: str) -> None:
        self._value_lbl.configure(text=value)


# ═════════════════════════════════════════════════════════════════════════════
# COMPONENT: DataTable — Bảng kết quả (Treeview thuần tkinter bọc trong CTk)
# ═════════════════════════════════════════════════════════════════════════════

class DataTable(ctk.CTkFrame):
    COLUMNS = (
        ("filename",  "Tên file",    320),
        ("old_label", "Nhãn cũ",     150),
        ("new_label", "Nhãn mới",    150),
        ("status",    "Trạng thái",  110),
    )

    def __init__(self, master, **kw):
        super().__init__(master, corner_radius=10, **kw)

        import tkinter.ttk as ttk
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "DocSort.Treeview",
            background="#1E293B",
            foreground="#E2E8F0",
            fieldbackground="#1E293B",
            borderwidth=0,
            rowheight=30,
            font=("JetBrains Mono", 11),
        )
        style.configure(
            "DocSort.Treeview.Heading",
            background="#0F172A",
            foreground="#94A3B8",
            font=("SF Pro Text", 11, "bold"),
            borderwidth=0,
        )
        style.map("DocSort.Treeview", background=[("selected", "#2563EB")])

        cols = [c[0] for c in self.COLUMNS]
        self._tree = ttk.Treeview(
            self, columns=cols, show="headings",
            style="DocSort.Treeview", selectmode="browse",
        )
        for col_id, col_title, col_width in self.COLUMNS:
            self._tree.heading(col_id, text=col_title)
            self._tree.column(col_id, width=col_width, minwidth=80, anchor="w")

        vsb = ctk.CTkScrollbar(self, command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def load(self, rows: list[dict]) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        for row in rows:
            tag = "changed" if row.get("new_label") != row.get("old_label") else ""
            self._tree.insert("", "end", values=(
                row.get("filename", ""),
                row.get("old_label", ""),
                row.get("new_label", ""),
                row.get("status", ""),
            ), tags=(tag,))
        self._tree.tag_configure("changed", foreground="#FCD34D")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: PHÂN TÍCH & CÀI ĐẶT CHẾ ĐỘ PHÂN LOẠI (Có Kéo Thả)
# ═════════════════════════════════════════════════════════════════════════════

class AnalysisTab(ctk.CTkFrame):
    def __init__(self, master, app: "App", **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._app = app
        self._csv_path: Path | None = None
        self._result_rows: list[dict] = []
        self._build()
        self._init_drag_and_drop()

    def _build(self) -> None:
        # ── Upper Configuration Layout ────────────────────────────────────────
        upper_layout = ctk.CTkFrame(self, fg_color="transparent")
        upper_layout.pack(fill="x", padx=24, pady=(16, 0))

        # Khung trái: Kéo thả file
        self._drop_zone = ctk.CTkFrame(
            upper_layout, height=130, corner_radius=12,
            border_width=2, border_color=PAL["accent"],
            fg_color=(PAL["drop_bg_light"], PAL["drop_bg_dark"])
        )
        self._drop_zone.pack(side="left", expand=True, fill="both", padx=(0, 12))
        self._drop_zone.pack_propagate(False)

        self._drop_label = ctk.CTkLabel(
            self._drop_zone,
            text="📥 KÉO THẢ FILE CLASSIFICATION_REPORT.CSV VÀO ĐÂY\n(hoặc click để chọn tệp thủ công)",
            font=("SF Pro Text", 12, "bold"), text_color=PAL["accent"]
        )
        self._drop_label.pack(expand=True)
        # Cho phép click vào khung để duyệt file truyền thống
        self._drop_zone.bind("<Button-1>", lambda e: self._browse_csv())
        self._drop_label.bind("<Button-1>", lambda e: self._browse_csv())

        # Khung phải: Cài đặt chế độ phân loại môn học
        config_zone = ctk.CTkFrame(upper_layout, width=320, corner_radius=12)
        config_zone.pack(side="right", fill="both")
        config_zone.pack_propagate(False)

        ctk.CTkLabel(
            config_zone, text="CHẾ ĐỘ PHÂN LOẠI MÔN",
            font=("SF Pro Text", 10, "bold"), text_color=PAL["text_muted"]
        ).pack(anchor="w", padx=16, pady=(14, 2))

        self._mode_var = ctk.StringVar(value="Phân tầng nghiêm ngặt")
        self._mode_combo = ctk.CTkComboBox(
            config_zone,
            variable=self._mode_var,
            values=["Phân tầng nghiêm ngặt", "Linh hoạt (Substring)"],
            height=36, font=FONT_LABEL, corner_radius=8, dropdown_font=FONT_LABEL
        )
        self._mode_combo.pack(fill="x", padx=16, pady=4)

        # Trạng thái hiển thị tự động nhận diện
        self._auto_detect_lbl = ctk.CTkLabel(
            config_zone, text="⚡ Tự động ánh xạ từ khóa: Sẵn sàng",
            font=FONT_SMALL, text_color=PAL["success"], anchor="w"
        )
        self._auto_detect_lbl.pack(fill="x", padx=16, pady=(4, 10))

        # ── Vùng điều khiển hành động ─────────────────────────────────────────
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=24, pady=(12, 0))

        self._run_btn = ctk.CTkButton(
            ctrl, text="▶  Bắt đầu phân tích",
            height=40, corner_radius=8,
            fg_color=PAL["accent"], hover_color=PAL["accent_dark"],
            font=("SF Pro Text", 13, "bold"),
            command=self._run_analysis,
        )
        self._run_btn.pack(side="left")

        self._export_btn = ctk.CTkButton(
            ctrl, text="↓  Xuất kết quả (.csv)",
            height=40, corner_radius=8, width=180,
            fg_color="transparent", border_width=1,
            border_color=PAL["accent"], text_color=PAL["accent"],
            hover_color=("#EFF6FF", "#1E3A5F"),
            font=("SF Pro Text", 13),
            command=self._export_csv,
            state="disabled",
        )
        self._export_btn.pack(side="left", padx=(10, 0))

        self._progress = ctk.CTkProgressBar(
            ctrl, width=180, height=8, corner_radius=4,
            fg_color=("#E2E8F0", "#1E293B"), progress_color=PAL["accent"],
        )
        self._progress.set(0)
        self._progress.pack(side="left", padx=(20, 0))
        self._progress.pack_forget()

        self._status_lbl = ctk.CTkLabel(
            ctrl, text="", font=FONT_SMALL, text_color=PAL["text_muted"],
        )
        self._status_lbl.pack(side="left", padx=10)

        # ── Metric Cards Dashboard ────────────────────────────────────────────
        metrics_row = ctk.CTkFrame(self, fg_color="transparent")
        metrics_row.pack(fill="x", padx=24, pady=(14, 0))

        self._card_accuracy = MetricCard(metrics_row, title="Độ chính xác cũ", value="—", accent=PAL["accent"])
        self._card_accuracy.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self._card_fixed = MetricCard(metrics_row, title="Số file đề xuất sửa nhãn", value="—", accent=PAL["warning"])
        self._card_fixed.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self._card_total = MetricCard(metrics_row, title="Tổng file kiểm thử", value="—", accent=PAL["success"])
        self._card_total.pack(side="left", expand=True, fill="x")

        # ── Bảng hiển thị kết quả đề xuất ──────────────────────────────────────
        ctk.CTkLabel(
            self, text="DANH SÁCH FILE ĐƯỢC TỰ ĐỘNG KHỚP TỐI ƯU NHÃN MỚI",
            font=("SF Pro Text", 10, "bold"), text_color=PAL["text_muted"], anchor="w",
        ).pack(fill="x", padx=24, pady=(14, 4))

        self._table = DataTable(self)
        self._table.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _init_drag_and_drop(self) -> None:
        """Kích hoạt và liên kết thư viện TkDND xuống widget thông qua Tcl gọi trực tiếp."""
        try:
            self.tk.call('package', 'require', 'tkdnd')
            # Đăng ký vùng drop_zone làm mục tiêu nhận diện kéo thả tệp tin
            self._drop_zone.tk.call('dnd', 'register', self._drop_zone._w, 'target', 'DND_Files')
            self._drop_zone.bind('<<Drop>>', self._on_file_drop)
        except Exception as e:
            print(f"[Cảnh báo] Hệ thống không tìm thấy thư viện tkdnd: {e}")
            self._drop_label.configure(text="📂 CLICK VÀO ĐÂY ĐỂ CHỌN FILE REPORT CSV\n(Tính năng kéo thả chưa được thiết lập)")

    def _on_file_drop(self, event) -> None:
        """Xử lý chuỗi đường dẫn khi người dùng thả file vào GUI."""
        try:
            data = self.tk.call('dnd', 'data')
            if data.startswith('{') and data.endswith('}'):
                data = data[1:-1]
            path = Path(data)
            if path.suffix.lower() == '.csv':
                self._process_selected_csv(path)
            else:
                messagebox.showerror("Sai định dạng", "Hệ thống chỉ chấp nhận tệp cấu trúc báo cáo .csv")
        except Exception as exc:
            messagebox.showerror("Lỗi kéo thả", str(exc))

    def _browse_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn file báo cáo CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._process_selected_csv(Path(path))

    def _process_selected_csv(self, path: Path) -> None:
        self._csv_path = path
        self._drop_label.configure(text=f"✓ Đã chọn file: {path.name}", text_color=PAL["success"])
        if self._app.aliases:
            self._auto_detect_lbl.configure(
                text=f"⚡ Nhận diện: {len(self._app.aliases)} môn học cấu hình sẵn",
                text_color=PAL["success"]
            )

    def _run_analysis(self) -> None:
        if not self._csv_path or not self._csv_path.exists():
            messagebox.showerror("Lỗi", "Vui lòng kéo thả hoặc chọn file CSV hợp lệ trước.")
            return
        if not self._app.aliases:
            messagebox.showerror("Lỗi", "Chưa nạp cơ sở dữ liệu Bộ từ khóa. Vui lòng kiểm tra Tab Quản lý từ khóa.")
            return

        self._run_btn.configure(state="disabled", text="Đang phân tích...")
        self._export_btn.configure(state="disabled")
        self._progress.pack(side="left", padx=(20, 0))
        self._progress.set(0)
        self._set_status("Đang đọc tiến trình...")

        mode = self._mode_var.get()

        def _worker():
            try:
                rows = load_report(self._csv_path)
                total = len(rows)

                def _progress_cb(ratio: float):
                    self._progress.set(ratio)
                    self._set_status(f"Xử lý nâng cao: {int(ratio * total)}/{total}...")

                changes, accuracy, n_fixed = analyse_report(
                    rows, self._app.aliases, mode, _progress_cb
                )
                self._result_rows = changes
                self.after(0, lambda: self._on_done(changes, accuracy, n_fixed, total))
            except Exception as exc:
                self.after(0, lambda: self._on_error(str(exc)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_done(self, changes: list[dict], accuracy: float, n_fixed: int, total: int) -> None:
        self._card_accuracy.set_value(f"{accuracy:.1f}%")
        self._card_fixed.set_value(str(n_fixed))
        self._card_total.set_value(str(total))
        self._table.load(changes)
        self._progress.set(1.0)
        self._set_status(f"Hoàn tất! Tìm thấy {n_fixed} tệp cần tối ưu")
        self._run_btn.configure(state="normal", text="▶  Bắt đầu phân tích")
        if changes:
            self._export_btn.configure(state="normal")
        self.after(3000, lambda: self._progress.pack_forget())

    def _on_error(self, msg: str) -> None:
        self._run_btn.configure(state="normal", text="▶  Bắt đầu phân tích")
        self._progress.pack_forget()
        self._set_status("")
        messagebox.showerror("Lỗi hệ thống", msg)

    def _set_status(self, text: str) -> None:
        self._status_lbl.configure(text=text)

    def _export_csv(self) -> None:
        if not self._result_rows:
            return
        path = filedialog.asksaveasfilename(
            title="Lưu kết quả tối ưu nhãn mới",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="de_xuat_doi_nhan_nang_cao.csv",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["filename", "old_label", "new_label", "status"])
                writer.writeheader()
                writer.writerows(self._result_rows)
            messagebox.showinfo("Thành công", f"Đã xuất dữ liệu tối ưu thành công ra file:\n{path}")
        except Exception as exc:
            messagebox.showerror("Lỗi xuất file", str(exc))


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: QUẢN LÝ TỪ KHÓA (Aliases)
# ═════════════════════════════════════════════════════════════════════════════

class KeywordTab(ctk.CTkFrame):
    def __init__(self, master, app: "App", **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._app = app
        self._aliases_path: Path | None = None
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 0))

        ctk.CTkLabel(header, text="Quản lý từ khóa môn học (Aliases)", font=("SF Pro Display", 20, "bold")).pack(side="left")

        file_frame = ctk.CTkFrame(self, corner_radius=12)
        file_frame.pack(fill="x", padx=24, pady=(16, 0))

        ctk.CTkLabel(file_frame, text="FILE CẤU HÌNH ALIASES.JSON", font=("SF Pro Text", 10, "bold"), text_color=PAL["text_muted"]).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 0))

        self._alias_entry = ctk.CTkEntry(file_frame, placeholder_text="Chọn file aliases.json...", font=FONT_MONO, height=36, corner_radius=8)
        self._alias_entry.grid(row=1, column=0, sticky="ew", padx=16, pady=(4, 14))

        ctk.CTkButton(file_frame, text="Browse", width=90, height=36, corner_radius=8, fg_color=PAL["accent"], hover_color=PAL["accent_dark"], command=self._browse_aliases).grid(row=1, column=1, padx=(0, 16), pady=(4, 14))
        file_frame.columnconfigure(0, weight=1)

        picker_row = ctk.CTkFrame(self, fg_color="transparent")
        picker_row.pack(fill="x", padx=24, pady=(14, 0))

        ctk.CTkLabel(picker_row, text="DANH SÁCH MÔN HỌC", font=("SF Pro Text", 10, "bold"), text_color=PAL["text_muted"]).pack(anchor="w")

        subject_row = ctk.CTkFrame(picker_row, fg_color="transparent")
        subject_row.pack(fill="x", pady=(4, 0))

        self._subject_var = ctk.StringVar(value="— Chọn môn học —")
        self._subject_combo = ctk.CTkComboBox(subject_row, variable=self._subject_var, values=["— Chọn môn học —"], width=260, height=38, corner_radius=8, font=FONT_LABEL, command=self._on_subject_change, state="disabled")
        self._subject_combo.pack(side="left")

        ctk.CTkButton(subject_row, text="+ Thêm môn mới", width=120, height=38, corner_radius=8, fg_color="transparent", border_width=1, border_color=PAL["accent"], text_color=PAL["accent"], hover_color=("#EFF6FF", "#1E3A5F"), font=FONT_SMALL, command=self._add_subject).pack(side="left", padx=(10, 0))
        ctk.CTkButton(subject_row, text="Xóa môn chọn", width=110, height=38, corner_radius=8, fg_color="transparent", border_width=1, border_color=PAL["danger"], text_color=PAL["danger"], hover_color=("#FEF2F2", "#3B1515"), font=FONT_SMALL, command=self._delete_subject).pack(side="left", padx=(8, 0))

        guide_frame = ctk.CTkFrame(self, corner_radius=8, fg_color=("#EFF6FF", "#172554"))
        guide_frame.pack(fill="x", padx=24, pady=(12, 0))

        ctk.CTkLabel(guide_frame, text="ℹ  Nhập các từ khóa phân tách bằng dấu PHẨY. Ví dụ để sửa lỗi chữ tuồng:  tuồng, vở tuồng, tuong, kich tuong", font=FONT_SMALL, text_color=("#1D4ED8", "#93C5FD"), anchor="w").pack(padx=12, pady=8)

        ctk.CTkLabel(self, text="TỪ KHÓA ĐỊNH DANH (PHÂN CÁCH BẰNG DẤU PHẨY)", font=("SF Pro Text", 10, "bold"), text_color=PAL["text_muted"], anchor="w").pack(fill="x", padx=24, pady=(14, 4))

        self._keyword_box = ctk.CTkTextbox(self, corner_radius=10, font=FONT_MONO, wrap="word", height=200, border_width=1)
        self._keyword_box.pack(fill="both", expand=True, padx=24)
        self._keyword_box.insert("end", "Vui lòng mở file aliases.json và chọn một môn học cụ thể để chỉnh sửa từ khóa...")
        self._keyword_box.configure(state="disabled")

        save_row = ctk.CTkFrame(self, fg_color="transparent")
        save_row.pack(fill="x", padx=24, pady=(12, 20))

        self._save_btn = ctk.CTkButton(save_row, text="💾  Lưu bộ từ khóa", height=42, corner_radius=8, fg_color=PAL["success"], hover_color="#16A34A", font=("SF Pro Text", 13, "bold"), command=self._save_aliases, state="disabled")
        self._save_btn.pack(side="left")

        self._save_status = ctk.CTkLabel(save_row, text="", font=FONT_SMALL, text_color=PAL["text_muted"])
        self._save_status.pack(side="left", padx=14)

    def _browse_aliases(self) -> None:
        path = filedialog.askopenfilename(title="Chọn file aliases.json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        self._aliases_path = Path(path)
        self._alias_entry.delete(0, "end")
        self._alias_entry.insert(0, str(self._aliases_path))

        try:
            data = load_aliases(self._aliases_path)
            self._app.aliases = data
            self._app.aliases_path = self._aliases_path
            self._refresh_combo()
            self._subject_combo.configure(state="normal")
            self._save_status.configure(text=f"Đã kích hoạt {len(data)} môn học", text_color=PAL["success"])
            
            # Cập nhật thông tin sang Tab 1 tự động
            if self._app._analysis_tab:
                self._app._analysis_tab._auto_detect_lbl.configure(
                    text=f"⚡ Nhận diện: {len(data)} môn học cấu hình sẵn", text_color=PAL["success"]
                )
        except Exception as exc:
            messagebox.showerror("Lỗi cấu trúc", str(exc))

    def _refresh_combo(self) -> None:
        subjects = list(self._app.aliases.keys())
        self._subject_combo.configure(values=["— Chọn môn học —"] + subjects)
        self._subject_var.set("— Chọn môn học —")

    def _on_subject_change(self, value: str) -> None:
        if value.startswith("—"):
            self._keyword_box.configure(state="disabled")
            self._save_btn.configure(state="disabled")
            return

        keywords = self._app.aliases.get(value, [])
        self._keyword_box.configure(state="normal")
        self._keyword_box.delete("1.0", "end")
        self._keyword_box.insert("end", ", ".join(keywords))
        self._save_btn.configure(state="normal")
        self._save_status.configure(text="")

    def _save_aliases(self) -> None:
        subject = self._subject_var.get()
        if subject.startswith("—"):
            return

        raw_text = self._keyword_box.get("1.0", "end").strip()
        keywords = [kw.strip().lower() for kw in raw_text.split(",") if kw.strip()]

        if not keywords:
            messagebox.showwarning("Dữ liệu trống", f"Môn '{subject}' yêu cầu tối thiểu một thực thể từ khóa định danh.")
            return

        self._app.aliases[subject] = keywords

        if not self._aliases_path:
            messagebox.showerror("Thất bại", "Không tìm thấy đích đến tệp tin aliases.json.")
            return

        try:
            save_aliases(self._aliases_path, self._app.aliases)
            self._save_status.configure(text=f"✓ Đã lưu thành công bộ {len(keywords)} từ khóa cho môn {subject}", text_color=PAL["success"])
            self.after(4000, lambda: self._save_status.configure(text="", text_color=PAL["text_muted"]))
        except Exception as exc:
            messagebox.showerror("Lỗi ghi dữ liệu", str(exc))

    def _add_subject(self) -> None:
        dialog = ctk.CTkInputDialog(text="Nhập tên môn học cần thêm mới (ví dụ: Ngu_van):", title="Tạo môn học")
        name = dialog.get_input()
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self._app.aliases:
            messagebox.showwarning("Trùng lắp", f"Môn '{name}' đã có trên phân hệ lưu trữ.")
            return
        self._app.aliases[name] = []
        self._refresh_combo()
        self._subject_var.set(name)
        self._on_subject_change(name)

    def _delete_subject(self) -> None:
        subject = self._subject_var.get()
        if subject.startswith("—"):
            return
        confirm = messagebox.askyesno("Xác nhận", f"Xóa vĩnh viễn danh mục môn '{subject}'?\nHành động này sẽ ghi đè lên file json.")
        if not confirm:
            return
        self._app.aliases.pop(subject, None)
        if self._aliases_path:
            try:
                save_aliases(self._aliases_path, self._app.aliases)
            except Exception:
                pass
        self._refresh_combo()
        self._keyword_box.configure(state="disabled")
        self._keyword_box.delete("1.0", "end")
        self._keyword_box.insert("end", "Vui lòng mở file aliases.json và chọn một môn học cụ thể để chỉnh sửa từ khóa...")
        self._save_btn.configure(state="disabled")


# ═════════════════════════════════════════════════════════════════════════════
# APP ROOT
# ═════════════════════════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.aliases: dict[str, list[str]] = {}
        self.aliases_path: Path | None = None

        self.title("Phân loại Tài liệu THPT — Bản nâng cấp thông minh")
        self.geometry("1020x750")
        self.minsize(850, 600)

        self._build()

    def _build(self) -> None:
        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(24, 0), padx=16)

        ctk.CTkLabel(logo_frame, text="DocSort v2.0", font=("SF Pro Display", 18, "bold"), text_color=PAL["accent"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="Phân loại & Tối ưu thông minh", font=FONT_SMALL, text_color=PAL["text_muted"]).pack(anchor="w")

        ctk.CTkFrame(sidebar, height=1, fg_color=("#E2E8F0", "#1E293B")).pack(fill="x", padx=16, pady=20)

        self._tab_btns: list[ctk.CTkButton] = []
        nav_items = [
            ("📊  Phân tích & Tối ưu", self._make_analysis_tab),
            ("🔑  Quản lý từ khóa",    self._make_keyword_tab),
        ]

        for idx, (label, factory) in enumerate(nav_items):
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w", height=40, corner_radius=8,
                fg_color="transparent", text_color=("#1E293B", "#E2E8F0"),
                hover_color=("#EFF6FF", "#1E3A5F"), font=FONT_LABEL,
                command=lambda i=idx: self._switch_tab(i),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._tab_btns.append(btn)

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="y", expand=True)

        theme_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        theme_row.pack(fill="x", padx=16, pady=(0, 20))
        ctk.CTkLabel(theme_row, text="Chế độ tối", font=FONT_SMALL).pack(side="left")
        ctk.CTkSwitch(theme_row, text="", width=44, command=self._toggle_theme).pack(side="right")

        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray10"))
        self._content.pack(side="left", fill="both", expand=True)

        self._analysis_tab: AnalysisTab | None = None
        self._keyword_tab:  KeywordTab  | None = None
        self._current_tab  = -1

        self._switch_tab(0)

    def _make_analysis_tab(self) -> AnalysisTab:
        if self._analysis_tab is None:
            self._analysis_tab = AnalysisTab(self._content, app=self)
        return self._analysis_tab

    def _make_keyword_tab(self) -> KeywordTab:
        if self._keyword_tab is None:
            self._keyword_tab = KeywordTab(self._content, app=self)
        return self._keyword_tab

    _tab_factories = [_make_analysis_tab, _make_keyword_tab]

    def _switch_tab(self, idx: int) -> None:
        if idx == self._current_tab:
            return
        for frame in self._content.winfo_children():
            frame.pack_forget()

        tab = self._tab_factories[idx](self)
        tab.pack(fill="both", expand=True)
        self._current_tab = idx

        for i, btn in enumerate(self._tab_btns):
            if i == idx:
                btn.configure(fg_color=(PAL["accent"], PAL["accent_dark"]), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("#1E293B", "#E2E8F0"))

    def _toggle_theme(self) -> None:
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if current == "Dark" else "Dark")


if __name__ == "__main__":
    app = App()
    app.mainloop()