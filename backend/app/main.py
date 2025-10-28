"""
TaskifAI - Sales Data Analytics Platform
Main FastAPI Application
"""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

from app.api import auth, uploads, chat, dashboards, analytics, admin, dashboard_config, bibbi_uploads, bibbi_product_mappings
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

# Startup event for environment validation
@app.on_event("startup")
async def startup_event():
    """Validate environment on startup"""
    print("[Startup] Validating environment...")

    # Validate BIBBI configuration if enabled
    if settings.bibbi_enabled:
        print(f"[Startup] BIBBI system enabled for tenant: {settings.bibbi_tenant_id}")

        # Create BIBBI upload directory if it doesn't exist
        bibbi_upload_dir = Path(settings.bibbi_upload_dir)
        if not bibbi_upload_dir.exists():
            print(f"[Startup] Creating BIBBI upload directory: {bibbi_upload_dir}")
            bibbi_upload_dir.mkdir(parents=True, exist_ok=True)
        else:
            print(f"[Startup] BIBBI upload directory exists: {bibbi_upload_dir}")

        # Validate Supabase connection
        try:
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)

            # Test query to verify database access
            # Try to access a common table that should exist
            test_query = supabase.table("products").select("ean").limit(1).execute()
            print(f"[Startup] Supabase connection validated ✓")

        except Exception as e:
            print(f"[Startup] WARNING: Supabase connection test failed: {e}")
            print(f"[Startup] BIBBI features may not work correctly")

        # Validate required settings
        required_settings = {
            "supabase_url": settings.supabase_url,
            "supabase_service_key": bool(settings.supabase_service_key),
            "secret_key": bool(settings.secret_key),
        }

        print(f"[Startup] Required settings validation:")
        for setting_name, value in required_settings.items():
            status = "✓" if value else "✗"
            print(f"[Startup]   {setting_name}: {status}")

        print(f"[Startup] BIBBI system validation complete")
    else:
        print("[Startup] BIBBI system disabled")

    print("[Startup] Environment validation complete")


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

# BIBBI-specific routers (tenant-isolated reseller upload system)
# Use /api/bibbi prefix to avoid conflict with generic /api/uploads endpoint
app.include_router(bibbi_uploads.router, prefix="/api/bibbi")
app.include_router(bibbi_product_mappings.router, prefix="/api/bibbi")


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
