import secrets
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import set_organization
from app.core.deps import Context, get_db, require_admin
from app.core.security import create_admin_token, hash_password, hash_token, new_token, verify_password
from app.models import Branch, MemberBranch, MemberRole, Organization, OrganizationMember, Permission, Role, RolePermission, User
from app.models.extras import AdminSession, AdminUser
from app.schemas.generated import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    OrganizationRead,
    OrganizationUpdate,
    PermissionCreate,
    PermissionRead,
    PermissionUpdate,
    RoleCreate,
    RoleRead,
    UserRead,
)
from app.schemas.requests import IdList, LoginRequest, RefreshRequest
from app.services.auth_service import find_user, provision_organization
from app.services.common import apply_update, create_model, delete_model, list_where, paginate

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminOrganizationCreate(BaseModel):
    legal_name: str = Field(min_length=1, max_length=200)
    display_name: str | None = Field(default=None, max_length=160)
    code: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    owner_email: EmailStr | None = None
    owner_name: str | None = Field(default=None, max_length=160)


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=160)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=40)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class WorkspaceUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=40)


class AdminAccountCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=8, max_length=128)


class AdminAccountUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    is_active: bool | None = None


def _page(page: dict, schema) -> dict:
    return {**page, "items": [schema.model_validate(item).model_dump(mode="json") for item in page["items"]]}


def _organization(db: Session, organization_id: uuid.UUID) -> Organization:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


def _owner(db: Session, ctx: Context, body: AdminOrganizationCreate) -> tuple[User, str | None]:
    if body.owner_email is None:
        raise HTTPException(status_code=422, detail="Owner email is required. Administrators are not workspace users.")
    user = find_user(db, str(body.owner_email))
    temporary_password = None
    if user is None:
        temporary_password = secrets.token_urlsafe(9)
        user = User(
            email=str(body.owner_email),
            full_name=body.owner_name or str(body.owner_email),
            password_hash=hash_password(temporary_password),
        )
        db.add(user)
        db.flush()
    return user, temporary_password


@router.get("/organizations")
def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_admin),
):
    filters = []
    if status:
        filters.append(Organization.status == status)
    return _page(
        paginate(
            db,
            Organization,
            None,
            page=page,
            page_size=page_size,
            q=q,
            search_fields=("display_name", "legal_name", "code", "email"),
            filters=filters,
        ),
        OrganizationRead,
    )


