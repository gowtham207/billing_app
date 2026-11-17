from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Context
from app.models import (
    CreditNote,
    Customer,
    Expense,
    GoodsReceipt,
    GoodsReceiptItem,
    InvoicePayment,
    Lead,
    Payment,
    Product,
    PurchaseInvoice,
    PurchaseInvoiceItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Quotation,
    QuotationItem,
    SalesInvoice,
    SalesInvoiceItem,
    SalesOrder,
    SalesOrderItem,
    SalesReturn,
    SalesReturnItem,
    StockAdjustment,
    StockAdjustmentItem,
    StockTransfer,
    StockTransferItem,
    SupplierPayment,
)
from app.services.common import allocate_number, apply_movement, ensure_mutable, get_scoped, money, quantity, set_status, status_key


def _header_totals(lines: list[dict], *, price_key: str, discount_key: str = "discount_amount", tax_key: str = "tax_amount", shipping=0):
    subtotal = money(sum(Decimal(str(line["quantity"])) * Decimal(str(line[price_key])) for line in lines))
    discount = money(sum(line.get(discount_key) or 0 for line in lines))
    tax = money(sum(line.get(tax_key) or 0 for line in lines))
    grand = money(subtotal - discount + tax + Decimal(str(shipping or 0)))
    if grand < 0:
        raise HTTPException(status_code=422, detail="Document total cannot be negative")
    return subtotal, discount, tax, grand


def _priced(line: dict) -> dict:
    if line.get("tax_amount") in (None, 0) and line.get("tax_rate"):
        net = Decimal(str(line["quantity"])) * Decimal(str(line["unit_price"])) - Decimal(str(line.get("discount_amount") or 0))
        line["tax_amount"] = money(net * Decimal(str(line["tax_rate"])) / Decimal("100"))
    return line


def _line_total(quantity_value, price, discount=0, tax=0) -> Decimal:
    total = money(Decimal(str(quantity_value)) * Decimal(str(price)) - Decimal(str(discount or 0)) + Decimal(str(tax or 0)))
    if total < 0:
        raise HTTPException(status_code=422, detail="Line total cannot be negative")
    return total


def create_quotation(db: Session, ctx: Context, body) -> Quotation:
    get_scoped(db, Customer, body.customer_id, ctx.organization_id)
    lines = [_priced(item.model_dump()) for item in body.items]
    subtotal, discount, tax, grand = _header_totals(lines, price_key="unit_price")
    quotation = Quotation(
        organization_id=ctx.organization_id,
        branch_id=body.branch_id,
        customer_id=body.customer_id,
        quotation_no=body.quotation_no or allocate_number(db, ctx.organization_id, "quotation", body.branch_id),
        quotation_date=body.quotation_date or date.today(),
        valid_until=body.valid_until,
        currency=body.currency,
        subtotal=subtotal,
        discount_total=discount,
        tax_total=tax,
        grand_total=grand,
        notes=body.notes,
        created_by=ctx.user.id,
    )
    db.add(quotation)
    db.flush()
    for line in lines:
        db.add(
            QuotationItem(
                organization_id=ctx.organization_id,
                quotation_id=quotation.id,
                product_id=line.get("product_id"),
                description=line["description"],
                quantity=quantity(line["quantity"]),
                unit_price=quantity(line["unit_price"]),
                discount_amount=money(line.get("discount_amount") or 0),
                tax_rate=line.get("tax_rate") or 0,
                line_total=_line_total(line["quantity"], line["unit_price"], line.get("discount_amount") or 0, line.get("tax_amount") or 0),
            )
        )
    set_status(db, quotation, ctx=ctx, module_key="billing", entity_key="quotation", status_key="draft")
    db.refresh(quotation)
    return quotation


