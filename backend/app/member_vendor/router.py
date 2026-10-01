"""PWA convenience reads, scoped to the signed-in member or vendor."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.member_vendor.contracts import MemberHomeResponse, VendorOverviewResponse
from app.member_vendor.service import get_member_home, get_vendor_overview
from app.models import User
from app.schemas import LockRequest, MemberLookupRequest
from app.services.auth_service import normalize_phone
from app.services.commitments import preview_lock
from app.services.contact_lookup_rate_limit import consume_contact_lookup
from app.services.vendor_accounts import get_authenticated_vendor_id

router = APIRouter(prefix="/v1/app", tags=["member vendor app"])


def _require_individual(current_user: AuthPrincipal) -> None:
    if current_user.role != "individual":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member access is required.")


@router.get("/home", response_model=MemberHomeResponse)
def member_home(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return get_member_home(db, current_user.user_id)


@router.post("/members/resolve")
def resolve_member_contact(
    payload: MemberLookupRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Resolve one exact contact for an authenticated group creator."""
    _require_individual(current_user)
    normalized_phone = normalize_phone(payload.phone)
    consume_contact_lookup(db, current_user.user_id)
    user = db.query(User).filter(User.phone == normalized_phone, User.role == "individual").one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Sura member was found for this contact.")
    return {"user_id": user.id, "first_name": user.name.split(maxsplit=1)[0]}


@router.post("/commitments/lock-preview")
def lock_preview(
    payload: LockRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    return preview_lock(db, payload, current_user.user_id)


@router.get("/vendor/overview", response_model=VendorOverviewResponse)
def vendor_overview(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    if not current_user.can_redeem_vendor_vouchers:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vendor access is required.")
    vendor_id = get_authenticated_vendor_id(current_user)
    return get_vendor_overview(db, vendor_id)
