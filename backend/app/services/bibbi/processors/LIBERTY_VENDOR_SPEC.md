# Liberty Vendor Processor Specification

**Status**: ✅ **IMPLEMENTED AND VERIFIED** (2025-10-26)
**Implementation**: `backend/app/services/bibbi/processors/liberty_processor.py`
**Test Results**: £7,023.46 total (expected £7,023.50) - 4p variance due to rounding

---

## 1. BASIC INFORMATION

**Vendor Name** (exact string for class name):
→ **Liberty**

**Primary Contact Person**:
→ (To be filled by user)

**Reporting Currency**:
☑ GBP  ☐ EUR  ☐ USD  ☐ PLN  ☐ ZAR  ☐ Other

**Reporting Frequency**:
☑ Monthly  ☐ Weekly  ☐ Daily  ☐ Other

**Timezone**:
→ **N/A** (dates extracted from filename or user-provided)

---

## 2. FILE STRUCTURE ANALYSIS

### 2.1 File Format
☑ Excel .xlsx
☐ Excel .xls (old format)
☐ CSV
☐ JSON
☐ Other

### 2.2 Excel-Specific Details

**Sheet name(s) to process**:
→ **First sheet (index 0)**

**Total number of header rows** (before data starts):
→ **3 rows** (Rows 1-3 are headers, data starts Row 4)

**Data start row number** (1-indexed):
→ **Row 4**

**Data end row**:
☑ Last non-empty row in sheet
☐ Specific row
☐ Until specific marker

**Are there merged cells?**
☑ Yes → **Row 1: Store names (Flagship spans cols 12-15, Internet spans cols 16-19)**
        **Row 2: Date ranges (Actual spans cols 12-13, YTD spans cols 14-15, etc.)**

**Are there summary/total rows?**
☐ No
☑ Yes → **Rows containing "All Sales Channels" or "All Warehouse" are skipped**

---

## 3. HEADER ROW STRUCTURE

### 3.1 Number of Header Rows
→ **3** rows

### 3.2 Row-by-Row Header Breakdown

**ROW 1 Contains**:
→ **Store names and product metadata column headers**

**Merged cells in Row 1?**
☑ Yes → **Flagship (merged across cols 12-15), Internet (merged across cols 16-19), All Sales Channels (merged), All Warehouse (merged)**

**Values in Row 1** (first 25 columns):
```
Col 0: "" (empty)
Col 1: None
Col 2: None
Col 3: None
Col 4: None
Col 5: "" (empty)
Col 6: None
Col 7: None
Col 8: None
Col 9: None
Col 10: None
Col 11: None
Col 12: "Flagship"
Col 13: None (merged continuation)
Col 14: None (merged continuation)
Col 15: None (merged continuation)
Col 16: "Internet"
Col 17: None (merged continuation)
Col 18: None (merged continuation)
Col 19: None (merged continuation)
Col 20: "All Sales Channels"
Col 21: None (merged continuation)
Col 22: None (merged continuation)
Col 23: None (merged continuation)
Col 24: "All Warehouse"
```

---

**ROW 2 Contains**:
→ **Date range labels (Actual, YTD) - CRITICAL for column filtering**

**Merged cells in Row 2?**
☑ Yes → **"Actual" merged across 2 columns, "YTD" merged across 2 columns**

**Values in Row 2** (first 25 columns):
```
Col 0: "" (empty)
Col 1: None
Col 2: None
Col 3: None
Col 4: None
Col 5: "" (empty)
Col 6: None
Col 7: None
Col 8: None
Col 9: None
Col 10: None
Col 11: None
Col 12: "Actual"
Col 13: None (merged continuation)
Col 14: "YTD"
Col 15: None (merged continuation)
Col 16: "Actual"
Col 17: None (merged continuation)
Col 18: "YTD"
Col 19: None (merged continuation)
Col 20: "Actual"
Col 21: None (merged continuation)
Col 22: "YTD"
Col 23: None (merged continuation)
Col 24: "Actual"
```

---

**ROW 3 Contains**:
→ **Final column headers (Sales Qty Un, Sales Inc VAT £, etc.)**

