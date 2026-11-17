from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import set_organization
from app.core.security import create_access_token, hash_password, hash_token, new_token, verify_password
from app.models import Branch, Organization, OrganizationMember, OrganizationSubscription, Permission, Role, RolePermission, User
from app.models.extras import AuthSession, EmailVerificationToken, PasswordResetToken
from app.services.bootstrap import seed_organization, starter_plan_id


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _client_ip(request: Request | None) -> str | None:
    if request is None or request.client is None:
        return None
    host = request.client.host
    return host if host and host.count(".") == 3 or ":" in host else None


def _code(value: str) -> str:
    code = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:40]
    return code or "org"


def unique_code(db: Session, requested: str) -> str:
    base = _code(requested)
    code = base
    suffix = 2
    while db.scalar(select(Organization.id).where(Organization.code == code)):
        extra = f"-{suffix}"
        code = f"{base[: 40 - len(extra)]}{extra}"
        suffix += 1
    return code


def find_user(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.normalized_email == email.strip().lower()))


def provision_organization(db: Session, user: User, name: str, code: str | None = None) -> Organization:
    organization_id = uuid.uuid4()
    set_organization(db, organization_id)
    organization = Organization(
        id=organization_id,
        code=unique_code(db, code or name),
        legal_name=name,
        display_name=name,
        email=user.email,
        status="active",
    )
    member = OrganizationMember(
        id=uuid.uuid4(),
        organization_id=organization_id,
        user_id=user.id,
        member_status="active",
        joined_at=_now(),
    )
    role = Role(
        id=uuid.uuid4(),
        organization_id=organization_id,
        role_key="owner",
        name="Owner",
        is_system=True,
    )
    db.add(organization)
    db.flush()
    db.add_all(
        [
            member,
            role,
            Branch(organization_id=organization_id, code="HQ", name="Head Office", is_head_office=True),
        ]
    )
    db.flush()
    for permission in db.scalars(select(Permission)).all():
        db.add(RolePermission(organization_id=organization_id, role_id=role.id, permission_id=permission.id))
    from app.models import MemberRole

    db.add(MemberRole(organization_id=organization_id, member_id=member.id, role_id=role.id, assigned_by=user.id))
    seed_organization(db, organization_id)
    plan_id = starter_plan_id(db)
    if plan_id is not None:
        db.add(
            OrganizationSubscription(
                organization_id=organization_id,
                plan_id=plan_id,
                subscription_status="active",
                starts_at=_now(),
            )
        )
    db.flush()
    return organization


def start_session(db: Session, user: User, organization_id, request: Request | None) -> tuple[AuthSession, str, str]:
    refresh = new_token()
    session = AuthSession(
        user_id=user.id,
        organization_id=organization_id,
        refresh_token_hash=hash_token(refresh),
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=_client_ip(request),
        expires_at=_now() + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    db.flush()
    access = create_access_token(user_id=user.id, session_id=session.id, organization_id=organization_id)
    return session, access, refresh


def token_payload(access: str, refresh: str, organization_id) -> dict:
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
        "organization_id": organization_id,
    }


def register_user(db: Session, body, request: Request) -> dict:
    if find_user(db, body.email):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(email=str(body.email), password_hash=hash_password(body.password), full_name=body.full_name, phone=body.phone)
    db.add(user)
    db.flush()
    organization = None
    if body.organization_name:
        organization = provision_organization(db, user, body.organization_name, body.organization_code)
    _issue_verification(db, user)
    _, access, refresh = start_session(db, user, None if organization is None else organization.id, request)
    return {"user": user, "organization": organization, **token_payload(access, refresh, None if organization is None else organization.id)}


