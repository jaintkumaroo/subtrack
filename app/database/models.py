"""Database tables, defined as Python classes (SQLAlchemy ORM)."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Unicode, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Unicode(60), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="category")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    billing_cycle: Mapped[str] = mapped_column(String(10), nullable=False, default="monthly")
    # The date of one known renewal. Future renewals are calculated from it.
    next_renewal: Mapped[date] = mapped_column(Date, nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Unicode(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    category: Mapped[Category | None] = relationship(back_populates="subscriptions")