def create_sales_order(db: Session, ctx: Context, body, quotation: Quotation | None = None) -> SalesOrder:
    customer_id = body.customer_id if quotation is None else quotation.customer_id
    get_scoped(db, Customer, customer_id, ctx.organization_id)
    source_lines = [item.model_dump() for item in body.items] if quotation is None else [
        {
            "product_id": item.product_id,
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "discount_amount": item.discount_amount,
            "tax_rate": item.tax_rate,
        }
        for item in db.scalars(select(QuotationItem).where(QuotationItem.quotation_id == quotation.id)).all()
    ]
    source_lines = [_priced(line) for line in source_lines]
    subtotal, discount, tax, grand = _header_totals(source_lines, price_key="unit_price")
    order = SalesOrder(
        organization_id=ctx.organization_id,
        branch_id=getattr(body, "branch_id", None) if quotation is None else quotation.branch_id,
        customer_id=customer_id,
        quotation_id=None if quotation is None else quotation.id,
        order_no=getattr(body, "order_no", None) or allocate_number(db, ctx.organization_id, "sales_order", getattr(body, "branch_id", None)),
        order_date=getattr(body, "order_date", None) or date.today(),
        currency=getattr(body, "currency", None) or (quotation.currency if quotation else "INR"),
        subtotal=subtotal,
        discount_total=discount,
        tax_total=tax,
        grand_total=grand,
        created_by=ctx.user.id,
    )
    db.add(order)
    db.flush()
    for line in source_lines:
        db.add(
            SalesOrderItem(
                organization_id=ctx.organization_id,
                sales_order_id=order.id,
                product_id=line.get("product_id"),
                variant_id=line.get("variant_id"),
                description=line["description"],
                quantity=quantity(line["quantity"]),
                unit_price=quantity(line["unit_price"]),
                discount_amount=money(line.get("discount_amount") or 0),
                tax_rate=line.get("tax_rate") or 0,
                line_total=_line_total(line["quantity"], line["unit_price"], line.get("discount_amount") or 0),
            )
        )
    set_status(db, order, ctx=ctx, module_key="billing", entity_key="sales_order", status_key="draft")
    db.refresh(order)
    return order


def create_invoice(db: Session, ctx: Context, body, order: SalesOrder | None = None) -> SalesInvoice:
    customer_id = body.customer_id if order is None else order.customer_id
    get_scoped(db, Customer, customer_id, ctx.organization_id)
    if order is None:
        source_lines = [item.model_dump() for item in body.items]
    else:
        existing = db.scalar(select(SalesInvoice.id).where(SalesInvoice.sales_order_id == order.id))
        if existing:
            raise HTTPException(status_code=409, detail="Sales order is already invoiced")
        source_lines = [
            {
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount_amount": item.discount_amount,
                "tax_amount": 0,
                "warehouse_id": None,
            }
            for item in db.scalars(select(SalesOrderItem).where(SalesOrderItem.sales_order_id == order.id)).all()
        ]
    shipping = getattr(body, "shipping_amount", 0) or 0
    subtotal, discount, tax, grand = _header_totals(source_lines, price_key="unit_price", shipping=shipping)
    invoice = SalesInvoice(
        organization_id=ctx.organization_id,
        branch_id=getattr(body, "branch_id", None) if order is None else order.branch_id,
        customer_id=customer_id,
        sales_order_id=None if order is None else order.id,
        invoice_no=getattr(body, "invoice_no", None) or allocate_number(db, ctx.organization_id, "sales_invoice", getattr(body, "branch_id", None)),
        invoice_date=getattr(body, "invoice_date", None) or date.today(),
        due_date=getattr(body, "due_date", None),
        currency=getattr(body, "currency", None) or (order.currency if order else "INR"),
        subtotal=subtotal,
        discount_total=discount,
        tax_total=tax,
        shipping_amount=money(shipping),
        grand_total=grand,
        amount_paid=0,
        notes=getattr(body, "notes", None),
        billing_snapshot=getattr(body, "billing_snapshot", None),
        created_by=ctx.user.id,
    )
    db.add(invoice)
    db.flush()
    for line in source_lines:
        db.add(
            SalesInvoiceItem(
                organization_id=ctx.organization_id,
                invoice_id=invoice.id,
                product_id=line.get("product_id"),
                variant_id=line.get("variant_id"),
                description=line["description"],
                quantity=quantity(line["quantity"]),
                unit_price=quantity(line["unit_price"]),
                discount_amount=money(line.get("discount_amount") or 0),
                tax_amount=money(line.get("tax_amount") or 0),
                line_total=_line_total(line["quantity"], line["unit_price"], line.get("discount_amount") or 0, line.get("tax_amount") or 0),
                warehouse_id=line.get("warehouse_id"),
            )
        )
    set_status(db, invoice, ctx=ctx, module_key="billing", entity_key="sales_invoice", status_key="draft")
    db.refresh(invoice)
    return invoice


