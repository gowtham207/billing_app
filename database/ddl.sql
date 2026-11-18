-- Multi-Organization CRM, Billing, Inventory & Analytics SaaS
-- PostgreSQL 14+
-- Run as a database owner in a new database.
-- Tenant-owned tables carry organization_id. Composite foreign keys prevent
-- cross-organization references. Set app.current_organization_id per transaction
-- in trusted server-side code before querying tenant data.
--
-- IMPORTANT:
-- 1) Do not trust organization_id supplied by clients.
-- 2) Enable RLS policies below only after the application sets the tenant context.
-- 3) Review tax/accounting rules for each jurisdiction before production use.

BEGIN;

CREATE SCHEMA IF NOT EXISTS app;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
SET search_path TO app, public;

-- ---------- Common utility ----------
CREATE OR REPLACE FUNCTION app.set_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION app.current_org_id()
RETURNS uuid LANGUAGE sql STABLE AS $$
    SELECT NULLIF(current_setting('app.current_organization_id', true), '')::uuid
$$;

-- ---------- Platform / organization core ----------
CREATE TABLE app.organizations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(40) NOT NULL UNIQUE,
    legal_name varchar(200) NOT NULL,
    display_name varchar(160) NOT NULL,
    email varchar(254),
    phone varchar(40),
    website text,
    tax_registration_no varchar(80),
    default_currency char(3) NOT NULL DEFAULT 'INR',
    timezone varchar(64) NOT NULL DEFAULT 'Asia/Kolkata',
    status varchar(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','active','suspended','archived')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    archived_at timestamptz
);

CREATE TABLE app.organization_addresses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    address_type varchar(20) NOT NULL CHECK (address_type IN ('registered','billing','shipping','other')),
    line1 varchar(200) NOT NULL,
    line2 varchar(200),
    city varchar(100),
    state_region varchar(100),
    postal_code varchar(20),
    country_code char(2) NOT NULL,
    is_default boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id)
);
CREATE UNIQUE INDEX uq_org_default_address_type
    ON app.organization_addresses(organization_id, address_type) WHERE is_default;

CREATE TABLE app.branches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    code varchar(40) NOT NULL,
    name varchar(160) NOT NULL,
    email varchar(254),
    phone varchar(40),
    timezone varchar(64),
    is_head_office boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, code)
);
CREATE UNIQUE INDEX uq_one_head_office_per_org ON app.branches(organization_id)
    WHERE is_head_office;

CREATE TABLE app.users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar(254) NOT NULL,
    normalized_email varchar(254) GENERATED ALWAYS AS (lower(email)) STORED,
    password_hash text NOT NULL,
    full_name varchar(160) NOT NULL,
    phone varchar(40),
    is_platform_admin boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    email_verified_at timestamptz,
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (normalized_email)
);

CREATE TABLE app.organization_members (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE RESTRICT,
    member_status varchar(20) NOT NULL DEFAULT 'invited'
        CHECK (member_status IN ('invited','active','disabled','removed')),
    joined_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, user_id)
);

CREATE TABLE app.roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    role_key varchar(60) NOT NULL,
    name varchar(100) NOT NULL,
    description text,
    is_system boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, role_key),
    UNIQUE (organization_id, id)
);

CREATE TABLE app.permissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    permission_key varchar(100) NOT NULL UNIQUE,
    module_key varchar(60) NOT NULL,
    description text
);

CREATE TABLE app.role_permissions (
    organization_id uuid NOT NULL,
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL REFERENCES app.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (organization_id, role_id, permission_id),
    FOREIGN KEY (organization_id, role_id)
        REFERENCES app.roles(organization_id, id) ON DELETE CASCADE
);

CREATE TABLE app.member_roles (
    organization_id uuid NOT NULL,
    member_id uuid NOT NULL,
    role_id uuid NOT NULL,
    assigned_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    assigned_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, member_id, role_id),
    FOREIGN KEY (organization_id, member_id)
        REFERENCES app.organization_members(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, role_id)
        REFERENCES app.roles(organization_id, id) ON DELETE CASCADE
);

CREATE TABLE app.member_branches (
    organization_id uuid NOT NULL,
    member_id uuid NOT NULL,
    branch_id uuid NOT NULL,
    PRIMARY KEY (organization_id, member_id, branch_id),
    FOREIGN KEY (organization_id, member_id)
        REFERENCES app.organization_members(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, branch_id)
        REFERENCES app.branches(organization_id, id) ON DELETE CASCADE
);

-- ---------- SaaS subscriptions and module entitlements ----------
CREATE TABLE app.modules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    module_key varchar(60) NOT NULL UNIQUE,
    name varchar(120) NOT NULL,
    description text,
    is_active boolean NOT NULL DEFAULT true
);

CREATE TABLE app.subscription_plans (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_code varchar(40) NOT NULL UNIQUE,
    name varchar(120) NOT NULL,
    description text,
    billing_interval varchar(20) NOT NULL CHECK (billing_interval IN ('monthly','quarterly','yearly','custom')),
    price numeric(18,2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    currency char(3) NOT NULL DEFAULT 'INR',
    max_members integer CHECK (max_members IS NULL OR max_members > 0),
    max_branches integer CHECK (max_branches IS NULL OR max_branches > 0),
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.plan_modules (
    plan_id uuid NOT NULL REFERENCES app.subscription_plans(id) ON DELETE CASCADE,
    module_id uuid NOT NULL REFERENCES app.modules(id) ON DELETE RESTRICT,
    PRIMARY KEY (plan_id, module_id)
);

CREATE TABLE app.organization_subscriptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    plan_id uuid NOT NULL REFERENCES app.subscription_plans(id) ON DELETE RESTRICT,
    subscription_status varchar(20) NOT NULL
        CHECK (subscription_status IN ('trialing','active','past_due','suspended','cancelled','expired')),
    starts_at timestamptz NOT NULL,
    ends_at timestamptz,
    trial_ends_at timestamptz,
    auto_renew boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    CHECK (ends_at IS NULL OR ends_at > starts_at)
);
CREATE INDEX ix_org_subscriptions_current
    ON app.organization_subscriptions(organization_id, subscription_status, ends_at DESC);

CREATE TABLE app.organization_module_overrides (
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    module_id uuid NOT NULL REFERENCES app.modules(id) ON DELETE CASCADE,
    is_enabled boolean NOT NULL,
    reason text,
    expires_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, module_id)
);

