from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vendor
from app.schemas import VendorVerificationRequest

router = APIRouter(prefix="/v1/vendors", tags=["vendors"])


@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_vendor(payload: VendorVerificationRequest, db: Session = Depends(get_db)):
    if not payload.vendor_id:
        raise HTTPException(status_code=400, detail="vendor_id is required.")

    vendor = db.get(Vendor, payload.vendor_id)
    if vendor is None:
        vendor = Vendor(
            id=payload.vendor_id,
            name=payload.name or payload.vendor_id,
            category=payload.category or "demo",
        )
        db.add(vendor)
    elif payload.name:
        vendor.name = payload.name
    if payload.category:
        vendor.category = payload.category

    vendor.verified_at = datetime.utcnow() if payload.verified else None
    db.commit()

    return {
        "vendor_id": payload.vendor_id,
        "verified": vendor.verified_at is not None,
        "status": "eligible" if vendor.verified_at is not None else "not_eligible",
    }
