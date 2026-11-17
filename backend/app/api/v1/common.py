import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import Context, get_db, require_org, require_write
from app.models import AnalysisSettings, AuditLog, BillingSettings, FileAttachment, Notification, Organization
from app.schemas.generated import AnalysisSettingsUpdate, AuditLogRead, BillingSettingsUpdate, FileAttachmentRead, OrganizationUpdate
from app.services.common import apply_update, get_scoped, paginate

router = APIRouter(tags=["Common"])
MAX_UPLOAD = 20 * 1024 * 1024


class SettingsUpdate(BaseModel):
    organization: OrganizationUpdate | None = None
    billing: BillingSettingsUpdate | None = None
    analysis: AnalysisSettingsUpdate | None = None


def _root() -> Path:
    root = Path(settings.upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_path(storage_key: str) -> Path:
    root = _root()
    path = (root / storage_key).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(status_code=400, detail="Invalid attachment path")
    return path


@router.get("/audit-logs")
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_org),
):
    stmt = select(AuditLog).where(AuditLog.organization_id == ctx.organization_id).order_by(AuditLog.created_at.desc())
    rows = db.scalars(stmt).all()
    start = (page - 1) * page_size
    items = [AuditLogRead.model_validate(row).model_dump(mode="json") for row in rows[start : start + page_size]]
    return {"items": items, "total": len(rows), "page": page, "page_size": page_size}


@router.get("/attachments")
def list_attachments(
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_org),
):
    filters = []
    if entity_type:
        filters.append(FileAttachment.entity_type == entity_type)
    if entity_id:
        filters.append(FileAttachment.entity_id == entity_id)
    return paginate(db, FileAttachment, ctx.organization_id, page=page, page_size=page_size, filters=filters)


@router.post("/attachments", response_model=FileAttachmentRead, status_code=201)
async def upload_attachment(
    entity_type: str = Form(...),
    entity_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_org),
):
    payload = await file.read()
    if len(payload) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="File is larger than 20 MB")
    suffix = Path(file.filename or "file").suffix[:16]
    stored_name = f"{uuid.uuid4()}{suffix}"
    relative = f"{ctx.organization_id}/{stored_name}"
    destination = _safe_path(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    row = FileAttachment(
        organization_id=ctx.organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        storage_key=relative,
        original_filename=(file.filename or stored_name)[:255],
        content_type=file.content_type,
        file_size_bytes=len(payload),
        uploaded_by=ctx.user.id,
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


@router.get("/attachments/{id}", response_model=FileAttachmentRead)
def get_attachment(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, FileAttachment, id, ctx.organization_id)


@router.get("/attachments/{id}/download")
def download_attachment(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    row = get_scoped(db, FileAttachment, id, ctx.organization_id)
    path = _safe_path(row.storage_key)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File is missing")
    return FileResponse(path, media_type=row.content_type or "application/octet-stream", filename=row.original_filename)


@router.delete("/attachments/{id}", status_code=204)
def delete_attachment(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, None)
    row = get_scoped(db, FileAttachment, id, ctx.organization_id)
    path = _safe_path(row.storage_key)
    if path.is_file():
        path.unlink()
    db.delete(row)
    db.flush()
    return None


@router.get("/notifications")
def list_notifications(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(
        select(Notification).where(Notification.user_id == ctx.user.id).order_by(Notification.created_at.desc())
    ).all()
    start = (page - 1) * page_size
    return {"items": rows[start : start + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.patch("/notifications/{id}/read")
def mark_read(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    row = db.get(Notification, id)
    if row is None or row.user_id != ctx.user.id:
        raise HTTPException(status_code=404, detail="Not found")
    row.is_read = True
    db.flush()
    db.refresh(row)
    return row


def _settings(db: Session, organization_id):
    organization = db.get(Organization, organization_id)
    billing = db.get(BillingSettings, organization_id)
    analysis = db.get(AnalysisSettings, organization_id)
    if billing is None:
        billing = BillingSettings(organization_id=organization_id)
        db.add(billing)
        db.flush()
    if analysis is None:
        analysis = AnalysisSettings(organization_id=organization_id)
        db.add(analysis)
        db.flush()
    return organization, billing, analysis


@router.get("/settings")
def get_settings(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    organization, billing, analysis = _settings(db, ctx.organization_id)
    return {"organization": organization, "billing": billing, "analysis": analysis}


@router.put("/settings")
def update_settings(body: SettingsUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, "settings.write")
    organization, billing, analysis = _settings(db, ctx.organization_id)
    if body.organization is not None:
        data = body.organization.model_dump(exclude_unset=True)
        data.pop("code", None)
        data.pop("status", None)
        apply_update(db, organization, data, ctx)
    if body.billing is not None:
        apply_update(db, billing, body.billing.model_dump(exclude_unset=True), ctx)
    if body.analysis is not None:
        apply_update(db, analysis, body.analysis.model_dump(exclude_unset=True), ctx)
    return {"organization": organization, "billing": billing, "analysis": analysis}
