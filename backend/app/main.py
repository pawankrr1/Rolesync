"""Career Intelligence Backend Application Entrypoint."""

from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from contextlib import asynccontextmanager
from app.config import settings
from app.api.v1.router import api_v1_router
from app.db.session import create_all_tables

docs_url = "/docs" if (not settings.is_production or settings.ENABLE_DOCS) else None
redoc_url = "/redoc" if (not settings.is_production or settings.ENABLE_DOCS) else None
openapi_url = "/openapi.json" if (not settings.is_production or settings.ENABLE_DOCS) else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all registered tables exist
    create_all_tables()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Explainable AI talent-job matching ecosystem for India (Build for Bharat 2.0).",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan,
)

# High-Performance HTTP Response Compression for Payloads >= 1 KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Safe CORS Configuration: Disallow credentials if wildcard origin is configured
cors_origins = settings.cors_origins_list
allow_credentials = False if "*" in cors_origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# Standard HTTP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Root-level health endpoint (GET /health)
@app.get("/health", response_model=Dict[str, Any], tags=["Health"])
async def root_health() -> Dict[str, Any]:
    """Root health check endpoint confirming the service and database connectivity."""
    db_status = "connected"
    try:
        from app.db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {type(e).__name__}"

    is_healthy = db_status == "connected"
    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }


# Root informational endpoint (GET /)
@app.get("/", response_model=Dict[str, Any], tags=["System"])
async def root() -> Dict[str, Any]:
    """Root informational endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if (not settings.is_production or settings.ENABLE_DOCS) else "Disabled in production",
        "health_endpoints": ["/health", f"{settings.API_V1_PREFIX}/health"]
    }


# Mount API v1 router (exposes GET /api/v1/health and subsequent endpoints)
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=(settings.ENVIRONMENT == "development" and settings.DEBUG),
        workers=settings.WORKERS if settings.is_production else 1
    )
