import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.mount import mount_collection, mount_item
from app.core.deps import Context, get_db, require_org, require_write
from app.models import GoodsReceipt, Payment, PurchaseInvoice, PurchaseOrder, Supplier, SupplierAddress, SupplierPayment
from app.schemas.generated import (
    GoodsReceiptRead,
    PurchaseInvoiceRead,
    PurchaseOrderRead,
    SupplierAddressCreate,
    SupplierAddressRead,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)
from app.schemas.requests import (
    AllocateBills,
    GoodsReceiptCreateRequest,
    PaymentCreateRequest,
    PurchaseInvoiceCreateRequest,
    PurchaseOrderCreateRequest,
)
from app.services.common import create_model, get_scoped, list_where, set_status, status_key
from app.services.documents import (
    allocate_supplier_payment,
    complete_receipt,
    create_goods_receipt,
    create_purchase_invoice,
    create_purchase_order,
    record_payment,
)

router = APIRouter(prefix="/purchases", tags=["Purchasing"])
P = "purchasing.write"

mount_collection(router, name="suppliers", path="/suppliers", model=Supplier, read=SupplierRead, create=SupplierCreate, tag="Purchasing", search=("name", "supplier_code", "email"), permission=P)
mount_item(router, name="suppliers", path="/suppliers", model=Supplier, read=SupplierRead, update=SupplierUpdate, tag="Purchasing", permission=P)


@router.get("/suppliers/{id}/addresses", response_model=list[SupplierAddressRead])
def list_addresses(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Supplier, id, ctx.organization_id)
    return list_where(db, SupplierAddress, ctx.organization_id, supplier_id=id)


@router.post("/suppliers/{id}/addresses", response_model=SupplierAddressRead, status_code=201)
def add_address(id: uuid.UUID, body: SupplierAddressCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    get_scoped(db, Supplier, id, ctx.organization_id)
    data = body.model_dump(exclude_unset=True)
    data.update(organization_id=ctx.organization_id, supplier_id=id)
    return create_model(db, SupplierAddress, data, ctx, "supplier_addresses")


@router.get("/suppliers/{id}/transactions")
def supplier_transactions(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Supplier, id, ctx.organization_id)
    return {
        "invoices": db.scalars(select(PurchaseInvoice).where(PurchaseInvoice.organization_id == ctx.organization_id, PurchaseInvoice.supplier_id == id)).all(),
        "payments": db.scalars(select(Payment).where(Payment.organization_id == ctx.organization_id, Payment.supplier_id == id)).all(),
    }


def _page(rows, page: int, page_size: int):
    start = (page - 1) * page_size
    return {"items": rows[start : start + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.get("/orders")
def list_orders(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(PurchaseOrder).where(PurchaseOrder.organization_id == ctx.organization_id).order_by(PurchaseOrder.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/orders", response_model=PurchaseOrderRead, status_code=201)
def add_order(body: PurchaseOrderCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_purchase_order(db, ctx, body)


@router.get("/orders/{id}", response_model=PurchaseOrderRead)
def get_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, PurchaseOrder, id, ctx.organization_id)


@router.put("/orders/{id}", response_model=PurchaseOrderRead)
def update_order(id: uuid.UUID, body: PurchaseOrderCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    current = get_scoped(db, PurchaseOrder, id, ctx.organization_id)
    if status_key(db, current.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft purchase orders can be edited")
    db.delete(current)
    db.flush()
    return create_purchase_order(db, ctx, body)


@router.post("/orders/{id}/submit", response_model=PurchaseOrderRead)
def submit_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, PurchaseOrder, id, ctx.organization_id), ctx=ctx, module_key="purchasing", entity_key="purchase_order", status_key="submitted")


@router.post("/orders/{id}/approve", response_model=PurchaseOrderRead)
def approve_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, PurchaseOrder, id, ctx.organization_id), ctx=ctx, module_key="purchasing", entity_key="purchase_order", status_key="approved")


@router.post("/orders/{id}/cancel", response_model=PurchaseOrderRead)
def cancel_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, PurchaseOrder, id, ctx.organization_id), ctx=ctx, module_key="purchasing", entity_key="purchase_order", status_key="cancelled")


@router.get("/goods-receipts")
def list_receipts(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(GoodsReceipt).where(GoodsReceipt.organization_id == ctx.organization_id).order_by(GoodsReceipt.received_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/goods-receipts", response_model=GoodsReceiptRead, status_code=201)
def add_receipt(body: GoodsReceiptCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_goods_receipt(db, ctx, body)


@router.get("/goods-receipts/{id}", response_model=GoodsReceiptRead)
def get_receipt(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, GoodsReceipt, id, ctx.organization_id)


@router.post("/goods-receipts/{id}/complete", response_model=GoodsReceiptRead)
def finish_receipt(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return complete_receipt(db, ctx, get_scoped(db, GoodsReceipt, id, ctx.organization_id))


@router.get("/invoices")
def list_invoices(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(PurchaseInvoice).where(PurchaseInvoice.organization_id == ctx.organization_id).order_by(PurchaseInvoice.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/invoices", response_model=PurchaseInvoiceRead, status_code=201)
def add_invoice(body: PurchaseInvoiceCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_purchase_invoice(db, ctx, body)


@router.get("/invoices/{id}", response_model=PurchaseInvoiceRead)
def get_invoice(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, PurchaseInvoice, id, ctx.organization_id)


@router.put("/invoices/{id}", response_model=PurchaseInvoiceRead)
def update_invoice(id: uuid.UUID, body: PurchaseInvoiceCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    current = get_scoped(db, PurchaseInvoice, id, ctx.organization_id)
    if status_key(db, current.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft supplier invoices can be edited")
    db.delete(current)
    db.flush()
    return create_purchase_invoice(db, ctx, body)


@router.post("/invoices/{id}/post", response_model=PurchaseInvoiceRead)
def post_invoice(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, PurchaseInvoice, id, ctx.organization_id), ctx=ctx, module_key="purchasing", entity_key="purchase_invoice", status_key="posted")


@router.get("/supplier-payments")
def list_supplier_payments(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(Payment).where(Payment.organization_id == ctx.organization_id, Payment.payment_direction == "out").order_by(Payment.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/supplier-payments", status_code=201)
def add_supplier_payment(body: PaymentCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    if body.supplier_id is None:
        raise HTTPException(status_code=422, detail="supplier_id is required")
    return record_payment(db, ctx, direction="out", body=body)


@router.post("/supplier-payments/{id}/allocate")
def allocate_payment(id: uuid.UUID, body: AllocateBills, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    payment = get_scoped(db, Payment, id, ctx.organization_id)
    allocate_supplier_payment(db, ctx, payment, body.allocations)
    return {"payment_id": id, "allocations": [item.model_dump() for item in body.allocations]}
