"""Category endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.subscription import CategoryCreate, CategoryOut
from app.services import subscription_service as service

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    return service.create_category(db, data)