CREATE TABLE app.subscription_payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    subscription_id uuid NOT NULL,
    amount numeric(18,2) NOT NULL CHECK (amount >= 0),
    currency char(3) NOT NULL,
    payment_status varchar(20) NOT NULL CHECK (payment_status IN ('pending','paid','failed','refunded')),
    provider varchar(60),
    provider_reference varchar(160),
    paid_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (organization_id, subscription_id)
        REFERENCES app.organization_subscriptions(organization_id, id) ON DELETE RESTRICT,
    UNIQUE (provider, provider_reference)
);

-- ---------- Central status / workflow module ----------
CREATE TABLE app.status_groups (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    module_key varchar(60) NOT NULL,
    entity_key varchar(80) NOT NULL,
    name varchar(120) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, module_key, entity_key)
);

CREATE TABLE app.status_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    status_group_id uuid NOT NULL,
    status_key varchar(60) NOT NULL,
    label varchar(100) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_initial boolean NOT NULL DEFAULT false,
    is_final boolean NOT NULL DEFAULT false,
    color varchar(20),
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, status_group_id, status_key),
    FOREIGN KEY (organization_id, status_group_id)
        REFERENCES app.status_groups(organization_id, id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_status_one_initial_per_group
    ON app.status_definitions(organization_id, status_group_id) WHERE is_initial;

CREATE TABLE app.status_transitions (
    organization_id uuid NOT NULL,
    status_group_id uuid NOT NULL,
    from_status_id uuid NOT NULL,
    to_status_id uuid NOT NULL,
    requires_permission varchar(100),
    is_active boolean NOT NULL DEFAULT true,
    PRIMARY KEY (organization_id, status_group_id, from_status_id, to_status_id),
    FOREIGN KEY (organization_id, status_group_id)
        REFERENCES app.status_groups(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, from_status_id)
        REFERENCES app.status_definitions(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, to_status_id)
        REFERENCES app.status_definitions(organization_id, id) ON DELETE CASCADE,
    CHECK (from_status_id <> to_status_id)
);

CREATE TABLE app.workflow_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    workflow_key varchar(80) NOT NULL,
    name varchar(120) NOT NULL,
    module_key varchar(60) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, workflow_key)
);

CREATE TABLE app.workflow_steps (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    workflow_id uuid NOT NULL,
    status_id uuid NOT NULL,
    step_order integer NOT NULL,
    is_required boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, workflow_id, step_order),
    FOREIGN KEY (organization_id, workflow_id)
        REFERENCES app.workflow_definitions(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, status_id)
        REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);

-- Polymorphic entity_id is intentional: validate entity ownership in application
-- services (or implement per-entity triggers if database-enforced polymorphism is required).
CREATE TABLE app.status_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    module_key varchar(60) NOT NULL,
    entity_type varchar(80) NOT NULL,
    entity_id uuid NOT NULL,
    from_status_id uuid,
    to_status_id uuid NOT NULL,
    changed_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    remarks text,
    changed_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (organization_id, from_status_id)
        REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, to_status_id)
        REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_status_history_entity
    ON app.status_history(organization_id, module_key, entity_type, entity_id, changed_at DESC);

-- ---------- CRM ----------
CREATE TABLE app.customer_sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(100) NOT NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);

CREATE TABLE app.customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    customer_code varchar(50) NOT NULL,
    customer_type varchar(20) NOT NULL DEFAULT 'business'
        CHECK (customer_type IN ('individual','business')),
    display_name varchar(180) NOT NULL,
    legal_name varchar(200),
    email varchar(254),
    phone varchar(40),
    tax_registration_no varchar(80),
    source_id uuid,
    credit_limit numeric(18,2) NOT NULL DEFAULT 0 CHECK (credit_limit >= 0),
    opening_balance numeric(18,2) NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, customer_code),
    FOREIGN KEY (organization_id, source_id)
        REFERENCES app.customer_sources(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.customer_contacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    name varchar(160) NOT NULL,
    designation varchar(100),
    email varchar(254),
    phone varchar(40),
    is_primary boolean NOT NULL DEFAULT false,
    FOREIGN KEY (organization_id, customer_id)
        REFERENCES app.customers(organization_id, id) ON DELETE CASCADE,
    UNIQUE (organization_id, id)
);
CREATE UNIQUE INDEX uq_customer_primary_contact
    ON app.customer_contacts(organization_id, customer_id) WHERE is_primary;

CREATE TABLE app.customer_addresses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    address_type varchar(20) NOT NULL CHECK (address_type IN ('billing','shipping','other')),
    line1 varchar(200) NOT NULL,
    line2 varchar(200),
    city varchar(100),
    state_region varchar(100),
    postal_code varchar(20),
    country_code char(2) NOT NULL,
    is_default boolean NOT NULL DEFAULT false,
    FOREIGN KEY (organization_id, customer_id)
        REFERENCES app.customers(organization_id, id) ON DELETE CASCADE,
    UNIQUE (organization_id, id)
);
CREATE UNIQUE INDEX uq_customer_default_address
    ON app.customer_addresses(organization_id, customer_id, address_type) WHERE is_default;

