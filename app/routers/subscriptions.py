"""Subscription endpoints: list, create, read, update, pause/resume, delete."""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.deps import get_base
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut, SubscriptionUpdate
from app.services import subscription_service as service

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("", response_model=list[SubscriptionOut])
def list_subscriptions(
    status_filter: Literal["all", "active", "paused"] = Query("all", alias="status"),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    sort: Literal["renewal", "price", "name"] = "renewal",
    base: str = Depends(get_base),
    db: Session = Depends(get_db),
):
    return service.list_subscriptions(db, base, status_filter, category_id, search, sort)


@router.post("", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
def create_subscription(
    data: SubscriptionCreate, base: str = Depends(get_base), db: Session = Depends(get_db)
):
    return service.create_subscription(db, data, base)


@router.get("/{sub_id}", response_model=SubscriptionOut)
def get_subscription(sub_id: int, base: str = Depends(get_base), db: Session = Depends(get_db)):
    return service.get_subscription(db, sub_id, base)


@router.put("/{sub_id}", response_model=SubscriptionOut)
def update_subscription(
    sub_id: int,
    data: SubscriptionUpdate,
    base: str = Depends(get_base),
    db: Session = Depends(get_db),
):
    return service.update_subscription(db, sub_id, data, base)


@router.patch("/{sub_id}/toggle", response_model=SubscriptionOut)
def toggle_subscription(sub_id: int, base: str = Depends(get_base), db: Session = Depends(get_db)):
    """Pause an active subscription, or resume a paused one."""
    return service.toggle_subscription(db, sub_id, base)


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(sub_id: int, db: Session = Depends(get_db)):
    service.delete_subscription(db, sub_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
