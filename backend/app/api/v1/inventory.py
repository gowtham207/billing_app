import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.mount import mount_collection, mount_item
from app.core.deps import Context, get_db, require_org, require_write
from app.models import Brand, Product, ProductCategory, ProductVariant, StockAdjustment, StockBalance, StockMovement, StockTransfer, Unit, Warehouse
from app.schemas.generated import (
    BrandCreate,
    BrandRead,
    ProductCategoryCreate,
    ProductCategoryRead,
    ProductCategoryUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantRead,
    ProductVariantUpdate,
    StockAdjustmentRead,
    StockMovementRead,
    StockTransferRead,
    UnitCreate,
    UnitRead,
    WarehouseCreate,
    WarehouseRead,
    WarehouseUpdate,
)
from app.schemas.base import Page
from app.schemas.requests import AdjustmentCreateRequest, OpeningStockRequest, TransferCreateRequest
from app.services.common import apply_movement, create_model, get_scoped, paginate, set_status, status_key
from app.services.documents import complete_transfer, create_adjustment, create_transfer, post_adjustment
from app.services.reports import inventory_rows, low_stock

router = APIRouter(prefix="/inventory")
P = "inventory.write"

class CategoryBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None = None


class ProductWithCategory(ProductRead):
    category: CategoryBrief | None = None


def _product_view(db: Session, product: Product) -> dict:
    payload = ProductRead.model_validate(product).model_dump()
    if product.category_id is None:
        payload["category"] = None
        return payload
    category = get_scoped(db, ProductCategory, product.category_id, product.organization_id)
    payload["category"] = CategoryBrief.model_validate(category).model_dump()
    return payload


@router.get("/products", response_model=Page[ProductWithCategory], tags=["Inventory - Products & Catalog"])
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    is_active: bool | None = None,
    category_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_org),
):
    filters = []
    if is_active is not None:
        filters.append(Product.is_active.is_(is_active))
    if category_id is not None:
        get_scoped(db, ProductCategory, category_id, ctx.organization_id)
        filters.append(Product.category_id == category_id)
    result = paginate(
        db,
        Product,
        ctx.organization_id,
        page=page,
        page_size=page_size,
        q=q,
        search_fields=("name", "sku", "barcode"),
        filters=filters,
    )
    result["items"] = [_product_view(db, row) for row in result["items"]]
    return result


