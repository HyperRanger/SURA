from app.bank.models import BankAuditEvent, BankPartner, BankStaff, RiskFlag
from app.models import Commitment, CommitmentMember, Redemption, ScoreHistory, User, Voucher
from app.services.demo_data import (
    DEMO_BANK_ID,
    DEMO_COMMITMENT_ID,
    DEMO_PORTFOLIO_BALANCE_SNAPSHOT,
    DEMO_PORTFOLIO_SPECS,
    DEMO_REDEMPTION_ID,
    SIM_BANK_CUSTOMER_ID,
    seed_demo_data,
)


def test_demo_data_seed_is_idempotent_and_contains_the_demo_story(client):
    db = client.app.state.testing_session()
    try:
        first = seed_demo_data(db, reset=True)
        assert first["created"] is True
        db.commit()
        assert db.get(Commitment, DEMO_COMMITMENT_ID).status == "active"
        assert db.get(Redemption, DEMO_REDEMPTION_ID).voucher_code == "SURA-DEMO-LAPTOP-01"
        assert db.get(Voucher, "vch_demo_laptop_cycle_1").status == "redeemed"
        assert first["user_count"] == 90
        assert db.query(User).filter(User.id.in_(first["users"])).count() == 90
        assert first["sim_bank_customer_id"] == SIM_BANK_CUSTOMER_ID
        assert first["portfolio_available_balance_snapshot"] == DEMO_PORTFOLIO_BALANCE_SNAPSHOT
        portfolio_user_ids = [spec[0] for spec in DEMO_PORTFOLIO_SPECS]
        assert db.query(User).filter(User.id.in_(portfolio_user_ids)).count() == 20
        assert db.query(BankPartner).filter(BankPartner.id == DEMO_BANK_ID).count() == 1
        assert first["partner_bank"]["customer_count"] == 90
        assert [bank["customer_count"] for bank in first["source_institutions"]] == [16, 14, 12, 10, 10, 8]
        assert first["commitment_count"] == 25
        commitments = db.query(Commitment).filter(Commitment.id.like("cmt_demo_%")).all()
        assert len(commitments) == 25
        assert {row.status for row in commitments} == {"active", "pending_members", "completed"}
        assert sum(row.status == "active" for row in commitments) == 10
        assert sum(row.status == "pending_members" for row in commitments) == 7
        assert sum(row.status == "completed" for row in commitments) == 8
        member_ids = {
            row[0]
            for row in db.query(CommitmentMember.user_id)
            .filter(CommitmentMember.commitment_id.in_([row.id for row in commitments]))
            .distinct()
            .all()
        }
        assert member_ids == set(first["users"])
        assert db.query(RiskFlag).filter(RiskFlag.bank_id == DEMO_BANK_ID).count() == 12
        assert db.query(RiskFlag.status).filter(RiskFlag.bank_id == DEMO_BANK_ID).distinct().count() == 4
        assert db.query(ScoreHistory.score).filter(ScoreHistory.user_id.in_(first["users"])).distinct().count() >= 4
        assert db.query(BankStaff).count() == 1
        assert db.get(User, "usr_demo_amara").available_balance > 0
        assert db.query(BankAuditEvent).filter(BankAuditEvent.bank_id == DEMO_BANK_ID).count() == 2

        second = seed_demo_data(db)
        assert second["created"] is False

        third = seed_demo_data(db, reset=True)
        assert third["created"] is True
        db.commit()
        assert db.query(BankStaff).count() == 1
    finally:
        db.close()


def test_seed_reset_removes_legacy_demo_flags_before_deleting_members(client):
    """A database seeded before the multi-bank portfolio must still reset."""
    db = client.app.state.testing_session()
    try:
        seed_demo_data(db, reset=True)
        db.add(BankPartner(id="bnk_demo", name="Legacy Demo Bank"))
        db.add(RiskFlag(
            id="flag_legacy_demo_tunde",
            bank_id="bnk_demo",
            user_id="usr_demo_tunde",
            rule="legacy_demo_rule",
            severity="low",
            status="open",
            evidence_json="{}",
        ))
        # Represents a record from an older demo shortcut. It is not one of the
        # fixed reset identities, so its legacy parent must be retained rather
        # than causing reset to fail.
        db.add(User(
            id="usr_legacy_demo_extra",
            name="Legacy Demo Extra",
            phone="legacy.demo.extra@sura.local",
            bank_id="bnk_demo",
        ))
        db.commit()

        result = seed_demo_data(db, reset=True)
        db.commit()

        assert result["created"] is True
        assert db.query(RiskFlag).filter(RiskFlag.id == "flag_legacy_demo_tunde").count() == 0
        assert db.get(User, "usr_demo_tunde") is not None
        assert db.get(User, "usr_legacy_demo_extra") is not None
        assert db.get(BankPartner, "bnk_demo") is not None
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
        json={"email": "demo.admin@sura.local", "password": "demo-password-never-in-production"},
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
    assert overview.json()["customers"] == 90
    assert overview.json()["portfolio_available_balance_snapshot"] == DEMO_PORTFOLIO_BALANCE_SNAPSHOT

    customer = client.get("/v1/bank/users?bank_customer_id=CUST-DEMO-8241", headers=headers)
    assert customer.status_code == 200, customer.text
    assert customer.json()[0]["user_id"] == "usr_demo_amara"
    assert customer.json()[0]["available_balance"] > 0
    assert customer.json()[0]["source_institution"] == {"institution_id": "inst_banter", "name": "Banter Bank"}

    member_login = client.post(
        "/v1/auth/demo-token",
        json={"user_id": "usr_demo_amara", "otp_code": "123456"},
    )
    assert member_login.status_code == 200, member_login.text
    member_score = client.get(
        "/v1/score/usr_demo_amara",
        headers={"Authorization": f"Bearer {member_login.json()['access_token']}"},
    )
    assert member_score.status_code == 200, member_score.text
    assert "available_balance" not in member_score.json()

    commitments = client.get("/v1/bank/commitments", headers=headers)
    assert commitments.status_code == 200, commitments.text
    assert DEMO_COMMITMENT_ID in {row["commitment_id"] for row in commitments.json()}

    settlements = client.get("/v1/bank/settlements", headers=headers)
    assert settlements.status_code == 200, settlements.text
    assert settlements.json()[0]["settlement_id"] == DEMO_REDEMPTION_ID

    audit = client.get("/v1/bank/audit-log", headers=headers)
    assert audit.status_code == 200, audit.text
    assert any(event["event_type"] == "demo_data_seeded" for event in audit.json())
