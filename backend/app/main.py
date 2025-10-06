"""
BIBBI v2 - Sales Data Analytics Platform
Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, uploads
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

# CORS middleware (first, outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-tenant middleware stack (order matters!)
# 1. Logging - outermost, logs all requests
app.add_middleware(RequestLoggingMiddleware)

# 2. Tenant Context - extracts subdomain and resolves tenant
app.add_middleware(TenantContextMiddleware)

# 3. Authentication - validates JWT and checks tenant match
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(uploads.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BIBBI Sales Analytics Platform API",
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
