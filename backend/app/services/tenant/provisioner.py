"""
Tenant provisioning service

Handles automated tenant creation via Supabase Management API,
including project setup, schema migration, and initial configuration.
"""

import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import asyncpg

from app.core.config import settings
from app.models.tenant import TenantCreate, Tenant
from app.services.tenant.registry import TenantRegistry


class TenantProvisioner:
    """
    Automated tenant provisioning via Supabase Management API

    Creates new Supabase projects, applies schema migrations,
    seeds initial data, and registers tenant in master registry.
    """

    def __init__(self):
        """Initialize provisioner with Supabase Management API credentials"""
        self.management_api_url = "https://api.supabase.com/v1"
        self.management_api_key = settings.supabase_management_api_key
        self.registry = TenantRegistry()

    async def provision_tenant(
        self,
        subdomain: str,
        organization_name: str,
        admin_email: str,
        region: str = "us-east-1"
    ) -> Tenant:
        """
        Provision a new tenant with complete setup

        Steps:
        1. Create Supabase project via Management API
        2. Wait for project to be ready
        3. Apply database schema migrations
        4. Seed vendor configurations
        5. Register tenant in master registry
        6. Return tenant details

        Args:
            subdomain: Unique subdomain for tenant
            organization_name: Organization display name
            admin_email: Admin user email
            region: Supabase project region

        Returns:
            Provisioned tenant details

        Raises:
            ValueError: If subdomain is taken or validation fails
            Exception: If provisioning fails at any step
        """
        # Validate subdomain availability
        if await self._is_subdomain_taken(subdomain):
            raise ValueError(f"Subdomain '{subdomain}' is already taken")

        # Step 1: Create Supabase project
        project_details = await self._create_supabase_project(
            subdomain, organization_name, region
        )

        try:
            # Step 2: Wait for project to be ready
            await self._wait_for_project_ready(project_details['project_id'])

            # Step 3: Apply schema migrations
            await self._apply_schema_migrations(
                project_details['database_url'],
                project_details['database_key']
            )

            # Step 4: Seed vendor configurations
            await self._seed_vendor_configs(
                project_details['database_url'],
                project_details['database_key']
            )

            # Step 5: Register in master registry
            tenant_data = TenantCreate(
                subdomain=subdomain,
                organization_name=organization_name,
                admin_email=admin_email,
                database_url=project_details['database_url'],
                database_key=project_details['database_key'],
                supabase_project_id=project_details['project_id'],
                is_active=True
            )

            tenant = await self.registry.create_tenant(tenant_data)

            return tenant

        except Exception as e:
            # Rollback: Delete project if provisioning fails
            await self._cleanup_failed_provisioning(project_details['project_id'])
            raise Exception(f"Tenant provisioning failed: {str(e)}")

    async def _create_supabase_project(
        self,
        subdomain: str,
        organization_name: str,
        region: str
    ) -> Dict[str, str]:
        """
        Create new Supabase project via Management API

        Args:
            subdomain: Project subdomain
            organization_name: Organization name
            region: AWS region

        Returns:
            Dictionary with project_id, database_url, database_key
        """
        async with httpx.AsyncClient() as client:
            # Create project
            response = await client.post(
                f"{self.management_api_url}/projects",
                headers={
                    "Authorization": f"Bearer {self.management_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "name": f"{organization_name} ({subdomain})",
                    "organization_id": settings.supabase_organization_id,
                    "region": region,
                    "plan": "pro",  # or "free" for testing
                    "db_pass": self._generate_secure_password()
                },
                timeout=30.0
            )

            if response.status_code != 201:
                raise Exception(f"Failed to create Supabase project: {response.text}")

            project_data = response.json()

            return {
                'project_id': project_data['id'],
                'database_url': project_data['database']['host'],
                'database_key': project_data['anon_key']
            }

    async def _wait_for_project_ready(
        self,
        project_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 10
    ) -> None:
        """
        Wait for Supabase project to be fully provisioned

        Args:
            project_id: Supabase project ID
            max_wait_seconds: Maximum time to wait
            poll_interval: Seconds between status checks

        Raises:
            TimeoutError: If project doesn't become ready in time
        """
        async with httpx.AsyncClient() as client:
            elapsed = 0

            while elapsed < max_wait_seconds:
                response = await client.get(
                    f"{self.management_api_url}/projects/{project_id}",
                    headers={
                        "Authorization": f"Bearer {self.management_api_key}"
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    project = response.json()
                    if project['status'] == 'ACTIVE_HEALTHY':
                        return

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

            raise TimeoutError(f"Project {project_id} did not become ready in {max_wait_seconds}s")

    async def _apply_schema_migrations(
        self,
        database_url: str,
        database_key: str
    ) -> None:
        """
        Apply database schema migrations to new tenant database

        Args:
            database_url: Database connection URL
            database_key: Database password/key
        """
        # Read schema file
        with open('backend/db/schema.sql', 'r') as f:
            schema_sql = f.read()

        # Connect and execute
        conn = await asyncpg.connect(
            host=database_url,
            database='postgres',
            user='postgres',
            password=database_key,
            ssl='require'
        )

        try:
            await conn.execute(schema_sql)
        finally:
            await conn.close()

    async def _seed_vendor_configs(
        self,
        database_url: str,
        database_key: str
    ) -> None:
        """
        Seed default vendor configurations

        Args:
            database_url: Database connection URL
            database_key: Database password/key
        """
        # Read seed data
        with open('backend/db/seed_vendor_configs.sql', 'r') as f:
            seed_sql = f.read()

        # Connect and execute
        conn = await asyncpg.connect(
            host=database_url,
            database='postgres',
            user='postgres',
            password=database_key,
            ssl='require'
        )

        try:
            await conn.execute(seed_sql)
        finally:
            await conn.close()

    async def _cleanup_failed_provisioning(self, project_id: str) -> None:
        """
        Clean up failed provisioning attempt

        Args:
            project_id: Supabase project ID to delete
        """
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{self.management_api_url}/projects/{project_id}",
                    headers={
                        "Authorization": f"Bearer {self.management_api_key}"
                    },
                    timeout=30.0
                )
        except Exception:
            # Log but don't raise - cleanup is best effort
            pass

    async def _is_subdomain_taken(self, subdomain: str) -> bool:
        """
        Check if subdomain is already in use

        Args:
            subdomain: Subdomain to check

        Returns:
            True if taken, False if available
        """
        existing = await self.registry.get_tenant_by_subdomain(subdomain)
        return existing is not None

    def _generate_secure_password(self, length: int = 32) -> str:
        """
        Generate secure random password

        Args:
            length: Password length

        Returns:
            Secure random password
        """
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


# Celery task for async provisioning
async def provision_tenant_task(
    subdomain: str,
    organization_name: str,
    admin_email: str,
    region: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Celery task wrapper for tenant provisioning

    Args:
        subdomain: Unique subdomain
        organization_name: Organization name
        admin_email: Admin email
        region: AWS region

    Returns:
        Provisioning result with tenant details
    """
    provisioner = TenantProvisioner()

    try:
        tenant = await provisioner.provision_tenant(
            subdomain, organization_name, admin_email, region
        )

        return {
            'status': 'success',
            'tenant_id': str(tenant.tenant_id),
            'subdomain': tenant.subdomain,
            'organization_name': tenant.organization_name
        }

    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }
