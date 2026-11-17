import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.database import set_organization
from app.core.deps import Context, get_current_user, get_db, require_admin, require_org, require_write
from app.models import Branch, Organization, OrganizationAddress
from app.schemas.generated import (
    BranchCreate,
    BranchRead,
    BranchUpdate,
    OrganizationAddressCreate,
    OrganizationAddressRead,
    OrganizationAddressUpdate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.schemas.requests import OrganizationCreateRequest, StatusChange
from app.services.auth_service import provision_organization
from app.services.common import apply_update, create_model, delete_model, get_scoped, list_where, paginate

router = APIRouter(prefix="/organizations", tags=["Organizations & Branches"])


def _can_read(db: Session, ctx: Context, organization_id: uuid.UUID) -> Organization:
    organization = db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if ctx.is_platform_admin:
        return organization
    from sqlalchemy import text

    rows = db.execute(text("SELECT organization_id FROM app.organizations_for_user(:user_id)"), {"user_id": ctx.user.id}).all()
    if organization_id not in {row.organization_id for row in rows}:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization


@router.post("/", response_model=OrganizationRead, status_code=201)
def create_organization(body: OrganizationCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    return provision_organization(db, ctx.user, body.display_name or body.legal_name, body.code)


@router.get("/")
def list_organizations(
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_admin),
):
    return paginate(db, Organization, None, page=page, page_size=page_size, q=q, search_fields=("display_name", "legal_name", "code", "email"))


@router.get("/{id}", response_model=OrganizationRead)
def get_organization(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    return _can_read(db, ctx, id)


@router.put("/{id}", response_model=OrganizationRead)
def update_organization(id: uuid.UUID, body: OrganizationUpdate, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    organization = _can_read(db, ctx, id)
    require_write(ctx, "settings.write")
    return apply_update(db, organization, body.model_dump(exclude_unset=True), ctx)


@router.patch("/{id}/status", response_model=OrganizationRead)
def change_status(id: uuid.UUID, body: StatusChange, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    organization = get_scoped(db, Organization, id, None)
    if body.status not in {"pending", "active", "suspended", "archived"}:
        raise HTTPException(status_code=422, detail="Unknown organization status")
    organization.status = body.status
    if body.status == "archived":
        from datetime import datetime, timezone

        organization.archived_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(organization)
    return organization


@router.delete("/{id}", status_code=204)
def delete_organization(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    db.delete(get_scoped(db, Organization, id, None))
    db.flush()
    return Response(status_code=204)


@router.get("/{id}/branches", response_model=list[BranchRead])
def list_branches(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    _can_read(db, ctx, id)
    return list_where(db, Branch, id)


@router.post("/{id}/branches", response_model=BranchRead, status_code=201)
def create_branch(id: uuid.UUID, body: BranchCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    set_organization(db, id)
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = id
    return create_model(db, Branch, data, ctx, "branches")


@router.put("/branches/{branch_id}", response_model=BranchRead)
def update_branch(branch_id: uuid.UUID, body: BranchUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    return apply_update(db, get_scoped(db, Branch, branch_id, ctx.organization_id), body.model_dump(exclude_unset=True), ctx)


@router.delete("/branches/{branch_id}", status_code=204)
def delete_branch(branch_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    delete_model(db, get_scoped(db, Branch, branch_id, ctx.organization_id), ctx)
    return Response(status_code=204)


@router.get("/{id}/addresses", response_model=list[OrganizationAddressRead])
def list_addresses(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return list_where(db, OrganizationAddress, id)


@router.post("/{id}/addresses", response_model=OrganizationAddressRead, status_code=201)
def create_address(id: uuid.UUID, body: OrganizationAddressCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = id
    return create_model(db, OrganizationAddress, data, ctx, "organization_addresses")


@router.put("/addresses/{address_id}", response_model=OrganizationAddressRead)
def update_address(address_id: uuid.UUID, body: OrganizationAddressUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    return apply_update(db, get_scoped(db, OrganizationAddress, address_id, ctx.organization_id), body.model_dump(exclude_unset=True), ctx)


@router.delete("/addresses/{address_id}", status_code=204)
def delete_address(address_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    db.delete(get_scoped(db, OrganizationAddress, address_id, ctx.organization_id))
    db.flush()
    return Response(status_code=204)
