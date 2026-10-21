import re
from datetime import date, timedelta
from typing import List, Tuple


def parse_week(week_str: str) -> Tuple[int, int]:
    """Convierte '2026-W08', 'W08' o '8' en (2026, 8)."""
    s = str(week_str).strip().upper()
    m = re.match(r"^(\d{4})-W(\d{1,2})$", s)
    if m:
        year, week = int(m.group(1)), int(m.group(2))
        last_week = date(year, 12, 28).isocalendar().week
        return year, max(1, min(last_week, week))
    m2 = re.match(r"^W?(\d{1,2})$", s)
    if m2:
        return 2026, max(1, min(52, int(m2.group(1))))
    return 2026, 1


def format_week(year: int, week_num: int) -> str:
    jan_fourth = date(year, 1, 4)
    first_monday = jan_fourth - timedelta(days=jan_fourth.isoweekday() - 1)
    target = first_monday + timedelta(weeks=week_num - 1)
    iso_year, iso_week, _ = target.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def shift_week(week_str: str, delta_weeks: int) -> str:
    y, w = parse_week(week_str)
    return format_week(y, w + delta_weeks)


def compare_weeks(w1: str, w2: str) -> int:
    """Devuelve la diferencia en semanas (w1 - w2)."""
    y1, n1 = parse_week(w1)
    y2, n2 = parse_week(w2)
    date1 = date.fromisocalendar(y1, n1, 1)
    date2 = date.fromisocalendar(y2, n2, 1)
    return (date1 - date2).days // 7


def generate_week_range(w_from: str, w_to: str) -> List[str]:
    y1, n1 = parse_week(w_from)
    y2, n2 = parse_week(w_to)
    total_diff = compare_weeks(w_to, w_from)
    if total_diff < 0:
        return [format_week(y1, n1)]
    return [format_week(y1, n1 + i) for i in range(min(total_diff + 1, 105))]
