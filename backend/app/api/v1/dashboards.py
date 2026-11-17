import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.api.v1.mount import mount_collection, mount_item
from app.core.deps import Context, get_db, require_org, require_write
from app.models import Dashboard, DashboardWidget
from app.schemas.generated import DashboardCreate, DashboardRead, DashboardUpdate, DashboardWidgetRead, DashboardWidgetUpdate
from app.schemas.requests import LayoutUpdate
from app.services.common import create_model, get_scoped

router = APIRouter(prefix="/dashboards", tags=["Dashboard Builder"])


class WidgetIn(BaseModel):
    report_id: uuid.UUID | None = None
    widget_key: str
    title: str
    widget_type: Literal["number", "bar", "line", "pie", "table", "list"]
    position_x: int = 0
    position_y: int = 0
    width_units: int = 4
    height_units: int = 3
    config: dict = {}


@router.put("/widgets/{widget_id}", response_model=DashboardWidgetRead)
def update_widget(widget_id: uuid.UUID, body: DashboardWidgetUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    row = get_scoped(db, DashboardWidget, widget_id, ctx.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.delete("/widgets/{widget_id}", status_code=204)
def delete_widget(widget_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    db.delete(get_scoped(db, DashboardWidget, widget_id, ctx.organization_id))
    db.flush()
    return None


mount_collection(
    router,
    name="dashboards",
    path="/",
    model=Dashboard,
    read=DashboardRead,
    create=DashboardCreate,
    tag="Dashboard Builder",
    search=("name",),
    permission="reports.read",
)
mount_item(
    router,
    name="dashboards",
    path="/",
    model=Dashboard,
    read=DashboardRead,
    update=DashboardUpdate,
    tag="Dashboard Builder",
    permission="reports.read",
)


@router.post("/{id}/set-default", response_model=DashboardRead)
def set_default(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    row = get_scoped(db, Dashboard, id, ctx.organization_id)
    db.execute(update(Dashboard).where(Dashboard.organization_id == ctx.organization_id).values(is_default=False))
    db.flush()
    row.is_default = True
    db.flush()
    db.refresh(row)
    return row


@router.get("/{id}/widgets", response_model=list[DashboardWidgetRead])
def list_widgets(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Dashboard, id, ctx.organization_id)
    from sqlalchemy import select

    return db.scalars(
        select(DashboardWidget).where(DashboardWidget.organization_id == ctx.organization_id, DashboardWidget.dashboard_id == id)
    ).all()


@router.post("/{id}/widgets", response_model=DashboardWidgetRead, status_code=201)
def add_widget(id: uuid.UUID, body: WidgetIn, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    get_scoped(db, Dashboard, id, ctx.organization_id)
    data = body.model_dump()
    data.update(organization_id=ctx.organization_id, dashboard_id=id)
    return create_model(db, DashboardWidget, data, ctx, "dashboard_widgets")


@router.put("/{id}/layout")
def save_layout(id: uuid.UUID, body: LayoutUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    get_scoped(db, Dashboard, id, ctx.organization_id)
    for item in body.widgets:
        row = get_scoped(db, DashboardWidget, item.id, ctx.organization_id)
        if row.dashboard_id != id:
            continue
        row.position_x = item.position_x
        row.position_y = item.position_y
        row.width_units = item.width_units
        row.height_units = item.height_units
    db.flush()
    return {"dashboard_id": id, "widgets": [item.model_dump() for item in body.widgets]}
