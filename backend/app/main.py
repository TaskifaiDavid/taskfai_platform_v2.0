"""
TaskifAI - Sales Data Analytics Platform
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, tenant_discovery, uploads, chat, dashboards, analytics, admin, dashboard_config
from app.core.config import settings
from app.middleware.tenant_context import TenantContextMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import RequestLoggingMiddleware

# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sales data analytics platform with AI-powered insights",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware - consolidated production and development origins
# Supports both production (*.taskifai.com) and development (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # localhost for development
    allow_origin_regex=r"https://([a-z0-9-]+\.)?taskifai\.com",  # production domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-tenant middleware stack (order matters!)
# IMPORTANT: Middlewares execute in REVERSE order (LIFO)
# Added first = Executes last, Added last = Executes first

# 1. Logging - outermost, logs all requests (executes last)
app.add_middleware(RequestLoggingMiddleware)

# 2. Authentication - validates JWT and checks tenant match (executes second)
app.add_middleware(AuthMiddleware)

# 3. Tenant Context - extracts subdomain and resolves tenant (executes FIRST)
app.add_middleware(TenantContextMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(tenant_discovery.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(dashboards.router, prefix="/api")
app.include_router(dashboard_config.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TaskifAI Sales Analytics Platform API",
        "version": settings.app_version,
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
