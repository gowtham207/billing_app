"""SQLAlchemy models generated from database/ddl.sql. Do not edit by hand."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class Organization(Base):
    __tablename__ = 'organizations'
    __table_args__ = (
        CheckConstraint("status IN ('pending','active','suspended','archived')", name='ck_organizations_status_0'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    website: Mapped[str | None] = mapped_column(Text(), nullable=True)
    tax_registration_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    default_currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'Asia/Kolkata'"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrganizationAddress(Base):
    __tablename__ = 'organization_addresses'
    __table_args__ = (
        CheckConstraint("address_type IN ('registered','billing','shipping','other')", name='ck_organization_addresses_address_type_0'),
        UniqueConstraint('organization_id', 'id', name='uq_organization_addresses_organization_id_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    address_type: Mapped[str] = mapped_column(String(20), nullable=False)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class Branch(Base):
    __tablename__ = 'branches'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_branches_organization_id_id'),
        UniqueConstraint('organization_id', 'code', name='uq_branches_organization_id_code'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_head_office: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    normalized_email: Mapped[str | None] = mapped_column(String(254), Computed('lower(email)', persisted=True), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class OrganizationMember(Base):
    __tablename__ = 'organization_members'
    __table_args__ = (
        CheckConstraint("member_status IN ('invited','active','disabled','removed')", name='ck_organization_members_member_status_0'),
        UniqueConstraint('organization_id', 'id', name='uq_organization_members_organization_id_id'),
        UniqueConstraint('organization_id', 'user_id', name='uq_organization_members_organization_id_user_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='RESTRICT'), nullable=False)
    member_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'invited'"))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class Role(Base):
    __tablename__ = 'roles'
    __table_args__ = (
        UniqueConstraint('organization_id', 'role_key', name='uq_roles_organization_id_role_key'),
        UniqueConstraint('organization_id', 'id', name='uq_roles_organization_id_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    role_key: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    permission_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    module_key: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)


class RolePermission(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'role_id'], ['app.roles.organization_id', 'app.roles.id'], ondelete='CASCADE', name='fk_role_permissions_organization_id_role_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.permissions.id', ondelete='CASCADE'), primary_key=True, nullable=False)


class MemberRole(Base):
    __tablename__ = 'member_roles'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'member_id'], ['app.organization_members.organization_id', 'app.organization_members.id'], ondelete='CASCADE', name='fk_member_roles_organization_id_member_id'),
        ForeignKeyConstraint(['organization_id', 'role_id'], ['app.roles.organization_id', 'app.roles.id'], ondelete='CASCADE', name='fk_member_roles_organization_id_role_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class MemberBranch(Base):
    __tablename__ = 'member_branches'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'member_id'], ['app.organization_members.organization_id', 'app.organization_members.id'], ondelete='CASCADE', name='fk_member_branches_organization_id_member_id'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='CASCADE', name='fk_member_branches_organization_id_branch_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)


class Module(Base):
    __tablename__ = 'modules'
    __table_args__ = {"schema": "app"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    module_key: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class SubscriptionPlan(Base):
    __tablename__ = 'subscription_plans'
    __table_args__ = (
        CheckConstraint("billing_interval IN ('monthly','quarterly','yearly','custom')", name='ck_subscription_plans_billing_interval_0'),
        CheckConstraint('price >= 0', name='ck_subscription_plans_price_1'),
        CheckConstraint('max_members IS NULL OR max_members > 0', name='ck_subscription_plans_max_members_2'),
        CheckConstraint('max_branches IS NULL OR max_branches > 0', name='ck_subscription_plans_max_branches_3'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    plan_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    billing_interval: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    max_members: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    max_branches: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class PlanModule(Base):
    __tablename__ = 'plan_modules'
    __table_args__ = {"schema": "app"}

    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.subscription_plans.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.modules.id', ondelete='RESTRICT'), primary_key=True, nullable=False)


class OrganizationSubscription(Base):
    __tablename__ = 'organization_subscriptions'
    __table_args__ = (
        CheckConstraint("subscription_status IN ('trialing','active','past_due','suspended','cancelled','expired')", name='ck_organization_subscriptions_subscription_status_0'),
        UniqueConstraint('organization_id', 'id', name='uq_organization_subscriptions_organization_id_id'),
        CheckConstraint('ends_at IS NULL OR ends_at > starts_at', name='ck_organization_subscriptions_1'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.subscription_plans.id', ondelete='RESTRICT'), nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(20), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class OrganizationModuleOverride(Base):
    __tablename__ = 'organization_module_overrides'
    __table_args__ = {"schema": "app"}

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.modules.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class SubscriptionPayment(Base):
    __tablename__ = 'subscription_payments'
    __table_args__ = (
        CheckConstraint('amount >= 0', name='ck_subscription_payments_amount_0'),
        CheckConstraint("payment_status IN ('pending','paid','failed','refunded')", name='ck_subscription_payments_payment_status_1'),
        ForeignKeyConstraint(['organization_id', 'subscription_id'], ['app.organization_subscriptions.organization_id', 'app.organization_subscriptions.id'], ondelete='RESTRICT', name='fk_subscription_payments_organization_id_subscription_id'),
        UniqueConstraint('provider', 'provider_reference', name='uq_subscription_payments_provider_provider_reference'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(60), nullable=True)
    provider_reference: Mapped[str | None] = mapped_column(String(160), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class StatusGroup(Base):
    __tablename__ = 'status_groups'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_status_groups_organization_id_id'),
        UniqueConstraint('organization_id', 'module_key', 'entity_key', name='uq_status_groups_organization_id_module_key_entity_key'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    module_key: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class StatusDefinition(Base):
    __tablename__ = 'status_definitions'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_status_definitions_organization_id_id'),
        UniqueConstraint('organization_id', 'status_group_id', 'status_key', name='uq_status_definitions_organization_id_status_group_id_status_ke'),
        ForeignKeyConstraint(['organization_id', 'status_group_id'], ['app.status_groups.organization_id', 'app.status_groups.id'], ondelete='CASCADE', name='fk_status_definitions_organization_id_status_group_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status_key: Mapped[str] = mapped_column(String(60), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    is_initial: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    is_final: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class StatusTransition(Base):
    __tablename__ = 'status_transitions'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'status_group_id'], ['app.status_groups.organization_id', 'app.status_groups.id'], ondelete='CASCADE', name='fk_status_transitions_organization_id_status_group_id'),
        ForeignKeyConstraint(['organization_id', 'from_status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='CASCADE', name='fk_status_transitions_organization_id_from_status_id'),
        ForeignKeyConstraint(['organization_id', 'to_status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='CASCADE', name='fk_status_transitions_organization_id_to_status_id'),
        CheckConstraint('from_status_id <> to_status_id', name='ck_status_transitions_4'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    status_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    from_status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    to_status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    requires_permission: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class WorkflowDefinition(Base):
    __tablename__ = 'workflow_definitions'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_workflow_definitions_organization_id_id'),
        UniqueConstraint('organization_id', 'workflow_key', name='uq_workflow_definitions_organization_id_workflow_key'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    workflow_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    module_key: Mapped[str] = mapped_column(String(60), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class WorkflowStep(Base):
    __tablename__ = 'workflow_steps'
    __table_args__ = (
        UniqueConstraint('organization_id', 'workflow_id', 'step_order', name='uq_workflow_steps_organization_id_workflow_id_step_order'),
        ForeignKeyConstraint(['organization_id', 'workflow_id'], ['app.workflow_definitions.organization_id', 'app.workflow_definitions.id'], ondelete='CASCADE', name='fk_workflow_steps_organization_id_workflow_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_workflow_steps_organization_id_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer(), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class StatusHistory(Base):
    __tablename__ = 'status_history'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'from_status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_status_history_organization_id_from_status_id'),
        ForeignKeyConstraint(['organization_id', 'to_status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_status_history_organization_id_to_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    module_key: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    from_status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    to_status_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text(), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class CustomerSource(Base):
    __tablename__ = 'customer_sources'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_customer_sources_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_customer_sources_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Customer(Base):
    __tablename__ = 'customers'
    __table_args__ = (
        CheckConstraint("customer_type IN ('individual','business')", name='ck_customers_customer_type_0'),
        CheckConstraint('credit_limit >= 0', name='ck_customers_credit_limit_1'),
        UniqueConstraint('organization_id', 'id', name='uq_customers_organization_id_id'),
        UniqueConstraint('organization_id', 'customer_code', name='uq_customers_organization_id_customer_code'),
        ForeignKeyConstraint(['organization_id', 'source_id'], ['app.customer_sources.organization_id', 'app.customer_sources.id'], ondelete='RESTRICT', name='fk_customers_organization_id_source_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    customer_code: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'business'"))
    display_name: Mapped[str] = mapped_column(String(180), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tax_registration_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class CustomerContact(Base):
    __tablename__ = 'customer_contacts'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='CASCADE', name='fk_customer_contacts_organization_id_customer_id'),
        UniqueConstraint('organization_id', 'id', name='uq_customer_contacts_organization_id_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))


class CustomerAddress(Base):
    __tablename__ = 'customer_addresses'
    __table_args__ = (
        CheckConstraint("address_type IN ('billing','shipping','other')", name='ck_customer_addresses_address_type_0'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='CASCADE', name='fk_customer_addresses_organization_id_customer_id'),
        UniqueConstraint('organization_id', 'id', name='uq_customer_addresses_organization_id_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    address_type: Mapped[str] = mapped_column(String(20), nullable=False)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))


class LeadSource(Base):
    __tablename__ = 'lead_sources'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_lead_sources_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_lead_sources_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Lead(Base):
    __tablename__ = 'leads'
    __table_args__ = (
        CheckConstraint('estimated_value IS NULL OR estimated_value >= 0', name='ck_leads_estimated_value_0'),
        UniqueConstraint('organization_id', 'id', name='uq_leads_organization_id_id'),
        UniqueConstraint('organization_id', 'lead_code', name='uq_leads_organization_id_lead_code'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_leads_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'source_id'], ['app.lead_sources.organization_id', 'app.lead_sources.id'], ondelete='RESTRICT', name='fk_leads_organization_id_source_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_leads_organization_id_status_id'),
        ForeignKeyConstraint(['organization_id', 'converted_customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='RESTRICT', name='fk_leads_organization_id_converted_customer_id'),
        ForeignKeyConstraint(['assigned_to'], ['app.users.id'], ondelete='SET NULL', name='fk_leads_assigned_to'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    lead_code: Mapped[str] = mapped_column(String(50), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    converted_customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    lost_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class Opportunity(Base):
    __tablename__ = 'opportunities'
    __table_args__ = (
        CheckConstraint('expected_value >= 0', name='ck_opportunities_expected_value_0'),
        CheckConstraint('probability BETWEEN 0 AND 100', name='ck_opportunities_probability_1'),
        UniqueConstraint('organization_id', 'id', name='uq_opportunities_organization_id_id'),
        UniqueConstraint('organization_id', 'opportunity_code', name='uq_opportunities_organization_id_opportunity_code'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='RESTRICT', name='fk_opportunities_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'lead_id'], ['app.leads.organization_id', 'app.leads.id'], ondelete='RESTRICT', name='fk_opportunities_organization_id_lead_id'),
        ForeignKeyConstraint(['organization_id', 'stage_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_opportunities_organization_id_stage_id'),
        CheckConstraint('customer_id IS NOT NULL OR lead_id IS NOT NULL', name='ck_opportunities_5'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    opportunity_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    stage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    expected_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    expected_close_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class Activity(Base):
    __tablename__ = 'activities'
    __table_args__ = (
        CheckConstraint("activity_type IN ('call','email','meeting','task','note','other')", name='ck_activities_activity_type_0'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_activities_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='CASCADE', name='fk_activities_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'lead_id'], ['app.leads.organization_id', 'app.leads.id'], ondelete='CASCADE', name='fk_activities_organization_id_lead_id'),
        ForeignKeyConstraint(['organization_id', 'opportunity_id'], ['app.opportunities.organization_id', 'app.opportunities.id'], ondelete='CASCADE', name='fk_activities_organization_id_opportunity_id'),
        CheckConstraint('num_nonnulls(customer_id, lead_id, opportunity_id) >= 1', name='ck_activities_4'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class CustomerNote(Base):
    __tablename__ = 'customer_notes'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='CASCADE', name='fk_customer_notes_organization_id_customer_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    note: Mapped[str] = mapped_column(Text(), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class Tag(Base):
    __tablename__ = 'tags'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_tags_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_tags_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)


class CustomerTag(Base):
    __tablename__ = 'customer_tags'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='CASCADE', name='fk_customer_tags_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'tag_id'], ['app.tags.organization_id', 'app.tags.id'], ondelete='CASCADE', name='fk_customer_tags_organization_id_tag_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)


class Unit(Base):
    __tablename__ = 'units'
    __table_args__ = (
        CheckConstraint('decimal_places BETWEEN 0 AND 6', name='ck_units_decimal_places_0'),
        UniqueConstraint('organization_id', 'id', name='uq_units_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_units_organization_id_name'),
        UniqueConstraint('organization_id', 'symbol', name='uq_units_organization_id_symbol'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    decimal_places: Mapped[int] = mapped_column(SmallInteger(), nullable=False, server_default=text('2'))


class ProductCategory(Base):
    __tablename__ = 'product_categories'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_product_categories_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_product_categories_organization_id_name'),
        ForeignKeyConstraint(['organization_id', 'parent_id'], ['app.product_categories.organization_id', 'app.product_categories.id'], ondelete='RESTRICT', name='fk_product_categories_organization_id_parent_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class Brand(Base):
    __tablename__ = 'brands'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_brands_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_brands_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)


class Product(Base):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint("product_type IN ('stock','service','non_stock')", name='ck_products_product_type_0'),
        CheckConstraint('purchase_price >= 0', name='ck_products_purchase_price_1'),
        CheckConstraint('selling_price >= 0', name='ck_products_selling_price_2'),
        CheckConstraint('reorder_level >= 0', name='ck_products_reorder_level_3'),
        UniqueConstraint('organization_id', 'id', name='uq_products_organization_id_id'),
        UniqueConstraint('organization_id', 'sku', name='uq_products_organization_id_sku'),
        ForeignKeyConstraint(['organization_id', 'category_id'], ['app.product_categories.organization_id', 'app.product_categories.id'], ondelete='RESTRICT', name='fk_products_organization_id_category_id'),
        ForeignKeyConstraint(['organization_id', 'brand_id'], ['app.brands.organization_id', 'app.brands.id'], ondelete='RESTRICT', name='fk_products_organization_id_brand_id'),
        ForeignKeyConstraint(['organization_id', 'unit_id'], ['app.units.organization_id', 'app.units.id'], ondelete='RESTRICT', name='fk_products_organization_id_unit_id'),
        CheckConstraint("product_type <> 'service' OR track_inventory = false", name='ck_products_5'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'stock'"))
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    track_inventory: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class ProductVariant(Base):
    __tablename__ = 'product_variants'
    __table_args__ = (
        CheckConstraint('selling_price IS NULL OR selling_price >= 0', name='ck_product_variants_selling_price_0'),
        UniqueConstraint('organization_id', 'id', name='uq_product_variants_organization_id_id'),
        UniqueConstraint('organization_id', 'variant_sku', name='uq_product_variants_organization_id_variant_sku'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='CASCADE', name='fk_product_variants_organization_id_product_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_sku: Mapped[str] = mapped_column(String(80), nullable=False)
    variant_name: Mapped[str] = mapped_column(String(120), nullable=False)
    attributes: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'{}'::jsonb"))
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    selling_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class Supplier(Base):
    __tablename__ = 'suppliers'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_suppliers_organization_id_id'),
        UniqueConstraint('organization_id', 'supplier_code', name='uq_suppliers_organization_id_supplier_code'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    supplier_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tax_registration_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class SupplierAddress(Base):
    __tablename__ = 'supplier_addresses'
    __table_args__ = (
        CheckConstraint("address_type IN ('billing','shipping','other')", name='ck_supplier_addresses_address_type_0'),
        ForeignKeyConstraint(['organization_id', 'supplier_id'], ['app.suppliers.organization_id', 'app.suppliers.id'], ondelete='CASCADE', name='fk_supplier_addresses_organization_id_supplier_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    address_type: Mapped[str] = mapped_column(String(20), nullable=False)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)


class Warehouse(Base):
    __tablename__ = 'warehouses'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_warehouses_organization_id_id'),
        UniqueConstraint('organization_id', 'code', name='uq_warehouses_organization_id_code'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_warehouses_organization_id_branch_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class StockBalance(Base):
    __tablename__ = 'stock_balances'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_stock_balances_organization_id_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_stock_balances_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_stock_balances_organization_id_variant_id'),
        CheckConstraint('quantity_reserved >= 0', name='ck_stock_balances_3'),
        CheckConstraint('quantity_on_hand >= quantity_reserved', name='ck_stock_balances_4'),
        CheckConstraint('average_cost >= 0', name='ck_stock_balances_5'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    quantity_available: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), Computed('quantity_on_hand - quantity_reserved', persisted=True), nullable=True)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class StockMovement(Base):
    __tablename__ = 'stock_movements'
    __table_args__ = (
        CheckConstraint("movement_type IN\n        ('opening','purchase_receipt','sale','sales_return','purchase_return','adjustment','transfer_in','transfer_out')", name='ck_stock_movements_movement_type_0'),
        CheckConstraint('quantity_delta <> 0', name='ck_stock_movements_quantity_delta_1'),
        CheckConstraint('unit_cost >= 0', name='ck_stock_movements_unit_cost_2'),
        ForeignKeyConstraint(['organization_id', 'warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_stock_movements_organization_id_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_stock_movements_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_stock_movements_organization_id_variant_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    source_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)


class StockAdjustment(Base):
    __tablename__ = 'stock_adjustments'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_stock_adjustments_organization_id_id'),
        UniqueConstraint('organization_id', 'adjustment_no', name='uq_stock_adjustments_organization_id_adjustment_no'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_stock_adjustments_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_stock_adjustments_organization_id_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_stock_adjustments_organization_id_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    adjustment_no: Mapped[str] = mapped_column(String(50), nullable=False)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    adjusted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)


class StockAdjustmentItem(Base):
    __tablename__ = 'stock_adjustment_items'
    __table_args__ = (
        CheckConstraint('counted_quantity >= 0', name='ck_stock_adjustment_items_counted_quantity_0'),
        ForeignKeyConstraint(['organization_id', 'adjustment_id'], ['app.stock_adjustments.organization_id', 'app.stock_adjustments.id'], ondelete='CASCADE', name='fk_stock_adjustment_items_organization_id_adjustment_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_stock_adjustment_items_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_stock_adjustment_items_organization_id_variant_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    adjustment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    counted_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    system_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)


class StockTransfer(Base):
    __tablename__ = 'stock_transfers'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_stock_transfers_organization_id_id'),
        UniqueConstraint('organization_id', 'transfer_no', name='uq_stock_transfers_organization_id_transfer_no'),
        ForeignKeyConstraint(['organization_id', 'from_warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_stock_transfers_organization_id_from_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'to_warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_stock_transfers_organization_id_to_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_stock_transfers_organization_id_status_id'),
        CheckConstraint('from_warehouse_id <> to_warehouse_id', name='ck_stock_transfers_5'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    transfer_no: Mapped[str] = mapped_column(String(50), nullable=False)
    from_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)


class StockTransferItem(Base):
    __tablename__ = 'stock_transfer_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_stock_transfer_items_quantity_0'),
        ForeignKeyConstraint(['organization_id', 'transfer_id'], ['app.stock_transfers.organization_id', 'app.stock_transfers.id'], ondelete='CASCADE', name='fk_stock_transfer_items_organization_id_transfer_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_stock_transfer_items_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_stock_transfer_items_organization_id_variant_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    transfer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)


class PurchaseOrder(Base):
    __tablename__ = 'purchase_orders'
    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='ck_purchase_orders_subtotal_0'),
        CheckConstraint('tax_total >= 0', name='ck_purchase_orders_tax_total_1'),
        CheckConstraint('discount_total >= 0', name='ck_purchase_orders_discount_total_2'),
        CheckConstraint('grand_total >= 0', name='ck_purchase_orders_grand_total_3'),
        UniqueConstraint('organization_id', 'id', name='uq_purchase_orders_organization_id_id'),
        UniqueConstraint('organization_id', 'po_number', name='uq_purchase_orders_organization_id_po_number'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_purchase_orders_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'supplier_id'], ['app.suppliers.organization_id', 'app.suppliers.id'], ondelete='RESTRICT', name='fk_purchase_orders_organization_id_supplier_id'),
        ForeignKeyConstraint(['organization_id', 'warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_purchase_orders_organization_id_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_purchase_orders_organization_id_status_id'),
        CheckConstraint('expected_date IS NULL OR expected_date >= order_date', name='ck_purchase_orders_6'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    order_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    expected_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class PurchaseOrderItem(Base):
    __tablename__ = 'purchase_order_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_purchase_order_items_quantity_0'),
        CheckConstraint('received_quantity >= 0', name='ck_purchase_order_items_received_quantity_1'),
        CheckConstraint('unit_cost >= 0', name='ck_purchase_order_items_unit_cost_2'),
        CheckConstraint('tax_rate BETWEEN 0 AND 100', name='ck_purchase_order_items_tax_rate_3'),
        CheckConstraint('line_total >= 0', name='ck_purchase_order_items_line_total_4'),
        UniqueConstraint('organization_id', 'id', name='uq_purchase_order_items_organization_id_id'),
        ForeignKeyConstraint(['organization_id', 'purchase_order_id'], ['app.purchase_orders.organization_id', 'app.purchase_orders.id'], ondelete='CASCADE', name='fk_purchase_order_items_organization_id_purchase_order_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_purchase_order_items_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_purchase_order_items_organization_id_variant_id'),
        CheckConstraint('received_quantity <= quantity', name='ck_purchase_order_items_4'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, server_default=text('0'))
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class GoodsReceipt(Base):
    __tablename__ = 'goods_receipts'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_goods_receipts_organization_id_id'),
        UniqueConstraint('organization_id', 'receipt_no', name='uq_goods_receipts_organization_id_receipt_no'),
        ForeignKeyConstraint(['organization_id', 'purchase_order_id'], ['app.purchase_orders.organization_id', 'app.purchase_orders.id'], ondelete='RESTRICT', name='fk_goods_receipts_organization_id_purchase_order_id'),
        ForeignKeyConstraint(['organization_id', 'supplier_id'], ['app.suppliers.organization_id', 'app.suppliers.id'], ondelete='RESTRICT', name='fk_goods_receipts_organization_id_supplier_id'),
        ForeignKeyConstraint(['organization_id', 'warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_goods_receipts_organization_id_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_goods_receipts_organization_id_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    receipt_no: Mapped[str] = mapped_column(String(50), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    received_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)


class GoodsReceiptItem(Base):
    __tablename__ = 'goods_receipt_items'
    __table_args__ = (
        CheckConstraint('quantity_received > 0', name='ck_goods_receipt_items_quantity_received_0'),
        CheckConstraint('unit_cost >= 0', name='ck_goods_receipt_items_unit_cost_1'),
        ForeignKeyConstraint(['organization_id', 'goods_receipt_id'], ['app.goods_receipts.organization_id', 'app.goods_receipts.id'], ondelete='CASCADE', name='fk_goods_receipt_items_organization_id_goods_receipt_id'),
        ForeignKeyConstraint(['organization_id', 'purchase_order_item_id'], ['app.purchase_order_items.organization_id', 'app.purchase_order_items.id'], ondelete='RESTRICT', name='fk_goods_receipt_items_organization_id_purchase_order_item_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_goods_receipt_items_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_goods_receipt_items_organization_id_variant_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    goods_receipt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    purchase_order_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, server_default=text('0'))


class BillingSettings(Base):
    __tablename__ = 'billing_settings'
    __table_args__ = (
        CheckConstraint('default_payment_terms_days >= 0', name='ck_billing_settings_default_payment_terms_days_0'),
        CheckConstraint('default_due_days >= 0', name='ck_billing_settings_default_due_days_1'),
        CheckConstraint('decimal_places BETWEEN 0 AND 4', name='ck_billing_settings_decimal_places_2'),
        CheckConstraint("rounding_method IN ('half_up','half_even','up','down')", name='ck_billing_settings_rounding_method_3'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    default_currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    tax_inclusive_pricing: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    allow_partial_payment: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    allow_overpayment: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    default_payment_terms_days: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    default_due_days: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('15'))
    decimal_places: Mapped[int] = mapped_column(SmallInteger(), nullable=False, server_default=text('2'))
    rounding_method: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'half_up'"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class DocumentSequence(Base):
    __tablename__ = 'document_sequences'
    __table_args__ = (
        CheckConstraint('next_number > 0', name='ck_document_sequences_next_number_0'),
        CheckConstraint('padding BETWEEN 1 AND 12', name='ck_document_sequences_padding_1'),
        CheckConstraint("reset_period IN ('never','yearly','monthly')", name='ck_document_sequences_reset_period_2'),
        UniqueConstraint('organization_id', 'id', name='uq_document_sequences_organization_id_id'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='CASCADE', name='fk_document_sequences_organization_id_branch_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    document_type: Mapped[str] = mapped_column(String(40), nullable=False)
    prefix: Mapped[str] = mapped_column(String(30), nullable=False)
    suffix: Mapped[str | None] = mapped_column(String(30), nullable=True)
    next_number: Mapped[int] = mapped_column(BigInteger(), nullable=False, server_default=text('1'))
    padding: Mapped[int] = mapped_column(SmallInteger(), nullable=False, server_default=text('5'))
    reset_period: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'never'"))
    last_reset_key: Mapped[str | None] = mapped_column(String(20), nullable=True)


class TaxRate(Base):
    __tablename__ = 'tax_rates'
    __table_args__ = (
        CheckConstraint('rate BETWEEN 0 AND 100', name='ck_tax_rates_rate_0'),
        CheckConstraint("tax_type IN ('percentage','fixed')", name='ck_tax_rates_tax_type_1'),
        UniqueConstraint('organization_id', 'id', name='uq_tax_rates_organization_id_id'),
        UniqueConstraint('organization_id', 'tax_code', name='uq_tax_rates_organization_id_tax_code'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    tax_code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'percentage'"))
    is_compound: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class TaxGroup(Base):
    __tablename__ = 'tax_groups'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_tax_groups_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_tax_groups_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class TaxGroupRate(Base):
    __tablename__ = 'tax_group_rates'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'tax_group_id'], ['app.tax_groups.organization_id', 'app.tax_groups.id'], ondelete='CASCADE', name='fk_tax_group_rates_organization_id_tax_group_id'),
        ForeignKeyConstraint(['organization_id', 'tax_rate_id'], ['app.tax_rates.organization_id', 'app.tax_rates.id'], ondelete='RESTRICT', name='fk_tax_group_rates_organization_id_tax_rate_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tax_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tax_rate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))


class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_payment_methods_organization_id_id'),
        UniqueConstraint('organization_id', 'method_key', name='uq_payment_methods_organization_id_method_key'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    method_key: Mapped[str] = mapped_column(String(40), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class InvoiceTemplate(Base):
    __tablename__ = 'invoice_templates'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_invoice_templates_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_invoice_templates_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    template_config: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'{}'::jsonb"))
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class Quotation(Base):
    __tablename__ = 'quotations'
    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='ck_quotations_subtotal_0'),
        CheckConstraint('discount_total >= 0', name='ck_quotations_discount_total_1'),
        CheckConstraint('tax_total >= 0', name='ck_quotations_tax_total_2'),
        CheckConstraint('grand_total >= 0', name='ck_quotations_grand_total_3'),
        UniqueConstraint('organization_id', 'id', name='uq_quotations_organization_id_id'),
        UniqueConstraint('organization_id', 'quotation_no', name='uq_quotations_organization_id_quotation_no'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_quotations_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='RESTRICT', name='fk_quotations_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_quotations_organization_id_status_id'),
        CheckConstraint('valid_until IS NULL OR valid_until >= quotation_date', name='ck_quotations_5'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    quotation_no: Mapped[str] = mapped_column(String(50), nullable=False)
    quotation_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    valid_until: Mapped[date | None] = mapped_column(Date(), nullable=True)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class QuotationItem(Base):
    __tablename__ = 'quotation_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_quotation_items_quantity_0'),
        CheckConstraint('unit_price >= 0', name='ck_quotation_items_unit_price_1'),
        CheckConstraint('discount_amount >= 0', name='ck_quotation_items_discount_amount_2'),
        CheckConstraint('tax_rate BETWEEN 0 AND 100', name='ck_quotation_items_tax_rate_3'),
        CheckConstraint('line_total >= 0', name='ck_quotation_items_line_total_4'),
        ForeignKeyConstraint(['organization_id', 'quotation_id'], ['app.quotations.organization_id', 'app.quotations.id'], ondelete='CASCADE', name='fk_quotation_items_organization_id_quotation_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_quotation_items_organization_id_product_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    quotation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, server_default=text('0'))
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class SalesOrder(Base):
    __tablename__ = 'sales_orders'
    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='ck_sales_orders_subtotal_0'),
        CheckConstraint('discount_total >= 0', name='ck_sales_orders_discount_total_1'),
        CheckConstraint('tax_total >= 0', name='ck_sales_orders_tax_total_2'),
        CheckConstraint('grand_total >= 0', name='ck_sales_orders_grand_total_3'),
        UniqueConstraint('organization_id', 'id', name='uq_sales_orders_organization_id_id'),
        UniqueConstraint('organization_id', 'order_no', name='uq_sales_orders_organization_id_order_no'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_sales_orders_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='RESTRICT', name='fk_sales_orders_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'quotation_id'], ['app.quotations.organization_id', 'app.quotations.id'], ondelete='RESTRICT', name='fk_sales_orders_organization_id_quotation_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_sales_orders_organization_id_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    quotation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    order_no: Mapped[str] = mapped_column(String(50), nullable=False)
    order_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class SalesOrderItem(Base):
    __tablename__ = 'sales_order_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_sales_order_items_quantity_0'),
        CheckConstraint('unit_price >= 0', name='ck_sales_order_items_unit_price_1'),
        CheckConstraint('discount_amount >= 0', name='ck_sales_order_items_discount_amount_2'),
        CheckConstraint('tax_rate BETWEEN 0 AND 100', name='ck_sales_order_items_tax_rate_3'),
        CheckConstraint('line_total >= 0', name='ck_sales_order_items_line_total_4'),
        ForeignKeyConstraint(['organization_id', 'sales_order_id'], ['app.sales_orders.organization_id', 'app.sales_orders.id'], ondelete='CASCADE', name='fk_sales_order_items_organization_id_sales_order_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_sales_order_items_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_sales_order_items_organization_id_variant_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sales_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, server_default=text('0'))
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class SalesInvoice(Base):
    __tablename__ = 'sales_invoices'
    __table_args__ = (
        CheckConstraint('exchange_rate > 0', name='ck_sales_invoices_exchange_rate_0'),
        CheckConstraint('subtotal >= 0', name='ck_sales_invoices_subtotal_1'),
        CheckConstraint('discount_total >= 0', name='ck_sales_invoices_discount_total_2'),
        CheckConstraint('tax_total >= 0', name='ck_sales_invoices_tax_total_3'),
        CheckConstraint('shipping_amount >= 0', name='ck_sales_invoices_shipping_amount_4'),
        CheckConstraint('grand_total >= 0', name='ck_sales_invoices_grand_total_5'),
        CheckConstraint('amount_paid >= 0', name='ck_sales_invoices_amount_paid_6'),
        UniqueConstraint('organization_id', 'id', name='uq_sales_invoices_organization_id_id'),
        UniqueConstraint('organization_id', 'invoice_no', name='uq_sales_invoices_organization_id_invoice_no'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_sales_invoices_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='RESTRICT', name='fk_sales_invoices_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'sales_order_id'], ['app.sales_orders.organization_id', 'app.sales_orders.id'], ondelete='RESTRICT', name='fk_sales_invoices_organization_id_sales_order_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_sales_invoices_organization_id_status_id'),
        CheckConstraint('due_date IS NULL OR due_date >= invoice_date', name='ck_sales_invoices_6'),
        CheckConstraint('amount_paid <= grand_total', name='ck_sales_invoices_7'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sales_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    invoice_no: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    due_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    balance_due: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), Computed('grand_total - amount_paid', persisted=True), nullable=True)
    billing_snapshot: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'{}'::jsonb"))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class SalesInvoiceItem(Base):
    __tablename__ = 'sales_invoice_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_sales_invoice_items_quantity_0'),
        CheckConstraint('unit_price >= 0', name='ck_sales_invoice_items_unit_price_1'),
        CheckConstraint('discount_amount >= 0', name='ck_sales_invoice_items_discount_amount_2'),
        CheckConstraint('tax_amount >= 0', name='ck_sales_invoice_items_tax_amount_3'),
        CheckConstraint('line_total >= 0', name='ck_sales_invoice_items_line_total_4'),
        UniqueConstraint('organization_id', 'id', name='uq_sales_invoice_items_organization_id_id'),
        ForeignKeyConstraint(['organization_id', 'invoice_id'], ['app.sales_invoices.organization_id', 'app.sales_invoices.id'], ondelete='CASCADE', name='fk_sales_invoice_items_organization_id_invoice_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_sales_invoice_items_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_sales_invoice_items_organization_id_variant_id'),
        ForeignKeyConstraint(['organization_id', 'warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_sales_invoice_items_organization_id_warehouse_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class InvoiceItemTax(Base):
    __tablename__ = 'invoice_item_taxes'
    __table_args__ = (
        CheckConstraint('taxable_amount >= 0', name='ck_invoice_item_taxes_taxable_amount_0'),
        CheckConstraint('tax_amount >= 0', name='ck_invoice_item_taxes_tax_amount_1'),
        ForeignKeyConstraint(['organization_id', 'invoice_item_id'], ['app.sales_invoice_items.organization_id', 'app.sales_invoice_items.id'], ondelete='CASCADE', name='fk_invoice_item_taxes_organization_id_invoice_item_id'),
        ForeignKeyConstraint(['organization_id', 'tax_rate_id'], ['app.tax_rates.organization_id', 'app.tax_rates.id'], ondelete='RESTRICT', name='fk_invoice_item_taxes_organization_id_tax_rate_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    invoice_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    tax_rate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class Payment(Base):
    __tablename__ = 'payments'
    __table_args__ = (
        CheckConstraint("payment_direction IN ('in','out')", name='ck_payments_payment_direction_0'),
        CheckConstraint('amount > 0', name='ck_payments_amount_1'),
        CheckConstraint("payment_status IN ('pending','completed','failed','refunded','void')", name='ck_payments_payment_status_2'),
        UniqueConstraint('organization_id', 'id', name='uq_payments_organization_id_id'),
        UniqueConstraint('organization_id', 'payment_no', name='uq_payments_organization_id_payment_no'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_payments_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='RESTRICT', name='fk_payments_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'supplier_id'], ['app.suppliers.organization_id', 'app.suppliers.id'], ondelete='RESTRICT', name='fk_payments_organization_id_supplier_id'),
        ForeignKeyConstraint(['organization_id', 'payment_method_id'], ['app.payment_methods.organization_id', 'app.payment_methods.id'], ondelete='RESTRICT', name='fk_payments_organization_id_payment_method_id'),
        CheckConstraint("(payment_direction = 'in' AND customer_id IS NOT NULL AND supplier_id IS NULL) OR (payment_direction = 'out' AND supplier_id IS NOT NULL AND customer_id IS NULL)", name='ck_payments_6'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payment_no: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_direction: Mapped[str] = mapped_column(String(10), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    payment_method_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reference_no: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'completed'"))
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    received_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class InvoicePayment(Base):
    __tablename__ = 'invoice_payments'
    __table_args__ = (
        CheckConstraint('amount_applied > 0', name='ck_invoice_payments_amount_applied_0'),
        ForeignKeyConstraint(['organization_id', 'invoice_id'], ['app.sales_invoices.organization_id', 'app.sales_invoices.id'], ondelete='RESTRICT', name='fk_invoice_payments_organization_id_invoice_id'),
        ForeignKeyConstraint(['organization_id', 'payment_id'], ['app.payments.organization_id', 'app.payments.id'], ondelete='RESTRICT', name='fk_invoice_payments_organization_id_payment_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    amount_applied: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class PurchaseInvoice(Base):
    __tablename__ = 'purchase_invoices'
    __table_args__ = (
        CheckConstraint('subtotal >= 0', name='ck_purchase_invoices_subtotal_0'),
        CheckConstraint('tax_total >= 0', name='ck_purchase_invoices_tax_total_1'),
        CheckConstraint('grand_total >= 0', name='ck_purchase_invoices_grand_total_2'),
        CheckConstraint('amount_paid >= 0', name='ck_purchase_invoices_amount_paid_3'),
        UniqueConstraint('organization_id', 'id', name='uq_purchase_invoices_organization_id_id'),
        UniqueConstraint('organization_id', 'purchase_invoice_no', name='uq_purchase_invoices_organization_id_purchase_invoice_no'),
        ForeignKeyConstraint(['organization_id', 'supplier_id'], ['app.suppliers.organization_id', 'app.suppliers.id'], ondelete='RESTRICT', name='fk_purchase_invoices_organization_id_supplier_id'),
        ForeignKeyConstraint(['organization_id', 'goods_receipt_id'], ['app.goods_receipts.organization_id', 'app.goods_receipts.id'], ondelete='RESTRICT', name='fk_purchase_invoices_organization_id_goods_receipt_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_purchase_invoices_organization_id_status_id'),
        CheckConstraint('amount_paid <= grand_total', name='ck_purchase_invoices_5'),
        CheckConstraint('due_date IS NULL OR due_date >= invoice_date', name='ck_purchase_invoices_6'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    goods_receipt_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    vendor_invoice_no: Mapped[str | None] = mapped_column(String(80), nullable=True)
    purchase_invoice_no: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    due_date: Mapped[date | None] = mapped_column(Date(), nullable=True)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    balance_due: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), Computed('grand_total - amount_paid', persisted=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class PurchaseInvoiceItem(Base):
    __tablename__ = 'purchase_invoice_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_purchase_invoice_items_quantity_0'),
        CheckConstraint('unit_cost >= 0', name='ck_purchase_invoice_items_unit_cost_1'),
        CheckConstraint('tax_amount >= 0', name='ck_purchase_invoice_items_tax_amount_2'),
        CheckConstraint('line_total >= 0', name='ck_purchase_invoice_items_line_total_3'),
        ForeignKeyConstraint(['organization_id', 'purchase_invoice_id'], ['app.purchase_invoices.organization_id', 'app.purchase_invoices.id'], ondelete='CASCADE', name='fk_purchase_invoice_items_organization_id_purchase_invoice_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_purchase_invoice_items_organization_id_product_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    purchase_invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class SupplierPayment(Base):
    __tablename__ = 'supplier_payments'
    __table_args__ = (
        CheckConstraint('amount_applied > 0', name='ck_supplier_payments_amount_applied_0'),
        ForeignKeyConstraint(['organization_id', 'purchase_invoice_id'], ['app.purchase_invoices.organization_id', 'app.purchase_invoices.id'], ondelete='RESTRICT', name='fk_supplier_payments_organization_id_purchase_invoice_id'),
        ForeignKeyConstraint(['organization_id', 'payment_id'], ['app.payments.organization_id', 'app.payments.id'], ondelete='RESTRICT', name='fk_supplier_payments_organization_id_payment_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    purchase_invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    amount_applied: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)


class SalesReturn(Base):
    __tablename__ = 'sales_returns'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_sales_returns_organization_id_id'),
        UniqueConstraint('organization_id', 'return_no', name='uq_sales_returns_organization_id_return_no'),
        ForeignKeyConstraint(['organization_id', 'invoice_id'], ['app.sales_invoices.organization_id', 'app.sales_invoices.id'], ondelete='RESTRICT', name='fk_sales_returns_organization_id_invoice_id'),
        ForeignKeyConstraint(['organization_id', 'warehouse_id'], ['app.warehouses.organization_id', 'app.warehouses.id'], ondelete='RESTRICT', name='fk_sales_returns_organization_id_warehouse_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_sales_returns_organization_id_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    return_no: Mapped[str] = mapped_column(String(50), nullable=False)
    return_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class SalesReturnItem(Base):
    __tablename__ = 'sales_return_items'
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_sales_return_items_quantity_0'),
        CheckConstraint('refund_amount >= 0', name='ck_sales_return_items_refund_amount_1'),
        ForeignKeyConstraint(['organization_id', 'sales_return_id'], ['app.sales_returns.organization_id', 'app.sales_returns.id'], ondelete='CASCADE', name='fk_sales_return_items_organization_id_sales_return_id'),
        ForeignKeyConstraint(['organization_id', 'invoice_item_id'], ['app.sales_invoice_items.organization_id', 'app.sales_invoice_items.id'], ondelete='RESTRICT', name='fk_sales_return_items_organization_id_invoice_item_id'),
        ForeignKeyConstraint(['organization_id', 'product_id'], ['app.products.organization_id', 'app.products.id'], ondelete='RESTRICT', name='fk_sales_return_items_organization_id_product_id'),
        ForeignKeyConstraint(['organization_id', 'variant_id'], ['app.product_variants.organization_id', 'app.product_variants.id'], ondelete='RESTRICT', name='fk_sales_return_items_organization_id_variant_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sales_return_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    invoice_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    restock: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class CreditNote(Base):
    __tablename__ = 'credit_notes'
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_credit_notes_amount_0'),
        UniqueConstraint('organization_id', 'id', name='uq_credit_notes_organization_id_id'),
        UniqueConstraint('organization_id', 'credit_note_no', name='uq_credit_notes_organization_id_credit_note_no'),
        ForeignKeyConstraint(['organization_id', 'customer_id'], ['app.customers.organization_id', 'app.customers.id'], ondelete='RESTRICT', name='fk_credit_notes_organization_id_customer_id'),
        ForeignKeyConstraint(['organization_id', 'invoice_id'], ['app.sales_invoices.organization_id', 'app.sales_invoices.id'], ondelete='RESTRICT', name='fk_credit_notes_organization_id_invoice_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_credit_notes_organization_id_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    credit_note_no: Mapped[str] = mapped_column(String(50), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class ExpenseCategory(Base):
    __tablename__ = 'expense_categories'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_expense_categories_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_expense_categories_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class Expense(Base):
    __tablename__ = 'expenses'
    __table_args__ = (
        CheckConstraint('amount >= 0', name='ck_expenses_amount_0'),
        CheckConstraint('tax_amount >= 0', name='ck_expenses_tax_amount_1'),
        UniqueConstraint('organization_id', 'id', name='uq_expenses_organization_id_id'),
        UniqueConstraint('organization_id', 'expense_no', name='uq_expenses_organization_id_expense_no'),
        ForeignKeyConstraint(['organization_id', 'branch_id'], ['app.branches.organization_id', 'app.branches.id'], ondelete='RESTRICT', name='fk_expenses_organization_id_branch_id'),
        ForeignKeyConstraint(['organization_id', 'category_id'], ['app.expense_categories.organization_id', 'app.expense_categories.id'], ondelete='RESTRICT', name='fk_expenses_organization_id_category_id'),
        ForeignKeyConstraint(['organization_id', 'status_id'], ['app.status_definitions.organization_id', 'app.status_definitions.id'], ondelete='RESTRICT', name='fk_expenses_organization_id_status_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    branch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    expense_no: Mapped[str] = mapped_column(String(50), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date(), nullable=False, server_default=text('current_date'))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, server_default=text('0'))
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default=text("'INR'"))
    vendor_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class Dashboard(Base):
    __tablename__ = 'dashboards'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_dashboards_organization_id_id'),
        UniqueConstraint('organization_id', 'name', name='uq_dashboards_organization_id_name'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('false'))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class ReportDefinition(Base):
    __tablename__ = 'report_definitions'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_report_definitions_organization_id_id'),
        UniqueConstraint('organization_id', 'report_key', name='uq_report_definitions_organization_id_report_key'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    report_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    module_key: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    query_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    default_config: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class DashboardWidget(Base):
    __tablename__ = 'dashboard_widgets'
    __table_args__ = (
        CheckConstraint("widget_type IN ('number','bar','line','pie','table','list')", name='ck_dashboard_widgets_widget_type_0'),
        CheckConstraint('width_units BETWEEN 1 AND 12', name='ck_dashboard_widgets_width_units_1'),
        CheckConstraint('height_units > 0', name='ck_dashboard_widgets_height_units_2'),
        ForeignKeyConstraint(['organization_id', 'dashboard_id'], ['app.dashboards.organization_id', 'app.dashboards.id'], ondelete='CASCADE', name='fk_dashboard_widgets_organization_id_dashboard_id'),
        ForeignKeyConstraint(['organization_id', 'report_id'], ['app.report_definitions.organization_id', 'app.report_definitions.id'], ondelete='RESTRICT', name='fk_dashboard_widgets_organization_id_report_id'),
        UniqueConstraint('organization_id', 'dashboard_id', 'widget_key', name='uq_dashboard_widgets_organization_id_dashboard_id_widget_key'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    report_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    widget_key: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    widget_type: Mapped[str] = mapped_column(String(30), nullable=False)
    position_x: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    position_y: Mapped[int] = mapped_column(Integer(), nullable=False, server_default=text('0'))
    width_units: Mapped[int] = mapped_column(SmallInteger(), nullable=False, server_default=text('4'))
    height_units: Mapped[int] = mapped_column(SmallInteger(), nullable=False, server_default=text('3'))
    config: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'{}'::jsonb"))


class KpiDefinition(Base):
    __tablename__ = 'kpi_definitions'
    __table_args__ = (
        CheckConstraint("aggregation IN ('count','sum','avg','min','max','ratio')", name='ck_kpi_definitions_aggregation_0'),
        UniqueConstraint('organization_id', 'id', name='uq_kpi_definitions_organization_id_id'),
        UniqueConstraint('organization_id', 'kpi_key', name='uq_kpi_definitions_organization_id_kpi_key'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    kpi_key: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    source_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    aggregation: Mapped[str] = mapped_column(String(30), nullable=False)
    format_key: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'number'"))
    config: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))


class AnalysisSettings(Base):
    __tablename__ = 'analysis_settings'
    __table_args__ = (
        CheckConstraint('fiscal_year_start_month BETWEEN 1 AND 12', name='ck_analysis_settings_fiscal_year_start_month_0'),
        ForeignKeyConstraint(['organization_id', 'default_dashboard_id'], ['app.dashboards.organization_id', 'app.dashboards.id'], ondelete='RESTRICT', name='fk_analysis_settings_organization_id_default_dashboard_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    default_date_range: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'this_month'"))
    fiscal_year_start_month: Mapped[int] = mapped_column(SmallInteger(), nullable=False, server_default=text('4'))
    default_dashboard_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'Asia/Kolkata'"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'), onupdate=func.now())


class SavedReport(Base):
    __tablename__ = 'saved_reports'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_saved_reports_organization_id_id'),
        ForeignKeyConstraint(['organization_id', 'report_id'], ['app.report_definitions.organization_id', 'app.report_definitions.id'], ondelete='CASCADE', name='fk_saved_reports_organization_id_report_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    filters: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class ReportSchedule(Base):
    __tablename__ = 'report_schedules'
    __table_args__ = (
        CheckConstraint("output_format IN ('pdf','xlsx','csv')", name='ck_report_schedules_output_format_0'),
        UniqueConstraint('organization_id', 'id', name='uq_report_schedules_organization_id_id'),
        ForeignKeyConstraint(['organization_id', 'report_id'], ['app.report_definitions.organization_id', 'app.report_definitions.id'], ondelete='CASCADE', name='fk_report_schedules_organization_id_report_id'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    schedule_name: Mapped[str] = mapped_column(String(120), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'Asia/Kolkata'"))
    output_format: Mapped[str] = mapped_column(String(10), nullable=False, server_default=text("'pdf'"))
    recipients: Mapped[Any] = mapped_column(JSONB(), nullable=False, server_default=text("'[]'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default=text('true'))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class ReportAccess(Base):
    __tablename__ = 'report_access'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'report_id'], ['app.report_definitions.organization_id', 'app.report_definitions.id'], ondelete='CASCADE', name='fk_report_access_organization_id_report_id'),
        ForeignKeyConstraint(['organization_id', 'role_id'], ['app.roles.organization_id', 'app.roles.id'], ondelete='CASCADE', name='fk_report_access_organization_id_role_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    report_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)


class DashboardAccess(Base):
    __tablename__ = 'dashboard_access'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id', 'dashboard_id'], ['app.dashboards.organization_id', 'app.dashboards.id'], ondelete='CASCADE', name='fk_dashboard_access_organization_id_dashboard_id'),
        ForeignKeyConstraint(['organization_id', 'role_id'], ['app.roles.organization_id', 'app.roles.id'], ondelete='CASCADE', name='fk_dashboard_access_organization_id_role_id'),
        {"schema": "app"},
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    __table_args__ = {"schema": "app"}

    id: Mapped[int] = mapped_column(BigInteger(), Identity(), primary_key=True, nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='SET NULL'), nullable=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET(), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text(), nullable=True)
    before_data: Mapped[Any | None] = mapped_column(JSONB(), nullable=True)
    after_data: Mapped[Any | None] = mapped_column(JSONB(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


class FileAttachment(Base):
    __tablename__ = 'file_attachments'
    __table_args__ = (
        CheckConstraint('file_size_bytes IS NULL OR file_size_bytes >= 0', name='ck_file_attachments_file_size_bytes_0'),
        {"schema": "app"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'), default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('app.organizations.id', ondelete='CASCADE'), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text(), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('app.users.id', ondelete='SET NULL'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text('now()'))


GENERATED_MODELS = {
    'organizations': Organization,
    'organization_addresses': OrganizationAddress,
    'branches': Branch,
    'users': User,
    'organization_members': OrganizationMember,
    'roles': Role,
    'permissions': Permission,
    'role_permissions': RolePermission,
    'member_roles': MemberRole,
    'member_branches': MemberBranch,
    'modules': Module,
    'subscription_plans': SubscriptionPlan,
    'plan_modules': PlanModule,
    'organization_subscriptions': OrganizationSubscription,
    'organization_module_overrides': OrganizationModuleOverride,
    'subscription_payments': SubscriptionPayment,
    'status_groups': StatusGroup,
    'status_definitions': StatusDefinition,
    'status_transitions': StatusTransition,
    'workflow_definitions': WorkflowDefinition,
    'workflow_steps': WorkflowStep,
    'status_history': StatusHistory,
    'customer_sources': CustomerSource,
    'customers': Customer,
    'customer_contacts': CustomerContact,
    'customer_addresses': CustomerAddress,
    'lead_sources': LeadSource,
    'leads': Lead,
    'opportunities': Opportunity,
    'activities': Activity,
    'customer_notes': CustomerNote,
    'tags': Tag,
    'customer_tags': CustomerTag,
    'units': Unit,
    'product_categories': ProductCategory,
    'brands': Brand,
    'products': Product,
    'product_variants': ProductVariant,
    'suppliers': Supplier,
    'supplier_addresses': SupplierAddress,
    'warehouses': Warehouse,
    'stock_balances': StockBalance,
    'stock_movements': StockMovement,
    'stock_adjustments': StockAdjustment,
    'stock_adjustment_items': StockAdjustmentItem,
    'stock_transfers': StockTransfer,
    'stock_transfer_items': StockTransferItem,
    'purchase_orders': PurchaseOrder,
    'purchase_order_items': PurchaseOrderItem,
    'goods_receipts': GoodsReceipt,
    'goods_receipt_items': GoodsReceiptItem,
    'billing_settings': BillingSettings,
    'document_sequences': DocumentSequence,
    'tax_rates': TaxRate,
    'tax_groups': TaxGroup,
    'tax_group_rates': TaxGroupRate,
    'payment_methods': PaymentMethod,
    'invoice_templates': InvoiceTemplate,
    'quotations': Quotation,
    'quotation_items': QuotationItem,
    'sales_orders': SalesOrder,
    'sales_order_items': SalesOrderItem,
    'sales_invoices': SalesInvoice,
    'sales_invoice_items': SalesInvoiceItem,
    'invoice_item_taxes': InvoiceItemTax,
    'payments': Payment,
    'invoice_payments': InvoicePayment,
    'purchase_invoices': PurchaseInvoice,
    'purchase_invoice_items': PurchaseInvoiceItem,
    'supplier_payments': SupplierPayment,
    'sales_returns': SalesReturn,
    'sales_return_items': SalesReturnItem,
    'credit_notes': CreditNote,
    'expense_categories': ExpenseCategory,
    'expenses': Expense,
    'dashboards': Dashboard,
    'report_definitions': ReportDefinition,
    'dashboard_widgets': DashboardWidget,
    'kpi_definitions': KpiDefinition,
    'analysis_settings': AnalysisSettings,
    'saved_reports': SavedReport,
    'report_schedules': ReportSchedule,
    'report_access': ReportAccess,
    'dashboard_access': DashboardAccess,
    'audit_logs': AuditLog,
    'file_attachments': FileAttachment,
}
