"""Shared utility functions for the GUI."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Return human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def format_eta(seconds: float) -> str:
    """Return human-readable ETA string."""
    if seconds <= 0:
        return "—"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    if m < 60:
        return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m"


def open_directory(path: str | Path) -> None:
    """Open a directory in the OS file explorer."""
    path = str(path)
    if not os.path.exists(path):
        return
    if sys.platform == "win32":
        subprocess.Popen(f'explorer "{os.path.abspath(path)}"')
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def open_file(path: str | Path) -> None:
    """Open a file with the default OS application."""
    path = str(path)
    if not os.path.exists(path):
        return
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