CREATE TABLE app.lead_sources (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(100) NOT NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);

CREATE TABLE app.leads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    lead_code varchar(50) NOT NULL,
    company_name varchar(180),
    contact_name varchar(160) NOT NULL,
    email varchar(254),
    phone varchar(40),
    source_id uuid,
    status_id uuid,
    estimated_value numeric(18,2) CHECK (estimated_value IS NULL OR estimated_value >= 0),
    assigned_to uuid,
    converted_customer_id uuid,
    lost_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, lead_code),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, source_id) REFERENCES app.lead_sources(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, converted_customer_id) REFERENCES app.customers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (assigned_to) REFERENCES app.users(id) ON DELETE SET NULL
);
CREATE INDEX ix_leads_org_status ON app.leads(organization_id, status_id, created_at DESC);

CREATE TABLE app.opportunities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    customer_id uuid,
    lead_id uuid,
    opportunity_code varchar(50) NOT NULL,
    title varchar(180) NOT NULL,
    stage_id uuid,
    expected_value numeric(18,2) NOT NULL DEFAULT 0 CHECK (expected_value >= 0),
    probability numeric(5,2) CHECK (probability BETWEEN 0 AND 100),
    expected_close_date date,
    owner_user_id uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, opportunity_code),
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, lead_id) REFERENCES app.leads(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, stage_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    CHECK (customer_id IS NOT NULL OR lead_id IS NOT NULL)
);

CREATE TABLE app.activities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    activity_type varchar(30) NOT NULL CHECK (activity_type IN ('call','email','meeting','task','note','other')),
    subject varchar(180) NOT NULL,
    description text,
    customer_id uuid,
    lead_id uuid,
    opportunity_id uuid,
    assigned_to uuid REFERENCES app.users(id) ON DELETE SET NULL,
    due_at timestamptz,
    completed_at timestamptz,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, lead_id) REFERENCES app.leads(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, opportunity_id) REFERENCES app.opportunities(organization_id, id) ON DELETE CASCADE,
    CHECK (num_nonnulls(customer_id, lead_id, opportunity_id) >= 1)
);
CREATE INDEX ix_activities_due ON app.activities(organization_id, assigned_to, due_at) WHERE completed_at IS NULL;

CREATE TABLE app.customer_notes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    note text NOT NULL,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE CASCADE
);

CREATE TABLE app.tags (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(60) NOT NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);
CREATE TABLE app.customer_tags (
    organization_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    PRIMARY KEY (organization_id, customer_id, tag_id),
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, tag_id) REFERENCES app.tags(organization_id, id) ON DELETE CASCADE
);

-- ---------- Catalog / inventory ----------
CREATE TABLE app.units (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(80) NOT NULL,
    symbol varchar(20) NOT NULL,
    decimal_places smallint NOT NULL DEFAULT 2 CHECK (decimal_places BETWEEN 0 AND 6),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name),
    UNIQUE (organization_id, symbol)
);

CREATE TABLE app.product_categories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    parent_id uuid,
    name varchar(120) NOT NULL,
    description text,
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name),
    FOREIGN KEY (organization_id, parent_id) REFERENCES app.product_categories(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.brands (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(120) NOT NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);

CREATE TABLE app.products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    category_id uuid,
    brand_id uuid,
    unit_id uuid NOT NULL,
    product_type varchar(20) NOT NULL DEFAULT 'stock'
        CHECK (product_type IN ('stock','service','non_stock')),
    sku varchar(80) NOT NULL,
    barcode varchar(100),
    name varchar(180) NOT NULL,
    description text,
    purchase_price numeric(18,4) NOT NULL DEFAULT 0 CHECK (purchase_price >= 0),
    selling_price numeric(18,4) NOT NULL DEFAULT 0 CHECK (selling_price >= 0),
    reorder_level numeric(18,4) NOT NULL DEFAULT 0 CHECK (reorder_level >= 0),
    track_inventory boolean NOT NULL DEFAULT true,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, sku),
    FOREIGN KEY (organization_id, category_id) REFERENCES app.product_categories(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, brand_id) REFERENCES app.brands(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, unit_id) REFERENCES app.units(organization_id, id) ON DELETE RESTRICT,
    CHECK (product_type <> 'service' OR track_inventory = false)
);
CREATE INDEX ix_products_search ON app.products(organization_id, name);
CREATE INDEX ix_products_barcode ON app.products(organization_id, barcode) WHERE barcode IS NOT NULL;

CREATE TABLE app.product_variants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    product_id uuid NOT NULL,
    variant_sku varchar(80) NOT NULL,
    variant_name varchar(120) NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    barcode varchar(100),
    selling_price numeric(18,4) CHECK (selling_price IS NULL OR selling_price >= 0),
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, variant_sku),
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE CASCADE
);

CREATE TABLE app.suppliers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    supplier_code varchar(50) NOT NULL,
    name varchar(180) NOT NULL,
    email varchar(254),
    phone varchar(40),
    tax_registration_no varchar(80),
    opening_balance numeric(18,2) NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, supplier_code)
);

CREATE TABLE app.supplier_addresses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    supplier_id uuid NOT NULL,
    address_type varchar(20) NOT NULL CHECK (address_type IN ('billing','shipping','other')),
    line1 varchar(200) NOT NULL,
    line2 varchar(200),
    city varchar(100),
    state_region varchar(100),
    postal_code varchar(20),
    country_code char(2) NOT NULL,
    FOREIGN KEY (organization_id, supplier_id) REFERENCES app.suppliers(organization_id, id) ON DELETE CASCADE
);

