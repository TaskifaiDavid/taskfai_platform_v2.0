"""
BIBBI Store Service

Handles store auto-creation, deduplication, and metadata enrichment.

Pipeline Stage: Processing → **STORE CREATION** → Sales Insertion

Features:
- get_or_create_store() with automatic creation
- Store deduplication via unique constraint (tenant_id, reseller_id, store_identifier)
- Metadata enrichment (country, city, store_type)
- In-memory caching for performance
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.core.bibbi import BibbιDB, BIBBI_TENANT_ID


class BibbιStoreService:
    """
    Service for BIBBI store management

    Responsibilities:
    - Auto-create stores from processor data
    - Deduplicate stores (reseller_id + store_identifier)
    - Enrich store metadata
    - Cache store lookups for performance
    """

    def __init__(self, bibbi_db: BibbιDB):
        """
        Initialize store service

        Args:
            bibbi_db: BIBBI-specific Supabase client
        """
        self.db = bibbi_db
        # In-memory cache: {cache_key -> store_id}
        self._store_cache: Dict[str, str] = {}

    def get_or_create_store(
        self,
        reseller_id: str,
        store_data: Dict[str, Any]
    ) -> str:
        """
        Get existing store or create new one

        Uses unique constraint: (tenant_id, reseller_id, store_identifier)

        Auto-creates stores with metadata enrichment:
        - store_name: Descriptive name
        - store_type: "physical" or "online"
        - country: Store country
        - city: Store city (optional)

        Args:
            reseller_id: Reseller UUID
            store_data: Store information from processor
                Required fields:
                - store_identifier: Unique store code (e.g., "flagship", "online")
                - store_name: Human-readable name
                Optional fields:
                - store_type: "physical" or "online" (default: "physical")
                - country: Country name
                - city: City name
                - address: Full address
                - postal_code: Postal/ZIP code

        Returns:
            store_id: UUID of existing or newly created store

        Raises:
            ValueError: If required fields missing
            Exception: If database operation fails

        Example:
            store_id = service.get_or_create_store(
                reseller_id="abc-123",
                store_data={
                    "store_identifier": "flagship",
                    "store_name": "Liberty Flagship",
                    "store_type": "physical",
                    "city": "London",
                    "country": "United Kingdom"
                }
            )
        """
        # Validate required fields
        # BIBBI uses store_code (not store_identifier)
        store_code = store_data.get("store_identifier") or store_data.get("store_code")
        store_name = store_data.get("store_name")

        if not store_code:
            raise ValueError("store_code/store_identifier is required")
        if not store_name:
            raise ValueError("store_name is required")

        # Check cache first
        cache_key = self._make_cache_key(reseller_id, store_code)
        if cache_key in self._store_cache:
            return self._store_cache[cache_key]

        # Check if store exists
        existing_store = self._find_store(reseller_id, store_code)

        if existing_store:
            store_id = existing_store["store_id"]
            self._store_cache[cache_key] = store_id
            print(f"[BibbιStore] Found existing store: {store_code} → {store_id}")
            return store_id

        # Create new store (ensure store_code is in store_data)
        store_data_with_code = {**store_data, "store_code": store_code}
        store_id = self._create_store(reseller_id, store_data_with_code)
        self._store_cache[cache_key] = store_id

        print(f"[BibbιStore] Created new store: {store_code} → {store_id}")
        return store_id

    def bulk_get_or_create_stores(
        self,
        reseller_id: str,
        stores_data: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Batch get or create multiple stores

        More efficient than calling get_or_create_store() in a loop.

        Args:
            reseller_id: Reseller UUID
            stores_data: List of store data dictionaries

        Returns:
            Dictionary mapping store_identifier → store_id

        Example:
            mapping = service.bulk_get_or_create_stores(
                reseller_id="abc-123",
                stores_data=[
                    {"store_identifier": "flagship", "store_name": "Flagship"},
                    {"store_identifier": "online", "store_name": "Online"}
                ]
            )
            # Returns: {"flagship": "uuid-1", "online": "uuid-2"}
        """
        store_mapping = {}

        for store_data in stores_data:
            store_identifier = store_data.get("store_identifier")
            if not store_identifier:
                continue

            try:
                store_id = self.get_or_create_store(reseller_id, store_data)
                store_mapping[store_identifier] = store_id
            except Exception as e:
                print(f"[BibbιStore] Error processing store {store_identifier}: {e}")
                continue

        return store_mapping

    def _find_store(
        self,
        reseller_id: str,
        store_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find existing store by reseller and store_code

        Args:
            reseller_id: Reseller UUID
            store_code: Store code (BIBBI uses store_code, not store_identifier)

        Returns:
            Store record or None if not found
        """
        try:
            result = self.db.table("stores")\
                .select("*")\
                .eq("reseller_id", reseller_id)\
                .eq("store_code", store_code)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            print(f"[BibbιStore] Error finding store: {e}")
            return None

    def _create_store(
        self,
        reseller_id: str,
        store_data: Dict[str, Any]
    ) -> str:
        """
        Create new store record

        Args:
            reseller_id: Reseller UUID
            store_data: Store information

        Returns:
            store_id: UUID of created store

        Raises:
            Exception: If creation fails
        """
        # Generate UUID
        store_id = str(uuid.uuid4())

        # Build store record - BIBBI uses store_code (not store_identifier)
        store_record = {
            "store_id": store_id,
            "reseller_id": reseller_id,
            "store_code": store_data["store_code"],  # Changed from store_identifier
            "store_name": store_data["store_name"],
            "country": store_data.get("country"),
            "region": store_data.get("region"),
            "city": store_data.get("city"),
            "address": store_data.get("address"),
            "postal_code": store_data.get("postal_code"),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            result = self.db.table("stores").insert(store_record).execute()

            if not result.data:
                raise Exception("Failed to create store record")

            return store_id

        except Exception as e:
            # Check if it's a duplicate error (race condition)
            if "duplicate key" in str(e).lower():
                print(f"[BibbιStore] Race condition detected, re-fetching store")
                existing = self._find_store(reseller_id, store_data["store_code"])
                if existing:
                    return existing["store_id"]

            print(f"[BibbιStore] Error creating store: {e}")
            raise Exception(f"Failed to create store: {str(e)}")

    def update_store_metadata(
        self,
        store_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Update store metadata

        Allows enrichment of store information after creation.

        Args:
            store_id: Store UUID
            metadata: Fields to update (country, city, address, etc.)

        Raises:
            Exception: If update fails
        """
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }

        # Only update provided fields
        allowed_fields = ["store_name", "store_type", "country", "city", "address", "postal_code", "is_active"]
        for field in allowed_fields:
            if field in metadata:
                update_data[field] = metadata[field]

        try:
            self.db.table("stores")\
                .update(update_data)\
                .eq("store_id", store_id)\
                .execute()

            print(f"[BibbιStore] Updated store metadata: {store_id}")

        except Exception as e:
            print(f"[BibbιStore] Error updating store metadata: {e}")
            raise Exception(f"Failed to update store metadata: {str(e)}")

    def get_store_by_id(self, store_id: str) -> Optional[Dict[str, Any]]:
        """
        Get store record by ID

        Args:
            store_id: Store UUID

        Returns:
            Store record or None if not found
        """
        try:
            result = self.db.table("stores")\
                .select("*")\
                .eq("store_id", store_id)\
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

            return None

        except Exception as e:
            print(f"[BibbιStore] Error getting store: {e}")
            return None

    def get_reseller_stores(self, reseller_id: str) -> List[Dict[str, Any]]:
        """
        Get all stores for a reseller

        Args:
            reseller_id: Reseller UUID

        Returns:
            List of store records
        """
        try:
            result = self.db.table("stores")\
                .select("*")\
                .eq("reseller_id", reseller_id)\
                .order("store_name")\
                .execute()

            return result.data or []

        except Exception as e:
            print(f"[BibbιStore] Error getting reseller stores: {e}")
            return []

    def deactivate_store(self, store_id: str) -> None:
        """
        Deactivate a store

        Marks store as inactive without deleting historical data.

        Args:
            store_id: Store UUID

        Raises:
            Exception: If update fails
        """
        try:
            self.db.table("stores")\
                .update({
                    "is_active": False,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("store_id", store_id)\
                .execute()

            print(f"[BibbιStore] Deactivated store: {store_id}")

        except Exception as e:
            print(f"[BibbιStore] Error deactivating store: {e}")
            raise Exception(f"Failed to deactivate store: {str(e)}")

    def clear_cache(self) -> None:
        """
        Clear in-memory store cache

        Use when cache may be stale (e.g., after bulk operations).
        """
        self._store_cache.clear()
        print("[BibbιStore] Cache cleared")

    def _make_cache_key(self, reseller_id: str, store_code: str) -> str:
        """
        Generate cache key for store lookup

        Args:
            reseller_id: Reseller UUID
            store_code: Store code

        Returns:
            Cache key string
        """
        return f"{reseller_id}:{store_code}"


def get_store_service(bibbi_db: BibbιDB) -> BibbιStoreService:
    """
    Factory function to create store service

    Args:
        bibbi_db: BIBBI-specific Supabase client

    Returns:
        BibbιStoreService instance
    """
    return BibbιStoreService(bibbi_db)
