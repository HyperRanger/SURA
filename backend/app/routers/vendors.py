from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal, get_current_principal
from app.database import get_db
from app.models import User, Vendor
from app.schemas import (
    AccountResolveRequest,
    VendorProductCreateRequest,
    VendorProductUpdateRequest,
    VendorPayoutAccountRequest,
    VendorRedeemRequest,
    VendorVerificationRequest,
)
from app.services.commitments import (
    get_vendor_redemption_detail,
    list_vendor_redemptions,
    redeem_vendor_voucher,
    validate_vendor_voucher,
)
from app.services.vendor_accounts import get_authenticated_vendor_id
from app.services.vendor_catalogue import create_product, deactivate_product, list_products, update_product
from app.services import linked_accounts, vendor_payout_accounts

router = APIRouter(prefix="/v1/vendors", tags=["vendors"])


def _require_vendor_principal(current_user: AuthPrincipal) -> None:
    if not current_user.can_redeem_vendor_vouchers:
        raise HTTPException(status_code=403, detail="User is not authorized to redeem vouchers as a vendor.")


def _require_individual(current_user: AuthPrincipal) -> None:
    if current_user.role != "individual":
        raise HTTPException(status_code=403, detail="Member access is required.")


@router.get("")
def list_verified_vendors(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    vendors = db.query(Vendor).filter(Vendor.verified_at.is_not(None)).order_by(Vendor.name.asc()).all()
    return [
        {"vendor_id": vendor.id, "name": vendor.name, "category": vendor.category, "verified": True}
        for vendor in vendors
    ]


@router.get("/me/products")
def list_my_products(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    return {"products": list_products(db, get_authenticated_vendor_id(current_user), include_inactive=True)}


@router.get("/me/payout-account")
def get_my_payout_account(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    return {"account": vendor_payout_accounts.get_payout_account(db, get_authenticated_vendor_id(current_user))}


@router.get("/me/payout-account/simulation")
def get_my_payout_account_simulation(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Return the vendor's demo-only account fixture before payout setup.

    This is deliberately separate from the saved payout label. It lets the
    PWA show which simulated account/name pair will pass validation without
    retaining an unmasked account number after setup.
    """
    _require_vendor_principal(current_user)
    return linked_accounts.get_account_simulation(db, current_user.user_id)


@router.post("/me/payout-account/resolve")
def resolve_my_payout_account(
    payload: AccountResolveRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    user = db.get(User, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Vendor account not found.")
    return linked_accounts.resolve_account(
        db,
        payload.bank_name,
        payload.account_number,
        expected_subject_id=user.id,
        expected_holder_name=user.name,
    )


@router.put("/me/payout-account")
def save_my_payout_account(
    payload: VendorPayoutAccountRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    user = db.get(User, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Vendor account not found.")
    return vendor_payout_accounts.save_payout_account(
        db,
        get_authenticated_vendor_id(current_user),
        payload.bank_name,
        payload.account_number,
        holder_subject_id=user.id,
        holder_name=user.name,
    )


@router.post("/me/products", status_code=status.HTTP_201_CREATED)
def add_my_product(
    payload: VendorProductCreateRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    return create_product(db, get_authenticated_vendor_id(current_user), name=payload.name, price=payload.price)


@router.patch("/me/products/{product_id}")
def edit_my_product(
    product_id: str,
    payload: VendorProductUpdateRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    if not payload.has_changes():
        raise HTTPException(status_code=400, detail="Provide a product name or price to update.")
    return update_product(
        db,
        get_authenticated_vendor_id(current_user),
        product_id,
        name=payload.name,
        price=payload.price,
    )


@router.delete("/me/products/{product_id}")
def remove_my_product(
    product_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    return deactivate_product(db, get_authenticated_vendor_id(current_user), product_id)


@router.get("/{vendor_id}/products")
def list_vendor_products_for_member(
    vendor_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_individual(current_user)
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.verified_at is None:
        raise HTTPException(status_code=404, detail="Verified vendor not found.")
    return {"vendor_id": vendor.id, "products": list_products(db, vendor.id)}


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


@router.post("/redeem/validate")
def validate_voucher_for_vendor(
    payload: VendorRedeemRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Validate using the merchant record bound to the vendor session."""
    _require_vendor_principal(current_user)
    vendor_id = get_authenticated_vendor_id(current_user)
    return validate_vendor_voucher(db, payload.voucher_code, vendor_id)


@router.post("/redeem")
def redeem_voucher_for_vendor(
    payload: VendorRedeemRequest,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Confirm handover after the vendor has reviewed a validated voucher."""
    _require_vendor_principal(current_user)
    vendor_id = get_authenticated_vendor_id(current_user)
    return redeem_vendor_voucher(db, payload.voucher_code, vendor_id)


@router.get("/redemptions")
def get_vendor_redemptions(
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    vendor_id = get_authenticated_vendor_id(current_user)
    return list_vendor_redemptions(db, vendor_id)


@router.get("/redemptions/{redemption_id}")
def get_vendor_redemption_receipt(
    redemption_id: str,
    current_user: AuthPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    _require_vendor_principal(current_user)
    vendor_id = get_authenticated_vendor_id(current_user)
    return get_vendor_redemption_detail(db, vendor_id, redemption_id)
