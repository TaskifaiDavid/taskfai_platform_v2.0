"""
Tenant Registry Service

Manages CRUD operations for the master tenant registry.
The registry maps subdomains to tenant_ids and stores encrypted database credentials.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict
from supabase import create_client, Client

from app.core.config import settings
from app.core.security import encrypt_credential, decrypt_credential
from app.models.tenant import TenantCreate, TenantInDB, Tenant, TenantUpdate


class TenantRegistry:
    """
    Master tenant registry manager

    Handles tenant CRUD operations in the master registry database.
    All tenant credentials are encrypted before storage.
    """

    def __init__(self):
        """Initialize registry with master database connection"""
        # Master registry uses main Supabase project
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        self.table_name = "tenants"

    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """
        Create new tenant in registry

        Args:
            tenant_data: Tenant creation data with credentials

        Returns:
            Created tenant (public model without sensitive data)

        Raises:
            ValueError: If subdomain already exists
            Exception: If database operation fails
        """
        # Check subdomain availability
        existing = await self.get_by_subdomain(tenant_data.subdomain)
        if existing:
            raise ValueError(f"Subdomain '{tenant_data.subdomain}' already exists")

        # Generate tenant ID
        tenant_id = str(uuid.uuid4())

        # Encrypt credentials
        encrypted_db_url = encrypt_credential(tenant_data.database_url)
        credentials_dict = {
            "anon_key": tenant_data.database_anon_key,
            "service_key": tenant_data.database_service_key
        }
        encrypted_credentials = encrypt_credential(json.dumps(credentials_dict))

        # Prepare database record
        now = datetime.now(timezone.utc)
        db_record = {
            "tenant_id": tenant_id,
            "company_name": tenant_data.company_name,
            "subdomain": tenant_data.subdomain,
            "database_url": encrypted_db_url,
            "database_credentials": encrypted_credentials,
            "is_active": True,
            "created_at": now.isoformat(),
            "metadata": tenant_data.metadata or {}
        }

        # Insert into registry
        response = self.client.table(self.table_name).insert(db_record).execute()

        if not response.data:
            raise Exception("Failed to create tenant in registry")

        # Convert to Pydantic model
        tenant_in_db = TenantInDB(**response.data[0])
        return Tenant.from_db(tenant_in_db)

    async def get_by_subdomain(self, subdomain: str) -> Optional[TenantInDB]:
        """
        Get tenant by subdomain

        Args:
            subdomain: Tenant subdomain

        Returns:
            Tenant if found, None otherwise
        """
        response = self.client.table(self.table_name)\
            .select("*")\
            .eq("subdomain", subdomain)\
            .execute()

        if not response.data:
            return None

        return TenantInDB(**response.data[0])

    async def get_by_id(self, tenant_id: str) -> Optional[TenantInDB]:
        """
        Get tenant by ID

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tenant if found, None otherwise
        """
        response = self.client.table(self.table_name)\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .execute()

        if not response.data:
            return None

        return TenantInDB(**response.data[0])

    async def list_tenants(
        self,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """
        List all tenants

        Args:
            active_only: Filter for active tenants only
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of tenants (public models)
        """
        query = self.client.table(self.table_name).select("*")

        if active_only:
            query = query.eq("is_active", True)

        response = query.range(offset, offset + limit - 1).execute()

        tenants = []
        for data in response.data:
            tenant_in_db = TenantInDB(**data)
            tenants.append(Tenant.from_db(tenant_in_db))

        return tenants

    async def update_tenant(
        self,
        tenant_id: str,
        update_data: TenantUpdate
    ) -> Optional[Tenant]:
        """
        Update tenant information

        Args:
            tenant_id: Tenant UUID
            update_data: Fields to update

        Returns:
            Updated tenant or None if not found
        """
        # Build update dict (only non-None fields)
        update_dict = {}
        if update_data.company_name is not None:
            update_dict["company_name"] = update_data.company_name
        if update_data.is_active is not None:
            update_dict["is_active"] = update_data.is_active
        if update_data.metadata is not None:
            update_dict["metadata"] = update_data.metadata

        if not update_dict:
            # No fields to update
            return await self.get_by_id(tenant_id)

        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

        response = self.client.table(self.table_name)\
            .update(update_dict)\
            .eq("tenant_id", tenant_id)\
            .execute()

        if not response.data:
            return None

        tenant_in_db = TenantInDB(**response.data[0])
        return Tenant.from_db(tenant_in_db)

    async def suspend_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Suspend tenant (set is_active=False)

        Args:
            tenant_id: Tenant UUID

        Returns:
            Updated tenant or None if not found
        """
        now = datetime.now(timezone.utc)
        update_dict = {
            "is_active": False,
            "suspended_at": now.isoformat(),
            "updated_at": now.isoformat()
        }

        response = self.client.table(self.table_name)\
            .update(update_dict)\
            .eq("tenant_id", tenant_id)\
            .execute()

        if not response.data:
            return None

        tenant_in_db = TenantInDB(**response.data[0])
        return Tenant.from_db(tenant_in_db)

    async def reactivate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Reactivate suspended tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            Updated tenant or None if not found
        """
        now = datetime.now(timezone.utc)
        update_dict = {
            "is_active": True,
            "suspended_at": None,
            "updated_at": now.isoformat()
        }

        response = self.client.table(self.table_name)\
            .update(update_dict)\
            .eq("tenant_id", tenant_id)\
            .execute()

        if not response.data:
            return None

        tenant_in_db = TenantInDB(**response.data[0])
        return Tenant.from_db(tenant_in_db)

    def get_decrypted_credentials(self, tenant: TenantInDB) -> Dict[str, str]:
        """
        Decrypt tenant database credentials

        Args:
            tenant: Tenant model from database

        Returns:
            Dictionary with decrypted credentials
            {
                "database_url": "postgresql://...",
                "anon_key": "...",
                "service_key": "..."
            }

        Raises:
            Exception: If decryption fails
        """
        decrypted_url = decrypt_credential(tenant.database_url)
        credentials_json = decrypt_credential(tenant.database_credentials)
        credentials = json.loads(credentials_json)

        return {
            "database_url": decrypted_url,
            "anon_key": credentials["anon_key"],
            "service_key": credentials["service_key"]
        }

    async def check_subdomain_availability(self, subdomain: str) -> bool:
        """
        Check if subdomain is available

        Args:
            subdomain: Proposed subdomain

        Returns:
            True if available, False if taken
        """
        tenant = await self.get_by_subdomain(subdomain)
        return tenant is None


# Global registry instance
tenant_registry = TenantRegistry()
