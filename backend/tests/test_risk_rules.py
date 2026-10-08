"""Risk flag rules, flag review and account restriction decisions.

Items 6, 7 and 8 of the certification. Three properties are protected here, and
they are the ones worth stating out loud:

A rule observes. It never restricts, suspends, or moves money. A rule that could
lock a member would be a rule deciding eligibility, and eligibility belongs to
the fixed-weight model and to a named analyst.

A flag says what it saw. The rows that produced it are in the response, so an
analyst can disagree with the finding rather than trust it.

A restriction is reconstructable. The current state lives on the user for a cheap
check on the money path, and the decision lives in its own record with an actor,
a reason and a lift.
"""

import json
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.bank.models import AccountRestriction, BankAuditEvent, BankPartner, RiskFlag
from app.bank.risk_rules import (
    assert_can_transact,
    run_rules,
)
from app.models import Contribution, ScoreHistory, User
from app.services.demo_data import (
    DEMO_BANK_ID,
    DEMO_COMMITMENT_ID,
    seed_demo_data,
)

OTHER_BANK_ID = "bnk_other"


def _db(client):
    return client.app.state.testing_session()


def _seed(client):
    db = _db(client)
    try:
        seed_demo_data(db, reset=True)
        db.commit()
    finally:
        db.close()


def _headers(auth_headers, user_id="usr_demo_bank_admin", role="bank_admin"):
    return auth_headers(user_id, role=role, institution_id=DEMO_BANK_ID)


# --- item 6: the rule engine -------------------------------------------------


def test_running_the_rules_never_restricts_anybody(client):
    """The whole design rests on this. If it breaks, a rule can lock a member."""
    _seed(client)
    db = _db(client)
    try:
        before = {row.id: row.account_status for row in db.query(User).all()}
        run_rules(db, DEMO_BANK_ID, None)
        after = {row.id: row.account_status for row in db.query(User).all()}
    finally:
        db.close()

    assert before == after


def test_running_the_rules_only_ever_targets_this_bank(client):
    _seed(client)
    db = _db(client)
    try:
        outsider_user = User(
            id="usr_other_member",
            name="Someone Else",
            phone="+2348099999999",
            bank_id=OTHER_BANK_ID,
            role="individual",
        )
        outsider_bank = BankPartner(id=OTHER_BANK_ID, name="Other Bank")
        db.add_all([outsider_bank, outsider_user])
        db.commit()

        run_rules(db, DEMO_BANK_ID, None)

        leaked = db.query(RiskFlag).filter(RiskFlag.user_id == "usr_other_member").count()
    finally:
        db.close()

    assert leaked == 0


def test_a_flag_names_the_rows_that_produced_it(client):
    """An analyst has to be able to disagree with a finding, not just accept it."""
    _seed(client)
    db = _db(client)
    try:
        # Two shortfalls on the same commitment, inside the 90-day window.
        for index in range(2):
            db.add(
                Contribution(
                    id=f"con_short_{index}",
                    commitment_id=DEMO_COMMITMENT_ID,
                    user_id="usr_demo_amara",
                    amount=100,
                    cycle_number=index + 1,
                    event_id=f"evt_short_{index}",
                    status="paid",
                    rule_trace_json="{}",
                    paid_at=datetime.utcnow() - timedelta(days=index + 1),
                )
            )
        db.commit()

        run_rules(db, DEMO_BANK_ID, ["usr_demo_amara"])

        flag = (
            db.query(RiskFlag)
            .filter(RiskFlag.rule == "missed_contributions", RiskFlag.user_id == "usr_demo_amara")
            .one()
        )
        evidence = json.loads(flag.evidence_json)
    finally:
        db.close()

    assert flag.status == "open"
    assert flag.severity in {"medium", "high"}
    shortfalls = evidence["shortfalls"]
    assert len(shortfalls) == 2
    for row in shortfalls:
        # Every finding is traceable to a specific record, with the two numbers
        # that made it a shortfall.
        assert row["contribution_id"]
        assert row["amount_paid"] < row["amount_required"]


def test_rules_do_not_duplicate_a_finding_on_a_second_run(client):
    _seed(client)
    db = _db(client)
    try:
        for index in range(2):
            db.add(
                Contribution(
                    id=f"con_dup_{index}",
                    commitment_id=DEMO_COMMITMENT_ID,
                    user_id="usr_demo_amara",
                    amount=100,
                    cycle_number=index + 1,
                    event_id=f"evt_dup_{index}",
                    status="paid",
                    rule_trace_json="{}",
                    paid_at=datetime.utcnow() - timedelta(days=index + 1),
                )
            )
        db.commit()

        run_rules(db, DEMO_BANK_ID, ["usr_demo_amara"])
        first = db.query(RiskFlag).filter(RiskFlag.rule == "missed_contributions").count()
        run_rules(db, DEMO_BANK_ID, ["usr_demo_amara"])
        second = db.query(RiskFlag).filter(RiskFlag.rule == "missed_contributions").count()
    finally:
        db.close()

    assert first == 1
    # A scheduled job that runs nightly must not fill the review queue with
    # copies of the same finding.
    assert second == first


