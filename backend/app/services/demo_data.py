"""Deterministic demo records for the Sura Lock walkthrough.

This module is intentionally invoked by a script, never from application startup.
"""

import json
from datetime import datetime, timedelta

from sqlalchemy import delete, or_
from sqlalchemy.orm import Session

from app.bank.models import (
    AccountRestriction,
    BankApiKey,
    BankAuditEvent,
    BankPartner,
    BankStaff,
    RiskFlag,
    WebhookDelivery,
    WebhookSubscription,
)
from app.models import (
    AccountActivitySignal,
    AuthChallenge,
    Commitment,
    CommitmentActivity,
    CommitmentBeneficiary,
    CommitmentMember,
    Contribution,
    Redemption,
    PlatformAuditEvent,
    ScoreHistory,
    SessionRevocation,
    User,
    UserConsent,
    Vendor,
    Voucher,
)
from app.services.score_service import record_score_snapshot
from core.passwords import hash_password

DEMO_USER_IDS = ("usr_demo_amara", "usr_demo_tunde")
DEMO_BANK_STAFF_USER_IDS = ("usr_demo_bank_admin",)
LEGACY_DEMO_BANK_STAFF_USER_IDS = (
    "usr_demo_bank_admin",
    "usr_demo_bank_risk",
    "usr_demo_bank_integration",
)
DEMO_VENDOR_IDS = ("vnd_demo_electronics", "vnd_demo_education", "vnd_demo_equipment")
DEMO_COMMITMENT_ID = "cmt_demo_laptop_rotation"
DEMO_REDEMPTION_ID = "rdm_demo_laptop_cycle_1"
DEMO_BANK_ID = "bnk_banter"
DEMO_BANK_PASSWORD = "demo-password-never-in-production"

# The portfolio deliberately varies bank tenancy, onboarding context, balance,
# consent, score inputs, and account state. It is deterministic so a reset
# produces the same screen-recording story every time.
DEMO_BANKS = (
    ("bnk_banter", "Banter Bank", 20),
    ("bnk_chai", "Chai Bank", 14),
    ("bnk_kolo", "Kolo Bank", 12),
    ("bnk_jollof", "Jollof Bank", 10),
    ("bnk_gbedu", "Gbedu Bank", 8),
    ("bnk_sapa", "Sapa Bank", 6),
)

_EXTRA_DEMO_NAMES = (
    "Bisi Lawal", "Chidi Nwosu", "Dami Akinola", "Efe Ighalo", "Fola Bamidele",
    "Gburugburu Obi", "Hauwa Bello", "Ireti Cole", "Jide Martins", "Kemi Sanni",
    "Lekan Yusuf", "Muna Kalu", "Nene Osei", "Ola Peters", "Pemi Adebayo",
    "Qudus Balogun", "Rukayat Musa", "Seyi Adekunle", "Tari Briggs", "Uche Nnamdi",
    "Vera Eze", "Wale Johnson", "Xena Okoro", "Yinka Fashola", "Zainab Garba",
    "Adaeze Ibe", "Boma George", "Chuka Ekwueme", "Dera Nwachukwu", "Ebuka Obi",
    "Favour Umeh", "Ganiyu Afolabi", "Hadiza Sani", "Ifeanyi Nduka", "Jumoke Adeyemi",
    "Kelechi Obi", "Lami Abdullahi", "Moyo Adeniran", "Nkiru Okafor", "Ogechi Ude",
    "Precious James", "Raliat Ibrahim", "Somi Eze", "Tolu Ojo", "Ugochukwu Nwankwo",
    "Vicky Okon", "Wuraola Taiwo", "Xavier Ekanem", "Yejide Adewale", "Zara Mohammed",
    "Ayo Bassey", "Bunmi Aina", "Cynthia Ezeani", "Deji Ajayi", "Ese Akpan",
    "Feyi Akinyemi", "Gbemisola Ayo", "Halima Tanko", "Ikenna Okeke", "Jemima Udo",
    "Kola Ogunleye", "Lola Nwafor", "Mariam Danjuma", "Nnamdi Okafor", "Oluwatobi Akin",
    "Pere Davies", "Rasheed Adebisi", "Sade Olatunji",
)

