"""
Vendor Configuration Loader with Inheritance
"""

from typing import Optional, Dict, Any
from supabase import Client
from app.models.vendor_config import VendorConfigData, FileFormat, TransformationRules, ValidationRules, DetectionRules


class VendorConfigLoader:
    """
    Loads vendor configurations with inheritance

    Priority:
    1. Tenant-specific active config
    2. System default config
    3. Fallback to hardcoded defaults
    """

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def load_config(
        self,
        vendor_name: str,
        tenant_id: Optional[str] = None
    ) -> VendorConfigData:
        """
        Load vendor configuration with inheritance

        Args:
            vendor_name: Vendor identifier
            tenant_id: Tenant identifier (None for demo)

        Returns:
            VendorConfigData with merged configuration
        """
        # Try tenant-specific config
        if tenant_id and tenant_id != "demo":
            tenant_config = self._load_tenant_config(tenant_id, vendor_name)
            if tenant_config:
                return VendorConfigData(**tenant_config)

        # Fallback to system default
        default_config = self._load_default_config(vendor_name)
        if default_config:
            return VendorConfigData(**default_config)

        # Fallback to hardcoded defaults
        return self._get_hardcoded_default(vendor_name)

    def _load_tenant_config(self, tenant_id: str, vendor_name: str) -> Optional[Dict[str, Any]]:
        """Load tenant-specific configuration"""
        try:
            result = self.supabase.table("vendor_configs").select("config_data").match({
                "tenant_id": tenant_id,
                "vendor_name": vendor_name,
                "is_active": True
            }).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]["config_data"]
        except Exception as e:
            print(f"Error loading tenant config: {e}")

        return None

    def _load_default_config(self, vendor_name: str) -> Optional[Dict[str, Any]]:
        """Load system default configuration"""
        try:
            result = self.supabase.table("vendor_configs").select("config_data").match({
                "vendor_name": vendor_name,
                "is_default": True
            }).is_("tenant_id", "null").execute()

            if result.data and len(result.data) > 0:
                return result.data[0]["config_data"]
        except Exception as e:
            print(f"Error loading default config: {e}")

        return None

    def _get_hardcoded_default(self, vendor_name: str) -> VendorConfigData:
        """
        Fallback hardcoded defaults (temporary until DB configs are seeded)

        This ensures the system works even before vendor_configs table is populated
        """
        defaults = {
            "boxnox": VendorConfigData(
                vendor_name="boxnox",
                currency="EUR",
                exchange_rate=1.0,
                file_format=FileFormat(
                    type="excel",
                    sheet_name="Sell Out by EAN",
                    header_row=0,
                    skip_rows=0,
                    pivot_format=False
                ),
                column_mapping={
                    "product_ean": "Product EAN",
                    "functional_name": "Functional Name",
                    "quantity": "Sold Qty",
                    "sales_eur": "Sales Amount (EUR)",
                    "reseller": "Reseller",
                    "month": "Month",
                    "year": "Year"
                },
                transformation_rules=TransformationRules(
                    currency_conversion=None,
                    date_format="YYYY-MM-DD",
                    ean_cleanup=True,
                    price_rounding=2
                ),
                validation_rules=ValidationRules(
                    ean_length=13,
                    month_range=[1, 12],
                    year_range=[2000, 2100],
                    required_fields=["product_ean", "quantity", "month", "year"],
                    nullable_fields=["sales_eur"]
                ),
                detection_rules=DetectionRules(
                    filename_keywords=["boxnox"],
                    sheet_names=["Sell Out by EAN"],
                    required_columns=["Product EAN", "Sold Qty"],
                    confidence_threshold=0.7
                )
            ),
            # Add other vendors as needed...
        }

        if vendor_name in defaults:
            return defaults[vendor_name]

        # Ultimate fallback - generic config
        raise ValueError(f"No configuration found for vendor: {vendor_name}")

    def list_available_vendors(self, tenant_id: Optional[str] = None) -> list[str]:
        """List all available vendor configurations"""
        try:
            # Get all default vendors
            result = self.supabase.table("vendor_configs").select("vendor_name").match({
                "is_default": True
            }).is_("tenant_id", "null").execute()

            if result.data:
                return [row["vendor_name"] for row in result.data]
        except Exception as e:
            print(f"Error listing vendors: {e}")

        # Fallback to hardcoded list
        return ["boxnox", "galilu", "skins_sa", "cdlc", "liberty", "selfridges", "ukraine", "skins_nl", "continuity", "online"]


# Helper function for backward compatibility
def get_vendor_config(supabase: Client, vendor_name: str, tenant_id: Optional[str] = None) -> VendorConfigData:
    """
    Get vendor configuration (convenience function)

    Args:
        supabase: Supabase client
        vendor_name: Vendor identifier
        tenant_id: Tenant identifier

    Returns:
        VendorConfigData
    """
    loader = VendorConfigLoader(supabase)
    return loader.load_config(vendor_name, tenant_id)
