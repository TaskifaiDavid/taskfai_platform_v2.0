"""
Tenant management service

Handles tenant suspension, reactivation, and administrative operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import asyncpg

from app.services.tenant.registry import TenantRegistry
from app.core.db_manager import DatabaseManager
from app.models.tenant import Tenant, TenantUpdate


class TenantManager:
    """
    Tenant administrative operations

    Manages tenant lifecycle operations including suspension,
    reactivation, updates, and connection management.
    """

    def __init__(self):
        """Initialize tenant manager"""
        self.registry = TenantRegistry()
        self.db_manager = DatabaseManager()

    async def suspend_tenant(
        self,
        tenant_id: UUID,
        reason: Optional[str] = None
    ) -> Tenant:
        """
        Suspend a tenant

        Steps:
        1. Mark tenant as inactive in registry
        2. Invalidate all active connections
        3. Clear credentials from cache
        4. Log suspension event

        Args:
            tenant_id: Tenant ID to suspend
            reason: Suspension reason (optional)

        Returns:
            Updated tenant details

        Raises:
            ValueError: If tenant not found
        """
        # Get tenant
        tenant = await self.registry.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Update tenant status
        update_data = TenantUpdate(
            is_active=False,
            suspended_at=datetime.utcnow(),
            suspension_reason=reason
        )

        updated_tenant = await self.registry.update_tenant(tenant_id, update_data)

        # Invalidate connections
        await self._invalidate_tenant_connections(tenant.subdomain)

        # Log suspension
        await self._log_tenant_event(
            tenant_id,
            'suspended',
            {'reason': reason or 'No reason provided'}
        )

        return updated_tenant

    async def reactivate_tenant(self, tenant_id: UUID) -> Tenant:
        """
        Reactivate a suspended tenant

        Steps:
        1. Mark tenant as active in registry
        2. Clear suspension metadata
        3. Log reactivation event

        Args:
            tenant_id: Tenant ID to reactivate

        Returns:
            Updated tenant details

        Raises:
            ValueError: If tenant not found
        """
        # Get tenant
        tenant = await self.registry.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Update tenant status
        update_data = TenantUpdate(
            is_active=True,
            suspended_at=None,
            suspension_reason=None
        )

        updated_tenant = await self.registry.update_tenant(tenant_id, update_data)

        # Log reactivation
        await self._log_tenant_event(
            tenant_id,
            'reactivated',
            {}
        )

        return updated_tenant

    async def update_tenant_details(
        self,
        tenant_id: UUID,
        update_data: TenantUpdate
    ) -> Tenant:
        """
        Update tenant details

        Args:
            tenant_id: Tenant ID to update
            update_data: Update data

        Returns:
            Updated tenant

        Raises:
            ValueError: If tenant not found
        """
        # Validate tenant exists
        tenant = await self.registry.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # If changing credentials, invalidate connections
        if update_data.database_url or update_data.database_key:
            await self._invalidate_tenant_connections(tenant.subdomain)

        # Update tenant
        updated_tenant = await self.registry.update_tenant(tenant_id, update_data)

        # Log update
        await self._log_tenant_event(
            tenant_id,
            'updated',
            {'fields': list(update_data.model_dump(exclude_unset=True).keys())}
        )

        return updated_tenant

    async def get_tenant_stats(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Get tenant usage statistics

        Args:
            tenant_id: Tenant ID

        Returns:
            Dictionary with tenant statistics

        Raises:
            ValueError: If tenant not found
        """
        # Get tenant
        tenant = await self.registry.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Get database pool for tenant
        pool = await self.db_manager.get_pool(tenant.subdomain)

        # Query statistics
        async with pool.acquire() as conn:
            # User count
            user_count_row = await conn.fetchrow("SELECT COUNT(*) as count FROM users")
            user_count = user_count_row['count']

            # Upload count
            upload_count_row = await conn.fetchrow("SELECT COUNT(*) as count FROM upload_batches")
            upload_count = upload_count_row['count']

            # Sales data count
            offline_sales_row = await conn.fetchrow("SELECT COUNT(*) as count FROM sellout_entries2")
            offline_sales_count = offline_sales_row['count']

            online_sales_row = await conn.fetchrow("SELECT COUNT(*) as count FROM ecommerce_orders")
            online_sales_count = online_sales_row['count']

            # Last activity
            last_upload_row = await conn.fetchrow(
                "SELECT MAX(created_at) as last_upload FROM upload_batches"
            )
            last_upload = last_upload_row['last_upload']

        return {
            'tenant_id': str(tenant_id),
            'subdomain': tenant.subdomain,
            'organization_name': tenant.organization_name,
            'is_active': tenant.is_active,
            'created_at': tenant.created_at.isoformat(),
            'statistics': {
                'user_count': user_count,
                'upload_count': upload_count,
                'offline_sales_count': offline_sales_count,
                'online_sales_count': online_sales_count,
                'total_sales_records': offline_sales_count + online_sales_count,
                'last_upload': last_upload.isoformat() if last_upload else None
            }
        }

    async def list_all_tenants(
        self,
        active_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all tenants with basic stats

        Args:
            active_only: Return only active tenants
            skip: Pagination offset
            limit: Results per page

        Returns:
            List of tenants with stats
        """
        # Get tenants from registry
        tenants = await self.registry.list_tenants(active_only, skip, limit)

        # Enrich with basic stats (without heavy queries)
        enriched_tenants = []

        for tenant in tenants:
            tenant_dict = tenant.model_dump()

            # Add connection status
            try:
                pool = await self.db_manager.get_pool(tenant.subdomain)
                tenant_dict['connection_status'] = 'healthy' if pool else 'disconnected'
            except Exception:
                tenant_dict['connection_status'] = 'error'

            enriched_tenants.append(tenant_dict)

        return enriched_tenants

    async def _invalidate_tenant_connections(self, subdomain: str) -> None:
        """
        Invalidate all active connections for a tenant

        Args:
            subdomain: Tenant subdomain
        """
        try:
            # Close database pool
            await self.db_manager.close_pool(subdomain)

            # Clear credential cache
            await self.db_manager.clear_cache(subdomain)

        except Exception as e:
            # Log but don't fail suspension
            print(f"Error invalidating connections for {subdomain}: {str(e)}")

    async def _log_tenant_event(
        self,
        tenant_id: UUID,
        event_type: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Log tenant administrative event

        Args:
            tenant_id: Tenant ID
            event_type: Event type (suspended, reactivated, updated)
            metadata: Event metadata
        """
        # In production, log to dedicated audit table
        # For now, simple print
        event = {
            'tenant_id': str(tenant_id),
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata
        }
        print(f"[TENANT_EVENT] {event}")

    async def health_check_tenant(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Perform health check on tenant infrastructure

        Args:
            tenant_id: Tenant ID

        Returns:
            Health check results
        """
        tenant = await self.registry.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        health = {
            'tenant_id': str(tenant_id),
            'subdomain': tenant.subdomain,
            'is_active': tenant.is_active,
            'checks': {}
        }

        # Check database connectivity
        try:
            pool = await self.db_manager.get_pool(tenant.subdomain)
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health['checks']['database'] = 'healthy'
        except Exception as e:
            health['checks']['database'] = f'error: {str(e)}'

        # Check RLS policies
        try:
            pool = await self.db_manager.get_pool(tenant.subdomain)
            async with pool.acquire() as conn:
                policies = await conn.fetch(
                    """
                    SELECT tablename, policyname
                    FROM pg_policies
                    WHERE schemaname = 'public'
                    """
                )
            health['checks']['rls_policies'] = f'{len(policies)} policies active'
        except Exception as e:
            health['checks']['rls_policies'] = f'error: {str(e)}'

        # Overall health
        health['status'] = 'healthy' if all(
            'error' not in str(v).lower() for v in health['checks'].values()
        ) else 'unhealthy'

        return health
