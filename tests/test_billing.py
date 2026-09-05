import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_clients_crud(client):
    res = client.post("/api/clients", json={
        "name": "Prisma Test Client",
        "email": "prisma@client.io",
        "company": "Prisma Innovations",
        "phone": "+1 555 9988",
        "address": "Prisma Road, Suite 10",
        "tax_id": "TAX-PRISMA-1"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Prisma Test Client"
    client_id = data["id"]

    # Retrieve
    get_res = client.get(f"/api/clients/{client_id}")
    assert get_res.status_code == 200
    assert get_res.json()["company"] == "Prisma Innovations"

    # List
    list_res = client.get("/api/clients?search=Prisma")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

import uuid

def test_products_crud(client):
    unique_sku = f"SRV-PG-{uuid.uuid4().hex[:8]}"
    res = client.post("/api/products", json={
        "name": "PostgreSQL Optimization Retainer",
        "sku": unique_sku,
        "description": "Postgres indexing, connection pooling, and performance tuning",
        "unit_price": 450.0,
        "tax_rate": 10.0,
        "unit": "month"
    })
    assert res.status_code == 201
    data = res.json()
    assert "PostgreSQL" in data["name"]
    prod_id = data["id"]

    # Get
    p_get = client.get(f"/api/products/{prod_id}")
    assert p_get.status_code == 200
    assert p_get.json()["unit_price"] == 450.0

def test_invoice_creation_and_payment_workflow(client):
    # 1. Create client
    c_res = client.post("/api/clients", json={"name": "Prisma Invoicing Test Client"})
    assert c_res.status_code == 201
    client_id = c_res.json()["id"]

    # 2. Create invoice: 2 items
    # item 1: 2 x 200 = 400, tax 10% = 40 => 440
    # item 2: 1 x 600 = 600, tax 0% => 600
    # subtotal = 1000, tax = 40, total = 1040
    due_date = (date.today() + timedelta(days=14)).isoformat()
    inv_res = client.post("/api/invoices", json={
        "client_id": client_id,
        "due_date": due_date,
        "discount_type": "PERCENTAGE",
        "discount_value": 0.0,
        "items": [
            {"description": "Consulting Block A", "quantity": 2.0, "unit_price": 200.0, "tax_rate": 10.0, "discount": 0.0},
            {"description": "Architecture Design", "quantity": 1.0, "unit_price": 600.0, "tax_rate": 0.0, "discount": 0.0}
        ]
    })
    assert inv_res.status_code == 201
    inv_data = inv_res.json()
    assert inv_data["subtotal"] == 1000.0
    assert inv_data["tax_amount"] == 40.0
    assert inv_data["total_amount"] == 1040.0
    assert inv_data["balance_due"] == 1040.0
    assert inv_data["status"] == "SENT"
    invoice_id = inv_data["id"]

    # 3. Partial payment of $400
    p1_res = client.post("/api/payments", json={
        "invoice_id": invoice_id,
        "amount": 400.0,
        "payment_method": "BANK_TRANSFER",
        "reference_number": "WIRE-PRISMA-01"
    })
    assert p1_res.status_code == 201
    assert p1_res.json()["amount"] == 400.0

    check_inv = client.get(f"/api/invoices/{invoice_id}").json()
    assert check_inv["paid_amount"] == 400.0
    assert check_inv["balance_due"] == 640.0
    assert check_inv["status"] == "PARTIAL"

    # 4. Settle remainder $640
    p2_res = client.post("/api/payments", json={
        "invoice_id": invoice_id,
        "amount": 640.0,
        "payment_method": "CARD"
    })
    assert p2_res.status_code == 201

    check_inv2 = client.get(f"/api/invoices/{invoice_id}").json()
    assert check_inv2["paid_amount"] == 1040.0
    assert check_inv2["balance_due"] == 0.0
    assert check_inv2["status"] == "PAID"

def test_analytics_and_print_view(client):
    # Analytics
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] > 0
    assert data["total_invoiced"] > 0
    assert "invoices_by_status" in data

    # Printable invoice view
    invoices = client.get("/api/invoices").json()
    assert len(invoices) > 0
    first_id = invoices[0]["id"]
    print_res = client.get(f"/invoices/{first_id}/print")
    assert print_res.status_code == 200
    assert "Invoice" in print_res.text
