-- API tables, login helper, app role, and starter catalog.
-- Apply with psql after ddl.sql. CREATE ROLE uses \gexec so it stays outside a transaction.

SELECT 'CREATE ROLE billing_app LOGIN PASSWORD ''billing_app'' NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'billing_app')\gexec

CREATE OR REPLACE FUNCTION app.organizations_for_user(p_user_id uuid)
RETURNS TABLE (organization_id uuid, member_id uuid, member_status varchar(20))
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = app, public
AS $$
    SELECT m.organization_id, m.id, m.member_status
    FROM app.organization_members m
    WHERE m.user_id = p_user_id
      AND m.member_status IN ('invited', 'active', 'disabled');
$$;

REVOKE ALL ON FUNCTION app.organizations_for_user(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.organizations_for_user(uuid) TO billing_app;

GRANT USAGE ON SCHEMA app TO billing_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO billing_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO billing_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO billing_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO billing_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT USAGE, SELECT ON SEQUENCES TO billing_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT EXECUTE ON FUNCTIONS TO billing_app;

CREATE TABLE IF NOT EXISTS app.auth_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    organization_id uuid REFERENCES app.organizations(id) ON DELETE SET NULL,
    refresh_token_hash text NOT NULL UNIQUE,
    user_agent text,
    ip_address inet,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON app.auth_sessions (user_id);

CREATE TABLE IF NOT EXISTS app.password_reset_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    token_hash text NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.email_verification_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    token_hash text NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    used_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.notifications (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid REFERENCES app.organizations(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES app.users(id) ON DELETE CASCADE,
    title varchar(180) NOT NULL,
    body text,
    is_read boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_notifications_user_read ON app.notifications (user_id, is_read, created_at DESC);

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO billing_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO billing_app;

INSERT INTO app.modules (module_key, name) VALUES
    ('crm', 'CRM'),
    ('inventory', 'Inventory'),
    ('purchasing', 'Purchasing'),
    ('billing', 'Billing'),
    ('expenses', 'Expenses'),
    ('analytics', 'Analytics'),
    ('settings', 'Settings')
ON CONFLICT (module_key) DO NOTHING;

INSERT INTO app.permissions (permission_key, module_key, description) VALUES
    ('crm.read', 'crm', 'Read CRM records'),
    ('crm.write', 'crm', 'Change CRM records'),
    ('inventory.read', 'inventory', 'Read inventory'),
    ('inventory.write', 'inventory', 'Change inventory'),
    ('purchasing.read', 'purchasing', 'Read purchasing'),
    ('purchasing.write', 'purchasing', 'Change purchasing'),
    ('billing.read', 'billing', 'Read billing'),
    ('billing.write', 'billing', 'Change billing'),
    ('expenses.read', 'expenses', 'Read expenses'),
    ('expenses.write', 'expenses', 'Change expenses'),
    ('reports.read', 'analytics', 'Read reports and dashboards'),
    ('settings.write', 'settings', 'Change organization settings'),
    ('access.manage', 'settings', 'Manage members and roles'),
    ('workflows.manage', 'settings', 'Manage statuses and workflows')
ON CONFLICT (permission_key) DO NOTHING;

INSERT INTO app.subscription_plans (plan_code, name, billing_interval, price)
VALUES ('starter', 'Starter', 'monthly', 0)
ON CONFLICT (plan_code) DO NOTHING;

INSERT INTO app.plan_modules (plan_id, module_id)
SELECT plan.id, module.id
FROM app.subscription_plans plan
CROSS JOIN app.modules module
WHERE plan.plan_code = 'starter'
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS app.admin_users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email varchar(254) NOT NULL,
    normalized_email varchar(254) GENERATED ALWAYS AS (lower(email)) STORED,
    password_hash text NOT NULL,
    full_name varchar(160) NOT NULL,
    phone varchar(40),
    is_active boolean NOT NULL DEFAULT true,
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (normalized_email)
);

CREATE TABLE IF NOT EXISTS app.admin_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id uuid NOT NULL REFERENCES app.admin_users(id) ON DELETE CASCADE,
    refresh_token_hash text NOT NULL UNIQUE,
    user_agent text,
    ip_address inet,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_admin_sessions_admin_user_id ON app.admin_sessions (admin_user_id);

INSERT INTO app.admin_users (id, email, password_hash, full_name, phone, is_active)
SELECT id, email, password_hash, full_name, phone, is_active
FROM app.users
WHERE is_platform_admin = true
ON CONFLICT (normalized_email) DO NOTHING;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO billing_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO billing_app;
