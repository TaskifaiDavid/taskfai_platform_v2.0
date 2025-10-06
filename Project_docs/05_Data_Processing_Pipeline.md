# 5. Data Processing Pipeline

This document describes the abstract, step-by-step process for transforming a raw, uploaded data file into structured data in the database using a **configuration-driven** approach that supports tenant-specific customization.

## Pipeline Stages

The pipeline is a sequence of stages, executed by the Background Worker.

### 1. Ingestion
-   **Input:** A raw file (e.g., CSV, XLSX) uploaded by a user.
-   **Action:** The system receives the file and creates an `UploadBatch` record in the database with a "pending" status.
-   **Output:** The file is stored temporarily, and a processing job is queued.

### 2. Reseller/Format Detection (Optional but Recommended)
-   **Input:** The raw file or its metadata (e.g., filename).
-   **Action:** The system attempts to automatically identify which reseller the data is from. This can be done using filename patterns, or by inspecting the file's header columns.
-   **Output:** A confirmed Reseller profile to be used for transformations.

### 3. Extraction
-   **Input:** The raw file.
-   **Action:** The system reads the data from the file, row by row. It handles the specific file format (parsing CSV, reading Excel sheets).
-   **Output:** A list of raw data rows (e.g., list of dictionaries).

### 4. Transformation & Normalization
-   **Input:** A single raw data row.
-   **Action:** This is the core logic stage. The system applies a series of configurable rules to transform the raw row into a clean, standard format. This should be a flexible rules engine. The types of rules include:
    -   **Column Mapping:** Map a source column name to a target field name (e.g., `{"Sold Qty": "quantity_sold"}`).
    -   **Data Type Conversion:** Convert string values to appropriate types (e.g., `"€1,234.56" -> 1234.56` as a decimal).
    -   **Value Standardization:** Normalize values to a canonical form (e.g., `{"Jan", "january"} -> 1`; `{"GB", "UK"} -> "United Kingdom"`).
    -   **Entity Resolution:** Look up values in the database to find foreign keys (e.g., use the SKU from a row to find the correct `product_id`).
    -   **Calculated Fields:** Create new fields by combining others (e.g., `total_revenue = quantity * unit_price`).
-   **Output:** A single, clean data object that matches the `Sale` data model.

### 5. Validation
-   **Input:** The clean data object.
-   **Action:** The system validates the data against a set of business rules (e.g., `quantity_sold` must be > 0, `sale_date` cannot be in the future).
-   **Output:** The validated data object, or an `ErrorReport` if validation fails.

### 6. Loading
-   **Input:** A list of validated, clean data objects.
-   **Action:** The system performs a bulk insert of the clean data into the appropriate table (`sellout_entries2` for offline sales or `ecommerce_orders` for online sales). If any errors were generated, they are inserted into the `ErrorReport` table.
-   **Output:** The `UploadBatch` record is updated to "completed" or "failed".

---

## Configuration-Driven Processing Architecture

TaskifAI uses a **configuration-driven** approach to vendor processing, allowing each tenant to customize data transformation rules without code changes.

### Architecture Overview

**Traditional Approach (Hardcoded):**
```
Boxnox File → BoxnoxProcessor.py (hardcoded logic) → Database
```

**Configuration-Driven Approach (TaskifAI):**
```
Vendor File → Generic Processor → Load Vendor Config (JSON from DB) → Apply Rules → Database
```

### Benefits

1. **Tenant Customization**: Each customer can have unique vendor configurations
2. **No Code Deployment**: Adding/modifying vendor logic = database config update only
3. **Scalability**: One generic processor handles all vendors via configuration
4. **Versioning**: Configuration changes are tracked and can be rolled back

### Vendor Configuration Schema

Each vendor configuration is stored as JSON in the tenant's database:

