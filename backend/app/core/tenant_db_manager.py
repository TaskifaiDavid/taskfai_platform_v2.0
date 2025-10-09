"""
Tenant Database Connection Pool Manager

Manages per-tenant Supabase client instances with connection pooling.
Lazy initialization - clients created only when needed.
Thread-safe caching for reuse across requests.
"""

from typing import Dict, Optional
from threading import Lock
from supabase import Client, create_client

from app.core.tenant import TenantContext


class TenantDatabaseManager:
    """
    Connection pool manager for multi-tenant database access

    Features:
    - Per-tenant client caching (tenant_id → Supabase client)
    - Lazy initialization (clients created on first access)
    - Thread-safe access for concurrent requests
    - Automatic client reuse across requests for same tenant

    Example:
        manager = TenantDatabaseManager()
        client = manager.get_client(tenant_context)
        data = client.table("products").select("*").execute()
    """

    def __init__(self):
        """Initialize manager with empty client cache"""
        self._clients: Dict[str, Client] = {}
        self._lock = Lock()

    def get_client(self, tenant_context: TenantContext) -> Client:
        """
        Get or create Supabase client for tenant

        Args:
            tenant_context: Tenant context with database credentials

        Returns:
            Configured Supabase client for tenant's database

        Thread Safety:
            Uses lock to ensure only one client created per tenant
            even with concurrent requests
        """
        tenant_id = tenant_context.tenant_id

        # Fast path: client already exists
        if tenant_id in self._clients:
            return self._clients[tenant_id]

        # Slow path: create new client (thread-safe)
        with self._lock:
            # Double-check inside lock (another thread may have created it)
            if tenant_id in self._clients:
                return self._clients[tenant_id]

            # Create new client
            if tenant_context.database_url and tenant_context.database_key:
                client = create_client(
                    tenant_context.database_url,
                    tenant_context.database_key
                )
            else:
                # Fallback for demo tenant or incomplete config
                from app.core.config import settings
                client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_key
                )

            # Cache for future requests
            self._clients[tenant_id] = client

            print(f"[TenantDatabaseManager] Created new client for tenant: {tenant_id}")

            return client

    def clear_client(self, tenant_id: str) -> None:
        """
        Remove client from cache (useful for testing or tenant updates)

        Args:
            tenant_id: Tenant ID to remove from cache
        """
        with self._lock:
            if tenant_id in self._clients:
                del self._clients[tenant_id]
                print(f"[TenantDatabaseManager] Cleared client for tenant: {tenant_id}")

    def clear_all(self) -> None:
        """Clear all cached clients (useful for testing)"""
        with self._lock:
            count = len(self._clients)
            self._clients.clear()
            print(f"[TenantDatabaseManager] Cleared {count} cached clients")

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats:
            - cached_clients: Number of clients in cache
        """
        return {
            "cached_clients": len(self._clients)
        }


# Global singleton instance
_db_manager: Optional[TenantDatabaseManager] = None


def get_tenant_db_manager() -> TenantDatabaseManager:
    """
    Get global tenant database manager instance

    Returns:
        Singleton TenantDatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = TenantDatabaseManager()
    return _db_manager
