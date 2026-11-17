import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response as RawResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.mount import mount_collection, mount_item
from app.core.deps import Context, get_db, require_org, require_write
from app.models import (
    BillingSettings,
    CreditNote,
    Customer,
    DocumentSequence,
    InvoicePayment,
    InvoiceTemplate,
    Payment,
    PaymentMethod,
    Quotation,
    SalesInvoice,
    SalesInvoiceItem,
    SalesOrder,
    SalesReturn,
    TaxGroup,
    TaxGroupRate,
    TaxRate,
)
from app.schemas.generated import (
    BillingSettingsRead,
    BillingSettingsUpdate,
    CreditNoteRead,
    DocumentSequenceCreate,
    DocumentSequenceRead,
    DocumentSequenceUpdate,
    InvoiceTemplateCreate,
    InvoiceTemplateRead,
    InvoiceTemplateUpdate,
    PaymentMethodCreate,
    PaymentMethodRead,
    PaymentRead,
    QuotationRead,
    SalesInvoiceItemRead,
    SalesInvoiceRead,
    SalesOrderRead,
    SalesReturnRead,
    TaxRateCreate,
    TaxRateRead,
    TaxRateUpdate,
)
from app.schemas.requests import (
    AllocateInvoices,
    CreditNoteCreateRequest,
    InvoiceCreateBody,
    PaymentCreateRequest,
    QuotationCreateRequest,
    ReturnCreateRequest,
    SalesOrderCreateRequest,
    TaxGroupCreateRequest,
)
from app.services.common import apply_update, create_model, get_scoped, set_status, status_key
from app.services.documents import (
    allocate_customer_payment,
    cancel_invoice,
    complete_return,
    create_credit_note,
    create_invoice,
    create_quotation,
    create_return,
    create_sales_order,
    post_invoice,
    refund_payment,
)
from app.services.pdf import build_pdf
from app.services.reports import customer_ledger

router = APIRouter(prefix="/billing")
P = "billing.write"

mount_collection(router, name="sequences", path="/sequences", model=DocumentSequence, read=DocumentSequenceRead, create=DocumentSequenceCreate, tag="Billing - Settings & Masters", permission="settings.write")
mount_item(router, name="sequences", path="/sequences", model=DocumentSequence, read=DocumentSequenceRead, update=DocumentSequenceUpdate, tag="Billing - Settings & Masters", permission="settings.write", can_get=False, can_delete=False)
mount_collection(router, name="tax_rates", path="/tax-rates", model=TaxRate, read=TaxRateRead, create=TaxRateCreate, tag="Billing - Settings & Masters", search=("name", "tax_code"), permission="settings.write")
mount_item(router, name="tax_rates", path="/tax-rates", model=TaxRate, read=TaxRateRead, update=TaxRateUpdate, tag="Billing - Settings & Masters", permission="settings.write", can_get=False, can_delete=False)
mount_collection(router, name="payment_methods", path="/payment-methods", model=PaymentMethod, read=PaymentMethodRead, create=PaymentMethodCreate, tag="Billing - Settings & Masters", search=("display_name",), permission="settings.write")
mount_collection(router, name="templates", path="/invoice-templates", model=InvoiceTemplate, read=InvoiceTemplateRead, create=InvoiceTemplateCreate, tag="Billing - Settings & Masters", search=("name",), permission="settings.write")
mount_item(router, name="templates", path="/invoice-templates", model=InvoiceTemplate, read=InvoiceTemplateRead, update=InvoiceTemplateUpdate, tag="Billing - Settings & Masters", permission="settings.write", can_get=False, can_delete=False)