```json
{
  "vendor_name": "Boxnox",
  "tenant_id": "customer1",
  "currency": "EUR",
  "header_row": 0,
  "pivot_format": false,
  "column_mapping": {
    "Product EAN": "product_ean",
    "Functional Name": "functional_name",
    "Sold Qty": "quantity",
    "Sales Amount (EUR)": "sales_eur"
  },
  "transformation_rules": {
    "currency_conversion": null,
    "date_format": "YYYY-MM-DD"
  },
  "validation_rules": {
    "ean_length": 13,
    "month_range": [1, 12],
    "required_fields": ["product_ean", "quantity", "month", "year"]
  }
}
```

### Default vs Tenant-Specific Configurations

- **Default Configs**: System-provided baseline for each vendor (e.g., standard Boxnox config)
- **Tenant Overrides**: Customers can override any config parameter for their needs
- **Inheritance**: Tenant configs inherit from defaults, only override specific fields

**Example:**
```
Default Boxnox Config: { column_mapping: { "Product EAN": "product_ean" } }
Tenant Override: { column_mapping: { "Product Code": "product_ean" } }  // Different column name
```

---

## Vendor-Specific Processing

The system supports multiple vendors, each with unique data formats. The vendor detection system automatically identifies the vendor and applies appropriate transformation rules **loaded from the configuration database**.

### Vendor Detection Logic

**Detection Methods:**

1. **Filename Pattern Matching**
   - Extract vendor name from filename
   - Example: "Galilu_May_2024.xlsx" → Galilu detected

2. **Sheet Name Analysis**
   - Examine Excel sheet names for vendor-specific patterns
   - Example: "Sell Out by EAN" → Boxnox format

3. **Content Inspection**
   - Analyze column headers and data structure
   - Example: "OrderDate" column → Skins SA format

### Supported Vendors

#### **Galilu (Poland)**

**Currency:** PLN (Polish Zloty)
**Format:** Pivot table structure
**Special Features:**
- NULL EAN support (products without EAN codes)
- Auto-processes all products regardless of EAN
- Pivot table with months as columns

**Column Mapping:**
```
Source → Target
"Sold Qty" → quantity
"Sales Amount" → sales (converted from PLN to EUR)
Product columns → functional_name
```

**Processing Notes:**
- Allows NULL product_ean values
- Currency conversion: PLN → EUR (exchange rate applied)
- Reseller name: "Galilu"

---

#### **Boxnox (Europe)**

**Currency:** EUR
**Format:** Standard tabular
**Special Features:**
- Multiple sheet processing
- "Sell Out by EAN" sheet is primary data source

**Column Mapping:**
```
Source → Target
"Quantity" → quantity
"Revenue" → sales_eur
"EAN" → product_ean
"Product" → functional_name
```

**Processing Notes:**
- Looks for "Sell Out by EAN" sheet specifically
- Standard EUR currency (no conversion)
- Reseller name: "Boxnox"

---

#### **Skins SA (South Africa)**

**Currency:** ZAR (South African Rand)
**Format:** Standard tabular with OrderDate
**Special Features:**
- Auto-detects latest month from data
- OrderDate column for temporal analysis
- ZAR to EUR conversion

**Column Mapping:**
```
Source → Target
"OrderDate" → order_date (extracted to month/year)
"Quantity" → quantity
"Amount" → sales (converted from ZAR to EUR)
"EAN" → product_ean
"Product Name" → functional_name
```

**Processing Notes:**
- Automatically detects most recent month in dataset
- Reseller name: "Skins SA"
- Currency conversion: ZAR → EUR

---

#### **CDLC (Europe)**

**Currency:** EUR
**Format:** Pivot table with header offset
**Special Features:**
- Header row at line 4 (skip first 3 rows)
- Dynamic "Total" column detection
- Multiple month columns

**Column Mapping:**
```
Source → Target
Month columns (e.g., "Jan", "Feb") → month/year
"EAN" → product_ean
"Product" → functional_name
"Total" column → aggregated sales_eur
```

**Processing Notes:**
- Skips first 3 rows to find headers
- Detects "Total" column dynamically
- Supports both sales_eur and sales_value columns
- Reseller name: "CDLC"

---

#### **Selfridges (United Kingdom)**

