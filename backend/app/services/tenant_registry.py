"""
Tenant Registry Service

Handles CRUD operations for tenant management in the registry database.
Uses pgcrypto for encrypting database credentials.

Security:
- Credentials encrypted using encrypt_data(text, key) → bytea
- Decrypted using decrypt_data(bytea, key) → text
- Encryption key from settings.secret_key
"""

from typing import List, Optional
from uuid import UUID
import json
from datetime import datetime

from supabase import Client
from app.core.config import settings
from app.models.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    Tenant,
    TenantCredentials
)
from app.models.user_tenant import UserTenantCreate, UserRole


class TenantRegistryService:
    """Service for tenant registry operations"""

    def __init__(self, registry_client: Client):
        """
        Initialize tenant registry service

        Args:
            registry_client: Supabase client connected to tenant registry database
        """
        self.client = registry_client
        self.encryption_key = settings.secret_key[:32]  # Use first 32 chars as encryption key

    def create_tenant(
        self,
        tenant_data: TenantCreate
    ) -> TenantResponse:
        """
        Create new tenant with encrypted credentials

        Args:
            tenant_data: Tenant creation data including credentials

        Returns:
            Created tenant response (without credentials)

        Raises:
            ValueError: If subdomain already exists
            Exception: If database operation fails
        """
        # Check subdomain availability
        existing = self.get_tenant_by_subdomain(tenant_data.subdomain)
        if existing:
            raise ValueError(f"Subdomain '{tenant_data.subdomain}' already exists")

        # Encrypt credentials using pgcrypto
        credentials_json = json.dumps({
            "anon_key": tenant_data.database_credentials.anon_key,
            "service_key": tenant_data.database_credentials.service_key
        })

        # Insert tenant with encrypted credentials
        # Using RPC function to encrypt credentials server-side
        result = self.client.rpc(
            'create_tenant_with_encryption',
            {
                'p_subdomain': tenant_data.subdomain,
                'p_company_name': tenant_data.company_name,
                'p_database_url': tenant_data.database_url,
                'p_credentials_json': credentials_json,
                'p_encryption_key': self.encryption_key
            }
        ).execute()

        if not result.data:
            raise Exception("Failed to create tenant")

        tenant_record = result.data[0] if isinstance(result.data, list) else result.data
        tenant_id = tenant_record['tenant_id']

        # Add admin user to tenant
        self._add_user_to_tenant(
            tenant_id=tenant_id,
            email=tenant_data.admin_email,
            role=UserRole.ADMIN
        )

        # Return tenant response
        return TenantResponse(
            tenant_id=UUID(tenant_id),
            subdomain=tenant_data.subdomain,
            company_name=tenant_data.company_name,
            database_url=tenant_data.database_url,
            is_active=True,
            created_at=datetime.fromisoformat(tenant_record['created_at']),
            updated_at=None
        )

    def get_tenant_by_id(self, tenant_id: UUID) -> Optional[TenantResponse]:
        """
        Get tenant by ID

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tenant response or None if not found
        """
        result = self.client.table('tenants')\
            .select('*')\
            .eq('tenant_id', str(tenant_id))\
            .execute()

        if not result.data:
            return None

        tenant = result.data[0]
        return TenantResponse(
            tenant_id=UUID(tenant['tenant_id']),
            subdomain=tenant['subdomain'],
            company_name=tenant['company_name'],
            database_url=tenant['database_url'],
            is_active=tenant['is_active'],
            created_at=datetime.fromisoformat(tenant['created_at']),
            updated_at=datetime.fromisoformat(tenant['updated_at']) if tenant.get('updated_at') else None
        )

    def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """
        Get tenant by subdomain with decrypted credentials

        Args:
            subdomain: Tenant subdomain

        Returns:
            Complete tenant with credentials or None if not found
        """
        # Use RPC function to decrypt credentials
        result = self.client.rpc(
            'get_tenant_with_credentials',
            {
                'p_subdomain': subdomain.lower(),
                'p_encryption_key': self.encryption_key
            }
        ).execute()

        if not result.data:
            return None

        tenant = result.data[0] if isinstance(result.data, list) else result.data

        return Tenant(
            tenant_id=UUID(tenant['tenant_id']),
            subdomain=tenant['subdomain'],
            company_name=tenant['company_name'],
            database_url=tenant['database_url'],
            encrypted_credentials=tenant['decrypted_credentials'],  # Already decrypted by RPC
            is_active=tenant['is_active'],
            created_at=datetime.fromisoformat(tenant['created_at']),
            updated_at=datetime.fromisoformat(tenant['updated_at']) if tenant.get('updated_at') else None
        )

    def list_tenants(
        self,
        limit: int = 10,
        offset: int = 0,
        active_only: bool = False
    ) -> tuple[List[TenantResponse], int]:
        """
        List all tenants with pagination

        Args:
            limit: Number of tenants per page
            offset: Offset from start
            active_only: Only return active tenants

        Returns:
            Tuple of (list of tenants, total count)
        """
        query = self.client.table('tenants').select('*', count='exact')

        if active_only:
            query = query.eq('is_active', True)

        result = query.order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        tenants = [
            TenantResponse(
                tenant_id=UUID(t['tenant_id']),
                subdomain=t['subdomain'],
                company_name=t['company_name'],
                database_url=t['database_url'],
                is_active=t['is_active'],
                created_at=datetime.fromisoformat(t['created_at']),
                updated_at=datetime.fromisoformat(t['updated_at']) if t.get('updated_at') else None
            )
            for t in result.data
        ]

        total = result.count or 0

        return tenants, total

    def update_tenant(
        self,
        tenant_id: UUID,
        tenant_update: TenantUpdate
    ) -> TenantResponse:
        """
        Update tenant information

        Args:
            tenant_id: Tenant UUID
            tenant_update: Updated tenant data

        Returns:
            Updated tenant response

        Raises:
            ValueError: If tenant not found
        """
        # Build update data
        update_data = {}
        if tenant_update.company_name is not None:
            update_data['company_name'] = tenant_update.company_name
        if tenant_update.is_active is not None:
            update_data['is_active'] = tenant_update.is_active
        if tenant_update.database_url is not None:
            update_data['database_url'] = tenant_update.database_url

        if not update_data:
            raise ValueError("No fields to update")

        update_data['updated_at'] = datetime.utcnow().isoformat()

        # If credentials are being updated, encrypt them
        if tenant_update.database_credentials:
            credentials_json = json.dumps({
                "anon_key": tenant_update.database_credentials.anon_key,
                "service_key": tenant_update.database_credentials.service_key
            })

            result = self.client.rpc(
                'update_tenant_credentials',
                {
                    'p_tenant_id': str(tenant_id),
                    'p_credentials_json': credentials_json,
                    'p_encryption_key': self.encryption_key
                }
            ).execute()

            if not result.data:
                raise ValueError(f"Tenant {tenant_id} not found")

        # Update other fields
        if update_data:
            result = self.client.table('tenants')\
                .update(update_data)\
                .eq('tenant_id', str(tenant_id))\
                .execute()

            if not result.data:
                raise ValueError(f"Tenant {tenant_id} not found")

        # Return updated tenant
        updated = self.get_tenant_by_id(tenant_id)
        if not updated:
            raise ValueError(f"Tenant {tenant_id} not found after update")

        return updated

    def _add_user_to_tenant(
        self,
        tenant_id: str,
        email: str,
        role: str = UserRole.MEMBER
    ) -> None:
        """
        Add user to tenant (internal helper)

        Args:
            tenant_id: Tenant UUID string
            email: User email
            role: User role in tenant
        """
        self.client.table('user_tenants').insert({
            'email': email.lower(),
            'tenant_id': tenant_id,
            'role': role
        }).execute()

    def add_user_to_tenant(
        self,
        tenant_id: UUID,
        user_tenant: UserTenantCreate
    ) -> None:
        """
        Add user to tenant

        Args:
            tenant_id: Tenant UUID
            user_tenant: User-tenant creation data

        Raises:
            ValueError: If user already in tenant
        """
        # Check if user already in tenant
        existing = self.client.table('user_tenants')\
            .select('*')\
            .eq('tenant_id', str(tenant_id))\
            .eq('email', user_tenant.email.lower())\
            .execute()

        if existing.data:
            raise ValueError(f"User {user_tenant.email} already in tenant")

        self._add_user_to_tenant(
            tenant_id=str(tenant_id),
            email=user_tenant.email,
            role=user_tenant.role
        )

    def list_tenant_users(self, tenant_id: UUID) -> List[dict]:
        """
        List all users in a tenant

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of user-tenant records
        """
        result = self.client.table('user_tenants')\
            .select('*')\
            .eq('tenant_id', str(tenant_id))\
            .order('created_at', desc=False)\
            .execute()

        return result.data


