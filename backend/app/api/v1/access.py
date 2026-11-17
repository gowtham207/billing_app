import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import Context, get_db, require_org, require_write
from app.core.security import hash_password
from app.models import MemberBranch, MemberRole, OrganizationMember, Permission, Role, RolePermission, User
from app.schemas.generated import OrganizationMemberRead, OrganizationMemberUpdate, PermissionRead, RoleCreate, RoleRead, RoleUpdate
from app.schemas.requests import IdList, InviteMember
from app.services.auth_service import find_user
from app.services.common import apply_update, create_model, delete_model, get_scoped, paginate

router = APIRouter(prefix="/access", tags=["Access Control"])


class MemberStatusBody(BaseModel):
    member_status: str | None = None
    status: str | None = None


@router.get("/members")
def list_members(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return paginate(db, OrganizationMember, ctx.organization_id, page=page, page_size=page_size)


@router.post("/members/invite", status_code=201)
def invite_member(body: InviteMember, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    user = find_user(db, str(body.email))
    temporary_password = None
    if user is None:
        temporary_password = secrets.token_urlsafe(9)
        user = User(email=str(body.email), full_name=body.full_name or str(body.email), password_hash=hash_password(temporary_password))
        db.add(user)
        db.flush()
    existing = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == ctx.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="User is already a member")
    member = create_model(
        db,
        OrganizationMember,
        {"organization_id": ctx.organization_id, "user_id": user.id, "member_status": "invited"},
        ctx,
        "organization_members",
    )
    payload = {"member": OrganizationMemberRead.model_validate(member)}
    if temporary_password and settings.expose_dev_tokens:
        payload["temporary_password"] = temporary_password
    return payload


@router.get("/members/{id}", response_model=OrganizationMemberRead)
def get_member(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, OrganizationMember, id, ctx.organization_id)


@router.put("/members/{id}", response_model=OrganizationMemberRead)
def update_member(id: uuid.UUID, body: OrganizationMemberUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    return apply_update(db, get_scoped(db, OrganizationMember, id, ctx.organization_id), body.model_dump(exclude_unset=True), ctx)


@router.patch("/members/{id}/status", response_model=OrganizationMemberRead)
def member_status(id: uuid.UUID, body: MemberStatusBody, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    member = get_scoped(db, OrganizationMember, id, ctx.organization_id)
    status = body.member_status or body.status
    if status not in {"invited", "active", "disabled", "removed"}:
        raise HTTPException(status_code=422, detail="Unknown member status")
    member.member_status = status
    if status == "active" and member.joined_at is None:
        from datetime import datetime, timezone

        member.joined_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(member)
    return member


@router.delete("/members/{id}", status_code=204)
def remove_member(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    member = get_scoped(db, OrganizationMember, id, ctx.organization_id)
    member.member_status = "removed"
    db.flush()
    return Response(status_code=204)


@router.get("/roles")
def list_roles(page: int = 1, page_size: int = 50, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return paginate(db, Role, ctx.organization_id, page=page, page_size=page_size, search_fields=("name", "role_key"))


@router.post("/roles", response_model=RoleRead, status_code=201)
def create_role(body: RoleCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = ctx.organization_id
    return create_model(db, Role, data, ctx, "roles")


@router.put("/roles/{id}", response_model=RoleRead)
def update_role(id: uuid.UUID, body: RoleUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    return apply_update(db, get_scoped(db, Role, id, ctx.organization_id), body.model_dump(exclude_unset=True), ctx)


@router.delete("/roles/{id}", status_code=204)
def delete_role(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    delete_model(db, get_scoped(db, Role, id, ctx.organization_id), ctx)
    return Response(status_code=204)


@router.get("/permissions", response_model=list[PermissionRead])
def list_permissions(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return db.scalars(select(Permission).order_by(Permission.permission_key)).all()


def _replace(db: Session, model, ctx: Context, filters: dict, rows: list[dict]):
    stmt = db.query(model)
    for key, value in filters.items():
        stmt = stmt.filter(getattr(model, key) == value)
    stmt.delete()
    for row in rows:
        db.add(model(**row))
    db.flush()


@router.get("/roles/{id}/permissions")
def role_permissions(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Role, id, ctx.organization_id)
    ids = db.scalars(
        select(RolePermission.permission_id).where(RolePermission.organization_id == ctx.organization_id, RolePermission.role_id == id)
    ).all()
    return {"role_id": id, "permission_ids": ids}


@router.put("/roles/{id}/permissions")
def assign_permissions(id: uuid.UUID, body: IdList, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    get_scoped(db, Role, id, ctx.organization_id)
    _replace(
        db,
        RolePermission,
        ctx,
        {"organization_id": ctx.organization_id, "role_id": id},
        [{"organization_id": ctx.organization_id, "role_id": id, "permission_id": permission_id} for permission_id in body.ids],
    )
    return {"role_id": id, "permission_ids": body.ids}


@router.put("/members/{id}/roles")
def assign_roles(id: uuid.UUID, body: IdList, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    get_scoped(db, OrganizationMember, id, ctx.organization_id)
    _replace(
        db,
        MemberRole,
        ctx,
        {"organization_id": ctx.organization_id, "member_id": id},
        [{"organization_id": ctx.organization_id, "member_id": id, "role_id": role_id, "assigned_by": ctx.user.id} for role_id in body.ids],
    )
    return {"member_id": id, "role_ids": body.ids}


@router.get("/members/{id}/permissions")
def member_permissions(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, OrganizationMember, id, ctx.organization_id)
    rows = db.execute(
        __import__("sqlalchemy").text(
            """
            SELECT DISTINCT p.permission_key
            FROM app.member_roles mr
            JOIN app.role_permissions rp
              ON rp.organization_id = mr.organization_id AND rp.role_id = mr.role_id
            JOIN app.permissions p ON p.id = rp.permission_id
            WHERE mr.organization_id = :organization_id AND mr.member_id = :member_id
            ORDER BY p.permission_key
            """
        ),
        {"organization_id": ctx.organization_id, "member_id": id},
    ).all()
    return [row.permission_key for row in rows]


@router.get("/members/{id}/branches")
def member_branches(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, OrganizationMember, id, ctx.organization_id)
    return db.scalars(select(MemberBranch).where(MemberBranch.organization_id == ctx.organization_id, MemberBranch.member_id == id)).all()


@router.put("/members/{id}/branches")
def assign_branches(id: uuid.UUID, body: IdList, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "access.manage")
    get_scoped(db, OrganizationMember, id, ctx.organization_id)
    _replace(
        db,
        MemberBranch,
        ctx,
        {"organization_id": ctx.organization_id, "member_id": id},
        [{"organization_id": ctx.organization_id, "member_id": id, "branch_id": branch_id} for branch_id in body.ids],
    )
    return {"member_id": id, "branch_ids": body.ids}
