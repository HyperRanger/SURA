"""The contract Sura Lock codes against when a contribution moves the score.

Lock asks two things of this module: call it once and get the new score back, and
be unable to influence that score. Both are pinned here.
"""
import inspect
from datetime import datetime

import pytest

from app.bank.models import BankPartner
from app.models import User
from app.services.score_service import process_contribution

PILLARS = (
    "commitment_behaviour",
    "repayment_behaviour",
    "transaction_stability",
    "institutional_verification",
    "social_reliability",
)


def _seed_lock(client, auth_headers, members):
    for index, user_id in enumerate(members):
        db = client.app.state.testing_session()
        try:
            db.add(
                User(
                    id=user_id,
                    name=user_id.replace("_", " ").title(),
                    phone=f"{user_id}@sura.local",
                    verified_at=datetime.utcnow(),
                    bank_id="bank_handoff",
                )
            )
            db.commit()
        finally:
            db.close()
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": "handoff_vendor"},
        headers=auth_headers("verifier", role="verifier"),
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(members[0])).status_code == 200
    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Handoff Lock",
            "vendor_id": "handoff_vendor",
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": list(members),
            "payout_order": list(members),
        },
        headers=auth_headers(members[0]),
    )
    assert created.status_code == 201
    for user_id in members[1:]:
        assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers(user_id)).status_code == 200
        assert client.post(
            "/v1/commitments/join",
            json={"invite_code": created.json()["invite_code"]},
            headers=auth_headers(user_id),
        ).status_code == 200
    return created.json()["commitment_id"]


def test_contribution_returns_the_new_score_in_one_call(client, auth_headers):
    """Lock should not need a follow-up request to render the new score."""
    db = client.app.state.testing_session()
    try:
        db.add(BankPartner(id="bank_handoff", name="Handoff Bank"))
        db.commit()
    finally:
        db.close()

    commitment_id = _seed_lock(client, auth_headers, ("handoff_a", "handoff_b"))
    response = client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_handoff_a_1"},
        headers=auth_headers("handoff_a"),
    )

    assert response.status_code == 200
    score = response.json()["score"]
    assert set(score["breakdown"]) == set(PILLARS)
    assert score["score"] == sum(score["breakdown"].values())
    assert 0 <= score["score"] <= 1000
    assert score["score_version"] == "trd-5.2-v1"

    # The score in the response is the score the dedicated endpoint reports.
    fetched = client.get("/v1/score/handoff_a", headers=auth_headers("handoff_a")).json()
    assert fetched["score"] == score["score"]
    assert fetched["breakdown"] == score["breakdown"]


def test_a_replayed_contribution_returns_the_same_score_shape(client, auth_headers):
    """A retry must not leave the client guessing, and must not move the score."""
    db = client.app.state.testing_session()
    try:
        db.add(BankPartner(id="bank_handoff", name="Handoff Bank"))
        db.commit()
    finally:
        db.close()

    commitment_id = _seed_lock(client, auth_headers, ("replay_a", "replay_b"))
    payload = {"amount": 1000, "event_id": "evt_replay_a_1"}
    first = client.post(
        f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=auth_headers("replay_a")
    )
    assert first.status_code == 200

    replay = client.post(
        f"/v1/commitments/{commitment_id}/contribute", json=payload, headers=auth_headers("replay_a")
    )
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert replay.json()["score"] == first.json()["score"]


def test_process_contribution_recomputes_from_the_database(client, auth_headers):
    """The importable entry point ignores any claim the caller makes about the score."""
    db = client.app.state.testing_session()
    try:
        db.add(BankPartner(id="bank_handoff", name="Handoff Bank"))
        db.commit()
    finally:
        db.close()

    commitment_id = _seed_lock(client, auth_headers, ("direct_a", "direct_b"))
    assert client.post(
        f"/v1/commitments/{commitment_id}/contribute",
        json={"amount": 1000, "event_id": "evt_direct_a_1"},
        headers=auth_headers("direct_a"),
    ).status_code == 200

    session = client.app.state.testing_session()
    try:
        report = process_contribution(
            session,
            commitment_id,
            "direct_a",
            event_id="evt_direct_a_1",
        )
        session.commit()
    finally:
        session.close()

    assert set(report["breakdown"]) == set(PILLARS)
    assert report["score"] == sum(report["breakdown"].values())
    # One verified member completed one of two cycles. The score has to reflect
    # that partial record, not a perfect one.
    assert 0 < report["score"] < 1000


def test_a_caller_cannot_inflate_a_score_by_asserting_pillars(client, auth_headers):
    """The property the whole pitch rests on: the model decides, the caller does not.

    Taking `pillar_scores` as an argument would let anyone score 500/1000 with no
    recorded behaviour at all. The signature has no such parameter, so this asserts
    the refusal directly rather than trusting a comment.
    """
    signature = inspect.signature(process_contribution)
    for injected in ("pillar_scores", "pillars", "current_total", "total", "signals", "score"):
        assert injected not in signature.parameters

    db = client.app.state.testing_session()
    try:
        db.add(BankPartner(id="bank_handoff", name="Handoff Bank"))
        user = User(id="newcomer", name="Newcomer", phone="newcomer@sura.local", bank_id="bank_handoff")
        db.add(user)
        db.commit()

        report = process_contribution(db, "commitment_that_does_not_exist", "newcomer")
        db.commit()
    finally:
        db.close()

    # A user with no commitments and no verified history scores zero.
    assert report["score"] == 0
    assert report["tier"] == "unverified"
    assert report["breakdown"]["commitment_behaviour"] == 0


def test_unknown_user_is_rejected_rather_than_scored(client, auth_headers):
    db = client.app.state.testing_session()
    try:
        with pytest.raises(ValueError):
            process_contribution(db, "any_commitment", "user_that_does_not_exist")
        db.rollback()
    finally:
        db.close()


def test_score_history_works_before_any_snapshot_exists(client, auth_headers):
    """A brand new member has no history rows, so the endpoint has to fall back.

    This path reads the score through the same helper the contribution response
    uses, which is how a rename in that helper once left a 500 here instead of a
    zero.
    """
    db = client.app.state.testing_session()
    try:
        db.add(BankPartner(id="bank_handoff", name="Handoff Bank"))
        db.add(
            User(
                id="fresh_member",
                name="Fresh Member",
                phone="fresh@sura.local",
                verified_at=datetime.utcnow(),
                bank_id="bank_handoff",
            )
        )
        db.commit()
    finally:
        db.close()

    headers = auth_headers("fresh_member")
    history = client.get("/v1/score/fresh_member/history", headers=headers)
    assert history.status_code == 200
    assert history.json()["entries"] == []

    score = client.get("/v1/score/fresh_member", headers=headers)
    assert score.status_code == 200
    # No commitment history, but the account is institution-verified, which is
    # worth the entry-tier baseline on its own. See ENTRY_TIER_BASELINE.
    expected_baseline = 120
    assert score.json()["score"] == expected_baseline
    assert score.json()["breakdown"]["institutional_verification"] == expected_baseline
    assert score.json()["breakdown"]["commitment_behaviour"] == 0
    assert history.json()["current_score"] == score.json()["score"]