_BANK_ASSIGNMENTS = tuple(bank_id for bank_id, _, count in DEMO_BANKS for _ in range(count))
_CONTEXTS = ("student", "trader", "freelancer", "other")
_BALANCES = (0, 450, 1_250, 3_800, 8_500, 15_000, 27_500, 43_000, 68_000, 125_000, 240_000, 510_000)
_NON_ACTIVE_STATUSES = {17: "restricted", 36: "suspended", 58: "restricted", 67: "restricted"}


def _customer_specs() -> tuple[tuple[str, str, str, str, str, int, str], ...]:
    names = (("usr_demo_amara", "Amara Okafor"), ("usr_demo_tunde", "Tunde Adeyemi")) + tuple(
        (f"usr_demo_member_{index:02d}", name)
        for index, name in enumerate(_EXTRA_DEMO_NAMES, start=3)
    )
    assert len(names) == 70
    return tuple(
        (
            user_id,
            name,
            f"demo.member.{index:02d}@sura.local" if index > 2 else f"demo-{name.split()[0].lower()}@sura.local",
            _BANK_ASSIGNMENTS[index - 1],
            _CONTEXTS[(index - 1) % len(_CONTEXTS)],
            _BALANCES[(index * 3) % len(_BALANCES)],
            _NON_ACTIVE_STATUSES.get(index, "active"),
        )
        for index, (user_id, name) in enumerate(names, start=1)
    )


DEMO_CUSTOMER_SPECS = _customer_specs()
DEMO_CUSTOMER_IDS = tuple(row[0] for row in DEMO_CUSTOMER_SPECS)
DEMO_BANK_IDS = tuple(row[0] for row in DEMO_BANKS)
DEMO_RESET_BANK_IDS = (*DEMO_BANK_IDS, "bnk_demo")


def _bank_customer_reference(user_id: str, bank_id: str, index: int) -> str:
    if user_id == "usr_demo_amara":
        return "CUST-DEMO-8241"
    if user_id == "usr_demo_tunde":
        return "CUST-DEMO-8242"
    return f"CUST-{bank_id[4:].upper()}-{index:04d}"


