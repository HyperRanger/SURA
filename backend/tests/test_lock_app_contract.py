def _create_invite(client, auth_headers):
    vendor_id = "vendor_contract"
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id},
        headers=auth_headers("verifier", role="verifier"),
    ).status_code == 200
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("creator")).status_code == 200
    response = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Invite contract",
            "vendor_id": vendor_id,
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["creator", "invitee"],
            "payout_order": ["creator", "invitee"],
        },
        headers=auth_headers("creator"),
    )
    assert response.status_code == 201
    return response.json()


def test_invite_preview_join_and_member_safe_detail(client, auth_headers):
    created = _create_invite(client, auth_headers)
    commitment_id = created["commitment_id"]

    preview = client.get(
        f"/v1/commitments/preview?code={created['invite_code']}", headers=auth_headers("invitee")
    )
    assert preview.status_code == 200
    assert preview.json()["join_status"] == "invited"
    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("invitee")).status_code == 200

    joined = client.post(
        "/v1/commitments/join",
        json={"invite_code": created["invite_code"]},
        headers=auth_headers("invitee"),
    )
    assert joined.status_code == 200
    assert joined.json()["status"] == "active"

    assert client.get(f"/v1/commitments/{commitment_id}", headers=auth_headers("outsider")).status_code == 403
    mine = client.get("/v1/commitments", headers=auth_headers("invitee"))
    assert mine.status_code == 200
    assert mine.json()[0]["commitment_id"] == commitment_id


def test_consent_cancel_and_activity_endpoints(client, auth_headers):
    consent = client.post("/v1/consent", json={"granted": True}, headers=auth_headers("creator"))
    assert consent.status_code == 200
    assert consent.json()["granted"] is True

    created = _create_invite(client, auth_headers)
    cancelled = client.post(
        f"/v1/commitments/{created['commitment_id']}/cancel", headers=auth_headers("creator")
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    activity = client.get(
        f"/v1/commitments/{created['commitment_id']}/activity", headers=auth_headers("creator")
    )
    assert activity.status_code == 200
    assert [event["event_type"] for event in activity.json()] == ["commitment_created", "commitment_cancelled"]


def test_create_and_join_require_granted_score_processing_consent(client, auth_headers):
    vendor_id = "vendor_consent_required"
    assert client.post(
        "/v1/vendors/verify",
        json={"vendor_id": vendor_id},
        headers=auth_headers("verifier", role="verifier"),
    ).status_code == 200

    create_without_consent = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Consent required",
            "vendor_id": vendor_id,
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["consent_creator", "consent_invitee"],
            "payout_order": ["consent_creator", "consent_invitee"],
        },
        headers=auth_headers("consent_creator"),
    )
    assert create_without_consent.status_code == 400

    assert client.post("/v1/consent", json={"granted": True}, headers=auth_headers("consent_creator")).status_code == 200
    created = client.post(
        "/v1/commitments/lock",
        json={
            "type": "rotating",
            "title": "Consent required",
            "vendor_id": vendor_id,
            "contribution_amount": 1000,
            "contribution_frequency": "weekly",
            "cycles": 2,
            "members": ["consent_creator", "consent_invitee"],
            "payout_order": ["consent_creator", "consent_invitee"],
        },
        headers=auth_headers("consent_creator"),
    )
    assert created.status_code == 201

    join_without_consent = client.post(
        "/v1/commitments/join",
        json={"invite_code": created.json()["invite_code"]},
        headers=auth_headers("consent_invitee"),
    )
    assert join_without_consent.status_code == 400
