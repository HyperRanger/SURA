"""Deterministic demo records for the Sura Lock walkthrough.

This module is intentionally invoked by a script, never from application startup.
"""

import json
from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import (
    AccountActivitySignal,
    AuthChallenge,
    Commitment,
    CommitmentActivity,
    CommitmentBeneficiary,
    CommitmentMember,
    Contribution,
    Redemption,
    ScoreHistory,
    User,
    Vendor,
    Voucher,
)
from app.bank.models import BankAuditEvent, BankPartner, BankStaff, RiskFlag
from core.passwords import hash_password
from app.services.score_service import record_score_snapshot

DEMO_USER_IDS = ("usr_demo_amara", "usr_demo_tunde")
DEMO_BANK_STAFF_USER_IDS = (
    "usr_demo_bank_admin",
    "usr_demo_bank_risk",
    "usr_demo_bank_integration",
)
DEMO_VENDOR_IDS = ("vnd_demo_electronics", "vnd_demo_education", "vnd_demo_equipment")
DEMO_COMMITMENT_ID = "cmt_demo_laptop_rotation"
DEMO_REDEMPTION_ID = "rdm_demo_laptop_cycle_1"
DEMO_BANK_ID = "bnk_demo"
DEMO_BANK_PASSWORD = "demo-password-never-in-production"


def _reset_demo_data(db: Session) -> None:
    demo_user_ids = (*DEMO_USER_IDS, *DEMO_BANK_STAFF_USER_IDS)
    db.execute(delete(BankAuditEvent).where(BankAuditEvent.bank_id == DEMO_BANK_ID))
    db.execute(delete(RiskFlag).where(RiskFlag.bank_id == DEMO_BANK_ID))
    db.execute(delete(BankStaff).where(BankStaff.user_id.in_(DEMO_BANK_STAFF_USER_IDS)))
    db.execute(delete(AuthChallenge).where(AuthChallenge.user_id.in_(demo_user_ids)))
    db.execute(delete(AccountActivitySignal).where(AccountActivitySignal.user_id.in_(DEMO_USER_IDS)))
    db.execute(delete(Redemption).where(Redemption.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Voucher).where(Voucher.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Contribution).where(Contribution.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentActivity).where(CommitmentActivity.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentBeneficiary).where(CommitmentBeneficiary.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentMember).where(CommitmentMember.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Commitment).where(Commitment.id == DEMO_COMMITMENT_ID))
    db.execute(delete(ScoreHistory).where(ScoreHistory.user_id.in_(DEMO_USER_IDS)))
    db.execute(delete(User).where(User.id.in_(demo_user_ids)))


