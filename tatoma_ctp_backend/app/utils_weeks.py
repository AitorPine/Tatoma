import re
from typing import List, Tuple


def parse_week(week_str: str) -> Tuple[int, int]:
    """Convierte '2026-W08', 'W08' o '8' en (2026, 8)."""
    s = str(week_str).strip().upper()
    m = re.match(r"^(\d{4})-W(\d{1,2})$", s)
    if m:
        return int(m.group(1)), max(1, min(52, int(m.group(2))))
    m2 = re.match(r"^W?(\d{1,2})$", s)
    if m2:
        return 2026, max(1, min(52, int(m2.group(1))))
    return 2026, 1


def format_week(year: int, week_num: int) -> str:
    while week_num < 1:
        year -= 1
        week_num += 52
    while week_num > 52:
        year += 1
        week_num -= 52
    return f"{year}-W{week_num:02d}"


def shift_week(week_str: str, delta_weeks: int) -> str:
    y, w = parse_week(week_str)
    return format_week(y, w + delta_weeks)


def compare_weeks(w1: str, w2: str) -> int:
    """Devuelve la diferencia en semanas (w1 - w2)."""
    y1, n1 = parse_week(w1)
    y2, n2 = parse_week(w2)
    return (y1 - y2) * 52 + (n1 - n2)


def generate_week_range(w_from: str, w_to: str) -> List[str]:
    y1, n1 = parse_week(w_from)
    y2, n2 = parse_week(w_to)
    total_diff = (y2 - y1) * 52 + (n2 - n1)
    if total_diff < 0:
        return [format_week(y1, n1)]
    return [format_week(y1, n1 + i) for i in range(min(total_diff + 1, 53))]
