"""
BIBBI Product Mapping Service

Handles product code → EAN mapping for resellers without EAN codes.

Pipeline Stage: Processing → **PRODUCT MAPPING** → Validation

Critical for:
- Galilu: Uses product names instead of EAN codes
- CDLC: May need EAN conversion to functional name

Features:
- Fuzzy matching for product name variations
- In-memory caching for performance
- CRUD operations for product mappings
- Batch mapping operations
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from difflib import SequenceMatcher

from app.core.bibbi import BibbιDB, BIBBI_TENANT_ID


class BibbιProductMappingService:
    """
    Service for BIBBI product code → EAN mapping

    Responsibilities:
    - Map reseller product codes to EAN codes
    - Fuzzy match product names to handle variations
    - Cache mappings for performance
    - Manage product_reseller_mappings table
    """

    # Fuzzy matching threshold (85% similarity)
    FUZZY_MATCH_THRESHOLD = 0.85

    def __init__(self, bibbi_db: BibbιDB):
        """
        Initialize product mapping service

        Args:
            bibbi_db: BIBBI-specific Supabase client
        """
        self.db = bibbi_db
        # Cache: {reseller_id:product_code -> ean}
        self._mapping_cache: Dict[str, str] = {}

    def get_ean_by_product_code(
        self,
        reseller_id: str,
        product_code: str,
        use_fuzzy_match: bool = True
    ) -> Optional[str]:
        """
        Get EAN for a reseller product code

        Supports both exact and fuzzy matching for product name variations.

        Args:
            reseller_id: Reseller UUID
            product_code: Product code or name from reseller file
            use_fuzzy_match: Enable fuzzy matching (default: True)

        Returns:
            EAN code (13 digits) or None if not found

        Example:
            # Exact match
            ean = service.get_ean_by_product_code("abc-123", "PRODUCT_ABC")

            # Fuzzy match (handles variations)
            ean = service.get_ean_by_product_code("abc-123", "Product ABC  ")
            # Returns same EAN even with different spacing/case
        """
        # Normalize product code
        normalized_code = self._normalize_product_code(product_code)

        # Check cache first
        cache_key = self._make_cache_key(reseller_id, normalized_code)
        if cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]

        # Try exact match
        mapping = self._find_exact_mapping(reseller_id, normalized_code)
        if mapping:
            ean = mapping["product_id"]
            self._mapping_cache[cache_key] = ean
            return ean

        # Try fuzzy match if enabled
        if use_fuzzy_match:
            mapping = self._find_fuzzy_mapping(reseller_id, normalized_code)
            if mapping:
                ean = mapping["product_id"]
                self._mapping_cache[cache_key] = ean
                return ean

        return None

    def bulk_get_ean_mappings(
        self,
        reseller_id: str,
        product_codes: List[str]
    ) -> Dict[str, Optional[str]]:
        """
        Batch get EAN mappings for multiple product codes

        More efficient than calling get_ean_by_product_code() in a loop.

        Args:
            reseller_id: Reseller UUID
            product_codes: List of product codes to map

        Returns:
            Dictionary mapping product_code → EAN (or None if not found)

        Example:
            mappings = service.bulk_get_ean_mappings(
                "abc-123",
                ["PRODUCT_A", "PRODUCT_B", "PRODUCT_C"]
            )
            # Returns: {"PRODUCT_A": "1234567890123", "PRODUCT_B": None, ...}
        """
        result = {}

        for product_code in product_codes:
            ean = self.get_ean_by_product_code(reseller_id, product_code)
            result[product_code] = ean

        return result

    def create_mapping(
        self,
        reseller_id: str,
        product_code: str,
        ean: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create new product mapping

        Args:
            reseller_id: Reseller UUID
            product_code: Reseller's product code or name
            ean: EAN code (13 digits)
            metadata: Optional metadata (product_name, category, etc.)

        Returns:
            mapping_id: UUID of created mapping

        Raises:
            ValueError: If EAN format invalid or mapping exists
            Exception: If creation fails

        Example:
            mapping_id = service.create_mapping(
                reseller_id="abc-123",
                product_code="GALILU_PRODUCT_A",
                ean="1234567890123",
                metadata={"product_name": "Product A", "category": "Electronics"}
            )
        """
        # Validate EAN format
        if not self._validate_ean(ean):
            raise ValueError(f"Invalid EAN format: {ean}")

        # Normalize product code
        normalized_code = self._normalize_product_code(product_code)

        # Check for existing mapping
        existing = self._find_exact_mapping(reseller_id, normalized_code)
        if existing:
            raise ValueError(f"Mapping already exists for product code: {product_code}")

        # Generate UUID
        mapping_id = str(uuid.uuid4())

        # Build mapping record
        mapping_record = {
            "mapping_id": mapping_id,
            "reseller_id": reseller_id,
            "product_id": ean,  # EAN stored in product_id column
            "reseller_product_code": normalized_code,
            "mapping_metadata": metadata or {},
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            # tenant_id automatically added by BibbιSupabaseClient
        }

        try:
            result = self.db.table("product_reseller_mappings").insert(mapping_record).execute()

            if not result.data:
                raise Exception("Failed to create mapping record")

            # Update cache
            cache_key = self._make_cache_key(reseller_id, normalized_code)
            self._mapping_cache[cache_key] = ean

            print(f"[BibbιProductMapping] Created mapping: {product_code} → {ean}")
            return mapping_id

        except Exception as e:
            print(f"[BibbιProductMapping] Error creating mapping: {e}")
            raise Exception(f"Failed to create product mapping: {str(e)}")

    def bulk_create_mappings(
        self,
        reseller_id: str,
        mappings: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Batch create multiple product mappings

        Args:
            reseller_id: Reseller UUID
            mappings: List of mapping dicts with product_code, ean, metadata

        Returns:
            Dictionary mapping product_code → mapping_id

        Example:
            results = service.bulk_create_mappings(
                "abc-123",
                [
                    {"product_code": "PRODUCT_A", "ean": "1234567890123"},
                    {"product_code": "PRODUCT_B", "ean": "1234567890124"}
                ]
            )
        """
        results = {}

        for mapping in mappings:
            product_code = mapping.get("product_code")
            ean = mapping.get("ean")
            metadata = mapping.get("metadata")

            if not product_code or not ean:
                continue

            try:
                mapping_id = self.create_mapping(reseller_id, product_code, ean, metadata)
                results[product_code] = mapping_id
            except Exception as e:
                print(f"[BibbιProductMapping] Error creating mapping for {product_code}: {e}")
                continue

        return results

    def update_mapping(
        self,
        mapping_id: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update existing product mapping

        Args:
            mapping_id: Mapping UUID
            updates: Fields to update (ean, product_code, metadata, is_active)

        Raises:
            Exception: If update fails
        """
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }

        # Only update allowed fields
        allowed_fields = ["product_id", "reseller_product_code", "mapping_metadata", "is_active"]
        for field in allowed_fields:
            if field in updates:
                update_data[field] = updates[field]

        try:
            self.db.table("product_reseller_mappings")\
                .update(update_data)\
                .eq("mapping_id", mapping_id)\
                .execute()

            # Clear cache on update
            self.clear_cache()

            print(f"[BibbιProductMapping] Updated mapping: {mapping_id}")

        except Exception as e:
            print(f"[BibbιProductMapping] Error updating mapping: {e}")
            raise Exception(f"Failed to update mapping: {str(e)}")

    def delete_mapping(self, mapping_id: str) -> None:
        """
        Delete product mapping

        Args:
            mapping_id: Mapping UUID

        Raises:
            Exception: If deletion fails
        """
        try:
            self.db.table("product_reseller_mappings")\
                .delete()\
                .eq("mapping_id", mapping_id)\
                .execute()

            # Clear cache on deletion
            self.clear_cache()

            print(f"[BibbιProductMapping] Deleted mapping: {mapping_id}")

        except Exception as e:
            print(f"[BibbιProductMapping] Error deleting mapping: {e}")
            raise Exception(f"Failed to delete mapping: {str(e)}")

    def get_reseller_mappings(
        self,
        reseller_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all product mappings for a reseller

        Args:
            reseller_id: Reseller UUID
            active_only: Only return active mappings (default: True)

        Returns:
            List of mapping records
        """
        try:
            query = self.db.table("product_reseller_mappings")\
                .select("*")\
                .eq("reseller_id", reseller_id)

            if active_only:
                query = query.eq("is_active", True)

            result = query.order("reseller_product_code").execute()

            return result.data or []

        except Exception as e:
            print(f"[BibbιProductMapping] Error getting reseller mappings: {e}")
            return []

    def get_unmapped_products(
        self,
        reseller_id: str,
        product_codes: List[str]
    ) -> List[str]:
        """
        Find product codes that don't have mappings

        Useful for identifying missing mappings that need to be created.

        Args:
            reseller_id: Reseller UUID
            product_codes: List of product codes to check

        Returns:
            List of unmapped product codes
        """
        unmapped = []

        for product_code in product_codes:
            ean = self.get_ean_by_product_code(reseller_id, product_code, use_fuzzy_match=False)
            if ean is None:
                unmapped.append(product_code)

        return unmapped

    def _find_exact_mapping(
        self,
        reseller_id: str,
        product_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find exact product mapping

        Args:
            reseller_id: Reseller UUID
            product_code: Normalized product code

        Returns:
            Mapping record or None
        """
        try:
            result = self.db.table("product_reseller_mappings")\
                .select("*")\
                .eq("reseller_id", reseller_id)\
                .eq("reseller_product_code", product_code)\
                .eq("is_active", True)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            print(f"[BibbιProductMapping] Error finding exact mapping: {e}")
            return None

    def _find_fuzzy_mapping(
        self,
        reseller_id: str,
        product_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find product mapping using fuzzy matching

        Handles variations in product names (spacing, case, punctuation).

        Args:
            reseller_id: Reseller UUID
            product_code: Normalized product code

        Returns:
            Best matching mapping record or None
        """
        try:
            # Get all mappings for reseller
            result = self.db.table("product_reseller_mappings")\
                .select("*")\
                .eq("reseller_id", reseller_id)\
                .eq("is_active", True)\
                .execute()

            if not result.data:
                return None

            # Find best fuzzy match
            best_match = None
            best_score = 0.0

            for mapping in result.data:
                stored_code = mapping.get("reseller_product_code", "")
                similarity = self._calculate_similarity(product_code, stored_code)

                if similarity > best_score and similarity >= self.FUZZY_MATCH_THRESHOLD:
                    best_score = similarity
                    best_match = mapping

            if best_match:
                print(f"[BibbιProductMapping] Fuzzy match: '{product_code}' → '{best_match['reseller_product_code']}' (score: {best_score:.2f})")

            return best_match

        except Exception as e:
            print(f"[BibbιProductMapping] Error finding fuzzy mapping: {e}")
            return None

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity ratio between two strings

        Uses SequenceMatcher for similarity comparison.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _normalize_product_code(self, product_code: str) -> str:
        """
        Normalize product code for consistent matching

        Handles:
        - Strip whitespace
        - Lowercase
        - Remove extra spaces

        Args:
            product_code: Raw product code

        Returns:
            Normalized product code
        """
        return " ".join(product_code.strip().lower().split())

    def _validate_ean(self, ean: str) -> bool:
        """
        Validate EAN format

        Args:
            ean: EAN code to validate

        Returns:
            True if valid 13-digit EAN
        """
        if not isinstance(ean, str):
            return False

        if len(ean) != 13:
            return False

        if not ean.isdigit():
            return False

        return True

    def _make_cache_key(self, reseller_id: str, product_code: str) -> str:
        """
        Generate cache key

        Args:
            reseller_id: Reseller UUID
            product_code: Normalized product code

        Returns:
            Cache key string
        """
        return f"{reseller_id}:{product_code}"

    def clear_cache(self) -> None:
        """
        Clear in-memory mapping cache

        Use when mappings may be stale (after updates/deletes).
        """
        self._mapping_cache.clear()
        print("[BibbιProductMapping] Cache cleared")


def get_product_mapping_service(bibbi_db: BibbιDB) -> BibbιProductMappingService:
    """
    Factory function to create product mapping service

    Args:
        bibbi_db: BIBBI-specific Supabase client

    Returns:
        BibbιProductMappingService instance
    """
    return BibbιProductMappingService(bibbi_db)
