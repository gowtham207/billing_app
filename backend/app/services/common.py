from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import Context
from app.models import (
    AuditLog,
    DocumentSequence,
    StatusDefinition,
    StatusGroup,
    StatusHistory,
    StatusTransition,
    StockBalance,
    StockMovement,
)

MONEY = Decimal("0.01")
QTY = Decimal("0.0001")


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def quantity(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(QTY, rounding=ROUND_HALF_UP)


def audit(db: Session, ctx: Context | None, action: str, entity_type: str, entity_id: uuid.UUID | None) -> None:
    if ctx is None:
        return
    db.add(
        AuditLog(
            organization_id=ctx.organization_id,
            actor_user_id=None if ctx.user is None else ctx.user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    )


def paginate(
    db: Session,
    model,
    organization_id,
    *,
    page: int,
    page_size: int,
    q: str | None = None,
    search_fields: tuple[str, ...] = (),
    filters: list | None = None,
):
    stmt = select(model)
    if organization_id is not None and hasattr(model, "organization_id"):
        stmt = stmt.where(model.organization_id == organization_id)
    for clause in filters or []:
        stmt = stmt.where(clause)
    if q and search_fields:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(*[getattr(model, field).ilike(like) for field in search_fields]))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    if hasattr(model, "created_at"):
        stmt = stmt.order_by(model.created_at.desc())
    elif hasattr(model, "name"):
        stmt = stmt.order_by(model.name.asc())
    rows = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


def get_scoped(db: Session, model, object_id, organization_id):
    obj = db.get(model, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Not found")
    if organization_id is not None and hasattr(obj, "organization_id") and obj.organization_id != organization_id:
        raise HTTPException(status_code=404, detail="Not found")
    return obj


def create_model(db: Session, model, data: dict, ctx: Context | None = None, entity_type: str | None = None):
    obj = model(**data)
    db.add(obj)
    db.flush()
    audit(db, ctx, "create", entity_type or model.__tablename__, getattr(obj, "id", None))
    db.refresh(obj)
    return obj


def apply_update(db: Session, obj, data: dict, ctx: Context | None = None):
    for key, value in data.items():
        setattr(obj, key, value)
    db.flush()
    audit(db, ctx, "update", obj.__tablename__, getattr(obj, "id", None))
    db.refresh(obj)
    return obj


def delete_model(db: Session, obj, ctx: Context | None = None):
    if getattr(obj, "is_system", False):
        raise HTTPException(status_code=409, detail="System records cannot be deleted")
    audit(db, ctx, "delete", obj.__tablename__, getattr(obj, "id", None))
    if hasattr(obj, "is_active"):
        obj.is_active = False
        db.flush()
        return
    db.delete(obj)
    db.flush()


def list_where(db: Session, model, organization_id, **equals):
    stmt = select(model)
    if hasattr(model, "organization_id"):
        stmt = stmt.where(model.organization_id == organization_id)
    for key, value in equals.items():
        stmt = stmt.where(getattr(model, key) == value)
    return db.scalars(stmt).all()


def replace_children(db: Session, model, organization_id, parent_column: str, parent_id, rows: list[dict]):
    db.execute(
        delete(model).where(
            model.organization_id == organization_id,
            getattr(model, parent_column) == parent_id,
        )
    )
    created = []
    for row in rows:
        row = {**row, "organization_id": organization_id, parent_column: parent_id}
        obj = model(**row)
        db.add(obj)
        created.append(obj)
    db.flush()
    return created


def allocate_number(db: Session, organization_id, document_type: str, branch_id=None) -> str:
    stmt = select(DocumentSequence).where(
        DocumentSequence.organization_id == organization_id,
        DocumentSequence.document_type == document_type,
    )
    if branch_id is None:
        stmt = stmt.where(DocumentSequence.branch_id.is_(None))
    else:
        stmt = stmt.where(DocumentSequence.branch_id == branch_id)
    sequence = db.scalars(stmt.with_for_update()).first()
    if sequence is None and branch_id is not None:
        sequence = db.scalars(
            select(DocumentSequence)
            .where(
                DocumentSequence.organization_id == organization_id,
                DocumentSequence.document_type == document_type,
                DocumentSequence.branch_id.is_(None),
            )
            .with_for_update()
        ).first()
    if sequence is None:
        prefix = {
            "quotation": "QT-",
            "sales_order": "SO-",
            "sales_invoice": "INV-",
            "purchase_order": "PO-",
            "goods_receipt": "GRN-",
            "purchase_invoice": "BILL-",
            "payment": "PAY-",
            "credit_note": "CN-",
            "expense": "EXP-",
            "stock_adjustment": "ADJ-",
            "stock_transfer": "TR-",
            "sales_return": "SR-",
            "customer": "CUS-",
        }.get(document_type, "DOC-")
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"
    number = f"{sequence.prefix}{str(sequence.next_number).zfill(sequence.padding or 5)}{sequence.suffix or ''}"
    sequence.next_number += 1
    return number


def get_status(db: Session, organization_id, module_key: str, entity_key: str, status_key: str) -> StatusDefinition:
    stmt = (
        select(StatusDefinition)
        .join(
            StatusGroup,
            (StatusGroup.id == StatusDefinition.status_group_id)
            & (StatusGroup.organization_id == StatusDefinition.organization_id),
        )
        .where(
            StatusDefinition.organization_id == organization_id,
            StatusDefinition.status_key == status_key,
            StatusGroup.module_key == module_key,
            StatusGroup.entity_key == entity_key,
        )
    )
    found = db.scalars(stmt).first()
    if found is not None:
        return found
    group = db.scalars(
        select(StatusGroup).where(
            StatusGroup.organization_id == organization_id,
            StatusGroup.module_key == module_key,
            StatusGroup.entity_key == entity_key,
        )
    ).first()
    if group is None:
        group = StatusGroup(
            organization_id=organization_id,
            module_key=module_key,
            entity_key=entity_key,
            name=entity_key.replace("_", " ").title(),
        )
        db.add(group)
        db.flush()
    status = StatusDefinition(
        organization_id=organization_id,
        status_group_id=group.id,
        status_key=status_key,
        label=status_key.replace("_", " ").title(),
        is_initial=False,
        is_final=status_key in {"cancelled", "lost", "posted", "completed", "paid", "issued", "converted"},
    )
    db.add(status)
    db.flush()
    return status


def set_status(
    db: Session,
    obj,
    *,
    ctx: Context,
    module_key: str,
    entity_key: str,
    status_key: str,
    remarks: str | None = None,
    validate: bool = False,
):
    status = get_status(db, ctx.organization_id, module_key, entity_key, status_key)
    previous = getattr(obj, "status_id", None)
    if validate and previous is not None:
        rules = db.scalars(
            select(StatusTransition).where(
                StatusTransition.organization_id == ctx.organization_id,
                StatusTransition.status_group_id == status.status_group_id,
                StatusTransition.is_active.is_(True),
            )
        ).all()
        if rules and not any(rule.from_status_id == previous and rule.to_status_id == status.id for rule in rules):
            raise HTTPException(status_code=409, detail="Status transition is not allowed")
    obj.status_id = status.id
    db.add(
        StatusHistory(
            organization_id=ctx.organization_id,
            module_key=module_key,
            entity_type=entity_key,
            entity_id=obj.id,
            from_status_id=previous,
            to_status_id=status.id,
            changed_by=ctx.user.id,
            remarks=remarks,
        )
    )
    db.flush()
    db.refresh(obj)
    return obj


def status_key(db: Session, status_id) -> str | None:
    if status_id is None:
        return None
    row = db.get(StatusDefinition, status_id)
    return None if row is None else row.status_key


def ensure_mutable(db: Session, obj, blocked: set[str] | None = None):
    blocked = blocked or {"posted", "completed", "cancelled", "paid", "issued"}
    current = status_key(db, getattr(obj, "status_id", None))
    if current in blocked or getattr(obj, "issued_at", None) is not None:
        raise HTTPException(status_code=409, detail="This document can no longer be changed")


def _balance(db: Session, organization_id, warehouse_id, product_id, variant_id):
    stmt = select(StockBalance).where(
        StockBalance.organization_id == organization_id,
        StockBalance.warehouse_id == warehouse_id,
        StockBalance.product_id == product_id,
    )
    if variant_id is None:
        stmt = stmt.where(StockBalance.variant_id.is_(None))
    else:
        stmt = stmt.where(StockBalance.variant_id == variant_id)
    return db.scalars(stmt.with_for_update()).first()


def apply_movement(
    db: Session,
    *,
    organization_id,
    warehouse_id,
    product_id,
    variant_id,
    movement_type: str,
    quantity_delta: Decimal,
    unit_cost: Decimal = Decimal("0"),
    source_type: str | None = None,
    source_id=None,
    user_id=None,
    notes: str | None = None,
):
    delta = quantity(quantity_delta)
    if delta == 0:
        raise HTTPException(status_code=422, detail="Stock quantity cannot be zero")
    balance = _balance(db, organization_id, warehouse_id, product_id, variant_id)
    on_hand = balance.quantity_on_hand if balance is not None else Decimal("0")
    reserved = balance.quantity_reserved if balance is not None else Decimal("0")
    average = balance.average_cost if balance is not None else Decimal("0")
    new_qty = quantity(on_hand + delta)
    if new_qty < 0 or new_qty < reserved:
        raise HTTPException(status_code=409, detail="Insufficient stock")
    if delta > 0:
        average = quantity(((on_hand * average) + (delta * quantity(unit_cost))) / new_qty) if new_qty else Decimal("0")
    if balance is None:
        balance = StockBalance(
            organization_id=organization_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity_on_hand=new_qty,
            quantity_reserved=0,
            average_cost=average,
        )
        db.add(balance)
    else:
        balance.quantity_on_hand = new_qty
        balance.average_cost = average
    movement = StockMovement(
        organization_id=organization_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        variant_id=variant_id,
        movement_type=movement_type,
        quantity_delta=delta,
        unit_cost=quantity(unit_cost),
        source_type=source_type,
        source_id=source_id,
        created_by=user_id,
        notes=notes,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(movement)
    db.flush()
    return movement
