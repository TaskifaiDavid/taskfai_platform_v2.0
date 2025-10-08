"""
Dynamic Database Connection Manager

Manages per-tenant database connections with connection pooling.
Each tenant gets isolated connection pool with max 10 connections.
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import asyncpg
from contextlib import asynccontextmanager

from app.core.tenant import TenantContext


class TenantConnectionPool:
    """
    Connection pool for a single tenant

    Manages asyncpg pool with health checks and credential caching
    """

    def __init__(
        self,
        tenant_id: str,
        database_url: str,
        database_key: str,
        max_connections: int = 10
    ):
        """
        Initialize tenant connection pool

        Args:
            tenant_id: Tenant identifier
            database_url: PostgreSQL connection string
            database_key: Service role key for auth
            max_connections: Maximum concurrent connections (default 10)
        """
        self.tenant_id = tenant_id
        self.database_url = database_url
        self.database_key = database_key
        self.max_connections = max_connections
        self.pool: Optional[asyncpg.Pool] = None
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()

    async def get_pool(self) -> asyncpg.Pool:
        """
        Get or create connection pool

        Returns:
            asyncpg connection pool

        Raises:
            Exception: If pool creation fails
        """
        if self.pool is None or self.pool._closed:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=self.max_connections,
                timeout=30,
                command_timeout=60,
                server_settings={
                    'application_name': f'taskifai_tenant_{self.tenant_id}'
                }
            )

        self.last_accessed = datetime.utcnow()
        return self.pool

    async def close(self):
        """Close connection pool"""
        if self.pool and not self.pool._closed:
            await self.pool.close()
            self.pool = None

    @property
    def is_stale(self, cache_duration_minutes: int = 15) -> bool:
        """
        Check if pool credentials are stale

        Args:
            cache_duration_minutes: Cache duration in minutes

        Returns:
            True if pool should be refreshed
        """
        age = datetime.utcnow() - self.last_accessed
        return age > timedelta(minutes=cache_duration_minutes)


class TenantDBManager:
    """
    Multi-tenant database connection manager

    Features:
    - Per-tenant connection pools (max 10 connections each)
    - 15-minute credential cache
    - Automatic pool cleanup for inactive tenants
    - Thread-safe pool access
    """

    def __init__(self, cache_duration_minutes: int = 15):
        """
        Initialize database manager

        Args:
            cache_duration_minutes: How long to cache credentials
        """
        self.pools: Dict[str, TenantConnectionPool] = {}
        self.cache_duration = cache_duration_minutes
        self._lock = asyncio.Lock()

    async def get_pool(self, tenant: TenantContext) -> asyncpg.Pool:
        """
        Get connection pool for tenant

        Args:
            tenant: Tenant context with database credentials

        Returns:
            asyncpg connection pool for the tenant

        Raises:
            ValueError: If tenant database credentials missing
            Exception: If pool creation fails
        """
        if not tenant.database_url:
            raise ValueError(f"No database URL for tenant: {tenant.tenant_id}")

        async with self._lock:
            # Check if pool exists and is valid
            if tenant.tenant_id in self.pools:
                pool_obj = self.pools[tenant.tenant_id]

                # Check if credentials are stale
                if pool_obj.is_stale(self.cache_duration):
                    await pool_obj.close()
                    del self.pools[tenant.tenant_id]
                else:
                    return await pool_obj.get_pool()

            # Create new pool
            pool_obj = TenantConnectionPool(
                tenant_id=tenant.tenant_id,
                database_url=tenant.database_url,
                database_key=tenant.database_key,
                max_connections=10
            )

            self.pools[tenant.tenant_id] = pool_obj
            return await pool_obj.get_pool()

    @asynccontextmanager
    async def get_connection(self, tenant: TenantContext):
        """
        Get database connection for tenant (context manager)

        Usage:
            async with db_manager.get_connection(tenant) as conn:
                result = await conn.fetch("SELECT * FROM sales")

        Args:
            tenant: Tenant context

        Yields:
            asyncpg connection
        """
        pool = await self.get_pool(tenant)
        async with pool.acquire() as connection:
            yield connection

    async def close_pool(self, tenant_id: str):
        """
        Close connection pool for specific tenant

        Args:
            tenant_id: Tenant identifier
        """
        async with self._lock:
            if tenant_id in self.pools:
                await self.pools[tenant_id].close()
                del self.pools[tenant_id]

    async def close_all(self):
        """Close all connection pools"""
        async with self._lock:
            for pool_obj in self.pools.values():
                await pool_obj.close()
            self.pools.clear()

    async def cleanup_stale_pools(self):
        """
        Clean up stale connection pools

        Should be called periodically by a background task
        """
        async with self._lock:
            stale_tenants = [
                tenant_id
                for tenant_id, pool_obj in self.pools.items()
                if pool_obj.is_stale(self.cache_duration)
            ]

            for tenant_id in stale_tenants:
                await self.pools[tenant_id].close()
                del self.pools[tenant_id]

    def get_pool_stats(self) -> Dict[str, dict]:
        """
        Get statistics for all pools

        Returns:
            Dictionary of pool stats by tenant_id
        """
        stats = {}
        for tenant_id, pool_obj in self.pools.items():
            if pool_obj.pool:
                stats[tenant_id] = {
                    "size": pool_obj.pool.get_size(),
                    "free": pool_obj.pool.get_idle_size(),
                    "max_size": pool_obj.max_connections,
                    "created_at": pool_obj.created_at.isoformat(),
                    "last_accessed": pool_obj.last_accessed.isoformat()
                }
        return stats


# Global database manager instance
db_manager = TenantDBManager()

# Alias for backwards compatibility
DatabaseManager = TenantDBManager