# Database functions (should be created via migration)
#
# CREATE OR REPLACE FUNCTION create_tenant_with_encryption(
#     p_subdomain TEXT,
#     p_company_name TEXT,
#     p_database_url TEXT,
#     p_credentials_json TEXT,
#     p_encryption_key TEXT
# ) RETURNS TABLE(tenant_id UUID, subdomain TEXT, company_name TEXT, database_url TEXT, is_active BOOLEAN, created_at TIMESTAMPTZ)
# AS $$
# BEGIN
#     RETURN QUERY
#     INSERT INTO tenants (subdomain, company_name, database_url, encrypted_credentials, is_active)
#     VALUES (
#         p_subdomain,
#         p_company_name,
#         p_database_url,
#         pgp_sym_encrypt(p_credentials_json, p_encryption_key),
#         TRUE
#     )
#     RETURNING tenants.tenant_id, tenants.subdomain, tenants.company_name, tenants.database_url, tenants.is_active, tenants.created_at;
# END;
# $$ LANGUAGE plpgsql SECURITY DEFINER;
#
#
# CREATE OR REPLACE FUNCTION get_tenant_with_credentials(
#     p_subdomain TEXT,
#     p_encryption_key TEXT
# ) RETURNS TABLE(
#     tenant_id UUID,
#     subdomain TEXT,
#     company_name TEXT,
#     database_url TEXT,
#     decrypted_credentials TEXT,
#     is_active BOOLEAN,
#     created_at TIMESTAMPTZ,
#     updated_at TIMESTAMPTZ
# )
# AS $$
# BEGIN
#     RETURN QUERY
#     SELECT
#         tenants.tenant_id,
#         tenants.subdomain,
#         tenants.company_name,
#         tenants.database_url,
#         pgp_sym_decrypt(tenants.encrypted_credentials, p_encryption_key) AS decrypted_credentials,
#         tenants.is_active,
#         tenants.created_at,
#         tenants.updated_at
#     FROM tenants
#     WHERE tenants.subdomain = p_subdomain;
# END;
# $$ LANGUAGE plpgsql SECURITY DEFINER;
#
#
# CREATE OR REPLACE FUNCTION update_tenant_credentials(
#     p_tenant_id UUID,
#     p_credentials_json TEXT,
#     p_encryption_key TEXT
# ) RETURNS BOOLEAN
# AS $$
# BEGIN
#     UPDATE tenants
#     SET
#         encrypted_credentials = pgp_sym_encrypt(p_credentials_json, p_encryption_key),
#         updated_at = NOW()
#     WHERE tenant_id = p_tenant_id;
#
#     RETURN FOUND;
# END;
# $$ LANGUAGE plpgsql SECURITY DEFINER;