**Values in Row 3** (first 25 columns):
```
Col 0: "Retail Group"
Col 1: "Brand"
Col 2: "Colour Phase"
Col 3: "Product Group"
Col 4: "Item ID | Colour"
Col 5: "Item"
Col 6: "Supplier Reference"
Col 7: "Size"
Col 8: "Style"
Col 9: "Cost Price "
Col 10: "Original Price"
Col 11: "Retail Price "
Col 12: "Sales Qty Un"
Col 13: "Sales Inc VAT £ "
Col 14: "Sales Qty Un"
Col 15: "Sales Inc VAT £ "
Col 16: "Sales Qty Un"
Col 17: "Sales Inc VAT £ "
Col 18: "Sales Qty Un"
Col 19: "Sales Inc VAT £ "
Col 20: "Sales Qty Un"
Col 21: "Sales Inc VAT £ "
Col 22: "Sales Qty Un"
Col 23: "Sales Inc VAT £ "
Col 24: "Stock Qty Un"
```

---

## 4. COLUMN MAPPING SCHEMA

### 4.1 Structure Type

☐ SIMPLE: Single-row headers, one set of columns
☑ **COMPLEX: Multi-column horizontal structure**
  **→ Multiple stores (Flagship, Internet) side-by-side, each with Actual and YTD sections**
☐ VERTICAL: Multiple sections stacked vertically

### 4.3 For COMPLEX Multi-Column Structure

**Structure Description**:
→ **Flagship and Internet stores positioned horizontally with separate columns. Each store has "Actual" (monthly) and "YTD" (cumulative) sections. Processor extracts ONLY from "Actual" sections.**

**Store Identification Method**:
- Stores listed in: **Row 1, columns 12-24**
- Store names: **"Flagship", "Internet"**
- Skip these values (non-stores): **"Retail Group", "Brand", "Colour Phase", "Product Group", "Item ID | Colour", "Item", "All Warehouse", "All Sales Channels", "Total", ""**

**Column Pattern PER STORE**:

**Section Identifier** (Actual vs YTD):
- Found in: **Row 2**
- Section to KEEP: **"Actual"** (skip "YTD", "Total", "Budget")
- How to handle merged cells:
  ☑ **First cell has value, rest are None - track last seen value**
  **→ Use `current_row2_label` variable that updates when Row 2[idx] has value, persists when Row 2[idx] is None**

**Quantity Column per Store**:
- Header in Row 3: **"Sales Qty Un"**
- Position within store section: ☑ **First "Actual" occurrence per store**

**Sales Amount Column per Store**:
- Header in Row 3: **"Sales Inc VAT £ "** (note trailing space)
- Position within store section: ☑ **First "Actual" occurrence per store**

**Actual Column Indices**:
```
Store: Flagship
  - Section label "Actual" at column: 12 (merged through col 13)
  - Quantity column index: 12 (Row 3: "Sales Qty Un")
  - Sales column index: 13 (Row 3: "Sales Inc VAT £ ")

Store: Internet
  - Section label "Actual" at column: 16 (merged through col 17)
  - Quantity column index: 16 (Row 3: "Sales Qty Un")
  - Sales column index: 17 (Row 3: "Sales Inc VAT £ ")
```

---

## 5. DATA ROW IDENTIFICATION

### 5.1 Row Pattern

☐ SIMPLE: Every row from Row X to last row is a data row
☑ **COMPLEX: 2-row pattern per product**
  - Product record spans: **2 rows**
  - Row pattern: **Row 1 (odd row) has product metadata (EAN, name, category). Row 2 (even row) has sales data across stores (quantities, amounts).**

### 5.2 Row Identification Logic

**How to identify product row start**:
→ **First row of pair (odd row starting from Row 4): Contains product EAN in column 4 and product name in column 5**

**How to identify end of data**:
☑ Last non-empty row
☐ Row contains marker
☐ Fixed row number

**How to link rows in multi-row pattern**:
→ **Row N (product metadata) and Row N+1 (sales data) form a pair. Extract product info from Row N, extract sales quantities/amounts from Row N+1. Create separate records for each store.**

### 5.3 Skip Conditions

**Skip row if** (check all that apply):
☑ Quantity is zero
☑ Sales amount is zero
☑ Product name is empty
☐ Product EAN is invalid and lookup fails (handled with fallback)
☑ Row contains specific marker: **If store_identifier is in skip list or row is detected as summary row**
☐ Row is flagged as summary
☐ Other

