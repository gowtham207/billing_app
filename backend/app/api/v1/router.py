from fastapi import APIRouter

from app.api.v1 import (
    access,
    admin,
    auth,
    billing,
    common,
    crm,
    dashboard,
    dashboards,
    expenses,
    inventory,
    organizations,
    purchasing,
    reports,
    subscriptions,
    workflows,
)

api_router = APIRouter()
for module in (
    auth,
    admin,
    organizations,
    subscriptions,
    access,
    workflows,
    crm,
    inventory,
    purchasing,
    billing,
    expenses,
    dashboard,
    dashboards,
    reports,
    common,
):
    api_router.include_router(module.router)
