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
    # NOTE: Liberty has 3-row headers (rows 1-3), actual data starts at row 4
    COLUMN_MAPPING = {
        "Item ID | Colour": "product_ean",  # Contains EAN like "000834429 | 98-NO COLOUR"
        "Item": "functional_name",  # Product name
        "Sales Qty Un": "quantity",  # Quantity sold (may be in store-specific columns)
        "Sales Inc VAT £ ": "sales_gbp",  # Sales amount in GBP
        "Sales Inc VAT £": "sales_gbp",  # Alternative without trailing space
    }

    # Store-specific column pattern
    # Format: "Flagship" -> "Sales Qty Un", "Internet" -> "Sales Qty Un"
    # We need to detect which columns belong to which store dynamically

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

        Liberty has complex structure:
        - Rows 1-2: Multi-level store headers (Flagship, Internet, etc.)
        - Row 3: Column headers (Item ID | Colour, Item, Sales Qty Un, etc.)
        - Row 4+: Data rows where each product uses TWO rows:
          - Row 1: Product info (brand, EAN, name) - columns A-L
          - Row 2: Sales data (quantities/amounts by store) - columns M onwards

        We need to:
        1. Read row 3 as headers
        2. Process rows 4+ in pairs
        3. Combine product info (row 1) with sales data (row 2)
        4. Create separate records for each store (YTD columns)
        """
        workbook = self._load_workbook(file_path, read_only=False)
        sheet = workbook[workbook.sheetnames[0]]

        # Read row 3 as headers
        headers = []
        for cell in sheet[3]:  # Row 3 (1-indexed)
            if cell.value:
                headers.append(str(cell.value).strip())
            else:
                headers.append("")

        print(f"[Liberty] Found {len(headers)} columns in row 3")

        # Find store columns by looking at rows 1-2
        # Row 1 has store names like "Flagship", "Internet", "All Sales Channels"
        store_headers = []
        for cell in sheet[1]:
            if cell.value and str(cell.value).strip() and cell.value not in ['', 'All Warehouse']:
                store_name = str(cell.value).strip()
                if store_name not in ['Retail Group', 'Brand', 'Colour Phase', 'Product Group', 'Item ID | Colour', 'Item']:
                    store_headers.append(store_name)

        print(f"[Liberty] Found stores in row 1: {store_headers}")

        # Process data rows starting from row 4
        # Liberty uses 2-row pattern: info row + data row
        rows = []
        all_rows = list(sheet.iter_rows(min_row=4, values_only=True))

        i = 0
        while i < len(all_rows):
            info_row = all_rows[i]

            # Skip empty rows
            if not any(info_row):
                i += 1
                continue

            # Check if this is a product info row (has EAN in column E)
            ean_value = info_row[4] if len(info_row) > 4 else None  # Column E (0-indexed: 4)

            if ean_value and isinstance(ean_value, str) and '|' in ean_value and not ean_value.endswith('Total'):
                # This is a product info row, next row should have sales data
                product_name = info_row[5] if len(info_row) > 5 else None  # Column F

                # Get the data row (next row)
                if i + 1 < len(all_rows):
                    data_row = all_rows[i + 1]

                    # Start with sales data from data_row
                    combined_row = {}
                    for idx, header in enumerate(headers):
                        if idx < len(data_row):
                            combined_row[header] = data_row[idx]

                    # Override with product info from info_row (AFTER mapping data_row)
                    # This ensures EAN and product name don't get overwritten
                    combined_row['Item ID | Colour'] = ean_value
                    combined_row['Item'] = product_name

                    rows.append(combined_row)

                    # Skip both rows (info + data)
                    i += 2
                else:
                    # No data row following, skip this info row
                    i += 1
            else:
                # Not a product info row, skip
                i += 1

        workbook.close()
        print(f"[Liberty] Extracted {len(rows)} product rows")
        return rows

    def transform_row(
        self,
        raw_row: Dict[str, Any],
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Transform Liberty row to sales_unified schema

        Handles:
        1. EAN parsing from "Item ID | Colour" format (e.g., "000834429 | 98-NO COLOUR")
        2. Returns in parentheses: (123) → -123
        3. GBP → EUR conversion
        4. Store identification from column position
        5. YTD (year-to-date) sales data extraction

        Liberty data structure:
        - "Item ID | Colour" contains EAN
        - "Item" contains product name
        - YTD columns have sales data (we use YTD, not "Actual")
        - Multiple store columns (Flagship YTD, Internet YTD, etc.)
        """
        # Start with base row
        transformed = self._create_base_row(batch_id)

        # Extract and parse EAN from "Item ID | Colour" format
        ean_with_color = raw_row.get("Item ID | Colour")
        if not ean_with_color:
            raise ValueError("Missing 'Item ID | Colour'")

        # Parse EAN: extract everything before " | "
        if isinstance(ean_with_color, str) and '|' in ean_with_color:
            ean_value = ean_with_color.split('|')[0].strip()
        else:
            ean_value = str(ean_with_color).strip()

        # Liberty uses 9-digit internal codes, pad to 13 digits for EAN-13 format
        if ean_value.isdigit() and len(ean_value) < 13:
            ean_value = ean_value.zfill(13)  # Pad with leading zeros

        try:
            transformed["product_id"] = self._validate_ean(ean_value)
        except ValueError as e:
            raise ValueError(f"Invalid EAN from '{ean_with_color}': {e}")

        # Extract product name
        product_name = raw_row.get("Item")
        if product_name:
            transformed["product_name_raw"] = str(product_name).strip()

        # Extract quantity - Liberty has no single "quantity" column
        # Instead, quantity is in store-specific columns like "Sales Qty Un"
        # For now, we'll look for YTD quantity (columns after "Actual")

        # Try to find YTD Sales Qty Un column
        qty_value = None
        sales_value = None

        # Liberty file structure from row 3:
        # ...YTD columns are: "Sales Qty Un", "Sales Inc VAT £ " (with trailing space)

        # Check for various quantity column names
        for col_name in ["Sales Qty Un", "Sold", "Quantity"]:
            if col_name in raw_row and raw_row[col_name] is not None:
                qty_value = raw_row[col_name]
                break

        if qty_value is None or qty_value == '':
            # No quantity data - skip this row (might be a header or summary row)
            return None

        try:
            quantity = self._to_int(qty_value, "Sales Qty Un")
            if quantity == 0:
                # Zero quantity - skip
                return None

            transformed["quantity"] = quantity

            # If quantity is negative (returns), mark as return
            if quantity < 0:
                transformed["is_return"] = True
                transformed["return_quantity"] = abs(quantity)
            else:
                transformed["is_return"] = False

        except ValueError as e:
            raise ValueError(f"Invalid quantity: {e}")

        # Extract sales amount in GBP
        # Try different column name variations
        for col_name in ["Sales Inc VAT £ ", "Sales Inc VAT £", "Value", "Sales"]:
            if col_name in raw_row and raw_row[col_name] is not None and raw_row[col_name] != '':
                sales_value = raw_row[col_name]
                break

        if sales_value is None:
            raise ValueError("Missing sales amount")

        try:
            sales_gbp = self._to_float(sales_value, "Sales Inc VAT")

            # Store local currency amount
            transformed["sales_local_currency"] = sales_gbp

            # Convert to EUR
            transformed["sales_eur"] = self._convert_currency(sales_gbp, "GBP")

        except ValueError as e:
            raise ValueError(f"Invalid sales amount: {e}")

        # Extract date - Liberty files are named with dates
        # For now, extract from filename or use current month
        # TODO: Parse date from filename pattern "Continuity Supplier Size Report DD-MM-YYYY.xlsx"

        now = datetime.utcnow()
        transformed["sale_date"] = now.date().isoformat()
        transformed["year"] = now.year
        transformed["month"] = now.month
        transformed["quarter"] = self._calculate_quarter(now.month)

        # Store identification: For now, default to "flagship" for YTD columns
        # TODO: Detect which store column this data came from
        transformed["store_identifier"] = "flagship"

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
