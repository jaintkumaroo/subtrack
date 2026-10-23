"""Health check, app metadata, exchange rates and demo-data helpers."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.services import currency_service, demo_service
from app.services.billing import CYCLES

router = APIRouter(tags=["System"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": settings.db_label, "base_currency": settings.base_currency}


@router.get("/meta")
def meta():
    info = currency_service.get_rates()
    return {
        "base_currency": settings.base_currency,
        "currencies": currency_service.CURRENCIES,
        "billing_cycles": list(CYCLES),
        "rate_source": info["source"],
        "rates_updated": info["updated"],
        "database": settings.db_label,
    }


@router.get("/rates")
def rates():
    """Exchange rates, expressed as units of each currency per 1 USD."""
    return currency_service.get_rates()


@router.post("/demo/seed")
def seed_demo(db: Session = Depends(get_db)):
    """Load sample subscriptions (only if there are none yet)."""
    return {"added": demo_service.seed_demo(db)}


@router.delete("/demo/clear")
def clear_demo(db: Session = Depends(get_db)):
    """Delete every subscription. Categories are kept."""
    return {"deleted": demo_service.clear_subscriptions(db)}
