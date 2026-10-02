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
    Institution,
    PlatformAuditEvent,
    Redemption,
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
    "usr_demo_bank",
)
DEMO_VENDOR_IDS = ("vnd_demo_electronics", "vnd_demo_education", "vnd_demo_equipment")
DEMO_COMMITMENT_ID = "cmt_demo_laptop_rotation"
DEMO_REDEMPTION_ID = "rdm_demo_laptop_cycle_1"
DEMO_BANK_ID = "bnk_sura_partner"
DEMO_BANK_PASSWORD = "demo-password-never-in-production"

# There is deliberately one Sura API partner, not six bank tenants. ``bank_id``
# is the security boundary for the Bank Portal, so every demo member belongs to
# this tenant and is visible to its one administrator. The six institutions
# below describe the bank a member uses; they are source context, not portals.
DEMO_PARTNER_BANK = (DEMO_BANK_ID, "Sura Partner Bank")
DEMO_SOURCE_INSTITUTIONS = (
    ("inst_banter", "Banter Bank", 16),
    ("inst_chai", "Chai Bank", 14),
    ("inst_kolo", "Kolo Bank", 12),
    ("inst_jollof", "Jollof Bank", 10),
    ("inst_gbedu", "Gbedu Bank", 10),
    ("inst_sapa", "Sapa Bank", 8),
)
LEGACY_DEMO_BANK_IDS = ("bnk_banter", "bnk_chai", "bnk_kolo", "bnk_jollof", "bnk_gbedu", "bnk_sapa", "bnk_demo")

# First 30: contemporary English/Yoruba names. Then five Igbo, five Hausa,
# five names from other Nigerian ethnicities, and a final mixed set. These are
# fictional identities, intentionally suitable for a public demo.
_DEMO_NAMES = (
    "Amara Okafor", "Tunde Adeyemi", "Johnson Mitchell", "Adeayo Michael", "Adeogo Emmanuel",
    "Tolulope Toluwanimi", "Kaly David", "Damilola Grace", "Folarin James", "Temilade Ayo",
    "Oluwaseun Daniel", "Bimpe Williams", "Aderinsola Mercy", "Kehinde Samuel", "Ayomide Victoria",
    "Tobi Emmanuel", "Morenike David", "Seyi Nathan", "Olamide Hope", "Yewande Michael",
    "Bolanle Esther", "Dara Johnson", "Femi Alexander", "Kemi Grace", "Lekan Matthew",
    "Reni Adewale", "Sola David", "Wale Emmanuel", "Zainab Tolu", "Ireti James",
    "Muna Adebayo", "Pemi Oluwanifemi",
    "Chiamaka Nwosu", "Ikenna Okafor", "Ngozi Eze", "Obinna Kalu", "Somto Umeh",
    "Aisha Bello", "Hauwa Danjuma", "Sadiq Musa", "Maryam Abdullahi", "Yusuf Garba",
    "Ebiere Tamuno", "Boma Briggs", "Efe Oghene", "Mfon Akpan", "Zibah Kpeen",
    "Adaeze Ibe", "Chuka Ekwueme", "Dera Nwachukwu", "Ebuka Obi", "Favour Umeh",
    "Ganiyu Afolabi", "Hadiza Sani", "Ifeanyi Nduka", "Jumoke Adeyemi", "Kelechi Obi",
    "Lami Tanko", "Moyo Adeniran", "Nkiru Ude", "Ogechi Ezeani", "Precious James",
    "Raliat Ibrahim", "Tari Briggs", "Ugochukwu Nwankwo", "Vicky Okon", "Wuraola Taiwo",
    "Xavier Ekanem", "Yejide Adewale", "Zara Mohammed",
)
assert len(_DEMO_NAMES) == 70

