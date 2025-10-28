# Vendor Processor Specification Form

**Purpose**: This form captures ALL information needed to implement a vendor data processor in one shot without requiring any follow-up questions.

**Instructions**: Fill out EVERY section completely. Leave NO blanks. If a section doesn't apply, write "N/A" and explain why.

---

## 1. BASIC INFORMATION

**Vendor Name** (exact string for class name):
_Example: Liberty, Galilu, Selfridges_
→ ________________

**Primary Contact Person**:
→ ________________

**Reporting Currency**:
☐ EUR  ☐ GBP  ☐ USD  ☐ PLN  ☐ ZAR  ☐ Other: ________

**Reporting Frequency**:
☐ Monthly  ☐ Weekly  ☐ Daily  ☐ Other: ________

**Timezone** (if date/time matters):
→ ________________ or "N/A"

---

## 2. FILE STRUCTURE ANALYSIS

### 2.1 File Format
☐ Excel .xlsx
☐ Excel .xls (old format)
☐ CSV
☐ JSON
☐ Other: ________________

### 2.2 Excel-Specific Details (skip if not Excel)

**Sheet name(s) to process**:
→ ________________
_Example: "Sheet1", "Sales Data", "All Sheets"_

**Total number of header rows** (before data starts):
→ ________ rows
_Example: 3 (Rows 1-3 are headers, data starts Row 4)_

**Data start row number** (1-indexed):
→ Row ________

**Data end row**:
☐ Last non-empty row in sheet
☐ Specific row: ________
☐ Until specific marker: ________________

**Are there merged cells?**
☐ No
☐ Yes → Where exactly? ________________
_Example: "Row 1 columns 12-15 (store name)", "Row 2 columns 12-13 (date range)"_

**Are there summary/total rows?**
☐ No
☐ Yes → Where exactly? ________________
_Example: "Last row contains 'TOTAL'", "Every 50 rows has subtotal"_

**Screenshot Required**: Attach screenshot showing Rows 1-10 and first 20 columns

---

## 3. HEADER ROW STRUCTURE

**CRITICAL**: This section determines how to parse column headers, especially for multi-row headers like Liberty.

### 3.1 Number of Header Rows
→ ________ rows

### 3.2 Row-by-Row Header Breakdown

**ROW 1 Contains**:
_Examples: "Store names", "Date ranges", "Column categories", "Leave blank", "Product Group"_
→ ________________

**Merged cells in Row 1?**
☐ No
☐ Yes → Which columns? ________________

**Values in Row 1** (first 20 columns):
```
Col 0: ________________
Col 1: ________________
Col 2: ________________
Col 3: ________________
Col 4: ________________
Col 5: ________________
Col 6: ________________
Col 7: ________________
Col 8: ________________
Col 9: ________________
Col 10: ________________
Col 11: ________________
Col 12: ________________
Col 13: ________________
Col 14: ________________
Col 15: ________________
Col 16: ________________
Col 17: ________________
Col 18: ________________
Col 19: ________________
```

---

**ROW 2 Contains** (if applicable, otherwise write "N/A"):
_Examples: "Actual vs YTD labels", "Column groups", "Leave blank", "Units"_
→ ________________

**Merged cells in Row 2?**
☐ No
☐ Yes → Which columns? ________________

**Values in Row 2** (first 20 columns, write "None" for merged cell continuation):
```
Col 0: ________________
Col 1: ________________
Col 2: ________________
Col 3: ________________
Col 4: ________________
Col 5: ________________
Col 6: ________________
Col 7: ________________
Col 8: ________________
Col 9: ________________
Col 10: ________________
Col 11: ________________
Col 12: ________________
Col 13: ________________
Col 14: ________________
Col 15: ________________
Col 16: ________________
Col 17: ________________
Col 18: ________________
Col 19: ________________
```

---

**ROW 3 Contains** (if applicable, otherwise write "N/A"):
_Examples: "Final column headers", "Data type labels", "Leave blank"_
→ ________________

**Values in Row 3** (first 20 columns):
```
Col 0: ________________
Col 1: ________________
Col 2: ________________
Col 3: ________________
Col 4: ________________
Col 5: ________________
Col 6: ________________
Col 7: ________________
Col 8: ________________
Col 9: ________________
Col 10: ________________
Col 11: ________________
Col 12: ________________
Col 13: ________________
Col 14: ________________
Col 15: ________________
Col 16: ________________
Col 17: ________________
Col 18: ________________
Col 19: ________________
```

