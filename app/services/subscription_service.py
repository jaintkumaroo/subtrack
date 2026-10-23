"""Business logic for subscriptions and categories. Routers call these functions."""

from datetime import date
from typing import Optional

from sqlalchemy import false, func, select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database.models import Category, Subscription
from app.schemas.subscription import CategoryCreate, SubscriptionCreate, SubscriptionUpdate
from app.services.billing import monthly_factor, next_renewal_date
from app.services.currency_service import convert, get_rates


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class BadRequestError(Exception):
    pass


# ---------------------------------------------------------------- categories
def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def create_category(db: Session, data: CategoryCreate) -> Category:
    exists = db.scalar(select(Category).where(func.lower(Category.name) == data.name.lower()))
    if exists:
        raise ConflictError(f"Category '{data.name}' already exists")
    category = Category(name=data.name, color=data.color)
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"Category '{data.name}' already exists")
    return category


def _check_category(db: Session, category_id: Optional[int]) -> None:
    if category_id is not None and db.get(Category, category_id) is None:
        raise BadRequestError(f"Category {category_id} does not exist")


# ------------------------------------------------------------- subscriptions
def serialize(sub: Subscription, base: str, rates: dict, today: date) -> dict:
    """Turn a database row into the dictionary the API returns, with money converted to `base`."""
    renewal = next_renewal_date(sub.next_renewal, sub.billing_cycle, today)
    price_base = convert(sub.price, sub.currency, base, rates)
    monthly = price_base * monthly_factor(sub.billing_cycle)
    return {
        "id": sub.id,
        "name": sub.name,
        "price": sub.price,
        "currency": sub.currency,
        "billing_cycle": sub.billing_cycle,
        "next_renewal": renewal,
        "category_id": sub.category_id,
        "category_name": sub.category.name if sub.category else None,
        "category_color": sub.category.color if sub.category else None,
        "is_active": sub.is_active,
        "notes": sub.notes,
        "created_at": sub.created_at,
        "base_currency": base,
        "price_base": round(price_base, 2),
        "monthly_cost": round(monthly, 2),
        "yearly_cost": round(monthly * 12, 2),
        "days_until_renewal": (renewal - today).days,
    }


def list_subscriptions(
    db: Session,
    base: str,
    status: str = "all",
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    sort: str = "renewal",
) -> list[dict]:
    query = select(Subscription).options(selectinload(Subscription.category))
    if status == "active":
        query = query.where(Subscription.is_active == true())
    elif status == "paused":
        query = query.where(Subscription.is_active == false())
    if category_id is not None:
        query = query.where(Subscription.category_id == category_id)
    if search:
        query = query.where(Subscription.name.ilike(f"%{search.strip()}%"))

    rates = get_rates()["rates"]
    today = date.today()
    items = [serialize(sub, base, rates, today) for sub in db.scalars(query)]

    if sort == "price":
        items.sort(key=lambda s: s["monthly_cost"], reverse=True)
    elif sort == "name":
        items.sort(key=lambda s: s["name"].lower())
    else:
        items.sort(key=lambda s: (s["days_until_renewal"], s["name"].lower()))
    return items


def _get_row(db: Session, sub_id: int) -> Subscription:
    sub = db.scalar(
        select(Subscription)
        .options(selectinload(Subscription.category))
        .where(Subscription.id == sub_id)
    )
    if sub is None:
        raise NotFoundError(f"Subscription {sub_id} not found")
    return sub


def get_subscription(db: Session, sub_id: int, base: str) -> dict:
    sub = _get_row(db, sub_id)
    return serialize(sub, base, get_rates()["rates"], date.today())


def create_subscription(db: Session, data: SubscriptionCreate, base: str) -> dict:
    _check_category(db, data.category_id)
    sub = Subscription(**data.model_dump())
    db.add(sub)
    db.commit()
    return get_subscription(db, sub.id, base)


def update_subscription(db: Session, sub_id: int, data: SubscriptionUpdate, base: str) -> dict:
    sub = _get_row(db, sub_id)
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes:
        _check_category(db, changes["category_id"])
    for field, value in changes.items():
        if value is None and field not in {"category_id", "notes"}:
            continue  # name, price, ... can never be set to null
        setattr(sub, field, value)
    db.commit()
    return get_subscription(db, sub_id, base)


def toggle_subscription(db: Session, sub_id: int, base: str) -> dict:
    sub = _get_row(db, sub_id)
    sub.is_active = not sub.is_active
    db.commit()
    return get_subscription(db, sub_id, base)


def delete_subscription(db: Session, sub_id: int) -> None:
    sub = _get_row(db, sub_id)
    db.delete(sub)
    db.commit()