_SOURCE_INSTITUTION_ASSIGNMENTS = tuple(
    institution_id
    for institution_id, _, count in DEMO_SOURCE_INSTITUTIONS
    for _ in range(count)
)
assert len(_SOURCE_INSTITUTION_ASSIGNMENTS) == 70
_CONTEXTS = ("student", "trader", "freelancer", "other")
_BALANCES = (0, 450, 1_250, 3_800, 8_500, 15_000, 27_500, 43_000, 68_000, 125_000, 240_000, 510_000)
_NON_ACTIVE_STATUSES = {17: "restricted", 36: "suspended", 58: "restricted"}


def _customer_specs() -> tuple[tuple[str, str, str, str, str, int, str], ...]:
    names = tuple(
        ("usr_demo_amara" if index == 1 else "usr_demo_tunde" if index == 2 else f"usr_demo_member_{index:02d}", name)
        for index, name in enumerate(_DEMO_NAMES, start=1)
    )
    return tuple(
        (
            user_id,
            name,
            f"demo.member.{index:02d}@sura.local" if index > 2 else f"demo-{name.split()[0].lower()}@sura.local",
            _SOURCE_INSTITUTION_ASSIGNMENTS[index - 1],
            _CONTEXTS[(index - 1) % len(_CONTEXTS)],
            _BALANCES[(index * 3) % len(_BALANCES)],
            _NON_ACTIVE_STATUSES.get(index, "active"),
        )
        for index, (user_id, name) in enumerate(names, start=1)
    )


DEMO_CUSTOMER_SPECS = _customer_specs()
DEMO_CUSTOMER_IDS = tuple(row[0] for row in DEMO_CUSTOMER_SPECS)
DEMO_RESET_BANK_IDS = (DEMO_BANK_ID, *LEGACY_DEMO_BANK_IDS)

_ADDITIONAL_LOCK_TITLES = (
    "Market Stock Circle", "Tuition Support Circle", "Studio Equipment Circle", "Tailoring Kit Circle",
    "Phone Upgrade Circle", "Food Cart Circle", "Certification Fund", "Laptop Repair Circle",
    "Creative Tools Circle", "Hostel Essentials Circle", "Camera Gear Circle", "Small Shop Circle",
    "Design Course Circle", "Generator Service Circle", "Festival Stock Circle", "Medical Supplies Circle",
    "Printing Press Circle", "Farm Inputs Circle", "Workwear Circle", "Solar Kit Circle",
    "Bakery Tools Circle", "Trade Fair Circle", "Home Office Circle", "Graduation Fund",
)
assert len(_ADDITIONAL_LOCK_TITLES) == 24
DEMO_COMMITMENT_IDS = (DEMO_COMMITMENT_ID, *(f"cmt_demo_circle_{index:02d}" for index in range(2, 26)))


def _demo_lock_specs() -> tuple[dict[str, object], ...]:
    specs: list[dict[str, object]] = [{
        "id": DEMO_COMMITMENT_ID, "title": "Laptop Fund - Demo Rotation", "vendor_id": "vnd_demo_electronics",
        "amount": 5_000, "cycles": 2, "status": "active", "current_cycle": 2, "completed_cycles": 1,
        "members": ("usr_demo_amara", "usr_demo_tunde"),
    }]
    for index, title in enumerate(_ADDITIONAL_LOCK_TITLES, start=2):
        status = "active" if index <= 10 else "pending_members" if index <= 17 else "completed"
        members = tuple(DEMO_CUSTOMER_IDS[(index * 3 + offset) % len(DEMO_CUSTOMER_IDS)] for offset in range(4))
        specs.append({
            "id": f"cmt_demo_circle_{index:02d}", "title": title,
            "vendor_id": DEMO_VENDOR_IDS[(index - 2) % len(DEMO_VENDOR_IDS)],
            "amount": (2_000, 3_500, 5_000, 7_500)[index % 4], "cycles": 3, "status": status,
            "current_cycle": 2 if status == "active" else 1 if status == "pending_members" else 3,
            "completed_cycles": 1 if status == "active" else 0 if status == "pending_members" else 3,
            "members": members,
        })
    return tuple(specs)


