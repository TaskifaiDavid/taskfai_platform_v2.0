"""
Tenant Context Management for Multi-Tenant Architecture
"""

from typing import Optional, Dict
from dataclasses import dataclass
import asyncio


@dataclass
class TenantContext:
    """
    Tenant context for multi-tenant operations

    For demo mode: tenant_id = "demo"
    For production: tenant_id from subdomain lookup
    """
    tenant_id: str = "demo"
    company_name: str = "TaskifAI Demo"
    subdomain: str = "demo"
    database_url: Optional[str] = None
    database_key: Optional[str] = None
    is_active: bool = True
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_demo(self) -> bool:
        """Check if this is the demo tenant"""
        return self.tenant_id == "demo"

    def __repr__(self) -> str:
        return f"TenantContext(tenant_id='{self.tenant_id}', company='{self.company_name}')"


class TenantContextManager:
    """
    Manages tenant context resolution from request

    Uses tenant registry for subdomain→tenant lookup
    Falls back to demo tenant for local development
    """

    def __init__(self):
        """Initialize with tenant registry"""
        self._registry_service = None

    def _get_registry_service(self):
        """Lazy initialization of registry service"""
        if self._registry_service is None:
            try:
                from supabase import create_client
                from app.core.config import settings
                from app.services.tenant_registry import TenantRegistryService

                # Create registry client
                registry_client = create_client(
                    settings.tenant_registry_url,
                    settings.tenant_registry_service_key
                )

                # Create service
                self._registry_service = TenantRegistryService(registry_client)
            except Exception as e:
                print(f"[TenantContextManager] Failed to initialize registry service: {e}")
                return None

        return self._registry_service

    @staticmethod
    def get_demo_context() -> TenantContext:
        """Get demo tenant context"""
        return TenantContext(
            tenant_id="demo",
            company_name="TaskifAI Demo",
            subdomain="demo",
            is_active=True
        )

    async def from_subdomain(self, subdomain: str) -> TenantContext:
        """
        Get tenant context from subdomain

        Args:
            subdomain: Subdomain extracted from request

        Returns:
            TenantContext for the subdomain

        Raises:
            ValueError: If subdomain not found or inactive
        """
        # Handle demo/localhost
        if subdomain in ("demo", "localhost", None):
            return self.get_demo_context()

        # Get registry service
        registry = self._get_registry_service()
        if registry is None:
            # Fallback to demo if registry not available
            print(f"[TenantContextManager] Registry not available, using demo context")
            return self.get_demo_context()

        try:
            # Lookup tenant from registry (synchronous method)
            tenant = registry.get_tenant_by_subdomain(subdomain)

            if not tenant:
                raise ValueError(f"Tenant not found for subdomain: {subdomain}")

            if not tenant.is_active:
                raise ValueError(f"Tenant '{subdomain}' is suspended")

            # Parse decrypted credentials from tenant.encrypted_credentials
            import json
            try:
                credentials = json.loads(tenant.encrypted_credentials)
            except (json.JSONDecodeError, TypeError):
                raise ValueError(f"Invalid credentials format for tenant: {subdomain}")

            return TenantContext(
                tenant_id=str(tenant.tenant_id),
                company_name=tenant.company_name,
                subdomain=tenant.subdomain,
                database_url=tenant.database_url,
                database_key=credentials.get("service_key"),
                is_active=tenant.is_active,
                metadata={}
            )
        except ValueError:
            raise
        except Exception as e:
            print(f"[TenantContextManager] Error looking up tenant: {e}")
            raise ValueError(f"Failed to lookup tenant: {str(e)}")

    @staticmethod
    def extract_subdomain(hostname: str) -> Optional[str]:
        """
        Extract and validate subdomain from hostname

        Examples:
            customer1.taskifai.com → "customer1"
            demo.taskifai.com → "demo"
            taskifai.com → None
            localhost → None
            taskifai-demo-ak4kq.ondigitalocean.app → "demo"

        Args:
            hostname: Request hostname

        Returns:
            Subdomain or None if main domain/localhost/invalid

        Security:
            - Validates subdomain matches ^[a-z0-9-]+$ pattern
            - Rejects leading/trailing hyphens
            - Normalizes uppercase to lowercase
            - Prevents path traversal, XSS, SQL injection attempts
        """
        import re

        # Handle localhost
        if "localhost" in hostname or hostname.startswith("127.0.0.1"):
            return "demo"  # Use demo for local development

        # Handle DigitalOcean App Platform URLs (*.ondigitalocean.app)
        # These are direct backend URLs and should always use demo context
        if "ondigitalocean.app" in hostname:
            return "demo"

        # Split hostname
        parts = hostname.split('.')

        # If less than 3 parts, no subdomain (main domain or invalid)
        if len(parts) < 3:
            return None

        # Extract first part as subdomain candidate
        subdomain = parts[0]

        # Normalize to lowercase
        subdomain = subdomain.lower()

        # Validate subdomain format:
        # - Only lowercase alphanumeric and hyphens
        # - No leading or trailing hyphens
        # - Length between 1 and 50 characters
        subdomain_pattern = re.compile(r'^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$')

        if not subdomain_pattern.match(subdomain):
            # Invalid subdomain format - reject
            print(f"[TenantContextManager] Invalid subdomain format: {subdomain}")
            return None

        return subdomain


# Global tenant context manager instance
_tenant_manager = None

def get_tenant_manager() -> TenantContextManager:
    """Get or create global tenant manager instance"""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantContextManager()
    return _tenant_manager
