from app.bank.models import BankAuditEvent, BankStaff
from app.models import Commitment, Redemption, Voucher
from app.services.demo_data import DEMO_BANK_ID, DEMO_COMMITMENT_ID, DEMO_REDEMPTION_ID, seed_demo_data


def test_demo_data_seed_is_idempotent_and_contains_the_demo_story(client):
    db = client.app.state.testing_session()
    try:
        first = seed_demo_data(db, reset=True)
        assert first["created"] is True
        db.commit()
        assert db.get(Commitment, DEMO_COMMITMENT_ID).status == "active"
        assert db.get(Redemption, DEMO_REDEMPTION_ID).voucher_code == "SURA-DEMO-LAPTOP-01"
        assert db.get(Voucher, "vch_demo_laptop_cycle_1").status == "redeemed"
        assert db.query(BankStaff).filter(BankStaff.bank_id == DEMO_BANK_ID).count() == 3
        assert db.query(BankAuditEvent).filter(BankAuditEvent.bank_id == DEMO_BANK_ID).count() == 2

        second = seed_demo_data(db)
        assert second["created"] is False

        third = seed_demo_data(db, reset=True)
        assert third["created"] is True
        db.commit()
        assert db.query(BankStaff).filter(BankStaff.bank_id == DEMO_BANK_ID).count() == 3
    finally:
        db.close()


def test_seeded_bank_story_is_available_through_bank_portal_routes(client):
    db = client.app.state.testing_session()
    try:
        seed_demo_data(db, reset=True)
        db.commit()
    finally:
        db.close()

    login = client.post(
        "/v1/bank/login",
        json={"email": "demo.risk@sura.local", "password": "demo-password-never-in-production"},
    )
    assert login.status_code == 200, login.text
    verified = client.post(
        "/v1/bank/login/verify",
        json={"challenge_id": login.json()["challenge_id"], "code": login.json()["demo_code"]},
    )
    assert verified.status_code == 200, verified.text
    headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}

    overview = client.get("/v1/bank/overview", headers=headers)
    assert overview.status_code == 200, overview.text
    assert overview.json()["customers"] == 2

    customer = client.get("/v1/bank/users?bank_customer_id=CUST-DEMO-8241", headers=headers)
    assert customer.status_code == 200, customer.text
    assert customer.json()[0]["user_id"] == "usr_demo_amara"

    commitments = client.get("/v1/bank/commitments", headers=headers)
    assert commitments.status_code == 200, commitments.text
    assert commitments.json()[0]["commitment_id"] == DEMO_COMMITMENT_ID

    settlements = client.get("/v1/bank/settlements", headers=headers)
    assert settlements.status_code == 200, settlements.text
    assert settlements.json()[0]["settlement_id"] == DEMO_REDEMPTION_ID

    audit = client.get("/v1/bank/audit-log", headers=headers)
    assert audit.status_code == 200, audit.text
    assert any(event["event_type"] == "demo_data_seeded" for event in audit.json())
