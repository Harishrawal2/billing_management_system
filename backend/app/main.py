import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from prisma import Prisma

from backend.app.config import settings
from backend.app.db import prisma, get_db
from backend.app.routers import (
    clients_router,
    products_router,
    invoices_router,
    payments_router,
    analytics_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not prisma.is_connected():
        await prisma.connect()
    yield
    if prisma.is_connected():
        await prisma.disconnect()

app = FastAPI(
    title=settings.APP_NAME,
    description="Full-Featured Billing & Invoicing Management System API (PostgreSQL & Prisma)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directory structure exists
os.makedirs("frontend/static/css", exist_ok=True)
os.makedirs("frontend/static/js", exist_ok=True)
os.makedirs("frontend/templates", exist_ok=True)

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Register API Routers
app.include_router(clients_router)
app.include_router(products_router)
app.include_router(invoices_router)
app.include_router(payments_router)
app.include_router(analytics_router)

@app.get("/api/settings")
async def get_system_settings():
    return {
        "app_name": settings.APP_NAME,
        "currency": settings.DEFAULT_CURRENCY,
        "company_name": settings.COMPANY_NAME,
        "company_email": settings.COMPANY_EMAIL,
        "company_phone": settings.COMPANY_PHONE,
        "company_address": settings.COMPANY_ADDRESS,
        "company_tax_id": settings.COMPANY_TAX_ID,
        "default_tax_rate": settings.DEFAULT_TAX_RATE,
        "invoice_prefix": settings.INVOICE_PREFIX,
    }

@app.get("/", response_class=HTMLResponse)
async def index_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"settings": settings}
    )

@app.post("/api/seed")
async def seed_database_endpoint(db: Prisma = Depends(get_db)):
    from backend.seed_data import seed_data
    await seed_data(db)
    return {"message": "Sample billing data seeded into PostgreSQL via Prisma successfully!"}