def post_invoice(db: Session, ctx: Context, invoice: SalesInvoice) -> SalesInvoice:
    if invoice.issued_at is not None or status_key(db, invoice.status_id) == "posted":
        raise HTTPException(status_code=409, detail="Invoice is already posted")
    for item in db.scalars(select(SalesInvoiceItem).where(SalesInvoiceItem.invoice_id == invoice.id)).all():
        if item.product_id is None or item.warehouse_id is None:
            continue
        product = db.get(Product, item.product_id)
        if product is None or not product.track_inventory:
            continue
        apply_movement(
            db,
            organization_id=ctx.organization_id,
            warehouse_id=item.warehouse_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            movement_type="sale",
            quantity_delta=-item.quantity,
            unit_cost=product.purchase_price,
            source_type="sales_invoice",
            source_id=invoice.id,
            user_id=ctx.user.id,
        )
    invoice.issued_at = datetime.now(timezone.utc)
    set_status(db, invoice, ctx=ctx, module_key="billing", entity_key="sales_invoice", status_key="posted")
    return invoice


def cancel_invoice(db: Session, ctx: Context, invoice: SalesInvoice) -> SalesInvoice:
    if invoice.amount_paid and invoice.amount_paid > 0:
        raise HTTPException(status_code=409, detail="Paid invoices cannot be cancelled")
    if invoice.issued_at is not None:
        for item in db.scalars(select(SalesInvoiceItem).where(SalesInvoiceItem.invoice_id == invoice.id)).all():
            if item.product_id and item.warehouse_id:
                apply_movement(
                    db,
                    organization_id=ctx.organization_id,
                    warehouse_id=item.warehouse_id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    movement_type="adjustment",
                    quantity_delta=item.quantity,
                    source_type="sales_invoice_cancel",
                    source_id=invoice.id,
                    user_id=ctx.user.id,
                    notes="Reversal for cancelled invoice",
                )
    set_status(db, invoice, ctx=ctx, module_key="billing", entity_key="sales_invoice", status_key="cancelled")
    return invoice


def create_purchase_order(db: Session, ctx: Context, body) -> PurchaseOrder:
    lines = [item.model_dump() for item in body.items]
    subtotal = money(sum(Decimal(str(line["quantity"])) * Decimal(str(line["unit_cost"])) for line in lines))
    grand = Decimal("0")
    prepared = []
    for line in lines:
        base = Decimal(str(line["quantity"])) * Decimal(str(line["unit_cost"]))
        line_total = money(base * (1 + Decimal(str(line.get("tax_rate") or 0)) / Decimal("100")))
        grand += line_total
        prepared.append((line, line_total))
    order = PurchaseOrder(
        organization_id=ctx.organization_id,
        branch_id=body.branch_id,
        supplier_id=body.supplier_id,
        warehouse_id=body.warehouse_id,
        po_number=body.po_number or allocate_number(db, ctx.organization_id, "purchase_order", body.branch_id),
        order_date=body.order_date or date.today(),
        expected_date=body.expected_date,
        currency=body.currency,
        subtotal=subtotal,
        tax_total=money(grand - subtotal),
        grand_total=money(grand),
        notes=body.notes,
        created_by=ctx.user.id,
    )
    db.add(order)
    db.flush()
    for line, line_total in prepared:
        db.add(
            PurchaseOrderItem(
                organization_id=ctx.organization_id,
                purchase_order_id=order.id,
                product_id=line["product_id"],
                variant_id=line.get("variant_id"),
                description=line.get("description"),
                quantity=quantity(line["quantity"]),
                unit_cost=quantity(line["unit_cost"]),
                tax_rate=line.get("tax_rate") or 0,
                line_total=line_total,
            )
        )
    set_status(db, order, ctx=ctx, module_key="purchasing", entity_key="purchase_order", status_key="draft")
    db.refresh(order)
    return order