CREATE TABLE app.warehouses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    code varchar(40) NOT NULL,
    name varchar(120) NOT NULL,
    address text,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, code),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.stock_balances (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    warehouse_id uuid NOT NULL,
    product_id uuid NOT NULL,
    variant_id uuid,
    quantity_on_hand numeric(18,4) NOT NULL DEFAULT 0,
    quantity_reserved numeric(18,4) NOT NULL DEFAULT 0,
    quantity_available numeric(18,4) GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    average_cost numeric(18,4) NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (organization_id, warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT,
    CHECK (quantity_reserved >= 0),
    CHECK (quantity_on_hand >= quantity_reserved),
    CHECK (average_cost >= 0)
);
CREATE UNIQUE INDEX uq_stock_balance_without_variant
    ON app.stock_balances (organization_id, warehouse_id, product_id)
    WHERE variant_id IS NULL;
CREATE UNIQUE INDEX uq_stock_balance_with_variant
    ON app.stock_balances (organization_id, warehouse_id, product_id, variant_id)
    WHERE variant_id IS NOT NULL;

CREATE TABLE app.stock_movements (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    warehouse_id uuid NOT NULL,
    product_id uuid NOT NULL,
    variant_id uuid,
    movement_type varchar(30) NOT NULL CHECK (movement_type IN
        ('opening','purchase_receipt','sale','sales_return','purchase_return','adjustment','transfer_in','transfer_out')),
    quantity_delta numeric(18,4) NOT NULL CHECK (quantity_delta <> 0),
    unit_cost numeric(18,4) NOT NULL DEFAULT 0 CHECK (unit_cost >= 0),
    source_type varchar(60),
    source_id uuid,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    notes text,
    FOREIGN KEY (organization_id, warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_stock_movements_product_time ON app.stock_movements(organization_id, product_id, occurred_at DESC);
CREATE INDEX ix_stock_movements_source ON app.stock_movements(organization_id, source_type, source_id);

CREATE TABLE app.stock_adjustments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    warehouse_id uuid NOT NULL,
    adjustment_no varchar(50) NOT NULL,
    status_id uuid,
    reason text,
    adjusted_at timestamptz NOT NULL DEFAULT now(),
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, adjustment_no),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);
CREATE TABLE app.stock_adjustment_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    adjustment_id uuid NOT NULL,
    product_id uuid NOT NULL,
    variant_id uuid,
    counted_quantity numeric(18,4) NOT NULL CHECK (counted_quantity >= 0),
    system_quantity numeric(18,4) NOT NULL,
    reason text,
    FOREIGN KEY (organization_id, adjustment_id) REFERENCES app.stock_adjustments(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.stock_transfers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    transfer_no varchar(50) NOT NULL,
    from_warehouse_id uuid NOT NULL,
    to_warehouse_id uuid NOT NULL,
    status_id uuid,
    requested_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, transfer_no),
    FOREIGN KEY (organization_id, from_warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, to_warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    CHECK (from_warehouse_id <> to_warehouse_id)
);
CREATE TABLE app.stock_transfer_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    transfer_id uuid NOT NULL,
    product_id uuid NOT NULL,
    variant_id uuid,
    quantity numeric(18,4) NOT NULL CHECK (quantity > 0),
    FOREIGN KEY (organization_id, transfer_id) REFERENCES app.stock_transfers(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT
);

-- ---------- Purchasing ----------
CREATE TABLE app.purchase_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    supplier_id uuid NOT NULL,
    warehouse_id uuid NOT NULL,
    po_number varchar(50) NOT NULL,
    order_date date NOT NULL DEFAULT current_date,
    expected_date date,
    status_id uuid,
    currency char(3) NOT NULL DEFAULT 'INR',
    subtotal numeric(18,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_total >= 0),
    discount_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (discount_total >= 0),
    grand_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (grand_total >= 0),
    notes text,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, po_number),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, supplier_id) REFERENCES app.suppliers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    CHECK (expected_date IS NULL OR expected_date >= order_date)
);
CREATE TABLE app.purchase_order_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    purchase_order_id uuid NOT NULL,
    product_id uuid NOT NULL,
    variant_id uuid,
    description text,
    quantity numeric(18,4) NOT NULL CHECK (quantity > 0),
    received_quantity numeric(18,4) NOT NULL DEFAULT 0 CHECK (received_quantity >= 0),
    unit_cost numeric(18,4) NOT NULL CHECK (unit_cost >= 0),
    tax_rate numeric(7,4) NOT NULL DEFAULT 0 CHECK (tax_rate BETWEEN 0 AND 100),
    line_total numeric(18,2) NOT NULL CHECK (line_total >= 0),
    UNIQUE (organization_id, id),
    FOREIGN KEY (organization_id, purchase_order_id) REFERENCES app.purchase_orders(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT,
    CHECK (received_quantity <= quantity)
);
CREATE INDEX ix_po_supplier_date ON app.purchase_orders(organization_id, supplier_id, order_date DESC);

CREATE TABLE app.goods_receipts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    purchase_order_id uuid,
    supplier_id uuid NOT NULL,
    warehouse_id uuid NOT NULL,
    receipt_no varchar(50) NOT NULL,
    received_at timestamptz NOT NULL DEFAULT now(),
    status_id uuid,
    received_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    notes text,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, receipt_no),
    FOREIGN KEY (organization_id, purchase_order_id) REFERENCES app.purchase_orders(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, supplier_id) REFERENCES app.suppliers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);
