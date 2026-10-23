from datetime import date

from app.services.billing import (
    add_months,
    monthly_factor,
    next_renewal_date,
    renewals_between,
)


def test_add_months_clamps_day():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)  # leap year
    assert add_months(date(2026, 11, 15), 3) == date(2027, 2, 15)


def test_future_anchor_is_returned_unchanged():
    assert next_renewal_date(date(2026, 12, 1), "monthly", date(2026, 10, 18)) == date(2026, 12, 1)


def test_monthly_roll_forward():
    assert next_renewal_date(date(2026, 1, 20), "monthly", date(2026, 10, 18)) == date(2026, 10, 20)
    assert next_renewal_date(date(2026, 1, 10), "monthly", date(2026, 10, 18)) == date(2026, 11, 10)


def test_month_end_anchor_keeps_original_day():
    # Anchored on the 31st: February clamps to 28, March goes back to 31.
    assert next_renewal_date(date(2026, 1, 31), "monthly", date(2026, 3, 1)) == date(2026, 3, 31)


def test_weekly_and_yearly_roll_forward():
    assert next_renewal_date(date(2026, 10, 1), "weekly", date(2026, 10, 18)) == date(2026, 10, 22)
    assert next_renewal_date(date(2024, 3, 5), "yearly", date(2026, 10, 18)) == date(2027, 3, 5)
    assert next_renewal_date(date(2026, 1, 15), "quarterly", date(2026, 10, 18)) == date(2027, 1, 15)


def test_renewal_today_counts_as_today():
    assert next_renewal_date(date(2026, 9, 18), "monthly", date(2026, 10, 18)) == date(2026, 10, 18)


def test_monthly_factors():
    assert monthly_factor("monthly") == 1
    assert monthly_factor("yearly") == 1 / 12
    assert round(monthly_factor("weekly"), 4) == round(52 / 12, 4)


def test_renewals_between_weekly_counts_each_occurrence():
    due = list(renewals_between(date(2026, 10, 1), "weekly", date(2026, 10, 18), date(2026, 11, 1)))
    assert due == [date(2026, 10, 22), date(2026, 10, 29)]


def test_renewals_between_monthly():
    due = list(renewals_between(date(2026, 1, 5), "monthly", date(2026, 10, 1), date(2026, 12, 31)))
    assert due == [date(2026, 10, 5), date(2026, 11, 5), date(2026, 12, 5)]