@router.get("/settings", response_model=BillingSettingsRead, tags=["Billing - Settings & Masters"])
def get_settings(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    row = db.get(BillingSettings, ctx.organization_id)
    if row is None:
        row = BillingSettings(organization_id=ctx.organization_id)
        db.add(row)
        db.flush()
        db.refresh(row)
    return row


@router.put("/settings", response_model=BillingSettingsRead, tags=["Billing - Settings & Masters"])
def update_settings(body: BillingSettingsUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    row = db.get(BillingSettings, ctx.organization_id)
    if row is None:
        row = BillingSettings(organization_id=ctx.organization_id)
        db.add(row)
        db.flush()
    return apply_update(db, row, body.model_dump(exclude_unset=True), ctx)


@router.get("/tax-groups", tags=["Billing - Settings & Masters"])
def list_tax_groups(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return db.scalars(select(TaxGroup).where(TaxGroup.organization_id == ctx.organization_id).order_by(TaxGroup.name)).all()


@router.post("/tax-groups", status_code=201, tags=["Billing - Settings & Masters"])
def create_tax_group(body: TaxGroupCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    group = create_model(db, TaxGroup, {"organization_id": ctx.organization_id, "name": body.name}, ctx, "tax_groups")
    for index, tax_rate_id in enumerate(body.tax_rate_ids):
        db.add(TaxGroupRate(organization_id=ctx.organization_id, tax_group_id=group.id, tax_rate_id=tax_rate_id, sort_order=index))
    db.flush()
    return group


def _page(rows, page: int, page_size: int):
    start = (page - 1) * page_size
    return {"items": rows[start : start + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.get("/quotations", tags=["Billing - Quotations & Sales Orders"])
def list_quotations(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(Quotation).where(Quotation.organization_id == ctx.organization_id).order_by(Quotation.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/quotations", response_model=QuotationRead, status_code=201, tags=["Billing - Quotations & Sales Orders"])
def add_quotation(body: QuotationCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_quotation(db, ctx, body)


@router.get("/quotations/{id}", response_model=QuotationRead, tags=["Billing - Quotations & Sales Orders"])
def get_quotation(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, Quotation, id, ctx.organization_id)


@router.put("/quotations/{id}", response_model=QuotationRead, tags=["Billing - Quotations & Sales Orders"])
def update_quotation(id: uuid.UUID, body: QuotationCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    current = get_scoped(db, Quotation, id, ctx.organization_id)
    if status_key(db, current.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft quotations can be edited")
    db.delete(current)
    db.flush()
    return create_quotation(db, ctx, body)


@router.post("/quotations/{id}/send", response_model=QuotationRead, tags=["Billing - Quotations & Sales Orders"])
def send_quotation(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, Quotation, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="quotation", status_key="sent")


@router.post("/quotations/{id}/accept", response_model=QuotationRead, tags=["Billing - Quotations & Sales Orders"])
def accept_quotation(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, Quotation, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="quotation", status_key="accepted")


@router.post("/quotations/{id}/reject", response_model=QuotationRead, tags=["Billing - Quotations & Sales Orders"])
def reject_quotation(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, Quotation, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="quotation", status_key="rejected")


@router.post("/quotations/{id}/convert-to-order", response_model=SalesOrderRead, tags=["Billing - Quotations & Sales Orders"])
def quotation_to_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    quotation = get_scoped(db, Quotation, id, ctx.organization_id)
    order = create_sales_order(db, ctx, quotation, quotation)
    set_status(db, quotation, ctx=ctx, module_key="billing", entity_key="quotation", status_key="accepted")
    return order


@router.get("/orders", tags=["Billing - Quotations & Sales Orders"])
def list_orders(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(SalesOrder).where(SalesOrder.organization_id == ctx.organization_id).order_by(SalesOrder.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/orders", response_model=SalesOrderRead, status_code=201, tags=["Billing - Quotations & Sales Orders"])
def add_order(body: SalesOrderCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_sales_order(db, ctx, body)


@router.get("/orders/{id}", response_model=SalesOrderRead, tags=["Billing - Quotations & Sales Orders"])
def get_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, SalesOrder, id, ctx.organization_id)


@router.put("/orders/{id}", response_model=SalesOrderRead, tags=["Billing - Quotations & Sales Orders"])
def update_order(id: uuid.UUID, body: SalesOrderCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    current = get_scoped(db, SalesOrder, id, ctx.organization_id)
    if status_key(db, current.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft sales orders can be edited")
    db.delete(current)
    db.flush()
    return create_sales_order(db, ctx, body)


@router.post("/orders/{id}/confirm", response_model=SalesOrderRead, tags=["Billing - Quotations & Sales Orders"])
def confirm_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, SalesOrder, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="sales_order", status_key="confirmed")


@router.post("/orders/{id}/cancel", response_model=SalesOrderRead, tags=["Billing - Quotations & Sales Orders"])
def cancel_order(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, SalesOrder, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="sales_order", status_key="cancelled")


@router.post("/orders/{id}/convert-to-invoice", response_model=SalesInvoiceRead, tags=["Billing - Quotations & Sales Orders"])
def order_to_invoice(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    order = get_scoped(db, SalesOrder, id, ctx.organization_id)
    invoice = create_invoice(db, ctx, order, order)
    set_status(db, order, ctx=ctx, module_key="billing", entity_key="sales_order", status_key="invoiced")
    return invoice


@router.get("/invoices", tags=["Billing - Invoices & Payments"])
def list_invoices(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(SalesInvoice).where(SalesInvoice.organization_id == ctx.organization_id).order_by(SalesInvoice.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/invoices", response_model=SalesInvoiceRead, status_code=201, tags=["Billing - Invoices & Payments"])
def add_invoice(body: InvoiceCreateBody, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_invoice(db, ctx, body)


@router.get("/invoices/{id}", response_model=SalesInvoiceRead, tags=["Billing - Invoices & Payments"])
def get_invoice(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, SalesInvoice, id, ctx.organization_id)


@router.get("/invoices/{id}/items", response_model=list[SalesInvoiceItemRead], tags=["Billing - Invoices & Payments"])
def invoice_items(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, SalesInvoice, id, ctx.organization_id)
    return db.scalars(select(SalesInvoiceItem).where(SalesInvoiceItem.invoice_id == id)).all()


@router.put("/invoices/{id}", response_model=SalesInvoiceRead, tags=["Billing - Invoices & Payments"])
def update_invoice(id: uuid.UUID, body: InvoiceCreateBody, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    current = get_scoped(db, SalesInvoice, id, ctx.organization_id)
    if current.issued_at is not None or status_key(db, current.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft invoices can be edited")
    db.delete(current)
    db.flush()
    return create_invoice(db, ctx, body)


@router.post("/invoices/{id}/approve", response_model=SalesInvoiceRead, tags=["Billing - Invoices & Payments"])
def approve_invoice(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, SalesInvoice, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="sales_invoice", status_key="approved")


@router.post("/invoices/{id}/post", response_model=SalesInvoiceRead, tags=["Billing - Invoices & Payments"])
def post_sales_invoice(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return post_invoice(db, ctx, get_scoped(db, SalesInvoice, id, ctx.organization_id))


@router.post("/invoices/{id}/cancel", response_model=SalesInvoiceRead, tags=["Billing - Invoices & Payments"])
def cancel_sales_invoice(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return cancel_invoice(db, ctx, get_scoped(db, SalesInvoice, id, ctx.organization_id))


@router.get("/invoices/{id}/pdf", tags=["Billing - Invoices & Payments"])
def invoice_pdf(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    invoice = get_scoped(db, SalesInvoice, id, ctx.organization_id)
    customer = db.get(Customer, invoice.customer_id)
    lines = [f"Invoice {invoice.invoice_no}", f"Date {invoice.invoice_date}", f"Customer {customer.display_name if customer else ''}", ""]
    for item in db.scalars(select(SalesInvoiceItem).where(SalesInvoiceItem.invoice_id == invoice.id)).all():
        lines.append(f"{item.description}  {item.quantity} x {item.unit_price} = {item.line_total}")
    lines.append("")
    lines.append(f"Grand total {invoice.grand_total}")
    lines.append(f"Balance due {invoice.balance_due}")
    return RawResponse(build_pdf(lines), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_no}.pdf"'})


@router.get("/invoices/{id}/payments", tags=["Billing - Invoices & Payments"])
def invoice_payments(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, SalesInvoice, id, ctx.organization_id)
    return db.scalars(select(InvoicePayment).where(InvoicePayment.organization_id == ctx.organization_id, InvoicePayment.invoice_id == id)).all()


@router.get("/invoices/{id}/outstanding", tags=["Billing - Invoices & Payments"])
def invoice_outstanding(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    invoice = get_scoped(db, SalesInvoice, id, ctx.organization_id)
    db.refresh(invoice)
    return {"invoice_id": invoice.id, "grand_total": invoice.grand_total, "amount_paid": invoice.amount_paid, "balance_due": invoice.balance_due}


@router.get("/payments", tags=["Billing - Invoices & Payments"])
def list_payments(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(Payment).where(Payment.organization_id == ctx.organization_id, Payment.payment_direction == "in").order_by(Payment.created_at.desc())).all()
    return _page([PaymentRead.model_validate(row).model_dump() for row in rows], page, page_size)


@router.post("/payments", response_model=PaymentRead, status_code=201, tags=["Billing - Invoices & Payments"])
def add_payment(body: PaymentCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    if body.customer_id is None:
        raise HTTPException(status_code=422, detail="customer_id is required")
    return record_payment_in(db, ctx, body)


def record_payment_in(db, ctx, body):
    from app.services.documents import record_payment

    return record_payment(db, ctx, direction="in", body=body)


@router.get("/payments/{id}", response_model=PaymentRead, tags=["Billing - Invoices & Payments"])
def get_payment(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, Payment, id, ctx.organization_id)


@router.post("/payments/{id}/allocate", tags=["Billing - Invoices & Payments"])
def allocate_payment(id: uuid.UUID, body: AllocateInvoices, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    payment = get_scoped(db, Payment, id, ctx.organization_id)
    allocate_customer_payment(db, ctx, payment, body.allocations)
    return {"payment_id": id}


@router.post("/payments/{id}/refund", response_model=PaymentRead, tags=["Billing - Invoices & Payments"])
def refund(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return refund_payment(db, ctx, get_scoped(db, Payment, id, ctx.organization_id))


@router.get("/customers/{customer_id}/outstanding", tags=["Billing - Invoices & Payments"])
def customer_outstanding(customer_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Customer, customer_id, ctx.organization_id)
    total = db.scalar(
        select(func.coalesce(func.sum(SalesInvoice.balance_due), 0)).where(
            SalesInvoice.organization_id == ctx.organization_id, SalesInvoice.customer_id == customer_id
        )
    )
    return {"customer_id": customer_id, "outstanding": total}


@router.get("/customers/{customer_id}/ledger", tags=["Billing - Invoices & Payments"])
def ledger(customer_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Customer, customer_id, ctx.organization_id)
    return customer_ledger(db, ctx.organization_id, customer_id)


@router.get("/returns", tags=["Billing - Returns & Credit Notes"])
def list_returns(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(SalesReturn).where(SalesReturn.organization_id == ctx.organization_id).order_by(SalesReturn.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/returns", response_model=SalesReturnRead, status_code=201, tags=["Billing - Returns & Credit Notes"])
def add_return(body: ReturnCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_return(db, ctx, body)


@router.get("/returns/{id}", response_model=SalesReturnRead, tags=["Billing - Returns & Credit Notes"])
def get_return(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, SalesReturn, id, ctx.organization_id)


@router.post("/returns/{id}/approve", response_model=SalesReturnRead, tags=["Billing - Returns & Credit Notes"])
def approve_return(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, SalesReturn, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="sales_return", status_key="approved")


@router.post("/returns/{id}/complete", response_model=SalesReturnRead, tags=["Billing - Returns & Credit Notes"])
def finish_return(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return complete_return(db, ctx, get_scoped(db, SalesReturn, id, ctx.organization_id))


@router.get("/credit-notes", tags=["Billing - Returns & Credit Notes"])
def list_credit_notes(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(CreditNote).where(CreditNote.organization_id == ctx.organization_id).order_by(CreditNote.created_at.desc())).all()
    return _page(rows, page, page_size)


@router.post("/credit-notes", response_model=CreditNoteRead, status_code=201, tags=["Billing - Returns & Credit Notes"])
def add_credit_note(body: CreditNoteCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_credit_note(db, ctx, body)


@router.get("/credit-notes/{id}", response_model=CreditNoteRead, tags=["Billing - Returns & Credit Notes"])
def get_credit_note(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, CreditNote, id, ctx.organization_id)


@router.post("/credit-notes/{id}/issue", response_model=CreditNoteRead, tags=["Billing - Returns & Credit Notes"])
def issue_credit_note(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, CreditNote, id, ctx.organization_id), ctx=ctx, module_key="billing", entity_key="credit_note", status_key="issued")
