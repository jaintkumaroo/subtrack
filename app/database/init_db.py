"""Creates the database (SQL Server only), the tables and the default categories.

Run it by hand with:  python -m app.database.init_db
The API also runs it automatically on startup, so this is optional.
"""

from sqlalchemy import select, text

from app.config import settings
from app.database.connection import build_engine, engine
from app.database.models import Base, Category
from app.database.session import SessionLocal

DEFAULT_CATEGORIES = [
    ("Entertainment", "#f43f5e"),
    ("Music", "#a855f7"),
    ("Productivity", "#6366f1"),
    ("Cloud & Dev", "#06b6d4"),
    ("Education", "#10b981"),
    ("Health & Fitness", "#f59e0b"),
    ("Shopping", "#ec4899"),
    ("Other", "#94a3b8"),
]


def create_database_if_missing() -> None:
    """SQL Server cannot create tables in a database that does not exist yet."""
    if settings.db_mode != "mssql":
        return
    # CREATE DATABASE cannot run inside a transaction, hence AUTOCOMMIT.
    admin_engine = build_engine("master", isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(
            text(
                f"IF DB_ID(N'{settings.mssql_database}') IS NULL "
                f"CREATE DATABASE [{settings.mssql_database}]"
            )
        )
    admin_engine.dispose()


def seed_categories() -> None:
    with SessionLocal() as db:
        existing = set(db.scalars(select(Category.name)))
        for name, color in DEFAULT_CATEGORIES:
            if name not in existing:
                db.add(Category(name=name, color=color))
        db.commit()


def init_db() -> None:
    create_database_if_missing()
    Base.metadata.create_all(engine)
    seed_categories()


if __name__ == "__main__":
    init_db()
    where = settings.mssql_database if settings.db_mode == "mssql" else settings.sqlite_path
    print(f"Database ready ({settings.db_label}: {where}).")