def create_goods_receipt(db: Session, ctx: Context, body) -> GoodsReceipt:
    receipt = GoodsReceipt(
        organization_id=ctx.organization_id,
        purchase_order_id=body.purchase_order_id,
        supplier_id=body.supplier_id,
        warehouse_id=body.warehouse_id,
        receipt_no=body.receipt_no or allocate_number(db, ctx.organization_id, "goods_receipt"),
        notes=body.notes,
        received_by=ctx.user.id,
    )
    db.add(receipt)
    db.flush()
    for item in body.items:
        db.add(
            GoodsReceiptItem(
                organization_id=ctx.organization_id,
                goods_receipt_id=receipt.id,
                purchase_order_item_id=item.purchase_order_item_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity_received=quantity(item.quantity_received),
                unit_cost=quantity(item.unit_cost),
            )
        )
    set_status(db, receipt, ctx=ctx, module_key="purchasing", entity_key="goods_receipt", status_key="draft")
    db.refresh(receipt)
    return receipt


def complete_receipt(db: Session, ctx: Context, receipt: GoodsReceipt) -> GoodsReceipt:
    if status_key(db, receipt.status_id) == "completed":
        raise HTTPException(status_code=409, detail="Goods receipt is already completed")
    for item in db.scalars(select(GoodsReceiptItem).where(GoodsReceiptItem.goods_receipt_id == receipt.id)).all():
        apply_movement(
            db,
            organization_id=ctx.organization_id,
            warehouse_id=receipt.warehouse_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            movement_type="purchase_receipt",
            quantity_delta=item.quantity_received,
            unit_cost=item.unit_cost,
            source_type="goods_receipt",
            source_id=receipt.id,
            user_id=ctx.user.id,
        )
        if item.purchase_order_item_id:
            po_item = db.get(PurchaseOrderItem, item.purchase_order_item_id)
            if po_item is not None:
                po_item.received_quantity = quantity(po_item.received_quantity + item.quantity_received)
    set_status(db, receipt, ctx=ctx, module_key="purchasing", entity_key="goods_receipt", status_key="completed")
    return receipt


def create_purchase_invoice(db: Session, ctx: Context, body) -> PurchaseInvoice:
    lines = [item.model_dump() for item in body.items]
    subtotal = money(sum(Decimal(str(line["quantity"])) * Decimal(str(line["unit_cost"])) for line in lines))
    tax = money(sum(line.get("tax_amount") or 0 for line in lines))
    invoice = PurchaseInvoice(
        organization_id=ctx.organization_id,
        supplier_id=body.supplier_id,
        goods_receipt_id=body.goods_receipt_id,
        vendor_invoice_no=body.vendor_invoice_no,
        purchase_invoice_no=body.purchase_invoice_no or allocate_number(db, ctx.organization_id, "purchase_invoice"),
        invoice_date=body.invoice_date or date.today(),
        due_date=body.due_date,
        currency=body.currency,
        subtotal=subtotal,
        tax_total=tax,
        grand_total=money(subtotal + tax),
        amount_paid=0,
    )
    db.add(invoice)
    db.flush()
    for line in lines:
        db.add(
            PurchaseInvoiceItem(
                organization_id=ctx.organization_id,
                purchase_invoice_id=invoice.id,
                product_id=line.get("product_id"),
                description=line["description"],
                quantity=quantity(line["quantity"]),
                unit_cost=quantity(line["unit_cost"]),
                tax_amount=money(line.get("tax_amount") or 0),
                line_total=_line_total(line["quantity"], line["unit_cost"], 0, line.get("tax_amount") or 0),
            )
        )
    set_status(db, invoice, ctx=ctx, module_key="purchasing", entity_key="purchase_invoice", status_key="draft")
    db.refresh(invoice)
    return invoice