def _reset_demo_data(db: Session) -> None:
    demo_user_ids = (*DEMO_CUSTOMER_IDS, *LEGACY_DEMO_BANK_STAFF_USER_IDS)
    webhook_ids = [row[0] for row in db.query(WebhookSubscription.id).filter(WebhookSubscription.bank_id.in_(DEMO_RESET_BANK_IDS)).all()]
    if webhook_ids:
        db.execute(delete(WebhookDelivery).where(WebhookDelivery.webhook_id.in_(webhook_ids)))
    db.execute(delete(WebhookSubscription).where(WebhookSubscription.bank_id.in_(DEMO_RESET_BANK_IDS)))
    db.execute(delete(BankApiKey).where(BankApiKey.bank_id.in_(DEMO_RESET_BANK_IDS)))
    db.execute(delete(AccountRestriction).where(or_(
        AccountRestriction.bank_id.in_(DEMO_RESET_BANK_IDS),
        AccountRestriction.user_id.in_(DEMO_CUSTOMER_IDS),
    )))
    db.execute(delete(BankAuditEvent).where(BankAuditEvent.bank_id.in_(DEMO_RESET_BANK_IDS)))
    db.execute(delete(RiskFlag).where(or_(
        RiskFlag.bank_id.in_(DEMO_RESET_BANK_IDS),
        RiskFlag.user_id.in_(DEMO_CUSTOMER_IDS),
    )))
    db.execute(delete(BankStaff).where(BankStaff.user_id.in_(LEGACY_DEMO_BANK_STAFF_USER_IDS)))
    db.execute(delete(AuthChallenge).where(AuthChallenge.user_id.in_(demo_user_ids)))
    db.execute(delete(UserConsent).where(UserConsent.user_id.in_(demo_user_ids)))
    db.execute(delete(SessionRevocation).where(SessionRevocation.user_id.in_(demo_user_ids)))
    db.execute(delete(PlatformAuditEvent).where(PlatformAuditEvent.subject_id.in_(demo_user_ids)))
    db.execute(delete(AccountActivitySignal).where(AccountActivitySignal.user_id.in_(DEMO_CUSTOMER_IDS)))
    db.execute(delete(Redemption).where(Redemption.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Voucher).where(Voucher.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Contribution).where(Contribution.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentActivity).where(CommitmentActivity.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentBeneficiary).where(CommitmentBeneficiary.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(CommitmentMember).where(CommitmentMember.commitment_id == DEMO_COMMITMENT_ID))
    db.execute(delete(Commitment).where(Commitment.id == DEMO_COMMITMENT_ID))
    db.execute(delete(ScoreHistory).where(ScoreHistory.user_id.in_(DEMO_CUSTOMER_IDS)))
    db.execute(delete(User).where(User.id.in_(demo_user_ids)))
    db.execute(delete(BankPartner).where(BankPartner.id.in_(DEMO_RESET_BANK_IDS)))


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

    for bank_id, bank_name, _ in DEMO_BANKS:
        bank = db.get(BankPartner, bank_id)
        if bank is None:
            db.add(BankPartner(id=bank_id, name=bank_name, created_at=now))
        else:
            bank.name = bank_name
            bank.environment = "sandbox"

    for index, (user_id, name, phone, bank_id, context, balance, account_status) in enumerate(DEMO_CUSTOMER_SPECS, start=1):
        user = db.get(User, user_id)
        if user is None:
            db.add(User(
                id=user_id,
                name=name,
                phone=phone,
                verified_at=now,
                bank_id=bank_id,
                bank_customer_id=_bank_customer_reference(user_id, bank_id, index),
                role="individual",
                context=context,
                terms_accepted_at=now,
                phone_verified_at=now,
                available_balance=balance,
                account_status=account_status,
            ))
        else:
            user.name = name
            user.phone = phone
            user.verified_at = now
            user.bank_id = bank_id
            user.bank_customer_id = _bank_customer_reference(user_id, bank_id, index)
            user.role = "individual"
            user.context = context
            user.terms_accepted_at = now
            user.phone_verified_at = now
            user.available_balance = balance
            user.account_status = account_status
            user.restriction_reason = "Seeded review scenario." if account_status != "active" else None
            user.restricted_at = now if account_status != "active" else None

    # One portal identity only. Its administrator role carries every portal
    # permission so the demo never needs role switching or multiple OTP flows.
    staff_specs = (
        ("usr_demo_bank_admin", "Banter Bank Portal Admin", "demo.admin@sura.local", "bank_admin", [], "2347065250811"),
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

    for user_id in DEMO_CUSTOMER_IDS:
        consent = (
            db.query(UserConsent)
            .filter(UserConsent.user_id == user_id, UserConsent.consent_type == "score_processing")
            .one_or_none()
        )
        if consent is None:
            db.add(UserConsent(
                id=f"consent_demo_{user_id[4:]}",
                user_id=user_id,
                consent_type="score_processing",
                granted=user_id not in {"usr_demo_member_18", "usr_demo_member_42", "usr_demo_member_63"},
                recorded_at=now,
            ))
        else:
            consent.granted = user_id not in {"usr_demo_member_18", "usr_demo_member_42", "usr_demo_member_63"}
            consent.recorded_at = now
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
    for index, user_id in enumerate(DEMO_CUSTOMER_IDS, start=1):
        # Different cadence lengths feed the transaction-stability Score pillar
        # without claiming to have verified a real bank transaction.
        cadence = (21, 14, 7, 0) if index % 4 else (30, 10, 0)
        for offset_days in cadence:
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
    for user_id in DEMO_CUSTOMER_IDS:
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
                id="audit_demo_score_visible", bank_id=DEMO_BANK_ID, actor_id="usr_demo_bank_admin",
                event_type="customer_score_viewed", subject_type="user", subject_id="usr_demo_amara",
                detail_json='{"demo":true}', occurred_at=now - timedelta(hours=1),
            ),
        ]
    )
    return {
        "created": True,
        "users": list(DEMO_CUSTOMER_IDS),
        "user_count": len(DEMO_CUSTOMER_IDS),
        "banks": [{"bank_id": bank_id, "name": name, "customer_count": count} for bank_id, name, count in DEMO_BANKS],
        "bank_id": DEMO_BANK_ID,
        "bank_staff": [email for _, _, email, _, _, _ in staff_specs],
        "commitment_id": DEMO_COMMITMENT_ID,
        "vendor_id": "vnd_demo_electronics",
        "voucher_code": "SURA-DEMO-LAPTOP-01",
    }
