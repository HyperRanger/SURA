"""Phase 7 vendor matching is advisory, explainable, and deterministic."""

from datetime import datetime

from app.main import app
from app.models import Redemption, User, Vendor
from core.security import create_token


def _headers(user_id: str, role: str = "individual") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, {'role': role})}"}


def test_vendor_recommendations_rank_by_documented_facts_and_explain_every_score(client):
    db = app.state.testing_session()
    try:
        now = datetime.utcnow()
        db.add_all(
            [
                User(id="matching_member", name="Matching Member", phone="2348000000711", role="individual"),
                Vendor(id="match_electronics", name="Able Electronics", category="electronics", verified_at=now),
                Vendor(id="match_groceries", name="Bright Groceries", category="groceries", verified_at=now),
                Vendor(id="unverified_vendor", name="Hidden Vendor", category="electronics"),
                Redemption(
                    id="matching_redemption",
                    commitment_id="matching_commitment",
                    beneficiary_id="matching_member",
                    vendor_id="match_electronics",
                    cycle_number=1,
                    amount=10000,
                    voucher_code="SURA-MATCH-001",
                    status="settled",
                    redeemed_at=now,
                ),
            ]
        )
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/v1/app/recommendations/vendors?category=electronics&target_amount=10000",
        headers=_headers("matching_member"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["advisory"] is True
    assert body["group_recommendations_available"] is False
    assert body["unavailable_signals"] == ["location", "external fulfilment history"]
    assert [item["vendor_id"] for item in body["recommendations"]] == [
        "match_electronics",
        "match_groceries",
    ]
    first = body["recommendations"][0]
    assert first["recommendation_score"] == 100
    assert first["factor_points"] == {
        "verification": 30,
        "category_fit": 30,
        "amount_fit": 20,
        "in_sura_redemption_history": 20,
    }
    assert len(first["reasons"]) == 4


def test_vendor_recommendations_are_member_only_and_validate_query_values(client):
    db = app.state.testing_session()
    try:
        db.add_all(
            [
                User(id="matching_member_two", name="Second Member", phone="2348000000712", role="individual"),
                User(id="vendor_actor", name="Vendor Actor", phone="2348000000713", role="vendor"),
            ]
        )
        db.commit()
    finally:
        db.close()

    assert client.get(
        "/v1/app/recommendations/vendors",
        headers=_headers("vendor_actor", "vendor"),
    ).status_code == 403
    assert client.get(
        "/v1/app/recommendations/vendors?target_amount=0",
        headers=_headers("matching_member_two"),
    ).status_code == 400
    assert client.get(
        "/v1/app/recommendations/vendors?limit=21",
        headers=_headers("matching_member_two"),
    ).status_code == 400