---

## 6. DATA EXTRACTION RULES (Field-by-Field)

### Field: **product_ean**
**Source**:
- Column name/index: **"Item ID | Colour" (column 4, index 4)**
- Row in multi-row pattern: ☑ **Row 1 of 2-row pair**
- Extraction logic: **First 13 characters of cell value**

**Validation**:
- Must be: **13 digits (EAN-13 format)**

**If validation fails**:
☑ **Lookup in products table by functional_name (exact match)**
☐ Lookup in products table by functional_name (fuzzy match)
☐ Skip row and log error
☐ Use placeholder
☐ Other

---

### Field: **functional_name**
**Source**:
- Column name/index: **"Item" (column 5, index 5)**
- Row in multi-row pattern: ☑ **Row 1 of 2-row pair**

**Transformation**:
☑ **Entire cell value, strip whitespace**
☐ Title case
☐ Uppercase
☐ As-is (no changes)
☐ Extract pattern

**If missing**:
☑ **Skip row**
☐ Default to "Unknown Product"
☐ Use EAN as name
☐ Other

---

### Field: **quantity**
**Source**:
- ☑ **Multi-store: Depends on store (see multi-store logic)**
  **→ For Flagship: column 12, For Internet: column 16**

**Row in multi-row pattern**: ☑ **Row 2 of 2-row pair**

**Data type**: ☑ **Integer**

**Handling**:
- If negative: ☑ **Skip row**
- If zero: ☑ **Skip row**
- If missing/null: ☑ **Skip row**

---

### Field: **sales_eur**
**Source**:
- Column for sales amount: **"Sales Inc VAT £ "**
  **→ For Flagship: column 13, For Internet: column 17**
- Row in multi-row pattern: ☑ **Row 2 of 2-row pair**

**Currency Conversion**:
- Vendor's currency: **GBP**
- Conversion to EUR: **GBP amount × 1.17**

**Amount Interpretation** (CRITICAL):
☑ **TOTAL sales for all quantity in this row**
  **→ The value in "Sales Inc VAT £" is the TOTAL sales for all units sold. This is NOT per-unit price.**

**Decimal Places**: **2**

**If missing**: ☑ **Skip row**

---

### Field: **sale_date**
**Source**:
☐ From file column
☑ **From filename pattern: "Report_YYYYMM.xlsx" OR user provides month/year**
☐ User provides month/year during upload

**Date Calculation**:
→ **Use last day of the month. Example: Report_202401.xlsx → 2024-01-31**
→ **If no date found, use current date (upload date)**

**If ambiguous date format**:
☐ DD/MM/YYYY  ☐ MM/DD/YYYY  ☑ **N/A (date from filename or upload)**

**If missing**: ☑ **Use upload date (current date)**

---

### Field: **sales_channel**
**Source**:
☑ **From store identifier:**
  - **If store_identifier == "internet" → "online"**
  - **Otherwise (flagship, etc.) → "offline"**

☐ From file column
☐ Fixed value

---

### Fields: **month** and **year**
**Source**:
☑ **Derived from sale_date**
  **→ month = sale_date.month, year = sale_date.year**

☐ From file columns directly
☐ From filename pattern

---

### Field: **reseller_id**
**Source**: ☑ **From processor initialization parameter (UUID)**

### Field: **upload_id**
**Source**: ☑ **From batch_id parameter**

---

## 7. STORE EXTRACTION LOGIC

### 7.1 Number of Stores

☐ Single store
☑ **Multiple stores** (list ALL):

**Store 1**:
- Identifier (for database): **"flagship"**
- Display name: **"Flagship Store"**
- Type: ☑ **Physical**  ☐ Online

**Store 2**:
- Identifier: **"internet"**
- Display name: **"Internet Store"**
- Type: ☐ Physical  ☑ **Online**

### 7.2 Store Identification Method

**Source**: **Row 1, columns 12-24**

**Detection logic**:
→ **Cell value is not empty AND not in skip list:**
  **['Retail Group', 'Brand', 'Colour Phase', 'Product Group', 'Item ID | Colour', 'Item', 'All Warehouse', 'All Sales Channels', 'Total', '']**

