"""Vendor-owned catalogue records used by Sura Lock agreement creation."""

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Vendor, VendorProduct


def _serialize(product: VendorProduct) -> dict:
    return {
        "product_id": product.id,
        "vendor_id": product.vendor_id,
        "name": product.name,
        "price": product.price,
        "status": product.status,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def list_products(db: Session, vendor_id: str, *, include_inactive: bool = False) -> list[dict]:
    query = db.query(VendorProduct).filter(VendorProduct.vendor_id == vendor_id)
    if not include_inactive:
        query = query.filter(VendorProduct.status == "active")
    return [_serialize(product) for product in query.order_by(VendorProduct.name.asc(), VendorProduct.id.asc()).all()]


def create_product(db: Session, vendor_id: str, *, name: str, price: int) -> dict:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.verified_at is None:
        raise HTTPException(status_code=403, detail="Only verified vendors can manage a catalogue.")
    product = VendorProduct(id=str(uuid.uuid4()), vendor_id=vendor_id, name=name.strip(), price=price, status="active")
    db.add(product)
    db.commit()
    db.refresh(product)
    return _serialize(product)


def update_product(db: Session, vendor_id: str, product_id: str, *, name: str | None, price: int | None) -> dict:
    product = db.query(VendorProduct).filter(VendorProduct.id == product_id, VendorProduct.vendor_id == vendor_id).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found for this vendor.")
    if name is not None:
        product.name = name.strip()
    if price is not None:
        product.price = price
    db.commit()
    db.refresh(product)
    return _serialize(product)


def deactivate_product(db: Session, vendor_id: str, product_id: str) -> dict:
    product = db.query(VendorProduct).filter(VendorProduct.id == product_id, VendorProduct.vendor_id == vendor_id).one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found for this vendor.")
    product.status = "inactive"
    db.commit()
    db.refresh(product)
    return _serialize(product)


def active_product_for_vendor(db: Session, *, product_id: str, vendor_id: str) -> VendorProduct:
    product = db.query(VendorProduct).filter(
        VendorProduct.id == product_id,
        VendorProduct.vendor_id == vendor_id,
        VendorProduct.status == "active",
    ).one_or_none()
    if product is None:
        raise HTTPException(status_code=400, detail="Selected product is not active for the chosen verified vendor.")
    return product
