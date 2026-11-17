from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import Context, get_db, require_org
from app.models import AuditLog, Customer, Lead, Payment, Product, SalesInvoice, StatusHistory
from app.schemas.generated import PaymentRead, SalesInvoiceRead
from app.services.reports import expense_rows, grouped_chart, low_stock, money_float, overview, profit_loss, purchase_rows, sales_rows, top_customers, top_products

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _dump(model, rows):
    return [model.model_validate(row).model_dump(mode="json") for row in rows]


@router.get("/overview")
def dashboard_overview(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return overview(db, ctx.organization_id)


@router.get("/sales-summary")
def sales_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = sales_rows(db, ctx.organization_id)
    return {"count": len(rows), "total": sum(row["grand_total"] for row in rows)}


@router.get("/purchase-summary")
def purchase_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = purchase_rows(db, ctx.organization_id)
    return {"count": len(rows), "total": sum(row["grand_total"] for row in rows)}


@router.get("/revenue-summary")
def revenue_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return {"revenue": overview(db, ctx.organization_id)["revenue"]}


@router.get("/profit-summary")
def profit_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return profit_loss(db, ctx.organization_id)


@router.get("/expense-summary")
def expense_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = expense_rows(db, ctx.organization_id)
    return {"count": len(rows), "total": sum(row["amount"] for row in rows)}


@router.get("/customer-summary")
def customer_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    total = db.scalar(select(func.count()).select_from(Customer).where(Customer.organization_id == ctx.organization_id)) or 0
    return {"customers": total}


@router.get("/lead-summary")
def lead_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    total = db.scalar(select(func.count()).select_from(Lead).where(Lead.organization_id == ctx.organization_id)) or 0
    return {"leads": total}


@router.get("/inventory-summary")
def inventory_summary(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    total = db.scalar(select(func.count()).select_from(Product).where(Product.organization_id == ctx.organization_id, Product.is_active.is_(True))) or 0
    return {"products": total, "low_stock": len(low_stock(db, ctx.organization_id))}


@router.get("/low-stock")
def dashboard_low_stock(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return low_stock(db, ctx.organization_id)


@router.get("/top-selling-products")
def top_selling(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return top_products(db, ctx.organization_id)


@router.get("/top-customers")
def highest_customers(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return top_customers(db, ctx.organization_id)


@router.get("/recent-invoices")
def recent_invoices(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(
        select(SalesInvoice).where(SalesInvoice.organization_id == ctx.organization_id).order_by(SalesInvoice.created_at.desc()).limit(10)
    ).all()
    return _dump(SalesInvoiceRead, rows)


@router.get("/recent-payments")
def recent_payments(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(Payment).where(Payment.organization_id == ctx.organization_id).order_by(Payment.created_at.desc()).limit(10)).all()
    return _dump(PaymentRead, rows)


@router.get("/outstanding-payments")
def outstanding_payments(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    total = db.scalar(select(func.coalesce(func.sum(SalesInvoice.balance_due), 0)).where(SalesInvoice.organization_id == ctx.organization_id))
    count = db.scalar(
        select(func.count()).select_from(SalesInvoice).where(SalesInvoice.organization_id == ctx.organization_id, SalesInvoice.balance_due > 0)
    ) or 0
    return {"count": count, "outstanding": money_float(total)}


@router.get("/sales-chart")
def sales_chart(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return grouped_chart(db, SalesInvoice, SalesInvoice.grand_total, SalesInvoice.invoice_date, ctx.organization_id)


@router.get("/purchase-chart")
def purchase_chart(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    from app.models import PurchaseInvoice

    return grouped_chart(db, PurchaseInvoice, PurchaseInvoice.grand_total, PurchaseInvoice.invoice_date, ctx.organization_id)


@router.get("/cash-flow")
def cash_flow(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    inflow = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.organization_id == ctx.organization_id, Payment.payment_direction == "in")
    )
    outflow = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.organization_id == ctx.organization_id, Payment.payment_direction == "out")
    )
    return {"inflow": money_float(inflow), "outflow": money_float(outflow)}


@router.get("/activity-feed")
def activity_feed(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    history = db.scalars(
        select(StatusHistory).where(StatusHistory.organization_id == ctx.organization_id).order_by(StatusHistory.changed_at.desc()).limit(20)
    ).all()
    audits = db.scalars(
        select(AuditLog).where(AuditLog.organization_id == ctx.organization_id).order_by(AuditLog.created_at.desc()).limit(20)
    ).all()
    return {
        "status_changes": [
            {"entity_type": row.entity_type, "entity_id": row.entity_id, "changed_at": row.changed_at} for row in history
        ],
        "audit": [{"action": row.action, "entity_type": row.entity_type, "entity_id": row.entity_id, "created_at": row.created_at} for row in audits],
    }