**Currency:** GBP (British Pound)
**Format:** Standard tabular
**Special Features:**
- UK retailer-specific format
- GBP to EUR conversion
- Special product matching rules

**Column Mapping:**
```
Source → Target
"Units Sold" → quantity
"Sales Value" → sales (converted from GBP to EUR)
"Product Code" → product_ean
"Description" → functional_name
```

**Processing Notes:**
- Currency conversion: GBP → EUR
- Reseller name: "Selfridges"
- Premium retail channel

---

#### **Liberty (United Kingdom)**

**Currency:** GBP
**Format:** Supplier report format
**Special Features:**
- Preserves rows without product matches
- Flexible product matching
- Header row at line 1

**Column Mapping:**
```
Source → Target
"Quantity" → quantity
"Value" → sales (converted from GBP to EUR)
"SKU" → product_ean
"Item" → functional_name
```

**Processing Notes:**
- Keeps rows even if product not found in database
- Reseller name: "Liberty"
- Currency conversion: GBP → EUR

---

#### **Ukraine Distributors**

**Currency:** UAH (Ukrainian Hryvnia)
**Format:** TDSheet tab structure
**Special Features:**
- Pivot table format
- TDSheet-specific processing
- UAH to EUR conversion

**Column Mapping:**
```
Source → Target
Month columns → month/year
"Product" → functional_name
Sales values → sales (converted from UAH to EUR)
```

**Processing Notes:**
- Looks for "TDSheet" or "bibbi sales" sheet
- Currency conversion: UAH → EUR
- Reseller name: "Ukraine"

---

#### **Continuity Suppliers (United Kingdom)**

**Currency:** GBP
**Format:** Supplier size report
**Special Features:**
- Header row at line 3
- Size/variant tracking

**Column Mapping:**
```
Source → Target
"Quantity" → quantity
"Total Sales" → sales (converted from GBP to EUR)
"Product Code" → product_ean
"Size" → size variant
```

**Processing Notes:**
- Skips first 2 rows to find headers
- Reseller name: "Continuity"
- Currency conversion: GBP → EUR

---

#### **Skins NL (Netherlands)**

**Currency:** EUR
**Format:** SalesPerSKU sheet
**Special Features:**
- Netherlands-specific format
- "SalesPerSKU" sheet detection

**Column Mapping:**
```
Source → Target
"SKU" → product_ean
"Quantity" → quantity
"Sales" → sales_eur
"Product" → functional_name
```

**Processing Notes:**
- Looks for "SalesPerSKU" sheet
- Reseller name: "Skins NL"
- Standard EUR (no conversion)

---

## Advanced Processing Features

### Pivot Table Handling

Some vendors (Galilu, CDLC, Ukraine) use pivot table formats where:
- Products are rows
- Months are columns
- Values are sales figures

**Processing Strategy:**
1. Detect pivot structure
2. Iterate through month columns
3. Create separate records for each month
4. Extract month/year from column headers

**Example Transformation:**
```
Input (Pivot):
Product A | Jan 2024 | Feb 2024 | Mar 2024
          |   €100   |   €150   |   €200

Output (Normalized):
{product: "Product A", month: 1, year: 2024, sales: 100}
{product: "Product A", month: 2, year: 2024, sales: 150}
{product: "Product A", month: 3, year: 2024, sales: 200}
```

### Dynamic Column Detection

For vendors with variable column structures (CDLC):

**Challenge:** "Total" column position changes between files

**Solution:**
1. Read all column headers
2. Search for columns matching patterns (e.g., /total/i, /sum/i)
3. Use detected column for aggregation
4. Fall back to month-by-month sum if not found

### Currency Conversion

All sales data is normalized to EUR for consistency:

**Conversion Process:**
1. Detect original currency from vendor configuration
2. Apply exchange rate (configurable per vendor)
3. Store original currency in `currency` field
4. Store converted amount in `sales_eur` field

**Supported Currencies:**
- EUR (no conversion)
- GBP → EUR
- PLN → EUR
- ZAR → EUR
- UAH → EUR