CREATE TABLE app.goods_receipt_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    goods_receipt_id uuid NOT NULL,
    purchase_order_item_id uuid,
    product_id uuid NOT NULL,
    variant_id uuid,
    quantity_received numeric(18,4) NOT NULL CHECK (quantity_received > 0),
    unit_cost numeric(18,4) NOT NULL DEFAULT 0 CHECK (unit_cost >= 0),
    FOREIGN KEY (organization_id, goods_receipt_id) REFERENCES app.goods_receipts(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, purchase_order_item_id) REFERENCES app.purchase_order_items(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT
);

-- ---------- Billing settings ----------
CREATE TABLE app.billing_settings (
    organization_id uuid PRIMARY KEY REFERENCES app.organizations(id) ON DELETE CASCADE,
    default_currency char(3) NOT NULL DEFAULT 'INR',
    tax_inclusive_pricing boolean NOT NULL DEFAULT false,
    allow_partial_payment boolean NOT NULL DEFAULT true,
    allow_overpayment boolean NOT NULL DEFAULT false,
    default_payment_terms_days integer NOT NULL DEFAULT 0 CHECK (default_payment_terms_days >= 0),
    default_due_days integer NOT NULL DEFAULT 15 CHECK (default_due_days >= 0),
    decimal_places smallint NOT NULL DEFAULT 2 CHECK (decimal_places BETWEEN 0 AND 4),
    rounding_method varchar(20) NOT NULL DEFAULT 'half_up'
        CHECK (rounding_method IN ('half_up','half_even','up','down')),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE app.document_sequences (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    document_type varchar(40) NOT NULL,
    prefix varchar(30) NOT NULL,
    suffix varchar(30),
    next_number bigint NOT NULL DEFAULT 1 CHECK (next_number > 0),
    padding smallint NOT NULL DEFAULT 5 CHECK (padding BETWEEN 1 AND 12),
    reset_period varchar(20) NOT NULL DEFAULT 'never'
        CHECK (reset_period IN ('never','yearly','monthly')),
    last_reset_key varchar(20),
    UNIQUE (organization_id, id),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_document_sequence_org_default_branch
    ON app.document_sequences (organization_id, document_type) WHERE branch_id IS NULL;
CREATE UNIQUE INDEX uq_document_sequence_org_branch
    ON app.document_sequences (organization_id, branch_id, document_type) WHERE branch_id IS NOT NULL;

CREATE TABLE app.tax_rates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    tax_code varchar(40) NOT NULL,
    name varchar(100) NOT NULL,
    rate numeric(7,4) NOT NULL CHECK (rate BETWEEN 0 AND 100),
    tax_type varchar(20) NOT NULL DEFAULT 'percentage'
        CHECK (tax_type IN ('percentage','fixed')),
    is_compound boolean NOT NULL DEFAULT false,
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, tax_code)
);

CREATE TABLE app.tax_groups (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(100) NOT NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);
CREATE TABLE app.tax_group_rates (
    organization_id uuid NOT NULL,
    tax_group_id uuid NOT NULL,
    tax_rate_id uuid NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    PRIMARY KEY (organization_id, tax_group_id, tax_rate_id),
    FOREIGN KEY (organization_id, tax_group_id) REFERENCES app.tax_groups(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, tax_rate_id) REFERENCES app.tax_rates(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.payment_methods (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    method_key varchar(40) NOT NULL,
    display_name varchar(80) NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, method_key)
);

CREATE TABLE app.invoice_templates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(120) NOT NULL,
    template_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_default boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);
CREATE UNIQUE INDEX uq_default_invoice_template ON app.invoice_templates(organization_id) WHERE is_default;

-- ---------- Sales / invoicing ----------
CREATE TABLE app.quotations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    customer_id uuid NOT NULL,
    quotation_no varchar(50) NOT NULL,
    quotation_date date NOT NULL DEFAULT current_date,
    valid_until date,
    status_id uuid,
    currency char(3) NOT NULL DEFAULT 'INR',
    subtotal numeric(18,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    discount_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (discount_total >= 0),
    tax_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_total >= 0),
    grand_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (grand_total >= 0),
    notes text,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, quotation_no),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    CHECK (valid_until IS NULL OR valid_until >= quotation_date)
);
CREATE TABLE app.quotation_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    quotation_id uuid NOT NULL,
    product_id uuid,
    description text NOT NULL,
    quantity numeric(18,4) NOT NULL CHECK (quantity > 0),
    unit_price numeric(18,4) NOT NULL CHECK (unit_price >= 0),
    discount_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    tax_rate numeric(7,4) NOT NULL DEFAULT 0 CHECK (tax_rate BETWEEN 0 AND 100),
    line_total numeric(18,2) NOT NULL CHECK (line_total >= 0),
    FOREIGN KEY (organization_id, quotation_id) REFERENCES app.quotations(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.sales_orders (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    customer_id uuid NOT NULL,
    quotation_id uuid,
    order_no varchar(50) NOT NULL,
    order_date date NOT NULL DEFAULT current_date,
    status_id uuid,
    currency char(3) NOT NULL DEFAULT 'INR',
    subtotal numeric(18,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    discount_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (discount_total >= 0),
    tax_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_total >= 0),
    grand_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (grand_total >= 0),
    notes text,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, order_no),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, quotation_id) REFERENCES app.quotations(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);
