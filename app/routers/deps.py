"""Small shared dependencies for the routers."""

from typing import Optional

from fastapi import HTTPException, Query

from app.config import settings
from app.services.currency_service import CURRENCIES


def get_base(
    base: Optional[str] = Query(
        default=None,
        description="Currency to show amounts in (for example PKR or USD). Defaults to BASE_CURRENCY.",
    ),
) -> str:
    code = (base or settings.base_currency).upper()
    if code not in CURRENCIES:
        raise HTTPException(status_code=422, detail=f"Unsupported currency '{code}'")
    return code