**Exchange Rate Management:**
- Rates stored in vendor configuration
- Can be updated without code changes
- Historical rates can be preserved for data integrity

### NULL EAN Handling

**Problem:** Some vendors don't provide product EAN codes

**Solutions:**

1. **Galilu Approach:**
   - Allow NULL product_ean
   - Match on functional_name instead
   - Process all products regardless

2. **Other Vendors:**
   - Attempt EAN match first
   - Fall back to product name matching
   - Create error report if no match found

### Month Auto-Detection

**Skins SA Feature:**

Many vendor files don't explicitly state the reporting period.

**Detection Strategy:**
1. Scan all date values in file
2. Identify most recent month
3. Use as reporting period
4. Extract year and month number
5. Apply to all records

**Example:**
```
Dates found: 2024-05-03, 2024-05-15, 2024-05-28
Detected: May 2024
Result: month=5, year=2024 applied to all rows
```

---

## Error Handling Strategies

### Row-Level Errors

**When to Create Error Reports:**
- Missing required columns
- Invalid data types (text in numeric field)
- Failed product matching
- Date parsing failures
- Negative quantities or sales values

**Error Report Contents:**
```
{
  row_number: 15,
  error_type: "validation_error",
  error_message: "Invalid product EAN: '1234567890123' not found in database",
  raw_data: {original row data snapshot}
}
```

### File-Level Errors

**When to Fail Entire Upload:**
- Corrupted file (can't open)
- Missing all required columns
- Vendor detection failed
- Zero valid rows after processing
- Critical system errors

### Partial Success Handling

**Approach:**
- Process all valid rows
- Create error reports for invalid rows
- Mark upload as "completed with errors"
- Notify user of success count and error count

**Example:**
```
Upload Result:
- Total rows: 1,000
- Processed: 985
- Errors: 15
- Status: Completed with errors
```

---

## Performance Optimizations

### Batch Processing

- Read files in chunks (1000 rows at a time)
- Process in parallel where possible
- Bulk database inserts (not row-by-row)

### Caching

- Cache product lookups during processing
- Reuse vendor configurations
- Cache exchange rates for session

### Memory Management

- Stream large files instead of loading entirely
- Release memory after each chunk
- Limit concurrent processing jobs

---

## Adding New Vendors (Configuration-Driven)

**Steps to Add Vendor Support (No Code Required):**

1. **Analyze Vendor Format**
   - Obtain sample files from tenant
   - Identify column structure
   - Note currency and units
   - Document any special logic

2. **Create Vendor Configuration (JSON)**
   ```json
   {
     "vendor_name": "New Vendor",
     "tenant_id": "customer1",
     "currency": "USD",
     "exchange_rate_to_eur": 0.92,
     "header_row": 0,
     "pivot_format": false,
     "column_mapping": {
       "Qty Sold": "quantity",
       "Revenue": "sales",
       "Product EAN": "product_ean"
     },
     "transformation_rules": {
       "currency_conversion": "USD_to_EUR",
       "date_format": "MM/DD/YYYY"
     },
     "validation_rules": {
       "ean_length": 13,
       "required_fields": ["product_ean", "quantity"]
     }
   }
   ```

3. **Add Detection Rules (JSON)**
   ```json
   {
     "filename_keywords": ["new_vendor", "nv"],
     "sheet_names": ["Sales Data"],
     "required_columns": ["Product EAN", "Qty Sold"]
   }
   ```

4. **Store Configuration**
   - Insert config into tenant's `vendor_configs` table
   - Set `is_active = true` to enable
   - System automatically picks up new config

5. **Test with Sample Data**
   - Upload sample file
   - Verify generic processor uses config correctly
   - Check data transformation output
   - Validate results

6. **Adjust if Needed**
   - Update config JSON (no code deployment)
   - Re-test immediately
   - Changes apply instantly

**For Advanced Cases Requiring Code:**
- Complex pivot table logic
- Special data normalization algorithms
- Create custom transformation function
- Reference from config: `"custom_transform": "pivot_table_handler"`
