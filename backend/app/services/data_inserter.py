"""
Data insertion service for processed records
"""

from typing import List, Dict, Any, Tuple
from supabase import Client


class DataInserter:
    """Insert validated data into database"""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    def insert_sellout_entries(
        self,
        records: List[Dict[str, Any]],
        mode: str = "append"
    ) -> Tuple[int, int]:
        """
        Insert sellout entries into database

        Args:
            records: List of record dictionaries
            mode: "append" or "replace"

        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not records:
            return 0, 0

        # Get user_id from first record
        user_id = records[0].get("user_id")

        # Handle replace mode
        if mode == "replace" and user_id:
            self._delete_existing_data(user_id, "sellout_entries2")

        # Insert in batches
        batch_size = 1000
        successful = 0
        failed = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            try:
                result = self.supabase.table("sellout_entries2").insert(batch).execute()

                if result.data:
                    successful += len(result.data)
                else:
                    failed += len(batch)

            except Exception as e:
                print(f"Batch insert error: {e}")
                failed += len(batch)

                # Try inserting records one by one
                for record in batch:
                    try:
                        result = self.supabase.table("sellout_entries2").insert(record).execute()
                        if result.data:
                            successful += 1
                            failed -= 1
                    except Exception as single_error:
                        print(f"Single record insert error: {single_error}")
                        # Record remains in failed count

        return successful, failed

    def insert_ecommerce_orders(
        self,
        records: List[Dict[str, Any]],
        mode: str = "append"
    ) -> Tuple[int, int]:
        """
        Insert ecommerce orders into database

        Args:
            records: List of order dictionaries
            mode: "append" or "replace"

        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not records:
            return 0, 0

        # Get user_id from first record
        user_id = records[0].get("user_id")

        # Handle replace mode
        if mode == "replace" and user_id:
            self._delete_existing_data(user_id, "ecommerce_orders")

        # Insert in batches
        batch_size = 1000
        successful = 0
        failed = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]

            try:
                result = self.supabase.table("ecommerce_orders").insert(batch).execute()

                if result.data:
                    successful += len(result.data)
                else:
                    failed += len(batch)

            except Exception as e:
                print(f"Batch insert error: {e}")
                failed += len(batch)

                # Try inserting records one by one
                for record in batch:
                    try:
                        result = self.supabase.table("ecommerce_orders").insert(record).execute()
                        if result.data:
                            successful += 1
                            failed -= 1
                    except Exception as single_error:
                        print(f"Single record insert error: {single_error}")

        return successful, failed

    def _delete_existing_data(self, user_id: str, table_name: str) -> int:
        """
        Delete existing data for user (replace mode)

        Args:
            user_id: User identifier
            table_name: Target table name

        Returns:
            Number of deleted records
        """
        try:
            result = self.supabase.table(table_name).delete().eq("user_id", user_id).execute()
            return len(result.data) if result.data else 0

        except Exception as e:
            print(f"Error deleting existing data: {e}")
            return 0

    def check_duplicates(
        self,
        user_id: str,
        table_name: str,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Check for duplicate records

        Args:
            user_id: User identifier
            table_name: Target table name
            records: Records to check

        Returns:
            List of non-duplicate records
        """
        if not records or table_name != "sellout_entries2":
            return records

        # For sellout_entries2, check duplicates based on:
        # product_ean, reseller, month, year

        unique_records = []

        for record in records:
            ean = record.get("product_ean")
            reseller = record.get("reseller")
            month = record.get("month")
            year = record.get("year")

            if not all([ean, month, year]):
                unique_records.append(record)
                continue

            # Check if record exists
            try:
                query = self.supabase.table(table_name).select("id").eq("user_id", user_id).eq("product_ean", ean).eq("month", month).eq("year", year)

                if reseller:
                    query = query.eq("reseller", reseller)

                result = query.execute()

                if not result.data:
                    unique_records.append(record)

            except Exception as e:
                print(f"Duplicate check error: {e}")
                unique_records.append(record)

        return unique_records
