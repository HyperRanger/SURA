"""Deterministic demo records for the Sura Lock walkthrough.

This module is intentionally invoked by a script, never from application startup.
"""

import json
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import (
    Commitment,
    CommitmentBeneficiary,
    CommitmentMember,
    Contribution,
    Redemption,
    ScoreHistory,
    User,
    Vendor,
)
from app.services.scoring import build_score_snapshot, serialize_score_snapshot

DEMO_USER_IDS = ("usr_demo_amara", "usr_demo_tunde")
DEMO_VENDOR_IDS = ("vnd_demo_electronics", "vnd_demo_education", "vnd_demo_equipment")
DEMO_COMMITMENT_ID = "cmt_demo_laptop_rotation"
DEMO_REDEMPTION_ID = "rdm_demo_laptop_cycle_1"


def _reset_demo_data(db: Session) -> None:
    db.execute(delete(Redemption).where(Redemption.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Contribution).where(Contribution.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentBeneficiary).where(CommitmentBeneficiary.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentMember).where(CommitmentMember.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Commitment).where(Commitment.id == DEMO_COMMITMENT_ID))
    db.execute(delete(ScoreHistory).where(ScoreHistory.user_id.in_(DEMO_USER_IDS)))
    db.execute(delete(User).where(User.id.in_(DEMO_USER_IDS)))


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

    for user_id, name, phone in (
        ("usr_demo_amara", "Amara Okafor", "demo-amara@sura.local"),
        ("usr_demo_tunde", "Tunde Adeyemi", "demo-tunde@sura.local"),
    ):
        user = db.get(User, user_id)
        if user is None:
            db.add(User(id=user_id, name=name, phone=phone, verified_at=now))
        else:
            user.name = name
            user.phone = phone
            user.verified_at = now
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
    db.add_all(
        [
            CommitmentMember(commitment_id=DEMO_COMMITMENT_ID, user_id=user_id, role="contributor", joined_at=now)
            for user_id in DEMO_USER_IDS
        ]
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
    for user_id, score in (("usr_demo_amara", 62), ("usr_demo_tunde", 47)):
        snapshot = build_score_snapshot(base_score=score)
        db.add(
            ScoreHistory(
                id=f"scr_demo_{user_id.rsplit('_', 1)[-1]}", user_id=user_id, score=score,
                breakdown_json=serialize_score_snapshot(snapshot), computed_at=now,
            )
        )
    return {
        "created": True,
        "users": list(DEMO_USER_IDS),
        "commitment_id": DEMO_COMMITMENT_ID,
        "vendor_id": "vnd_demo_electronics",
        "voucher_code": "SURA-DEMO-LAPTOP-01",
    }