@router.get("/products/{id}", response_model=ProductWithCategory, tags=["Inventory - Products & Catalog"])
def get_product(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return _product_view(db, get_scoped(db, Product, id, ctx.organization_id))


mount_collection(
    router,
    name="products",
    path="/products",
    model=Product,
    read=ProductRead,
    create=ProductCreate,
    tag="Inventory - Products & Catalog",
    search=("name", "sku", "barcode"),
    permission=P,
    include_list=False,
)
mount_item(
    router,
    name="products",
    path="/products",
    model=Product,
    read=ProductRead,
    update=ProductUpdate,
    tag="Inventory - Products & Catalog",
    permission=P,
    can_get=False,
)
mount_collection(router, name="categories", path="/categories", model=ProductCategory, read=ProductCategoryRead, create=ProductCategoryCreate, tag="Inventory - Products & Catalog", search=("name",), permission=P)
mount_item(router, name="categories", path="/categories", model=ProductCategory, read=ProductCategoryRead, update=ProductCategoryUpdate, tag="Inventory - Products & Catalog", permission=P)


@router.get("/categories/{id}/products", response_model=Page[ProductWithCategory], tags=["Inventory - Products & Catalog"])
def products_in_category(
    id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    ctx: Context = Depends(require_org),
):
    get_scoped(db, ProductCategory, id, ctx.organization_id)
    result = paginate(
        db,
        Product,
        ctx.organization_id,
        page=page,
        page_size=page_size,
        filters=[Product.category_id == id],
    )
    result["items"] = [_product_view(db, row) for row in result["items"]]
    return result


mount_collection(router, name="brands", path="/brands", model=Brand, read=BrandRead, create=BrandCreate, tag="Inventory - Products & Catalog", search=("name",), permission=P)
mount_collection(router, name="units", path="/units", model=Unit, read=UnitRead, create=UnitCreate, tag="Inventory - Products & Catalog", search=("name", "symbol"), permission=P)
mount_collection(router, name="warehouses", path="/warehouses", model=Warehouse, read=WarehouseRead, create=WarehouseCreate, tag="Inventory - Warehouses & Stock", search=("name", "code"), permission=P)
mount_item(router, name="warehouses", path="/warehouses", model=Warehouse, read=WarehouseRead, update=WarehouseUpdate, tag="Inventory - Warehouses & Stock", permission=P)


@router.get("/products/{id}/variants", response_model=list[ProductVariantRead], tags=["Inventory - Products & Catalog"])
def list_variants(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Product, id, ctx.organization_id)
    return db.scalars(select(ProductVariant).where(ProductVariant.organization_id == ctx.organization_id, ProductVariant.product_id == id)).all()


@router.post("/products/{id}/variants", response_model=ProductVariantRead, status_code=201, tags=["Inventory - Products & Catalog"])
def create_variant(id: uuid.UUID, body: ProductVariantCreate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    get_scoped(db, Product, id, ctx.organization_id)
    data = body.model_dump(exclude_unset=True)
    data.update(organization_id=ctx.organization_id, product_id=id)
    return create_model(db, ProductVariant, data, ctx, "product_variants")


@router.put("/variants/{id}", response_model=ProductVariantRead, tags=["Inventory - Products & Catalog"])
def update_variant(id: uuid.UUID, body: ProductVariantUpdate, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, ProductVariant, id, ctx.organization_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.flush()
    db.refresh(row)
    return row


@router.delete("/variants/{id}", status_code=204, tags=["Inventory - Products & Catalog"])
def delete_variant(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, ProductVariant, id, ctx.organization_id)
    row.is_active = False
    db.flush()
    return None


@router.get("/stock", tags=["Inventory - Warehouses & Stock"])
def stock_overview(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return inventory_rows(db, ctx.organization_id)


@router.get("/stock/product/{product_id}", tags=["Inventory - Warehouses & Stock"])
def product_stock(product_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Product, product_id, ctx.organization_id)
    return db.scalars(select(StockBalance).where(StockBalance.organization_id == ctx.organization_id, StockBalance.product_id == product_id)).all()


@router.get("/stock/warehouse/{warehouse_id}", tags=["Inventory - Warehouses & Stock"])
def warehouse_stock(warehouse_id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    get_scoped(db, Warehouse, warehouse_id, ctx.organization_id)
    return db.scalars(select(StockBalance).where(StockBalance.organization_id == ctx.organization_id, StockBalance.warehouse_id == warehouse_id)).all()


@router.get("/stock/low-stock", tags=["Inventory - Warehouses & Stock"])
def low_stock_products(db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return low_stock(db, ctx.organization_id)


@router.get("/stock/movements", tags=["Inventory - Warehouses & Stock"])
def list_movements(page: int = 1, page_size: int = 50, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(StockMovement).where(StockMovement.organization_id == ctx.organization_id).order_by(StockMovement.occurred_at.desc())).all()
    start = (page - 1) * page_size
    return {"items": rows[start : start + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.get("/stock/movements/{id}", response_model=StockMovementRead, tags=["Inventory - Warehouses & Stock"])
def get_movement(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, StockMovement, id, ctx.organization_id)


@router.post("/stock/opening", status_code=201, tags=["Inventory - Warehouses & Stock"])
def opening_stock(body: OpeningStockRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    get_scoped(db, Warehouse, body.warehouse_id, ctx.organization_id)
    movements = []
    for line in body.lines:
        movements.append(
            apply_movement(
                db,
                organization_id=ctx.organization_id,
                warehouse_id=body.warehouse_id,
                product_id=line.product_id,
                variant_id=line.variant_id,
                movement_type="opening",
                quantity_delta=line.quantity,
                unit_cost=line.unit_cost,
                source_type="opening",
                user_id=ctx.user.id,
            )
        )
    return {"count": len(movements)}


@router.get("/adjustments", tags=["Inventory - Warehouses & Stock"])
def list_adjustments(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(StockAdjustment).where(StockAdjustment.organization_id == ctx.organization_id).order_by(StockAdjustment.adjusted_at.desc())).all()
    start = (page - 1) * page_size
    return {"items": rows[start : start + page_size], "total": len(rows), "page": page, "page_size": page_size}


@router.post("/adjustments", response_model=StockAdjustmentRead, status_code=201, tags=["Inventory - Warehouses & Stock"])
def add_adjustment(body: AdjustmentCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_adjustment(db, ctx, body)


@router.get("/adjustments/{id}", response_model=StockAdjustmentRead, tags=["Inventory - Warehouses & Stock"])
def get_adjustment(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, StockAdjustment, id, ctx.organization_id)


@router.put("/adjustments/{id}", response_model=StockAdjustmentRead, tags=["Inventory - Warehouses & Stock"])
def update_adjustment(id: uuid.UUID, body: AdjustmentCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    current = get_scoped(db, StockAdjustment, id, ctx.organization_id)
    if status_key(db, current.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft adjustments can be edited")
    db.delete(current)
    db.flush()
    return create_adjustment(db, ctx, body)


@router.post("/adjustments/{id}/submit", response_model=StockAdjustmentRead, tags=["Inventory - Warehouses & Stock"])
def submit_adjustment(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, StockAdjustment, id, ctx.organization_id), ctx=ctx, module_key="inventory", entity_key="stock_adjustment", status_key="submitted")


@router.post("/adjustments/{id}/approve", response_model=StockAdjustmentRead, tags=["Inventory - Warehouses & Stock"])
def approve_adjustment(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, StockAdjustment, id, ctx.organization_id), ctx=ctx, module_key="inventory", entity_key="stock_adjustment", status_key="approved")


@router.post("/adjustments/{id}/post", response_model=StockAdjustmentRead, tags=["Inventory - Warehouses & Stock"])
def post_adjustment_route(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return post_adjustment(db, ctx, get_scoped(db, StockAdjustment, id, ctx.organization_id))


@router.get("/transfers", tags=["Inventory - Warehouses & Stock"])
def list_transfers(page: int = 1, page_size: int = 20, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    rows = db.scalars(select(StockTransfer).where(StockTransfer.organization_id == ctx.organization_id).order_by(StockTransfer.requested_at.desc())).all()
    start = (page - 1) * page_size
    return {"items": [StockTransferRead.model_validate(row).model_dump() for row in rows[start : start + page_size]], "total": len(rows), "page": page, "page_size": page_size}


@router.post("/transfers", response_model=StockTransferRead, status_code=201, tags=["Inventory - Warehouses & Stock"])
def add_transfer(body: TransferCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return create_transfer(db, ctx, body)


@router.get("/transfers/{id}", response_model=StockTransferRead, tags=["Inventory - Warehouses & Stock"])
def get_transfer(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    return get_scoped(db, StockTransfer, id, ctx.organization_id)


@router.put("/transfers/{id}", response_model=StockTransferRead, tags=["Inventory - Warehouses & Stock"])
def update_transfer(id: uuid.UUID, body: TransferCreateRequest, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    current = get_scoped(db, StockTransfer, id, ctx.organization_id)
    if status_key(db, current.status_id) not in {None, "draft"}:
        raise HTTPException(status_code=409, detail="Only draft transfers can be edited")
    db.delete(current)
    db.flush()
    return create_transfer(db, ctx, body)


@router.post("/transfers/{id}/approve", response_model=StockTransferRead, tags=["Inventory - Warehouses & Stock"])
def approve_transfer(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return set_status(db, get_scoped(db, StockTransfer, id, ctx.organization_id), ctx=ctx, module_key="inventory", entity_key="stock_transfer", status_key="approved")


@router.post("/transfers/{id}/complete", response_model=StockTransferRead, tags=["Inventory - Warehouses & Stock"])
def finish_transfer(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    return complete_transfer(db, ctx, get_scoped(db, StockTransfer, id, ctx.organization_id))


@router.post("/transfers/{id}/cancel", response_model=StockTransferRead, tags=["Inventory - Warehouses & Stock"])
def cancel_transfer(id: uuid.UUID, db: Session = Depends(get_db), ctx: Context = Depends(require_org)):
    require_write(ctx, P)
    row = get_scoped(db, StockTransfer, id, ctx.organization_id)
    if status_key(db, row.status_id) == "completed":
        raise HTTPException(status_code=409, detail="Completed transfers cannot be cancelled")
    return set_status(db, row, ctx=ctx, module_key="inventory", entity_key="stock_transfer", status_key="cancelled")
