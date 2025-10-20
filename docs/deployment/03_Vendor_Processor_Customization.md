# Vendor Processor Customization Guide

## Table of Contents
1. [Processor Architecture](#processor-architecture)
2. [Creating a New Processor](#creating-a-new-processor)
3. [Common Patterns & Solutions](#common-patterns--solutions)
4. [Testing Processors](#testing-processors)
5. [Debugging & Troubleshooting](#debugging--troubleshooting)
6. [Best Practices](#best-practices)

---

## Processor Architecture

### How Vendor Processors Work

```
┌─────────────────────────────────────────────────────────────┐
│  1. File Upload (via API endpoint)                         │
│     POST /api/uploads                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Vendor Detection (VendorDetector)                       │
│     - Analyzes filename, sheet names, column headers        │
│     - Returns vendor name + confidence score                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Processor Factory (get_vendor_processor)                │
│     - Maps vendor name → processor instance                 │
│     - Returns None if vendor not found                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Processor Execution (processor.process)                 │
│     - Extracts data from file                               │
│     - Transforms to standardized schema                     │
│     - Validates and handles errors                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Database Insertion (Supabase)                           │
│     - Inserts into ecommerce_orders OR sellout_entries2    │
│     - Records errors in error_reports                       │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema Target

Processors must output data for ONE of these tables:

**Option A: ecommerce_orders (D2C/Online Sales)**
```sql
CREATE TABLE ecommerce_orders (
    order_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    upload_batch_id UUID,

    -- Product info
    product_ean VARCHAR(13),
    functional_name VARCHAR(255) NOT NULL,
    product_name VARCHAR(255),

    -- Financial data
    sales_eur DECIMAL(12, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    cost_of_goods DECIMAL(12, 2),
    stripe_fee DECIMAL(12, 2),

    -- Temporal data
    order_date DATE NOT NULL,

    -- Geographic data
    country VARCHAR(100),
    city VARCHAR(255),

    -- Marketing attribution
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    device_type VARCHAR(50),

    -- Metadata
    reseller VARCHAR(255) DEFAULT 'Online',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Option B: sellout_entries2 (B2B/Wholesale Sales)**
```sql
CREATE TABLE sellout_entries2 (
    sale_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    product_id UUID,
    reseller_id UUID,
    upload_batch_id UUID,

    -- Product info
    functional_name VARCHAR(255) NOT NULL,
    product_ean VARCHAR(13),

    -- Reseller info
    reseller VARCHAR(255) NOT NULL,

    -- Financial data
    sales_eur DECIMAL(12, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',

    -- Temporal data
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Creating a New Processor

### Step 1: Analyze the File Format

**Questions to Answer:**

1. **File Format**
   - Excel (.xlsx, .xls) or CSV?
   - Multiple sheets or single sheet?
   - Header row on line 1 or elsewhere?

2. **Column Mapping**
   - Which columns map to required fields?
   - Are column names consistent or variable?
   - Are there merged cells or multi-line headers?

3. **Data Types**
   - How are dates formatted? (DD/MM/YYYY, YYYY-MM-DD, etc.)
   - Are numbers with decimals or commas?
   - Are EAN codes 13 digits or custom format?

4. **Special Cases**
   - Empty rows or comment rows?
   - Subtotal/total rows to skip?
   - Multiple products per row?
   - Aggregation needed (daily → monthly)?

5. **Table Target**
   - D2C (ecommerce_orders) or B2B (sellout_entries2)?
   - Do we have order_date (D2C) or month/year (B2B)?

### Step 2: Create Processor File

```bash
cd backend/app/services/vendors

# Create new processor (use snake_case naming)
touch new_vendor_processor.py
```

### Step 3: Implement Processor Class

**Template Structure:**

```python
"""
[Vendor Name] vendor data processor
[Optional: Customer name, special notes]
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import openpyxl  # or: import csv, import pandas as pd
from openpyxl.worksheet.worksheet import Worksheet


class NewVendorProcessor:
    """Process [Vendor Name] files"""

    # Configuration
    TARGET_SHEET = "Sheet1"  # For Excel files
    SKIP_ROWS = 0  # Skip header rows if needed

    # Column mapping: Source Column → Target Field
    COLUMN_MAPPING = {
        "Source Column 1": "product_ean",
        "Source Column 2": "functional_name",
        "Source Column 3": "quantity",
        "Source Column 4": "sales_eur",
        # ... map all required columns
    }

    def process(
        self,
        file_path: str,
        user_id: str,
        batch_id: str
    ) -> Dict[str, Any]:
        """
        Process vendor file

        Args:
            file_path: Path to file
            user_id: User identifier
            batch_id: Upload batch identifier

        Returns:
            Processing result with statistics
        """
        try:
            # Step 1: Load file
            workbook = openpyxl.load_workbook(file_path, data_only=True)

            # Step 2: Get target sheet
            if self.TARGET_SHEET not in workbook.sheetnames:
                raise ValueError(f"Sheet '{self.TARGET_SHEET}' not found")

            sheet = workbook[self.TARGET_SHEET]

            # Step 3: Extract raw rows
            raw_rows = self._extract_rows(sheet)

            # Step 4: Transform rows
            transformed_rows = []
            errors = []

            for row_num, raw_row in enumerate(raw_rows, start=2):
                try:
                    transformed = self._transform_row(raw_row, user_id, batch_id)
                    if transformed:
                        transformed_rows.append(transformed)
                except Exception as e:
                    errors.append({
                        "row_number": row_num,
                        "error": str(e),
                        "raw_data": raw_row
                    })

            workbook.close()

            # Step 5: Return results
            return {
                "total_rows": len(raw_rows),
                "successful_rows": len(transformed_rows),
                "failed_rows": len(errors),
                "transformed_data": transformed_rows,
                "errors": errors
            }

        except Exception as e:
            raise Exception(f"Failed to process {self.__class__.__name__}: {str(e)}")

    def _extract_rows(self, sheet: Worksheet) -> List[Dict[str, Any]]:
        """
        Extract rows from worksheet

        Args:
            sheet: Excel worksheet

        Returns:
            List of row dictionaries
        """
        # Get headers from first row (or configured row)
        header_row = 1 + self.SKIP_ROWS
        headers = []

        for cell in sheet[header_row]:
            if cell.value:
                headers.append(str(cell.value).strip())

        # Extract data rows
        rows = []
        for row in sheet.iter_rows(min_row=header_row + 1, values_only=True):
            # Skip empty rows
            if not any(row):
                continue

            # Create dictionary
            row_dict = {}
            for idx, header in enumerate(headers):
                if idx < len(row):
                    row_dict[header] = row[idx]

            rows.append(row_dict)

        return rows

    def _transform_row(
        self,
        raw_row: Dict[str, Any],
        user_id: str,
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Transform raw row to standardized format

        Args:
            raw_row: Raw row data
            user_id: User identifier
            batch_id: Batch identifier

        Returns:
            Transformed row or None if invalid
        """
        transformed = {
            "user_id": user_id,
            "upload_batch_id": batch_id,
        }

        # Map columns using COLUMN_MAPPING
        for source_col, target_col in self.COLUMN_MAPPING.items():
            value = raw_row.get(source_col)

            # Apply transformations based on target column
            if target_col == "product_ean":
                transformed[target_col] = self._validate_ean(value)

            elif target_col == "quantity":
                transformed[target_col] = self._to_int(value, "Quantity")

            elif target_col == "sales_eur":
                transformed[target_col] = self._to_float(value, "Sales")

            elif target_col == "order_date":
                transformed[target_col] = self._parse_date(value)

            else:
                # Default: convert to string
                transformed[target_col] = str(value) if value else None

        # Add table-specific fields
        # For ecommerce_orders: order_date required
        # For sellout_entries2: year, month, reseller required

        # Example for B2B (sellout_entries2):
        if "order_date" in transformed:
            order_date = transformed["order_date"]
            transformed["year"] = order_date.year
            transformed["month"] = order_date.month

        if "reseller" not in transformed:
            transformed["reseller"] = "[Vendor Name]"

        # Add timestamp
        transformed["created_at"] = datetime.utcnow().isoformat()

        return transformed

    # =============================================
    # Validation & Transformation Helper Methods
    # =============================================

    def _validate_ean(self, value: Any) -> str:
        """Validate and normalize EAN code"""
        if not value:
            raise ValueError("EAN cannot be empty")

        ean_str = str(value).strip()

        # Remove decimal points (Excel sometimes formats as number)
        if '.' in ean_str:
            ean_str = ean_str.split('.')[0]

        # Validate length
        if len(ean_str) == 13 and ean_str.isdigit():
            return ean_str
        elif len(ean_str) == 8 and ean_str.isdigit():
            # Convert 8-digit to EAN-13 (pad with zeros)
            return "00000" + ean_str
        else:
            raise ValueError(f"Invalid EAN format: {ean_str}")

    def _parse_date(self, value: Any) -> datetime:
        """Parse date from various formats"""
        # Already a datetime?
        if isinstance(value, datetime):
            return value

        if not value:
            raise ValueError("Date cannot be empty")

        date_str = str(value).strip()

        # Try common date formats
        for fmt in [
            "%d/%m/%Y",     # 31/12/2024
            "%Y-%m-%d",     # 2024-12-31
            "%m/%d/%Y",     # 12/31/2024
            "%d-%m-%Y",     # 31-12-2024
            "%Y/%m/%d",     # 2024/12/31
        ]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def _to_int(self, value: Any, field_name: str) -> int:
        """Convert to integer"""
        if value is None:
            raise ValueError(f"{field_name} cannot be None")

        try:
            # Handle string with commas: "1,234" → 1234
            if isinstance(value, str):
                value = value.replace(',', '')

            return int(float(value))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid integer for {field_name}: {value}")

    def _to_float(self, value: Any, field_name: str) -> float:
        """Convert to float"""
        if value is None or value == "":
            return 0.0

        try:
            # Handle string with commas: "1,234.56" → 1234.56
            if isinstance(value, str):
                value = value.replace(',', '')

            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid float for {field_name}: {value}")

    def _to_currency(self, value: Any, field_name: str) -> float:
        """Convert currency to float (handles $ € symbols)"""
        if value is None or value == "":
            return 0.0

        try:
            # Remove currency symbols and commas
            if isinstance(value, str):
                value = value.replace('€', '').replace('$', '').replace(',', '').strip()

            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid currency for {field_name}: {value}")
```

### Step 4: Register in Detector

```python
# backend/app/services/vendors/detector.py

class VendorDetector:
    VENDOR_PATTERNS = {
        # ... existing patterns ...

        "new_vendor": {
            "filename_keywords": ["keyword1", "keyword2"],
            "sheet_names": ["Target Sheet Name"],
            "required_columns": ["Column1", "Column2", "Column3"]
        },
    }
```

### Step 5: Register in Factory

```python
# backend/app/services/vendors/__init__.py

from .new_vendor_processor import NewVendorProcessor

def get_vendor_processor(vendor_name: str):
    """Get processor instance for vendor"""
    processors = {
        # ... existing processors ...
        "new_vendor": NewVendorProcessor(),
    }

    processor = processors.get(vendor_name)
    if not processor:
        raise ValueError(f"Unknown vendor: {vendor_name}")

    return processor
```

---

## Common Patterns & Solutions

### Pattern 1: Multiple Sheets per File

**Problem:** File has multiple sheets with different data

**Solution:**

```python
def process(self, file_path: str, user_id: str, batch_id: str) -> Dict[str, Any]:
    workbook = openpyxl.load_workbook(file_path, data_only=True)

    all_transformed = []
    all_errors = []

    # Process multiple sheets
    for sheet_name in ["Sheet1", "Sheet2", "Sheet3"]:
        if sheet_name not in workbook.sheetnames:
            continue

        sheet = workbook[sheet_name]
        raw_rows = self._extract_rows(sheet)

        for row_num, raw_row in enumerate(raw_rows, start=2):
            try:
                transformed = self._transform_row(raw_row, user_id, batch_id)
                if transformed:
                    all_transformed.append(transformed)
            except Exception as e:
                all_errors.append({
                    "sheet": sheet_name,
                    "row_number": row_num,
                    "error": str(e),
                    "raw_data": raw_row
                })

    workbook.close()

    return {
        "total_rows": len(all_transformed) + len(all_errors),
        "successful_rows": len(all_transformed),
        "failed_rows": len(all_errors),
        "transformed_data": all_transformed,
        "errors": all_errors
    }
```

### Pattern 2: Aggregation Required (Daily → Monthly)

**Problem:** File has daily sales but we need monthly totals

**Solution:**

```python
from collections import defaultdict

def _transform_row(self, raw_row: Dict, user_id: str, batch_id: str):
    # Extract and transform as usual
    transformed = { ... }

    # Return with daily granularity
    return transformed

def process(self, file_path: str, user_id: str, batch_id: str):
    # ... extract rows ...

    # Transform rows
    daily_rows = []
    for raw_row in raw_rows:
        transformed = self._transform_row(raw_row, user_id, batch_id)
        if transformed:
            daily_rows.append(transformed)

    # Aggregate by product + month
    aggregated = defaultdict(lambda: {
        "quantity": 0,
        "sales_eur": 0.0
    })

    for row in daily_rows:
        key = (
            row["functional_name"],
            row["year"],
            row["month"],
            row.get("reseller", "Unknown")
        )

        aggregated[key]["quantity"] += row["quantity"]
        aggregated[key]["sales_eur"] += row["sales_eur"]

        # Keep other fields from first occurrence
        if "user_id" not in aggregated[key]:
            aggregated[key].update({
                "user_id": row["user_id"],
                "upload_batch_id": row["upload_batch_id"],
                "functional_name": row["functional_name"],
                "product_ean": row.get("product_ean"),
                "reseller": row.get("reseller"),
                "year": row["year"],
                "month": row["month"],
                "created_at": row["created_at"]
            })

    # Convert to list
    monthly_rows = list(aggregated.values())

    return {
        "total_rows": len(raw_rows),
        "successful_rows": len(monthly_rows),
        "failed_rows": 0,
        "transformed_data": monthly_rows,
        "errors": []
    }
```

### Pattern 3: CSV with Custom Delimiter

**Problem:** CSV uses semicolon (;) instead of comma

**Solution:**

```python
import csv

def _extract_rows_csv(self, file_path: str) -> List[Dict[str, Any]]:
    """Extract rows from CSV file"""
    rows = []

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        # Use semicolon delimiter
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            # Strip whitespace from keys and values
            cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
            rows.append(cleaned_row)

    return rows

def process(self, file_path: str, user_id: str, batch_id: str):
    # Use CSV extraction instead of Excel
    raw_rows = self._extract_rows_csv(file_path)

    # Rest is same as Excel processing
    # ...
```

### Pattern 4: Variable Column Names

**Problem:** Column names change across files (e.g., "Product" vs "Product Name")

**Solution:**

```python
COLUMN_ALIASES = {
    "product_ean": ["EAN", "Product EAN", "Article Number", "SKU"],
    "functional_name": ["Product", "Product Name", "Description", "Item"],
    "quantity": ["Qty", "Quantity", "Units", "Sold Qty"],
    "sales_eur": ["Sales", "Revenue", "Net Sales", "Amount (EUR)"]
}

def _find_column(self, row: Dict, field: str) -> Any:
    """Find column value using aliases"""
    aliases = self.COLUMN_ALIASES.get(field, [])

    for alias in aliases:
        if alias in row:
            return row[alias]

    # Not found
    raise KeyError(f"Column not found for {field}. Tried: {aliases}")

def _transform_row(self, raw_row: Dict, user_id: str, batch_id: str):
    transformed = {
        "user_id": user_id,
        "upload_batch_id": batch_id,
    }

    # Use flexible column lookup
    transformed["product_ean"] = self._validate_ean(
        self._find_column(raw_row, "product_ean")
    )

    transformed["functional_name"] = str(
        self._find_column(raw_row, "functional_name")
    )

    # ... etc
```

### Pattern 5: Skip Total/Subtotal Rows

**Problem:** File contains subtotal rows that should be skipped

**Solution:**

```python
def _is_data_row(self, row: Dict[str, Any]) -> bool:
    """Check if row contains actual data (not total/subtotal)"""

    # Check for total keywords
    for value in row.values():
        if value and isinstance(value, str):
            value_lower = value.lower()
            if any(keyword in value_lower for keyword in [
                "total", "subtotal", "sum", "grand total", "summary"
            ]):
                return False

    # Check if all numeric fields are present
    # (totals often have empty product fields)
    if not row.get("Product EAN"):
        return False

    return True

def _extract_rows(self, sheet: Worksheet) -> List[Dict[str, Any]]:
    # ... extract rows as usual ...

    # Filter out non-data rows
    data_rows = [row for row in rows if self._is_data_row(row)]

    return data_rows
```

---

## Testing Processors

### Unit Test Template

```python
# backend/tests/test_new_vendor_processor.py

import pytest
from pathlib import Path
from app.services.vendors.new_vendor_processor import NewVendorProcessor


@pytest.fixture
def sample_file():
    """Path to sample file"""
    return Path(__file__).parent / "fixtures" / "new_vendor_sample.xlsx"


@pytest.fixture
def processor():
    """Processor instance"""
    return NewVendorProcessor()


def test_process_success(processor, sample_file):
    """Test successful file processing"""
    result = processor.process(
        file_path=str(sample_file),
        user_id="test-user-123",
        batch_id="test-batch-456"
    )

    # Check result structure
    assert "total_rows" in result
    assert "successful_rows" in result
    assert "failed_rows" in result
    assert "transformed_data" in result
    assert "errors" in result

    # Verify processing
    assert result["successful_rows"] > 0
    assert len(result["transformed_data"]) == result["successful_rows"]


def test_transform_row(processor):
    """Test row transformation"""
    raw_row = {
        "Product EAN": "1234567890123",
        "Product Name": "Test Product",
        "Quantity": "10",
        "Sales (EUR)": "99.99"
    }

    transformed = processor._transform_row(
        raw_row,
        user_id="test-user",
        batch_id="test-batch"
    )

    # Verify required fields
    assert transformed["product_ean"] == "1234567890123"
    assert transformed["functional_name"] == "Test Product"
    assert transformed["quantity"] == 10
    assert transformed["sales_eur"] == 99.99
    assert transformed["user_id"] == "test-user"


def test_invalid_ean(processor):
    """Test EAN validation"""
    with pytest.raises(ValueError, match="Invalid EAN"):
        processor._validate_ean("invalid")


def test_date_parsing(processor):
    """Test date parsing"""
    # Test various formats
    assert processor._parse_date("31/12/2024").year == 2024
    assert processor._parse_date("2024-12-31").month == 12
    assert processor._parse_date("12/31/2024").day == 31


def test_empty_file(processor, tmp_path):
    """Test handling of empty file"""
    # Create empty Excel file
    import openpyxl
    wb = openpyxl.Workbook()
    empty_file = tmp_path / "empty.xlsx"
    wb.save(empty_file)
    wb.close()

    result = processor.process(
        file_path=str(empty_file),
        user_id="test-user",
        batch_id="test-batch"
    )

    assert result["successful_rows"] == 0
```

### Integration Test Script

```python
# backend/scripts/test_processor_integration.py

"""
Integration test for vendor processor
"""

import sys
from pathlib import Path
from app.services.vendors import get_vendor_processor
from app.services.vendors.detector import vendor_detector


def test_end_to_end(file_path: str):
    """Test complete processing flow"""

    # Step 1: Detect vendor
    print(f"Testing file: {file_path}")
    filename = Path(file_path).name

    vendor_name, confidence = vendor_detector.detect_vendor(file_path, filename)
    print(f"Detected vendor: {vendor_name} (confidence: {confidence:.2f})")

    if not vendor_name:
        print("❌ Vendor detection failed")
        return False

    # Step 2: Get processor
    try:
        processor = get_vendor_processor(vendor_name)
        print(f"✓ Processor loaded: {processor.__class__.__name__}")
    except ValueError as e:
        print(f"❌ Processor not found: {e}")
        return False

    # Step 3: Process file
    try:
        result = processor.process(
            file_path=file_path,
            user_id="test-user-integration",
            batch_id="test-batch-integration"
        )

        print(f"\n=== Processing Results ===")
        print(f"Total rows: {result['total_rows']}")
        print(f"Successful: {result['successful_rows']}")
        print(f"Failed: {result['failed_rows']}")

        # Show first transformed row
        if result['transformed_data']:
            print(f"\nSample transformed row:")
            sample = result['transformed_data'][0]
            for key, value in sample.items():
                print(f"  {key}: {value}")

        # Show errors
        if result['errors']:
            print(f"\nFirst 5 errors:")
            for error in result['errors'][:5]:
                print(f"  Row {error['row_number']}: {error['error']}")

        # Success criteria
        success_rate = result['successful_rows'] / result['total_rows'] if result['total_rows'] > 0 else 0
        print(f"\nSuccess rate: {success_rate:.1%}")

        if success_rate >= 0.95:
            print("✓ Processing passed (≥95% success)")
            return True
        else:
            print("⚠ Processing needs review (<95% success)")
            return False

    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_processor_integration.py <file_path>")
        sys.exit(1)

    success = test_end_to_end(sys.argv[1])
    sys.exit(0 if success else 1)
```

**Run integration test:**

```bash
cd backend
source venv/bin/activate
python scripts/test_processor_integration.py /path/to/sample.xlsx
```

---

## Debugging & Troubleshooting

### Common Issues

#### Issue 1: Column Not Found

**Error:** `KeyError: 'Product EAN'`

**Diagnosis:**
- Print actual column names in file
- Check for extra spaces, special characters
- Column might be in different language

**Solution:**
```python
def _extract_rows(self, sheet: Worksheet):
    headers = []
    for cell in sheet[1]:
        if cell.value:
            header = str(cell.value).strip()
            headers.append(header)
            print(f"Found header: '{header}'")  # Debug print

    # ... rest
```

#### Issue 2: Date Parsing Fails

**Error:** `ValueError: Unable to parse date: 44927`

**Diagnosis:**
- Excel stores dates as numbers (days since 1900-01-01)
- Need to handle Excel date format

**Solution:**
```python
from datetime import datetime, timedelta

def _parse_date(self, value: Any) -> datetime:
    # Handle Excel date number
    if isinstance(value, (int, float)):
        # Excel date (days since 1900-01-01)
        excel_epoch = datetime(1900, 1, 1)
        return excel_epoch + timedelta(days=int(value) - 2)  # Excel bug: -2

    # Handle string dates
    # ... existing string parsing logic
```

#### Issue 3: EAN Validation Too Strict

**Error:** `ValueError: Invalid EAN format: 123456`

**Diagnosis:**
- Vendor uses custom product codes, not standard EAN-13
- Need to allow vendor-specific formats

**Solution:**
```python
def _validate_ean(self, value: Any) -> str:
    """Validate product code (flexible)"""
    if not value:
        raise ValueError("Product code cannot be empty")

    code_str = str(value).strip()

    # Remove decimal points
    if '.' in code_str:
        code_str = code_str.split('.')[0]

    # Accept various formats
    if code_str.isdigit():
        # Pad to 13 digits if shorter
        if len(code_str) < 13:
            code_str = code_str.zfill(13)
        return code_str
    else:
        # Allow alphanumeric codes
        return code_str
```

---

## Best Practices

### 1. Error Handling

**Always validate required fields:**

```python
def _transform_row(self, raw_row: Dict, user_id: str, batch_id: str):
    # Validate required fields early
    required_fields = ["Product EAN", "Quantity", "Sales"]

    for field in required_fields:
        if field not in raw_row or not raw_row[field]:
            raise ValueError(f"Missing required field: {field}")

    # Continue with transformation
    # ...
```

**Provide descriptive error messages:**

```python
# Bad
raise ValueError("Invalid value")

# Good
raise ValueError(f"Invalid EAN format: '{value}' (expected 13 digits, got {len(value)})")
```

### 2. Logging

**Add logging for debugging:**

```python
import logging

logger = logging.getLogger(__name__)

def process(self, file_path: str, user_id: str, batch_id: str):
    logger.info(f"Processing {self.__class__.__name__}: {file_path}")

    # ... processing logic ...

    logger.info(f"Processed {len(transformed_rows)} rows successfully")
    logger.warning(f"Failed {len(errors)} rows")

    return result
```

### 3. Performance

**For large files (>10,000 rows), use batch processing:**

```python
def process(self, file_path: str, user_id: str, batch_id: str):
    # Process in batches of 1000 rows
    BATCH_SIZE = 1000

    all_transformed = []
    all_errors = []

    raw_rows = self._extract_rows(sheet)

    for i in range(0, len(raw_rows), BATCH_SIZE):
        batch = raw_rows[i:i + BATCH_SIZE]

        for row_num, raw_row in enumerate(batch, start=i + 2):
            # ... process row ...

        # Optionally: save batch to database here
        # instead of accumulating in memory

    return result
```

### 4. Testing

**Always test with:**
- ✅ Valid sample file (happy path)
- ✅ File with missing columns
- ✅ File with invalid data (empty cells, wrong formats)
- ✅ Empty file
- ✅ Large file (performance test)

### 5. Documentation

**Document processor-specific behavior:**

```python
class NewVendorProcessor:
    """
    Process [Vendor Name] Excel files

    File Format:
        - Excel (.xlsx)
        - Sheet: "Sales Report"
        - Date format: DD/MM/YYYY
        - EAN: 8-digit codes (converted to EAN-13)

    Special Cases:
        - Aggregates daily sales to monthly
        - Skips rows with "TOTAL" in product name
        - Handles multiple currencies (converts to EUR)

    Output Table: sellout_entries2 (B2B sales)

    Example:
        processor = NewVendorProcessor()
        result = processor.process("/path/to/file.xlsx", user_id, batch_id)
    """
```

---

## Quick Reference

### Processor Checklist

- [ ] Analyze file format thoroughly
- [ ] Choose target table (ecommerce_orders or sellout_entries2)
- [ ] Implement processor class
- [ ] Add column mapping
- [ ] Implement validation methods
- [ ] Handle edge cases
- [ ] Register in detector.py
- [ ] Register in __init__.py
- [ ] Write unit tests
- [ ] Test with real sample files
- [ ] Document special cases
- [ ] Deploy and monitor

### Key Files

```
backend/app/services/vendors/
├── __init__.py              # Processor factory
├── detector.py              # Vendor detection logic
├── new_vendor_processor.py  # Your new processor
└── config_loader.py         # Vendor configs

backend/tests/
└── test_new_vendor_processor.py  # Unit tests

backend/scripts/
└── test_processor_integration.py  # Integration test
```

### Common Imports

```python
# Excel processing
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

# CSV processing
import csv

# Date handling
from datetime import datetime, timedelta

# Type hints
from typing import Dict, List, Any, Optional

# Aggregation
from collections import defaultdict

# Logging
import logging
logger = logging.getLogger(__name__)
```

---

## Next Steps

- Read [Deployment Checklist](./04_Deployment_Checklist.md)
- Review existing processors in `backend/app/services/vendors/`
- Test your processor with sample files
- Monitor processing success rates in production