def create_adjustment(db: Session, ctx: Context, body) -> StockAdjustment:
    adjustment = StockAdjustment(
        organization_id=ctx.organization_id,
        branch_id=body.branch_id,
        warehouse_id=body.warehouse_id,
        adjustment_no=body.adjustment_no or allocate_number(db, ctx.organization_id, "stock_adjustment", body.branch_id),
        reason=body.reason,
        created_by=ctx.user.id,
    )
    db.add(adjustment)
    db.flush()
    for item in body.items:
        system_quantity = item.system_quantity
        if system_quantity is None:
            from app.models import StockBalance

            balance = db.scalar(
                select(StockBalance).where(
                    StockBalance.organization_id == ctx.organization_id,
                    StockBalance.warehouse_id == body.warehouse_id,
                    StockBalance.product_id == item.product_id,
                    StockBalance.variant_id.is_(None) if item.variant_id is None else StockBalance.variant_id == item.variant_id,
                )
            )
            system_quantity = 0 if balance is None else balance.quantity_on_hand
        db.add(
            StockAdjustmentItem(
                organization_id=ctx.organization_id,
                adjustment_id=adjustment.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                counted_quantity=quantity(item.counted_quantity),
                system_quantity=quantity(system_quantity),
                reason=item.reason,
            )
        )
    set_status(db, adjustment, ctx=ctx, module_key="inventory", entity_key="stock_adjustment", status_key="draft")
    db.refresh(adjustment)
    return adjustment


def post_adjustment(db: Session, ctx: Context, adjustment: StockAdjustment) -> StockAdjustment:
    if status_key(db, adjustment.status_id) == "posted":
        raise HTTPException(status_code=409, detail="Adjustment is already posted")
    for item in db.scalars(select(StockAdjustmentItem).where(StockAdjustmentItem.adjustment_id == adjustment.id)).all():
        delta = quantity(item.counted_quantity - item.system_quantity)
        if delta == 0:
            continue
        apply_movement(
            db,
            organization_id=ctx.organization_id,
            warehouse_id=adjustment.warehouse_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            movement_type="adjustment",
            quantity_delta=delta,
            source_type="stock_adjustment",
            source_id=adjustment.id,
            user_id=ctx.user.id,
            notes=item.reason,
        )
    set_status(db, adjustment, ctx=ctx, module_key="inventory", entity_key="stock_adjustment", status_key="posted")
    return adjustment


def create_transfer(db: Session, ctx: Context, body) -> StockTransfer:
    if body.from_warehouse_id == body.to_warehouse_id:
        raise HTTPException(status_code=422, detail="Choose two different warehouses")
    transfer = StockTransfer(
        organization_id=ctx.organization_id,
        transfer_no=body.transfer_no or allocate_number(db, ctx.organization_id, "stock_transfer"),
        from_warehouse_id=body.from_warehouse_id,
        to_warehouse_id=body.to_warehouse_id,
        created_by=ctx.user.id,
    )
    db.add(transfer)
    db.flush()
    for item in body.items:
        db.add(
            StockTransferItem(
                organization_id=ctx.organization_id,
                transfer_id=transfer.id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=quantity(item.quantity),
            )
        )
    set_status(db, transfer, ctx=ctx, module_key="inventory", entity_key="stock_transfer", status_key="draft")
    db.refresh(transfer)
    return transfer


def complete_transfer(db: Session, ctx: Context, transfer: StockTransfer) -> StockTransfer:
    if status_key(db, transfer.status_id) == "completed":
        raise HTTPException(status_code=409, detail="Transfer is already completed")
    for item in db.scalars(select(StockTransferItem).where(StockTransferItem.transfer_id == transfer.id)).all():
        apply_movement(
            db,
            organization_id=ctx.organization_id,
            warehouse_id=transfer.from_warehouse_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            movement_type="transfer_out",
            quantity_delta=-item.quantity,
            source_type="stock_transfer",
            source_id=transfer.id,
            user_id=ctx.user.id,
        )
        from app.services.common import _balance

        source = _balance(db, ctx.organization_id, transfer.from_warehouse_id, item.product_id, item.variant_id)
        apply_movement(
            db,
            organization_id=ctx.organization_id,
            warehouse_id=transfer.to_warehouse_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            movement_type="transfer_in",
            quantity_delta=item.quantity,
            unit_cost=0 if source is None else source.average_cost,
            source_type="stock_transfer",
            source_id=transfer.id,
            user_id=ctx.user.id,
        )
    transfer.completed_at = datetime.now(timezone.utc)
    set_status(db, transfer, ctx=ctx, module_key="inventory", entity_key="stock_transfer", status_key="completed")
    return transfer


