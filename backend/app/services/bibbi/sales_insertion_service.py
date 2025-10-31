"""
BIBBI Sales Insertion Service

Handles insertion of validated sales data into sales_unified table.

Pipeline Stage: Validation → **SALES INSERTION** → Complete

Features:
- Batch insert with configurable batch size (1000 rows default)
- Deduplication via unique constraint handling
- Transaction safety with rollback on errors
- Insertion statistics tracking
- Upload status updates
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from app.core.bibbi import BibbιDB, BIBBI_TENANT_ID


class InsertionResult:
    """Result of sales insertion operation"""

    def __init__(
        self,
        total_rows: int,
        inserted_rows: int,
        duplicate_rows: int,
        failed_rows: int,
        errors: List[Dict[str, Any]]
    ):
        self.total_rows = total_rows
        self.inserted_rows = inserted_rows
        self.duplicate_rows = duplicate_rows
        self.failed_rows = failed_rows
        self.errors = errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_rows": self.total_rows,
            "inserted_rows": self.inserted_rows,
            "duplicate_rows": self.duplicate_rows,
            "failed_rows": self.failed_rows,
            "insertion_success_rate": round(
                self.inserted_rows / self.total_rows * 100, 2
            ) if self.total_rows > 0 else 0,
            "errors": self.errors
        }


class BibbιSalesInsertionService:
    """
    Service for inserting validated BIBBI sales data

    Responsibilities:
    - Batch insert into sales_unified table
    - Handle duplicates gracefully
    - Track insertion statistics
    - Update upload status
    - Transaction safety
    """

    # Default batch size for bulk inserts
    DEFAULT_BATCH_SIZE = 1000

    def __init__(self, bibbi_db: BibbιDB):
        """
        Initialize sales insertion service

        Args:
            bibbi_db: BIBBI-specific Supabase client
        """
        self.db = bibbi_db
        # Cache for store details to avoid repeated queries
        self._store_cache: Dict[str, Dict[str, Any]] = {}
        # Cache for reseller names to avoid repeated queries
        self._reseller_cache: Dict[str, str] = {}

    def insert_validated_sales(
        self,
        validated_data: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        store_mapping: Optional[Dict[str, str]] = None
    ) -> InsertionResult:
        """
        Insert validated sales data into sales_unified table

        Handles:
        - Batch insertion for performance
        - Duplicate detection (unique constraint violations)
        - Error tracking per row
        - Transaction safety
        - Store identifier to UUID mapping

        Args:
            validated_data: List of validated sales records
            batch_size: Number of rows per batch (default: 1000)
            store_mapping: Dict mapping store_identifier → store_id (UUID)

        Returns:
            InsertionResult with statistics and errors

        Unique Constraint:
        (tenant_id, reseller_id, product_id, sale_date, store_id, quantity)

        This handles:
        - Liberty duplicate rows (same product, same store, same date, same quantity)
        - Living documents (Boxnox, Aromateque, Skins SA) re-uploading same data
        """
        batch_size = batch_size or self.DEFAULT_BATCH_SIZE
        store_mapping = store_mapping or {}

        total_rows = len(validated_data)
        inserted_rows = 0
        duplicate_rows = 0
        failed_rows = 0
        errors = []

        print(f"[BibbιSalesInsertion] Inserting {total_rows} rows (batch size: {batch_size})...")
        if store_mapping:
            print(f"[BibbιSalesInsertion] Using store mapping: {store_mapping}")

        # Process in batches
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch = validated_data[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1

            print(f"[BibbιSalesInsertion] Processing batch {batch_num} ({len(batch)} rows)...")

            batch_result = self._insert_batch(batch, batch_start, store_mapping)

            inserted_rows += batch_result["inserted"]
            duplicate_rows += batch_result["duplicates"]
            failed_rows += batch_result["failed"]
            errors.extend(batch_result["errors"])

        print(f"[BibbιSalesInsertion] Insertion complete:")
        print(f"  - Inserted: {inserted_rows}/{total_rows}")
        print(f"  - Duplicates: {duplicate_rows}")
        print(f"  - Failed: {failed_rows}")

        return InsertionResult(
            total_rows=total_rows,
            inserted_rows=inserted_rows,
            duplicate_rows=duplicate_rows,
            failed_rows=failed_rows,
            errors=errors
        )

    def _insert_batch(
        self,
        batch: List[Dict[str, Any]],
        offset: int,
        store_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Insert a single batch of rows

        Args:
            batch: List of rows to insert
            offset: Row number offset for error reporting
            store_mapping: Dict mapping store_identifier → store_id (UUID)

        Returns:
            Dictionary with inserted/duplicate/failed counts and errors
        """
        inserted = 0
        duplicates = 0
        failed = 0
        errors = []

        try:
            # Prepare batch data - ensure only valid BIBBI schema fields
            # BIBBI sales_unified schema (verified 2025-10-24 via Supabase MCP):
            # - id: auto-generated UUID PRIMARY KEY
            # - product_ean, reseller_id, store_id, customer_id (nullable), upload_id
            # - functional_name, sale_date, quantity, sales_local_currency, currency, sales_eur
            # - year, month, quarter, sales_channel, country, city
            # - created_at, updated_at
            # NOTE: Uses upload_id (NOT upload_batch_id) - FK to uploads.id

            batch_data = []
            for row in batch:
                # Clean row: remove fields not in BIBBI schema
                cleaned_row = {k: v for k, v in row.items() if k not in [
                    "sales_id",           # Auto-generated as 'id'
                    "tenant_id",          # Not in BIBBI schema (no multi-tenancy)
                    "batch_id",           # Use upload_id instead
                    "upload_batch_id",    # WRONG: Use upload_id instead
                    "vendor_name",        # Not in schema
                    "product_name_raw",   # Not in schema (temporary field)
                    "is_return",          # Not in schema
                    "return_quantity",    # Not in schema (quantity handles returns via negatives)
                    "local_currency",     # Use currency instead
                    "store_identifier",   # Not in schema (only store_id exists)
                ]}

                # Convert store_identifier to store_id using mapping
                store_identifier = row.get("store_identifier")
                if store_identifier and store_identifier in store_mapping:
                    store_id = store_mapping[store_identifier]
                    cleaned_row["store_id"] = store_id

                    # Populate geography fields from stores table
                    store_details = self._get_store_details(store_id)
                    if store_details:
                        # Only populate if not already set by processor
                        if not cleaned_row.get("country"):
                            cleaned_row["country"] = store_details.get("country")
                        if not cleaned_row.get("region"):
                            cleaned_row["region"] = store_details.get("region")
                        if not cleaned_row.get("city"):
                            cleaned_row["city"] = store_details.get("city")
                elif "store_id" not in cleaned_row:
                    # No mapping available and no store_id - this will fail FK constraint
                    print(f"[BibbιSalesInsertion] Warning: No store_id mapping for store_identifier='{store_identifier}'")

                # Populate reseller_name from reseller_id (denormalization for AI queries)
                if "reseller_id" in cleaned_row and not cleaned_row.get("reseller_name"):
                    reseller_name = self._get_reseller_name(cleaned_row["reseller_id"])
                    if reseller_name:
                        cleaned_row["reseller_name"] = reseller_name

                # Ensure timestamps
                if "created_at" not in cleaned_row:
                    cleaned_row["created_at"] = datetime.utcnow().isoformat()
                if "updated_at" not in cleaned_row:
                    cleaned_row["updated_at"] = datetime.utcnow().isoformat()

                batch_data.append(cleaned_row)

            # Attempt batch insert
            result = self.db.table("sales_unified").insert(batch_data).execute()

            if result.data:
                inserted = len(result.data)
                print(f"[BibbιSalesInsertion] Batch insert successful: {inserted} rows")

        except Exception as e:
            error_str = str(e).lower()

            # Check if it's a duplicate key violation
            if "duplicate key" in error_str or "unique constraint" in error_str:
                # Fall back to row-by-row insertion to identify duplicates
                print(f"[BibbιSalesInsertion] Batch duplicate detected, falling back to row-by-row insertion")
                row_result = self._insert_row_by_row(batch, offset, store_mapping)
                inserted = row_result["inserted"]
                duplicates = row_result["duplicates"]
                failed = row_result["failed"]
                errors = row_result["errors"]

            else:
                # Other error - mark entire batch as failed
                print(f"[BibbιSalesInsertion] Batch insert failed: {e}")
                failed = len(batch)
                for idx, row in enumerate(batch):
                    row_num = offset + idx + 1
                    errors.append({
                        "row_number": row_num,
                        "error_type": "insertion_error",
                        "error_message": str(e),
                        "product_ean": row.get("product_ean"),  # UPDATED: product_id → product_ean
                        "sale_date": row.get("sale_date")
                    })

        return {
            "inserted": inserted,
            "duplicates": duplicates,
            "failed": failed,
            "errors": errors
        }

    def _insert_row_by_row(
        self,
        batch: List[Dict[str, Any]],
        offset: int,
        store_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Insert rows one by one (fallback when batch insert fails)

        Used to identify which specific rows are duplicates vs failures.

        Args:
            batch: List of rows to insert
            offset: Row number offset for error reporting
            store_mapping: Dict mapping store_identifier → store_id (UUID)

        Returns:
            Dictionary with inserted/duplicate/failed counts and errors
        """
        inserted = 0
        duplicates = 0
        failed = 0
        errors = []

        for idx, row in enumerate(batch):
            row_num = offset + idx + 1

            try:
                # Clean row and convert store_identifier to store_id
                cleaned_row = {k: v for k, v in row.items() if k not in [
                    "sales_id",           # Auto-generated as 'id'
                    "tenant_id",          # Not in BIBBI schema
                    "batch_id",           # Use upload_id instead
                    "upload_batch_id",    # WRONG: Use upload_id instead
                    "vendor_name",        # Not in schema
                    "product_name_raw",   # Temporary field
                    "is_return",          # Not in schema
                    "return_quantity",    # Not in schema (quantity handles returns via negatives)
                    "local_currency",     # Use currency instead
                    "store_identifier",   # Not in schema (only store_id exists)
                ]}

                # Convert store_identifier to store_id using mapping
                store_identifier = row.get("store_identifier")
                if store_identifier and store_identifier in store_mapping:
                    cleaned_row["store_id"] = store_mapping[store_identifier]

                # Populate reseller_name from reseller_id (denormalization for AI queries)
                if "reseller_id" in cleaned_row and not cleaned_row.get("reseller_name"):
                    reseller_name = self._get_reseller_name(cleaned_row["reseller_id"])
                    if reseller_name:
                        cleaned_row["reseller_name"] = reseller_name

                # Ensure timestamps
                if "created_at" not in cleaned_row:
                    cleaned_row["created_at"] = datetime.utcnow().isoformat()
                if "updated_at" not in cleaned_row:
                    cleaned_row["updated_at"] = datetime.utcnow().isoformat()

                result = self.db.table("sales_unified").insert(cleaned_row).execute()

                if result.data:
                    inserted += 1

            except Exception as e:
                error_str = str(e).lower()

                if "duplicate key" in error_str or "unique constraint" in error_str:
                    # This is a duplicate - not an error, expected behavior
                    duplicates += 1
                    print(f"[BibbιSalesInsertion] Row {row_num}: Duplicate (skipped)")

                else:
                    # Actual error
                    failed += 1
                    errors.append({
                        "row_number": row_num,
                        "error_type": "insertion_error",
                        "error_message": str(e),
                        "product_ean": row.get("product_ean"),  # UPDATED: product_id → product_ean
                        "sale_date": row.get("sale_date"),
                        "store_id": row.get("store_id")
                    })
                    print(f"[BibbιSalesInsertion] Row {row_num}: Failed - {e}")

        return {
            "inserted": inserted,
            "duplicates": duplicates,
            "failed": failed,
            "errors": errors
        }

    def _get_store_details(self, store_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch store details for geography population (with caching)

        Args:
            store_id: Store UUID

        Returns:
            Dict with country, region, city, store_name or None
        """
        # Check cache first
        if store_id in self._store_cache:
            return self._store_cache[store_id]

        try:
            # Query stores table directly (no tenant filtering needed in BIBBI)
            result = self.db.table("stores")\
                .select("country, region, city, store_name")\
                .eq("store_id", store_id)\
                .execute()

            if result.data and len(result.data) > 0:
                store_details = result.data[0]
                # Cache for subsequent calls
                self._store_cache[store_id] = store_details
                return store_details
            else:
                print(f"[BibbιSalesInsertion] Store {store_id} not found in stores table")
                return None

        except Exception as e:
            print(f"[BibbιSalesInsertion] Error fetching store details: {e}")
            return None

    def _get_reseller_name(self, reseller_id: str) -> Optional[str]:
        """
        Fetch reseller name for denormalization (with caching)

        Args:
            reseller_id: Reseller UUID

        Returns:
            Reseller name string or None
        """
        # Check cache first
        if reseller_id in self._reseller_cache:
            return self._reseller_cache[reseller_id]

        try:
            # Query resellers table directly (no tenant filtering needed in BIBBI)
            # NOTE: BIBBI resellers table uses 'id' (not 'reseller_id') and 'reseller' (not 'name')
            result = self.db.table("resellers")\
                .select("reseller")\
                .eq("id", reseller_id)\
                .execute()

            if result.data and len(result.data) > 0:
                reseller_name = result.data[0].get("reseller")
                # Cache for subsequent calls
                self._reseller_cache[reseller_id] = reseller_name
                return reseller_name
            else:
                print(f"[BibbιSalesInsertion] Reseller {reseller_id} not found in resellers table")
                return None

        except Exception as e:
            print(f"[BibbιSalesInsertion] Error fetching reseller name: {e}")
            return None

    def update_upload_status(
        self,
        upload_id: str,
        insertion_result: InsertionResult,
        status: str = "completed"
    ) -> None:
        """
        Update upload record with insertion results

        Args:
            upload_id: Upload UUID
            insertion_result: Result from insert_validated_sales
            status: Upload status (completed, failed, partial)
        """
        try:
            # Determine final status
            if insertion_result.failed_rows > 0 and insertion_result.inserted_rows == 0:
                final_status = "failed"
            elif insertion_result.failed_rows > 0:
                final_status = "partial"
            else:
                final_status = "completed"

            # Build update data
            update_data = {
                "upload_status": final_status,
                "rows_processed": insertion_result.total_rows,
                "rows_inserted": insertion_result.inserted_rows,
                "rows_duplicated": insertion_result.duplicate_rows,
                "rows_failed": insertion_result.failed_rows,
                "processing_completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Store insertion errors if any
            if insertion_result.errors:
                update_data["processing_errors"] = {
                    "insertion_errors": insertion_result.errors,
                    "error_count": len(insertion_result.errors)
                }

            self.db.table("uploads")\
                .update(update_data)\
                .eq("upload_id", upload_id)\
                .execute()

            print(f"[BibbιSalesInsertion] Updated upload status: {upload_id} → {final_status}")

        except Exception as e:
            print(f"[BibbιSalesInsertion] Error updating upload status: {e}")
            # Don't raise - insertion succeeded even if status update failed

    def get_insertion_statistics(
        self,
        upload_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get insertion statistics for an upload

        Args:
            upload_id: Upload UUID

        Returns:
            Dictionary with insertion statistics or None
        """
        try:
            result = self.db.table("uploads")\
                .select("rows_processed, rows_inserted, rows_duplicated, rows_failed, upload_status")\
                .eq("upload_id", upload_id)\
                .execute()

            if result.data and len(result.data) > 0:
                upload = result.data[0]
                return {
                    "upload_id": upload_id,
                    "status": upload.get("upload_status"),
                    "total_rows": upload.get("rows_processed", 0),
                    "inserted_rows": upload.get("rows_inserted", 0),
                    "duplicate_rows": upload.get("rows_duplicated", 0),
                    "failed_rows": upload.get("rows_failed", 0),
                    "success_rate": round(
                        upload.get("rows_inserted", 0) / upload.get("rows_processed", 1) * 100, 2
                    )
                }

            return None

        except Exception as e:
            print(f"[BibbιSalesInsertion] Error getting insertion statistics: {e}")
            return None

    def rollback_upload(
        self,
        upload_id: str
    ) -> int:
        """
        Rollback/delete all sales records for an upload

        Useful for:
        - Correcting upload errors
        - Re-processing with updated mappings
        - Testing

        Args:
            upload_id: Upload UUID (sales_unified.upload_id)

        Returns:
            Number of rows deleted
        """
        try:
            # Delete all sales records with this upload_id
            result = self.db.table("sales_unified")\
                .delete()\
                .eq("upload_id", upload_id)\
                .execute()

            deleted_count = len(result.data) if result.data else 0

            print(f"[BibbιSalesInsertion] Rollback complete: {deleted_count} rows deleted")

            # Update upload status to rolled_back
            self.db.table("uploads")\
                .update({
                    "status": "rolled_back",
                    "rows_inserted": 0,
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq("id", upload_id)\
                .execute()

            return deleted_count

        except Exception as e:
            print(f"[BibbιSalesInsertion] Error during rollback: {e}")
            raise Exception(f"Failed to rollback upload: {str(e)}")

    def get_duplicate_report(
        self,
        reseller_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate duplicate detection report

        Identifies potential duplicate records based on unique constraint fields.

        Args:
            reseller_id: Reseller UUID
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)

        Returns:
            List of duplicate groups
        """
        try:
            # This would require a GROUP BY query which Supabase PostgREST doesn't support well
            # For now, return empty list and note that duplicates are handled during insertion
            print(f"[BibbιSalesInsertion] Duplicate report: Duplicates are automatically handled during insertion")
            return []

        except Exception as e:
            print(f"[BibbιSalesInsertion] Error generating duplicate report: {e}")
            return []


def get_sales_insertion_service(bibbi_db: BibbιDB) -> BibbιSalesInsertionService:
    """
    Factory function to create sales insertion service

    Args:
        bibbi_db: BIBBI-specific Supabase client

    Returns:
        BibbιSalesInsertionService instance
    """
    return BibbιSalesInsertionService(bibbi_db)