def test_a_rule_only_fires_on_its_own_signal(client):
    """One shortfall is a bad month, not a pattern."""
    _seed(client)
    db = _db(client)
    try:
        db.add(
            Contribution(
                id="con_single",
                commitment_id=DEMO_COMMITMENT_ID,
                user_id="usr_demo_amara",
                amount=100,
                cycle_number=1,
                event_id="evt_single",
                status="paid",
                rule_trace_json="{}",
                paid_at=datetime.utcnow(),
            )
        )
        db.commit()
        run_rules(db, DEMO_BANK_ID, ["usr_demo_amara"])
        found = db.query(RiskFlag).filter(RiskFlag.rule == "missed_contributions").count()
    finally:
        db.close()

    assert found == 0


def test_score_decline_is_read_from_persisted_history(client):
    """The flag reflects what the score did, not a recomputation that might differ."""
    _seed(client)
    db = _db(client)
    try:
        db.add(
            ScoreHistory(
                id="sh_before",
                user_id="usr_demo_amara",
                bank_id=DEMO_BANK_ID,
                score=700,
                breakdown_json="{}",
                computed_at=datetime.utcnow() - timedelta(days=20),
            )
        )
        db.add(
            ScoreHistory(
                id="sh_after",
                user_id="usr_demo_amara",
                bank_id=DEMO_BANK_ID,
                score=500,
                breakdown_json="{}",
                computed_at=datetime.utcnow(),
            )
        )
        db.commit()

        run_rules(db, DEMO_BANK_ID, ["usr_demo_amara"])

        flag = db.query(RiskFlag).filter(RiskFlag.rule == "score_decline").one()
        evidence = json.loads(flag.evidence_json)
    finally:
        db.close()

    assert evidence["score_before"] == 700
    assert evidence["score_after"] == 500
    assert evidence["decline_points"] == 200


# --- item 7: flag review ----------------------------------------------------


def test_resolving_a_flag_records_who_and_what(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)

    listed = client.get("/v1/bank/flags", headers=headers)
    assert listed.status_code == 200, listed.text
    flag_id = listed.json()[0]["flag_id"]

    resolved = client.post(
        f"/v1/bank/flags/{flag_id}/resolve",
        headers=headers,
        json={"action": "confirmed", "note": "Confirmed by phone with the member."},
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["resolved_by"] == "usr_demo_bank_admin"
    assert resolved.json()["status"] != "open"


def test_a_second_review_does_not_overwrite_the_first_decision(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)
    flag_id = client.get("/v1/bank/flags", headers=headers).json()[0]["flag_id"]

    first = client.post(
        f"/v1/bank/flags/{flag_id}/resolve",
        headers=headers,
        json={"action": "confirmed", "note": "First decision."},
    )
    assert first.status_code == 200, first.text

    # Silently replacing the original decision would destroy the audit trail the
    # decision exists to provide.
    second = client.post(
        f"/v1/bank/flags/{flag_id}/resolve",
        headers=headers,
        json={"action": "dismissed", "note": "Second decision."},
    )
    assert second.status_code == 409, second.text


def test_severity_is_from_a_closed_set(client):
    """A free-text severity becomes a flag no dashboard filter matches."""
    from app.bank.risk_rules import FLAG_SEVERITIES

    assert {"low", "medium", "high", "critical"} == FLAG_SEVERITIES


def test_a_flag_appears_in_the_member_list(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)
    client.post(
        f"/v1/bank/flags/{client.get('/v1/bank/flags', headers=headers).json()[0]['flag_id']}/resolve",
        headers=headers,
        json={"action": "confirmed", "note": "Reviewed."},
    )

    listed = client.get("/v1/bank/flags?status=resolved", headers=headers)
    assert listed.status_code == 200, listed.text
    assert all(row["status"] != "open" for row in listed.json())


# --- item 8: restriction decisions ------------------------------------------


def test_restriction_blocks_contributions_and_voucher_redemption(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)

    applied = client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "restricted", "reason": "Under review."},
    )
    assert applied.status_code == 200, applied.text

    db = _db(client)
    try:
        # Refused at the point of payment, so a restriction applied mid-session
        # takes effect on the next contribution rather than at next sign-in.
        with pytest.raises(HTTPException) as caught:
            assert_can_transact(db, "usr_demo_amara")
        assert caught.value.status_code == 403
        assert "review" in caught.value.detail.lower()

        # A member the bank said nothing about is unaffected.
        assert_can_transact(db, "usr_demo_tunde")
    finally:
        db.close()


def test_a_restriction_blocks_a_real_contribution(client, auth_headers):
    """End to end, through the endpoint a member actually calls."""
    _seed(client)
    headers = _headers(auth_headers)
    client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "restricted", "reason": "Under review."},
    )

    member = auth_headers("usr_demo_amara", role="individual")
    refused = client.post(
        f"/v1/commitments/{DEMO_COMMITMENT_ID}/contribute",
        headers=member,
        json={"amount": 1000, "event_id": "evt_restricted_member"},
    )
    assert refused.status_code == 403, refused.text
    assert "review" in refused.json()["detail"].lower()


