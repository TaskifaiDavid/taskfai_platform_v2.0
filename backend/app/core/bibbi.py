"""
BIBBI-Specific Tenant Utilities

This module provides strict tenant isolation for the BIBBI reseller upload system.
All utilities in this module ONLY work with tenant_id = 'bibbi'.

IMPORTANT: This system is designed to be tenant-isolated from the start.
Multi-tenant support can be added later, but for now it's BIBBI-only.
"""

from typing import Callable
from functools import wraps

from fastapi import HTTPException, status, Depends, Request
from supabase import Client

from app.core.tenant import TenantContext
from app.core.dependencies import get_tenant_context, get_supabase_client


# BIBBI tenant constant
BIBBI_TENANT_ID = "bibbi"


class BibbιTenantError(HTTPException):
    """Custom exception for BIBBI tenant validation failures"""
    def __init__(self, detail: str = "Access denied. This resource is only available for BIBBI tenant."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


def require_bibbi_tenant(func: Callable) -> Callable:
    """
    Decorator to enforce BIBBI tenant-only access on endpoints

    Usage:
        @router.post("/bibbi/uploads")
        @require_bibbi_tenant
        async def upload_bibbi_file(...):
            ...

    Raises:
        BibbιTenantError: If tenant_id != 'bibbi'
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract tenant context from kwargs (injected by FastAPI dependency)
        tenant_context = kwargs.get('tenant_context')

        # If not in kwargs, try to get from request
        if tenant_context is None:
            request = kwargs.get('request')
            if request and hasattr(request, 'state') and hasattr(request.state, 'tenant'):
                tenant_context = request.state.tenant

        # Validate tenant
        if tenant_context is None:
            raise BibbιTenantError("Tenant context not found. Ensure TenantContextMiddleware is registered.")

        if tenant_context.tenant_id != BIBBI_TENANT_ID:
            raise BibbιTenantError(
                f"Access denied. Expected tenant '{BIBBI_TENANT_ID}', got '{tenant_context.tenant_id}'."
            )

        # Tenant validated - proceed with endpoint logic
        return await func(*args, **kwargs)

    return wrapper


def get_bibbi_tenant_context(
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> TenantContext:
    """
    Dependency injection for BIBBI tenant context with validation

    Usage:
        async def upload_file(
            bibbi_tenant: TenantContext = Depends(get_bibbi_tenant_context)
        ):
            # bibbi_tenant is guaranteed to be bibbi tenant

    Returns:
        TenantContext with tenant_id = 'bibbi'

    Raises:
        BibbιTenantError: If tenant_id != 'bibbi'
    """
    if tenant_context.tenant_id != BIBBI_TENANT_ID:
        raise BibbιTenantError(
            f"Access denied. Expected tenant '{BIBBI_TENANT_ID}', got '{tenant_context.tenant_id}'."
        )

    return tenant_context


class BibbιSupabaseClient:
    """
    Wrapper around Supabase client that automatically filters all queries by tenant_id='bibbi'

    This ensures that no query can accidentally access data from other tenants.

    Usage:
        bibbi_db = BibbιSupabaseClient(supabase_client)

        # Automatically filters by tenant_id='bibbi'
        result = bibbi_db.table("sales_unified").select("*").execute()

        # Equivalent to:
        # result = supabase.table("sales_unified").select("*").eq("tenant_id", "bibbi").execute()
    """

    def __init__(self, client: Client):
        """
        Initialize BIBBI-specific Supabase client

        Args:
            client: Standard Supabase client instance
        """
        self._client = client
        self._tenant_id = BIBBI_TENANT_ID

    def table(self, table_name: str):
        """
        Get table with automatic tenant filtering

        Args:
            table_name: Name of the table to query

        Returns:
            BibbιTableQuery instance with tenant filter pre-applied
        """
        return BibbιTableQuery(self._client, table_name, self._tenant_id)

    @property
    def client(self) -> Client:
        """Access underlying Supabase client for advanced operations"""
        return self._client


class BibbιTableQuery:
    """
    Query builder that automatically injects tenant_id filter

    Wraps Supabase query builder to ensure tenant isolation.
    """

    def __init__(self, client: Client, table_name: str, tenant_id: str):
        self._client = client
        self._table_name = table_name
        self._tenant_id = tenant_id
        self._query = client.table(table_name)
        self._tenant_filter_applied = False

    def _ensure_tenant_filter(self):
        """Ensure tenant filter is applied before any query execution"""
        if not self._tenant_filter_applied:
            self._query = self._query.eq("tenant_id", self._tenant_id)
            self._tenant_filter_applied = True
        return self._query

    def select(self, *args, **kwargs):
        """Select with automatic tenant filtering"""
        self._ensure_tenant_filter()
        self._query = self._query.select(*args, **kwargs)
        return self

    def insert(self, data, **kwargs):
        """
        Insert with automatic tenant_id injection

        If data is dict: Injects tenant_id into the dict
        If data is list: Injects tenant_id into each dict in the list
        """
        # Inject tenant_id into data
        if isinstance(data, dict):
            data["tenant_id"] = self._tenant_id
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    item["tenant_id"] = self._tenant_id

        self._query = self._query.insert(data, **kwargs)
        return self

    def update(self, data, **kwargs):
        """Update with automatic tenant filtering"""
        self._ensure_tenant_filter()
        self._query = self._query.update(data, **kwargs)
        return self

    def delete(self, **kwargs):
        """Delete with automatic tenant filtering"""
        self._ensure_tenant_filter()
        self._query = self._query.delete(**kwargs)
        return self

    def eq(self, column: str, value):
        """Add equality filter"""
        self._query = self._query.eq(column, value)
        return self

    def neq(self, column: str, value):
        """Add not-equal filter"""
        self._query = self._query.neq(column, value)
        return self

    def gt(self, column: str, value):
        """Add greater-than filter"""
        self._query = self._query.gt(column, value)
        return self

    def gte(self, column: str, value):
        """Add greater-than-or-equal filter"""
        self._query = self._query.gte(column, value)
        return self

    def lt(self, column: str, value):
        """Add less-than filter"""
        self._query = self._query.lt(column, value)
        return self

    def lte(self, column: str, value):
        """Add less-than-or-equal filter"""
        self._query = self._query.lte(column, value)
        return self

    def like(self, column: str, pattern: str):
        """Add LIKE filter"""
        self._query = self._query.like(column, pattern)
        return self

    def ilike(self, column: str, pattern: str):
        """Add case-insensitive LIKE filter"""
        self._query = self._query.ilike(column, pattern)
        return self

    def is_(self, column: str, value):
        """Add IS filter (for NULL checks)"""
        self._query = self._query.is_(column, value)
        return self

    def in_(self, column: str, values: list):
        """Add IN filter"""
        self._query = self._query.in_(column, values)
        return self

    def order(self, column: str, **kwargs):
        """Add ordering"""
        self._query = self._query.order(column, **kwargs)
        return self

    def limit(self, count: int):
        """Add limit"""
        self._query = self._query.limit(count)
        return self

    def range(self, start: int, end: int):
        """Add range"""
        self._query = self._query.range(start, end)
        return self

    def execute(self):
        """Execute query with tenant filter guaranteed"""
        self._ensure_tenant_filter()
        return self._query.execute()


def get_bibbi_supabase_client(
    supabase: Client = Depends(get_supabase_client),
    tenant_context: TenantContext = Depends(get_bibbi_tenant_context)
) -> BibbιSupabaseClient:
    """
    Dependency injection for BIBBI-specific Supabase client

    Usage:
        async def upload_file(
            bibbi_db: BibbιSupabaseClient = Depends(get_bibbi_supabase_client)
        ):
            # All queries automatically filtered by tenant_id='bibbi'
            result = bibbi_db.table("sales_unified").select("*").execute()

    Returns:
        BibbιSupabaseClient with automatic tenant filtering
    """
    return BibbιSupabaseClient(supabase)


# Type aliases for dependency injection
BibbιTenant = TenantContext
BibbιDB = BibbιSupabaseClient
