"""
TaskifAI - Sales Data Analytics Platform
Main FastAPI Application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, uploads, chat, dashboards, analytics, admin, dashboard_config
from app.core.config import settings
from app.core.tenant import TenantContextManager
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

# CORS middleware - supports all tenant subdomains
# Development: localhost origins from settings.allowed_origins
# Production: All tenant subdomains (demo.taskifai.com, bibbi.taskifai.com, etc.)
# DigitalOcean: Also support *.ondigitalocean.app for deployed apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # localhost for development
    allow_origin_regex=r"https://([a-z0-9-]+)\.(taskifai\.com|ondigitalocean\.app)",  # tenant subdomains + DO apps
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
# NOTE: Auth and Admin routers registered twice to handle DigitalOcean App Platform route rewriting:
# - /api/auth/* and /api/admin/* (local development, direct backend access)
# - /auth/* and /admin/* (production with App Platform stripping /api prefix)
app.include_router(auth.router, prefix="/api")
app.include_router(auth.router)  # Register without /api prefix for production
app.include_router(uploads.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(dashboards.router, prefix="/api")
app.include_router(dashboard_config.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(admin.router)  # Register without /api prefix for production


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


@app.get("/api/debug/tenant")
async def debug_tenant(request: Request):
    """
    Diagnostic endpoint to debug tenant context setup

    This endpoint bypasses authentication to help diagnose why
    request.state.tenant is not being set by TenantContextMiddleware.
    """
    # Extract hostname from request
    hostname = request.headers.get("host", "").split(":")[0]

    # Manually test subdomain extraction
    try:
        subdomain = TenantContextManager.extract_subdomain(hostname)
    except Exception as e:
        subdomain = f"ERROR: {str(e)}"

    # Try to get demo context
    try:
        demo_context = TenantContextManager.get_demo_context()
        demo_context_str = {
            "tenant_id": demo_context.tenant_id,
            "subdomain": demo_context.subdomain,
            "database_url": demo_context.database_url[:50] + "..." if demo_context.database_url else None
        }
    except Exception as e:
        demo_context_str = f"ERROR: {str(e)}"

    # Check if tenant is in request.state
    has_tenant = hasattr(request.state, "tenant")
    tenant_from_state = None
    if has_tenant:
        try:
            tenant = request.state.tenant
            tenant_from_state = {
                "tenant_id": tenant.tenant_id,
                "subdomain": tenant.subdomain,
                "database_url": tenant.database_url[:50] + "..." if tenant.database_url else None
            }
        except Exception as e:
            tenant_from_state = f"ERROR accessing tenant: {str(e)}"

    return {
        "request_info": {
            "path": request.url.path,
            "method": request.method,
            "hostname": hostname,
        },
        "subdomain_extraction": {
            "extracted_subdomain": subdomain,
            "should_be": "demo (for *.ondigitalocean.app)",
        },
        "demo_context_test": demo_context_str,
        "request_state": {
            "has_tenant_attribute": has_tenant,
            "tenant_value": tenant_from_state,
        },
        "diagnosis": "If has_tenant_attribute is False, TenantContextMiddleware is not setting request.state.tenant"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
