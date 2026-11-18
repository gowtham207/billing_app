from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=160)
    phone: str | None = None
    organization_name: str | None = None
    organization_code: str | None = Field(default=None, max_length=40)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class TokenVerifyRequest(BaseModel):
    token: str


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = None


class SwitchOrganizationRequest(BaseModel):
    organization_id: uuid.UUID


class OrganizationCreateRequest(BaseModel):
    legal_name: str
    display_name: str | None = None
    code: str | None = None
    email: str | None = None
    phone: str | None = None


class StatusChange(BaseModel):
    status: str


class InviteMember(BaseModel):
    email: EmailStr
    full_name: str | None = None


class IdList(BaseModel):
    ids: list[uuid.UUID]


class ModuleAssign(BaseModel):
    module_ids: list[uuid.UUID]


class OverrideRequest(BaseModel):
    module_id: uuid.UUID
    is_enabled: bool
    reason: str | None = None
    expires_at: date | None = None


class WorkflowStepIn(BaseModel):
    status_id: uuid.UUID
    step_order: int
    is_required: bool = True


class WorkflowStepsUpdate(BaseModel):
    steps: list[WorkflowStepIn]


class TransitionRequest(BaseModel):
    module_key: str
    entity_type: str
    entity_id: uuid.UUID
    to_status_id: uuid.UUID | None = None
    to_status_key: str | None = None
    remarks: str | None = None


class SaleLine(BaseModel):
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=0, ge=0)
    tax_rate: Decimal = Field(default=0, ge=0, le=100)
    tax_amount: Decimal = Field(default=0, ge=0)
    warehouse_id: uuid.UUID | None = None


class QuotationCreateRequest(BaseModel):
    customer_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    quotation_no: str | None = None
    quotation_date: date | None = None
    valid_until: date | None = None
    currency: str = "INR"
    notes: str | None = None
    items: list[SaleLine] = Field(min_length=1)


class SalesOrderCreateRequest(BaseModel):
    customer_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    quotation_id: uuid.UUID | None = None
    order_no: str | None = None
    order_date: date | None = None
    currency: str = "INR"
    notes: str | None = None
    items: list[SaleLine] = Field(min_length=1)


class InvoiceCreateBody(BaseModel):
    customer_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    sales_order_id: uuid.UUID | None = None
    invoice_no: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str = "INR"
    shipping_amount: Decimal = Field(default=0, ge=0)
    notes: str | None = None
    billing_snapshot: dict | None = None  # from, to, and bill_to are stored independently
    reopen: bool = False  # return a posted invoice to draft instead of keeping it issued
    items: list[SaleLine] = Field(min_length=1)


class PurchaseLine(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    description: str | None = None
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    tax_rate: Decimal = Field(default=0, ge=0, le=100)


class PurchaseOrderCreateRequest(BaseModel):
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    po_number: str | None = None
    order_date: date | None = None
    expected_date: date | None = None
    currency: str = "INR"
    notes: str | None = None
    items: list[PurchaseLine] = Field(min_length=1)


class ReceiptLine(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    purchase_order_item_id: uuid.UUID | None = None
    quantity_received: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=0, ge=0)


class GoodsReceiptCreateRequest(BaseModel):
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    purchase_order_id: uuid.UUID | None = None
    receipt_no: str | None = None
    notes: str | None = None
    items: list[ReceiptLine] = Field(min_length=1)


class BillLine(BaseModel):
    product_id: uuid.UUID | None = None
    description: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=0, ge=0)


class PurchaseInvoiceCreateRequest(BaseModel):
    supplier_id: uuid.UUID
    goods_receipt_id: uuid.UUID | None = None
    vendor_invoice_no: str | None = None
    purchase_invoice_no: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency: str = "INR"
    items: list[BillLine] = Field(min_length=1)


class PaymentCreateRequest(BaseModel):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    payment_no: str | None = None
    payment_date: date | None = None
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    payment_method_id: uuid.UUID | None = None
    reference_no: str | None = None
    notes: str | None = None


class AllocationIn(BaseModel):
    invoice_id: uuid.UUID
    amount: Decimal = Field(gt=0)


class AllocateInvoices(BaseModel):
    allocations: list[AllocationIn] = Field(min_length=1)


class SupplierAllocationIn(BaseModel):
    purchase_invoice_id: uuid.UUID
    amount: Decimal = Field(gt=0)


class AllocateBills(BaseModel):
    allocations: list[SupplierAllocationIn] = Field(min_length=1)


class OpeningLine(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=0, ge=0)


class OpeningStockRequest(BaseModel):
    warehouse_id: uuid.UUID
    lines: list[OpeningLine] = Field(min_length=1)


class AdjustmentLine(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    counted_quantity: Decimal = Field(ge=0)
    system_quantity: Decimal | None = None
    reason: str | None = None


class AdjustmentCreateRequest(BaseModel):
    warehouse_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    adjustment_no: str | None = None
    reason: str | None = None
    items: list[AdjustmentLine] = Field(min_length=1)


class TransferLine(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: Decimal = Field(gt=0)


class TransferCreateRequest(BaseModel):
    from_warehouse_id: uuid.UUID
    to_warehouse_id: uuid.UUID
    transfer_no: str | None = None
    items: list[TransferLine] = Field(min_length=1)


class ReturnLine(BaseModel):
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    invoice_item_id: uuid.UUID | None = None
    quantity: Decimal = Field(gt=0)
    refund_amount: Decimal = Field(default=0, ge=0)
    restock: bool = True


class ReturnCreateRequest(BaseModel):
    invoice_id: uuid.UUID
    warehouse_id: uuid.UUID
    return_no: str | None = None
    return_date: date | None = None
    reason: str | None = None
    items: list[ReturnLine] = Field(min_length=1)


class CreditNoteCreateRequest(BaseModel):
    customer_id: uuid.UUID
    invoice_id: uuid.UUID | None = None
    credit_note_no: str | None = None
    issue_date: date | None = None
    amount: Decimal = Field(gt=0)
    reason: str | None = None


class ExpenseCreateRequest(BaseModel):
    category_id: uuid.UUID
    branch_id: uuid.UUID | None = None
    expense_no: str | None = None
    expense_date: date | None = None
    amount: Decimal = Field(ge=0)
    tax_amount: Decimal = Field(default=0, ge=0)
    currency: str = "INR"
    vendor_name: str | None = None
    description: str | None = None


class TaxGroupCreateRequest(BaseModel):
    name: str
    tax_rate_ids: list[uuid.UUID] = []


class LayoutItem(BaseModel):
    id: uuid.UUID
    position_x: int = 0
    position_y: int = 0
    width_units: int = 4
    height_units: int = 3


class LayoutUpdate(BaseModel):
    widgets: list[LayoutItem]


class ReportExecuteRequest(BaseModel):
    report_id: uuid.UUID | None = None
    report_key: str | None = None
    filters: dict = {}


class SavedReportCreateRequest(BaseModel):
    report_id: uuid.UUID
    name: str
    filters: dict = {}


class AssignRequest(BaseModel):
    user_id: uuid.UUID