---

## 4. COLUMN MAPPING SCHEMA

### 4.1 Structure Type

☐ **SIMPLE: Single-row headers, one set of columns**
_Example: Row 1 has "Product EAN", "Quantity", "Sales Amount"_

☐ **COMPLEX: Multi-column horizontal structure (like Liberty)**
_Example: Multiple stores/channels side-by-side, each with own qty/sales columns_

☐ **VERTICAL: Multiple sections stacked vertically**
_Example: Flagship data rows 10-50, Internet data rows 51-100_

### 4.2 For SIMPLE Structure (skip if complex)

Fill out for EACH required field in sales_unified:

**Product EAN**:
- Column name: ________________ or Column index (0-based): ________
- Data type: ☐ String  ☐ Integer  ☐ Decimal  ☐ Date
- Required: ☐ Yes  ☐ No
- Default if missing: ________________
- Validation: ________________
  _Example: "Must be 13 digits", "No validation", "Must not be empty"_

**Product Name / functional_name**:
- Column name: ________________ or Column index: ________
- Data type: ☐ String  ☐ Integer  ☐ Decimal  ☐ Date
- Transformation: ☐ As-is  ☐ Title case  ☐ Uppercase  ☐ Strip whitespace  ☐ Other: ________
- If missing: ☐ Skip row  ☐ Default to "Unknown"  ☐ Other: ________

**Quantity**:
- Column name: ________________ or Column index: ________
- Data type: ☐ Integer  ☐ Decimal
- If negative: ☐ Skip row  ☐ Absolute value  ☐ Record as return  ☐ Other: ________
- If zero: ☐ Skip row  ☐ Keep row
- If missing/null: ☐ Skip row  ☐ Default to 0  ☐ Other: ________

