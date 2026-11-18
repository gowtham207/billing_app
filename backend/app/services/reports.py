from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Customer,
    Expense,
    InvoiceItemTax,
    Lead,
    Payment,
    Product,
    PurchaseInvoice,
    SalesInvoice,
    SalesInvoiceItem,
    StatusDefinition,
    StockBalance,
    StockMovement,
    Supplier,
)


def plain(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def records(rows) -> list[dict]:
    return [{key: plain(value) for key, value in row._mapping.items()} for row in rows]


def _between(stmt, column, date_from, date_to):
    if date_from is not None:
        stmt = stmt.where(column >= date_from)
    if date_to is not None:
        stmt = stmt.where(column <= date_to)
    return stmt


def not_cancelled(organization_id):
    cancelled = select(StatusDefinition.id).where(
        StatusDefinition.organization_id == organization_id,
        func.lower(StatusDefinition.status_key).in_(("cancelled", "canceled")),
    )
    return or_(SalesInvoice.status_id.is_(None), SalesInvoice.status_id.not_in(cancelled))


def sales_rows(db: Session, organization_id, date_from=None, date_to=None):
    stmt = select(
        SalesInvoice.invoice_no,
        SalesInvoice.invoice_date,
        SalesInvoice.customer_id,
        SalesInvoice.grand_total,
        SalesInvoice.amount_paid,
        SalesInvoice.balance_due,
    ).where(SalesInvoice.organization_id == organization_id, not_cancelled(organization_id))
    return records(db.execute(_between(stmt, SalesInvoice.invoice_date, date_from, date_to).order_by(SalesInvoice.invoice_date.desc())).all())


def purchase_rows(db: Session, organization_id, date_from=None, date_to=None):
    stmt = select(
        PurchaseInvoice.purchase_invoice_no,
        PurchaseInvoice.invoice_date,
        PurchaseInvoice.supplier_id,
        PurchaseInvoice.grand_total,
        PurchaseInvoice.amount_paid,
        PurchaseInvoice.balance_due,
    ).where(PurchaseInvoice.organization_id == organization_id)
    return records(db.execute(_between(stmt, PurchaseInvoice.invoice_date, date_from, date_to).order_by(PurchaseInvoice.invoice_date.desc())).all())


def inventory_rows(db: Session, organization_id):
    stmt = (
        select(
            Product.sku,
            Product.name,
            func.coalesce(func.sum(StockBalance.quantity_on_hand), 0).label("quantity_on_hand"),
            func.coalesce(func.sum(StockBalance.quantity_available), 0).label("quantity_available"),
            Product.reorder_level,
        )
        .outerjoin(StockBalance, (StockBalance.product_id == Product.id) & (StockBalance.organization_id == Product.organization_id))
        .where(Product.organization_id == organization_id)
        .group_by(Product.id)
        .order_by(Product.name)
    )
    return records(db.execute(stmt).all())


def movement_rows(db: Session, organization_id, date_from=None, date_to=None):
    stmt = select(
        StockMovement.occurred_at,
        StockMovement.movement_type,
        StockMovement.product_id,
        StockMovement.warehouse_id,
        StockMovement.quantity_delta,
        StockMovement.unit_cost,
    ).where(StockMovement.organization_id == organization_id)
    return records(db.execute(_between(stmt, StockMovement.occurred_at, date_from, date_to).order_by(StockMovement.occurred_at.desc())).all())


def customer_ledger(db: Session, organization_id, customer_id):
    invoices = db.execute(
        select(SalesInvoice.invoice_date, SalesInvoice.invoice_no, SalesInvoice.grand_total).where(
            SalesInvoice.organization_id == organization_id, SalesInvoice.customer_id == customer_id
        )
    ).all()
    payments = db.execute(
        select(Payment.payment_date, Payment.payment_no, Payment.amount).where(
            Payment.organization_id == organization_id, Payment.customer_id == customer_id, Payment.payment_status == "completed"
        )
    ).all()
    rows = [{"date": plain(row.invoice_date), "type": "invoice", "reference": row.invoice_no, "debit": plain(row.grand_total), "credit": 0} for row in invoices]
    rows.extend({"date": plain(row.payment_date), "type": "payment", "reference": row.payment_no, "debit": 0, "credit": plain(row.amount)} for row in payments)
    rows.sort(key=lambda row: row["date"] or "")
    balance = 0
    for row in rows:
        balance += row["debit"] - row["credit"]
        row["balance"] = balance
    return rows


def supplier_ledger(db: Session, organization_id, supplier_id):
    invoices = db.execute(
        select(PurchaseInvoice.invoice_date, PurchaseInvoice.purchase_invoice_no, PurchaseInvoice.grand_total).where(
            PurchaseInvoice.organization_id == organization_id, PurchaseInvoice.supplier_id == supplier_id
        )
    ).all()
    payments = db.execute(
        select(Payment.payment_date, Payment.payment_no, Payment.amount).where(
            Payment.organization_id == organization_id, Payment.supplier_id == supplier_id, Payment.payment_status == "completed"
        )
    ).all()
    rows = [{"date": plain(row.invoice_date), "type": "bill", "reference": row.purchase_invoice_no, "credit": plain(row.grand_total), "debit": 0} for row in invoices]
    rows.extend({"date": plain(row.payment_date), "type": "payment", "reference": row.payment_no, "credit": 0, "debit": plain(row.amount)} for row in payments)
    rows.sort(key=lambda row: row["date"] or "")
    balance = 0
    for row in rows:
        balance += row["credit"] - row["debit"]
        row["balance"] = balance
    return rows


def outstanding_rows(db: Session, organization_id):
    stmt = (
        select(Customer.display_name, func.coalesce(func.sum(SalesInvoice.balance_due), 0).label("outstanding"))
        .join(SalesInvoice, (SalesInvoice.customer_id == Customer.id) & (SalesInvoice.organization_id == Customer.organization_id))
        .where(Customer.organization_id == organization_id, SalesInvoice.balance_due > 0, not_cancelled(organization_id))
        .group_by(Customer.id)
        .order_by(func.sum(SalesInvoice.balance_due).desc())
    )
    return records(db.execute(stmt).all())


def expense_rows(db: Session, organization_id, date_from=None, date_to=None):
    stmt = select(Expense.expense_no, Expense.expense_date, Expense.vendor_name, Expense.amount, Expense.tax_amount).where(
        Expense.organization_id == organization_id
    )
    return records(db.execute(_between(stmt, Expense.expense_date, date_from, date_to).order_by(Expense.expense_date.desc())).all())


def tax_rows(db: Session, organization_id):
    stmt = (
        select(InvoiceItemTax.tax_rate_id, func.coalesce(func.sum(InvoiceItemTax.tax_amount), 0).label("tax_amount"))
        .where(InvoiceItemTax.organization_id == organization_id)
        .group_by(InvoiceItemTax.tax_rate_id)
    )
    return records(db.execute(stmt).all())


def profit_loss(db: Session, organization_id, date_from=None, date_to=None) -> dict:
    sales = db.scalar(_between(select(func.coalesce(func.sum(SalesInvoice.grand_total), 0)).where(SalesInvoice.organization_id == organization_id, not_cancelled(organization_id)), SalesInvoice.invoice_date, date_from, date_to))
    purchases = db.scalar(_between(select(func.coalesce(func.sum(PurchaseInvoice.grand_total), 0)).where(PurchaseInvoice.organization_id == organization_id), PurchaseInvoice.invoice_date, date_from, date_to))
    expenses = db.scalar(_between(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.organization_id == organization_id), Expense.expense_date, date_from, date_to))
    sales, purchases, expenses = money_float(sales), money_float(purchases), money_float(expenses)
    return {"revenue": sales, "purchases": purchases, "expenses": expenses, "profit": sales - purchases - expenses}