def seed_demo_data(db: Session, *, reset: bool = False) -> dict[str, object]:
    """Create the fixed demo story and optionally replace only its own records."""
    if reset:
        _reset_demo_data(db)

    existing = db.get(Commitment, DEMO_COMMITMENT_ID)
    if existing is not None:
        return {"created": False, "commitment_id": DEMO_COMMITMENT_ID, "message": "Demo data already exists."}

    now = datetime.utcnow()
    vendors = (
        ("vnd_demo_electronics", "Sura Demo Electronics", "electronics"),
        ("vnd_demo_education", "Sura Demo Education", "education"),
        ("vnd_demo_equipment", "Sura Demo Equipment", "equipment"),
    )
    for vendor_id, name, category in vendors:
        vendor = db.get(Vendor, vendor_id)
        if vendor is None:
            db.add(Vendor(id=vendor_id, name=name, category=category, verified_at=now))
        else:
            vendor.name = name
            vendor.category = category
            vendor.verified_at = now

    bank = db.get(BankPartner, DEMO_BANK_ID)
    if bank is None:
        db.add(BankPartner(id=DEMO_BANK_ID, name="Demo Bank", created_at=now))
    else:
        bank.name = "Demo Bank"

    for user_id, name, phone in (
        ("usr_demo_amara", "Amara Okafor", "demo-amara@sura.local"),
        ("usr_demo_tunde", "Tunde Adeyemi", "demo-tunde@sura.local"),
    ):
        user = db.get(User, user_id)
        if user is None:
            db.add(User(
                id=user_id,
                name=name,
                phone=phone,
                verified_at=now,
                bank_id=DEMO_BANK_ID,
                bank_customer_id="CUST-DEMO-8241" if user_id == "usr_demo_amara" else "CUST-DEMO-8242",
                role="individual",
                context="student" if user_id == "usr_demo_amara" else "trader",
                terms_accepted_at=now,
                phone_verified_at=now,
            ))
        else:
            user.name = name
            user.phone = phone
            user.verified_at = now
            user.bank_id = DEMO_BANK_ID
            user.bank_customer_id = "CUST-DEMO-8241" if user_id == "usr_demo_amara" else "CUST-DEMO-8242"
            user.role = "individual"
            user.context = "student" if user_id == "usr_demo_amara" else "trader"
            user.terms_accepted_at = now
            user.phone_verified_at = now

    staff_specs = (
        ("usr_demo_bank_admin", "Demo Bank Administrator", "demo.admin@sura.local", "bank_admin", ["bank:developer:write"], "2347065250811"),
        ("usr_demo_bank_risk", "Demo Bank Risk Analyst", "demo.risk@sura.local", "bank_risk_analyst", ["bank:overview:read", "bank:users:read", "bank:commitments:read", "bank:flags:read", "bank:flags:write", "bank:audit:read", "bank:settlements:read"], "2347065250812"),
        ("usr_demo_bank_integration", "Demo Bank Integration Engineer", "demo.integration@sura.local", "bank_integration_engineer", ["bank:developer:write"], "2347065250813"),
    )
    for user_id, name, email, role, permissions, mfa_phone in staff_specs:
        user = db.get(User, user_id)
        if user is None:
            user = User(id=user_id, name=name, phone=email)
            db.add(user)
        user.name = name
        user.phone = email
        user.role = role
        user.bank_id = DEMO_BANK_ID
        user.verified_at = now
        user.phone_verified_at = now

    # PostgreSQL enforces the staff-to-user foreign key immediately. Flush the
    # user rows before adding their BankStaff records; SQLite's test defaults do
    # not reliably expose this ordering requirement.
    db.flush()

    for user_id, name, email, role, permissions, mfa_phone in staff_specs:
        staff = db.query(BankStaff).filter(BankStaff.user_id == user_id).one_or_none()
        if staff is None:
            staff = BankStaff(id=f"stf_{user_id[4:]}", user_id=user_id)
            db.add(staff)
        staff.bank_id = DEMO_BANK_ID
        staff.email = email
        staff.password_hash = hash_password(DEMO_BANK_PASSWORD)
        staff.role = role
        staff.permissions_json = json.dumps(permissions)
        staff.mfa_phone = mfa_phone
        staff.status = "active"
        staff.failed_password_attempts = 0
        staff.locked_until = None
        staff.password_changed_at = now
    db.add(
        Commitment(
            id=DEMO_COMMITMENT_ID,
            creator_id="usr_demo_amara",
            type="rotating",
            title="Laptop Fund — Demo Rotation",
            vendor_id="vnd_demo_electronics",
            contribution_amount=5000,
            frequency="weekly",
            cycles=2,
            status="active",
            invite_code="SURA-DEMO-LAPTOP",
            payout_order_json=json.dumps(["usr_demo_amara", "usr_demo_tunde"]),
            current_cycle_number=2,
            completed_cycle_count=1,
            created_at=now,
        )
    )
    for user_id in DEMO_USER_IDS:
        for offset_days in (21, 14, 7, 0):
            db.add(AccountActivitySignal(
                id=f"act_demo_{user_id}_{offset_days}",
                user_id=user_id,
                institution_id=None,
                source="simulated_bank_rail",
                occurred_at=now - timedelta(days=offset_days),
            ))
    db.add(RiskFlag(
        id="flag_demo_tunde_review",
        bank_id=DEMO_BANK_ID,
        user_id="usr_demo_tunde",
        rule="demo_account_review",
        severity="low",
        status="open",
        evidence_json='{"note":"Seeded demo review flag"}',
        created_at=now,
    ))
    db.add_all(
        [
            CommitmentMember(commitment_id=DEMO_COMMITMENT_ID, user_id=user_id, role="contributor", joined_at=now)
            for user_id in DEMO_USER_IDS
        ]
    )
    db.add_all(
        [
            CommitmentActivity(
                id="act_demo_commitment_created", commitment_id=DEMO_COMMITMENT_ID,
                event_type="commitment_created", actor_user_id="usr_demo_amara",
                detail_json='{"title":"Laptop Fund - Demo Rotation"}', occurred_at=now - timedelta(days=14),
            ),
            CommitmentActivity(
                id="act_demo_cycle_paid", commitment_id=DEMO_COMMITMENT_ID,
                event_type="cycle_paid", cycle_number=1,
                detail_json='{"beneficiary_id":"usr_demo_amara","amount":10000}', occurred_at=now - timedelta(days=7),
            ),
            CommitmentActivity(
                id="act_demo_voucher_redeemed", commitment_id=DEMO_COMMITMENT_ID,
                event_type="voucher_redeemed", actor_user_id="usr_demo_amara", cycle_number=1,
                detail_json='{"vendor_id":"vnd_demo_electronics","amount":10000}', occurred_at=now - timedelta(days=6),
            ),
            CommitmentActivity(
                id="act_demo_cycle_two_contribution", commitment_id=DEMO_COMMITMENT_ID,
                event_type="contribution_recorded", actor_user_id="usr_demo_amara", cycle_number=2,
                detail_json='{"amount":5000,"event_id":"evt_demo_amara_cycle_2"}', occurred_at=now - timedelta(days=1),
            ),
        ]
    )
    db.add(
        Voucher(
            id="vch_demo_laptop_cycle_1", commitment_id=DEMO_COMMITMENT_ID,
            beneficiary_id="usr_demo_amara", vendor_id="vnd_demo_electronics", cycle_number=1,
            amount=10000, code="SURA-DEMO-LAPTOP-01", status="redeemed",
            issued_at=now - timedelta(days=7), redeemed_at=now - timedelta(days=6),
        )
    )
    db.add_all(
        [
            CommitmentBeneficiary(
                id="bnf_demo_laptop_cycle_1", commitment_id=DEMO_COMMITMENT_ID, cycle_number=1,
                user_id="usr_demo_amara", payout_amount=10000, status="redeemed",
            ),
            CommitmentBeneficiary(
                id="bnf_demo_laptop_cycle_2", commitment_id=DEMO_COMMITMENT_ID, cycle_number=2,
                user_id="usr_demo_tunde", payout_amount=10000, status="scheduled",
            ),
        ]
    )
    db.add_all(
        [
            Contribution(
                id="ctr_demo_amara_cycle_1", commitment_id=DEMO_COMMITMENT_ID, cycle_number=1,
                user_id="usr_demo_amara", amount=5000, event_id="evt_demo_amara_cycle_1", status="full", rule_trace_json="{}", paid_at=now,
            ),
            Contribution(
                id="ctr_demo_tunde_cycle_1", commitment_id=DEMO_COMMITMENT_ID, cycle_number=1,
                user_id="usr_demo_tunde", amount=5000, event_id="evt_demo_tunde_cycle_1", status="full", rule_trace_json="{}", paid_at=now,
            ),
            Contribution(
                id="ctr_demo_amara_cycle_2", commitment_id=DEMO_COMMITMENT_ID, cycle_number=2,
                user_id="usr_demo_amara", amount=5000, event_id="evt_demo_amara_cycle_2", status="full", rule_trace_json="{}", paid_at=now,
            ),
        ]
    )
    db.add(
        Redemption(
            id=DEMO_REDEMPTION_ID, commitment_id=DEMO_COMMITMENT_ID, beneficiary_id="usr_demo_amara",
            vendor_id="vnd_demo_electronics", cycle_number=1, amount=10000,
            voucher_code="SURA-DEMO-LAPTOP-01", status="settled", redeemed_at=now,
        )
    )
    db.flush()
    for user_id in DEMO_USER_IDS:
        record_score_snapshot(
            db,
            user_id,
            event_type="demo_seed",
            reason="Seeded Sura Lock history for the demo environment.",
            source_id=DEMO_COMMITMENT_ID,
        )
    db.add_all(
        [
            BankAuditEvent(
                id="audit_demo_bank_seed", bank_id=DEMO_BANK_ID, actor_id="system",
                event_type="demo_data_seeded", subject_type="commitment", subject_id=DEMO_COMMITMENT_ID,
                detail_json='{"story":"active laptop rotation with one redeemed cycle"}', occurred_at=now,
            ),
            BankAuditEvent(
                id="audit_demo_score_visible", bank_id=DEMO_BANK_ID, actor_id="usr_demo_bank_risk",
                event_type="customer_score_viewed", subject_type="user", subject_id="usr_demo_amara",
                detail_json='{"demo":true}', occurred_at=now - timedelta(hours=1),
            ),
        ]
    )
    return {
        "created": True,
        "users": list(DEMO_USER_IDS),
        "bank_id": DEMO_BANK_ID,
        "bank_staff": [email for _, _, email, _, _, _ in staff_specs],
        "commitment_id": DEMO_COMMITMENT_ID,
        "vendor_id": "vnd_demo_electronics",
        "voucher_code": "SURA-DEMO-LAPTOP-01",
    }