def login_user(db: Session, body, request: Request) -> dict:
    user = find_user(db, body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.is_platform_admin:
        raise HTTPException(status_code=403, detail="This account belongs to the admin console")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
    user.last_login_at = _now()
    organization_id = _single_active_org(db, user.id)
    _, access, refresh = start_session(db, user, organization_id, request)
    return {"user": user, **token_payload(access, refresh, organization_id)}


def _single_active_org(db: Session, user_id):
    rows = db.execute(
        __import__("sqlalchemy").text(
            "SELECT organization_id, member_status FROM app.organizations_for_user(:user_id)"
        ),
        {"user_id": user_id},
    ).all()
    active = [row.organization_id for row in rows if row.member_status == "active"]
    return active[0] if len(active) == 1 else None


def refresh_session(db: Session, refresh_token: str) -> dict:
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == hash_token(refresh_token)))
    if session is None or session.revoked_at is not None or session.expires_at <= _now():
        raise HTTPException(status_code=401, detail="Refresh token is not active")
    replacement = new_token()
    session.refresh_token_hash = hash_token(replacement)
    session.expires_at = _now() + timedelta(days=settings.refresh_token_days)
    access = create_access_token(user_id=session.user_id, session_id=session.id, organization_id=session.organization_id)
    return token_payload(access, replacement, session.organization_id)


def revoke_refresh(db: Session, refresh_token: str) -> None:
    session = db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == hash_token(refresh_token)))
    if session is not None and session.revoked_at is None:
        session.revoked_at = _now()


def switch_organization(db: Session, ctx, organization_id, request: Request) -> dict:
    if not ctx.is_platform_admin:
        rows = db.execute(
            __import__("sqlalchemy").text(
                "SELECT organization_id, member_status FROM app.organizations_for_user(:user_id)"
            ),
            {"user_id": ctx.user.id},
        ).all()
        match = next((row for row in rows if row.organization_id == organization_id), None)
        if match is None or match.member_status != "active":
            raise HTTPException(status_code=403, detail="You are not an active member of this organization")
    session = db.get(AuthSession, ctx.session_id)
    session.organization_id = organization_id
    refresh = new_token()
    session.refresh_token_hash = hash_token(refresh)
    session.expires_at = _now() + timedelta(days=settings.refresh_token_days)
    access = create_access_token(user_id=ctx.user.id, session_id=session.id, organization_id=organization_id)
    return token_payload(access, refresh, organization_id)


def _issue_verification(db: Session, user: User) -> str:
    token = new_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=_now() + timedelta(hours=24),
        )
    )
    return token


def request_password_reset(db: Session, email: str) -> dict:
    user = find_user(db, email)
    payload = {"message": "If the account exists, a reset token has been created"}
    if user is None:
        return payload
    token = new_token()
    db.add(PasswordResetToken(user_id=user.id, token_hash=hash_token(token), expires_at=_now() + timedelta(hours=1)))
    if settings.expose_dev_tokens:
        payload["reset_token"] = token
    return payload


def reset_password(db: Session, token: str, password: str) -> dict:
    row = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(token)))
    if row is None or row.used_at is not None or row.expires_at <= _now():
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")
    user = db.get(User, row.user_id)
    user.password_hash = hash_password(password)
    row.used_at = _now()
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))).all():
        session.revoked_at = _now()
    return {"message": "Password updated"}


def change_password(db: Session, ctx, current_password: str, new_password: str) -> dict:
    if not verify_password(current_password, ctx.user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    ctx.user.password_hash = hash_password(new_password)
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id == ctx.user.id, AuthSession.revoked_at.is_(None))).all():
        if session.id != ctx.session_id:
            session.revoked_at = _now()
    return {"message": "Password changed"}


def verify_email(db: Session, token: str) -> dict:
    row = db.scalar(select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hash_token(token)))
    if row is None or row.used_at is not None or row.expires_at <= _now():
        raise HTTPException(status_code=400, detail="Verification token is invalid or expired")
    user = db.get(User, row.user_id)
    user.email_verified_at = _now()
    row.used_at = _now()
    return {"message": "Email verified"}


def resend_verification(db: Session, user: User) -> dict:
    if user.email_verified_at is not None:
        return {"message": "Email is already verified"}
    token = _issue_verification(db, user)
    payload = {"message": "Verification token created"}
    if settings.expose_dev_tokens:
        payload["verification_token"] = token
    return payload