def money_float(value) -> float:
    return float(value or 0)


def overview(db: Session, organization_id) -> dict:
    return {
        "customers": db.scalar(select(func.count()).select_from(Customer).where(Customer.organization_id == organization_id)) or 0,
        "leads": db.scalar(select(func.count()).select_from(Lead).where(Lead.organization_id == organization_id)) or 0,
        "revenue": money_float(db.scalar(select(func.coalesce(func.sum(SalesInvoice.grand_total), 0)).where(SalesInvoice.organization_id == organization_id, not_cancelled(organization_id)))),
        "outstanding": money_float(db.scalar(select(func.coalesce(func.sum(SalesInvoice.balance_due), 0)).where(SalesInvoice.organization_id == organization_id, not_cancelled(organization_id)))),
        "purchases": money_float(db.scalar(select(func.coalesce(func.sum(PurchaseInvoice.grand_total), 0)).where(PurchaseInvoice.organization_id == organization_id))),
        "expenses": money_float(db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.organization_id == organization_id))),
        "products": db.scalar(select(func.count()).select_from(Product).where(Product.organization_id == organization_id, Product.is_active.is_(True))) or 0,
    }


def grouped_chart(db: Session, model, amount_column, date_column, organization_id, date_from=None, date_to=None, extra=None):
    stmt = (
        select(date_column.label("day"), func.coalesce(func.sum(amount_column), 0).label("amount"))
        .where(model.organization_id == organization_id)
        .group_by(date_column)
        .order_by(date_column)
    )
    if extra is not None:
        stmt = stmt.where(extra)
    return records(db.execute(_between(stmt, date_column, date_from, date_to)).all())


