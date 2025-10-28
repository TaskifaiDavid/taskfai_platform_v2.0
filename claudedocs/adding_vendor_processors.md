# Adding New Vendor Processors - Developer Guide

**Target Audience**: Developers adding support for new reseller data formats
**Last Updated**: 2025-10-25

---

## Quick Start

### For BIBBI Vendors (Most Common)

```bash
# 1. Create new processor file
cp backend/app/services/bibbi/processors/liberty_processor.py \
   backend/app/services/bibbi/processors/new_vendor_processor.py

# 2. Implement vendor-specific logic (see template below)

# 3. Register in vendor router
# Edit: backend/app/services/bibbi/vendor_router.py

# 4. Test with sample file
pytest tests/bibbi/test_new_vendor_processor.py
```

---

## Processor Template

### BIBBI Vendor Processor Template

```python
"""
[VendorName] vendor data processor for BIBBI tenant

Handles data files from [VendorName] reseller.
Expected format: [describe Excel structure]
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from app.services.bibbi.processors.base import BibbiBseProcessor


class [VendorName]Processor(BibbiBseProcessor):
    """
    Process [VendorName] Excel files

    File Structure:
    - Sheet: "[SheetName]"
    - Headers: Row 1
    - Data: Row 2 onwards
    - Columns: [list key columns]

    Business Rules:
    - [Any vendor-specific rules]
    """

    TARGET_SHEET = "[SheetName]"

    COLUMN_MAPPING = {
        # Vendor Column → Standard Field
        "Product Code": "product_ean",
        "Product Name": "functional_name",
        "Quantity Sold": "quantity",
        "Sales Value": "sales_amount",
        # ... add all mappings
    }

    def get_vendor_name(self) -> str:
        """Return vendor identifier"""
        return "[vendor_name_lowercase]"

    def get_currency(self) -> str:
        """Return vendor's reporting currency"""
        return "EUR"  # or GBP, PLN, ZAR, USD

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract raw rows from Excel file

        Returns:
            List of row dictionaries with vendor-specific column names
        """
        workbook = self._load_workbook(file_path, read_only=True)
        sheet = workbook[self.TARGET_SHEET]

        # Use shared utility
        rows = self._extract_rows(sheet, min_row=2)

        workbook.close()
        return rows

    def transform_row(
        self,
        raw_row: Dict[str, Any],
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Transform vendor row to sales_unified schema

        Returns:
            Transformed row or None if row should be skipped

        Raises:
            ValueError: If required field is missing or invalid
        """
        # Start with base row (includes tenant_id, reseller_id, etc.)
        transformed = self._create_base_row(batch_id)

        # Map vendor columns to standard fields
        for source_col, target_col in self.COLUMN_MAPPING.items():
            value = raw_row.get(source_col)

            # Handle each field type appropriately
            if target_col == "product_ean":
                # Use shared validation utility
                transformed[target_col] = self._validate_ean(value, required=True)

            elif target_col == "quantity":
                if not value:
                    raise ValueError(f"Missing required field: {source_col}")
                transformed[target_col] = self._to_int(value, source_col)

            elif target_col == "sales_amount":
                transformed[target_col] = self._to_float(value, source_col)

                # Convert currency if needed
                if self.get_currency() != "EUR":
                    transformed["sales_eur"] = self._convert_currency(
                        transformed[target_col],
                        from_currency=self.get_currency()
                    )
                else:
                    transformed["sales_eur"] = transformed[target_col]

            elif target_col == "functional_name":
                transformed[target_col] = str(value) if value else None

            # ... handle other fields

        # Add derived fields if needed
        if "month" in transformed and "year" in transformed:
            transformed["quarter"] = self._calculate_quarter(transformed["month"])

        return transformed

    def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract store information from file

        Returns:
            List of store dictionaries (empty if no store data)
        """
        # If vendor provides store data, extract it here
        # Otherwise, return empty list
        return []


# Factory function for router
def get_[vendor_name]_processor(reseller_id: str) -> [VendorName]Processor:
    """Create [VendorName] processor instance"""
    return [VendorName]Processor(reseller_id)
```

---

## Step-by-Step Implementation Guide

### Step 1: Understand Vendor Data Format

