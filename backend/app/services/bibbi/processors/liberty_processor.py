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

    def _parse_store_columns(self, sheet) -> Dict[str, Dict[str, int]]:
        """
        Parse Liberty's multi-store column structure from rows 1-2

        Returns:
            Dict mapping store identifier to column ranges
            Example: {
                "flagship": {"qty_col": 12, "sales_col": 13},
                "online": {"qty_col": 14, "sales_col": 15}
            }
        """
        store_columns = {}

        # Row 1 has store names like "Flagship", "Internet"
        # Row 3 has column headers like "Sales Qty Un", "Sales Inc VAT £ "
        row1 = list(sheet[1])
        row3 = list(sheet[3])

        current_store = None
        for idx, cell in enumerate(row1):
            if cell.value and str(cell.value).strip():
                store_name = str(cell.value).strip()

                # Skip non-store headers
                if store_name in ['Retail Group', 'Brand', 'Colour Phase', 'Product Group', 'Item ID | Colour', 'Item', 'All Warehouse', '']:
                    continue

                # Skip "All Sales Channels" - we want individual stores only
                if store_name.lower() in ['all sales channels', 'total']:
                    continue

                # Normalize store name to identifier
                store_id = store_name.lower().replace(' ', '_')
                if store_id not in store_columns:
                    store_columns[store_id] = {}
                    current_store = store_id

            # Find quantity and sales columns under this store
            if current_store and idx < len(row3) and row3[idx].value:
                header = str(row3[idx].value).strip()

                if 'qty' in header.lower() or 'quantity' in header.lower():
                    store_columns[current_store]['qty_col'] = idx
                elif 'sales' in header.lower() and '£' in header:
                    store_columns[current_store]['sales_col'] = idx

        print(f"[Liberty] Parsed store columns: {store_columns}")
        return store_columns

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract rows from Liberty Excel file

        Liberty has complex structure:
        - Rows 1-2: Multi-level store headers (Flagship, Internet, etc.)
        - Row 3: Column headers (Item ID | Colour, Item, Sales Qty Un, etc.)
        - Row 4+: Data rows where each product uses TWO rows:
          - Row 1: Product info (brand, EAN, name) - columns A-L
          - Row 2: Sales data (quantities/amounts by store) - columns M onwards

        NEW: Creates MULTIPLE records per product - one for each store with data
        """
        workbook = self._load_workbook(file_path, read_only=False)
        sheet = workbook[workbook.sheetnames[0]]

        # Parse store column structure
        store_columns = self._parse_store_columns(sheet)

        # Read row 3 as headers
        headers = []
        for cell in sheet[3]:  # Row 3 (1-indexed)
            if cell.value:
                headers.append(str(cell.value).strip())
            else:
                headers.append("")

        print(f"[Liberty] Found {len(headers)} columns in row 3")
        print(f"[Liberty] Detected {len(store_columns)} stores with data")

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

                    # Create MULTIPLE records - one per store with data
                    for store_id, col_info in store_columns.items():
                        qty_col = col_info.get('qty_col')
                        sales_col = col_info.get('sales_col')

                        if qty_col is None or sales_col is None:
                            print(f"[Liberty] WARNING: Store '{store_id}' missing columns (qty_col: {qty_col}, sales_col: {sales_col}) - skipping")
                            continue

                        # Check if this store has data (non-zero quantity or sales)
                        qty_value = data_row[qty_col] if qty_col < len(data_row) else None
                        sales_value = data_row[sales_col] if sales_col < len(data_row) else None

                        # Skip if no data for this store
                        if not qty_value and not sales_value:
                            continue

                        # Create a record for this store
                        store_row = {
                            'Item ID | Colour': ean_value,
                            'Item': product_name,
                            'Sales Qty Un': qty_value,
                            'Sales Inc VAT £ ': sales_value,
                            'store_identifier': store_id  # Add store identifier
                        }

                        rows.append(store_row)

                    # Skip both rows (info + data)
                    i += 2
                else:
                    # No data row following, skip this info row
                    i += 1
            else:
                # Not a product info row, skip
                i += 1

        workbook.close()
        print(f"[Liberty] Extracted {len(rows)} sales records across {len(store_columns)} stores")
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

        # Extract Liberty product code from "Item ID | Colour" format
        # NOTE: These are Liberty's internal codes, NOT real EAN barcodes
        ean_with_color = raw_row.get("Item ID | Colour")
        if not ean_with_color:
            raise ValueError("Missing 'Item ID | Colour'")

        # Parse Liberty code: extract everything before " | "
        if isinstance(ean_with_color, str) and '|' in ean_with_color:
            liberty_code = ean_with_color.split('|')[0].strip()
        else:
            liberty_code = str(ean_with_color).strip()

        # Clean Liberty code (remove leading zeros for matching)
        if liberty_code.isdigit():
            liberty_code = liberty_code.lstrip('0') or '0'

        # Extract product name for matching
        product_name = raw_row.get("Item")
        product_name_str = str(product_name).strip() if product_name else None

        # Use product matcher to get BIBBI EAN
        # This will match existing products or auto-create with temporary EAN
        try:
            from app.services.bibbi.product_service import get_product_service
            from app.core.bibbi import get_bibbi_db

            bibbi_db = get_bibbi_db()
            product_service = get_product_service(bibbi_db)

            # Match or create product
            matched_ean = product_service.match_or_create_product(
                vendor_code=liberty_code,
                product_name=product_name_str,
                vendor_name="liberty"
            )

            transformed["product_id"] = matched_ean

        except Exception as e:
            raise ValueError(f"Failed to match product '{liberty_code}' ('{product_name_str}'): {e}")

        # Store product name for reference
        if product_name_str:
            transformed["product_name_raw"] = product_name_str

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

        # Store identification: Use the store_identifier from raw_row
        # This was set during extract_rows based on which store column had the data
        store_identifier = raw_row.get("store_identifier", "flagship")
        transformed["store_identifier"] = store_identifier

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
