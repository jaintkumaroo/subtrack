"""Pure date and cost maths for billing cycles. No database, no web: easy to test."""

import calendar
from datetime import date, timedelta
from typing import Iterator

CYCLES = ("weekly", "monthly", "quarterly", "yearly")

# How many months one billing cycle spans (weekly is handled separately).
_MONTHS_PER_CYCLE = {"monthly": 1, "quarterly": 3, "yearly": 12}

# Multiply the price of one cycle by this to get the cost per month.
_MONTHLY_FACTOR = {
    "weekly": 52 / 12,
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "yearly": 1 / 12,
}


def monthly_factor(cycle: str) -> float:
    return _MONTHLY_FACTOR[cycle]


def add_months(start: date, months: int) -> date:
    """Add months, clamping the day (Jan 31 + 1 month = Feb 28/29)."""
    index = start.year * 12 + (start.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def occurrence(anchor: date, cycle: str, n: int) -> date:
    """The n-th renewal counted from the anchor date (n = 0 is the anchor itself)."""
    if cycle == "weekly":
        return anchor + timedelta(weeks=n)
    return add_months(anchor, n * _MONTHS_PER_CYCLE[cycle])


def next_renewal_date(anchor: date, cycle: str, today: date) -> date:
    """First renewal on or after `today`, rolling the anchor date forward if it is in the past."""
    if anchor >= today:
        return anchor
    if cycle == "weekly":
        n = -(-(today - anchor).days // 7)  # ceiling division
        return occurrence(anchor, cycle, n)
    step = _MONTHS_PER_CYCLE[cycle]
    months_between = (today.year - anchor.year) * 12 + (today.month - anchor.month)
    n = max(0, months_between // step)
    while occurrence(anchor, cycle, n) < today:
        n += 1
    return occurrence(anchor, cycle, n)


def renewals_between(anchor: date, cycle: str, start: date, end: date) -> Iterator[date]:
    """Every renewal date d with start <= d <= end."""
    current = next_renewal_date(anchor, cycle, start)
    # Find which occurrence number `current` is, then walk forward.
    n = 0
    while occurrence(anchor, cycle, n) < current:
        n += 1
    while True:
        due = occurrence(anchor, cycle, n)
        if due > end:
            return
        yield due
        n += 1
