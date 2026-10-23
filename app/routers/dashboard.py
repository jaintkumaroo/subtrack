"""Dashboard numbers and the CSV report."""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.deps import get_base
from app.services import dashboard_service, subscription_service

router = APIRouter(tags=["Dashboard & Reports"])


@router.get("/dashboard")
def dashboard(base: str = Depends(get_base), db: Session = Depends(get_db)):
    return dashboard_service.build_dashboard(db, base)


@router.get("/reports/export.csv")
def export_csv(base: str = Depends(get_base), db: Session = Depends(get_db)):
    """All subscriptions as a CSV file (opens directly in Excel)."""
    items = subscription_service.list_subscriptions(db, base, status="all", sort="name")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Name",
            "Category",
            "Status",
            "Price",
            "Currency",
            "Billing cycle",
            "Next renewal",
            f"Monthly cost ({base})",
            f"Yearly cost ({base})",
            "Notes",
        ]
    )
    for s in items:
        writer.writerow(
            [
                s["name"],
                s["category_name"] or "",
                "Active" if s["is_active"] else "Paused",
                f"{s['price']:.2f}",
                s["currency"],
                s["billing_cycle"],
                s["next_renewal"].isoformat(),
                f"{s['monthly_cost']:.2f}",
                f"{s['yearly_cost']:.2f}",
                s["notes"] or "",
            ]
        )

    filename = f"subtrack-report-{date.today().isoformat()}.csv"
    return Response(
        content=buffer.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
