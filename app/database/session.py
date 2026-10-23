"""Database session factory and the FastAPI dependency that hands one out per request."""

from sqlalchemy.orm import sessionmaker

from app.database.connection import engine

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