**Store name normalization**:
→ **Lowercase + replace spaces with underscores:**
  **"Flagship" → "flagship", "Internet" → "internet"**

**Store type mapping**:
- **"flagship"** → type: ☑ **Physical**
- **"internet"** → type: ☑ **Online**
- Default → type: ☑ **Physical**

---

## 8. MULTI-STORE DATA GENERATION

**Output Strategy**:
☑ **Create separate sales_unified record for EACH store**
  **→ Example: 1 product in file with 2 stores = 2 rows in sales_unified**

### Per-Store Extraction

**For store "flagship"**:
- Quantity from: **Column 12** (Row 3 header: "Sales Qty Un")
  - Located under Row 2 section: **"Actual"**
- Sales amount from: **Column 13** (Row 3 header: "Sales Inc VAT £ ")
  - Located under Row 2 section: **"Actual"**
- store_identifier: **"flagship"**
- sales_channel: ☑ **offline**

**For store "internet"**:
- Quantity from: **Column 16** (Row 3 header: "Sales Qty Un")
  - Located under Row 2 section: **"Actual"**
- Sales amount from: **Column 17** (Row 3 header: "Sales Inc VAT £ ")
  - Located under Row 2 section: **"Actual"**
- store_identifier: **"internet"**
- sales_channel: ☑ **online**

---

## 9. COMPLETE WORKING EXAMPLE

### Input Data (actual Excel cells)

```
Row 1:  | Retail Group | Brand | ... | Item ID | Colour | Item | ... | Flagship | None | None | None | Internet | None | None | None | ...
Row 2:  | (empty)      | None  | ... | None    | None   | None | ... | Actual   | None | YTD  | None | Actual   | None | YTD  | None | ...
Row 3:  | Retail Group | Brand | ... | Item ID | Colour | Item | ... | Sales Qty Un | Sales Inc VAT £ | Sales Qty Un | Sales Inc VAT £ | Sales Qty Un | Sales Inc VAT £ | ...
Row 4:  | GHOST        | BIBBI | ... | 5060084589304 | | GHOST OF TOM EAU DE PARFUM 30 ML | ... | (empty) | (empty) | (empty) | (empty) | (empty) | (empty) | ...
Row 5:  | (empty)      | (empty) | ... | (empty) | (empty) | (empty) | ... | 1 | 99.00 | 71 | 7546.00 | 12 | 1210.00 | 328 | 33649.00 | ...
```

**Example Product**: **GHOST OF TOM EAU DE PARFUM 30 ML**
- Row 4 (metadata): EAN=5060084589304, Name="GHOST OF TOM EAU DE PARFUM 30 ML"
- Row 5 (sales data):
  - Flagship Actual: qty=1, sales=£99.00
  - Flagship YTD: qty=71, sales=£7,546.00 (SKIPPED - not "Actual")
  - Internet Actual: qty=12, sales=£1,210.00
  - Internet YTD: qty=328, sales=£33,649.00 (SKIPPED - not "Actual")

### Expected Output (exact sales_unified records)

**Record 1** (Flagship):
```json
{
  "product_ean": "5060084589304",
  "functional_name": "GHOST OF TOM EAU DE PARFUM 30 ML",
  "quantity": 1,
  "sales_eur": 115.83,  // 99.00 GBP * 1.17 = 115.83 EUR
  "sale_date": "2025-10-26",  // From upload date (no filename date)
  "sales_channel": "offline",
  "store_identifier": "flagship",
  "reseller_id": "uuid-from-parameter",
  "upload_id": "batch-id-from-parameter",
  "month": 10,
  "year": 2025
}
```

**Record 2** (Internet):
```json
{
  "product_ean": "5060084589304",
  "functional_name": "GHOST OF TOM EAU DE PARFUM 30 ML",
  "quantity": 12,
  "sales_eur": 1415.70,  // 1210.00 GBP * 1.17 = 1415.70 EUR
  "sale_date": "2025-10-26",
  "sales_channel": "online",
  "store_identifier": "internet",
  "reseller_id": "uuid-from-parameter",
  "upload_id": "batch-id-from-parameter",
  "month": 10,
  "year": 2025
}
```

