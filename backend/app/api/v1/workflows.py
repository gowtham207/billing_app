import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.deps import Context, get_db, require_org, require_write
from app.models import (
    CreditNote,
    Expense,
    GoodsReceipt,
    Lead,
    Opportunity,
    PurchaseInvoice,
    PurchaseOrder,
    Quotation,
    SalesInvoice,
    SalesOrder,
    SalesReturn,
    StatusDefinition,
    StatusGroup,
    StatusHistory,
    StatusTransition,
    StockAdjustment,
    StockTransfer,
    WorkflowDefinition,
    WorkflowStep,
)
from app.schemas.generated import (
    StatusDefinitionCreate,
    StatusDefinitionRead,
    StatusDefinitionUpdate,
    StatusGroupCreate,
    StatusGroupRead,
    StatusTransitionCreate,
    WorkflowDefinitionCreate,
    WorkflowDefinitionRead,
    WorkflowDefinitionUpdate,
)
from app.schemas.requests import TransitionRequest, WorkflowStepsUpdate
from app.services.common import create_model, get_scoped, get_status, paginate, set_status

router = APIRouter(prefix="/workflows", tags=["Workflows & Statuses"])

ENTITIES = {
    "lead": (Lead, "crm", "lead"),
    "opportunity": (Opportunity, "crm", "opportunity"),
    "quotation": (Quotation, "billing", "quotation"),
    "sales_order": (SalesOrder, "billing", "sales_order"),
    "sales_invoice": (SalesInvoice, "billing", "sales_invoice"),
    "purchase_order": (PurchaseOrder, "purchasing", "purchase_order"),
    "goods_receipt": (GoodsReceipt, "purchasing", "goods_receipt"),
    "purchase_invoice": (PurchaseInvoice, "purchasing", "purchase_invoice"),
    "stock_adjustment": (StockAdjustment, "inventory", "stock_adjustment"),
    "stock_transfer": (StockTransfer, "inventory", "stock_transfer"),
    "sales_return": (SalesReturn, "billing", "sales_return"),
    "credit_note": (CreditNote, "billing", "credit_note"),
    "expense": (Expense, "expenses", "expense"),
}


@router.get("/status-groups")
def list_groups(page: int = 1, page_size: int = 50, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return paginate(db, StatusGroup, ctx.organization_id, page=page, page_size=page_size)


@router.post("/status-groups", response_model=StatusGroupRead, status_code=201)
def create_group(body: StatusGroupCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = ctx.organization_id
    return create_model(db, StatusGroup, data, ctx, "status_groups")


@router.get("/statuses")
def list_statuses(page: int = 1, page_size: int = 100, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return paginate(db, StatusDefinition, ctx.organization_id, page=page, page_size=page_size)


@router.post("/statuses", response_model=StatusDefinitionRead, status_code=201)
def create_status(body: StatusDefinitionCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = ctx.organization_id
    return create_model(db, StatusDefinition, data, ctx, "status_definitions")


@router.put("/statuses/{id}", response_model=StatusDefinitionRead)
def update_status(id: uuid.UUID, body: StatusDefinitionUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    row = get_scoped(db, StatusDefinition, id, ctx.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.delete("/statuses/{id}", status_code=204)
def delete_status(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    db.delete(get_scoped(db, StatusDefinition, id, ctx.organization_id))
    db.flush()
    return None


@router.get("/transitions")
def list_transitions(page: int = 1, page_size: int = 100, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(StatusTransition).where(StatusTransition.organization_id == ctx.organization_id)).all()
    start = (page - 1) * page_size
    return {"items": rows[start : start + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.post("/transitions", status_code=201)
def create_transition(body: StatusTransitionCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = ctx.organization_id
    return create_model(db, StatusTransition, data, ctx, "status_transitions")


@router.get("/definitions")
def list_definitions(page: int = 1, page_size: int = 50, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return paginate(db, WorkflowDefinition, ctx.organization_id, page=page, page_size=page_size, search_fields=("name", "workflow_key"))


@router.post("/definitions", response_model=WorkflowDefinitionRead, status_code=201)
def create_definition(body: WorkflowDefinitionCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = ctx.organization_id
    return create_model(db, WorkflowDefinition, data, ctx, "workflow_definitions")


@router.put("/definitions/{id}", response_model=WorkflowDefinitionRead)
def update_definition(id: uuid.UUID, body: WorkflowDefinitionUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    row = get_scoped(db, WorkflowDefinition, id, ctx.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.get("/definitions/{id}/steps")
def list_steps(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, WorkflowDefinition, id, ctx.organization_id)
    return db.scalars(
        select(WorkflowStep).where(WorkflowStep.organization_id == ctx.organization_id, WorkflowStep.workflow_id == id).order_by(WorkflowStep.step_order)
    ).all()


@router.put("/definitions/{id}/steps")
def replace_steps(id: uuid.UUID, body: WorkflowStepsUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    get_scoped(db, WorkflowDefinition, id, ctx.organization_id)
    db.execute(delete(WorkflowStep).where(WorkflowStep.organization_id == ctx.organization_id, WorkflowStep.workflow_id == id))
    for step in body.steps:
        db.add(WorkflowStep(organization_id=ctx.organization_id, workflow_id=id, **step.model_dump()))
    db.flush()
    return body.steps


@router.post("/transition")
def transition(body: TransitionRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "workflows.manage")
    spec = ENTITIES.get(body.entity_type)
    if spec is None:
        raise HTTPException(status_code=422, detail="Unknown entity type")
    model, module_key, entity_key = spec
    obj = get_scoped(db, model, body.entity_id, ctx.organization_id)
    if body.to_status_id is not None:
        status = get_scoped(db, StatusDefinition, body.to_status_id, ctx.organization_id)
        status_name = status.status_key
    elif body.to_status_key:
        status_name = body.to_status_key
    else:
        raise HTTPException(status_code=422, detail="Provide a status")
    return set_status(
        db,
        obj,
        ctx=ctx,
        module_key=body.module_key or module_key,
        entity_key=entity_key,
        status_key=status_name,
        remarks=body.remarks,
        validate=True,
    )


@router.get("/history")
def history(
    module_key: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_org),
):
    stmt = select(StatusHistory).where(StatusHistory.organization_id == ctx.organization_id)
    if module_key:
        stmt = stmt.where(StatusHistory.module_key == module_key)
    if entity_type:
        stmt = stmt.where(StatusHistory.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(StatusHistory.entity_id == entity_id)
    rows = db.scalars(stmt.order_by(StatusHistory.changed_at.desc())).all()
    start = (page - 1) * page_size
    return {"items": rows[start : start + page_size], "total": len(rows), "page": page, "page_size": page_size}
