from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from prisma import Prisma
from backend.app.db import get_db
from backend.app.schemas.client import ClientCreate, ClientUpdate, ClientOut

router = APIRouter(prefix="/api/clients", tags=["Clients"])

def populate_client_balances(client) -> dict:
    total_invoiced = 0.0
    total_paid = 0.0
    balance_due = 0.0
    invoices = getattr(client, "invoices", []) or []
    
    for inv in invoices:
        if inv.status != "CANCELLED":
            total_invoiced += inv.total_amount
            total_paid += inv.paid_amount
            balance_due += inv.balance_due

    return {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "company": client.company,
        "address": client.address,
        "tax_id": client.tax_id,
        "created_at": client.created_at,
        "updated_at": client.updated_at,
        "total_invoiced": round(total_invoiced, 2),
        "total_paid": round(total_paid, 2),
        "balance_due": round(balance_due, 2),
        "invoice_count": len(invoices),
    }

@router.get("", response_model=List[ClientOut])
async def get_clients(
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    db: Prisma = Depends(get_db)
):
    where = None
    if search:
        where = {
            "OR": [
                {"name": {"contains": search, "mode": "insensitive"}},
                {"email": {"contains": search, "mode": "insensitive"}},
                {"company": {"contains": search, "mode": "insensitive"}},
            ]
        }
    
    clients = await db.client.find_many(
        where=where,
        include={"invoices": True},
        order={"name": "asc"}
    )
    return [populate_client_balances(c) for c in clients]

@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(client_in: ClientCreate, db: Prisma = Depends(get_db)):
    client = await db.client.create(
        data=client_in.model_dump(),
        include={"invoices": True}
    )
    return populate_client_balances(client)

@router.get("/{client_id}", response_model=ClientOut)
async def get_client(client_id: int, db: Prisma = Depends(get_db)):
    client = await db.client.find_unique(
        where={"id": client_id},
        include={"invoices": True}
    )
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return populate_client_balances(client)

@router.put("/{client_id}", response_model=ClientOut)
async def update_client(client_id: int, client_in: ClientUpdate, db: Prisma = Depends(get_db)):
    existing = await db.client.find_unique(where={"id": client_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = client_in.model_dump(exclude_unset=True)
    client = await db.client.update(
        where={"id": client_id},
        data=update_data,
        include={"invoices": True}
    )
    return populate_client_balances(client)

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_id: int, db: Prisma = Depends(get_db)):
    existing = await db.client.find_unique(where={"id": client_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Client not found")
    await db.client.delete(where={"id": client_id})
    return None