**Sales Amount** (in vendor's currency):
- Column name: ________________ or Column index: ________
- Data type: ☐ Decimal (recommended)  ☐ Integer
- Decimal places: ________ (usually 2)
- Amount interpretation:
  ☐ **TOTAL for all quantity** (divide by quantity for per-unit price)
  ☐ **PER-UNIT price** (multiply by quantity for total)
- If missing: ☐ Skip row  ☐ Default to 0.00  ☐ Other: ________

**Sale Date**:
- Source:
  ☐ Column name: ________________ or Column index: ________
  ☐ From filename pattern: ________________
  ☐ User provides when uploading
- Date format if from file: ________________
  _Example: "DD/MM/YYYY", "YYYY-MM-DD", "MM/DD/YYYY"_
- If ambiguous (like 01/02/2024): ☐ DD/MM/YYYY  ☐ MM/DD/YYYY
- If missing: ☐ Use upload date  ☐ Use filename date  ☐ Skip row  ☐ Other: ________

**Sales Channel**:
- Source:
  ☐ From column: ________________ (maps: {"Online": "online", "Retail": "offline"})
  ☐ From store identifier: If store_id contains "________" → online, else offline
  ☐ Fixed value: Always "________________"

### 4.3 For COMPLEX Multi-Column Structure (like Liberty)

**Structure Description**:
_Example: "Flagship and Internet stores side-by-side, each has Actual and YTD sections"_
→ ________________

**Store Identification Method**:
- Stores listed in: Row ________ columns ________ to ________
- Store names: ________________
  _Example: "Flagship, Internet, Wholesale"_
- Skip these values (non-stores): ________________
  _Example: "Retail Group, Brand, Total, All Sales Channels"_

**Column Pattern PER STORE**:

**Section Identifier** (like "Actual" vs "YTD"):
- Found in: Row ________
- Section to KEEP: "________________"
  _Example: "Actual" (skip "YTD", "Total", "Budget")_
- How to handle merged cells:
  ☐ First cell has value, rest are None (track last seen value)
  ☐ All cells have value
  ☐ Other: ________________

**Quantity Column per Store**:
- Header in Row ________: "________________"
  _Example: "Sales Qty Un", "Units Sold", "Quantity"_
- Position within store section: ☐ First "Actual" occurrence  ☐ All "Actual" occurrences  ☐ Specific: ________

**Sales Amount Column per Store**:
- Header in Row ________: "________________"
  _Example: "Sales Inc VAT £", "Revenue EUR", "Sales Amount"_
- Position within store section: ☐ First "Actual" occurrence  ☐ All "Actual" occurrences  ☐ Specific: ________

**Example Column Indices** (fill out based on actual file):
```
Store: Flagship
  - Section label "Actual" at column: ________
  - Quantity column index: ________
  - Sales column index: ________

Store: Internet
  - Section label "Actual" at column: ________
  - Quantity column index: ________
  - Sales column index: ________
```

---

## 5. DATA ROW IDENTIFICATION

### 5.1 Row Pattern

☐ **SIMPLE: Every row from Row X to last row is a data row**
  - Data starts at row: ________ (1-indexed)

☐ **COMPLEX: Multi-row pattern per product (like Liberty's 2-row pairs)**
  - Product record spans: ________ rows
  - Row pattern description: ________________
    _Example: "Row 1 has product metadata (EAN, name), Row 2 has sales data (qty, amount)"_

### 5.2 Row Identification Logic

**How to identify product row start**:
_Example: "Cell in column A is not empty", "Column B contains 13-digit EAN", "Row not flagged as TOTAL"_
→ ________________

**How to identify end of data**:
☐ Last non-empty row
☐ Row contains marker: ________________
☐ Fixed row number: ________

**How to link rows in multi-row pattern**:
_Example: "Row N has product info, Row N+1 has sales", "Rows with same value in column A are grouped"_
→ ________________ or "N/A"

### 5.3 Skip Conditions

**Skip row if** (check all that apply):
☐ Quantity is zero
☐ Sales amount is zero
☐ Product name is empty
☐ Product EAN is invalid and lookup fails
☐ Row contains specific marker: Column ________ = "________"
☐ Row is flagged as summary (how to detect: ________________)
☐ Other: ________________

---

## 6. DATA EXTRACTION RULES (Field-by-Field)

Fill out for EACH field in sales_unified schema. Use exact terminology.

### Field: **product_ean**
**Source**:
- Column name/index: ________________
- Row in multi-row pattern: ☐ N/A  ☐ Row 1 of 2  ☐ Row 2 of 2  ☐ Other: ________
- Extraction logic: ________________
  _Example: "First 13 characters", "Entire cell value", "Extract from SKU format XXX-NNNNNNNNNNNNN"_

**Validation**:
- Must be: ________________
  _Example: "13 digits exactly", "8 or 13 digits", "Any non-empty string"_

**If validation fails**:
☐ Lookup in products table by functional_name (exact match)
☐ Lookup in products table by functional_name (fuzzy match)
☐ Skip row and log error
☐ Use placeholder: "________________"
☐ Other: ________________

---

### Field: **functional_name**
**Source**:
- Column name/index: ________________
- Row in multi-row pattern: ☐ N/A  ☐ Row 1 of 2  ☐ Row 2 of 2  ☐ Other: ________

**Transformation**:
☐ Entire cell value, strip whitespace
☐ Title case
☐ Uppercase
☐ As-is (no changes)
☐ Extract pattern: ________________

**If missing**:
☐ Skip row
☐ Default to "Unknown Product"
☐ Use EAN as name
☐ Other: ________________

---

### Field: **quantity**
**Source**:
- Single column: "________________" OR
- Multi-store: "Depends on store (see multi-store logic)"

**Row in multi-row pattern**: ☐ N/A  ☐ Row 1 of 2  ☐ Row 2 of 2  ☐ Other: ________

**Data type**: ☐ Integer  ☐ Decimal

**Handling**:
- If negative: ☐ Skip row  ☐ Absolute value  ☐ Record as return  ☐ Other: ________
- If zero: ☐ Skip row  ☐ Keep row
- If missing/null: ☐ Skip row  ☐ Default to 0  ☐ Other: ________

---

### Field: **sales_eur**
**Source**:
- Column for sales amount: "________________"
- Row in multi-row pattern: ☐ N/A  ☐ Row 1 of 2  ☐ Row 2 of 2  ☐ Other: ________

**Currency Conversion**:
- Vendor's currency: ________________ (must match Section 1)
- Conversion to EUR: ________________ × rate
  _Example: "GBP to EUR: multiply by 1.17", "Already EUR: no conversion"_

**Amount Interpretation** (CRITICAL):
☐ **TOTAL sales for all quantity in this row**
  _To get per-unit price: divide sales_eur by quantity_
☐ **PER-UNIT price**
  _To get total sales: multiply by quantity_

**Decimal Places**: ________ (usually 2)

**If missing**: ☐ Skip row  ☐ Default to 0.00  ☐ Other: ________________

---

### Field: **sale_date**
**Source**:
☐ From file column: "________________" in format "________________"
☐ From filename pattern: "________________"
  _Example: "Report_YYYYMM.xlsx → extract 202401 → January 2024"_
☐ User provides month/year during upload

**Date Calculation**:
_Example: "Use last day of month: 2024-01-31", "Use first day: 2024-01-01", "Exact date from file"_
→ ________________

**If ambiguous date format** (01/02/2024):
☐ DD/MM/YYYY  ☐ MM/DD/YYYY

**If missing**: ☐ Use upload date  ☐ Use filename date  ☐ Skip row  ☐ Other: ________

---

### Field: **sales_channel**
**Source**:
☐ From file column: "________________"
  - Mapping: {"________________": "online", "________________": "offline"}
☐ From store identifier:
  - If store contains "________________" → "online"
  - Otherwise → "offline"
☐ Fixed value: Always "________________"

---

### Fields: **month** and **year**
**Source**:
☐ Derived from sale_date
☐ From file columns directly: month column "________", year column "________"
☐ From filename pattern: ________________

---

### Field: **reseller_id**
**Source**: ☐ From processor initialization parameter (UUID)

### Field: **upload_id**
**Source**: ☐ From batch_id parameter

---

## 7. STORE EXTRACTION LOGIC

### 7.1 Number of Stores

☐ **Single store** (always)
  - Store identifier: "________________"
  - Store name: "________________"
  - Store type: ☐ Physical  ☐ Online

☐ **Multiple stores** (list ALL):

**Store 1**:
- Identifier (for database): "________________"
- Display name: "________________"
- Type: ☐ Physical  ☐ Online

**Store 2**:
- Identifier: "________________"
- Display name: "________________"
- Type: ☐ Physical  ☐ Online

**Store 3** (add more if needed):
- Identifier: "________________"
- Display name: "________________"
- Type: ☐ Physical  ☐ Online

### 7.2 Store Identification Method (for multi-store)

**Source**: Row ________ columns ________ to ________

**Detection logic**:
_Example: "Cell value not empty AND not in skip list ['Retail Group', 'Brand', 'Total']"_
→ ________________

**Store name normalization**:
_Example: "Lowercase, replace spaces with underscores: 'Internet' → 'internet'"_
→ ________________

**Store type mapping**:
- "________________" → type: ☐ Physical  ☐ Online
- "________________" → type: ☐ Physical  ☐ Online
- Default → type: ☐ Physical  ☐ Online

---

## 8. MULTI-STORE DATA GENERATION

**Only fill out if vendor file has multiple stores per product row**

**Output Strategy**:
☐ Create separate sales_unified record for EACH store
  _Example: 1 product in file with 2 stores = 2 rows in sales_unified_
☐ Single record per product (aggregate stores)
☐ Other: ________________

### Per-Store Extraction

**For store "________________"**:
- Quantity from: Column ________ (Row 3 header: "________________")
  - Located under Row 2 section: "________________"
- Sales amount from: Column ________ (Row 3 header: "________________")
  - Located under Row 2 section: "________________"
- store_identifier: "________________"
- sales_channel: ☐ online  ☐ offline

**For store "________________"**:
- Quantity from: Column ________ (Row 3 header: "________________")
  - Located under Row 2 section: "________________"
- Sales amount from: Column ________ (Row 3 header: "________________")
  - Located under Row 2 section: "________________"
- store_identifier: "________________"
- sales_channel: ☐ online  ☐ offline

---

## 9. COMPLETE WORKING EXAMPLE

### Input Data (show actual Excel cells)

```
Row 1:  | ____________ | ____________ | ____________ | ____________ | ____________ | ...
Row 2:  | ____________ | ____________ | ____________ | ____________ | ____________ | ...
Row 3:  | ____________ | ____________ | ____________ | ____________ | ____________ | ...
Row 4:  | ____________ | ____________ | ____________ | ____________ | ____________ | ...
(Product data row)
```

**Example Product**:
- Name: ________________
- EAN: ________________
- Quantity (Store 1): ________
- Sales Amount (Store 1): ________
- Quantity (Store 2 if applicable): ________
- Sales Amount (Store 2 if applicable): ________

### Expected Output (exact sales_unified records)

**Record 1**:
```json
{
  "product_ean": "________________",
  "functional_name": "________________",
  "quantity": ________,
  "sales_eur": ________,  // Show calculation: X currency * rate = Y EUR
  "sale_date": "YYYY-MM-DD",
  "sales_channel": "online" or "offline",
  "store_identifier": "________________",
  "reseller_id": "uuid-from-parameter",
  "upload_id": "batch-id-from-parameter",
  "month": ________,
  "year": ________
}
```

**Record 2** (if multi-store):
```json
{
  "product_ean": "________________",
  "functional_name": "________________",
  "quantity": ________,
  "sales_eur": ________,
  "sale_date": "YYYY-MM-DD",
  "sales_channel": "online" or "offline",
  "store_identifier": "________________",
  "reseller_id": "uuid-from-parameter",
  "upload_id": "batch-id-from-parameter",
  "month": ________,
  "year": ________
}
```

---

## 10. EDGE CASES & SPECIAL HANDLING

### Missing EAN
**Action**:
☐ Lookup in products table using functional_name (exact match)
☐ Lookup in products table using functional_name (fuzzy match with threshold ________%)
☐ Skip row and log error
☐ Use placeholder EAN: "________________"
☐ Other: ________________

**If lookup fails**:
☐ Skip row
☐ Create with NULL EAN
☐ Other: ________________

---

### Duplicate Products
**Same product appears multiple times in file**:
☐ Sum quantities and sales amounts
☐ Keep as separate records
☐ Take first occurrence only
☐ Other: ________________

**Same product in different stores**:
☐ Create separate records (already handled by multi-store logic)
☐ Aggregate into one record
☐ Other: ________________

---

### Currency Issues
**File contains multiple currencies**:
☐ Not expected - fail processing with error
☐ Handle per row based on column: "________________"
☐ Other: ________________

**Currency symbol missing**:
☐ Assume vendor's default currency (from Section 1)
☐ Skip row
☐ Other: ________________

---

### Date Issues
**No date in file**:
☐ Extract from filename pattern: "________________"
☐ User provides during upload
☐ Use upload date
☐ Other: ________________

**Invalid/unparseable date**:
☐ Skip row
☐ Use upload date
☐ Use filename date
☐ Other: ________________

---

### Zero Quantity or Sales
**Quantity is zero**:
☐ Skip row
☐ Keep row
☐ Other: ________________

**Sales amount is zero**:
☐ Skip row
☐ Keep row
☐ Other: ________________

---

### Negative Values
**Negative quantity**:
☐ Skip row
☐ Take absolute value
☐ Record as product return/refund
☐ Other: ________________

**Negative sales amount**:
☐ Skip row
☐ Take absolute value
☐ Record as refund
☐ Other: ________________

---

## 11. VALIDATION CHECKLIST

Before submitting this form, verify:

☐ **Section 1**: Basic info complete (vendor name, currency)
☐ **Section 2**: File structure documented (format, headers, merged cells)
☐ **Section 3**: All header rows documented with values for first 20 columns
☐ **Section 4**: Column mapping complete for simple OR complex structure
☐ **Section 5**: Row identification logic clear
☐ **Section 6**: All sales_unified fields mapped with transformations
☐ **Section 7**: Store extraction logic defined
☐ **Section 8**: Multi-store generation explained (if applicable)
☐ **Section 9**: Working example provided with input → output
☐ **Section 10**: Edge cases addressed
☐ **Screenshot attached** showing first 10 rows and 20 columns

---

## SUBMISSION

**Completed by**: ________________
**Date**: ________________
**Reviewed by**: ________________ (if applicable)

**Ready for implementation**: ☐ Yes  ☐ No (see notes below)

**Implementation notes / special considerations**:
→ ________________
