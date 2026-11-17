from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AnalysisSettings,
    BillingSettings,
    DocumentSequence,
    PaymentMethod,
    StatusDefinition,
    StatusGroup,
    StatusTransition,
    TaxGroup,
    TaxGroupRate,
    TaxRate,
)

STATUS_SEEDS = {
    ("crm", "lead"): ["new", "qualified", "lost", "converted"],
    ("crm", "opportunity"): ["prospecting", "proposal", "won", "lost"],
    ("inventory", "stock_adjustment"): ["draft", "submitted", "approved", "posted"],
    ("inventory", "stock_transfer"): ["draft", "approved", "completed", "cancelled"],
    ("purchasing", "purchase_order"): ["draft", "submitted", "approved", "cancelled"],
    ("purchasing", "goods_receipt"): ["draft", "completed"],
    ("purchasing", "purchase_invoice"): ["draft", "posted"],
    ("billing", "quotation"): ["draft", "sent", "accepted", "rejected"],
    ("billing", "sales_order"): ["draft", "confirmed", "cancelled", "invoiced"],
    ("billing", "sales_invoice"): ["draft", "approved", "posted", "cancelled"],
    ("billing", "sales_return"): ["draft", "approved", "completed"],
    ("billing", "credit_note"): ["draft", "issued"],
    ("expenses", "expense"): ["draft", "submitted", "approved", "rejected", "paid"],
}

TRANSITIONS = {
    ("crm", "lead"): [("new", "qualified"), ("new", "lost"), ("qualified", "converted"), ("qualified", "lost")],
    ("crm", "opportunity"): [("prospecting", "proposal"), ("proposal", "won"), ("proposal", "lost")],
    ("inventory", "stock_adjustment"): [("draft", "submitted"), ("submitted", "approved"), ("approved", "posted")],
    ("inventory", "stock_transfer"): [("draft", "approved"), ("approved", "completed"), ("draft", "cancelled"), ("approved", "cancelled")],
    ("purchasing", "purchase_order"): [("draft", "submitted"), ("submitted", "approved"), ("draft", "cancelled"), ("submitted", "cancelled")],
    ("purchasing", "goods_receipt"): [("draft", "completed")],
    ("purchasing", "purchase_invoice"): [("draft", "posted")],
    ("billing", "quotation"): [("draft", "sent"), ("sent", "accepted"), ("sent", "rejected")],
    ("billing", "sales_order"): [("draft", "confirmed"), ("confirmed", "invoiced"), ("draft", "cancelled"), ("confirmed", "cancelled")],
    ("billing", "sales_invoice"): [("draft", "approved"), ("approved", "posted"), ("draft", "cancelled")],
    ("billing", "sales_return"): [("draft", "approved"), ("approved", "completed")],
    ("billing", "credit_note"): [("draft", "issued")],
    ("expenses", "expense"): [("draft", "submitted"), ("submitted", "approved"), ("submitted", "rejected"), ("approved", "paid")],
}

SEQUENCES = {
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
}

FINAL_KEYS = {"lost", "converted", "won", "posted", "completed", "cancelled", "rejected", "invoiced", "issued", "paid"}


def seed_organization(db: Session, organization_id) -> None:
    if db.get(BillingSettings, organization_id) is not None:
        return
    status_ids: dict[tuple[str, str, str], object] = {}
    for (module_key, entity_key), keys in STATUS_SEEDS.items():
        group = StatusGroup(
            organization_id=organization_id,
            module_key=module_key,
            entity_key=entity_key,
            name=entity_key.replace("_", " ").title(),
        )
        db.add(group)
        db.flush()
        for index, key in enumerate(keys):
            status = StatusDefinition(
                organization_id=organization_id,
                status_group_id=group.id,
                status_key=key,
                label=key.replace("_", " ").title(),
                sort_order=index,
                is_initial=index == 0,
                is_final=key in FINAL_KEYS,
            )
            db.add(status)
            db.flush()
            status_ids[(module_key, entity_key, key)] = status.id
        for source, target in TRANSITIONS.get((module_key, entity_key), []):
            db.add(
                StatusTransition(
                    organization_id=organization_id,
                    status_group_id=group.id,
                    from_status_id=status_ids[(module_key, entity_key, source)],
                    to_status_id=status_ids[(module_key, entity_key, target)],
                )
            )
    for key, name in (("cash", "Cash"), ("bank", "Bank transfer"), ("upi", "UPI")):
        db.add(PaymentMethod(organization_id=organization_id, method_key=key, display_name=name))
    for document_type, prefix in SEQUENCES.items():
        db.add(DocumentSequence(organization_id=organization_id, document_type=document_type, prefix=prefix))
    tax = TaxRate(organization_id=organization_id, tax_code="GST18", name="Sample GST 18%", rate=18)
    db.add(tax)
    db.flush()
    group = TaxGroup(organization_id=organization_id, name="GST")
    db.add(group)
    db.flush()
    db.add(TaxGroupRate(organization_id=organization_id, tax_group_id=group.id, tax_rate_id=tax.id, sort_order=1))
    db.add(BillingSettings(organization_id=organization_id))
    db.add(AnalysisSettings(organization_id=organization_id))
    db.flush()


def starter_plan_id(db: Session):
    from app.models import SubscriptionPlan

    return db.scalar(select(SubscriptionPlan.id).where(SubscriptionPlan.plan_code == "starter"))
