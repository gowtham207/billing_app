import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import Context, get_current_user, get_db
from app.models import User
from app.models.extras import AuthSession
from app.schemas.generated import UserRead
from app.schemas.requests import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    ProfileUpdate,
    RefreshRequest,
    RegisterRequest,
    SwitchOrganizationRequest,
    TokenVerifyRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    result = auth_service.register_user(db, body, request)
    result["user"] = UserRead.model_validate(result["user"])
    organization = result.pop("organization")
    result["organization_id"] = None if organization is None else organization.id
    return result


@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    result = auth_service.login_user(db, body, request)
    result["user"] = UserRead.model_validate(result["user"])
    return result


@router.post("/logout")
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    auth_service.revoke_refresh(db, body.refresh_token)
    return {"message": "Logged out"}


@router.post("/refresh")
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_session(db, body.refresh_token)


@router.post("/forgot-password")
def forgot_password(body: PasswordResetRequest, db: Session = Depends(get_db)):
    return auth_service.request_password_reset(db, str(body.email))


@router.post("/reset-password")
def reset_password(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    return auth_service.reset_password(db, body.token, body.password)


@router.post("/change-password")
def change_password(body: PasswordChangeRequest, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    return auth_service.change_password(db, ctx, body.current_password, body.new_password)


@router.get("/me")
def me(db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    organizations = db.execute(
        text(
            """
            SELECT o.id, o.code, o.display_name, o.status, m.member_status
            FROM app.organizations_for_user(:user_id) m
            JOIN app.organizations o ON o.id = m.organization_id
            """
        ),
        {"user_id": ctx.user.id},
    ).mappings().all()
    return {
        "user": UserRead.model_validate(ctx.user),
        "organization_id": ctx.organization_id,
        "organizations": [dict(row) for row in organizations],
        "roles": sorted(ctx.role_keys),
        "permissions": sorted(ctx.permissions),
    }


@router.put("/profile")
def update_profile(body: ProfileUpdate, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(ctx.user, key, value)
    db.flush()
    db.refresh(ctx.user)
    return UserRead.model_validate(ctx.user)


@router.post("/verify-email")
def verify_email(body: TokenVerifyRequest, db: Session = Depends(get_db)):
    return auth_service.verify_email(db, body.token)


@router.post("/resend-verification")
def resend_verification(db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    return auth_service.resend_verification(db, ctx.user)


@router.get("/sessions")
def sessions(db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    rows = db.query(AuthSession).filter(AuthSession.user_id == ctx.user.id, AuthSession.revoked_at.is_(None)).all()
    return [
        {
            "id": row.id,
            "organization_id": row.organization_id,
            "user_agent": row.user_agent,
            "ip_address": None if row.ip_address is None else str(row.ip_address),
            "expires_at": row.expires_at,
            "created_at": row.created_at,
            "current": row.id == ctx.session_id,
        }
        for row in rows
    ]


@router.delete("/sessions/{id}", status_code=204)
def revoke_session(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    row = db.get(AuthSession, id)
    if row is None or row.user_id != ctx.user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Session not found")
    row.revoked_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    return None


@router.get("/organizations")
def my_organizations(db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    rows = db.execute(
        text(
            """
            SELECT o.id, o.code, o.legal_name, o.display_name, o.status, m.member_status
            FROM app.organizations_for_user(:user_id) m
            JOIN app.organizations o ON o.id = m.organization_id
            ORDER BY o.display_name
            """
        ),
        {"user_id": ctx.user.id},
    ).mappings().all()
    return [dict(row) for row in rows]


@router.post("/switch-organization")
def switch_organization(
    body: SwitchOrganizationRequest,
    request: Request,
    db: Session = Depends(get_db),
    ctx: Context = Depends(get_current_user),
):
    return auth_service.switch_organization(db, ctx, body.organization_id, request)