CREATE TABLE app.sales_order_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    sales_order_id uuid NOT NULL,
    product_id uuid,
    variant_id uuid,
    description text NOT NULL,
    quantity numeric(18,4) NOT NULL CHECK (quantity > 0),
    unit_price numeric(18,4) NOT NULL CHECK (unit_price >= 0),
    discount_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    tax_rate numeric(7,4) NOT NULL DEFAULT 0 CHECK (tax_rate BETWEEN 0 AND 100),
    line_total numeric(18,2) NOT NULL CHECK (line_total >= 0),
    FOREIGN KEY (organization_id, sales_order_id) REFERENCES app.sales_orders(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.sales_invoices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    customer_id uuid NOT NULL,
    sales_order_id uuid,
    invoice_no varchar(50) NOT NULL,
    invoice_date date NOT NULL DEFAULT current_date,
    due_date date,
    status_id uuid,
    currency char(3) NOT NULL DEFAULT 'INR',
    exchange_rate numeric(18,8) NOT NULL DEFAULT 1 CHECK (exchange_rate > 0),
    subtotal numeric(18,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    discount_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (discount_total >= 0),
    tax_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_total >= 0),
    shipping_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (shipping_amount >= 0),
    grand_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (grand_total >= 0),
    amount_paid numeric(18,2) NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
    balance_due numeric(18,2) GENERATED ALWAYS AS (grand_total - amount_paid) STORED,
    billing_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb,
    notes text,
    issued_at timestamptz,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, invoice_no),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, sales_order_id) REFERENCES app.sales_orders(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    CHECK (due_date IS NULL OR due_date >= invoice_date),
    CHECK (amount_paid <= grand_total)
);
CREATE INDEX ix_invoices_customer_date ON app.sales_invoices(organization_id, customer_id, invoice_date DESC);
CREATE INDEX ix_invoices_due ON app.sales_invoices(organization_id, due_date) WHERE balance_due > 0;

CREATE TABLE app.sales_invoice_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    invoice_id uuid NOT NULL,
    product_id uuid,
    variant_id uuid,
    description text NOT NULL,
    quantity numeric(18,4) NOT NULL CHECK (quantity > 0),
    unit_price numeric(18,4) NOT NULL CHECK (unit_price >= 0),
    discount_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    tax_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    line_total numeric(18,2) NOT NULL CHECK (line_total >= 0),
    warehouse_id uuid,
    UNIQUE (organization_id, id),
    FOREIGN KEY (organization_id, invoice_id) REFERENCES app.sales_invoices(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_invoice_items_invoice ON app.sales_invoice_items(organization_id, invoice_id);

CREATE TABLE app.invoice_item_taxes (
    organization_id uuid NOT NULL,
    invoice_item_id uuid NOT NULL,
    tax_rate_id uuid NOT NULL,
    taxable_amount numeric(18,2) NOT NULL CHECK (taxable_amount >= 0),
    tax_amount numeric(18,2) NOT NULL CHECK (tax_amount >= 0),
    PRIMARY KEY (organization_id, invoice_item_id, tax_rate_id),
    FOREIGN KEY (organization_id, invoice_item_id) REFERENCES app.sales_invoice_items(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, tax_rate_id) REFERENCES app.tax_rates(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.payments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    customer_id uuid,
    supplier_id uuid,
    payment_no varchar(50) NOT NULL,
    payment_direction varchar(10) NOT NULL CHECK (payment_direction IN ('in','out')),
    payment_date date NOT NULL DEFAULT current_date,
    amount numeric(18,2) NOT NULL CHECK (amount > 0),
    currency char(3) NOT NULL DEFAULT 'INR',
    payment_method_id uuid,
    reference_no varchar(120),
    payment_status varchar(20) NOT NULL DEFAULT 'completed'
        CHECK (payment_status IN ('pending','completed','failed','refunded','void')),
    notes text,
    received_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, payment_no),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, supplier_id) REFERENCES app.suppliers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, payment_method_id) REFERENCES app.payment_methods(organization_id, id) ON DELETE RESTRICT,
    CHECK ((payment_direction = 'in' AND customer_id IS NOT NULL AND supplier_id IS NULL)
        OR (payment_direction = 'out' AND supplier_id IS NOT NULL AND customer_id IS NULL))
);
CREATE INDEX ix_payments_customer_date ON app.payments(organization_id, customer_id, payment_date DESC);

