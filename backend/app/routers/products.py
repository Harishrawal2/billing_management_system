from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from prisma import Prisma
from backend.app.db import get_db
from backend.app.schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/api/products", tags=["Products & Services"])

@router.get("", response_model=List[ProductOut])
async def get_products(
    search: Optional[str] = Query(None, description="Search by name, SKU, or description"),
    active_only: bool = Query(True),
    db: Prisma = Depends(get_db)
):
    where = {}
    if active_only:
        where["is_active"] = True
    if search:
        where["OR"] = [
            {"name": {"contains": search, "mode": "insensitive"}},
            {"sku": {"contains": search, "mode": "insensitive"}},
            {"description": {"contains": search, "mode": "insensitive"}},
        ]
        
    products = await db.product.find_many(
        where=where if where else None,
        order={"name": "asc"}
    )
    return products

@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(product_in: ProductCreate, db: Prisma = Depends(get_db)):
    if product_in.sku:
        existing = await db.product.find_unique(where={"sku": product_in.sku})
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
            
    product = await db.product.create(data=product_in.model_dump())
    return product

@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: Prisma = Depends(get_db)):
    product = await db.product.find_unique(where={"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, product_in: ProductUpdate, db: Prisma = Depends(get_db)):
    product = await db.product.find_unique(where={"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_in.sku and product_in.sku != product.sku:
        existing = await db.product.find_unique(where={"sku": product_in.sku})
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")

    update_data = product_in.model_dump(exclude_unset=True)
    updated = await db.product.update(
        where={"id": product_id},
        data=update_data
    )
    return updated

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: Prisma = Depends(get_db)):
    product = await db.product.find_unique(where={"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # Soft delete
    await db.product.update(where={"id": product_id}, data={"is_active": False})
    return None
