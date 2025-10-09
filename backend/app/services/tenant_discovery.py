"""
Tenant Discovery Service

Handles tenant discovery for user login flow:
1. User enters email on central portal
2. System queries user_tenants to find associated tenants
3. Returns tenant info for redirect or selection

Supports:
- Single tenant users → direct redirect
- Multi-tenant users → tenant selector
"""

from typing import List, Optional, Union
from supabase import Client
from app.models.tenant import (
    TenantDiscoveryRequest,
    TenantDiscoverySingleResponse,
    TenantDiscoveryMultiResponse,
    TenantOption
)


class TenantDiscoveryService:
    """Service for discovering tenants associated with user email"""

    def __init__(self, registry_client: Client):
        """
        Initialize tenant discovery service

        Args:
            registry_client: Supabase client connected to tenant registry database
        """
        self.client = registry_client

    def discover_tenant(
        self,
        discovery_request: TenantDiscoveryRequest
    ) -> Union[TenantDiscoverySingleResponse, TenantDiscoveryMultiResponse]:
        """
        Discover tenants for user email

        Args:
            discovery_request: Discovery request with user email

        Returns:
            Single tenant response (with redirect URL) or
            Multi-tenant response (with tenant list)

        Raises:
            ValueError: If email not found in any tenant
        """
        email = discovery_request.email.lower()

        # Query user_tenants to find associated tenants
        # Join with tenants table to get tenant details
        result = self.client.table('user_tenants')\
            .select('tenant_id, tenants!inner(subdomain, company_name, is_active)')\
            .eq('email', email)\
            .eq('tenants.is_active', True)\
            .execute()

        if not result.data or len(result.data) == 0:
            raise ValueError(f"No tenant found for email: {email}")

        # Extract tenant information
        tenants_data = []
        for record in result.data:
            tenant_info = record['tenants']
            tenants_data.append({
                'subdomain': tenant_info['subdomain'],
                'company_name': tenant_info['company_name']
            })

        # Single tenant: return redirect URL
        if len(tenants_data) == 1:
            tenant = tenants_data[0]
            redirect_url = f"https://{tenant['subdomain']}.taskifai.com/login?email={email}"

            return TenantDiscoverySingleResponse(
                subdomain=tenant['subdomain'],
                company_name=tenant['company_name'],
                redirect_url=redirect_url
            )

        # Multi-tenant: return tenant list for selection
        tenant_options = [
            TenantOption(
                subdomain=t['subdomain'],
                company_name=t['company_name']
            )
            for t in tenants_data
        ]

        return TenantDiscoveryMultiResponse(tenants=tenant_options)

    def get_tenants_for_user(self, email: str) -> List[TenantOption]:
        """
        Get list of tenants user has access to

        Args:
            email: User email address

        Returns:
            List of tenant options
        """
        email = email.lower()

        result = self.client.table('user_tenants')\
            .select('tenant_id, tenants!inner(subdomain, company_name, is_active)')\
            .eq('email', email)\
            .eq('tenants.is_active', True)\
            .execute()

        if not result.data:
            return []

        return [
            TenantOption(
                subdomain=record['tenants']['subdomain'],
                company_name=record['tenants']['company_name']
            )
            for record in result.data
        ]

    def is_user_in_tenant(self, email: str, subdomain: str) -> bool:
        """
        Check if user has access to tenant

        Args:
            email: User email address
            subdomain: Tenant subdomain

        Returns:
            True if user is in tenant, False otherwise
        """
        email = email.lower()
        subdomain = subdomain.lower()

        # Get tenant_id from subdomain
        tenant_result = self.client.table('tenants')\
            .select('tenant_id')\
            .eq('subdomain', subdomain)\
            .eq('is_active', True)\
            .execute()

        if not tenant_result.data:
            return False

        tenant_id = tenant_result.data[0]['tenant_id']

        # Check if user is in tenant
        user_result = self.client.table('user_tenants')\
            .select('id')\
            .eq('email', email)\
            .eq('tenant_id', tenant_id)\
            .execute()

        return bool(user_result.data)

    def get_user_role_in_tenant(
        self,
        email: str,
        subdomain: str
    ) -> Optional[str]:
        """
        Get user's role in specific tenant

        Args:
            email: User email address
            subdomain: Tenant subdomain

        Returns:
            User role (member, admin, super_admin) or None if not in tenant
        """
        email = email.lower()
        subdomain = subdomain.lower()

        # Get tenant_id from subdomain
        tenant_result = self.client.table('tenants')\
            .select('tenant_id')\
            .eq('subdomain', subdomain)\
            .execute()

        if not tenant_result.data:
            return None

        tenant_id = tenant_result.data[0]['tenant_id']

        # Get user role
        user_result = self.client.table('user_tenants')\
            .select('role')\
            .eq('email', email)\
            .eq('tenant_id', tenant_id)\
            .execute()

        if not user_result.data:
            return None

        return user_result.data[0]['role']
