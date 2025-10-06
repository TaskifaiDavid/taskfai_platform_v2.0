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
        # Import here to avoid circular dependency
        from app.services.tenant.registry import tenant_registry
        self.registry = tenant_registry

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

        # Lookup tenant from registry
        tenant = await self.registry.get_by_subdomain(subdomain)

        if not tenant:
            raise ValueError(f"Tenant not found for subdomain: {subdomain}")

        if not tenant.is_active:
            raise ValueError(f"Tenant '{subdomain}' is suspended")

        # Get decrypted credentials
        credentials = self.registry.get_decrypted_credentials(tenant)

        return TenantContext(
            tenant_id=tenant.tenant_id,
            company_name=tenant.company_name,
            subdomain=tenant.subdomain,
            database_url=credentials["database_url"],
            database_key=credentials["service_key"],
            is_active=tenant.is_active,
            metadata=tenant.metadata or {}
        )

    @staticmethod
    def extract_subdomain(hostname: str) -> Optional[str]:
        """
        Extract subdomain from hostname

        Examples:
            customer1.taskifai.com → "customer1"
            demo.taskifai.com → "demo"
            taskifai.com → None
            localhost → None

        Args:
            hostname: Request hostname

        Returns:
            Subdomain or None if main domain/localhost
        """
        # Handle localhost
        if "localhost" in hostname or hostname.startswith("127.0.0.1"):
            return "demo"  # Use demo for local development

        # Split hostname
        parts = hostname.split('.')

        # If 3+ parts, first part is subdomain
        if len(parts) >= 3:
            return parts[0]

        # Main domain or invalid
        return None


# Global tenant context manager instance
_tenant_manager = None

def get_tenant_manager() -> TenantContextManager:
    """Get or create global tenant manager instance"""
    global _tenant_manager
    if _tenant_manager is None:
        _tenant_manager = TenantContextManager()
    return _tenant_manager
