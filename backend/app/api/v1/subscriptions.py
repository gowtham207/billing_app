import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import set_organization
from app.core.deps import Context, get_current_user, get_db, require_admin, require_org, require_write
from app.models import (
    Module,
    OrganizationModuleOverride,
    OrganizationSubscription,
    PlanModule,
    SubscriptionPayment,
    SubscriptionPlan,
)
from app.schemas.generated import (
    ModuleRead,
    OrganizationSubscriptionRead,
    SubscriptionPaymentRead,
    SubscriptionPlanCreate,
    SubscriptionPlanRead,
    SubscriptionPlanUpdate,
)
from app.schemas.requests import ModuleAssign
from app.services.common import apply_update, create_model, get_scoped, paginate

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


class SubscriptionStart(BaseModel):
    plan_id: uuid.UUID
    subscription_status: str = "active"
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    trial_ends_at: datetime | None = None
    auto_renew: bool = True


class SubscriptionStatusBody(BaseModel):
    subscription_status: str


class SubscriptionPaymentIn(BaseModel):
    amount: float
    currency: str = "INR"
    payment_status: str = "paid"
    provider: str | None = None
    provider_reference: str | None = None


class ModuleOverrideIn(BaseModel):
    module_id: uuid.UUID
    is_enabled: bool
    reason: str | None = None
    expires_at: datetime | None = None


def _use_org(db: Session, ctx: Context, organization_id: uuid.UUID) -> None:
    if not ctx.is_platform_admin and ctx.organization_id != organization_id:
        raise HTTPException(status_code=403, detail="Cannot access another organization")
    set_organization(db, organization_id)


@router.get("/plans", response_model=list[SubscriptionPlanRead])
def list_plans(db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    return db.scalars(select(SubscriptionPlan).order_by(SubscriptionPlan.name)).all()


@router.post("/plans", response_model=SubscriptionPlanRead, status_code=201)
def create_plan(body: SubscriptionPlanCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    return create_model(db, SubscriptionPlan, body.model_dump(exclude_unset=True), ctx, "subscription_plans")


@router.put("/plans/{id}", response_model=SubscriptionPlanRead)
def update_plan(id: uuid.UUID, body: SubscriptionPlanUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    return apply_update(db, get_scoped(db, SubscriptionPlan, id, None), body.model_dump(exclude_unset=True), ctx)


@router.get("/modules", response_model=list[ModuleRead])
def list_modules(db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    return db.scalars(select(Module).order_by(Module.name)).all()


@router.post("/plans/{id}/modules")
def assign_modules(id: uuid.UUID, body: ModuleAssign, db: Session = Depends(get_db), ctx: Context = Depends(require_admin)):
    get_scoped(db, SubscriptionPlan, id, None)
    db.query(PlanModule).filter(PlanModule.plan_id == id).delete()
    for module_id in body.module_ids:
        db.add(PlanModule(plan_id=id, module_id=module_id))
    db.flush()
    return {"plan_id": id, "module_ids": body.module_ids}


@router.get("/organization/{org_id}", response_model=list[OrganizationSubscriptionRead])
def organization_subscription(org_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    _use_org(db, ctx, org_id)
    rows = db.scalars(
        select(OrganizationSubscription)
        .where(OrganizationSubscription.organization_id == org_id)
        .order_by(OrganizationSubscription.starts_at.desc())
    ).all()
    return rows


@router.post("/organization/{org_id}", status_code=201)
def create_subscription(org_id: uuid.UUID, body: SubscriptionStart, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    _use_org(db, ctx, org_id)
    require_write(ctx, "settings.write")
    data = body.model_dump()
    data["organization_id"] = org_id
    data["starts_at"] = data["starts_at"] or datetime.now(timezone.utc)
    return create_model(db, OrganizationSubscription, data, ctx, "organization_subscriptions")


@router.put("/{id}")
def update_subscription(id: uuid.UUID, body: SubscriptionStart, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    row = get_scoped(db, OrganizationSubscription, id, ctx.organization_id)
    return apply_update(db, row, body.model_dump(exclude_unset=True), ctx)


@router.patch("/{id}/status")
def subscription_status(id: uuid.UUID, body: SubscriptionStatusBody, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    allowed = {"trialing", "active", "past_due", "suspended", "cancelled", "expired"}
    if body.subscription_status not in allowed:
        raise HTTPException(status_code=422, detail="Unknown subscription status")
    row = get_scoped(db, OrganizationSubscription, id, ctx.organization_id)
    row.subscription_status = body.subscription_status
    db.flush()
    db.refresh(row)
    return row


@router.get("/{id}/payments", response_model=list[SubscriptionPaymentRead])
def list_payments(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, OrganizationSubscription, id, ctx.organization_id)
    return db.scalars(select(SubscriptionPayment).where(SubscriptionPayment.subscription_id == id)).all()


@router.post("/{id}/payments", response_model=SubscriptionPaymentRead, status_code=201)
def record_payment(id: uuid.UUID, body: SubscriptionPaymentIn, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    subscription = get_scoped(db, OrganizationSubscription, id, ctx.organization_id)
    return create_model(
        db,
        SubscriptionPayment,
        {**body.model_dump(), "organization_id": ctx.organization_id, "subscription_id": subscription.id},
        ctx,
        "subscription_payments",
    )


@router.get("/organization/{org_id}/entitlements")
def entitlements(org_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    _use_org(db, ctx, org_id)
    subscription = db.scalars(
        select(OrganizationSubscription)
        .where(OrganizationSubscription.organization_id == org_id, OrganizationSubscription.subscription_status.in_(["trialing", "active"]))
        .order_by(OrganizationSubscription.starts_at.desc())
    ).first()
    module_ids = set()
    if subscription is not None:
        module_ids.update(
            row.module_id for row in db.scalars(select(PlanModule).where(PlanModule.plan_id == subscription.plan_id)).all()
        )
    now = datetime.now(timezone.utc)
    for override in db.scalars(select(OrganizationModuleOverride).where(OrganizationModuleOverride.organization_id == org_id)).all():
        if override.expires_at is not None and override.expires_at <= now:
            continue
        if override.is_enabled:
            module_ids.add(override.module_id)
        else:
            module_ids.discard(override.module_id)
    modules = db.scalars(select(Module).where(Module.id.in_(module_ids))).all() if module_ids else []
    return [ModuleRead.model_validate(module) for module in modules]


@router.put("/organization/{org_id}/module-overrides")
def override_module(org_id: uuid.UUID, body: ModuleOverrideIn, db: Session = Depends(get_db), ctx: Context = Depends(get_current_user)):
    _use_org(db, ctx, org_id)
    require_write(ctx, "settings.write")
    row = db.get(OrganizationModuleOverride, (org_id, body.module_id))
    if row is None:
        row = OrganizationModuleOverride(organization_id=org_id, module_id=body.module_id, is_enabled=body.is_enabled, reason=body.reason, expires_at=body.expires_at)
        db.add(row)
    else:
        row.is_enabled = body.is_enabled
        row.reason = body.reason
        row.expires_at = body.expires_at
    db.flush()
    db.refresh(row)
    return row
