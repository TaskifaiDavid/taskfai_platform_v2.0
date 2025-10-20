"""
Liberty Processor for Demo Tenant

Processes Liberty "Continuity Supplier Size Report" files with store-level extraction.
Extracts Flagship (physical store in London) and Internet (online) sales separately.
"""

import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import openpyxl
from supabase import create_client, Client


class LibertyProcessor:
    """Process Liberty vendor files for demo tenant"""

    # Fixed column positions (0-based index)
    COLUMN_MAPPING = {
        "product_name": 5,           # Column F - Liberty product name
        "flagship_qty": 14,          # Column O - Flagship Actual Quantity
        "flagship_sales_gbp": 15,    # Column P - Flagship Actual Sales (GBP)
        "internet_qty": 18,          # Column S - Internet Actual Quantity
        "internet_sales_gbp": 19,    # Column T - Internet Actual Sales (GBP)
    }

    # Currency conversion rate
    GBP_TO_EUR = 1.17

    def __init__(self):
        """Initialize processor with BIBBI Supabase connection for product mapping"""
        self.bibbi_supabase: Optional[Client] = None
        self._init_bibbi_connection()

    def _init_bibbi_connection(self):
        """Initialize connection to BIBBI Supabase for product name lookups"""
        try:
            # BIBBI Supabase credentials from environment
            bibbi_url = os.getenv("BIBBI_SUPABASE_URL", "https://edckqdrbgtnnjfnshjfq.supabase.co")
            bibbi_key = os.getenv("BIBBI_SUPABASE_SERVICE_KEY")

            if bibbi_key:
                self.bibbi_supabase = create_client(bibbi_url, bibbi_key)
                print("[LibertyProcessor] Connected to BIBBI Supabase for product mapping")
            else:
                print("[LibertyProcessor] WARNING: BIBBI_SUPABASE_SERVICE_KEY not set, product mapping disabled")
        except Exception as e:
            print(f"[LibertyProcessor] Failed to connect to BIBBI Supabase: {e}")

    def _extract_date_from_filename(self, filename: str) -> tuple[int, int, int]:
        """
        Extract date from Liberty filename pattern: DD-MM-YYYY

        Returns:
            Tuple of (year, month, day)
        """
        # Pattern: "Continuity Supplier Size Report 27-07-2025.xlsx"
        pattern = r"(\d{2})[-_](\d{2})[-_](\d{4})"
        match = re.search(pattern, filename)

        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))

            # Apply -1 week logic as per Liberty instructions
            date_obj = datetime(year, month, day) - timedelta(weeks=1)
            return date_obj.year, date_obj.month, date_obj.day

        # Fallback to current date if pattern not found
        now = datetime.now()
        return now.year, now.month, now.day

    def _map_product_name(self, liberty_name: str) -> str:
        """
        Map Liberty product name to functional name using BIBBI database

        Args:
            liberty_name: Raw product name from Liberty file

        Returns:
            Mapped functional name (uppercase) or original if no mapping found
        """
        if not self.bibbi_supabase or not liberty_name:
            return liberty_name.upper() if liberty_name else ""

        try:
            # Query BIBBI products table for liberty_name mapping
            result = self.bibbi_supabase.table("products")\
                .select("functional_name")\
                .eq("liberty_name", liberty_name.strip())\
                .execute()

            if result.data and len(result.data) > 0:
                functional_name = result.data[0].get("functional_name")
                if functional_name:
                    print(f"[LibertyProcessor] Mapped '{liberty_name}' → '{functional_name}'")
                    return functional_name.upper()
        except Exception as e:
            print(f"[LibertyProcessor] Product mapping failed for '{liberty_name}': {e}")

        # Fallback to raw Liberty name in uppercase
        return liberty_name.upper() if liberty_name else ""

    def _clean_numeric_value(self, value) -> Optional[float]:
        """Clean and convert numeric values, handling parentheses as negatives"""
        if value is None or value == "":
            return None

        try:
            # Convert to string for processing
            str_val = str(value).strip()

            # Check for parentheses (negative values/returns)
            is_negative = str_val.startswith("(") and str_val.endswith(")")
            if is_negative:
                str_val = str_val[1:-1]  # Remove parentheses

            # Remove currency symbols and commas
            str_val = str_val.replace("£", "").replace(",", "").strip()

            if not str_val or str_val == "-":
                return None

            numeric_val = float(str_val)
            return -numeric_val if is_negative else numeric_val
        except (ValueError, TypeError):
            return None

    def _is_total_row(self, row: tuple) -> bool:
        """Check if row is a total/summary row"""
        for cell_val in row:
            if cell_val and isinstance(cell_val, str):
                val_lower = str(cell_val).lower()
                if any(word in val_lower for word in ['total', 'sum', 'grand total', 'subtotal']) or \
                   val_lower.endswith(' total'):
                    return True
        return False

    def _is_duplicate_row(
        self,
        current_row: Dict,
        previous_rows: List[Dict],
        max_distance: int = 2
    ) -> bool:
        """
        Check if current row is duplicate of recent previous rows

        Liberty has consecutive duplicate pairs - check within max_distance rows
        """
        if not previous_rows:
            return False

        # Check last max_distance rows
        for prev_row in previous_rows[-max_distance:]:
            # Compare key fields
            if (current_row.get("functional_name") == prev_row.get("functional_name") and
                current_row.get("quantity") == prev_row.get("quantity") and
                current_row.get("sales_gbp") == prev_row.get("sales_gbp") and
                current_row.get("store_identifier") == prev_row.get("store_identifier")):
                return True

        return False

    def process(self, file_path: str, user_id: str) -> List[Dict]:
        """
        Process Liberty Excel file and return list of records for sales_unified table

        Args:
            file_path: Path to Liberty Excel file
            user_id: User ID for RLS filtering (not used in sales_unified, tenant-based instead)

        Returns:
            List of dictionaries ready for sales_unified insertion
        """
        print(f"[LibertyProcessor] Processing Liberty file: {file_path}")

        # Extract date from filename
        filename = os.path.basename(file_path)
        year, month, day = self._extract_date_from_filename(filename)
        sale_date = f"{year}-{month:02d}-{day:02d}"

        print(f"[LibertyProcessor] Extracted date: {sale_date} (from filename: {filename})")

        # Load Excel workbook
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active

        # Get all rows as list
        rows = list(sheet.iter_rows(values_only=True))

        print(f"[LibertyProcessor] Total rows in file: {len(rows)}")
        print(f"[LibertyProcessor] Skipping first 3 header rows, processing from row 4")

        records = []
        processed_rows = []  # Track for duplicate detection

        # Start from row 4 (index 3) to skip 3-row header structure
        # Liberty structure: product header row → data row → total row (repeating)
        idx = 3
        while idx < len(rows) - 1:  # -1 because we read pairs
            # Get current row and next row
            header_row = rows[idx]
            data_row = rows[idx + 1] if idx + 1 < len(rows) else None

            # Skip if not enough columns
            if not header_row or not data_row or len(header_row) <= max(self.COLUMN_MAPPING.values()) or len(data_row) <= max(self.COLUMN_MAPPING.values()):
                idx += 1
                continue

            # Extract product name from header row (Column F)
            liberty_name = header_row[self.COLUMN_MAPPING["product_name"]]

            # Skip if no product name or is a total row
            if not liberty_name or str(liberty_name).strip() == "" or self._is_total_row(header_row):
                idx += 1
                continue

            # Check if data row has any numeric values (not empty header row)
            flagship_qty_raw = data_row[self.COLUMN_MAPPING["flagship_qty"]]
            flagship_sales_raw = data_row[self.COLUMN_MAPPING["flagship_sales_gbp"]]

            # If data row is also empty (no quantities), skip this pair
            if (not flagship_qty_raw or flagship_qty_raw == '') and (not flagship_sales_raw or flagship_sales_raw == ''):
                idx += 1
                continue

            # Map to functional name
            functional_name = self._map_product_name(str(liberty_name))

            # Extract Flagship data from data row (columns O, P)
            flagship_qty = self._clean_numeric_value(flagship_qty_raw)
            flagship_sales_gbp = self._clean_numeric_value(flagship_sales_raw)

            # Create Flagship record if has data
            if flagship_qty is not None and flagship_sales_gbp is not None:
                flagship_record = {
                    "functional_name": functional_name,
                    "product_id": functional_name,  # Use functional_name as product_id
                    "quantity": int(flagship_qty) if flagship_qty else 0,
                    "sales_gbp": flagship_sales_gbp,
                    "sales_eur": round(flagship_sales_gbp * self.GBP_TO_EUR, 2) if flagship_sales_gbp else 0,
                    "store_identifier": "London",
                    "sale_date": sale_date,
                    "year": year,
                    "month": month,
                }

                # Check for duplicates
                if not self._is_duplicate_row(flagship_record, processed_rows):
                    # Include if quantity > 0 OR (quantity <= 0 AND has sales value)
                    if flagship_record["quantity"] > 0 or (flagship_record["quantity"] <= 0 and flagship_record["sales_gbp"] != 0):
                        records.append(flagship_record)
                        processed_rows.append(flagship_record)

            # Extract Internet data from data row (columns S, T)
            internet_qty_raw = data_row[self.COLUMN_MAPPING["internet_qty"]]
            internet_sales_raw = data_row[self.COLUMN_MAPPING["internet_sales_gbp"]]

            internet_qty = self._clean_numeric_value(internet_qty_raw)
            internet_sales_gbp = self._clean_numeric_value(internet_sales_raw)

            # Create Internet record if has data
            if internet_qty is not None and internet_sales_gbp is not None:
                internet_record = {
                    "functional_name": functional_name,
                    "product_id": functional_name,  # Use functional_name as product_id
                    "quantity": int(internet_qty) if internet_qty else 0,
                    "sales_gbp": internet_sales_gbp,
                    "sales_eur": round(internet_sales_gbp * self.GBP_TO_EUR, 2) if internet_sales_gbp else 0,
                    "store_identifier": "Online",
                    "sale_date": sale_date,
                    "year": year,
                    "month": month,
                }

                # Check for duplicates
                if not self._is_duplicate_row(internet_record, processed_rows):
                    # Include if quantity > 0 OR (quantity <= 0 AND has sales value)
                    if internet_record["quantity"] > 0 or (internet_record["quantity"] <= 0 and internet_record["sales_gbp"] != 0):
                        records.append(internet_record)
                        processed_rows.append(internet_record)

            # Move to next product (skip data row and total row)
            idx += 3

        workbook.close()

        print(f"[LibertyProcessor] Extracted {len(records)} records (after deduplication)")
        print(f"[LibertyProcessor] Sample record: {records[0] if records else 'No records'}")

        return records