CREATE TABLE app.invoice_payments (
    organization_id uuid NOT NULL,
    invoice_id uuid NOT NULL,
    payment_id uuid NOT NULL,
    amount_applied numeric(18,2) NOT NULL CHECK (amount_applied > 0),
    PRIMARY KEY (organization_id, invoice_id, payment_id),
    FOREIGN KEY (organization_id, invoice_id) REFERENCES app.sales_invoices(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, payment_id) REFERENCES app.payments(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.purchase_invoices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    supplier_id uuid NOT NULL,
    goods_receipt_id uuid,
    vendor_invoice_no varchar(80),
    purchase_invoice_no varchar(50) NOT NULL,
    invoice_date date NOT NULL DEFAULT current_date,
    due_date date,
    status_id uuid,
    currency char(3) NOT NULL DEFAULT 'INR',
    subtotal numeric(18,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_total >= 0),
    grand_total numeric(18,2) NOT NULL DEFAULT 0 CHECK (grand_total >= 0),
    amount_paid numeric(18,2) NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
    balance_due numeric(18,2) GENERATED ALWAYS AS (grand_total - amount_paid) STORED,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, purchase_invoice_no),
    FOREIGN KEY (organization_id, supplier_id) REFERENCES app.suppliers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, goods_receipt_id) REFERENCES app.goods_receipts(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT,
    CHECK (amount_paid <= grand_total),
    CHECK (due_date IS NULL OR due_date >= invoice_date)
);
CREATE TABLE app.purchase_invoice_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    purchase_invoice_id uuid NOT NULL,
    product_id uuid,
    description text NOT NULL,
    quantity numeric(18,4) NOT NULL CHECK (quantity > 0),
    unit_cost numeric(18,4) NOT NULL CHECK (unit_cost >= 0),
    tax_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    line_total numeric(18,2) NOT NULL CHECK (line_total >= 0),
    FOREIGN KEY (organization_id, purchase_invoice_id) REFERENCES app.purchase_invoices(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.supplier_payments (
    organization_id uuid NOT NULL,
    purchase_invoice_id uuid NOT NULL,
    payment_id uuid NOT NULL,
    amount_applied numeric(18,2) NOT NULL CHECK (amount_applied > 0),
    PRIMARY KEY (organization_id, purchase_invoice_id, payment_id),
    FOREIGN KEY (organization_id, purchase_invoice_id) REFERENCES app.purchase_invoices(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, payment_id) REFERENCES app.payments(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.sales_returns (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    invoice_id uuid NOT NULL,
    return_no varchar(50) NOT NULL,
    return_date date NOT NULL DEFAULT current_date,
    warehouse_id uuid NOT NULL,
    status_id uuid,
    reason text,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, return_no),
    FOREIGN KEY (organization_id, invoice_id) REFERENCES app.sales_invoices(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, warehouse_id) REFERENCES app.warehouses(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);
CREATE TABLE app.sales_return_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    sales_return_id uuid NOT NULL,
    invoice_item_id uuid,
    product_id uuid NOT NULL,
    variant_id uuid,
    quantity numeric(18,4) NOT NULL CHECK (quantity > 0),
    refund_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (refund_amount >= 0),
    restock boolean NOT NULL DEFAULT true,
    FOREIGN KEY (organization_id, sales_return_id) REFERENCES app.sales_returns(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, invoice_item_id) REFERENCES app.sales_invoice_items(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, product_id) REFERENCES app.products(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, variant_id) REFERENCES app.product_variants(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.credit_notes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    customer_id uuid NOT NULL,
    invoice_id uuid,
    credit_note_no varchar(50) NOT NULL,
    issue_date date NOT NULL DEFAULT current_date,
    amount numeric(18,2) NOT NULL CHECK (amount > 0),
    reason text,
    status_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, credit_note_no),
    FOREIGN KEY (organization_id, customer_id) REFERENCES app.customers(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, invoice_id) REFERENCES app.sales_invoices(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);

-- ---------- Expenses ----------
CREATE TABLE app.expense_categories (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(100) NOT NULL,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);
CREATE TABLE app.expenses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    branch_id uuid,
    category_id uuid NOT NULL,
    expense_no varchar(50) NOT NULL,
    expense_date date NOT NULL DEFAULT current_date,
    amount numeric(18,2) NOT NULL CHECK (amount >= 0),
    tax_amount numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    currency char(3) NOT NULL DEFAULT 'INR',
    vendor_name varchar(180),
    description text,
    status_id uuid,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, expense_no),
    FOREIGN KEY (organization_id, branch_id) REFERENCES app.branches(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, category_id) REFERENCES app.expense_categories(organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (organization_id, status_id) REFERENCES app.status_definitions(organization_id, id) ON DELETE RESTRICT
);

-- ---------- Analysis / reporting configuration ----------
CREATE TABLE app.dashboards (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    name varchar(120) NOT NULL,
    description text,
    is_default boolean NOT NULL DEFAULT false,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, name)
);
CREATE UNIQUE INDEX uq_dashboard_default ON app.dashboards(organization_id) WHERE is_default;

CREATE TABLE app.report_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    report_key varchar(80) NOT NULL,
    name varchar(140) NOT NULL,
    module_key varchar(60) NOT NULL,
    description text,
    query_identifier varchar(120) NOT NULL,
    default_config jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, report_key)
);

CREATE TABLE app.dashboard_widgets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL,
    dashboard_id uuid NOT NULL,
    report_id uuid,
    widget_key varchar(80) NOT NULL,
    title varchar(120) NOT NULL,
    widget_type varchar(30) NOT NULL CHECK (widget_type IN ('number','bar','line','pie','table','list')),
    position_x integer NOT NULL DEFAULT 0,
    position_y integer NOT NULL DEFAULT 0,
    width_units smallint NOT NULL DEFAULT 4 CHECK (width_units BETWEEN 1 AND 12),
    height_units smallint NOT NULL DEFAULT 3 CHECK (height_units > 0),
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    FOREIGN KEY (organization_id, dashboard_id) REFERENCES app.dashboards(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, report_id) REFERENCES app.report_definitions(organization_id, id) ON DELETE RESTRICT,
    UNIQUE (organization_id, dashboard_id, widget_key)
);

CREATE TABLE app.kpi_definitions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    kpi_key varchar(80) NOT NULL,
    name varchar(120) NOT NULL,
    description text,
    source_identifier varchar(120) NOT NULL,
    aggregation varchar(30) NOT NULL CHECK (aggregation IN ('count','sum','avg','min','max','ratio')),
    format_key varchar(30) NOT NULL DEFAULT 'number',
    config jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active boolean NOT NULL DEFAULT true,
    UNIQUE (organization_id, id),
    UNIQUE (organization_id, kpi_key)
);

CREATE TABLE app.analysis_settings (
    organization_id uuid PRIMARY KEY REFERENCES app.organizations(id) ON DELETE CASCADE,
    default_date_range varchar(20) NOT NULL DEFAULT 'this_month',
    fiscal_year_start_month smallint NOT NULL DEFAULT 4 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    default_dashboard_id uuid,
    timezone varchar(64) NOT NULL DEFAULT 'Asia/Kolkata',
    updated_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (organization_id, default_dashboard_id) REFERENCES app.dashboards(organization_id, id) ON DELETE RESTRICT
);

CREATE TABLE app.saved_reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    report_id uuid NOT NULL,
    owner_user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    name varchar(120) NOT NULL,
    filters jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    FOREIGN KEY (organization_id, report_id) REFERENCES app.report_definitions(organization_id, id) ON DELETE CASCADE
);

