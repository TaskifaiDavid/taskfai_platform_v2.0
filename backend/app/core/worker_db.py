"""
Worker-specific database client for Celery background tasks

Provides Supabase client creation without FastAPI dependency injection.
Used by Celery workers running in separate processes without request context.
"""

from supabase import Client, create_client
from app.core.config import settings


def get_worker_supabase_client(tenant_id: str = "demo") -> Client:
    """
    Create Supabase client for background workers

    Unlike get_supabase_client() in dependencies.py, this function:
    - Does NOT use FastAPI dependency injection
    - Works in Celery worker processes
    - Takes tenant_id as simple string parameter

    Args:
        tenant_id: Tenant identifier (default: "demo")

    Returns:
        Configured Supabase client for tenant's database

    Usage:
        # In Celery tasks
        supabase = get_worker_supabase_client(tenant_id="demo")
        result = supabase.table("upload_batches").select("*").execute()
    """
    # For demo tenant, use configured demo database
    if tenant_id == "demo" or not tenant_id:
        return create_client(
            settings.supabase_url,
            settings.supabase_service_key  # Service key bypasses RLS
        )

    # For BIBBI or other tenants, use same database
    # (Future: Load tenant-specific credentials from registry)
    return create_client(
        settings.supabase_url,
        settings.supabase_service_key
    )
