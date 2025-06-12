from fastapi import APIRouter

from app.api.v1.endpoints.health_check import router as health_check_router
from app.api.v1.endpoints.statements import router as statements_router

api_router = APIRouter()
api_router.include_router(
    health_check_router,
    tags=["Health Check"],
)

api_router.include_router(
    statements_router,
    prefix="/statements",
    tags=["Statements"],
)