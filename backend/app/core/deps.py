from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, set_organization
from app.core.security import decode_access_token
from app.models import Organization, User
from app.models.extras import AuthSession

bearer = HTTPBearer(auto_error=False)


@dataclass
class Context:
    user: User | None
    session_id: uuid.UUID
    organization_id: uuid.UUID | None
    is_platform_admin: bool
    role_keys: set[str] = field(default_factory=set)
    permissions: set[str] = field(default_factory=set)
    admin_id: uuid.UUID | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def require_write(ctx: Context, permission: str | None) -> None:
    if permission is None:
        return
    if ctx.is_platform_admin or "owner" in ctx.role_keys or permission in ctx.permissions:
        return
    raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")


def _memberships(db: Session, user_id: uuid.UUID):
    try:
        return db.execute(
            text(
                "SELECT organization_id, member_id, member_status "
                "FROM app.organizations_for_user(:user_id)"
            ),
            {"user_id": user_id},
        ).all()
    except ProgrammingError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database is missing API tables. Apply database/app_extras.sql.",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Context:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User is not active")
    session = db.get(AuthSession, uuid.UUID(payload["sid"]))
    now = datetime.now(timezone.utc)
    if (
        session is None
        or session.user_id != user.id
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        raise HTTPException(status_code=401, detail="Session is not active")
    org_raw = payload.get("org")
    organization_id = uuid.UUID(org_raw) if org_raw else None
    role_keys: set[str] = set()
    permissions: set[str] = set()
    if organization_id is not None:
        organization = db.get(Organization, organization_id)
        if organization is None:
            raise HTTPException(status_code=404, detail="Organization not found")
        if not user.is_platform_admin:
            if organization.status != "active":
                raise HTTPException(status_code=403, detail="Organization is not active")
            match = next(
                (row for row in _memberships(db, user.id) if row.organization_id == organization_id),
                None,
            )
            if match is None or match.member_status != "active":
                raise HTTPException(status_code=403, detail="Organization membership is not active")
        set_organization(db, organization_id)
        rows = db.execute(
            text(
                """
                SELECT r.role_key, p.permission_key
                FROM app.organization_members m
                JOIN app.member_roles mr
                  ON mr.organization_id = m.organization_id AND mr.member_id = m.id
                JOIN app.roles r
                  ON r.organization_id = mr.organization_id AND r.id = mr.role_id
                LEFT JOIN app.role_permissions rp
                  ON rp.organization_id = r.organization_id AND rp.role_id = r.id
                LEFT JOIN app.permissions p ON p.id = rp.permission_id
                WHERE m.user_id = :user_id
                  AND m.organization_id = :organization_id
                  AND m.member_status = 'active'
                """
            ),
            {"user_id": user.id, "organization_id": organization_id},
        ).all()
        role_keys = {row.role_key for row in rows if row.role_key}
        permissions = {row.permission_key for row in rows if row.permission_key}
    return Context(
        user=user,
        session_id=session.id,
        organization_id=organization_id,
        is_platform_admin=user.is_platform_admin,
        role_keys=role_keys,
        permissions=permissions,
    )


def require_org(ctx: Context = Depends(get_current_user)) -> Context:
    if ctx.organization_id is None:
        raise HTTPException(status_code=400, detail="Switch to an organization first")
    return ctx


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Context:
    from app.models.extras import AdminSession, AdminUser

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    if payload.get("typ") != "admin":
        raise HTTPException(status_code=403, detail="Platform administrator access is required")
    admin = db.get(AdminUser, uuid.UUID(payload["sub"]))
    session = db.get(AdminSession, uuid.UUID(payload["sid"]))
    now = datetime.now(timezone.utc)
    if (
        admin is None
        or not admin.is_active
        or session is None
        or session.admin_user_id != admin.id
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        raise HTTPException(status_code=401, detail="Admin session is not active")
    return Context(
        user=None,
        session_id=session.id,
        organization_id=None,
        is_platform_admin=True,
        admin_id=admin.id,
    )