def test_a_restriction_does_not_block_read_access(client, auth_headers):
    """Otherwise a member cannot find out why they cannot transact."""
    _seed(client)
    headers = _headers(auth_headers)
    client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "restricted", "reason": "Under review."},
    )

    member = auth_headers("usr_demo_amara", role="individual")
    assert client.get("/v1/me", headers=member).status_code == 200


def test_a_suspension_blocks_sign_in_immediately(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)
    client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "suspended", "reason": "Suspected account takeover."},
    )

    db = _db(client)
    try:
        from core.security import create_token

        token = create_token("usr_demo_amara", {"role": "individual"})
        member = {"Authorization": f"Bearer {token}"}
    finally:
        db.close()

    refused = client.get("/v1/me", headers=member)
    assert refused.status_code == 403
    assert "takeover" in refused.json()["detail"].lower()


def test_a_restriction_is_recorded_as_its_own_decision(client, auth_headers):
    """A bare status column cannot answer who decided this and why."""
    _seed(client)
    headers = _headers(auth_headers)
    client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "restricted", "reason": "Under review."},
    )

    db = _db(client)
    try:
        record = db.query(AccountRestriction).one()
        assert record.user_id == "usr_demo_amara"
        assert record.actor_id == "usr_demo_bank_admin"
        assert record.reason == "Under review."
        assert record.lifted_at is None
    finally:
        db.close()


def test_reinstating_lifts_the_record_and_says_who(client, auth_headers):
    _seed(client)
    headers = _headers(auth_headers)
    client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "restricted", "reason": "Under review."},
    )
    lifted = client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "reinstated", "reason": "Review closed, no issue found."},
    )
    assert lifted.status_code == 200, lifted.text

    db = _db(client)
    try:
        records = db.query(AccountRestriction).order_by(AccountRestriction.created_at).all()
        user = db.get(User, "usr_demo_amara")
        # Both decisions survive. The trail is not overwritten by the outcome.
        assert len(records) == 2
        assert records[0].lifted_at is not None
        assert records[0].lifted_by == "usr_demo_bank_admin"
        assert user.account_status == "active"
        assert user.restriction_reason is None
    finally:
        db.close()


def test_a_restriction_needs_a_reason(client, auth_headers):
    """A restriction nobody can explain is not a usable control."""
    _seed(client)
    headers = _headers(auth_headers)

    refused = client.post(
        "/v1/bank/users/usr_demo_amara/restriction",
        headers=headers,
        json={"action": "restricted", "reason": ""},
    )
    assert refused.status_code == 422, refused.text


def test_restricting_the_same_state_twice_is_refused(client, auth_headers):
    """Otherwise the audit trail fills with no-op decisions."""
    _seed(client)
    headers = _headers(auth_headers)
    body = {"action": "restricted", "reason": "Under review."}
    assert client.post("/v1/bank/users/usr_demo_amara/restriction", headers=headers, json=body).status_code == 200

    repeat = client.post("/v1/bank/users/usr_demo_amara/restriction", headers=headers, json=body)
    assert repeat.status_code == 409, repeat.text


def test_one_bank_cannot_restrict_another_banks_member(client, auth_headers):
    _seed(client)
    db = _db(client)
    try:
        db.add(BankPartner(id=OTHER_BANK_ID, name="Other Bank"))
        db.add(
            User(
                id="usr_other_member",
                name="Someone Else",
                phone="+2348099999999",
                bank_id=OTHER_BANK_ID,
                role="individual",
            )
        )
        db.commit()
    finally:
        db.close()

    headers = _headers(auth_headers)
    refused = client.post(
        "/v1/bank/users/usr_other_member/restriction",
        headers=headers,
        json={"action": "restricted", "reason": "Not my member."},
    )
    assert refused.status_code == 404, refused.text


def test_bank_staff_can_end_a_members_sessions(client, auth_headers):
    """The response to a session being in use by someone who should not have it."""
    _seed(client)
    headers = _headers(auth_headers)

    from core.security import create_token

    # Backdated, because the invalidation instant is only comparable at whole
    # seconds: a token minted in the same second as the revocation is genuinely
    # undecidable and is treated as still valid.
    token = create_token("usr_demo_amara", {"role": "individual"}, backdate_seconds=5)
    member = {"Authorization": f"Bearer {token}"}
    assert client.get("/v1/me", headers=member).status_code == 200

    revoked = client.post("/v1/bank/users/usr_demo_amara/sessions/revoke", headers=headers)
    assert revoked.status_code == 200, revoked.text

    after = client.get("/v1/me", headers=member)
    assert after.status_code == 401

    db = _db(client)
    try:
        events = [
            row.event_type
            for row in db.query(BankAuditEvent).filter(BankAuditEvent.subject_id == "usr_demo_amara")
        ]
        assert "member_sessions_revoked" in events
    finally:
        db.close()
