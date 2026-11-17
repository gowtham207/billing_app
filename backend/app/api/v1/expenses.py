import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.mount import mount_collection, mount_item
from app.core.deps import Context, get_db, require_org, require_write
from app.models import Expense, ExpenseCategory
from app.schemas.generated import ExpenseCategoryCreate, ExpenseCategoryRead, ExpenseCategoryUpdate, ExpenseRead
from app.schemas.requests import ExpenseCreateRequest
from app.services.common import get_scoped, set_status, status_key
from app.services.documents import create_expense

router = APIRouter(prefix="/expenses", tags=["Expenses"])
P = "expenses.write"

mount_collection(
    router,
    name="expense_categories",
    path="/categories",
    model=ExpenseCategory,
    read=ExpenseCategoryRead,
    create=ExpenseCategoryCreate,
    tag="Expenses",
    search=("name",),
    permission=P,
)
mount_item(
    router,
    name="expense_categories",
    path="/categories",
    model=ExpenseCategory,
    read=ExpenseCategoryRead,
    update=ExpenseCategoryUpdate,
    tag="Expenses",
    permission=P,
    can_get=False,
)
mount_collection(router, name="expenses", path="/", model=Expense, read=ExpenseRead, create=None, tag="Expenses", permission=P)
mount_item(router, name="expenses", path="/", model=Expense, read=ExpenseRead, update=None, tag="Expenses", permission=P, can_update=False)


@router.post("/", response_model=ExpenseRead, status_code=201)
def add_expense(body: ExpenseCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_expense(db, ctx, body)


@router.put("/{id}", response_model=ExpenseRead)
def update_expense(id: uuid.UUID, body: ExpenseCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, Expense, id, ctx.organization_id)
    if status_key(db, row.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft expenses can be edited")
    for key in ("category_id", "branch_id", "expense_date", "amount", "tax_amount", "currency", "vendor_name", "description"):
        value = getattr(body, key)
        if value is not None or key in {"vendor_name", "description", "branch_id"}:
            setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


def _move(db: Session, ctx: Context, expense_id: uuid.UUID, status: str) -> Expense:
    require_write(ctx, P)
    return set_status(
        db,
        get_scoped(db, Expense, expense_id, ctx.organization_id),
        ctx=ctx,
        module_key="expenses",
        entity_key="expense",
        status_key=status,
    )


@router.post("/{id}/submit", response_model=ExpenseRead)
def submit_expense(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return _move(db, ctx, id, "submitted")


@router.post("/{id}/approve", response_model=ExpenseRead)
def approve_expense(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return _move(db, ctx, id, "approved")


@router.post("/{id}/reject", response_model=ExpenseRead)
def reject_expense(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return _move(db, ctx, id, "rejected")


@router.post("/{id}/pay", response_model=ExpenseRead)
def pay_expense(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return _move(db, ctx, id, "paid")
