"""Query-count regression tests for the dashboard's hot read models."""

import json

from sqlalchemy import event

from app.models import Commitment, CommitmentMember, User, Vendor
from app.services.commitments import list_member_commitments


def test_member_commitment_list_uses_a_bounded_number_of_selects(client):
    """A larger Lock list must not produce more relation queries per Lock."""
    db = client.app.state.testing_session()
    try:
        member_id = "hot_member"
        member = User(id=member_id, name="Hot Read", phone="2348000090001", role="individual")
        vendor = Vendor(id="hot_vendor", name="Hot Vendor", category="demo")
        db.add_all([member, vendor])
        for number in range(6):
            commitment = Commitment(
                id=f"hot_commitment_{number}",
                creator_id=member.id,
                type="rotating",
                title=f"Hot Lock {number}",
                vendor_id=vendor.id,
                contribution_amount=1_000,
                frequency="weekly",
                cycles=1,
                status="active",
                invite_code=f"HOT{number}",
                payout_order_json=json.dumps([member_id]),
            )
            db.add(commitment)
            db.add(
                CommitmentMember(
                    commitment_id=commitment.id,
                    user_id=member_id,
                    role="creator",
                )
            )
        db.commit()

        statements: list[str] = []

        def count_selects(_connection, _cursor, statement, _parameters, _context, _executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        event.listen(db.bind, "before_cursor_execute", count_selects)
        try:
            result = list_member_commitments(db, member_id)
        finally:
            event.remove(db.bind, "before_cursor_execute", count_selects)

        assert len(result) == 6
        # One commitment query plus the six batched relation lookups. Before
        # batching, six Locks caused 37 SELECTs (one plus six per Lock).
        assert len(statements) <= 7, len(statements)
    finally:
        db.close()
