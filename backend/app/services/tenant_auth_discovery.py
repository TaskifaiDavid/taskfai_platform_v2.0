"""
Tenant Discovery Service with Authentication

Handles Flow B: Combined authentication + tenant discovery
1. User enters email + password on app.taskifai.com
2. System authenticates credentials against users table
3. System queries user_tenants to find associated tenants
4. Returns:
   - Single tenant: JWT token + redirect to subdomain dashboard
   - Multi-tenant: Temporary token + tenant list for selection
"""

from typing import Union, List
from supabase import Client
from app.models.tenant import (
    LoginAndDiscoverRequest,
    LoginAndDiscoverSingleResponse,
    LoginAndDiscoverMultiResponse,
    TenantOption
)
from app.core.security import verify_password, create_access_token


class TenantAuthDiscoveryService:
    """Service for authenticated tenant discovery"""

    def __init__(self, registry_client: Client):
        """
        Initialize tenant auth discovery service

        Args:
            registry_client: Supabase client connected to tenant registry database
        """
        self.client = registry_client

    def login_and_discover(
        self,
        request: LoginAndDiscoverRequest
    ) -> Union[LoginAndDiscoverSingleResponse, LoginAndDiscoverMultiResponse]:
        """
        Authenticate user and discover associated tenants

        Flow:
        1. Find user by email in users table
        2. Verify password
        3. Query user_tenants for tenant associations
        4. Return single tenant (with token + redirect) or multi (with temp token)

        Args:
            request: Login credentials (email + password)

        Returns:
            Single tenant response (with JWT + redirect) or
            Multi-tenant response (with temp token + tenant list)

        Raises:
            ValueError: If authentication fails or no tenants found
        """
        email = request.email.lower()
        password = request.password

        # Step 1: Authenticate user credentials
        user = self._authenticate_user(email, password)
        if not user:
            raise ValueError("Invalid email or password")

        # Step 2: Query user_tenants to find associated tenants (by email)
        tenants_data = self._get_user_tenants(email)

        if not tenants_data:
            raise ValueError(f"No tenant found for user: {email}")

        # Step 3: Handle single tenant vs multi-tenant response
        if len(tenants_data) == 1:
            return self._create_single_tenant_response(user, tenants_data[0])
        else:
            return self._create_multi_tenant_response(user, tenants_data)

    def _authenticate_user(self, email: str, password: str) -> dict:
        """
        Authenticate user credentials against users table

        Args:
            email: User email
            password: Plain text password

        Returns:
            User record if authentication succeeds

        Raises:
            ValueError: If authentication fails
        """
        # Query users table (from tenant registry or any tenant database)
        # Note: For multi-tenant, we need to query a central users table
        # This should be in the tenant registry database
        result = self.client.table('users')\
            .select('user_id, email, hashed_password, full_name, role')\
            .eq('email', email)\
            .execute()

        if not result.data or len(result.data) == 0:
            raise ValueError(f"No user found with email: {email}")

        user = result.data[0]

        # Verify password
        if not verify_password(password, user['hashed_password']):
            raise ValueError("Invalid password")

        return user

    def _get_user_tenants(self, email: str) -> List[dict]:
        """
        Get list of active tenants for user by email

        Args:
            email: User email address (lowercase)

        Returns:
            List of tenant records with subdomain and company_name
        """
        # Query user_tenants with JOIN to tenants table (by email, not user_id)
        result = self.client.table('user_tenants')\
            .select('tenant_id, tenants!inner(subdomain, company_name, is_active)')\
            .eq('email', email)\
            .eq('tenants.is_active', True)\
            .execute()

        if not result.data:
            return []

        # Extract tenant information
        tenants = []
        for record in result.data:
            tenant_info = record['tenants']
            tenants.append({
                'tenant_id': record['tenant_id'],
                'subdomain': tenant_info['subdomain'],
                'company_name': tenant_info['company_name']
            })

        return tenants

    def _create_single_tenant_response(
        self,
        user: dict,
        tenant: dict
    ) -> LoginAndDiscoverSingleResponse:
        """
        Create response for single-tenant user

        Args:
            user: User record
            tenant: Tenant record

        Returns:
            Single tenant response with JWT token and redirect URL
        """
        # Create JWT token with user + tenant claims
        access_token = create_access_token(
            data={
                "sub": user['user_id'],
                "email": user['email'],
                "role": user['role']
            },
            tenant_id=tenant['tenant_id'],
            subdomain=tenant['subdomain']
        )

        # Redirect to tenant dashboard (not login page)
        redirect_url = f"https://{tenant['subdomain']}.taskifai.com/dashboard"

        return LoginAndDiscoverSingleResponse(
            subdomain=tenant['subdomain'],
            company_name=tenant['company_name'],
            redirect_url=redirect_url,
            access_token=access_token
        )

    def _create_multi_tenant_response(
        self,
        user: dict,
        tenants: List[dict]
    ) -> LoginAndDiscoverMultiResponse:
        """
        Create response for multi-tenant user

        Args:
            user: User record
            tenants: List of tenant records

        Returns:
            Multi-tenant response with temporary token and tenant list
        """
        # Create temporary token (valid for 5 minutes)
        # User will select tenant, then exchange temp token for real token
        temp_token = create_access_token(
            data={
                "sub": user['user_id'],
                "email": user['email'],
                "role": user['role'],
                "temp": True  # Mark as temporary
            },
            # No tenant_id/subdomain yet - user must select
            tenant_id=None,
            subdomain=None,
            expires_minutes=5,  # Short expiration
            add_jti=True  # Enable one-time use tracking
        )

        # Build tenant options list
        tenant_options = [
            TenantOption(
                subdomain=t['subdomain'],
                company_name=t['company_name']
            )
            for t in tenants
        ]

        return LoginAndDiscoverMultiResponse(
            tenants=tenant_options,
            temp_token=temp_token
        )

    def exchange_temp_token(
        self,
        temp_token: str,
        selected_subdomain: str
    ) -> str:
        """
        Exchange temporary token for tenant-specific token

        Used when multi-tenant user selects a tenant.

        Args:
            temp_token: Temporary JWT token
            selected_subdomain: User's selected tenant subdomain

        Returns:
            New JWT token with tenant claims

        Raises:
            ValueError: If token invalid or user not in selected tenant
        """
        # This would be implemented in auth.py endpoint
        # For now, this is a placeholder
        raise NotImplementedError("Token exchange endpoint not yet implemented")
