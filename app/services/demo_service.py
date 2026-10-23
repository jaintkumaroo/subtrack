"""Sample data so the app can be demonstrated in one click."""

from datetime import date, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.database.models import Category, Subscription

# name, price, currency, cycle, category, days until next renewal, active
DEMO_SUBSCRIPTIONS = [
    ("Netflix", 15.49, "USD", "monthly", "Entertainment", 3, True),
    ("YouTube Premium", 11.99, "USD", "monthly", "Entertainment", 5, True),
    ("Spotify Premium", 4.99, "USD", "monthly", "Music", 9, True),
    ("ChatGPT Plus", 20.00, "USD", "monthly", "Productivity", 12, True),
    ("Notion Plus", 10.00, "USD", "monthly", "Productivity", 21, True),
    ("GitHub Copilot", 10.00, "USD", "monthly", "Cloud & Dev", 17, True),
    ("Domain Name", 12.98, "USD", "yearly", "Cloud & Dev", 74, True),
    ("Coursera Plus", 399.00, "USD", "yearly", "Education", 142, True),
    ("Gym Membership", 6000.00, "PKR", "monthly", "Health & Fitness", 2, True),
    ("Home Internet", 4500.00, "PKR", "monthly", "Other", 6, True),
    ("Amazon Prime", 14.99, "USD", "monthly", "Shopping", 25, True),
    ("Adobe Creative Cloud", 59.99, "USD", "monthly", "Productivity", 11, False),
]


def seed_demo(db: Session) -> int:
    """Adds the demo subscriptions only when the table is empty. Returns how many were added."""
    if db.scalar(select(func.count(Subscription.id))):
        return 0
    categories = {c.name: c.id for c in db.scalars(select(Category))}
    today = date.today()
    for name, price, currency, cycle, category, days, active in DEMO_SUBSCRIPTIONS:
        db.add(
            Subscription(
                name=name,
                price=price,
                currency=currency,
                billing_cycle=cycle,
                next_renewal=today + timedelta(days=days),
                category_id=categories.get(category),
                is_active=active,
            )
        )
    db.commit()
    return len(DEMO_SUBSCRIPTIONS)


def clear_subscriptions(db: Session) -> int:
    count = db.scalar(select(func.count(Subscription.id))) or 0
    db.execute(delete(Subscription))
    db.commit()
    return count
