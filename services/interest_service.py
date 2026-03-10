from datetime import date, datetime
import math


def parse_date(value: str) -> date:
    return datetime.fromisoformat(value).date()


def calculate_interest(principal: float, due_from: str, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    start_date = parse_date(due_from)
    days_open = (as_of - start_date).days
    overdue_days = max(0, days_open - 14)
    weeks_overdue = math.floor(overdue_days / 7)
    interest = round(principal * 0.005 * weeks_overdue, 2) if weeks_overdue > 0 else 0.0
    return {
        "days_open": max(days_open, 0),
        "overdue_days": overdue_days,
        "weeks_overdue": weeks_overdue,
        "interest": interest,
        "total_with_interest": round(principal + interest, 2),
        "is_overdue": overdue_days > 0,
    }
