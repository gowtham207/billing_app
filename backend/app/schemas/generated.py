"""Pydantic schemas generated from database/ddl.sql. Do not edit by hand."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from app.schemas.base import AppSchema

class OrganizationRead(AppSchema):
    id: uuid.UUID
    code: str
    legal_name: str
    display_name: str
    email: str | None
    phone: str | None
    website: str | None
    tax_registration_no: str | None
    default_currency: str
    timezone: str
    status: Literal['pending', 'active', 'suspended', 'archived']
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class OrganizationCreate(AppSchema):
    code: str
    legal_name: str
    display_name: str
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    tax_registration_no: str | None = None
    default_currency: str | None = None
    timezone: str | None = None
    status: Literal['pending', 'active', 'suspended', 'archived'] | None = None


class OrganizationUpdate(AppSchema):
    code: str | None = None
    legal_name: str | None = None
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    tax_registration_no: str | None = None
    default_currency: str | None = None
    timezone: str | None = None
    status: Literal['pending', 'active', 'suspended', 'archived'] | None = None


class OrganizationAddressRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    address_type: Literal['registered', 'billing', 'shipping', 'other']
    line1: str
    line2: str | None
    city: str | None
    state_region: str | None
    postal_code: str | None
    country_code: str
    is_default: bool
    created_at: datetime


class OrganizationAddressCreate(AppSchema):
    address_type: Literal['registered', 'billing', 'shipping', 'other']
    line1: str
    line2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postal_code: str | None = None
    country_code: str
    is_default: bool | None = None


class OrganizationAddressUpdate(AppSchema):
    address_type: Literal['registered', 'billing', 'shipping', 'other'] | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    is_default: bool | None = None


class BranchRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    name: str
    email: str | None
    phone: str | None
    timezone: str | None
    is_head_office: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BranchCreate(AppSchema):
    code: str
    name: str
    email: str | None = None
    phone: str | None = None
    timezone: str | None = None
    is_head_office: bool | None = None
    is_active: bool | None = None


class BranchUpdate(AppSchema):
    code: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    timezone: str | None = None
    is_head_office: bool | None = None
    is_active: bool | None = None


class UserRead(AppSchema):
    id: uuid.UUID
    email: str
    normalized_email: str | None
    full_name: str
    phone: str | None
    is_platform_admin: bool
    is_active: bool
    email_verified_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserCreate(AppSchema):
    email: str
    full_name: str
    phone: str | None = None
    is_active: bool | None = None


class UserUpdate(AppSchema):
    email: str | None = None
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class OrganizationMemberRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    member_status: Literal['invited', 'active', 'disabled', 'removed']
    joined_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OrganizationMemberCreate(AppSchema):
    user_id: uuid.UUID
    member_status: Literal['invited', 'active', 'disabled', 'removed'] | None = None
    joined_at: datetime | None = None


class OrganizationMemberUpdate(AppSchema):
    user_id: uuid.UUID | None = None
    member_status: Literal['invited', 'active', 'disabled', 'removed'] | None = None
    joined_at: datetime | None = None


class RoleRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    role_key: str
    name: str
    description: str | None
    is_system: bool
    created_at: datetime


class RoleCreate(AppSchema):
    role_key: str
    name: str
    description: str | None = None
    is_system: bool | None = None


class RoleUpdate(AppSchema):
    role_key: str | None = None
    name: str | None = None
    description: str | None = None
    is_system: bool | None = None


class PermissionRead(AppSchema):
    id: uuid.UUID
    permission_key: str
    module_key: str
    description: str | None


class PermissionCreate(AppSchema):
    permission_key: str
    module_key: str
    description: str | None = None


class PermissionUpdate(AppSchema):
    permission_key: str | None = None
    module_key: str | None = None
    description: str | None = None


class RolePermissionRead(AppSchema):
    organization_id: uuid.UUID
    role_id: uuid.UUID
    permission_id: uuid.UUID


class RolePermissionCreate(AppSchema):
    role_id: uuid.UUID
    permission_id: uuid.UUID


class RolePermissionUpdate(AppSchema):
    role_id: uuid.UUID | None = None
    permission_id: uuid.UUID | None = None


class MemberRoleRead(AppSchema):
    organization_id: uuid.UUID
    member_id: uuid.UUID
    role_id: uuid.UUID
    assigned_by: uuid.UUID | None
    assigned_at: datetime


class MemberRoleCreate(AppSchema):
    member_id: uuid.UUID
    role_id: uuid.UUID
    assigned_by: uuid.UUID | None = None
    assigned_at: datetime | None = None


class MemberRoleUpdate(AppSchema):
    member_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    assigned_by: uuid.UUID | None = None
    assigned_at: datetime | None = None


class MemberBranchRead(AppSchema):
    organization_id: uuid.UUID
    member_id: uuid.UUID
    branch_id: uuid.UUID


class MemberBranchCreate(AppSchema):
    member_id: uuid.UUID
    branch_id: uuid.UUID


class MemberBranchUpdate(AppSchema):
    member_id: uuid.UUID | None = None
    branch_id: uuid.UUID | None = None


class ModuleRead(AppSchema):
    id: uuid.UUID
    module_key: str
    name: str
    description: str | None
    is_active: bool


class ModuleCreate(AppSchema):
    module_key: str
    name: str
    description: str | None = None
    is_active: bool | None = None


class ModuleUpdate(AppSchema):
    module_key: str | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SubscriptionPlanRead(AppSchema):
    id: uuid.UUID
    plan_code: str
    name: str
    description: str | None
    billing_interval: Literal['monthly', 'quarterly', 'yearly', 'custom']
    price: Decimal
    currency: str
    max_members: int | None
    max_branches: int | None
    is_active: bool
    created_at: datetime


class SubscriptionPlanCreate(AppSchema):
    plan_code: str
    name: str
    description: str | None = None
    billing_interval: Literal['monthly', 'quarterly', 'yearly', 'custom']
    price: Decimal | None = None
    currency: str | None = None
    max_members: int | None = None
    max_branches: int | None = None
    is_active: bool | None = None


class SubscriptionPlanUpdate(AppSchema):
    plan_code: str | None = None
    name: str | None = None
    description: str | None = None
    billing_interval: Literal['monthly', 'quarterly', 'yearly', 'custom'] | None = None
    price: Decimal | None = None
    currency: str | None = None
    max_members: int | None = None
    max_branches: int | None = None
    is_active: bool | None = None


class PlanModuleRead(AppSchema):
    plan_id: uuid.UUID
    module_id: uuid.UUID


class PlanModuleCreate(AppSchema):
    plan_id: uuid.UUID
    module_id: uuid.UUID


class PlanModuleUpdate(AppSchema):
    plan_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None


class OrganizationSubscriptionRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    plan_id: uuid.UUID
    subscription_status: Literal['trialing', 'active', 'past_due', 'suspended', 'cancelled', 'expired']
    starts_at: datetime
    ends_at: datetime | None
    trial_ends_at: datetime | None
    auto_renew: bool
    created_at: datetime
    updated_at: datetime


class OrganizationSubscriptionCreate(AppSchema):
    plan_id: uuid.UUID
    subscription_status: Literal['trialing', 'active', 'past_due', 'suspended', 'cancelled', 'expired']
    starts_at: datetime
    ends_at: datetime | None = None
    trial_ends_at: datetime | None = None
    auto_renew: bool | None = None


class OrganizationSubscriptionUpdate(AppSchema):
    plan_id: uuid.UUID | None = None
    subscription_status: Literal['trialing', 'active', 'past_due', 'suspended', 'cancelled', 'expired'] | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    trial_ends_at: datetime | None = None
    auto_renew: bool | None = None


class OrganizationModuleOverrideRead(AppSchema):
    organization_id: uuid.UUID
    module_id: uuid.UUID
    is_enabled: bool
    reason: str | None
    expires_at: datetime | None
    updated_at: datetime


class OrganizationModuleOverrideCreate(AppSchema):
    module_id: uuid.UUID
    is_enabled: bool
    reason: str | None = None
    expires_at: datetime | None = None


class OrganizationModuleOverrideUpdate(AppSchema):
    module_id: uuid.UUID | None = None
    is_enabled: bool | None = None
    reason: str | None = None
    expires_at: datetime | None = None


class SubscriptionPaymentRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    subscription_id: uuid.UUID
    amount: Decimal
    currency: str
    payment_status: Literal['pending', 'paid', 'failed', 'refunded']
    provider: str | None
    provider_reference: str | None
    paid_at: datetime | None
    created_at: datetime


class SubscriptionPaymentCreate(AppSchema):
    subscription_id: uuid.UUID
    amount: Decimal
    currency: str
    payment_status: Literal['pending', 'paid', 'failed', 'refunded']
    provider: str | None = None
    provider_reference: str | None = None
    paid_at: datetime | None = None


class SubscriptionPaymentUpdate(AppSchema):
    subscription_id: uuid.UUID | None = None
    amount: Decimal | None = None
    currency: str | None = None
    payment_status: Literal['pending', 'paid', 'failed', 'refunded'] | None = None
    provider: str | None = None
    provider_reference: str | None = None
    paid_at: datetime | None = None


class StatusGroupRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    module_key: str
    entity_key: str
    name: str
    is_active: bool


class StatusGroupCreate(AppSchema):
    module_key: str
    entity_key: str
    name: str
    is_active: bool | None = None


class StatusGroupUpdate(AppSchema):
    module_key: str | None = None
    entity_key: str | None = None
    name: str | None = None
    is_active: bool | None = None


class StatusDefinitionRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    status_group_id: uuid.UUID
    status_key: str
    label: str
    sort_order: int
    is_initial: bool
    is_final: bool
    color: str | None
    is_active: bool


class StatusDefinitionCreate(AppSchema):
    status_group_id: uuid.UUID
    status_key: str
    label: str
    sort_order: int | None = None
    is_initial: bool | None = None
    is_final: bool | None = None
    color: str | None = None
    is_active: bool | None = None


class StatusDefinitionUpdate(AppSchema):
    status_group_id: uuid.UUID | None = None
    status_key: str | None = None
    label: str | None = None
    sort_order: int | None = None
    is_initial: bool | None = None
    is_final: bool | None = None
    color: str | None = None
    is_active: bool | None = None


class StatusTransitionRead(AppSchema):
    organization_id: uuid.UUID
    status_group_id: uuid.UUID
    from_status_id: uuid.UUID
    to_status_id: uuid.UUID
    requires_permission: str | None
    is_active: bool


class StatusTransitionCreate(AppSchema):
    status_group_id: uuid.UUID
    from_status_id: uuid.UUID
    to_status_id: uuid.UUID
    requires_permission: str | None = None
    is_active: bool | None = None


class StatusTransitionUpdate(AppSchema):
    status_group_id: uuid.UUID | None = None
    from_status_id: uuid.UUID | None = None
    to_status_id: uuid.UUID | None = None
    requires_permission: str | None = None
    is_active: bool | None = None


class WorkflowDefinitionRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    workflow_key: str
    name: str
    module_key: str
    is_active: bool
    created_at: datetime


class WorkflowDefinitionCreate(AppSchema):
    workflow_key: str
    name: str
    module_key: str
    is_active: bool | None = None


class WorkflowDefinitionUpdate(AppSchema):
    workflow_key: str | None = None
    name: str | None = None
    module_key: str | None = None
    is_active: bool | None = None


class WorkflowStepRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    workflow_id: uuid.UUID
    status_id: uuid.UUID
    step_order: int
    is_required: bool


class WorkflowStepCreate(AppSchema):
    workflow_id: uuid.UUID
    status_id: uuid.UUID
    step_order: int
    is_required: bool | None = None


class WorkflowStepUpdate(AppSchema):
    workflow_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    step_order: int | None = None
    is_required: bool | None = None


class StatusHistoryRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    module_key: str
    entity_type: str
    entity_id: uuid.UUID
    from_status_id: uuid.UUID | None
    to_status_id: uuid.UUID
    changed_by: uuid.UUID | None
    remarks: str | None
    changed_at: datetime


class StatusHistoryCreate(AppSchema):
    module_key: str
    entity_type: str
    entity_id: uuid.UUID
    from_status_id: uuid.UUID | None = None
    to_status_id: uuid.UUID
    changed_by: uuid.UUID | None = None
    remarks: str | None = None
    changed_at: datetime | None = None


class StatusHistoryUpdate(AppSchema):
    module_key: str | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    from_status_id: uuid.UUID | None = None
    to_status_id: uuid.UUID | None = None
    changed_by: uuid.UUID | None = None
    remarks: str | None = None
    changed_at: datetime | None = None


class CustomerSourceRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class CustomerSourceCreate(AppSchema):
    name: str


class CustomerSourceUpdate(AppSchema):
    name: str | None = None


class CustomerRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_code: str
    customer_type: Literal['individual', 'business']
    display_name: str
    legal_name: str | None
    email: str | None
    phone: str | None
    tax_registration_no: str | None
    source_id: uuid.UUID | None
    credit_limit: Decimal
    opening_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerCreate(AppSchema):
    customer_code: str
    customer_type: Literal['individual', 'business'] | None = None
    display_name: str
    legal_name: str | None = None
    email: str | None = None
    phone: str | None = None
    tax_registration_no: str | None = None
    source_id: uuid.UUID | None = None
    credit_limit: Decimal | None = None
    opening_balance: Decimal | None = None
    is_active: bool | None = None


class CustomerUpdate(AppSchema):
    customer_code: str | None = None
    customer_type: Literal['individual', 'business'] | None = None
    display_name: str | None = None
    legal_name: str | None = None
    email: str | None = None
    phone: str | None = None
    tax_registration_no: str | None = None
    source_id: uuid.UUID | None = None
    credit_limit: Decimal | None = None
    opening_balance: Decimal | None = None
    is_active: bool | None = None


class CustomerContactRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    name: str
    designation: str | None
    email: str | None
    phone: str | None
    is_primary: bool


class CustomerContactCreate(AppSchema):
    customer_id: uuid.UUID
    name: str
    designation: str | None = None
    email: str | None = None
    phone: str | None = None
    is_primary: bool | None = None


class CustomerContactUpdate(AppSchema):
    customer_id: uuid.UUID | None = None
    name: str | None = None
    designation: str | None = None
    email: str | None = None
    phone: str | None = None
    is_primary: bool | None = None


class CustomerAddressRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    address_type: Literal['billing', 'shipping', 'other']
    line1: str
    line2: str | None
    city: str | None
    state_region: str | None
    postal_code: str | None
    country_code: str
    is_default: bool


class CustomerAddressCreate(AppSchema):
    customer_id: uuid.UUID
    address_type: Literal['billing', 'shipping', 'other']
    line1: str
    line2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postal_code: str | None = None
    country_code: str
    is_default: bool | None = None


class CustomerAddressUpdate(AppSchema):
    customer_id: uuid.UUID | None = None
    address_type: Literal['billing', 'shipping', 'other'] | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    is_default: bool | None = None


class LeadSourceRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class LeadSourceCreate(AppSchema):
    name: str


class LeadSourceUpdate(AppSchema):
    name: str | None = None


class LeadRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    lead_code: str
    company_name: str | None
    contact_name: str
    email: str | None
    phone: str | None
    source_id: uuid.UUID | None
    status_id: uuid.UUID | None
    estimated_value: Decimal | None
    assigned_to: uuid.UUID | None
    converted_customer_id: uuid.UUID | None
    lost_reason: str | None
    created_at: datetime
    updated_at: datetime


class LeadCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    lead_code: str
    company_name: str | None = None
    contact_name: str
    email: str | None = None
    phone: str | None = None
    source_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    estimated_value: Decimal | None = None
    assigned_to: uuid.UUID | None = None
    converted_customer_id: uuid.UUID | None = None
    lost_reason: str | None = None


class LeadUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    lead_code: str | None = None
    company_name: str | None = None
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    source_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    estimated_value: Decimal | None = None
    assigned_to: uuid.UUID | None = None
    converted_customer_id: uuid.UUID | None = None
    lost_reason: str | None = None


class OpportunityRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID | None
    lead_id: uuid.UUID | None
    opportunity_code: str
    title: str
    stage_id: uuid.UUID | None
    expected_value: Decimal
    probability: Decimal | None
    expected_close_date: date | None
    owner_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class OpportunityCreate(AppSchema):
    customer_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    opportunity_code: str
    title: str
    stage_id: uuid.UUID | None = None
    expected_value: Decimal | None = None
    probability: Decimal | None = None
    expected_close_date: date | None = None
    owner_user_id: uuid.UUID | None = None


class OpportunityUpdate(AppSchema):
    customer_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    opportunity_code: str | None = None
    title: str | None = None
    stage_id: uuid.UUID | None = None
    expected_value: Decimal | None = None
    probability: Decimal | None = None
    expected_close_date: date | None = None
    owner_user_id: uuid.UUID | None = None


class ActivityRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    activity_type: Literal['call', 'email', 'meeting', 'task', 'note', 'other']
    subject: str
    description: str | None
    customer_id: uuid.UUID | None
    lead_id: uuid.UUID | None
    opportunity_id: uuid.UUID | None
    assigned_to: uuid.UUID | None
    due_at: datetime | None
    completed_at: datetime | None
    created_by: uuid.UUID | None
    created_at: datetime


class ActivityCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    activity_type: Literal['call', 'email', 'meeting', 'task', 'note', 'other']
    subject: str
    description: str | None = None
    customer_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    opportunity_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: uuid.UUID | None = None


class ActivityUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    activity_type: Literal['call', 'email', 'meeting', 'task', 'note', 'other'] | None = None
    subject: str | None = None
    description: str | None = None
    customer_id: uuid.UUID | None = None
    lead_id: uuid.UUID | None = None
    opportunity_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: uuid.UUID | None = None


class CustomerNoteRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    note: str
    created_by: uuid.UUID | None
    created_at: datetime


class CustomerNoteCreate(AppSchema):
    customer_id: uuid.UUID
    note: str
    created_by: uuid.UUID | None = None


class CustomerNoteUpdate(AppSchema):
    customer_id: uuid.UUID | None = None
    note: str | None = None
    created_by: uuid.UUID | None = None


class TagRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class TagCreate(AppSchema):
    name: str


class TagUpdate(AppSchema):
    name: str | None = None


class CustomerTagRead(AppSchema):
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    tag_id: uuid.UUID


class CustomerTagCreate(AppSchema):
    customer_id: uuid.UUID
    tag_id: uuid.UUID


class CustomerTagUpdate(AppSchema):
    customer_id: uuid.UUID | None = None
    tag_id: uuid.UUID | None = None


class UnitRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    symbol: str
    decimal_places: int


class UnitCreate(AppSchema):
    name: str
    symbol: str
    decimal_places: int | None = None


class UnitUpdate(AppSchema):
    name: str | None = None
    symbol: str | None = None
    decimal_places: int | None = None


class ProductCategoryRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    description: str | None
    is_active: bool


class ProductCategoryCreate(AppSchema):
    parent_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    is_active: bool | None = None


class ProductCategoryUpdate(AppSchema):
    parent_id: uuid.UUID | None = None
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class BrandRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class BrandCreate(AppSchema):
    name: str


class BrandUpdate(AppSchema):
    name: str | None = None


class ProductRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    category_id: uuid.UUID | None
    brand_id: uuid.UUID | None
    unit_id: uuid.UUID
    product_type: Literal['stock', 'service', 'non_stock']
    sku: str
    barcode: str | None
    name: str
    description: str | None
    purchase_price: Decimal
    selling_price: Decimal
    reorder_level: Decimal
    track_inventory: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductCreate(AppSchema):
    category_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None
    unit_id: uuid.UUID
    product_type: Literal['stock', 'service', 'non_stock'] | None = None
    sku: str
    barcode: str | None = None
    name: str
    description: str | None = None
    purchase_price: Decimal | None = None
    selling_price: Decimal | None = None
    reorder_level: Decimal | None = None
    track_inventory: bool | None = None
    is_active: bool | None = None


class ProductUpdate(AppSchema):
    category_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None
    unit_id: uuid.UUID | None = None
    product_type: Literal['stock', 'service', 'non_stock'] | None = None
    sku: str | None = None
    barcode: str | None = None
    name: str | None = None
    description: str | None = None
    purchase_price: Decimal | None = None
    selling_price: Decimal | None = None
    reorder_level: Decimal | None = None
    track_inventory: bool | None = None
    is_active: bool | None = None


class ProductVariantRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    product_id: uuid.UUID
    variant_sku: str
    variant_name: str
    attributes: Any
    barcode: str | None
    selling_price: Decimal | None
    is_active: bool


class ProductVariantCreate(AppSchema):
    product_id: uuid.UUID
    variant_sku: str
    variant_name: str
    attributes: Any | None = None
    barcode: str | None = None
    selling_price: Decimal | None = None
    is_active: bool | None = None


class ProductVariantUpdate(AppSchema):
    product_id: uuid.UUID | None = None
    variant_sku: str | None = None
    variant_name: str | None = None
    attributes: Any | None = None
    barcode: str | None = None
    selling_price: Decimal | None = None
    is_active: bool | None = None


class SupplierRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    supplier_code: str
    name: str
    email: str | None
    phone: str | None
    tax_registration_no: str | None
    opening_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SupplierCreate(AppSchema):
    supplier_code: str
    name: str
    email: str | None = None
    phone: str | None = None
    tax_registration_no: str | None = None
    opening_balance: Decimal | None = None
    is_active: bool | None = None


class SupplierUpdate(AppSchema):
    supplier_code: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    tax_registration_no: str | None = None
    opening_balance: Decimal | None = None
    is_active: bool | None = None


class SupplierAddressRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    supplier_id: uuid.UUID
    address_type: Literal['billing', 'shipping', 'other']
    line1: str
    line2: str | None
    city: str | None
    state_region: str | None
    postal_code: str | None
    country_code: str


class SupplierAddressCreate(AppSchema):
    supplier_id: uuid.UUID
    address_type: Literal['billing', 'shipping', 'other']
    line1: str
    line2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postal_code: str | None = None
    country_code: str


class SupplierAddressUpdate(AppSchema):
    supplier_id: uuid.UUID | None = None
    address_type: Literal['billing', 'shipping', 'other'] | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state_region: str | None = None
    postal_code: str | None = None
    country_code: str | None = None


class WarehouseRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    code: str
    name: str
    address: str | None
    is_active: bool
    created_at: datetime


class WarehouseCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    code: str
    name: str
    address: str | None = None
    is_active: bool | None = None


class WarehouseUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    code: str | None = None
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None


class StockBalanceRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal | None
    average_cost: Decimal
    updated_at: datetime


class StockBalanceCreate(AppSchema):
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity_on_hand: Decimal | None = None
    quantity_reserved: Decimal | None = None
    average_cost: Decimal | None = None


class StockBalanceUpdate(AppSchema):
    warehouse_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    quantity_on_hand: Decimal | None = None
    quantity_reserved: Decimal | None = None
    average_cost: Decimal | None = None


class StockMovementRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    movement_type: Literal['opening', 'purchase_receipt', 'sale', 'sales_return', 'purchase_return', 'adjustment', 'transfer_in', 'transfer_out']
    quantity_delta: Decimal
    unit_cost: Decimal
    source_type: str | None
    source_id: uuid.UUID | None
    occurred_at: datetime
    created_by: uuid.UUID | None
    notes: str | None


class StockMovementCreate(AppSchema):
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    movement_type: Literal['opening', 'purchase_receipt', 'sale', 'sales_return', 'purchase_return', 'adjustment', 'transfer_in', 'transfer_out']
    quantity_delta: Decimal
    unit_cost: Decimal | None = None
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    occurred_at: datetime | None = None
    created_by: uuid.UUID | None = None
    notes: str | None = None


class StockMovementUpdate(AppSchema):
    warehouse_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    movement_type: Literal['opening', 'purchase_receipt', 'sale', 'sales_return', 'purchase_return', 'adjustment', 'transfer_in', 'transfer_out'] | None = None
    quantity_delta: Decimal | None = None
    unit_cost: Decimal | None = None
    source_type: str | None = None
    source_id: uuid.UUID | None = None
    occurred_at: datetime | None = None
    created_by: uuid.UUID | None = None
    notes: str | None = None


class StockAdjustmentRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    warehouse_id: uuid.UUID
    adjustment_no: str
    status_id: uuid.UUID | None
    reason: str | None
    adjusted_at: datetime
    created_by: uuid.UUID | None


class StockAdjustmentCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    warehouse_id: uuid.UUID
    adjustment_no: str
    status_id: uuid.UUID | None = None
    reason: str | None = None
    adjusted_at: datetime | None = None
    created_by: uuid.UUID | None = None


class StockAdjustmentUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    warehouse_id: uuid.UUID | None = None
    adjustment_no: str | None = None
    status_id: uuid.UUID | None = None
    reason: str | None = None
    adjusted_at: datetime | None = None
    created_by: uuid.UUID | None = None


class StockAdjustmentItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    adjustment_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    counted_quantity: Decimal
    system_quantity: Decimal
    reason: str | None


class StockAdjustmentItemCreate(AppSchema):
    adjustment_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    counted_quantity: Decimal
    system_quantity: Decimal
    reason: str | None = None


class StockAdjustmentItemUpdate(AppSchema):
    adjustment_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    counted_quantity: Decimal | None = None
    system_quantity: Decimal | None = None
    reason: str | None = None


class StockTransferRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    transfer_no: str
    from_warehouse_id: uuid.UUID
    to_warehouse_id: uuid.UUID
    status_id: uuid.UUID | None
    requested_at: datetime
    completed_at: datetime | None
    created_by: uuid.UUID | None


class StockTransferCreate(AppSchema):
    transfer_no: str
    from_warehouse_id: uuid.UUID
    to_warehouse_id: uuid.UUID
    status_id: uuid.UUID | None = None
    requested_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: uuid.UUID | None = None


class StockTransferUpdate(AppSchema):
    transfer_no: str | None = None
    from_warehouse_id: uuid.UUID | None = None
    to_warehouse_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    requested_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: uuid.UUID | None = None


class StockTransferItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    transfer_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity: Decimal


class StockTransferItemCreate(AppSchema):
    transfer_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: Decimal


class StockTransferItemUpdate(AppSchema):
    transfer_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    quantity: Decimal | None = None


class PurchaseOrderRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    po_number: str
    order_date: date
    expected_date: date | None
    status_id: uuid.UUID | None
    currency: str
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    grand_total: Decimal
    notes: str | None
    created_by: uuid.UUID | None
    created_at: datetime


class PurchaseOrderCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    po_number: str
    order_date: date | None = None
    expected_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    discount_total: Decimal | None = None
    grand_total: Decimal | None = None
    notes: str | None = None
    created_by: uuid.UUID | None = None


class PurchaseOrderUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    warehouse_id: uuid.UUID | None = None
    po_number: str | None = None
    order_date: date | None = None
    expected_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    discount_total: Decimal | None = None
    grand_total: Decimal | None = None
    notes: str | None = None
    created_by: uuid.UUID | None = None


class PurchaseOrderItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    purchase_order_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    description: str | None
    quantity: Decimal
    received_quantity: Decimal
    unit_cost: Decimal
    tax_rate: Decimal
    line_total: Decimal


class PurchaseOrderItemCreate(AppSchema):
    purchase_order_id: uuid.UUID
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    description: str | None = None
    quantity: Decimal
    received_quantity: Decimal | None = None
    unit_cost: Decimal
    tax_rate: Decimal | None = None
    line_total: Decimal


class PurchaseOrderItemUpdate(AppSchema):
    purchase_order_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str | None = None
    quantity: Decimal | None = None
    received_quantity: Decimal | None = None
    unit_cost: Decimal | None = None
    tax_rate: Decimal | None = None
    line_total: Decimal | None = None


class GoodsReceiptRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    purchase_order_id: uuid.UUID | None
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    receipt_no: str
    received_at: datetime
    status_id: uuid.UUID | None
    received_by: uuid.UUID | None
    notes: str | None


class GoodsReceiptCreate(AppSchema):
    purchase_order_id: uuid.UUID | None = None
    supplier_id: uuid.UUID
    warehouse_id: uuid.UUID
    receipt_no: str
    received_at: datetime | None = None
    status_id: uuid.UUID | None = None
    received_by: uuid.UUID | None = None
    notes: str | None = None


class GoodsReceiptUpdate(AppSchema):
    purchase_order_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    warehouse_id: uuid.UUID | None = None
    receipt_no: str | None = None
    received_at: datetime | None = None
    status_id: uuid.UUID | None = None
    received_by: uuid.UUID | None = None
    notes: str | None = None


class GoodsReceiptItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    goods_receipt_id: uuid.UUID
    purchase_order_item_id: uuid.UUID | None
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity_received: Decimal
    unit_cost: Decimal


class GoodsReceiptItemCreate(AppSchema):
    goods_receipt_id: uuid.UUID
    purchase_order_item_id: uuid.UUID | None = None
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity_received: Decimal
    unit_cost: Decimal | None = None


class GoodsReceiptItemUpdate(AppSchema):
    goods_receipt_id: uuid.UUID | None = None
    purchase_order_item_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    quantity_received: Decimal | None = None
    unit_cost: Decimal | None = None


class BillingSettingsRead(AppSchema):
    organization_id: uuid.UUID
    default_currency: str
    tax_inclusive_pricing: bool
    allow_partial_payment: bool
    allow_overpayment: bool
    default_payment_terms_days: int
    default_due_days: int
    decimal_places: int
    rounding_method: Literal['half_up', 'half_even', 'up', 'down']
    updated_at: datetime


class BillingSettingsCreate(AppSchema):
    default_currency: str | None = None
    tax_inclusive_pricing: bool | None = None
    allow_partial_payment: bool | None = None
    allow_overpayment: bool | None = None
    default_payment_terms_days: int | None = None
    default_due_days: int | None = None
    decimal_places: int | None = None
    rounding_method: Literal['half_up', 'half_even', 'up', 'down'] | None = None


class BillingSettingsUpdate(AppSchema):
    default_currency: str | None = None
    tax_inclusive_pricing: bool | None = None
    allow_partial_payment: bool | None = None
    allow_overpayment: bool | None = None
    default_payment_terms_days: int | None = None
    default_due_days: int | None = None
    decimal_places: int | None = None
    rounding_method: Literal['half_up', 'half_even', 'up', 'down'] | None = None


class DocumentSequenceRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    document_type: str
    prefix: str
    suffix: str | None
    next_number: int
    padding: int
    reset_period: Literal['never', 'yearly', 'monthly']
    last_reset_key: str | None


class DocumentSequenceCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    document_type: str
    prefix: str
    suffix: str | None = None
    next_number: int | None = None
    padding: int | None = None
    reset_period: Literal['never', 'yearly', 'monthly'] | None = None
    last_reset_key: str | None = None


class DocumentSequenceUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    document_type: str | None = None
    prefix: str | None = None
    suffix: str | None = None
    next_number: int | None = None
    padding: int | None = None
    reset_period: Literal['never', 'yearly', 'monthly'] | None = None
    last_reset_key: str | None = None


class TaxRateRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    tax_code: str
    name: str
    rate: Decimal
    tax_type: Literal['percentage', 'fixed']
    is_compound: bool
    is_active: bool


class TaxRateCreate(AppSchema):
    tax_code: str
    name: str
    rate: Decimal
    tax_type: Literal['percentage', 'fixed'] | None = None
    is_compound: bool | None = None
    is_active: bool | None = None


class TaxRateUpdate(AppSchema):
    tax_code: str | None = None
    name: str | None = None
    rate: Decimal | None = None
    tax_type: Literal['percentage', 'fixed'] | None = None
    is_compound: bool | None = None
    is_active: bool | None = None


class TaxGroupRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class TaxGroupCreate(AppSchema):
    name: str


class TaxGroupUpdate(AppSchema):
    name: str | None = None


class TaxGroupRateRead(AppSchema):
    organization_id: uuid.UUID
    tax_group_id: uuid.UUID
    tax_rate_id: uuid.UUID
    sort_order: int


class TaxGroupRateCreate(AppSchema):
    tax_group_id: uuid.UUID
    tax_rate_id: uuid.UUID
    sort_order: int | None = None


class TaxGroupRateUpdate(AppSchema):
    tax_group_id: uuid.UUID | None = None
    tax_rate_id: uuid.UUID | None = None
    sort_order: int | None = None


class PaymentMethodRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    method_key: str
    display_name: str
    is_active: bool


class PaymentMethodCreate(AppSchema):
    method_key: str
    display_name: str
    is_active: bool | None = None


class PaymentMethodUpdate(AppSchema):
    method_key: str | None = None
    display_name: str | None = None
    is_active: bool | None = None


class InvoiceTemplateRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    template_config: Any
    is_default: bool
    created_at: datetime


class InvoiceTemplateCreate(AppSchema):
    name: str
    template_config: Any | None = None
    is_default: bool | None = None


class InvoiceTemplateUpdate(AppSchema):
    name: str | None = None
    template_config: Any | None = None
    is_default: bool | None = None


class QuotationRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    customer_id: uuid.UUID
    quotation_no: str
    quotation_date: date
    valid_until: date | None
    status_id: uuid.UUID | None
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    notes: str | None
    created_by: uuid.UUID | None
    created_at: datetime


class QuotationCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID
    quotation_no: str
    quotation_date: date | None = None
    valid_until: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    discount_total: Decimal | None = None
    tax_total: Decimal | None = None
    grand_total: Decimal | None = None
    notes: str | None = None
    created_by: uuid.UUID | None = None


class QuotationUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    quotation_no: str | None = None
    quotation_date: date | None = None
    valid_until: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    discount_total: Decimal | None = None
    tax_total: Decimal | None = None
    grand_total: Decimal | None = None
    notes: str | None = None
    created_by: uuid.UUID | None = None


class QuotationItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    quotation_id: uuid.UUID
    product_id: uuid.UUID | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    line_total: Decimal


class QuotationItemCreate(AppSchema):
    quotation_id: uuid.UUID
    product_id: uuid.UUID | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    line_total: Decimal


class QuotationItemUpdate(AppSchema):
    quotation_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    discount_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    line_total: Decimal | None = None


class SalesOrderRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    customer_id: uuid.UUID
    quotation_id: uuid.UUID | None
    order_no: str
    order_date: date
    status_id: uuid.UUID | None
    currency: str
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    grand_total: Decimal
    created_by: uuid.UUID | None
    created_at: datetime


class SalesOrderCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID
    quotation_id: uuid.UUID | None = None
    order_no: str
    order_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    discount_total: Decimal | None = None
    tax_total: Decimal | None = None
    grand_total: Decimal | None = None
    created_by: uuid.UUID | None = None


class SalesOrderUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    quotation_id: uuid.UUID | None = None
    order_no: str | None = None
    order_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    discount_total: Decimal | None = None
    tax_total: Decimal | None = None
    grand_total: Decimal | None = None
    created_by: uuid.UUID | None = None


class SalesOrderItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    sales_order_id: uuid.UUID
    product_id: uuid.UUID | None
    variant_id: uuid.UUID | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate: Decimal
    line_total: Decimal


class SalesOrderItemCreate(AppSchema):
    sales_order_id: uuid.UUID
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    line_total: Decimal


class SalesOrderItemUpdate(AppSchema):
    sales_order_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    discount_amount: Decimal | None = None
    tax_rate: Decimal | None = None
    line_total: Decimal | None = None


class SalesInvoiceRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    customer_id: uuid.UUID
    sales_order_id: uuid.UUID | None
    invoice_no: str
    invoice_date: date
    due_date: date | None
    status_id: uuid.UUID | None
    currency: str
    exchange_rate: Decimal
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    shipping_amount: Decimal
    grand_total: Decimal
    amount_paid: Decimal
    balance_due: Decimal | None
    billing_snapshot: Any
    notes: str | None
    issued_at: datetime | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class SalesInvoiceCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID
    sales_order_id: uuid.UUID | None = None
    invoice_no: str
    invoice_date: date | None = None
    due_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    exchange_rate: Decimal | None = None
    subtotal: Decimal | None = None
    discount_total: Decimal | None = None
    tax_total: Decimal | None = None
    shipping_amount: Decimal | None = None
    grand_total: Decimal | None = None
    amount_paid: Decimal | None = None
    billing_snapshot: Any | None = None
    notes: str | None = None
    issued_at: datetime | None = None
    created_by: uuid.UUID | None = None


class SalesInvoiceUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    sales_order_id: uuid.UUID | None = None
    invoice_no: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    exchange_rate: Decimal | None = None
    subtotal: Decimal | None = None
    discount_total: Decimal | None = None
    tax_total: Decimal | None = None
    shipping_amount: Decimal | None = None
    grand_total: Decimal | None = None
    amount_paid: Decimal | None = None
    billing_snapshot: Any | None = None
    notes: str | None = None
    issued_at: datetime | None = None
    created_by: uuid.UUID | None = None


class SalesInvoiceItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_id: uuid.UUID
    product_id: uuid.UUID | None
    variant_id: uuid.UUID | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    line_total: Decimal
    warehouse_id: uuid.UUID | None


class SalesInvoiceItemCreate(AppSchema):
    invoice_id: uuid.UUID
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    line_total: Decimal
    warehouse_id: uuid.UUID | None = None


class SalesInvoiceItemUpdate(AppSchema):
    invoice_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    discount_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    line_total: Decimal | None = None
    warehouse_id: uuid.UUID | None = None


class InvoiceItemTaxRead(AppSchema):
    organization_id: uuid.UUID
    invoice_item_id: uuid.UUID
    tax_rate_id: uuid.UUID
    taxable_amount: Decimal
    tax_amount: Decimal


class InvoiceItemTaxCreate(AppSchema):
    invoice_item_id: uuid.UUID
    tax_rate_id: uuid.UUID
    taxable_amount: Decimal
    tax_amount: Decimal


class InvoiceItemTaxUpdate(AppSchema):
    invoice_item_id: uuid.UUID | None = None
    tax_rate_id: uuid.UUID | None = None
    taxable_amount: Decimal | None = None
    tax_amount: Decimal | None = None


class PaymentRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    supplier_id: uuid.UUID | None
    payment_no: str
    payment_direction: Literal['in', 'out']
    payment_date: date
    amount: Decimal
    currency: str
    payment_method_id: uuid.UUID | None
    reference_no: str | None
    payment_status: Literal['pending', 'completed', 'failed', 'refunded', 'void']
    notes: str | None
    received_by: uuid.UUID | None
    created_at: datetime


class PaymentCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    payment_no: str
    payment_direction: Literal['in', 'out']
    payment_date: date | None = None
    amount: Decimal
    currency: str | None = None
    payment_method_id: uuid.UUID | None = None
    reference_no: str | None = None
    payment_status: Literal['pending', 'completed', 'failed', 'refunded', 'void'] | None = None
    notes: str | None = None
    received_by: uuid.UUID | None = None


class PaymentUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    payment_no: str | None = None
    payment_direction: Literal['in', 'out'] | None = None
    payment_date: date | None = None
    amount: Decimal | None = None
    currency: str | None = None
    payment_method_id: uuid.UUID | None = None
    reference_no: str | None = None
    payment_status: Literal['pending', 'completed', 'failed', 'refunded', 'void'] | None = None
    notes: str | None = None
    received_by: uuid.UUID | None = None


class InvoicePaymentRead(AppSchema):
    organization_id: uuid.UUID
    invoice_id: uuid.UUID
    payment_id: uuid.UUID
    amount_applied: Decimal


class InvoicePaymentCreate(AppSchema):
    invoice_id: uuid.UUID
    payment_id: uuid.UUID
    amount_applied: Decimal


class InvoicePaymentUpdate(AppSchema):
    invoice_id: uuid.UUID | None = None
    payment_id: uuid.UUID | None = None
    amount_applied: Decimal | None = None


class PurchaseInvoiceRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    supplier_id: uuid.UUID
    goods_receipt_id: uuid.UUID | None
    vendor_invoice_no: str | None
    purchase_invoice_no: str
    invoice_date: date
    due_date: date | None
    status_id: uuid.UUID | None
    currency: str
    subtotal: Decimal
    tax_total: Decimal
    grand_total: Decimal
    amount_paid: Decimal
    balance_due: Decimal | None
    created_at: datetime


class PurchaseInvoiceCreate(AppSchema):
    supplier_id: uuid.UUID
    goods_receipt_id: uuid.UUID | None = None
    vendor_invoice_no: str | None = None
    purchase_invoice_no: str
    invoice_date: date | None = None
    due_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    grand_total: Decimal | None = None
    amount_paid: Decimal | None = None


class PurchaseInvoiceUpdate(AppSchema):
    supplier_id: uuid.UUID | None = None
    goods_receipt_id: uuid.UUID | None = None
    vendor_invoice_no: str | None = None
    purchase_invoice_no: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    status_id: uuid.UUID | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    tax_total: Decimal | None = None
    grand_total: Decimal | None = None
    amount_paid: Decimal | None = None


class PurchaseInvoiceItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    purchase_invoice_id: uuid.UUID
    product_id: uuid.UUID | None
    description: str
    quantity: Decimal
    unit_cost: Decimal
    tax_amount: Decimal
    line_total: Decimal


class PurchaseInvoiceItemCreate(AppSchema):
    purchase_invoice_id: uuid.UUID
    product_id: uuid.UUID | None = None
    description: str
    quantity: Decimal
    unit_cost: Decimal
    tax_amount: Decimal | None = None
    line_total: Decimal


class PurchaseInvoiceItemUpdate(AppSchema):
    purchase_invoice_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit_cost: Decimal | None = None
    tax_amount: Decimal | None = None
    line_total: Decimal | None = None


class SupplierPaymentRead(AppSchema):
    organization_id: uuid.UUID
    purchase_invoice_id: uuid.UUID
    payment_id: uuid.UUID
    amount_applied: Decimal


class SupplierPaymentCreate(AppSchema):
    purchase_invoice_id: uuid.UUID
    payment_id: uuid.UUID
    amount_applied: Decimal


class SupplierPaymentUpdate(AppSchema):
    purchase_invoice_id: uuid.UUID | None = None
    payment_id: uuid.UUID | None = None
    amount_applied: Decimal | None = None


class SalesReturnRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    invoice_id: uuid.UUID
    return_no: str
    return_date: date
    warehouse_id: uuid.UUID
    status_id: uuid.UUID | None
    reason: str | None
    created_by: uuid.UUID | None
    created_at: datetime


class SalesReturnCreate(AppSchema):
    invoice_id: uuid.UUID
    return_no: str
    return_date: date | None = None
    warehouse_id: uuid.UUID
    status_id: uuid.UUID | None = None
    reason: str | None = None
    created_by: uuid.UUID | None = None


class SalesReturnUpdate(AppSchema):
    invoice_id: uuid.UUID | None = None
    return_no: str | None = None
    return_date: date | None = None
    warehouse_id: uuid.UUID | None = None
    status_id: uuid.UUID | None = None
    reason: str | None = None
    created_by: uuid.UUID | None = None


class SalesReturnItemRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    sales_return_id: uuid.UUID
    invoice_item_id: uuid.UUID | None
    product_id: uuid.UUID
    variant_id: uuid.UUID | None
    quantity: Decimal
    refund_amount: Decimal
    restock: bool


class SalesReturnItemCreate(AppSchema):
    sales_return_id: uuid.UUID
    invoice_item_id: uuid.UUID | None = None
    product_id: uuid.UUID
    variant_id: uuid.UUID | None = None
    quantity: Decimal
    refund_amount: Decimal | None = None
    restock: bool | None = None


class SalesReturnItemUpdate(AppSchema):
    sales_return_id: uuid.UUID | None = None
    invoice_item_id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None
    quantity: Decimal | None = None
    refund_amount: Decimal | None = None
    restock: bool | None = None


class CreditNoteRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID
    invoice_id: uuid.UUID | None
    credit_note_no: str
    issue_date: date
    amount: Decimal
    reason: str | None
    status_id: uuid.UUID | None
    created_at: datetime


class CreditNoteCreate(AppSchema):
    customer_id: uuid.UUID
    invoice_id: uuid.UUID | None = None
    credit_note_no: str
    issue_date: date | None = None
    amount: Decimal
    reason: str | None = None
    status_id: uuid.UUID | None = None


class CreditNoteUpdate(AppSchema):
    customer_id: uuid.UUID | None = None
    invoice_id: uuid.UUID | None = None
    credit_note_no: str | None = None
    issue_date: date | None = None
    amount: Decimal | None = None
    reason: str | None = None
    status_id: uuid.UUID | None = None


class ExpenseCategoryRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str


class ExpenseCategoryCreate(AppSchema):
    name: str


class ExpenseCategoryUpdate(AppSchema):
    name: str | None = None


class ExpenseRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    branch_id: uuid.UUID | None
    category_id: uuid.UUID
    expense_no: str
    expense_date: date
    amount: Decimal
    tax_amount: Decimal
    currency: str
    vendor_name: str | None
    description: str | None
    status_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime


class ExpenseCreate(AppSchema):
    branch_id: uuid.UUID | None = None
    category_id: uuid.UUID
    expense_no: str
    expense_date: date | None = None
    amount: Decimal
    tax_amount: Decimal | None = None
    currency: str | None = None
    vendor_name: str | None = None
    description: str | None = None
    status_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None


class ExpenseUpdate(AppSchema):
    branch_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    expense_no: str | None = None
    expense_date: date | None = None
    amount: Decimal | None = None
    tax_amount: Decimal | None = None
    currency: str | None = None
    vendor_name: str | None = None
    description: str | None = None
    status_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None


class DashboardRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    created_by: uuid.UUID | None
    created_at: datetime


class DashboardCreate(AppSchema):
    name: str
    description: str | None = None
    is_default: bool | None = None
    created_by: uuid.UUID | None = None


class DashboardUpdate(AppSchema):
    name: str | None = None
    description: str | None = None
    is_default: bool | None = None
    created_by: uuid.UUID | None = None


class ReportDefinitionRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    report_key: str
    name: str
    module_key: str
    description: str | None
    query_identifier: str
    default_config: Any
    is_active: bool


class ReportDefinitionCreate(AppSchema):
    report_key: str
    name: str
    module_key: str
    description: str | None = None
    query_identifier: str
    default_config: Any | None = None
    is_active: bool | None = None


class ReportDefinitionUpdate(AppSchema):
    report_key: str | None = None
    name: str | None = None
    module_key: str | None = None
    description: str | None = None
    query_identifier: str | None = None
    default_config: Any | None = None
    is_active: bool | None = None


class DashboardWidgetRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    dashboard_id: uuid.UUID
    report_id: uuid.UUID | None
    widget_key: str
    title: str
    widget_type: Literal['number', 'bar', 'line', 'pie', 'table', 'list']
    position_x: int
    position_y: int
    width_units: int
    height_units: int
    config: Any


class DashboardWidgetCreate(AppSchema):
    dashboard_id: uuid.UUID
    report_id: uuid.UUID | None = None
    widget_key: str
    title: str
    widget_type: Literal['number', 'bar', 'line', 'pie', 'table', 'list']
    position_x: int | None = None
    position_y: int | None = None
    width_units: int | None = None
    height_units: int | None = None
    config: Any | None = None


class DashboardWidgetUpdate(AppSchema):
    dashboard_id: uuid.UUID | None = None
    report_id: uuid.UUID | None = None
    widget_key: str | None = None
    title: str | None = None
    widget_type: Literal['number', 'bar', 'line', 'pie', 'table', 'list'] | None = None
    position_x: int | None = None
    position_y: int | None = None
    width_units: int | None = None
    height_units: int | None = None
    config: Any | None = None


class KpiDefinitionRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    kpi_key: str
    name: str
    description: str | None
    source_identifier: str
    aggregation: Literal['count', 'sum', 'avg', 'min', 'max', 'ratio']
    format_key: str
    config: Any
    is_active: bool


class KpiDefinitionCreate(AppSchema):
    kpi_key: str
    name: str
    description: str | None = None
    source_identifier: str
    aggregation: Literal['count', 'sum', 'avg', 'min', 'max', 'ratio']
    format_key: str | None = None
    config: Any | None = None
    is_active: bool | None = None


class KpiDefinitionUpdate(AppSchema):
    kpi_key: str | None = None
    name: str | None = None
    description: str | None = None
    source_identifier: str | None = None
    aggregation: Literal['count', 'sum', 'avg', 'min', 'max', 'ratio'] | None = None
    format_key: str | None = None
    config: Any | None = None
    is_active: bool | None = None


class AnalysisSettingsRead(AppSchema):
    organization_id: uuid.UUID
    default_date_range: str
    fiscal_year_start_month: int
    default_dashboard_id: uuid.UUID | None
    timezone: str
    updated_at: datetime


class AnalysisSettingsCreate(AppSchema):
    default_date_range: str | None = None
    fiscal_year_start_month: int | None = None
    default_dashboard_id: uuid.UUID | None = None
    timezone: str | None = None


class AnalysisSettingsUpdate(AppSchema):
    default_date_range: str | None = None
    fiscal_year_start_month: int | None = None
    default_dashboard_id: uuid.UUID | None = None
    timezone: str | None = None


class SavedReportRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    report_id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    filters: Any
    created_at: datetime


class SavedReportCreate(AppSchema):
    report_id: uuid.UUID
    owner_user_id: uuid.UUID
    name: str
    filters: Any | None = None


class SavedReportUpdate(AppSchema):
    report_id: uuid.UUID | None = None
    owner_user_id: uuid.UUID | None = None
    name: str | None = None
    filters: Any | None = None


class ReportScheduleRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    report_id: uuid.UUID
    created_by: uuid.UUID | None
    schedule_name: str
    cron_expression: str
    timezone: str
    output_format: Literal['pdf', 'xlsx', 'csv']
    recipients: Any
    is_active: bool
    next_run_at: datetime | None
    created_at: datetime


class ReportScheduleCreate(AppSchema):
    report_id: uuid.UUID
    created_by: uuid.UUID | None = None
    schedule_name: str
    cron_expression: str
    timezone: str | None = None
    output_format: Literal['pdf', 'xlsx', 'csv'] | None = None
    recipients: Any | None = None
    is_active: bool | None = None
    next_run_at: datetime | None = None


class ReportScheduleUpdate(AppSchema):
    report_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    schedule_name: str | None = None
    cron_expression: str | None = None
    timezone: str | None = None
    output_format: Literal['pdf', 'xlsx', 'csv'] | None = None
    recipients: Any | None = None
    is_active: bool | None = None
    next_run_at: datetime | None = None


class ReportAccessRead(AppSchema):
    organization_id: uuid.UUID
    report_id: uuid.UUID
    role_id: uuid.UUID


class ReportAccessCreate(AppSchema):
    report_id: uuid.UUID
    role_id: uuid.UUID


class ReportAccessUpdate(AppSchema):
    report_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None


class DashboardAccessRead(AppSchema):
    organization_id: uuid.UUID
    dashboard_id: uuid.UUID
    role_id: uuid.UUID


class DashboardAccessCreate(AppSchema):
    dashboard_id: uuid.UUID
    role_id: uuid.UUID


class DashboardAccessUpdate(AppSchema):
    dashboard_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None


class AuditLogRead(AppSchema):
    id: int
    organization_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    request_id: str | None
    ip_address: str | None
    user_agent: str | None
    before_data: Any | None
    after_data: Any | None
    created_at: datetime


class AuditLogCreate(AppSchema):
    actor_user_id: uuid.UUID | None = None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    before_data: Any | None = None
    after_data: Any | None = None


class AuditLogUpdate(AppSchema):
    actor_user_id: uuid.UUID | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    before_data: Any | None = None
    after_data: Any | None = None


class FileAttachmentRead(AppSchema):
    id: uuid.UUID
    organization_id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    storage_key: str
    original_filename: str
    content_type: str | None
    file_size_bytes: int | None
    uploaded_by: uuid.UUID | None
    created_at: datetime


class FileAttachmentCreate(AppSchema):
    entity_type: str
    entity_id: uuid.UUID
    storage_key: str
    original_filename: str
    content_type: str | None = None
    file_size_bytes: int | None = None
    uploaded_by: uuid.UUID | None = None


class FileAttachmentUpdate(AppSchema):
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    storage_key: str | None = None
    original_filename: str | None = None
    content_type: str | None = None
    file_size_bytes: int | None = None
    uploaded_by: uuid.UUID | None = None