DEMO_LOCK_SPECS = _demo_lock_specs()
DEMO_RISK_FLAG_SPECS = (
    ("usr_demo_tunde", "unusual_contribution_pattern", "low", "open"),
    ("usr_demo_member_09", "identity_review", "medium", "open"),
    ("usr_demo_member_17", "account_access_review", "high", "open"),
    ("usr_demo_member_22", "duplicate_contact_review", "medium", "confirmed"),
    ("usr_demo_member_28", "voucher_redemption_review", "low", "dismissed"),
    ("usr_demo_member_36", "account_access_review", "high", "escalated"),
    ("usr_demo_member_41", "contribution_timing_review", "medium", "open"),
    ("usr_demo_member_47", "identity_review", "low", "dismissed"),
    ("usr_demo_member_52", "unusual_contribution_pattern", "medium", "open"),
    ("usr_demo_member_58", "account_access_review", "high", "confirmed"),
    ("usr_demo_member_63", "voucher_redemption_review", "medium", "open"),
    ("usr_demo_member_69", "duplicate_contact_review", "low", "dismissed"),
)
assert len(DEMO_RISK_FLAG_SPECS) == 12


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
    db.execute(delete(Redemption).where(Redemption.commitment_id.in_(DEMO_COMMITMENT_IDS)))
    db.execute(delete(Voucher).where(Voucher.commitment_id.in_(DEMO_COMMITMENT_IDS)))
    db.execute(delete(Contribution).where(Contribution.commitment_id.in_(DEMO_COMMITMENT_IDS)))
    db.execute(delete(CommitmentActivity).where(CommitmentActivity.commitment_id.in_(DEMO_COMMITMENT_IDS)))
    db.execute(delete(CommitmentBeneficiary).where(CommitmentBeneficiary.commitment_id.in_(DEMO_COMMITMENT_IDS)))
    db.execute(delete(CommitmentMember).where(CommitmentMember.commitment_id.in_(DEMO_COMMITMENT_IDS)))
    db.execute(delete(Commitment).where(Commitment.id.in_(DEMO_COMMITMENT_IDS)))
    db.execute(delete(ScoreHistory).where(ScoreHistory.user_id.in_(DEMO_CUSTOMER_IDS)))
    db.execute(delete(User).where(User.id.in_(demo_user_ids)))
    # An old demo shortcut may have created additional users under ``bnk_demo``.
    # Do not turn a reproducible demo reset into a broad user delete merely to
    # remove its parent bank row. Current demo banks are deleted when empty;
    # any bank still referenced by an unknown row is left intact.
    empty_bank_ids = [
        bank_id
        for bank_id in DEMO_RESET_BANK_IDS
        if db.query(User.id).filter(User.bank_id == bank_id).first() is None
    ]
    if empty_bank_ids:
        db.execute(delete(BankPartner).where(BankPartner.id.in_(empty_bank_ids)))
    source_institution_ids = [row[0] for row in DEMO_SOURCE_INSTITUTIONS]
    empty_institution_ids = [
        institution_id
        for institution_id in source_institution_ids
        if db.query(User.id).filter(User.institution_id == institution_id).first() is None
    ]
    if empty_institution_ids:
        db.execute(delete(Institution).where(Institution.id.in_(empty_institution_ids)))


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
        db.add(BankPartner(id=DEMO_BANK_ID, name=DEMO_PARTNER_BANK[1], environment="sandbox", created_at=now))
    else:
        bank.name = DEMO_PARTNER_BANK[1]
        bank.environment = "sandbox"

    for institution_id, name, _ in DEMO_SOURCE_INSTITUTIONS:
        institution = db.get(Institution, institution_id)
        if institution is None:
            db.add(Institution(id=institution_id, name=name, fee_calendar_json=None))
        else:
            institution.name = name

    for index, (user_id, name, phone, source_institution_id, context, balance, account_status) in enumerate(DEMO_CUSTOMER_SPECS, start=1):
        user = db.get(User, user_id)
        if user is None:
            db.add(User(
                id=user_id,
                name=name,
                phone=phone,
                verified_at=now,
                bank_id=DEMO_BANK_ID,
                institution_id=source_institution_id,
                bank_customer_id=_bank_customer_reference(user_id, source_institution_id, index),
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
            user.bank_id = DEMO_BANK_ID
            user.institution_id = source_institution_id
            user.bank_customer_id = _bank_customer_reference(user_id, source_institution_id, index)
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
        ("usr_demo_bank_admin", "Sura Partner Bank Portal Admin", "demo.admin@sura.local", "bank_admin", [], "2347065250811"),
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
    # Keep the two-member laptop story compact for the narrated walkthrough.
    db.add(Commitment(
        id=DEMO_COMMITMENT_ID, creator_id="usr_demo_amara", type="rotating",
        title="Laptop Fund - Demo Rotation", vendor_id="vnd_demo_electronics", contribution_amount=5_000,
        frequency="weekly", cycles=2, status="active", invite_code="SURA-DEMO-LAPTOP",
        payout_order_json=json.dumps(["usr_demo_amara", "usr_demo_tunde"]), current_cycle_number=2,
        completed_cycle_count=1, created_at=now - timedelta(days=14),
    ))
    for index, user_id in enumerate(DEMO_CUSTOMER_IDS, start=1):
        # Different cadence lengths feed the transaction-stability Score pillar
        # without claiming to have verified a real bank transaction.
        cadence = (21, 14, 7, 0) if index % 4 else (30, 10, 0)
        for offset_days in cadence:
            user = db.get(User, user_id)
            if user is None:
                # Every DEMO_CUSTOMER_IDS row is created earlier in this file;
                # this is a guard for the reader, not a runtime branch.
                continue
            db.add(AccountActivitySignal(
                id=f"act_demo_{user_id}_{offset_days}",
                user_id=user_id,
                institution_id=user.institution_id,
                source="simulated_bank_rail",
                occurred_at=now - timedelta(days=offset_days),
            ))
    db.add(RiskFlag(
        id="flag_demo_tunde_review",
        bank_id=DEMO_BANK_ID,
        user_id="usr_demo_tunde",
        rule="unusual_contribution_pattern",
        severity="low",
        status="open",
        evidence_json='{"source":"seeded_demo","review_reason":"unusual_contribution_pattern"}',
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
    # The primary walkthrough above remains intentionally small and easy to
    # narrate. The rest of the portfolio gives every screen realistic density:
    # 25 Locks in total, overlapping membership, active/pending/completed states,
    # and several vendor-linked historical settlements.
    for lock_index, spec in enumerate(DEMO_LOCK_SPECS[1:], start=2):
        commitment_id = str(spec["id"])
        members = tuple(spec["members"])
        status = str(spec["status"])
        amount = int(spec["amount"])
        cycles = int(spec["cycles"])
        completed_cycles = int(spec["completed_cycles"])
        created_at = now - timedelta(days=lock_index * 3)
        db.add(Commitment(
            id=commitment_id, creator_id=members[0], type="rotating", title=str(spec["title"]),
            vendor_id=str(spec["vendor_id"]), contribution_amount=amount, frequency="weekly", cycles=cycles,
            status=status, invite_code=f"SURA-DEMO-{lock_index:02d}", payout_order_json=json.dumps(members),
            current_cycle_number=int(spec["current_cycle"]), completed_cycle_count=completed_cycles,
            created_at=created_at,
        ))
        for member_index, user_id in enumerate(members):
            role = "invited" if status == "pending_members" and member_index == len(members) - 1 else "contributor"
            db.add(CommitmentMember(commitment_id=commitment_id, user_id=user_id, role=role, joined_at=created_at))
        db.add(CommitmentActivity(
            id=f"act_demo_{lock_index:02d}_created", commitment_id=commitment_id, event_type="commitment_created",
            actor_user_id=members[0], detail_json=json.dumps({"title": spec["title"]}), occurred_at=created_at,
        ))
        payout_amount = amount * len(members)
        for cycle_number in range(1, cycles + 1):
            settled = cycle_number <= completed_cycles
            beneficiary_id = members[(cycle_number - 1) % len(members)]
            db.add(CommitmentBeneficiary(
                id=f"bnf_demo_{lock_index:02d}_{cycle_number}", commitment_id=commitment_id, cycle_number=cycle_number,
                user_id=beneficiary_id, payout_amount=payout_amount, status="redeemed" if settled else "scheduled",
            ))
            if settled:
                code = f"SURA-DEMO-{lock_index:02d}-{cycle_number:02d}"
                redeemed_at = now - timedelta(days=10 + lock_index + cycle_number)
                db.add(Voucher(
                    id=f"vch_demo_{lock_index:02d}_{cycle_number}", commitment_id=commitment_id,
                    beneficiary_id=beneficiary_id, vendor_id=str(spec["vendor_id"]), cycle_number=cycle_number,
                    amount=payout_amount, code=code, status="redeemed", issued_at=redeemed_at - timedelta(days=1),
                    redeemed_at=redeemed_at,
                ))
                db.add(Redemption(
                    id=f"rdm_demo_{lock_index:02d}_{cycle_number}", commitment_id=commitment_id,
                    beneficiary_id=beneficiary_id, vendor_id=str(spec["vendor_id"]), cycle_number=cycle_number,
                    amount=payout_amount, voucher_code=code, status="settled", redeemed_at=redeemed_at,
                ))
                db.add(CommitmentActivity(
                    id=f"act_demo_{lock_index:02d}_cycle_{cycle_number}_paid", commitment_id=commitment_id,
                    event_type="cycle_paid", cycle_number=cycle_number,
                    detail_json=json.dumps({"beneficiary_id": beneficiary_id, "amount": payout_amount}),
                    occurred_at=redeemed_at - timedelta(days=1),
                ))
            contributors = (
                members if settled else members[:1]
                if status == "active" and cycle_number == int(spec["current_cycle"])
                else ()
            )
            for member_index, user_id in enumerate(contributors, start=1):
                db.add(Contribution(
                    id=f"ctr_demo_{lock_index:02d}_{cycle_number}_{member_index}", commitment_id=commitment_id,
                    cycle_number=cycle_number, user_id=user_id, amount=amount,
                    event_id=f"evt_demo_{lock_index:02d}_{cycle_number}_{member_index}", status="full",
                    rule_trace_json="{}", paid_at=now - timedelta(days=max(0, 2 + lock_index - cycle_number)),
                ))

    for flag_index, (user_id, rule, severity, flag_status) in enumerate(DEMO_RISK_FLAG_SPECS[1:], start=2):
        db.add(RiskFlag(
            id=f"flag_demo_{flag_index:02d}", bank_id=DEMO_BANK_ID, user_id=user_id, rule=rule,
            severity=severity, status=flag_status,
            evidence_json=json.dumps({"source": "seeded_demo", "review_reason": rule}),
            created_at=now - timedelta(days=flag_index),
        ))
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
        "partner_bank": {"bank_id": DEMO_BANK_ID, "name": DEMO_PARTNER_BANK[1], "customer_count": len(DEMO_CUSTOMER_IDS)},
        "source_institutions": [
            {"institution_id": institution_id, "name": name, "customer_count": count}
            for institution_id, name, count in DEMO_SOURCE_INSTITUTIONS
        ],
        "bank_id": DEMO_BANK_ID,
        "bank_staff": [email for _, _, email, _, _, _ in staff_specs],
        "commitment_count": len(DEMO_LOCK_SPECS),
        "open_risk_flag_count": sum(status == "open" for _, _, _, status in DEMO_RISK_FLAG_SPECS),
        "commitment_id": DEMO_COMMITMENT_ID,
        "vendor_id": "vnd_demo_electronics",
        "voucher_code": "SURA-DEMO-LAPTOP-01",
    }
