"""Health check endpoint for API v1."""

from typing import Dict, Any
from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def api_health() -> Dict[str, Any]:
    """Health check endpoint for API v1 confirming service status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "api_prefix": settings.API_V1_PREFIX
    }
