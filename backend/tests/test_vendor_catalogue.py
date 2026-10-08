"""Vendor catalogue ownership and the immutable Lock product agreement."""

from datetime import datetime

from app.main import app
from app.models import Commitment, User, UserConsent, Vendor, VendorProduct
from core.security import create_token


def _headers(user_id: str, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, {'role': role})}"}


def _setup(client):
    db = app.state.testing_session()
    try:
        now = datetime.utcnow()
        db.add_all([
            Vendor(id="vendor_one", name="One Shop", category="electronics", verified_at=now),
            Vendor(id="vendor_two", name="Two Shop", category="fashion", verified_at=now),
            User(id="vendor_user", name="Vendor Owner", phone="2348000010001", role="vendor", vendor_id="vendor_one"),
            User(id="other_vendor", name="Other Vendor", phone="2348000010002", role="vendor", vendor_id="vendor_two"),
            User(id="member_one", name="Member One", phone="2348000010003", role="individual"),
            User(id="member_two", name="Member Two", phone="2348000010004", role="individual"),
            UserConsent(id="consent_one", user_id="member_one", consent_type="score_processing", granted=True, recorded_at=now),
        ])
        db.commit()
    finally:
        db.close()


def test_vendor_manages_only_its_own_catalogue_and_members_see_active_items(client):
    _setup(client)
    vendor_headers = _headers("vendor_user", "vendor")
    member_headers = _headers("member_one", "individual")

    created = client.post("/v1/vendors/me/products", json={"name": "Starter Laptop", "price": 285000}, headers=vendor_headers)
    assert created.status_code == 201, created.text
    product = created.json()

    visible = client.get("/v1/vendors/vendor_one/products", headers=member_headers)
    assert visible.status_code == 200
    assert visible.json()["products"] == [product]

    forbidden = client.patch(
        f"/v1/vendors/me/products/{product['product_id']}",
        json={"price": 1},
        headers=_headers("other_vendor", "vendor"),
    )
    assert forbidden.status_code == 404

    removed = client.delete(f"/v1/vendors/me/products/{product['product_id']}", headers=vendor_headers)
    assert removed.status_code == 200
    assert removed.json()["status"] == "inactive"
    assert client.get("/v1/vendors/vendor_one/products", headers=member_headers).json()["products"] == []


def test_lock_product_snapshot_is_owned_by_its_vendor_and_survives_catalogue_edits(client):
    _setup(client)
    vendor_headers = _headers("vendor_user", "vendor")
    member_headers = _headers("member_one", "individual")
    product = client.post("/v1/vendors/me/products", json={"name": "Original Laptop", "price": 285000}, headers=vendor_headers).json()

    created = client.post("/v1/commitments/lock", json={
        "type": "rotating", "title": "Laptop circle", "vendor_id": "vendor_one", "product_id": product["product_id"],
        "contribution_amount": 5000, "contribution_frequency": "monthly", "cycles": 2,
        "members": ["member_one", "member_two"], "payout_order": ["member_one", "member_two"],
    }, headers=member_headers)
    assert created.status_code == 201, created.text
    commitment_id = created.json()["commitment_id"]

    changed = client.patch(
        f"/v1/vendors/me/products/{product['product_id']}",
        json={"name": "Changed Laptop", "price": 1}, headers=vendor_headers,
    )
    assert changed.status_code == 200

    details = client.get(f"/v1/commitments/{commitment_id}", headers=member_headers)
    assert details.status_code == 200
    assert details.json()["product"] == {"product_id": product["product_id"], "name": "Original Laptop", "price": 285000}

    db = app.state.testing_session()
    try:
        commitment = db.get(Commitment, commitment_id)
        assert commitment.product_name_snapshot == "Original Laptop"
        assert commitment.product_price_snapshot == 285000
        assert db.get(VendorProduct, product["product_id"]).price == 1
    finally:
        db.close()


def test_lock_rejects_a_product_from_another_vendor(client):
    _setup(client)
    db = app.state.testing_session()
    try:
        db.add(VendorProduct(id="other_product", vendor_id="vendor_two", name="Other item", price=5000, status="active"))
        db.commit()
    finally:
        db.close()

    response = client.post("/v1/commitments/lock", json={
        "type": "rotating", "title": "Wrong product", "vendor_id": "vendor_one", "product_id": "other_product",
        "contribution_amount": 5000, "contribution_frequency": "weekly", "cycles": 2,
        "members": ["member_one", "member_two"], "payout_order": ["member_one", "member_two"],
    }, headers=_headers("member_one", "individual"))
    assert response.status_code == 400
    assert response.json()["detail"] == "Selected product is not active for the chosen verified vendor."
