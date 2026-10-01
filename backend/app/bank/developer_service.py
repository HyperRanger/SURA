"""Developer Hub credentials, webhooks, and auditable simulated deliveries."""

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bank.contracts import BANK_API_SCOPES, WEBHOOK_EVENTS
from app.bank.models import BankApiKey, BankPartner, WebhookDelivery, WebhookSubscription
from app.bank.service import _audit
from core.config import get_settings

API_KEY_ENVIRONMENTS = frozenset({"sandbox", "live"})
WEBHOOK_STATUSES = frozenset({"active", "disabled"})


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _cipher() -> Fernet:
    material = hashlib.sha256(get_settings().secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(material))


def _secret(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def _utc_naive(value: datetime) -> datetime:
    """Store expiry timestamps as UTC because the schema uses naive datetimes."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _validate_event_types(event_types: list[str]) -> list[str]:
    unique = list(dict.fromkeys(event_types))
    if not unique:
        raise HTTPException(status_code=400, detail="At least one webhook event is required.")
    unknown = set(unique).difference(WEBHOOK_EVENTS)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unsupported webhook events: {', '.join(sorted(unknown))}.")
    return unique


def _validate_scopes(scopes: list[str]) -> list[str]:
    unique = list(dict.fromkeys(scopes))
    if not unique:
        raise HTTPException(status_code=400, detail="At least one API key scope is required.")
    unknown = set(unique).difference(BANK_API_SCOPES)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unsupported API key scopes: {', '.join(sorted(unknown))}.")
    return unique


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Webhook URL must be an absolute HTTPS URL.")
    return url


def _serialize_key(row: BankApiKey) -> dict:
    return {
        "key_id": row.id,
        "name": row.name,
        "prefix": row.key_prefix,
        "scopes": json.loads(row.scopes_json),
        "environment": row.environment,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
        "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_api_keys(db: Session, bank_id: str) -> list[dict]:
    rows = db.query(BankApiKey).filter(BankApiKey.bank_id == bank_id).order_by(BankApiKey.created_at.desc()).all()
    return [_serialize_key(row) for row in rows]


def create_api_key(db: Session, bank_id: str, actor_id: str, name: str, scopes: list[str], environment: str, expires_at: datetime | None) -> dict:
    if environment not in API_KEY_ENVIRONMENTS:
        raise HTTPException(status_code=400, detail="API key environment must be sandbox or live.")
    normalized_expiry = _utc_naive(expires_at) if expires_at else None
    if normalized_expiry and normalized_expiry <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="API key expiry must be in the future.")
    raw_secret = _secret("sk_sura")
    row = BankApiKey(
        id=str(uuid.uuid4()), bank_id=bank_id, name=name, key_prefix=raw_secret[:14], secret_hash=hash_secret(raw_secret),
        scopes_json=json.dumps(_validate_scopes(scopes)), environment=environment, expires_at=normalized_expiry,
    )
    db.add(row)
    _audit(db, bank_id, actor_id, "api_key_created", "api_key", row.id, {"environment": environment, "scopes": scopes})
    db.commit()
    return {**_serialize_key(row), "secret": raw_secret, "secret_revealed_once": True}


def rotate_api_key(db: Session, bank_id: str, actor_id: str, key_id: str) -> dict:
    existing = db.query(BankApiKey).filter(BankApiKey.id == key_id, BankApiKey.bank_id == bank_id).one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    if existing.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Revoked API keys cannot be rotated.")
    existing.revoked_at = datetime.utcnow()
    _audit(db, bank_id, actor_id, "api_key_rotated", "api_key", existing.id)
    result = create_api_key(db, bank_id, actor_id, existing.name, json.loads(existing.scopes_json), existing.environment, existing.expires_at)
    result["rotated_key_id"] = key_id
    return result


def revoke_api_key(db: Session, bank_id: str, actor_id: str, key_id: str) -> None:
    row = db.query(BankApiKey).filter(BankApiKey.id == key_id, BankApiKey.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    if row.revoked_at is None:
        row.revoked_at = datetime.utcnow()
        _audit(db, bank_id, actor_id, "api_key_revoked", "api_key", row.id)
        db.commit()


def _serialize_webhook(row: WebhookSubscription) -> dict:
    return {"webhook_id": row.id, "url": row.url, "events": json.loads(row.event_types_json), "status": row.status, "created_at": row.created_at.isoformat() if row.created_at else None, "updated_at": row.updated_at.isoformat() if row.updated_at else None}


def list_webhooks(db: Session, bank_id: str) -> list[dict]:
    rows = db.query(WebhookSubscription).filter(WebhookSubscription.bank_id == bank_id).order_by(WebhookSubscription.created_at.desc()).all()
    return [_serialize_webhook(row) for row in rows]


def create_webhook(db: Session, bank_id: str, actor_id: str, url: str, event_types: list[str]) -> dict:
    signing_secret = _secret("whsec_sura")
    row = WebhookSubscription(
        id=str(uuid.uuid4()), bank_id=bank_id, url=_validate_url(url), event_types_json=json.dumps(_validate_event_types(event_types)),
        signing_secret_hash=hash_secret(signing_secret), signing_secret_encrypted=_cipher().encrypt(signing_secret.encode()).decode(),
    )
    db.add(row)
    _audit(db, bank_id, actor_id, "webhook_created", "webhook", row.id, {"events": event_types})
    db.commit()
    return {**_serialize_webhook(row), "signing_secret": signing_secret, "secret_revealed_once": True}


def update_webhook(db: Session, bank_id: str, actor_id: str, webhook_id: str, url: str | None, event_types: list[str] | None, status: str | None) -> dict:
    row = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id, WebhookSubscription.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    if url is not None:
        row.url = _validate_url(url)
    if event_types is not None:
        row.event_types_json = json.dumps(_validate_event_types(event_types))
    if status is not None:
        if status not in WEBHOOK_STATUSES:
            raise HTTPException(status_code=400, detail="Webhook status must be active or disabled.")
        row.status = status
    row.updated_at = datetime.utcnow()
    _audit(db, bank_id, actor_id, "webhook_updated", "webhook", row.id)
    db.commit()
    return _serialize_webhook(row)


def disable_webhook(db: Session, bank_id: str, actor_id: str, webhook_id: str) -> None:
    row = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id, WebhookSubscription.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    if row.status != "disabled":
        row.status = "disabled"
        row.updated_at = datetime.utcnow()
        _audit(db, bank_id, actor_id, "webhook_disabled", "webhook", row.id)
        db.commit()


def _record_delivery(db: Session, row: WebhookSubscription, event_type: str, payload: dict, *, status: str, response_summary: str | None = None) -> WebhookDelivery:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    secret = _cipher().decrypt(row.signing_secret_encrypted.encode()).decode()
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    delivery = WebhookDelivery(id=str(uuid.uuid4()), webhook_id=row.id, bank_id=row.bank_id, event_id=str(uuid.uuid4()), event_type=event_type, payload_json=body, signature=f"sha256={signature}", status=status, response_status=200 if status == "simulated_success" else None, response_summary=response_summary, delivered_at=datetime.utcnow() if status == "simulated_success" else None)
    db.add(delivery)
    return delivery


def _serialize_delivery(row: WebhookDelivery) -> dict:
    return {"delivery_id": row.id, "event_id": row.event_id, "event_type": row.event_type, "attempt_number": row.attempt_number, "status": row.status, "response_status": row.response_status, "response_summary": row.response_summary, "payload": json.loads(row.payload_json), "signature": row.signature, "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None, "created_at": row.created_at.isoformat() if row.created_at else None}


def test_webhook(db: Session, bank_id: str, actor_id: str, webhook_id: str) -> dict:
    row = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id, WebhookSubscription.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    if row.status != "active":
        raise HTTPException(status_code=400, detail="Only active webhooks can receive test deliveries.")
    delivery = _record_delivery(db, row, "webhook.test", {"id": "evt_test", "type": "webhook.test", "data": {"simulated": True}}, status="simulated_success", response_summary="Simulated test delivery; no external request was made.")
    _audit(db, bank_id, actor_id, "webhook_tested", "webhook", webhook_id, {"delivery_id": delivery.id})
    db.commit()
    return _serialize_delivery(delivery)


def rotate_webhook_secret(db: Session, bank_id: str, actor_id: str, webhook_id: str) -> dict:
    row = db.query(WebhookSubscription).filter(WebhookSubscription.id == webhook_id, WebhookSubscription.bank_id == bank_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    secret = _secret("whsec_sura")
    row.signing_secret_hash = hash_secret(secret)
    row.signing_secret_encrypted = _cipher().encrypt(secret.encode()).decode()
    row.updated_at = datetime.utcnow()
    _audit(db, bank_id, actor_id, "webhook_secret_rotated", "webhook", row.id)
    db.commit()
    return {"webhook_id": row.id, "signing_secret": secret, "secret_revealed_once": True}


def list_deliveries(db: Session, bank_id: str, webhook_id: str) -> list[dict]:
    if db.query(WebhookSubscription.id).filter(WebhookSubscription.id == webhook_id, WebhookSubscription.bank_id == bank_id).one_or_none() is None:
        raise HTTPException(status_code=404, detail="Webhook not found.")
    rows = db.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == webhook_id, WebhookDelivery.bank_id == bank_id).order_by(WebhookDelivery.created_at.desc()).all()
    return [_serialize_delivery(row) for row in rows]


def event_catalogue() -> list[dict]:
    return [{"event_type": event, "delivery": "signed JSON payload", "retry": "not available in this MVP"} for event in WEBHOOK_EVENTS]


def developer_home(db: Session, bank_id: str) -> dict:
    bank = db.get(BankPartner, bank_id)
    if bank is None:
        raise HTTPException(status_code=404, detail="Bank not found.")
    return {
        "bank_id": bank.id,
        "environment": bank.environment,
        "authentication": "X-Sura-API-Key",
        "api_docs_path": "/docs",
        "machine_endpoints": [
            "GET /v1/integrations/customers/{user_id}/score",
            "GET /v1/integrations/customers/{user_id}/commitments",
        ],
        "webhook_delivery": "signed test deliveries only; outbound dispatch is not part of this MVP",
    }
