# Test Data Files

This directory contains sample data files for testing the upload and processing pipeline.

## Creating Test Files

### Option 1: Use the Generator Script

```bash
# From backend directory, inside virtual environment
cd backend
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies if not already installed
pip install openpyxl

# Run generator
python scripts/generate_test_data.py
```

This will create:
- `test_boxnox.xlsx` - Valid Boxnox data (10 rows)
- `test_boxnox_invalid.xlsx` - Invalid data for error testing

### Option 2: Manual Creation

Create an Excel file with the following structure:

**Filename:** `test_boxnox.xlsx`
**Sheet Name:** `Sell Out by EAN`

**Headers (Row 1):**
| Product EAN | Functional Name | Sold Qty | Sales Amount (EUR) | Reseller | Month | Year |

**Sample Data Rows:**
| Product EAN   | Functional Name      | Sold Qty | Sales Amount (EUR) | Reseller    | Month | Year |
|---------------|----------------------|----------|-------------------|-------------|-------|------|
| 1234567890123 | Test Product Alpha   | 10       | 99.99             | Retailer A  | 1     | 2025 |
| 9876543210987 | Test Product Beta    | 5        | 49.99             | Retailer B  | 1     | 2025 |
| 5555555555555 | Test Product Gamma   | 20       | 199.99            | Retailer A  | 2     | 2025 |
| 1111111111111 | Test Product Delta   | 15       | 149.99            | Retailer C  | 2     | 2025 |
| 2222222222222 | Test Product Epsilon | 8        | 79.99             | Retailer B  | 3     | 2025 |

**Requirements:**
- ✅ Sheet must be named exactly "Sell Out by EAN"
- ✅ EAN must be 13 digits (can be stored as text or number)
- ✅ Month: 1-12
- ✅ Year: 2000-2100
- ✅ Sold Qty: Integer > 0
- ✅ Sales Amount: Decimal number

### Option 3: Download Template

Use the template spreadsheet:

1. Open a spreadsheet application (Excel, Google Sheets, LibreOffice)
2. Create a sheet named "Sell Out by EAN"
3. Add the headers in row 1
4. Add sample data rows
5. Save as `.xlsx` format

## Test Scenarios

### Valid Upload (Happy Path)

**File:** `test_boxnox.xlsx`

**Expected Results:**
- ✅ File accepted and validated
- ✅ Vendor detected as "boxnox"
- ✅ All rows processed successfully
- ✅ Data inserted into `sellout_entries2` table
- ✅ Success email sent
- ✅ Processing status: "completed"

### Invalid Data (Error Handling)

**File:** `test_boxnox_invalid.xlsx`

**Expected Results:**
- ⚠️ File accepted but processing encounters errors
- ❌ Invalid rows rejected (wrong EAN format, invalid month, etc.)
- ✅ Error details recorded in `error_reports` table
- ✅ Batch status shows failed rows count
- ⚠️ Warning email sent with error details

### Append Mode Test

1. Upload `test_boxnox.xlsx` with mode: **Append**
2. Upload the same file again with mode: **Append**
3. Expected: Duplicates detected and skipped

### Replace Mode Test

1. Upload `test_boxnox.xlsx` with mode: **Replace**
2. Upload the same file again with mode: **Replace**
3. Expected: Old data deleted, new data inserted

## Test Data Specifications

### Boxnox Format

**File Pattern:** Filename contains "boxnox" (case-insensitive)
**Sheet Name:** "Sell Out by EAN"
**Columns:**
- `Product EAN` (text/number, 13 digits) - REQUIRED
- `Functional Name` (text) - optional
- `Sold Qty` (integer) - REQUIRED
- `Sales Amount (EUR)` (decimal) - optional
- `Reseller` (text) - optional
- `Month` (integer 1-12) - REQUIRED
- `Year` (integer 2000-2100) - REQUIRED

**Validation Rules:**
```python
# EAN must be exactly 13 digits
ean_pattern = r'^\d{13}$'

# Month range
1 <= month <= 12

# Year range
2000 <= year <= 2100

# Quantity must be positive
quantity > 0
```

## Quick Test Commands

### Using cURL

```bash
# Set your token
TOKEN="your-jwt-token-here"

# Upload test file
curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_boxnox.xlsx" \
  -F "mode=append"

# Response will include batch_id, use it to check status:
BATCH_ID="returned-batch-id"

# Check processing status
curl -X GET "http://localhost:8000/api/uploads/batches/$BATCH_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### Using the Frontend

1. Start frontend: `cd frontend && npm run dev`
2. Navigate to: `http://localhost:5173`
3. Login with test user
4. Go to Upload page
5. Select mode (Append/Replace)
6. Drag and drop test file
7. Click Upload
8. Monitor processing status

## Troubleshooting

### Issue: Vendor not detected

**Check:**
- Sheet name is exactly "Sell Out by EAN" (case-sensitive)
- Filename contains "boxnox"
- Column headers match expected names

### Issue: All rows fail validation

**Check:**
- EAN codes are 13 digits
- Month values are 1-12
- Year values are 2000-2100
- Required fields are not empty

### Issue: Duplicate detection not working

**Check:**
- Using "append" mode
- Same EAN + Reseller + Month + Year combination
- RLS policies allow read access for duplicate checking

## Files in This Directory

```
test_data/
├── README.md (this file)
├── test_boxnox.xlsx (generated by script)
└── test_boxnox_invalid.xlsx (generated by script)
```

## Next Steps

After testing with Boxnox files, you'll add processors for other vendors in Phase 2:
- Galilu (Poland, PLN)
- Skins SA (South Africa, ZAR)
- CDLC (special header format)
- Liberty/Selfridges (UK, GBP)
- Ukraine (TDSheet tab, UAH)
- Skins NL (Netherlands, EUR)
- Continuity (UK subscription data)
- Online/Ecommerce (different schema)
