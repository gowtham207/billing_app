import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.mount import mount_collection, mount_item
from app.core.deps import Context, get_db, require_org, require_write
from app.models import KpiDefinition, ReportDefinition, ReportSchedule, SavedReport
from app.schemas.generated import (
    KpiDefinitionRead,
    ReportDefinitionCreate,
    ReportDefinitionRead,
    ReportDefinitionUpdate,
    ReportScheduleCreate,
    ReportScheduleRead,
    ReportScheduleUpdate,
    SavedReportRead,
)
from app.schemas.requests import ReportExecuteRequest, SavedReportCreateRequest
from app.services.common import create_model, delete_model, get_scoped, paginate
from app.services.export import as_csv, as_xlsx
from app.services.pdf import build_pdf
from app.services.reports import REPORTS

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


def _coerce(filters: dict) -> dict:
    data = dict(filters or {})
    for key in ("date_from", "date_to"):
        if isinstance(data.get(key), str) and data[key]:
            data[key] = date.fromisoformat(data[key])
    for key in ("customer_id", "supplier_id"):
        if isinstance(data.get(key), str) and data[key]:
            data[key] = uuid.UUID(data[key])
    return data


def _run(db: Session, organization_id, identifier: str, filters: dict):
    runner = REPORTS.get(identifier)
    if runner is None:
        raise HTTPException(status_code=422, detail="Unknown report")
    return runner(db, organization_id, _coerce(filters))


@router.get("/kpis", response_model=list[KpiDefinitionRead])
def list_kpis(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return db.scalars(select(KpiDefinition).where(KpiDefinition.organization_id == ctx.organization_id).order_by(KpiDefinition.name)).all()


@router.post("/saved", response_model=SavedReportRead, status_code=201)
def save_report(body: SavedReportCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    get_scoped(db, ReportDefinition, body.report_id, ctx.organization_id)
    return create_model(
        db,
        SavedReport,
        {
            "organization_id": ctx.organization_id,
            "report_id": body.report_id,
            "owner_user_id": ctx.user.id,
            "name": body.name,
            "filters": body.filters,
        },
        ctx,
        "saved_reports",
    )


@router.get("/saved")
def list_saved(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return paginate(db, SavedReport, ctx.organization_id, page=page, page_size=page_size, search_fields=("name",))


@router.get("/saved/{id}", response_model=SavedReportRead)
def get_saved(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, SavedReport, id, ctx.organization_id)


@router.delete("/saved/{id}", status_code=204)
def delete_saved(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    delete_model(db, get_scoped(db, SavedReport, id, ctx.organization_id), ctx)
    return None


@router.post("/schedules", response_model=ReportScheduleRead, status_code=201)
def create_schedule(body: ReportScheduleCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    data = body.model_dump(exclude_unset=True)
    data["organization_id"] = ctx.organization_id
    data["created_by"] = ctx.user.id
    get_scoped(db, ReportDefinition, data["report_id"], ctx.organization_id)
    return create_model(db, ReportSchedule, data, ctx, "report_schedules")


@router.get("/schedules")
def list_schedules(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return paginate(db, ReportSchedule, ctx.organization_id, page=page, page_size=page_size, search_fields=("schedule_name",))


@router.put("/schedules/{id}", response_model=ReportScheduleRead)
def update_schedule(id: uuid.UUID, body: ReportScheduleUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    row = get_scoped(db, ReportSchedule, id, ctx.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.delete("/schedules/{id}", status_code=204)
def delete_schedule(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "reports.read")
    delete_model(db, get_scoped(db, ReportSchedule, id, ctx.organization_id), ctx)
    return None


@router.get("/export")
def export_report(
    name: str = Query(...),
    format: str = Query("csv"),
    date_from: date | None = None,
    date_to: date | None = None,
    customer_id: uuid.UUID | None = None,
    supplier_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_org),
):
    rows = _run(
        db,
        ctx.organization_id,
        name,
        {"date_from": date_from, "date_to": date_to, "customer_id": customer_id, "supplier_id": supplier_id},
    )
    if format == "csv":
        return Response(as_csv(rows), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})
    if format == "xlsx":
        return Response(
            as_xlsx(rows),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{name}.xlsx"'},
        )
    if format == "pdf":
        lines = [name, ""]
        for row in rows:
            lines.append(" | ".join(f"{key}: {value}" for key, value in row.items()))
        return Response(build_pdf(lines or [name, "No rows"]), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}.pdf"'})
    raise HTTPException(status_code=422, detail="format must be pdf, xlsx, or csv")


mount_collection(
    router,
    name="report_definitions",
    path="/definitions",
    model=ReportDefinition,
    read=ReportDefinitionRead,
    create=ReportDefinitionCreate,
    tag="Reports & Analytics",
    search=("name", "report_key"),
    permission="reports.read",
)
mount_item(
    router,
    name="report_definitions",
    path="/definitions",
    model=ReportDefinition,
    read=ReportDefinitionRead,
    update=ReportDefinitionUpdate,
    tag="Reports & Analytics",
    permission="reports.read",
    can_delete=False,
)


@router.post("/execute")
def execute_report(body: ReportExecuteRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    identifier = body.report_key
    if body.report_id is not None:
        definition = get_scoped(db, ReportDefinition, body.report_id, ctx.organization_id)
        identifier = definition.query_identifier
    if not identifier:
        raise HTTPException(status_code=422, detail="Provide a report")
    return {"rows": _run(db, ctx.organization_id, identifier, body.filters)}


def _named(name: str):
    def endpoint(
        date_from: date | None = None,
        date_to: date | None = None,
        customer_id: uuid.UUID | None = None,
        supplier_id: uuid.UUID | None = None,
        db: Session = Depends(get_db),
        ctx: Context = Depends(require_org),
    ):
        return _run(
            db,
            ctx.organization_id,
            name,
            {"date_from": date_from, "date_to": date_to, "customer_id": customer_id, "supplier_id": supplier_id},
        )

    endpoint.__name__ = f"report_{name.replace('-', '_')}"
    return endpoint


for _report_name in (
    "sales",
    "purchases",
    "inventory",
    "stock-movement",
    "customer-ledger",
    "supplier-ledger",
    "outstanding",
    "expenses",
    "tax",
    "profit-loss",
):
    router.add_api_route(f"/{_report_name}", _named(_report_name), methods=["GET"], name=f"report_{_report_name}")
