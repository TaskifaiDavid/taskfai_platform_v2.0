"""
BIBBI Product Service

Handles product management, matching, and auto-creation for vendor uploads.

Key Features:
- 3-tier product matching (exact code → name fuzzy → auto-create)
- Product auto-creation with vendor codes as temporary EANs
- Caching for performance
- Vendor-specific product mapping
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from difflib import SequenceMatcher

from app.core.bibbi import BibbιDB


class BibbιProductService:
    """
    Service for BIBBI product management and matching

    Handles the complexity of mapping vendor-specific product codes
    to BIBBI's master product catalog (keyed by EAN barcodes).
    """

    # Configuration constants
    TEMP_EAN_PREFIX = "9"  # Prefix for temporary EANs (vendor codes)
    MAX_VENDOR_CODE_DIGITS = 12  # Maximum digits in vendor code (EAN-13 = 1 prefix + 12 digits)
    NAME_MATCH_THRESHOLD = 0.75  # Minimum similarity for fuzzy name matching (75%)
    FUZZY_MATCH_LIMIT = 1000  # Maximum products to load for fuzzy matching

    def __init__(self, bibbi_db: BibbιDB):
        """
        Initialize product service

        Args:
            bibbi_db: BIBBI-specific Supabase client
        """
        self.db = bibbi_db
        # Cache: {vendor_code -> ean}
        self._product_cache: Dict[str, str] = {}

    def match_or_create_product(
        self,
        vendor_code: str,
        product_name: Optional[str] = None,
        vendor_name: str = "liberty"
    ) -> str:
        """
        Match vendor product code to BIBBI EAN, or create if not found

        3-Tier Matching Strategy:
        1. Exact vendor code match (e.g., liberty_name column)
        2. Fuzzy product name matching
        3. Auto-create with vendor code as temporary EAN

        Args:
            vendor_code: Vendor's internal product code (e.g., "834429")
            product_name: Product name from vendor file
            vendor_name: Vendor identifier ("liberty", "galilu", etc.)

        Returns:
            ean: BIBBI product EAN barcode

        Example:
            ean = service.match_or_create_product(
                vendor_code="834429",
                product_name="TROISIEME 10ML",
                vendor_name="liberty"
            )
        """
        # Check cache first
        cache_key = f"{vendor_name}:{vendor_code}"
        if cache_key in self._product_cache:
            return self._product_cache[cache_key]

        # Tier 1: Exact vendor code match
        ean = self._match_by_vendor_code(vendor_code, vendor_name)
        if ean:
            self._product_cache[cache_key] = ean
            print(f"[BibbiProduct] Matched by vendor code: {vendor_code} → {ean}")
            return ean

        # Tier 2: Fuzzy product name match (if name provided)
        if product_name:
            ean = self._match_by_product_name(product_name)
            if ean:
                # Update vendor column for future uploads
                self._update_vendor_mapping(ean, vendor_code, vendor_name)
                self._product_cache[cache_key] = ean
                print(f"[BibbiProduct] Matched by name: '{product_name}' → {ean}")
                return ean

        # Tier 3: Auto-create with vendor code as temporary EAN
        ean = self._create_product(vendor_code, product_name, vendor_name)
        self._product_cache[cache_key] = ean
        print(f"[BibbiProduct] Auto-created: {vendor_code} → {ean} (temporary)")
        return ean

    def _match_by_vendor_code(self, vendor_code: str, vendor_name: str) -> Optional[str]:
        """
        Match by vendor-specific product code

        Args:
            vendor_code: Vendor's product code
            vendor_name: Vendor identifier

        Returns:
            ean if found, None otherwise
        """
        try:
            vendor_column = f"{vendor_name}_name"

            # Query products table for vendor code match
            # NOTE: Use raw client to bypass tenant filter (products table has no tenant_id)
            result = self.db.client.table("products")\
                .select("ean")\
                .eq(vendor_column, vendor_code)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]["ean"]

            return None

        except Exception as e:
            print(f"[BibbiProduct] Error matching by vendor code: {e}")
            return None

    def _match_by_product_name(self, product_name: str) -> Optional[str]:
        """
        Match by fuzzy product name similarity

        Args:
            product_name: Product name from vendor file

        Returns:
            ean if good match found, None otherwise
        """
        try:
            # Get products with descriptions (limit to avoid N+1 performance issue)
            # Prioritize most recent products
            # NOTE: Use raw client to bypass tenant filter (products table has no tenant_id)
            result = self.db.client.table("products")\
                .select("ean, description, functional_name")\
                .order("updated_at", desc=True)\
                .limit(self.FUZZY_MATCH_LIMIT)\
                .execute()

            if not result.data:
                return None

            # Find best match using fuzzy string matching
            best_match_ean = None
            best_match_score = 0.0

            product_name_lower = product_name.lower().strip()

            for product in result.data:
                # Check description
                if product.get("description"):
                    desc_lower = product["description"].lower().strip()
                    score = SequenceMatcher(None, product_name_lower, desc_lower).ratio()

                    if score > best_match_score:
                        best_match_score = score
                        best_match_ean = product["ean"]

                # Check functional name
                if product.get("functional_name"):
                    func_lower = product["functional_name"].lower().strip()
                    score = SequenceMatcher(None, product_name_lower, func_lower).ratio()

                    if score > best_match_score:
                        best_match_score = score
                        best_match_ean = product["ean"]

            # Return match if score exceeds threshold
            if best_match_score >= self.NAME_MATCH_THRESHOLD:
                return best_match_ean

            return None

        except Exception as e:
            print(f"[BibbiProduct] Error matching by product name: {e}")
            return None

    def _create_product(
        self,
        vendor_code: str,
        product_name: Optional[str],
        vendor_name: str
    ) -> str:
        """
        Auto-create product with vendor code as temporary EAN

        Args:
            vendor_code: Vendor's product code
            product_name: Product name from vendor file
            vendor_name: Vendor identifier

        Returns:
            ean: The created product's EAN (vendor code zero-padded to 13 digits)
        """
        try:
            # Sanitize vendor code: filter to digits only
            sanitized_code = ''.join(filter(str.isdigit, str(vendor_code)))

            # Validate length: must fit in MAX_VENDOR_CODE_DIGITS
            if len(sanitized_code) > self.MAX_VENDOR_CODE_DIGITS:
                raise ValueError(
                    f"Vendor code '{vendor_code}' too long "
                    f"(>{self.MAX_VENDOR_CODE_DIGITS} digits after sanitization)"
                )

            # Use vendor code as temporary EAN (zero-pad to 13 digits)
            # Prefix with TEMP_EAN_PREFIX to indicate temporary/internal code
            temp_ean = f"{self.TEMP_EAN_PREFIX}{sanitized_code.zfill(self.MAX_VENDOR_CODE_DIGITS)}"

            vendor_column = f"{vendor_name}_name"

            product_data = {
                "ean": temp_ean,
                "functional_name": product_name[:50] if product_name else vendor_code,
                "description": product_name if product_name else f"Auto-created from {vendor_name} upload",
                vendor_column: vendor_code,
                "active": False,  # Mark as inactive until EAN assigned
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # NOTE: Use raw client to bypass tenant filter (products table has no tenant_id)
            result = self.db.client.table("products").insert(product_data).execute()

            if not result.data:
                raise Exception("Failed to create product")

            return temp_ean

        except Exception as e:
            # If duplicate (race condition), try to fetch it
            if "duplicate key" in str(e).lower():
                print(f"[BibbiProduct] Race condition detected, fetching existing product")
                # FIXED: Return formatted temp_ean instead of raw vendor_code
                matched = self._match_by_vendor_code(vendor_code, vendor_name)
                if matched:
                    return matched
                # If still not found, return properly formatted temp_ean with sanitization
                sanitized_code = ''.join(filter(str.isdigit, str(vendor_code)))
                return f"{self.TEMP_EAN_PREFIX}{sanitized_code.zfill(self.MAX_VENDOR_CODE_DIGITS)}"

            print(f"[BibbiProduct] Error creating product: {e}")
            # Fallback: return vendor code as-is (will likely fail FK constraint)
            raise Exception(f"Failed to create product: {str(e)}")

    def _update_vendor_mapping(
        self,
        ean: str,
        vendor_code: str,
        vendor_name: str
    ) -> None:
        """
        Update vendor-specific column in products table

        Args:
            ean: Product EAN
            vendor_code: Vendor's product code
            vendor_name: Vendor identifier
        """
        try:
            vendor_column = f"{vendor_name}_name"

            # NOTE: Use raw client to bypass tenant filter (products table has no tenant_id)
            self.db.client.table("products")\
                .update({
                    vendor_column: vendor_code,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("ean", ean)\
                .execute()

            print(f"[BibbiProduct] Updated vendor mapping: {ean} ← {vendor_code}")

        except Exception as e:
            print(f"[BibbiProduct] Error updating vendor mapping: {e}")
            # Don't raise - this is non-critical

    def get_unmapped_products(self, vendor_name: str) -> List[Dict[str, Any]]:
        """
        Get products that don't have vendor mapping

        Args:
            vendor_name: Vendor identifier

        Returns:
            List of products without vendor code
        """
        try:
            vendor_column = f"{vendor_name}_name"

            # NOTE: Use raw client to bypass tenant filter (products table has no tenant_id)
            result = self.db.client.table("products")\
                .select("ean, functional_name, description")\
                .is_(vendor_column, None)\
                .execute()

            return result.data or []

        except Exception as e:
            print(f"[BibbiProduct] Error getting unmapped products: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear product matching cache"""
        self._product_cache.clear()
        print("[BibbiProduct] Cache cleared")


def get_product_service(bibbi_db: BibbιDB) -> BibbιProductService:
    """
    Factory function to create product service

    Args:
        bibbi_db: BIBBI-specific Supabase client

    Returns:
        BibbιProductService instance
    """
    return BibbιProductService(bibbi_db)
