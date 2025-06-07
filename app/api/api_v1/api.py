from fastapi import APIRouter

from app.api.api_v1.endpoints.health_check import router as health_check_router
from app.api.api_v1.endpoints.statements import router as statements_router
from app.api.api_v1.endpoints.transactions import router as transactions_router

# Configure router to handle both trailing and non-trailing slashes
api_router = APIRouter(redirect_slashes=False)

# Health check
api_router.include_router(
    health_check_router,
    prefix="/health",
    tags=["Health Check"],
)

# Statements endpoints
api_router.include_router(
    statements_router,
    prefix="/statements",
    tags=["Bank Statements"],
)

# Transactions endpoints  
api_router.include_router(
    transactions_router,
    prefix="/transactions",
    tags=["Transactions"],
)
