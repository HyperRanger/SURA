from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.models import Vendor
from app.schemas import VendorVerificationRequest

router = APIRouter(prefix="/v1/vendors", tags=["vendors"])


@router.get("")
def list_verified_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).filter(Vendor.verified_at.is_not(None)).order_by(Vendor.name.asc()).all()
    return [
        {"vendor_id": vendor.id, "name": vendor.name, "category": vendor.category, "verified": True}
        for vendor in vendors
    ]


@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_vendor(
    payload: VendorVerificationRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    if not current_user.can_verify_vendor:
        raise HTTPException(status_code=403, detail="User is not authorized to verify vendors.")

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

    vendor.verified_at = datetime.utcnow()
    db.commit()

    return {
        "vendor_id": payload.vendor_id,
        "verified": vendor.verified_at is not None,
        "status": "eligible" if vendor.verified_at is not None else "not_eligible",
    }
