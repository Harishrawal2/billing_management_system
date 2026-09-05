# BillMaster - FastAPI Billing & Invoicing Management System (PostgreSQL & Prisma)

A modern, production-grade Billing and Invoicing Management System built with **FastAPI**, **PostgreSQL**, **Prisma** (`prisma-client-py`), and a sleek **Glassmorphic Single-Page Application (SPA)** web frontend.

---

## Key Features

- **Database & ORM**:
  - **PostgreSQL 17** database backend.
  - **Prisma Client Python** with declarative schema in `prisma/schema.prisma`.
  - Type-safe async queries across all endpoints.
- **Client Directory**: Manage client accounts, billing addresses, contact info, and tax/VAT/GSTIN IDs with real-time balance tracking.
- **Product & Service Catalog**: Maintain SKU codes, standard unit prices, tax rates, and billing units (hours, items, months, etc.).
- **Dynamic Invoice Builder**:
  - Auto-generated sequential invoice numbers (e.g. `INV-2026-0001`).
  - Add/remove line items with live auto-fill from catalog.
  - Real-time client-side calculation of line totals, discounts (percentage or fixed), item taxes, and grand totals.
  - Payment terms (`Net 30`, `Net 15`, `Due on Receipt`, etc.).
- **Payments & Reconciliation**:
  - Record full or partial payments with method tracking (Bank Transfer, Card, UPI, Cash, Cheque).
  - Automatic status progression (`DRAFT` → `SENT` → `PARTIAL` → `PAID` / `OVERDUE`).
  - Validation against overpayment.
- **Financial Analytics & Visual Dashboard**:
  - Real-time KPIs: Total Revenue Collected, Total Billed, Outstanding Receivables, Overdue Amount.
  - Interactive Chart.js monthly trend (Billed vs Collected) and invoice status breakdown.
  - Recent activity streams.
- **Printable & PDF-Ready Invoices**:
  - Executive layout with company branding, client details, payment terms, and status watermark stamp.
  - One-click print or "Save as PDF" directly from the browser.
- **Automated Test Suite**: Pytest test suite testing clients, products, invoices, payments, and analytics against PostgreSQL.

---

## Tech Stack

- **Backend**: FastAPI 0.115+, Uvicorn, Prisma Client Python 0.15+, Pydantic v2, Jinja2
- **Database**: PostgreSQL (`postgresql://...`)
- **Frontend**: Vanilla HTML5/CSS3 (Modern glassmorphic dark/light design system), JavaScript SPA, Chart.js, FontAwesome 6
- **Testing**: Pytest, HTTPX

---

## Configuration (`.env`)

Configure your PostgreSQL database connection in `.env`:

```env
DATABASE_URL="postgresql://postgres:admin@127.0.0.1:5432/billing_db"
APP_NAME=BillMaster
DEFAULT_CURRENCY=$
COMPANY_NAME=BillMaster Solutions Ltd.
COMPANY_EMAIL=billing@billmaster.io
COMPANY_PHONE=+1 (800) 555-0199
COMPANY_ADDRESS=120 Silicon Blvd, Suite 300, San Francisco, CA 94107
COMPANY_TAX_ID=US-EIN-98-7654321
INVOICE_PREFIX=INV
DEFAULT_TAX_RATE=10.0
```

---

## Quick Start Guide

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Push Prisma Schema & Generate Client
```bash
python -m prisma db push
python -m prisma generate
```

### 3. Seed Initial Demo Data (Optional)
Populate realistic clients, products, invoices, and payments in PostgreSQL:
```bash
python -m backend.seed_data
```
*(Or click the **"Seed Demo Data"** button directly inside the web UI!)*

### 4. Launch Application
Start the FastAPI server with Uvicorn:
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 5. Access the Application
- **Web Dashboard**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Prisma Studio (Visual Database Browser)**:
  ```bash
  python -m prisma studio
  ```

---

## Running Automated Tests

Run the test suite with `pytest`:
```bash
python -m pytest tests/ -v
```

---

## API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/clients` | List all clients with balance stats |
| `POST` | `/api/clients` | Create a new client |
| `GET` | `/api/products` | List active products/services |
| `POST` | `/api/products` | Add a new product or service |
| `GET` | `/api/invoices` | List invoices with status/search filters |
| `POST` | `/api/invoices` | Create a new invoice with itemized lines |
| `GET` | `/api/invoices/{id}` | Get full invoice details & payments |
| `GET` | `/invoices/{id}/print` | Printable HTML / PDF view of invoice |
| `POST` | `/api/payments` | Record payment against invoice |
| `GET` | `/api/analytics/summary` | Retrieve dashboard KPI aggregates & charts |
| `POST` | `/api/seed` | Populate realistic demo billing data into PostgreSQL |