@router.post("/organizations", status_code=201)
def create_organization(body: AdminOrganizationCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    owner, temporary_password = _owner(db, ctx, body)
    organization = provision_organization(db, owner, body.display_name or body.legal_name, body.code)
    organization.legal_name = body.legal_name
    if body.display_name:
        organization.display_name = body.display_name
    if body.email:
        organization.email = str(body.email)
    if body.phone:
        organization.phone = body.phone
    db.flush()
    db.refresh(organization)
    payload = OrganizationRead.model_validate(organization).model_dump(mode="json")
    if temporary_password and settings.expose_dev_tokens:
        payload["temporary_owner_password"] = temporary_password
    return payload


@router.get("/organizations/{id}", response_model=OrganizationRead)
def get_organization(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    return _organization(db, id)


@router.put("/organizations/{id}", response_model=OrganizationRead)
def update_organization(id: uuid.UUID, body: OrganizationUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    organization = _organization(db, id)
    data = body.model_dump(exclude_unset=True)
    data.pop("status", None)
    for key, value in data.items():
        setattr(organization, key, value)
    db.flush()
    db.refresh(organization)
    return organization


@router.post("/organizations/{id}/activate", response_model=OrganizationRead)
def activate_organization(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    organization = _organization(db, id)
    organization.status = "active"
    organization.archived_at = None
    db.flush()
    db.refresh(organization)
    return organization


@router.post("/organizations/{id}/deactivate", response_model=OrganizationRead)
def deactivate_organization(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    organization = _organization(db, id)
    organization.status = "suspended"
    db.flush()
    db.refresh(organization)
    return organization


@router.delete("/organizations/{id}", status_code=204)
def delete_organization(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    db.delete(_organization(db, id))
    db.flush()
    return Response(status_code=204)


@router.get("/permissions", response_model=list[PermissionRead])
def list_permissions(
    q: str | None = None,
    module_key: str | None = None,
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_admin),
):
    stmt = select(Permission).order_by(Permission.permission_key)
    if module_key:
        stmt = stmt.where(Permission.module_key == module_key)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Permission.permission_key.ilike(like), Permission.description.ilike(like)))
    return db.scalars(stmt).all()


@router.post("/permissions", response_model=PermissionRead, status_code=201)
def create_permission(body: PermissionCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    row = Permission(**body.model_dump(exclude_unset=True))
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


@router.get("/permissions/{id}", response_model=PermissionRead)
def get_permission(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    row = db.get(Permission, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return row


@router.put("/permissions/{id}", response_model=PermissionRead)
def update_permission(id: uuid.UUID, body: PermissionUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    row = db.get(Permission, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.delete("/permissions/{id}", status_code=204)
def delete_permission(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    row = db.get(Permission, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(row)
    db.flush()
    return Response(status_code=204)


def _scope(db: Session, organization_id: uuid.UUID, ctx: Context) -> Context:
    _organization(db, organization_id)
    set_organization(db, organization_id)
    return replace(ctx, organization_id=organization_id)


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_admin),
):
    return _page(
        paginate(
            db,
            User,
            None,
            page=page,
            page_size=page_size,
            q=q,
            search_fields=("full_name", "email"),
            filters=[User.is_platform_admin.is_(False)],
        ),
        UserRead,
    )


@router.post("/users", response_model=UserRead, status_code=201)
def create_workspace_user(body: WorkspaceUserCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    if find_user(db, str(body.email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        email=str(body.email),
        full_name=body.full_name,
        phone=body.phone,
        password_hash=hash_password(body.password),
        is_platform_admin=False,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


@router.patch("/users/{id}", response_model=UserRead)
def update_user(id: uuid.UUID, body: AdminUserUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    user = db.get(User, id)
    if user is None or user.is_platform_admin:
        raise HTTPException(status_code=404, detail="User not found")
    data = body.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    email = data.pop("email", None)
    if email is not None:
        other = find_user(db, str(email))
        if other is not None and other.id != user.id:
            raise HTTPException(status_code=409, detail="Email is already registered")
        user.email = str(email)
    if password:
        user.password_hash = hash_password(password)
    if data.get("phone") == "":
        data["phone"] = None
    for key, value in data.items():
        setattr(user, key, value)
    db.flush()
    db.refresh(user)
    return user


@router.get("/organizations/{id}/branches", response_model=list[BranchRead])
def list_branches(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    _scope(db, id, ctx)
    return list_where(db, Branch, id)


@router.post("/organizations/{id}/branches", response_model=BranchRead, status_code=201)
def create_branch(id: uuid.UUID, body: BranchCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    scoped = _scope(db, id, ctx)
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = id
    return create_model(db, Branch, data, scoped, "branches")


@router.put("/organizations/{id}/branches/{branch_id}", response_model=BranchRead)
def update_branch(id: uuid.UUID, branch_id: uuid.UUID, body: BranchUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    scoped = _scope(db, id, ctx)
    branch = next((row for row in list_where(db, Branch, id) if row.id == branch_id), None)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    return apply_update(db, branch, body.model_dump(exclude_unset=True), scoped)


@router.delete("/organizations/{id}/branches/{branch_id}", status_code=204)
def delete_branch(id: uuid.UUID, branch_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    scoped = _scope(db, id, ctx)
    branch = next((row for row in list_where(db, Branch, id) if row.id == branch_id), None)
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    delete_model(db, branch, scoped)
    return Response(status_code=204)


class MembershipMap(BaseModel):
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None
    member_status: str = "active"


@router.get("/memberships")
def list_memberships(db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    rows = []
    organizations = db.scalars(select(Organization).order_by(Organization.display_name)).all()
    for organization in organizations:
        set_organization(db, organization.id)
        members = db.execute(
            select(OrganizationMember, User)
            .join(User, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == organization.id, User.is_platform_admin.is_(False))
            .order_by(User.full_name)
        ).all()
        for member, user in members:
            role_names = db.scalars(
                select(Role.name)
                .join(MemberRole, (MemberRole.role_id == Role.id) & (MemberRole.organization_id == Role.organization_id))
                .where(MemberRole.organization_id == organization.id, MemberRole.member_id == member.id)
            ).all()
            branch_names = db.scalars(
                select(Branch.name)
                .join(MemberBranch, (MemberBranch.branch_id == Branch.id) & (MemberBranch.organization_id == Branch.organization_id))
                .where(MemberBranch.organization_id == organization.id, MemberBranch.member_id == member.id)
                .order_by(Branch.name)
            ).all()
            rows.append({
                "id": str(member.id),
                "user_id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                "organization_id": str(organization.id),
                "organization_name": organization.display_name,
                "organization_code": organization.code,
                "member_status": member.member_status,
                "roles": list(role_names),
                "branches": list(branch_names),
            })
    return rows


@router.post("/memberships", status_code=201)
def map_membership(body: MembershipMap, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    if body.member_status not in {"invited", "active", "disabled"}:
        raise HTTPException(status_code=422, detail="Unknown member status")
    organization = _organization(db, body.organization_id)
    user = db.get(User, body.user_id)
    if user is None or user.is_platform_admin:
        raise HTTPException(status_code=404, detail="Workspace user not found")
    scoped = _scope(db, organization.id, ctx)
    member = db.scalar(select(OrganizationMember).where(OrganizationMember.organization_id == organization.id, OrganizationMember.user_id == user.id))
    if member is None:
        member = create_model(
            db,
            OrganizationMember,
            {
                "organization_id": organization.id,
                "user_id": user.id,
                "member_status": body.member_status,
                "joined_at": datetime.now(timezone.utc) if body.member_status == "active" else None,
            },
            scoped,
            "organization_members",
        )
    else:
        member.member_status = body.member_status
        if body.member_status == "active" and member.joined_at is None:
            member.joined_at = datetime.now(timezone.utc)
        db.flush()
    if body.role_id is not None:
        role = db.get(Role, body.role_id)
        if role is None or role.organization_id != organization.id:
            raise HTTPException(status_code=404, detail="Role not found")
        existing_role = db.scalar(
            select(MemberRole).where(
                MemberRole.organization_id == organization.id,
                MemberRole.member_id == member.id,
                MemberRole.role_id == role.id,
            )
        )
        if existing_role is None:
            db.add(MemberRole(organization_id=organization.id, member_id=member.id, role_id=role.id))
            db.flush()
    if body.branch_id is not None:
        branch = db.get(Branch, body.branch_id)
        if branch is None or branch.organization_id != organization.id:
            raise HTTPException(status_code=404, detail="Branch not found")
        if db.get(MemberBranch, (organization.id, member.id, branch.id)) is None:
            db.add(MemberBranch(organization_id=organization.id, member_id=member.id, branch_id=branch.id))
            db.flush()
    return {"id": str(member.id), "user_id": str(user.id), "organization_id": str(organization.id), "member_status": member.member_status}


class MembershipAssignment(BaseModel):
    organization_id: uuid.UUID
    role_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None


class MembershipBulk(BaseModel):
    user_id: uuid.UUID
    organizations: list[MembershipAssignment] = Field(min_length=1)


@router.post("/memberships/bulk", status_code=201)
def map_memberships(body: MembershipBulk, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    seen: set[uuid.UUID] = set()
    created = []
    for item in body.organizations:
        if item.organization_id in seen:
            continue
        seen.add(item.organization_id)
        created.append(
            map_membership(
                MembershipMap(
                    user_id=body.user_id,
                    organization_id=item.organization_id,
                    role_id=item.role_id,
                    branch_id=item.branch_id,
                    member_status="active",
                ),
                db,
                ctx,
            )
        )
    return created


@router.delete("/memberships/{organization_id}/{member_id}", status_code=204)
def unmap_membership(organization_id: uuid.UUID, member_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    _scope(db, organization_id, ctx)
    member = db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Mapping not found")
    member.member_status = "removed"
    db.flush()
    return Response(status_code=204)


@router.get("/organizations/{id}/members")
def list_members(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    _scope(db, id, ctx)
    rows = db.execute(
        select(OrganizationMember, User)
        .join(User, User.id == OrganizationMember.user_id)
        .where(OrganizationMember.organization_id == id)
        .order_by(User.full_name)
    ).all()
    return [
        {
            "id": str(member.id),
            "user_id": str(member.user_id),
            "full_name": user.full_name,
            "email": user.email,
            "member_status": member.member_status,
            "joined_at": member.joined_at,
            "is_active": user.is_active,
        }
        for member, user in rows
    ]


@router.post("/organizations/{id}/members", status_code=201)
def invite_member(id: uuid.UUID, body: OrgUserCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    scoped = _scope(db, id, ctx)
    user = find_user(db, str(body.email))
    temporary_password = None
    if user is None:
        temporary_password = None if body.password else secrets.token_urlsafe(9)
        user = User(
            email=str(body.email),
            full_name=body.full_name or str(body.email),
            password_hash=hash_password(body.password or temporary_password or ""),
            is_platform_admin=False,
        )
        db.add(user)
        db.flush()
    existing = db.scalar(select(OrganizationMember).where(OrganizationMember.organization_id == id, OrganizationMember.user_id == user.id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="User is already a member")
    member = create_model(
        db,
        OrganizationMember,
        {"organization_id": id, "user_id": user.id, "member_status": "invited"},
        scoped,
        "organization_members",
    )
    payload = {"id": str(member.id), "user_id": str(user.id), "email": user.email, "member_status": member.member_status}
    if temporary_password and settings.expose_dev_tokens:
        payload["temporary_password"] = temporary_password
    return payload


class OrgUserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, max_length=160)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class MemberStatusBody(BaseModel):
    member_status: str


@router.patch("/organizations/{id}/members/{member_id}")
def member_status(id: uuid.UUID, member_id: uuid.UUID, body: MemberStatusBody, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    _scope(db, id, ctx)
    if body.member_status not in {"invited", "active", "disabled", "removed"}:
        raise HTTPException(status_code=422, detail="Unknown member status")
    member = db.get(OrganizationMember, member_id)
    if member is None or member.organization_id != id:
        raise HTTPException(status_code=404, detail="Member not found")
    member.member_status = body.member_status
    db.flush()
    db.refresh(member)
    return {"id": str(member.id), "member_status": member.member_status}


@router.get("/organizations/{id}/roles")
def list_roles(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    _scope(db, id, ctx)
    return _page(paginate(db, Role, id, page=1, page_size=100), RoleRead)


@router.post("/organizations/{id}/roles", response_model=RoleRead, status_code=201)
def create_role(id: uuid.UUID, body: RoleCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    scoped = _scope(db, id, ctx)
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = id
    data["is_system"] = False
    return create_model(db, Role, data, scoped, "roles")


@router.delete("/organizations/{id}/roles/{role_id}", status_code=204)
def delete_role(id: uuid.UUID, role_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    scoped = _scope(db, id, ctx)
    role = next((row for row in list_where(db, Role, id) if row.id == role_id), None)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    delete_model(db, role, scoped)
    return Response(status_code=204)


@router.get("/organizations/{id}/roles/{role_id}/permissions")
def role_permissions(id: uuid.UUID, role_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    _scope(db, id, ctx)
    if next((row for row in list_where(db, Role, id) if row.id == role_id), None) is None:
        raise HTTPException(status_code=404, detail="Role not found")
    ids = db.scalars(select(RolePermission.permission_id).where(RolePermission.organization_id == id, RolePermission.role_id == role_id)).all()
    return {"role_id": str(role_id), "permission_ids": [str(item) for item in ids]}


@router.put("/organizations/{id}/roles/{role_id}/permissions")
def assign_role_permissions(id: uuid.UUID, role_id: uuid.UUID, body: IdList, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    _scope(db, id, ctx)
    if next((row for row in list_where(db, Role, id) if row.id == role_id), None) is None:
        raise HTTPException(status_code=404, detail="Role not found")
    db.query(RolePermission).filter(RolePermission.organization_id == id, RolePermission.role_id == role_id).delete()
    for permission_id in body.ids:
        db.add(RolePermission(organization_id=id, role_id=role_id, permission_id=permission_id))
    db.flush()
    return {"role_id": str(role_id), "permission_ids": [str(item) for item in body.ids]}


def _admin_public(admin: AdminUser) -> dict:
    return {
        "id": str(admin.id),
        "email": admin.email,
        "full_name": admin.full_name,
        "is_active": admin.is_active,
        "last_login_at": admin.last_login_at,
        "created_at": admin.created_at,
    }


def _find_admin(db: Session, email: str) -> AdminUser | None:
    return db.scalar(select(AdminUser).where(AdminUser.normalized_email == email.strip().lower()))


@router.post("/auth/login")
def admin_login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    admin = _find_admin(db, str(body.email))
    if admin is None or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Administrator is disabled")
    admin.last_login_at = datetime.now(timezone.utc)
    refresh = new_token()
    session = AdminSession(
        admin_user_id=admin.id,
        refresh_token_hash=hash_token(refresh),
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    db.flush()
    return {
        "access_token": create_admin_token(admin_id=admin.id, session_id=session.id),
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
        "user": _admin_public(admin),
    }


@router.post("/auth/refresh")
def admin_refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    session = db.scalar(select(AdminSession).where(AdminSession.refresh_token_hash == hash_token(body.refresh_token)))
    now = datetime.now(timezone.utc)
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh token is not active")
    refresh = new_token()
    session.refresh_token_hash = hash_token(refresh)
    session.expires_at = now + timedelta(days=settings.refresh_token_days)
    return {
        "access_token": create_admin_token(admin_id=session.admin_user_id, session_id=session.id),
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.access_token_minutes * 60,
        "organization_id": None,
    }


@router.post("/auth/logout")
def admin_logout(body: RefreshRequest, db: Session = Depends(get_db)):
    session = db.scalar(select(AdminSession).where(AdminSession.refresh_token_hash == hash_token(body.refresh_token)))
    if session is not None:
        session.revoked_at = datetime.now(timezone.utc)
    return {"message": "Logged out"}


@router.get("/auth/me")
def admin_me(db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    admin = db.get(AdminUser, ctx.admin_id)
    if admin is None:
        raise HTTPException(status_code=401, detail="Administrator not found")
    return {"user": _admin_public(admin)}


@router.get("/admins")
def list_admins(q: str | None = None, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    stmt = select(AdminUser).order_by(AdminUser.full_name)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(AdminUser.full_name.ilike(like), AdminUser.email.ilike(like)))
    return [_admin_public(row) for row in db.scalars(stmt).all()]


@router.post("/admins", status_code=201)
def create_admin(body: AdminAccountCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    if _find_admin(db, str(body.email)):
        raise HTTPException(status_code=409, detail="An administrator with this email already exists")
    admin = AdminUser(email=str(body.email), full_name=body.full_name, password_hash=hash_password(body.password))
    db.add(admin)
    db.flush()
    db.refresh(admin)
    return _admin_public(admin)


@router.patch("/admins/{id}")
def update_admin(id: uuid.UUID, body: AdminAccountUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    admin = db.get(AdminUser, id)
    if admin is None:
        raise HTTPException(status_code=404, detail="Administrator not found")
    if admin.id == ctx.admin_id and body.is_active is False:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(admin, key, value)
    db.flush()
    db.refresh(admin)
    return _admin_public(admin)
