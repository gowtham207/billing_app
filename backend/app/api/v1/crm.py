import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.v1.mount import mount_collection, mount_item
from app.core.deps import Context, get_db, require_org, require_write
from app.models import (
    Activity,
    Customer,
    CustomerAddress,
    CustomerContact,
    CustomerNote,
    CustomerSource,
    CustomerTag,
    InvoicePayment,
    Lead,
    LeadSource,
    Opportunity,
    Payment,
    SalesInvoice,
    Tag,
)
from app.schemas.generated import (
    ActivityCreate,
    ActivityRead,
    ActivityUpdate,
    CustomerAddressCreate,
    CustomerAddressRead,
    CustomerAddressUpdate,
    CustomerContactCreate,
    CustomerContactRead,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerNoteCreate,
    CustomerNoteRead,
    CustomerRead,
    CustomerSourceCreate,
    CustomerSourceRead,
    CustomerUpdate,
    LeadCreate,
    LeadRead,
    LeadSourceCreate,
    LeadSourceRead,
    LeadUpdate,
    OpportunityCreate,
    OpportunityRead,
    OpportunityUpdate,
    TagCreate,
    TagRead,
    TagUpdate,
)
from app.schemas.requests import AssignRequest, IdList, StatusChange
from app.services.common import create_model, get_scoped, list_where, set_status
from app.services.documents import convert_lead

router = APIRouter(prefix="/crm")
P = "crm.write"


