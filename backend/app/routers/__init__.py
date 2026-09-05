from backend.app.routers.clients import router as clients_router
from backend.app.routers.products import router as products_router
from backend.app.routers.invoices import router as invoices_router
from backend.app.routers.payments import router as payments_router
from backend.app.routers.analytics import router as analytics_router

__all__ = [
    "clients_router",
    "products_router",
    "invoices_router",
    "payments_router",
    "analytics_router",
]
