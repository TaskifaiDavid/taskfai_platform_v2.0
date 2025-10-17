"""
Liberty Processor (BIBBI Version)

Handles Liberty UK reseller data with special cases:
1. Duplicate rows: Liberty uses 2 rows per product with same amount
2. Returns: Parentheses indicate returns (123) = -123
3. Store identification: "Flagship" = physical, "online" = online
4. Currency: GBP → EUR conversion

Based on: backend/BIBBI/Resellers/resellers_info.md
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import openpyxl

from .base import BibbiBseProcessor


class LibertyProcessor(BibbiBseProcessor):
    """Process Liberty Excel files with GBP to EUR conversion"""

    VENDOR_NAME = "liberty"
    CURRENCY = "GBP"
    GBP_TO_EUR_RATE = 1.17

    # Column mapping from Liberty format to internal names
    COLUMN_MAPPING = {
        "EAN": "product_ean",
        "Product": "functional_name",
        "Sold": "quantity",
        "Value": "sales_gbp",
        "Sales": "sales_gbp",  # Alternative column name
        "Month": "month",
        "Year": "year",
        "Store": "store_identifier",
        "Location": "store_identifier",  # Alternative column name
    }

    def get_vendor_name(self) -> str:
        return self.VENDOR_NAME

    def get_currency(self) -> str:
        return self.CURRENCY

    def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract Liberty store information

        Liberty typically has:
        - "Flagship" = physical store (London flagship location)
        - "online" / "Online" = e-commerce
        - Sometimes "Store 1", "Store 2", etc.

        Returns:
            List of store dictionaries
        """
        stores = []

        try:
            workbook = self._load_workbook(file_path)
            sheet = workbook[workbook.sheetnames[0]]
            headers = self._get_sheet_headers(sheet)

            # Find store column
            store_col_idx = None
            for idx, header in enumerate(headers):
                if header in ["Store", "Location", "Shop"]:
                    store_col_idx = idx
                    break

            if store_col_idx is None:
                # No store column - assume single store
                # Liberty minimum: Flagship + online
                stores = [
                    {
                        "store_identifier": "flagship",
                        "store_name": "Liberty Flagship",
                        "store_type": "physical",
                        "reseller_id": self.reseller_id,
                        "city": "London",
                        "country": "UK"
                    },
                    {
                        "store_identifier": "online",
                        "store_name": "Liberty Online",
                        "store_type": "online",
                        "reseller_id": self.reseller_id,
                        "country": "UK"
                    }
                ]
            else:
                # Extract unique store identifiers
                seen_stores = set()
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    if not any(row):
                        continue

                    store_value = row[store_col_idx] if store_col_idx < len(row) else None
                    if store_value:
                        store_str = str(store_value).strip().lower()
                        if store_str and store_str not in seen_stores:
                            seen_stores.add(store_str)

                            # Determine store type
                            is_online = any(keyword in store_str for keyword in ["online", "web", "e-commerce", "ecom"])
                            store_type = "online" if is_online else "physical"

                            stores.append({
                                "store_identifier": store_str,
                                "store_name": f"Liberty {store_value.strip()}",
                                "store_type": store_type,
                                "reseller_id": self.reseller_id,
                                "city": "London" if store_type == "physical" else None,
                                "country": "UK"
                            })

            workbook.close()

        except Exception as e:
            print(f"[Liberty] Error extracting stores: {e}")
            # Fallback to default stores
            stores = [
                {
                    "store_identifier": "flagship",
                    "store_name": "Liberty Flagship",
                    "store_type": "physical",
                    "reseller_id": self.reseller_id,
                    "city": "London",
                    "country": "UK"
                },
                {
                    "store_identifier": "online",
                    "store_name": "Liberty Online",
                    "store_type": "online",
                    "reseller_id": self.reseller_id,
                    "country": "UK"
                }
            ]

        return stores

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract rows from Liberty Excel file

        CRITICAL: Liberty uses 2 rows per product with same amount
        We need to deduplicate in transform_row(), not here
        """
        workbook = self._load_workbook(file_path)
        sheet = workbook[workbook.sheetnames[0]]
        headers = self._get_sheet_headers(sheet)

        rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue

            row_dict = {}
            for idx, header in enumerate(headers):
                if idx < len(row):
                    row_dict[header] = row[idx]

            rows.append(row_dict)

        workbook.close()
        return rows

    def transform_row(
        self,
        raw_row: Dict[str, Any],
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Transform Liberty row to sales_unified schema

        Handles:
        1. Returns in parentheses: (123) → -123
        2. GBP → EUR conversion
        3. Store mapping
        4. EAN validation

        Note: Duplicate row deduplication happens at insertion time
        using unique constraint on (tenant_id, reseller_id, product_id, sale_date, store_id, quantity)
        """
        # Start with base row
        transformed = self._create_base_row(batch_id)

        # Extract and validate EAN
        ean_value = raw_row.get("EAN")
        if not ean_value:
            raise ValueError("Missing EAN")

        try:
            transformed["product_id"] = self._validate_ean(ean_value)
        except ValueError as e:
            raise ValueError(f"Invalid EAN: {e}")

        # Extract quantity (handle returns in parentheses)
        qty_value = raw_row.get("Sold")
        if qty_value is None:
            raise ValueError("Missing Sold quantity")

        try:
            quantity = self._to_int(qty_value, "Sold")
            transformed["quantity"] = quantity

            # If quantity is negative, it's a return
            if quantity < 0:
                transformed["is_return"] = True
                transformed["return_quantity"] = abs(quantity)
            else:
                transformed["is_return"] = False

        except ValueError as e:
            raise ValueError(f"Invalid quantity: {e}")

        # Extract sales amount in GBP (handle returns)
        sales_value = raw_row.get("Value") or raw_row.get("Sales")
        if sales_value is None:
            raise ValueError("Missing Value/Sales")

        try:
            sales_gbp = self._to_float(sales_value, "Value")

            # Store local currency amount
            transformed["sales_local_currency"] = sales_gbp

            # Convert to EUR
            transformed["sales_eur"] = self._convert_currency(sales_gbp, "GBP")

        except ValueError as e:
            raise ValueError(f"Invalid sales amount: {e}")

        # Extract date information
        month_value = raw_row.get("Month")
        year_value = raw_row.get("Year")

        if month_value and year_value:
            try:
                month = self._to_int(month_value, "Month")
                year = self._to_int(year_value, "Year")

                if month < 1 or month > 12:
                    raise ValueError(f"Invalid month: {month}")

                if year < 2000 or year > 2100:
                    raise ValueError(f"Invalid year: {year}")

                # Create sale_date (use first day of month)
                transformed["sale_date"] = datetime(year, month, 1).date().isoformat()
                transformed["year"] = year
                transformed["month"] = month
                transformed["quarter"] = self._calculate_quarter(month)

            except ValueError as e:
                raise ValueError(f"Invalid date: {e}")
        else:
            # Use current date if not provided
            now = datetime.utcnow()
            transformed["sale_date"] = now.date().isoformat()
            transformed["year"] = now.year
            transformed["month"] = now.month
            transformed["quarter"] = self._calculate_quarter(now.month)

        # Extract store identifier
        store_value = raw_row.get("Store") or raw_row.get("Location")
        if store_value:
            store_str = str(store_value).strip().lower()
            transformed["store_identifier"] = store_str
        else:
            # Default to flagship if not specified
            transformed["store_identifier"] = "flagship"

        # Extract product name (informational only, not stored in sales_unified)
        product_name = raw_row.get("Product")
        if product_name:
            transformed["product_name_raw"] = str(product_name)

        return transformed


def get_liberty_processor(reseller_id: str) -> LibertyProcessor:
    """
    Factory function to create Liberty processor

    Args:
        reseller_id: UUID of Liberty reseller from resellers table

    Returns:
        LibertyProcessor instance
    """
    return LibertyProcessor(reseller_id)
