"""The simulated funding-source contract keeps account numbers out of storage."""

from app.main import app
from app.models import LinkedAccount, User
from app.services.linked_accounts import simulated_account_number
from core.security import create_token


def _headers(user_id: str, role: str = "individual") -> dict[str, str]:
    return {"Authorization": f"Bearer {create_token(user_id, {'role': role})}"}


def _member(client, user_id: str = "funding_member") -> dict[str, str]:
    db = app.state.testing_session()
    try:
        db.add(User(id=user_id, name="Amina Bello", phone="2348000900001", role="individual"))
        db.commit()
    finally:
        db.close()
    return _headers(user_id)


def test_member_can_resolve_and_link_a_masked_simulated_account(client):
    headers = _member(client)
    account_number = simulated_account_number("funding_member")

    banks = client.get("/v1/banks")
    assert banks.status_code == 200
    assert "Ecobank Nigeria" in banks.json()["banks"]

    resolved = client.post(
        "/v1/accounts/resolve",
        json={"bank_name": "GTBank", "account_number": account_number},
        headers=headers,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json() == {
        "bank_name": "GTBank",
        "display_name": "Amina Bello",
        "account_number_masked": f"ending {account_number[-4:]}",
        "simulated": True,
    }
    assert resolved.json()["display_name"]

    linked = client.post(
        "/v1/accounts/link",
        json={"bank_name": "GTBank", "account_number": account_number},
        headers=headers,
    )
    assert linked.status_code == 201, linked.text
    assert linked.json()["account_number_masked"] == f"ending {account_number[-4:]}"
    assert linked.json()["simulated"] is True

    account = client.get("/v1/me/account", headers=headers)
    assert account.status_code == 200
    assert account.json()["account"]["display_name"] == resolved.json()["display_name"]

    db = app.state.testing_session()
    try:
        row = db.query(LinkedAccount).one()
        assert row.account_number_masked == f"ending {account_number[-4:]}"
        assert "0123456789" not in str(row.__dict__)
    finally:
        db.close()


def test_relink_replaces_the_display_label_and_never_creates_a_second_source(client):
    headers = _member(client)
    number = simulated_account_number("funding_member")
    for bank_name in ("GTBank", "Ecobank Nigeria"):
        response = client.post(
            "/v1/accounts/link",
            json={"bank_name": bank_name, "account_number": number},
            headers=headers,
        )
        assert response.status_code == 201

    db = app.state.testing_session()
    try:
        rows = db.query(LinkedAccount).all()
        assert len(rows) == 1
        assert rows[0].bank_name == "Ecobank Nigeria"
        assert rows[0].account_number_masked == f"ending {number[-4:]}"
    finally:
        db.close()


def test_account_number_validation_and_member_boundary(client):
    headers = _member(client)
    invalid = client.post(
        "/v1/accounts/resolve",
        json={"bank_name": "GTBank", "account_number": "123"},
        headers=headers,
    )
    assert invalid.status_code == 400

    mismatch = client.post(
        "/v1/accounts/resolve",
        json={"bank_name": "GTBank", "account_number": "0123456789"},
        headers=headers,
    )
    assert mismatch.status_code == 400

    db = app.state.testing_session()
    try:
        db.add(User(id="vendor", name="Vendor", phone="2348000900002", role="vendor"))
        db.commit()
    finally:
        db.close()
    not_a_member = client.post(
        "/v1/accounts/resolve",
        json={"bank_name": "GTBank", "account_number": "0123456789"},
        headers=_headers("vendor", "vendor"),
    )
    assert not_a_member.status_code == 403