@router.get("/activities/my-tasks", tags=["CRM - Opportunities & Activities"])
def my_tasks(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return db.scalars(
        select(Activity).where(
            Activity.organization_id == ctx.organization_id,
            Activity.assigned_to == ctx.user.id,
            Activity.completed_at.is_(None),
        )
    ).all()


@router.get("/activities/upcoming", tags=["CRM - Opportunities & Activities"])
def upcoming(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return db.scalars(
        select(Activity)
        .where(Activity.organization_id == ctx.organization_id, Activity.completed_at.is_(None), Activity.due_at.is_not(None))
        .order_by(Activity.due_at)
    ).all()


mount_collection(router, name="customers", path="/customers", model=Customer, read=CustomerRead, create=CustomerCreate, tag="CRM - Customers", search=("display_name", "legal_name", "customer_code", "email", "phone", "tax_registration_no"), permission=P)
mount_item(router, name="customers", path="/customers", model=Customer, read=CustomerRead, update=CustomerUpdate, tag="CRM - Customers", permission=P)
mount_collection(router, name="lead_sources", path="/lead-sources", model=LeadSource, read=LeadSourceRead, create=LeadSourceCreate, tag="CRM - Leads", search=("name",), permission=P)
mount_collection(router, name="customer_sources", path="/customer-sources", model=CustomerSource, read=CustomerSourceRead, create=CustomerSourceCreate, tag="CRM - Leads", search=("name",), permission=P)
mount_collection(router, name="leads", path="/leads", model=Lead, read=LeadRead, create=LeadCreate, tag="CRM - Leads", search=("lead_code", "contact_name", "company_name", "email"), permission=P)
mount_item(router, name="leads", path="/leads", model=Lead, read=LeadRead, update=LeadUpdate, tag="CRM - Leads", permission=P)
mount_collection(router, name="opportunities", path="/opportunities", model=Opportunity, read=OpportunityRead, create=OpportunityCreate, tag="CRM - Opportunities & Activities", search=("title", "opportunity_code"), permission=P)
mount_item(router, name="opportunities", path="/opportunities", model=Opportunity, read=OpportunityRead, update=OpportunityUpdate, tag="CRM - Opportunities & Activities", permission=P)
mount_collection(router, name="activities", path="/activities", model=Activity, read=ActivityRead, create=ActivityCreate, tag="CRM - Opportunities & Activities", search=("subject",), permission=P)
mount_item(router, name="activities", path="/activities", model=Activity, read=ActivityRead, update=ActivityUpdate, tag="CRM - Opportunities & Activities", permission=P)
mount_collection(router, name="tags", path="/tags", model=Tag, read=TagRead, create=TagCreate, tag="CRM - Opportunities & Activities", search=("name",), permission=P)
mount_item(router, name="tags", path="/tags", model=Tag, read=TagRead, update=TagUpdate, tag="CRM - Opportunities & Activities", permission=P, can_get=False)


@router.get("/customers/{id}/contacts", response_model=list[CustomerContactRead], tags=["CRM - Customers"])
def list_contacts(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Customer, id, ctx.organization_id)
    return list_where(db, CustomerContact, ctx.organization_id, customer_id=id)


@router.post("/customers/{id}/contacts", response_model=CustomerContactRead, status_code=201, tags=["CRM - Customers"])
def add_contact(id: uuid.UUID, body: CustomerContactCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    get_scoped(db, Customer, id, ctx.organization_id)
    data = body.model_dump(exclude_unset=True)
    data.update(organization_id=ctx.organization_id, customer_id=id)
    return create_model(db, CustomerContact, data, ctx, "customer_contacts")


@router.put("/customers/{id}/contacts/{contact_id}", response_model=CustomerContactRead, tags=["CRM - Customers"])
def update_contact(id: uuid.UUID, contact_id: uuid.UUID, body: CustomerContactUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, CustomerContact, contact_id, ctx.organization_id)
    if row.customer_id != id:
        raise HTTPException(status_code=404, detail="Not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.delete("/customers/{id}/contacts/{contact_id}", status_code=204, tags=["CRM - Customers"])
def delete_contact(id: uuid.UUID, contact_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, CustomerContact, contact_id, ctx.organization_id)
    db.delete(row)
    db.flush()
    return None


@router.get("/customers/{id}/addresses", response_model=list[CustomerAddressRead], tags=["CRM - Customers"])
def list_addresses(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Customer, id, ctx.organization_id)
    return list_where(db, CustomerAddress, ctx.organization_id, customer_id=id)


@router.post("/customers/{id}/addresses", response_model=CustomerAddressRead, status_code=201, tags=["CRM - Customers"])
def add_address(id: uuid.UUID, body: CustomerAddressCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    get_scoped(db, Customer, id, ctx.organization_id)
    data = body.model_dump(exclude_unset=True)
    data.update(organization_id=ctx.organization_id, customer_id=id)
    return create_model(db, CustomerAddress, data, ctx, "customer_addresses")


@router.put("/customers/{id}/addresses/{address_id}", response_model=CustomerAddressRead, tags=["CRM - Customers"])
def update_address(id: uuid.UUID, address_id: uuid.UUID, body: CustomerAddressUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, CustomerAddress, address_id, ctx.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.get("/customers/{id}/notes", response_model=list[CustomerNoteRead], tags=["CRM - Customers"])
def list_notes(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Customer, id, ctx.organization_id)
    return list_where(db, CustomerNote, ctx.organization_id, customer_id=id)


@router.post("/customers/{id}/notes", response_model=CustomerNoteRead, status_code=201, tags=["CRM - Customers"])
def add_note(id: uuid.UUID, body: CustomerNoteCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    get_scoped(db, Customer, id, ctx.organization_id)
    data = body.model_dump(exclude_unset=True)
    data.update(organization_id=ctx.organization_id, customer_id=id, created_by=ctx.user.id)
    return create_model(db, CustomerNote, data, ctx, "customer_notes")


@router.get("/customers/{id}/tags", response_model=list[TagRead], tags=["CRM - Customers"])
def customer_tags(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Customer, id, ctx.organization_id)
    tag_ids = [row.tag_id for row in db.scalars(select(CustomerTag).where(CustomerTag.organization_id == ctx.organization_id, CustomerTag.customer_id == id)).all()]
    if not tag_ids:
        return []
    return db.scalars(select(Tag).where(Tag.id.in_(tag_ids))).all()


@router.put("/customers/{id}/tags", tags=["CRM - Customers"])
def assign_tags(id: uuid.UUID, body: IdList, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    get_scoped(db, Customer, id, ctx.organization_id)
    db.execute(delete(CustomerTag).where(CustomerTag.organization_id == ctx.organization_id, CustomerTag.customer_id == id))
    for tag_id in body.ids:
        db.add(CustomerTag(organization_id=ctx.organization_id, customer_id=id, tag_id=tag_id))
    db.flush()
    return {"customer_id": id, "tag_ids": body.ids}


@router.get("/customers/{id}/transactions", tags=["CRM - Customers"])
def customer_transactions(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Customer, id, ctx.organization_id)
    invoices = db.scalars(select(SalesInvoice).where(SalesInvoice.organization_id == ctx.organization_id, SalesInvoice.customer_id == id)).all()
    payments = db.scalars(select(Payment).where(Payment.organization_id == ctx.organization_id, Payment.customer_id == id)).all()
    return {"invoices": invoices, "payments": payments, "allocations": db.scalars(select(InvoicePayment).where(InvoicePayment.organization_id == ctx.organization_id)).all()}


@router.patch("/leads/{id}/status", response_model=LeadRead, tags=["CRM - Leads"])
def lead_status(id: uuid.UUID, body: StatusChange, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, Lead, id, ctx.organization_id), ctx=ctx, module_key="crm", entity_key="lead", status_key=body.status)


@router.patch("/leads/{id}/assign", response_model=LeadRead, tags=["CRM - Leads"])
def assign_lead(id: uuid.UUID, body: AssignRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    lead = get_scoped(db, Lead, id, ctx.organization_id)
    lead.assigned_to = body.user_id
    db.flush()
    db.refresh(lead)
    return lead


@router.post("/leads/{id}/convert", tags=["CRM - Leads"])
def convert(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    customer = convert_lead(db, ctx, get_scoped(db, Lead, id, ctx.organization_id))
    return CustomerRead.model_validate(customer)


@router.patch("/opportunities/{id}/stage", response_model=OpportunityRead, tags=["CRM - Opportunities & Activities"])
def change_stage(id: uuid.UUID, body: StatusChange, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, Opportunity, id, ctx.organization_id), ctx=ctx, module_key="crm", entity_key="opportunity", status_key=body.status)


@router.patch("/activities/{id}/complete", response_model=ActivityRead, tags=["CRM - Opportunities & Activities"])
def complete_activity(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, Activity, id, ctx.organization_id)
    row.completed_at = datetime.now(timezone.utc)
    db.flush()
    db.refresh(row)
    return row
