from __future__ import annotations


def sampled_page_indexes(total_pages: int, max_pages: int) -> list[int]:
    if total_pages <= 0 or max_pages <= 0:
        return []
    candidates = [0, 1]
    middle = total_pages // 2
    candidates.extend([middle, middle + 1, total_pages - 2, total_pages - 1])
    ordered: list[int] = []
    for page in candidates:
        if 0 <= page < total_pages and page not in ordered:
            ordered.append(page)
    if len(ordered) > max_pages:
        return ordered[:max_pages]
    return ordered
