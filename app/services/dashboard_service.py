"""Aggregations for the dashboard: totals, upcoming renewals, category split, insights."""

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.database.models import Subscription
from app.services.billing import monthly_factor, renewals_between
from app.services.currency_service import convert, get_rates
from app.services.subscription_service import list_subscriptions

ZERO_DECIMAL_CURRENCIES = {"PKR", "JPY", "INR", "BDT", "EGP"}
TIMELINE_WEEKS = 5


def money(value: float, currency: str) -> str:
    decimals = 0 if currency in ZERO_DECIMAL_CURRENCIES else 2
    return f"{currency} {value:,.{decimals}f}"


def _timeline(db_rows: list[Subscription], base: str, rates: dict, today: date) -> list[dict]:
    """Money due in each of the next few weeks (a weekly subscription can renew several times)."""
    buckets = []
    for week in range(TIMELINE_WEEKS):
        start = today + timedelta(days=7 * week)
        end = start + timedelta(days=6)
        amount, count = 0.0, 0
        for sub in db_rows:
            if not sub.is_active:
                continue
            for _ in renewals_between(sub.next_renewal, sub.billing_cycle, start, end):
                amount += convert(sub.price, sub.currency, base, rates)
                count += 1
        buckets.append(
            {
                "label": f"{start.strftime('%b')} {start.day} – {end.strftime('%b')} {end.day}",
                "start": start,
                "end": end,
                "amount": round(amount, 2),
                "count": count,
            }
        )
    return buckets


def _due_within(db_rows: list[Subscription], base: str, rates: dict, today: date, days: int):
    end = today + timedelta(days=days)
    amount, count = 0.0, 0
    for sub in db_rows:
        if not sub.is_active:
            continue
        for _ in renewals_between(sub.next_renewal, sub.billing_cycle, today, end):
            amount += convert(sub.price, sub.currency, base, rates)
            count += 1
    return round(amount, 2), count


def build_dashboard(db: Session, base: str) -> dict:
    rates_info = get_rates()
    rates = rates_info["rates"]
    today = date.today()

    everything = list_subscriptions(db, base, status="all")
    active = [s for s in everything if s["is_active"]]
    paused = [s for s in everything if not s["is_active"]]

    monthly_total = round(sum(s["monthly_cost"] for s in active), 2)
    yearly_total = round(monthly_total * 12, 2)
    daily_total = round(yearly_total / 365, 2)
    paused_savings = round(sum(s["monthly_cost"] for s in paused), 2)

    rows = list(db.query(Subscription).all())
    due_7_total, due_7_count = _due_within(rows, base, rates, today, 7)
    due_30_total, due_30_count = _due_within(rows, base, rates, today, 30)

    upcoming = [s for s in active if s["days_until_renewal"] <= 30]
    upcoming.sort(key=lambda s: (s["days_until_renewal"], s["name"].lower()))

    # --- by category ---
    groups: dict[str, dict] = defaultdict(lambda: {"monthly_cost": 0.0, "count": 0, "color": "#94a3b8"})
    for s in active:
        key = s["category_name"] or "Uncategorized"
        groups[key]["monthly_cost"] += s["monthly_cost"]
        groups[key]["count"] += 1
        if s["category_color"]:
            groups[key]["color"] = s["category_color"]
    by_category = [
        {
            "name": name,
            "color": g["color"],
            "monthly_cost": round(g["monthly_cost"], 2),
            "count": g["count"],
            "share": round(g["monthly_cost"] / monthly_total * 100, 1) if monthly_total else 0.0,
        }
        for name, g in groups.items()
    ]
    by_category.sort(key=lambda g: g["monthly_cost"], reverse=True)

    # --- by billing cycle ---
    cycle_groups: dict[str, dict] = defaultdict(lambda: {"count": 0, "monthly_cost": 0.0})
    for s in active:
        cycle_groups[s["billing_cycle"]]["count"] += 1
        cycle_groups[s["billing_cycle"]]["monthly_cost"] += s["monthly_cost"]
    by_cycle = [
        {"cycle": c, "count": g["count"], "monthly_cost": round(g["monthly_cost"], 2)}
        for c, g in cycle_groups.items()
    ]

    top = sorted(active, key=lambda s: s["monthly_cost"], reverse=True)[:5]

    return {
        "base_currency": base,
        "rate_source": rates_info["source"],
        "monthly_total": monthly_total,
        "yearly_total": yearly_total,
        "daily_total": daily_total,
        "active_count": len(active),
        "paused_count": len(paused),
        "total_count": len(everything),
        "paused_monthly_savings": paused_savings,
        "due_7_total": due_7_total,
        "due_7_count": due_7_count,
        "due_30_total": due_30_total,
        "due_30_count": due_30_count,
        "upcoming": upcoming[:8],
        "by_category": by_category,
        "by_cycle": by_cycle,
        "top": top,
        "timeline": _timeline(rows, base, rates, today),
        "insights": _insights(active, by_category, monthly_total, daily_total, paused,
                              paused_savings, due_7_total, due_7_count, base),
    }


def _insights(active, by_category, monthly_total, daily_total, paused, paused_savings,
              due_7_total, due_7_count, base) -> list[str]:
    if not active:
        return ["Add your first subscription to see personal insights here."]

    notes: list[str] = []
    top = max(active, key=lambda s: s["monthly_cost"])
    share = top["monthly_cost"] / monthly_total * 100 if monthly_total else 0
    notes.append(
        f"{top['name']} is your biggest subscription at {money(top['monthly_cost'], base)} "
        f"per month ({share:.0f}% of your total)."
    )
    if len(by_category) > 1:
        lead = by_category[0]
        notes.append(f"{lead['name']} is your largest category, taking {lead['share']:.0f}% of your spending.")
    if due_7_count:
        plural = "renewal" if due_7_count == 1 else "renewals"
        notes.append(f"{due_7_count} {plural} in the next 7 days will charge {money(due_7_total, base)}.")
    notes.append(f"Your subscriptions cost roughly {money(daily_total, base)} every single day.")
    if paused:
        notes.append(
            f"Pausing {len(paused)} subscription{'s' if len(paused) != 1 else ''} "
            f"is saving you {money(paused_savings, base)} per month."
        )
    monthly_plans = [s for s in active if s["billing_cycle"] == "monthly"]
    if len(monthly_plans) >= 3:
        notes.append(
            f"Tip: you pay monthly for {len(monthly_plans)} services. Many offer a yearly plan "
            "with a discount, so it is worth checking."
        )
    return notes