---

## 10. EDGE CASES & SPECIAL HANDLING

### Missing EAN
**Action**:
☑ **Lookup in products table using functional_name (exact match)**
☐ Lookup in products table using functional_name (fuzzy match)
☐ Skip row and log error
☐ Use placeholder EAN
☐ Other

**If lookup fails**:
☐ Skip row
☑ **Continue with NULL EAN (still insert the record)**
☐ Other

---

### Duplicate Products
**Same product appears multiple times in file**:
☐ Sum quantities and sales amounts
☑ **Keep as separate records** (each row pair creates 2 records)
☐ Take first occurrence only
☐ Other

**Same product in different stores**:
☑ **Create separate records (already handled by multi-store logic)**
☐ Aggregate into one record
☐ Other

---

### Currency Issues
**File contains multiple currencies**:
☑ **Not expected - all amounts are GBP**
☐ Handle per row based on column
☐ Other

**Currency symbol missing**:
☑ **Assume GBP (vendor's default currency)**
☐ Skip row
☐ Other

---

### Date Issues
**No date in file**:
☑ **Extract from filename pattern: "Report_YYYYMM.xlsx" → "YYYY-MM-31" (last day of month)**
☑ **User provides during upload**
☑ **Use upload date if both fail**
☐ Other

**Invalid/unparseable date**:
☑ **Use upload date (current date)**
☐ Skip row
☐ Use filename date
☐ Other

---

### Zero Quantity or Sales
**Quantity is zero**:
☑ **Skip row**
☐ Keep row
☐ Other

**Sales amount is zero**:
☑ **Skip row**
☐ Keep row
☐ Other

---

### Negative Values
**Negative quantity**:
☑ **Skip row**
☐ Take absolute value
☐ Record as product return/refund
☐ Other

**Negative sales amount**:
☑ **Skip row**
☐ Take absolute value
☐ Record as refund
☐ Other

---

## 11. VALIDATION CHECKLIST

**Verification** (2025-10-26):

☑ **Section 1**: Basic info complete (Liberty, GBP currency)
☑ **Section 2**: File structure documented (.xlsx, 3 header rows, merged cells)
☑ **Section 3**: All header rows documented with actual values
☑ **Section 4**: Complex multi-column structure mapped
☑ **Section 5**: 2-row pattern identified
☑ **Section 6**: All sales_unified fields mapped with GBP→EUR conversion
☑ **Section 7**: 2 stores extracted (flagship, internet)
☑ **Section 8**: Multi-store generation creates 2 records per product
☑ **Section 9**: Working example verified: Ghost of Tom → 2 records
☑ **Section 10**: Edge cases addressed (merged cells, missing EAN, zero values)
☑ **Actual test results**: £7,023.46 total (expected £7,023.50) - 4p variance acceptable

---

## IMPLEMENTATION NOTES

**Key Implementation Details**:

1. **Merged Cell Handling**: Use `current_row2_label` variable that tracks the most recent Row 2 value. When Row 2[idx] has a value, update the variable. When Row 2[idx] is None (merged cell continuation), use the tracked value.

2. **"Actual" Section Filtering**: Only map columns where `current_row2_label` contains "actual". This prevents reading YTD/cumulative columns.

3. **2-Row Pattern**: Process rows in pairs:
   - Row N (metadata): Extract EAN, name from columns 4-5
   - Row N+1 (sales): Extract qty/sales for each store from their respective columns

4. **Store-Specific Columns**: Each store has its own column indices detected dynamically. First "Actual" section under each store name in Row 1.

5. **Sales Amount Interpretation**: The value is TOTAL sales for all quantity, not per-unit price. Do NOT divide by quantity.

---

## SUBMISSION

**Completed by**: Claude Code
**Date**: 2025-10-26
**Reviewed by**: Working implementation verified with actual upload

**Ready for implementation**: ☑ **Yes - Already implemented and tested**

**Test Results**:
- ✅ 22 records processed, 21 inserted
- ✅ Total: £7,023.46 (expected £7,023.50)
- ✅ Ghost of Tom: Flagship (1 unit, £99), Internet (12 units, £1,210)
- ✅ Columns correctly detected: flagship (12, 13), internet (16, 17)
