from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import VendorVerificationRequest

router = APIRouter(prefix="/v1/vendors", tags=["vendors"])


@router.post("/verify", status_code=status.HTTP_200_OK)
def verify_vendor(payload: VendorVerificationRequest, db: Session = Depends(get_db)):
    if not payload.vendor_id:
        raise HTTPException(status_code=400, detail="vendor_id is required.")

    return {
        "vendor_id": payload.vendor_id,
        "verified": payload.verified,
        "status": "eligible" if payload.verified else "not_eligible",
    }
