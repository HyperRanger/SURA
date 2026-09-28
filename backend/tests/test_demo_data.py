from app.models import Commitment, Redemption
from app.services.demo_data import DEMO_COMMITMENT_ID, DEMO_REDEMPTION_ID, seed_demo_data


def test_demo_data_seed_is_idempotent_and_contains_the_demo_story(client):
    db = client.app.state.testing_session()
    try:
        first = seed_demo_data(db, reset=True)
        assert first["created"] is True
        db.commit()
        assert db.get(Commitment, DEMO_COMMITMENT_ID).status == "active"
        assert db.get(Redemption, DEMO_REDEMPTION_ID).voucher_code == "SURA-DEMO-LAPTOP-01"

        second = seed_demo_data(db)
        assert second["created"] is False
    finally:
        db.close()