def record_payment(db: Session, ctx: Context, *, direction: str, body) -> Payment:
    payment = Payment(
        organization_id=ctx.organization_id,
        branch_id=body.branch_id,
        customer_id=body.customer_id if direction == "in" else None,
        supplier_id=body.supplier_id if direction == "out" else None,
        payment_no=body.payment_no or allocate_number(db, ctx.organization_id, "payment", body.branch_id),
        payment_direction=direction,
        payment_date=body.payment_date or date.today(),
        amount=money(body.amount),
        currency=body.currency or "INR",
        payment_method_id=body.payment_method_id,
        reference_no=body.reference_no,
        notes=body.notes,
        received_by=ctx.user.id,
    )
    db.add(payment)
    db.flush()
    db.refresh(payment)
    return payment


def allocate_customer_payment(db: Session, ctx: Context, payment: Payment, allocations: list) -> Payment:
    if payment.payment_direction != "in":
        raise HTTPException(status_code=422, detail="Only incoming payments can be allocated to invoices")
    already = sum(
        row.amount_applied
        for row in db.scalars(select(InvoicePayment).where(InvoicePayment.payment_id == payment.id)).all()
    )
    remaining = money(payment.amount - already)
    for allocation in allocations:
        amount = money(allocation.amount)
        if amount > remaining:
            raise HTTPException(status_code=422, detail="Allocation exceeds the unapplied payment")
        invoice = get_scoped(db, SalesInvoice, allocation.invoice_id, ctx.organization_id)
        db.refresh(invoice)
        if amount > invoice.balance_due:
            raise HTTPException(status_code=422, detail="Allocation exceeds the invoice balance")
        db.add(
            InvoicePayment(
                organization_id=ctx.organization_id,
                invoice_id=invoice.id,
                payment_id=payment.id,
                amount_applied=amount,
            )
        )
        invoice.amount_paid = money(invoice.amount_paid + amount)
        remaining = money(remaining - amount)
    db.flush()
    db.refresh(payment)
    return payment


def allocate_supplier_payment(db: Session, ctx: Context, payment: Payment, allocations: list) -> Payment:
    if payment.payment_direction != "out":
        raise HTTPException(status_code=422, detail="Only outgoing payments can be allocated to supplier invoices")
    already = sum(
        row.amount_applied
        for row in db.scalars(select(SupplierPayment).where(SupplierPayment.payment_id == payment.id)).all()
    )
    remaining = money(payment.amount - already)
    for allocation in allocations:
        amount = money(allocation.amount)
        if amount > remaining:
            raise HTTPException(status_code=422, detail="Allocation exceeds the unapplied payment")
        invoice = get_scoped(db, PurchaseInvoice, allocation.purchase_invoice_id, ctx.organization_id)
        db.refresh(invoice)
        if amount > invoice.balance_due:
            raise HTTPException(status_code=422, detail="Allocation exceeds the supplier invoice balance")
        db.add(
            SupplierPayment(
                organization_id=ctx.organization_id,
                purchase_invoice_id=invoice.id,
                payment_id=payment.id,
                amount_applied=amount,
            )
        )
        invoice.amount_paid = money(invoice.amount_paid + amount)
        remaining = money(remaining - amount)
    db.flush()
    db.refresh(payment)
    return payment


def refund_payment(db: Session, ctx: Context, payment: Payment) -> Payment:
    if payment.payment_status == "refunded":
        raise HTTPException(status_code=409, detail="Payment is already refunded")
    for allocation in db.scalars(select(InvoicePayment).where(InvoicePayment.payment_id == payment.id)).all():
        invoice = db.get(SalesInvoice, allocation.invoice_id)
        invoice.amount_paid = money(invoice.amount_paid - allocation.amount_applied)
        db.delete(allocation)
    for allocation in db.scalars(select(SupplierPayment).where(SupplierPayment.payment_id == payment.id)).all():
        invoice = db.get(PurchaseInvoice, allocation.purchase_invoice_id)
        invoice.amount_paid = money(invoice.amount_paid - allocation.amount_applied)
        db.delete(allocation)
    payment.payment_status = "refunded"
    db.flush()
    db.refresh(payment)
    return payment