**Before writing code**, analyze sample file:

1. Open Excel file, identify:
   - Sheet name(s)
   - Header row location (usually row 1)
   - Data start row (usually row 2)
   - Key columns: EAN, product name, quantity, sales amount, date

2. Document business rules:
   - Are EANs always present? (some vendors don't provide EANs for all products)
   - What currency? (EUR, GBP, PLN, ZAR, USD)
   - Date format? (separate month/year columns, or single date column)
   - Any store/location data?
   - Any special calculations needed?

3. Check for edge cases:
   - Empty rows
   - Missing data
   - Negative quantities (returns)
   - Multiple sheets
   - Summary rows at bottom

### Step 2: Create Processor File

```bash
# BIBBI vendor
touch backend/app/services/bibbi/processors/vendorname_processor.py

# Demo/general vendor (rare)
touch backend/app/services/vendors/vendorname_processor.py
```

**Naming Convention**:
- File: `vendorname_processor.py` (lowercase, underscores)
- Class: `VendorNameProcessor` (PascalCase)
- Function: `get_vendorname_processor` (lowercase, underscores)

### Step 3: Implement Core Methods

#### 3.1 Define Constants

```python
class VendorNameProcessor(BibbiBseProcessor):
    # Sheet to read from
    TARGET_SHEET = "Sales Data"  # or use first sheet

    # Column mapping
    COLUMN_MAPPING = {
        "EAN": "product_ean",
        "Product": "functional_name",
        "Qty": "quantity",
        "Value": "sales_amount",
        "Month": "month",
        "Year": "year"
    }
```

#### 3.2 Implement `get_vendor_name()` and `get_currency()`

```python
def get_vendor_name(self) -> str:
    return "vendorname"  # lowercase, used in database

def get_currency(self) -> str:
    return "EUR"  # or GBP, PLN, ZAR, USD
```

#### 3.3 Implement `extract_rows()`

**Simple case** (standard Excel structure):

```python
def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
    workbook = self._load_workbook(file_path, read_only=True)
    sheet = workbook[self.TARGET_SHEET]
    rows = self._extract_rows(sheet, min_row=2)  # Skip header row
    workbook.close()
    return rows
```

**Complex case** (multiple sheets, custom parsing):

```python
def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
    workbook = self._load_workbook(file_path, read_only=True)

    # Find correct sheet
    if "Sales" in workbook.sheetnames:
        sheet = workbook["Sales"]
    else:
        sheet = workbook[workbook.sheetnames[0]]

    # Get headers manually if needed
    headers = self._get_sheet_headers(sheet)

    # Custom row extraction if standard method doesn't work
    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not any(row):  # Skip empty rows
            continue
        if row[0] == "TOTAL":  # Skip summary rows
            continue

        row_dict = {}
        for idx, header in enumerate(headers):
            if idx < len(row):
                row_dict[header] = row[idx]
        rows.append(row_dict)

    workbook.close()
    return rows
```

#### 3.4 Implement `transform_row()`

**Key Principles**:
- Start with `self._create_base_row(batch_id)` for BIBBI processors
- Use shared utilities: `_validate_ean()`, `_to_int()`, `_to_float()`
- Raise `ValueError` for invalid required fields
- Return `None` to skip row (or raise ValueError)
- Handle currency conversion if needed

```python
def transform_row(
    self,
    raw_row: Dict[str, Any],
    batch_id: str
) -> Optional[Dict[str, Any]]:
    # Start with base fields (tenant_id, reseller_id, batch_id, etc.)
    transformed = self._create_base_row(batch_id)

    # Required fields - raise ValueError if missing
    ean = raw_row.get("EAN")
    if not ean:
        raise ValueError("Missing required field: EAN")
    transformed["product_ean"] = self._validate_ean(ean)

    quantity = raw_row.get("Qty")
    if not quantity:
        raise ValueError("Missing required field: Qty")
    transformed["quantity"] = self._to_int(quantity, "Qty")

    # Optional fields - use defaults
    sales = raw_row.get("Value")
    transformed["sales_amount"] = self._to_float(sales, "Value") if sales else 0.0

    # Currency conversion
    if self.get_currency() != "EUR":
        transformed["sales_eur"] = self._convert_currency(
            transformed["sales_amount"],
            from_currency=self.get_currency()
        )
    else:
        transformed["sales_eur"] = transformed["sales_amount"]

    # Product name
    transformed["functional_name"] = str(raw_row.get("Product", "Unknown"))

    # Date handling - separate month/year
    if "Month" in raw_row and "Year" in raw_row:
        transformed["month"] = self._validate_month(raw_row["Month"])
        transformed["year"] = self._validate_year(raw_row["Year"])
        transformed["quarter"] = self._calculate_quarter(transformed["month"])

    return transformed
```

#### 3.5 Implement `extract_stores()`

**If vendor provides NO store data**:

```python
def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
    return []
```

**If vendor provides store data**:

```python
def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
    workbook = self._load_workbook(file_path, read_only=True)
    sheet = workbook["Stores"]  # or wherever store data is

    stores = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if not any(row):
            continue

        stores.append({
            "store_identifier": str(row[0]),  # Vendor's store code
            "store_name": str(row[1]),        # Display name
            "store_type": "physical",         # or "online"
            "reseller_id": self.reseller_id
        })

    workbook.close()
    return stores
```

### Step 4: Register in Router

**For BIBBI processors**, edit `backend/app/services/bibbi/vendor_router.py`:

```python
# Add to PROCESSOR_MAP
PROCESSOR_MAP = {
    "aromateque": "get_aromateque_processor",
    "boxnox": "get_boxnox_processor",
    # ... existing processors
    "vendorname": "get_vendorname_processor",  # ← ADD THIS
}

# Add import at top
from app.services.bibbi.processors.vendorname_processor import (
    get_vendorname_processor
)
```

### Step 5: Add Vendor Detection Pattern

Edit `backend/app/services/vendors/detector.py` or `backend/app/services/bibbi/vendor_detector.py`:

```python
VENDOR_PATTERNS = {
    "vendorname": [
        r"vendorname.*\.xlsx",           # Case-insensitive filename match
        r"vendor.*sales.*report",
        # Add patterns that uniquely identify this vendor's files
    ],
    # ... other vendors
}
```

### Step 6: Create Sample Data & Test

```python
# tests/bibbi/test_vendorname_processor.py

import pytest
from app.services.bibbi.processors.vendorname_processor import VendorNameProcessor

def test_vendorname_processor():
    """Test VendorName processor with sample data"""
    processor = VendorNameProcessor(reseller_id="test-reseller-id")

    # Test with sample file
    result = processor.process(
        file_path="tests/fixtures/vendorname_sample.xlsx",
        batch_id="test-batch-id"
    )

    # Assertions
    assert result.successful_rows > 0
    assert result.failed_rows == 0
    assert len(result.transformed_data) > 0

    # Check first row structure
    first_row = result.transformed_data[0]
    assert "product_ean" in first_row
    assert "quantity" in first_row
    assert "sales_eur" in first_row
    assert first_row["vendor_name"] == "vendorname"

def test_vendorname_transform_row():
    """Test row transformation logic"""
    processor = VendorNameProcessor(reseller_id="test-reseller-id")

    raw_row = {
        "EAN": "1234567890123",
        "Product": "Test Product",
        "Qty": 10,
        "Value": 125.50,
        "Month": 6,
        "Year": 2025
    }

    transformed = processor.transform_row(raw_row, "batch-123")

    assert transformed["product_ean"] == "1234567890123"
    assert transformed["quantity"] == 10
    assert transformed["sales_eur"] == 125.50  # or converted value
    assert transformed["month"] == 6
    assert transformed["quarter"] == 2
```

---

## Common Patterns & Solutions

### Pattern: Optional EAN (like Galilu)

```python
# In transform_row()
ean = raw_row.get("EAN")
transformed["product_ean"] = self._validate_ean(ean, required=False)
# Returns None if EAN is missing or invalid
```

### Pattern: Currency Conversion (like Galilu - PLN to EUR)

```python
# In transform_row()
pln_amount = self._to_float(raw_row.get("Amount"), "Amount")
transformed["sales_eur"] = self._convert_currency(pln_amount, "PLN")
```

### Pattern: Negative Quantities (Returns)

```python
# Accounting notation: "(10)" = -10
# Base class _to_int() and _to_float() handle this automatically
quantity = self._to_int(raw_row.get("Qty"), "Qty")  # Handles "(10)" → -10
```

### Pattern: Multiple Sheets

```python
def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
    workbook = self._load_workbook(file_path)

    all_rows = []
    for sheet_name in ["Jan", "Feb", "Mar"]:  # Multiple monthly sheets
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            rows = self._extract_rows(sheet)
            all_rows.extend(rows)

    workbook.close()
    return all_rows
```

### Pattern: Date Column (Single Date vs Month/Year)

```python
# Single date column
date_value = self._validate_date(raw_row.get("Date"))
transformed["month"] = date_value.month
transformed["year"] = date_value.year
transformed["quarter"] = self._calculate_quarter(date_value.month)

# Separate month/year columns
transformed["month"] = self._validate_month(raw_row.get("Month"))
transformed["year"] = self._validate_year(raw_row.get("Year"))
transformed["quarter"] = self._calculate_quarter(transformed["month"])
```

---

## Checklist Before Submitting

### Code Quality

- [ ] Processor inherits from correct base class (BibbiBseProcessor for BIBBI)
- [ ] All methods implemented (get_vendor_name, get_currency, extract_rows, transform_row, extract_stores)
- [ ] Uses shared utilities from `app.utils.validation` and `app.utils.excel`
- [ ] No duplicate code (check against other processors)
- [ ] Proper error handling (raise ValueError with clear messages)
- [ ] Type hints on all method signatures
- [ ] Docstrings on class and key methods

### Testing

- [ ] Sample file tested manually
- [ ] Unit tests written for transform_row()
- [ ] Integration test with full file processing
- [ ] Edge cases tested (empty EAN, missing fields, negative values)
- [ ] Currency conversion tested (if applicable)

### Registration

- [ ] Added to PROCESSOR_MAP in vendor_router.py
- [ ] Import added at top of router file
- [ ] Vendor detection pattern added to detector.py
- [ ] Factory function created (get_vendorname_processor)

### Documentation

- [ ] File docstring explains vendor and format
- [ ] Business rules documented in class docstring
- [ ] Comments on any non-obvious logic
- [ ] This guide updated if new patterns discovered

---

## Troubleshooting

### Error: "Sheet 'X' not found in workbook"

**Solution**: Use fallback or check sheet names

```python
from app.utils.excel import find_sheet_by_name

sheet = find_sheet_by_name(workbook, "Sales Data", fallback_to_first=True)
```

### Error: "Invalid EAN format"

**Solution**: Check for Excel number formatting

```python
# EAN might be formatted as float: 1234567890123.0
# _validate_ean() handles this automatically by stripping decimals
```

### Error: "Missing required field: X"

**Solution**: Check exact column name in Excel (case-sensitive, whitespace)

```python
# Debug: Print available columns
print(f"Available columns: {list(raw_row.keys())}")

# Use .strip() to handle whitespace
value = raw_row.get("Product Name ".strip())
```

### Error: "Invalid integer/float"

**Solution**: Handle empty strings and None

```python
# Use allow_none parameter
quantity = self._to_float(value, "Qty", allow_none=True, default=0.0)
```

---

## Performance Tips

1. **Use read_only=True** when loading workbooks (faster, less memory)
2. **Close workbooks** after processing
3. **Batch inserts** instead of row-by-row (handled by framework)
4. **Cache reseller data** (handled by BibbiBseProcessor automatically)

---

## Next Steps After Implementation

1. **Manual Testing**: Upload sample file through UI
2. **Monitor Logs**: Check for errors during processing
3. **Validate Data**: Query database to verify inserted records
4. **Update Documentation**: Add vendor to supported list
5. **Create PR**: Follow git workflow for code review

---

## Questions?

- **Architecture**: See `/claudedocs/architecture_clarity.md`
- **System Overview**: See `/docs/architecture/SYSTEM_OVERVIEW.md`
- **BIBBI Specifics**: See `/docs/deployment/02_Customer_Onboarding_BIBBI_Example.md`
- **Refactoring History**: See `/docs/architecture/REFACTORING_IMPROVEMENTS.md`

**Last Updated**: 2025-10-25 (Post DRY refactoring)
