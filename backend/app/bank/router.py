"""HTTP contract consumed by the Bank Portal frontend."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import AuthPrincipal
from app.bank import developer_service, operations_service, risk_rules, service
from app.bank.dependencies import require_bank_permission
from app.bank.models import BankStaff
from app.database import get_db
from app.services import bank_auth_service
from app.services.group_health import get_group_health
from app.services.commitments import open_commitment_case, resolve_commitment_case


def _staff_for_principal(db: Session, current: AuthPrincipal) -> BankStaff:
    """The staff row behind a Bank Portal session.

    Credential changes need one, so an external identity-provider session gets a
    plain refusal rather than an endpoint that appears to work.
    """
    staff = db.query(BankStaff).filter(BankStaff.user_id == current.user_id).one_or_none()
    if staff is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session is issued by an external identity provider and manages no local credentials.",
        )
    return staff


class FlagResolutionRequest(BaseModel):
    action: str = Field(pattern="^(dismissed|confirmed|escalated)$")
    note: str = Field(min_length=1, max_length=1000)


class CommitmentCaseRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class CommitmentCaseResolutionRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)


class RuleRunRequest(BaseModel):
    # Optional so a bank can run the whole book. Supplying ids scopes the run,
    # which is what a scheduled job wants when re-checking recent members only.
    user_ids: list[str] | None = Field(default=None, max_length=500)


class RestrictionRequest(BaseModel):
    action: str = Field(pattern="^(restricted|suspended|reinstated)$")
    reason: str = Field(min_length=1, max_length=1000)
    flag_id: str | None = None


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1)
    environment: str = Field(default="sandbox", pattern="^(sandbox|live)$")
    expires_at: datetime | None = None


class WebhookCreateRequest(BaseModel):
    url: AnyHttpUrl
    events: list[str] = Field(min_length=1)


class WebhookUpdateRequest(BaseModel):
    url: AnyHttpUrl | None = None
    events: list[str] | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, pattern="^(active|disabled)$")


class BankStaffCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=254)
    role: str
    mfa_phone: str = Field(min_length=4, max_length=32)
    temporary_password: str = Field(min_length=12, max_length=72)
    permissions: list[str] | None = None


class BankStaffUpdateRequest(BaseModel):
    role: str | None = None
    permissions: list[str] | None = None
    status: str | None = None


class BankResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=12, max_length=72)


class BankPermissionsRequest(BaseModel):
    permissions: list[str] = Field(min_length=1)


class BankSettingsUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    environment: str | None = None
    supported_vendor_categories: list[str] | None = None
    retention_days: int | None = None
    security_settings: dict[str, Any] | None = None


router = APIRouter(prefix="/v1/bank", tags=["bank portal"])


@router.get("/overview")
def bank_overview(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    current: AuthPrincipal = Depends(require_bank_permission("bank:overview:read")),
    db: Session = Depends(get_db),
):
    return service.overview(db, current.institution_id, date_from=date_from, date_to=date_to)


@router.get("/users")
def bank_users(
    q: str | None = Query(default=None, description="Name, phone, Sura user ID, bank customer reference, or commitment ID."),
    bank_customer_id: str | None = Query(default=None, description="Exact authorised bank customer reference."),
    score_tier: str | None = Query(default=None, description="Score tier: unverified, entry, building, or established."),
    flag_status: str | None = Query(default=None, description="Return customers with a flag in this status."),
    verified: bool | None = Query(default=None),
    float_eligibility: str | None = Query(default=None, pattern="^(eligible|locked)$"),
    commitment_status: str | None = Query(default=None),
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    return service.list_users(
        db,
        current.institution_id,
        query=q,
        bank_customer_id=bank_customer_id,
        score_tier=score_tier,
        flag_status=flag_status,
        verified=verified,
        float_eligibility=float_eligibility,
        commitment_status=commitment_status,
    )


@router.get("/users/{user_id}")
def bank_user_profile(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    response = service.get_user_profile(db, current.institution_id, current.user_id, user_id)
    db.commit()
    return response


@router.get("/users/{user_id}/score")
def bank_user_score(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    response = service.get_user_score(db, current.institution_id, current.user_id, user_id)
    db.commit()
    return response


@router.get("/users/{user_id}/commitments")
def bank_user_commitments(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    return service.get_user_commitments(db, current.institution_id, user_id)


@router.get("/users/{user_id}/activity")
def bank_user_activity(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:users:read")),
    db: Session = Depends(get_db),
):
    return service.get_user_activity(db, current.institution_id, user_id)


@router.get("/users/{user_id}/flags")
def bank_user_flags(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:read")),
    db: Session = Depends(get_db),
):
    service._user_or_404(db, current.institution_id, user_id)
    return service.list_flags(db, current.institution_id, user_id)


@router.get("/commitments")
def bank_commitments(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    vendor_id: str | None = Query(default=None),
    member_id: str | None = Query(default=None),
    current: AuthPrincipal = Depends(require_bank_permission("bank:commitments:read")),
    db: Session = Depends(get_db),
):
    return service.list_commitments(db, current.institution_id, query=q, status_filter=status_filter, vendor_id=vendor_id, member_id=member_id)


@router.get("/commitments/{commitment_id}")
def bank_commitment(
    commitment_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:commitments:read")),
    db: Session = Depends(get_db),
):
    return service.get_commitment(db, current.institution_id, commitment_id)


@router.get("/commitments/{commitment_id}/group-health")
def bank_commitment_group_health(
    commitment_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:commitments:read")),
    db: Session = Depends(get_db),
):
    # Reuse the established tenant check before returning aggregate-only health.
    service.get_commitment(db, current.institution_id, commitment_id)
    return get_group_health(db, commitment_id)


@router.post("/commitments/{commitment_id}/cases", status_code=status.HTTP_201_CREATED)
def open_case(
    commitment_id: str,
    payload: CommitmentCaseRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:commitments:write")),
    db: Session = Depends(get_db),
):
    response = open_commitment_case(db, commitment_id, current.institution_id, current.user_id, payload.reason)
    service._audit(db, current.institution_id, current.user_id, "commitment_case_opened", "commitment", commitment_id, {"case_id": response["case_id"]})
    db.commit()
    return response


@router.post("/commitments/{commitment_id}/cases/{case_id}/resolve")
def resolve_case(
    commitment_id: str,
    case_id: str,
    payload: CommitmentCaseResolutionRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:commitments:write")),
    db: Session = Depends(get_db),
):
    response = resolve_commitment_case(db, commitment_id, current.institution_id, current.user_id, case_id, payload.note)
    service._audit(db, current.institution_id, current.user_id, "commitment_case_resolved", "commitment", commitment_id, {"case_id": case_id})
    db.commit()
    return response


@router.get("/audit-log")
def bank_audit_log(
    user_id: str | None = Query(default=None),
    commitment_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    current: AuthPrincipal = Depends(require_bank_permission("bank:audit:read")),
    db: Session = Depends(get_db),
):
    return service.audit_log(db, current.institution_id, user_id=user_id, commitment_id=commitment_id, event_type=event_type, actor_id=actor_id, date_from=date_from, date_to=date_to)


@router.post("/audit-log/export", response_class=PlainTextResponse)
def bank_audit_export(
    current: AuthPrincipal = Depends(require_bank_permission("bank:audit:read")),
    db: Session = Depends(get_db),
):
    return service.export_audit_log(db, current.institution_id, current.user_id)


@router.get("/flags")
def bank_flags(
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    rule: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:read")),
    db: Session = Depends(get_db),
):
    return service.list_flags(db, current.institution_id, user_id=user_id, status_filter=status_filter, severity=severity, rule=rule)


@router.get("/flags/{flag_id}")
def bank_flag_detail(
    flag_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:read")),
    db: Session = Depends(get_db),
):
    return service.get_flag(db, current.institution_id, flag_id)


@router.post("/flags/{flag_id}/resolve")
def bank_resolve_flag(
    flag_id: str,
    payload: FlagResolutionRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:write")),
    db: Session = Depends(get_db),
):
    return service.resolve_flag(db, current.institution_id, current.user_id, flag_id, payload.action, payload.note)


@router.post("/risk-rules/run")
def bank_run_risk_rules(
    payload: RuleRunRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:write")),
    db: Session = Depends(get_db),
):
    """Evaluate the rule set and open a flag per new finding.

    Never restricts an account. A rule that could lock a member would be a rule
    that decides eligibility, and eligibility belongs to the fixed-weight model
    and to a named analyst.
    """
    return service.run_risk_rules(db, current.institution_id, current.user_id, payload.user_ids)


@router.post("/users/{user_id}/restriction")
def bank_apply_restriction(
    user_id: str,
    payload: RestrictionRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:write")),
    db: Session = Depends(get_db),
):
    return risk_rules.apply_restriction(
        db,
        current.institution_id,
        current.user_id,
        user_id,
        payload.action,
        payload.reason,
        flag_id=payload.flag_id,
    )


@router.get("/users/{user_id}/restrictions")
def bank_list_restrictions(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:read")),
    db: Session = Depends(get_db),
):
    return risk_rules.list_restrictions(db, current.institution_id, user_id)


@router.post("/users/{user_id}/sessions/revoke")
def bank_revoke_member_sessions(
    user_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:flags:write")),
    db: Session = Depends(get_db),
):
    """End every live session for one of this bank's members.

    The response to a session being in use by someone who should not have it.
    Shares the flag-write permission because it is the same decision: this
    account stops acting until a human says otherwise.
    """
    return service.revoke_member_sessions(db, current.institution_id, current.user_id, user_id)


@router.get("/settlements")
def bank_settlements(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    vendor_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    commitment_id: str | None = Query(default=None),
    current: AuthPrincipal = Depends(require_bank_permission("bank:settlements:read")),
    db: Session = Depends(get_db),
):
    return service.settlements(db, current.institution_id, query=q, status_filter=status_filter, vendor_id=vendor_id, user_id=user_id, commitment_id=commitment_id)


@router.get("/developers")
def bank_developer_home(
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.developer_home(db, current.institution_id)


@router.get("/api-keys")
def bank_api_keys(
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.list_api_keys(db, current.institution_id)


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
def bank_create_api_key(
    payload: ApiKeyCreateRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.create_api_key(
        db, current.institution_id, current.user_id, payload.name, payload.scopes, payload.environment, payload.expires_at
    )


@router.post("/api-keys/{key_id}/rotate")
def bank_rotate_api_key(
    key_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.rotate_api_key(db, current.institution_id, current.user_id, key_id)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def bank_revoke_api_key(
    key_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    developer_service.revoke_api_key(db, current.institution_id, current.user_id, key_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/webhooks")
def bank_webhooks(
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.list_webhooks(db, current.institution_id)


@router.post("/webhooks", status_code=status.HTTP_201_CREATED)
def bank_create_webhook(
    payload: WebhookCreateRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.create_webhook(db, current.institution_id, current.user_id, str(payload.url), payload.events)


@router.patch("/webhooks/{webhook_id}")
def bank_update_webhook(
    webhook_id: str,
    payload: WebhookUpdateRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.update_webhook(db, current.institution_id, current.user_id, webhook_id, str(payload.url) if payload.url else None, payload.events, payload.status)


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def bank_delete_webhook(
    webhook_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    developer_service.disable_webhook(db, current.institution_id, current.user_id, webhook_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/webhooks/{webhook_id}/test")
def bank_test_webhook(
    webhook_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.test_webhook(db, current.institution_id, current.user_id, webhook_id)


@router.post("/webhooks/{webhook_id}/rotate-secret")
def bank_rotate_webhook_secret(
    webhook_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.rotate_webhook_secret(db, current.institution_id, current.user_id, webhook_id)


@router.get("/webhooks/{webhook_id}/deliveries")
def bank_webhook_deliveries(
    webhook_id: str,
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
    db: Session = Depends(get_db),
):
    return developer_service.list_deliveries(db, current.institution_id, webhook_id)


@router.get("/events")
def bank_events(
    current: AuthPrincipal = Depends(require_bank_permission("bank:developer:write")),
):
    return developer_service.event_catalogue()


@router.get("/team")
def bank_team(
    current: AuthPrincipal = Depends(require_bank_permission("bank:team:write")),
    db: Session = Depends(get_db),
):
    return operations_service.list_staff(db, current.institution_id)


@router.post("/team", status_code=status.HTTP_201_CREATED)
def bank_provision_staff(
    payload: BankStaffCreateRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:team:write")),
    db: Session = Depends(get_db),
):
    return operations_service.create_staff(db, current.institution_id, current.user_id, **payload.model_dump())


@router.patch("/team/{staff_id}")
def bank_update_staff(
    staff_id: str,
    payload: BankStaffUpdateRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:team:write")),
    db: Session = Depends(get_db),
):
    return operations_service.update_staff(db, current.institution_id, current.user_id, staff_id, **payload.model_dump())


@router.post("/team/{staff_id}/password-reset")
def bank_reset_staff_password(
    staff_id: str,
    payload: BankResetPasswordRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:team:write")),
    db: Session = Depends(get_db),
):
    """Set a colleague's password. Bank administrators only.

    The recovery path for someone locked out. Refused on your own account, so it
    cannot be used to bypass proving possession of the current password.
    """
    actor = _staff_for_principal(db, current)
    return bank_auth_service.reset_password(db, actor, staff_id, payload.new_password)


@router.put("/team/{staff_id}/permissions")
def bank_set_staff_permissions(
    staff_id: str,
    payload: BankPermissionsRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:team:write")),
    db: Session = Depends(get_db),
):
    """Replace a colleague's permission set. Bank administrators only.

    Narrowing and widening are the same call, so both are guarded the same way.
    Permissions outside the role's map are refused rather than stored and failed
    later at the route.
    """
    actor = _staff_for_principal(db, current)
    return bank_auth_service.change_permissions(db, actor, staff_id, payload.permissions)


@router.get("/settings")
def bank_settings(
    current: AuthPrincipal = Depends(require_bank_permission("bank:settings:write")),
    db: Session = Depends(get_db),
):
    return operations_service.get_settings(db, current.institution_id)


@router.patch("/settings")
def bank_update_settings(
    payload: BankSettingsUpdateRequest,
    current: AuthPrincipal = Depends(require_bank_permission("bank:settings:write")),
    db: Session = Depends(get_db),
):
    return operations_service.update_settings(db, current.institution_id, current.user_id, **payload.model_dump())