def create_return(db: Session, ctx: Context, body) -> SalesReturn:
    sales_return = SalesReturn(
        organization_id=ctx.organization_id,
        invoice_id=body.invoice_id,
        return_no=body.return_no or allocate_number(db, ctx.organization_id, "sales_return"),
        return_date=body.return_date or date.today(),
        warehouse_id=body.warehouse_id,
        reason=body.reason,
        created_by=ctx.user.id,
    )
    db.add(sales_return)
    db.flush()
    for item in body.items:
        db.add(
            SalesReturnItem(
                organization_id=ctx.organization_id,
                sales_return_id=sales_return.id,
                invoice_item_id=item.invoice_item_id,
                product_id=item.product_id,
                variant_id=item.variant_id,
                quantity=quantity(item.quantity),
                refund_amount=money(item.refund_amount or 0),
                restock=item.restock,
            )
        )
    set_status(db, sales_return, ctx=ctx, module_key="billing", entity_key="sales_return", status_key="draft")
    db.refresh(sales_return)
    return sales_return


def complete_return(db: Session, ctx: Context, sales_return: SalesReturn) -> SalesReturn:
    if status_key(db, sales_return.status_id) == "completed":
        raise HTTPException(status_code=409, detail="Return is already completed")
    for item in db.scalars(select(SalesReturnItem).where(SalesReturnItem.sales_return_id == sales_return.id)).all():
        if not item.restock:
            continue
        apply_movement(
            db,
            organization_id=ctx.organization_id,
            warehouse_id=sales_return.warehouse_id,
            product_id=item.product_id,
            variant_id=item.variant_id,
            movement_type="sales_return",
            quantity_delta=item.quantity,
            source_type="sales_return",
            source_id=sales_return.id,
            user_id=ctx.user.id,
        )
    set_status(db, sales_return, ctx=ctx, module_key="billing", entity_key="sales_return", status_key="completed")
    return sales_return


def create_credit_note(db: Session, ctx: Context, body) -> CreditNote:
    note = CreditNote(
        organization_id=ctx.organization_id,
        customer_id=body.customer_id,
        invoice_id=body.invoice_id,
        credit_note_no=body.credit_note_no or allocate_number(db, ctx.organization_id, "credit_note"),
        issue_date=body.issue_date or date.today(),
        amount=money(body.amount),
        reason=body.reason,
    )
    db.add(note)
    db.flush()
    set_status(db, note, ctx=ctx, module_key="billing", entity_key="credit_note", status_key="draft")
    db.refresh(note)
    return note


def create_expense(db: Session, ctx: Context, body) -> Expense:
    expense = Expense(
        organization_id=ctx.organization_id,
        branch_id=body.branch_id,
        category_id=body.category_id,
        expense_no=body.expense_no or allocate_number(db, ctx.organization_id, "expense", body.branch_id),
        expense_date=body.expense_date or date.today(),
        amount=money(body.amount),
        tax_amount=money(body.tax_amount or 0),
        currency=body.currency or "INR",
        vendor_name=body.vendor_name,
        description=body.description,
        created_by=ctx.user.id,
    )
    db.add(expense)
    db.flush()
    set_status(db, expense, ctx=ctx, module_key="expenses", entity_key="expense", status_key="draft")
    db.refresh(expense)
    return expense


def convert_lead(db: Session, ctx: Context, lead: Lead) -> Customer:
    if lead.converted_customer_id is not None:
        raise HTTPException(status_code=409, detail="Lead is already converted")
    customer = Customer(
        organization_id=ctx.organization_id,
        customer_code=allocate_number(db, ctx.organization_id, "customer"),
        display_name=lead.company_name or lead.contact_name,
        legal_name=lead.company_name,
        email=lead.email,
        phone=lead.phone,
    )
    db.add(customer)
    db.flush()
    lead.converted_customer_id = customer.id
    set_status(db, lead, ctx=ctx, module_key="crm", entity_key="lead", status_key="converted")
    db.refresh(customer)
    return customer