def low_stock(db: Session, organization_id):
    return [row for row in inventory_rows(db, organization_id) if row["quantity_available"] <= row["reorder_level"]]


def top_products(db: Session, organization_id):
    stmt = (
        select(Product.name, Product.sku, func.coalesce(func.sum(SalesInvoiceItem.quantity), 0).label("quantity"))
        .join(SalesInvoiceItem, (SalesInvoiceItem.product_id == Product.id) & (SalesInvoiceItem.organization_id == Product.organization_id))
        .join(SalesInvoice, (SalesInvoice.id == SalesInvoiceItem.invoice_id) & (SalesInvoice.organization_id == SalesInvoiceItem.organization_id))
        .where(Product.organization_id == organization_id, not_cancelled(organization_id))
        .group_by(Product.id)
        .order_by(func.sum(SalesInvoiceItem.quantity).desc())
        .limit(10)
    )
    return records(db.execute(stmt).all())


def top_customers(db: Session, organization_id):
    stmt = (
        select(Customer.display_name, func.coalesce(func.sum(SalesInvoice.grand_total), 0).label("revenue"))
        .join(SalesInvoice, (SalesInvoice.customer_id == Customer.id) & (SalesInvoice.organization_id == Customer.organization_id))
        .where(Customer.organization_id == organization_id, not_cancelled(organization_id))
        .group_by(Customer.id)
        .order_by(func.sum(SalesInvoice.grand_total).desc())
        .limit(10)
    )
    return records(db.execute(stmt).all())


REPORTS = {
    "sales": lambda db, org, filters: sales_rows(db, org, filters.get("date_from"), filters.get("date_to")),
    "purchases": lambda db, org, filters: purchase_rows(db, org, filters.get("date_from"), filters.get("date_to")),
    "inventory": lambda db, org, filters: inventory_rows(db, org),
    "stock_movement": lambda db, org, filters: movement_rows(db, org, filters.get("date_from"), filters.get("date_to")),
    "stock-movement": lambda db, org, filters: movement_rows(db, org, filters.get("date_from"), filters.get("date_to")),
    "customer_ledger": lambda db, org, filters: customer_ledger(db, org, filters.get("customer_id")),
    "customer-ledger": lambda db, org, filters: customer_ledger(db, org, filters.get("customer_id")),
    "supplier_ledger": lambda db, org, filters: supplier_ledger(db, org, filters.get("supplier_id")),
    "supplier-ledger": lambda db, org, filters: supplier_ledger(db, org, filters.get("supplier_id")),
    "outstanding": lambda db, org, filters: outstanding_rows(db, org),
    "expenses": lambda db, org, filters: expense_rows(db, org, filters.get("date_from"), filters.get("date_to")),
    "tax": lambda db, org, filters: tax_rows(db, org),
    "profit_loss": lambda db, org, filters: [profit_loss(db, org, filters.get("date_from"), filters.get("date_to"))],
    "profit-loss": lambda db, org, filters: [profit_loss(db, org, filters.get("date_from"), filters.get("date_to"))],
}