CREATE TABLE app.report_schedules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    report_id uuid NOT NULL,
    created_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    schedule_name varchar(120) NOT NULL,
    cron_expression varchar(100) NOT NULL,
    timezone varchar(64) NOT NULL DEFAULT 'Asia/Kolkata',
    output_format varchar(10) NOT NULL DEFAULT 'pdf' CHECK (output_format IN ('pdf','xlsx','csv')),
    recipients jsonb NOT NULL DEFAULT '[]'::jsonb,
    is_active boolean NOT NULL DEFAULT true,
    next_run_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (organization_id, id),
    FOREIGN KEY (organization_id, report_id) REFERENCES app.report_definitions(organization_id, id) ON DELETE CASCADE
);
CREATE INDEX ix_report_schedules_next_run ON app.report_schedules(next_run_at) WHERE is_active;

CREATE TABLE app.report_access (
    organization_id uuid NOT NULL,
    report_id uuid NOT NULL,
    role_id uuid NOT NULL,
    PRIMARY KEY (organization_id, report_id, role_id),
    FOREIGN KEY (organization_id, report_id) REFERENCES app.report_definitions(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, role_id) REFERENCES app.roles(organization_id, id) ON DELETE CASCADE
);
CREATE TABLE app.dashboard_access (
    organization_id uuid NOT NULL,
    dashboard_id uuid NOT NULL,
    role_id uuid NOT NULL,
    PRIMARY KEY (organization_id, dashboard_id, role_id),
    FOREIGN KEY (organization_id, dashboard_id) REFERENCES app.dashboards(organization_id, id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id, role_id) REFERENCES app.roles(organization_id, id) ON DELETE CASCADE
);

-- ---------- Audit / files / generic notes ----------
CREATE TABLE app.audit_logs (
    id bigserial PRIMARY KEY,
    organization_id uuid REFERENCES app.organizations(id) ON DELETE SET NULL,
    actor_user_id uuid REFERENCES app.users(id) ON DELETE SET NULL,
    action varchar(80) NOT NULL,
    entity_type varchar(100) NOT NULL,
    entity_id uuid,
    request_id varchar(100),
    ip_address inet,
    user_agent text,
    before_data jsonb,
    after_data jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_org_time ON app.audit_logs(organization_id, created_at DESC);
CREATE INDEX ix_audit_entity ON app.audit_logs(organization_id, entity_type, entity_id);

CREATE TABLE app.file_attachments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES app.organizations(id) ON DELETE CASCADE,
    entity_type varchar(80) NOT NULL,
    entity_id uuid NOT NULL,
    storage_key text NOT NULL,
    original_filename varchar(255) NOT NULL,
    content_type varchar(120),
    file_size_bytes bigint CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    uploaded_by uuid REFERENCES app.users(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_file_attachments_entity ON app.file_attachments(organization_id, entity_type, entity_id);

-- ---------- Updated-at triggers ----------
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'organizations','branches','users','organization_members','organization_subscriptions',
    'customers','leads','opportunities','products','suppliers','sales_invoices'
  ]
  LOOP
    EXECUTE format('CREATE TRIGGER trg_%I_updated_at BEFORE UPDATE ON app.%I FOR EACH ROW EXECUTE FUNCTION app.set_updated_at()', t, t);
  END LOOP;
END $$;

-- ---------- Tenant row-level security ----------
-- Apply to organization-owned business tables. The app must execute:
-- SELECT set_config('app.current_organization_id', '<authorized-uuid>', true);
-- within each transaction, after authenticating membership.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'branches','organization_members','roles','role_permissions','member_roles','member_branches',
    'organization_subscriptions','organization_module_overrides','subscription_payments',
    'status_groups','status_definitions','status_transitions','workflow_definitions','workflow_steps','status_history',
    'customer_sources','customers','customer_contacts','customer_addresses','lead_sources','leads','opportunities',
    'activities','customer_notes','tags','customer_tags','units','product_categories','brands','products','product_variants',
    'suppliers','supplier_addresses','warehouses','stock_balances','stock_movements','stock_adjustments',
    'stock_adjustment_items','stock_transfers','stock_transfer_items','purchase_orders','purchase_order_items',
    'goods_receipts','goods_receipt_items','billing_settings','document_sequences','tax_rates','tax_groups',
    'tax_group_rates','payment_methods','invoice_templates','quotations','quotation_items','sales_orders',
    'sales_order_items','sales_invoices','sales_invoice_items','invoice_item_taxes','payments','invoice_payments',
    'purchase_invoices','purchase_invoice_items','supplier_payments','sales_returns','sales_return_items','credit_notes',
    'expense_categories','expenses','dashboards','report_definitions','dashboard_widgets','kpi_definitions',
    'analysis_settings','saved_reports','report_schedules','report_access','dashboard_access','file_attachments'
  ]
  LOOP
    EXECUTE format('ALTER TABLE app.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE app.%I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format(
      'CREATE POLICY tenant_isolation ON app.%I USING (organization_id = app.current_org_id()) WITH CHECK (organization_id = app.current_org_id())',
      t
    );
  END LOOP;
END $$;

-- Organizations and users are platform identity tables. Access them through
-- narrowly scoped service functions / a non-owner application role, not tenant-wide RLS.
-- The platform administrator's access should be separately authorized and audited.

COMMIT;

-- ---------- Operational notes ----------
-- Stock balances must be updated in the same transaction as stock_movements.
-- Invoice amount_paid / purchase invoice amount_paid should be maintained by a
-- transactional service or carefully designed trigger from payment allocations.
-- Document numbers must be allocated with SELECT ... FOR UPDATE on document_sequences.
-- Never update/delete posted invoice lines or stock movements; use reversal documents.
-- Consider partitioning audit_logs and stock_movements after measuring volume.
