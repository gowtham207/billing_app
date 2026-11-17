import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.deps import Context, get_db, require_org, require_write
from app.schemas.base import Page
from app.services.common import apply_update, create_model, delete_model, get_scoped, paginate


def mount_collection(
    router: APIRouter,
    *,
    name: str,
    path: str,
    model,
    read,
    create,
    tag: str,
    search: tuple[str, ...] = (),
    permission: str | None = None,
    include_list: bool = True,
):
    collection = "/" if path in {"", "/"} else path

    def list_items(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        q: str | None = None,
        is_active: bool | None = None,
        db: Session = Depends(get_db),
        ctx: Context = Depends(require_org),
    ):
        filters = []
        if is_active is not None and hasattr(model, "is_active"):
            filters.append(model.is_active.is_(is_active))
        return paginate(
            db,
            model,
            ctx.organization_id,
            page=page,
            page_size=page_size,
            q=q,
            search_fields=search,
            filters=filters,
        )

    if include_list:
        list_items.__name__ = f"{name}_list"
        router.add_api_route(collection, list_items, methods=["GET"], response_model=Page[read], tags=[tag], name=f"{name}_list")

    if create is not None:

        def create_item(body: create, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
            require_write(ctx, permission)
            data = body.model_dump(exclude_unset=True)
            if hasattr(model, "organization_id"):
                data["organization_id"] = ctx.organization_id
            if hasattr(model, "created_by") and "created_by" not in data:
                data["created_by"] = ctx.user.id
            return create_model(db, model, data, ctx, model.__tablename__)

        create_item.__name__ = f"{name}_create"
        router.add_api_route(
            collection,
            create_item,
            methods=["POST"],
            response_model=read,
            status_code=201,
            tags=[tag],
            name=f"{name}_create",
        )


def mount_item(
    router: APIRouter,
    *,
    name: str,
    path: str,
    model,
    read,
    update,
    tag: str,
    permission: str | None = None,
    can_get: bool = True,
    can_update: bool = True,
    can_delete: bool = True,
):
    item = "/{id}" if path in {"", "/"} else f"{path}/{{id}}"

    if can_get:

        def get_item(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
            return get_scoped(db, model, id, ctx.organization_id)

        get_item.__name__ = f"{name}_get"
        router.add_api_route(item, get_item, methods=["GET"], response_model=read, tags=[tag], name=f"{name}_get")

    if can_update and update is not None:

        def update_item(
            id: uuid.UUID,
            body: update,
            db: Session = Depends(get_db),
            ctx: Context = Depends(require_org),
        ):
            require_write(ctx, permission)
            obj = get_scoped(db, model, id, ctx.organization_id)
            return apply_update(db, obj, body.model_dump(exclude_unset=True), ctx)

        update_item.__name__ = f"{name}_update"
        router.add_api_route(item, update_item, methods=["PUT"], response_model=read, tags=[tag], name=f"{name}_update")

    if can_delete:

        def delete_item(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
            require_write(ctx, permission)
            delete_model(db, get_scoped(db, model, id, ctx.organization_id), ctx)
            return Response(status_code=204)

        delete_item.__name__ = f"{name}_delete"
        router.add_api_route(item, delete_item, methods=["DELETE"], status_code=204, tags=[tag], name=f"{name}_delete")
