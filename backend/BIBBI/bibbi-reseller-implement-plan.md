# BIBBI Reseller Upload/Processing Implementation Plan

**Project**: Multi-Reseller Excel Data Processing Pipeline for BIBBI Tenant
**Target Database**: New 15-table schema (sales_unified as central fact table)
**Scope**: Tenant-isolated system for bibbi tenant ONLY
**Status**: Planning Phase → Ready for Implementation

---

## 🎯 Critical Design Principles

### 1. TENANT ISOLATION (BIBBI ONLY)
- **ALL database queries** must filter by `tenant_id = 'bibbi'`
- **ALL API endpoints** must validate tenant context before processing
- **ALL file uploads** must be tagged with `tenant_id = 'bibbi'`
- **NO cross-tenant data access** - enforce at database + application layer
- **Row-Level Security (RLS)** policies must enforce tenant isolation

### 2. New Database Schema Integration
- **Central fact table**: `sales_unified` (replaces ecommerce_orders + sellout_entries2)
- **Store tracking**: `stores` table with auto-creation on first encounter
- **Product mapping**: `product_reseller_mappings` for non-EAN resellers
- **Staging layer**: `sales_staging` with JSONB raw data storage
- **3-stage pipeline**: Raw Upload → Staging → Validation → Unified

### 3. Store-Level Granularity
- **ALL 8 resellers** provide store-level data (confirmed via resellers_info.md)
- **Store auto-creation**: First upload creates store record
- **Store identification logic**: Reseller-specific parsing rules

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ BIBBI TENANT BOUNDARY (tenant_id = 'bibbi')                     │
│                                                                  │
│  User Upload (Excel)                                            │
│         ↓                                                        │
│  [1] Vendor Detection Service                                   │
│         ↓                                                        │
│  [2] Staging Service (sales_staging table)                      │
│         ↓ (Celery async)                                        │
│  [3] Vendor-Specific Processor (9 processors)                   │
│         ↓                                                        │
│  [4] Validation Service (row-level error tracking)              │
│         ↓                                                        │
│  [5] Store Service (auto-create + mapping)                      │
│         ↓                                                        │
│  [6] Product Mapping Service (for non-EAN resellers)            │
│         ↓                                                        │
│  [7] Sales Unified Insertion (final fact table)                 │
│         ↓                                                        │
│  Dashboard Updates + Notifications                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 IMPLEMENTATION TODO LIST

### PHASE 1: Core Infrastructure Setup (Days 1-2)

#### ✅ Database Schema
- [x] 15 tables created via Supabase MCP
- [x] Indexes and triggers configured
- [x] Validation functions implemented

#### 🔲 Tenant Isolation Layer
- [ ] **Task 1.1**: Create `TenantContext` middleware
  - Location: `backend/app/core/tenant.py`
  - Validates `tenant_id = 'bibbi'` on all requests
  - Injects tenant_id into request state
  - Raises 403 for non-bibbi tenant attempts

- [ ] **Task 1.2**: Update Supabase client wrapper
  - Location: `backend/app/core/dependencies.py`
  - Add `get_bibbi_supabase_client()` that auto-filters by tenant
  - All queries must include `.eq('tenant_id', 'bibbi')`
  - Document: "NEVER use raw supabase client - always use tenant-filtered version"

- [ ] **Task 1.3**: Create tenant validation decorator
  - Location: `backend/app/core/tenant.py`
  - `@require_bibbi_tenant` decorator for all upload endpoints
  - Validates JWT token has `tenant_id = 'bibbi'`
  - Short-circuits with 403 if tenant mismatch

#### 🔲 Configuration Management
- [ ] **Task 1.4**: Create BIBBI-specific settings
  - Location: `backend/app/core/settings.py`
  - Add `BIBBI_TENANT_ID = 'bibbi'` constant
  - Add `ENABLE_MULTI_TENANT = False` (hardcode bibbi-only for now)
  - Document: "Multi-tenant support future enhancement"

- [ ] **Task 1.5**: Environment validation
  - Add startup check: Verify Supabase connection for bibbi tenant
  - Fail fast if tenant data not accessible
  - Location: `backend/app/main.py` startup event

---

### PHASE 2: File Upload & Staging (Days 3-4)

#### 🔲 Upload API Endpoint
- [ ] **Task 2.1**: Create BIBBI upload endpoint
  - Location: `backend/app/api/bibbi_uploads.py`
  - Endpoint: `POST /api/bibbi/uploads`
  - Validates: tenant_id, file type (xlsx/xls), file size (<50MB)
  - Returns: `upload_id`, `batch_id`, `status`
  - **CRITICAL**: Add `@require_bibbi_tenant` decorator

- [ ] **Task 2.2**: File hash duplicate detection
  - Calculate SHA256 hash of uploaded file
  - Query `uploads` table: `.eq('tenant_id', 'bibbi').eq('file_hash', hash)`
  - Return 409 Conflict if duplicate found
  - Store hash in uploads table for future checks

- [ ] **Task 2.3**: S3/Supabase Storage integration
  - Upload to bucket: `bibbi-reseller-uploads/{year}/{month}/{upload_id}.xlsx`
  - Tag file with metadata: `tenant_id=bibbi`, `reseller=detected_vendor`
  - Generate presigned URL for processing

#### 🔲 Staging Service
- [ ] **Task 2.4**: Create staging service
  - Location: `backend/app/services/bibbi/staging_service.py`
  - Function: `stage_upload(upload_id: str, file_path: str) -> str`
  - Inserts raw file data into `sales_staging` table
  - JSONB column stores: filename, upload_timestamp, raw_metadata
  - Returns `staging_id` for downstream processing

- [ ] **Task 2.5**: Update uploads table
  - Set `upload_status = 'staged'`
  - Record `staged_at` timestamp
  - Link `staging_id` to upload record

---

### PHASE 3: Vendor Detection & Routing (Day 5)

#### 🔲 Enhance Vendor Detector
- [ ] **Task 3.1**: Update existing detector for BIBBI
  - Location: `backend/app/services/vendors/detector.py`
  - Add tenant check: Only detect from BIBBI_VENDOR_PATTERNS
  - Current patterns support 9 vendors (boxnox, galilu, liberty, skins_sa, etc.)
  - Return: `(vendor_name: str, confidence: float, metadata: dict)`

- [ ] **Task 3.2**: Add store detection hints
  - Enhance metadata return to include: `has_store_column`, `store_sheet_name`
  - Read first 10 rows to detect store identifiers
  - Examples:
    - Liberty: "Flagship" vs "online" column
    - Skins SA: Column A "ON" = online
    - Galilu: Multiple sheets (each = store)
  - Pass hints to processor for efficient parsing

- [ ] **Task 3.3**: Create vendor router service
  - Location: `backend/app/services/bibbi/vendor_router.py`
  - Maps detected vendor → processor class
  - Returns processor instance with tenant context injected
  - Validates: Only BIBBI-supported vendors allowed

---

### PHASE 4: Adapt Existing Processors (Days 6-8)

#### 🔲 Processor Base Class
- [ ] **Task 4.1**: Create BibbiBseProcessor
  - Location: `backend/app/services/bibbi/processors/base.py`
  - Abstract base class with required methods:
    - `extract_rows(file_path: str) -> List[Dict]`
    - `transform_row(raw_row: Dict) -> Dict` (maps to sales_unified schema)
    - `extract_stores(file_path: str) -> List[Dict]` (NEW - store parsing)
    - `validate_row(transformed: Dict) -> Tuple[bool, List[str]]`
  - Injects `tenant_id = 'bibbi'` into all transformed rows
  - Currency conversion utilities (GBP→EUR, ZAR→EUR, PLN→EUR)

#### 🔲 Adapt Liberty Processor
- [ ] **Task 4.2**: Update liberty_processor.py for new schema
  - Location: `backend/app/services/bibbi/processors/liberty_processor.py`
  - Inherit from BibbiBseProcessor
  - **CRITICAL HANDLING**:
    - **Duplicate rows**: Liberty uses 2 rows per product with same amount
      - Solution: Deduplicate by `(ean, date, amount)` - keep first occurrence
    - **Returns**: Parentheses indicate returns `(123)` = -123
      - Solution: Parse `_parse_quantity()` to handle negative values
    - **Store identification**: "Flagship" = physical, "online" = online
      - Solution: `extract_stores()` creates 2 store records
  - Update COLUMN_MAPPING to sales_unified fields:
    ```python
    COLUMN_MAPPING = {
        "EAN": "product_id",
        "Product": None,  # Not stored in sales_unified
        "Sold": "quantity",
        "Value": "sales_local_currency",
        "Month": "month",
        "Year": "year",
        "Store": "store_identifier"  # NEW
    }
    ```
  - Add `sales_eur` calculation: `sales_gbp * 1.17`
  - Set `currency = 'GBP'`, `sales_local_currency` = original amount
  - Set `reseller_id` by querying `resellers` table for Liberty UUID

- [ ] **Task 4.3**: Test with Liberty sample files
  - Test files: `backend/BIBBI/Resellers/Liberty/*.xlsx` (verify count)
  - Assert: No duplicate rows in final output
  - Assert: Returns parsed as negative quantities
  - Assert: Store records auto-created (Flagship + online)

#### 🔲 Adapt Galilu Processor
- [ ] **Task 4.4**: Update galilu_processor.py for new schema
  - Location: `backend/app/services/bibbi/processors/galilu_processor.py`
  - **CRITICAL HANDLING**:
    - **No EAN codes**: Galilu uses product names only
      - Solution: Query `product_reseller_mappings` table
      - Match: `reseller_id = galilu_id AND reseller_product_code = product_name`
      - Return: `product_id` (EAN) from mapping
      - If not found: Create validation error, skip row
    - **Multi-sheet = multi-store**: Each Excel sheet represents a store
      - Solution: Override `extract_rows()` to iterate all sheets
      - Sheet name = store name → create store record
    - **Price not in file**: Galilu doesn't report sales amount
      - Solution: Query `products` table for `list_price`
      - Calculate: `sales_eur = quantity * list_price`
  - Add `_match_product_by_name()` method
  - Add `_get_or_create_store_from_sheet()` method
  - Set `currency = 'PLN'`, convert to EUR with rate 0.23

- [ ] **Task 4.5**: Create product mapping seeder
  - Location: `backend/db/seed_galilu_product_mappings.sql`
  - Manually map Galilu product names → EANs
  - Insert into `product_reseller_mappings` table
  - **REQUIRES**: Business owner input for accurate mappings

- [ ] **Task 4.6**: Test with Galilu sample files
  - Test files: `backend/BIBBI/Resellers/Galilu/*.xlsx`
  - Assert: All product names successfully mapped to EANs
  - Assert: Each sheet creates separate store record
  - Assert: Sales amount calculated from list price

#### 🔲 Adapt Skins SA Processor
- [ ] **Task 4.7**: Update skins_sa_processor.py for new schema
  - Location: `backend/app/services/bibbi/processors/skins_sa_processor.py`
  - **CRITICAL HANDLING**:
    - **Store identification**: Column A contains store codes
      - "ON" = online store
      - All other codes = physical store names
      - Solution: Parse Column A, create store records
    - **Living document**: Same file updated monthly
      - Solution: Check `month/year` columns for new data
      - Deduplicate: `(reseller_id, product_id, month, year, store_id)`
    - **Currency**: ZAR (South African Rand)
      - Conversion rate: 0.05 ZAR→EUR
    - **Dual sales columns**: "netsales" and "exvatnetsales"
      - Solution: Use `exvatnetsales` as `sales_local_currency`
    - **EAN column**: Called "Stockcode" in file
      - Map: "Stockcode" → `product_id`
  - Update date parsing to handle multiple formats
  - Set `currency = 'ZAR'`

- [ ] **Task 4.8**: Test with Skins SA sample files
  - Test files: `backend/BIBBI/Resellers/Skins_SA/*.xlsx`
  - Assert: "ON" mapped to online store
  - Assert: Physical store names extracted from Column A
  - Assert: exvatnetsales used for sales amount
  - Assert: Duplicate detection working for monthly updates

#### 🔲 Adapt Remaining 6 Processors
- [ ] **Task 4.9**: Update boxnox_processor.py
  - Store identifier: "POS" column
  - Currency: EUR (no conversion needed)
  - Living document: Check existing rows before insert
  - Sheet name: "Sell Out by EAN"

- [ ] **Task 4.10**: Update cdlc_processor.py (Creme de la Creme)
  - Store identifier: "e-shop" = online, else physical
  - Currency: EUR
  - EAN column present but needs validation
  - Requires EAN→functional_name mapping

- [ ] **Task 4.11**: Update aromateque_processor.py
  - Living document: Monthly additions to same file
  - Store/online analysis: Check for quantity per store
  - Currency: EUR
  - Requires monthly report detection

- [ ] **Task 4.12**: Update selfridges_processor.py
  - 4 physical stores + 1 online
  - Weekly reports (not monthly)
  - Store names in column headers
  - Currency: GBP (convert to EUR)
  - Living document: Weekly additions

- [ ] **Task 4.13**: Update skins_nl_processor.py
  - Sheet name: "SalesPerLocation"
  - Multi-sheet processing needed
  - Currency: EUR
  - Reports to South Africa (stops Sept 2025)
  - Store data in location columns

- [ ] **Task 4.14**: Create processors for missing vendors
  - Check if continuity/ukraine/online processors exist
  - Create if missing following BibbiBseProcessor pattern

---

### PHASE 5: Validation Service (Day 9)

#### 🔲 Row-Level Validation
- [ ] **Task 5.1**: Create validation service
  - Location: `backend/app/services/bibbi/validation_service.py`
  - Function: `validate_transformed_data(rows: List[Dict]) -> ValidationResult`
  - Checks:
    - **Required fields**: product_id, reseller_id, sale_date, quantity, sales_eur
    - **Data types**: UUID format, date format, numeric values
    - **Business rules**: quantity > 0, sales_eur >= 0 (allow 0 for returns)
    - **Foreign keys**: product_id exists in products table (tenant=bibbi)
    - **Foreign keys**: reseller_id exists in resellers table (tenant=bibbi)
    - **Foreign keys**: store_id exists in stores table (tenant=bibbi)
  - Returns: `ValidationResult` with `valid_rows`, `invalid_rows`, `errors`

- [ ] **Task 5.2**: Update sales_staging with validation results
  - Add columns: `validation_status`, `validation_errors`, `validated_at`
  - Store row-level errors: `{"row_12": ["Invalid EAN format"], ...}`
  - Set status: `pending` → `validated` or `validation_failed`

- [ ] **Task 5.3**: Create validation error reporting
  - Generate Excel report with validation errors
  - Columns: Row Number, Field, Error Message, Raw Value
  - Store in S3: `bibbi-validation-reports/{upload_id}_errors.xlsx`
  - Send email notification to uploader with report link

---

### PHASE 6: Store Service (Day 10)

#### 🔲 Store Auto-Creation
- [ ] **Task 6.1**: Create store service
  - Location: `backend/app/services/bibbi/store_service.py`
  - Function: `get_or_create_store(reseller_id: str, store_identifier: str, tenant_id: str) -> UUID`
  - Logic:
    1. Query `stores` table: `.eq('tenant_id', 'bibbi').eq('reseller_id', reseller_id).eq('store_name', store_identifier)`
    2. If exists: Return `store_id`
    3. If not exists:
       - Generate UUID
       - Determine `store_type`: 'online' if identifier in ['online', 'e-shop', 'web', 'ON'], else 'physical'
       - Insert: `{store_id, reseller_id, store_name, store_type, tenant_id='bibbi'}`
       - Return new `store_id`

- [ ] **Task 6.2**: Add store metadata enrichment
  - Parse store identifiers for additional data:
    - City/region extraction (if present in store name)
    - Online/physical classification
    - Store code normalization
  - Update stores table with metadata

- [ ] **Task 6.3**: Create store deduplication logic
  - Handle variations: "Store 1" vs "store_1" vs "Store_01"
  - Normalize store names before lookup
  - Log potential duplicates for manual review

#### 🔲 Store Mapping Cache
- [ ] **Task 6.4**: Implement Redis caching for store lookups
  - Cache key: `bibbi:store:{reseller_id}:{store_identifier}`
  - Cache value: `store_id` (UUID)
  - TTL: 24 hours
  - Reduces database lookups during bulk processing

---

### PHASE 7: Product Mapping Service (Day 11)

#### 🔲 Non-EAN Product Matching
- [ ] **Task 7.1**: Create product mapping service
  - Location: `backend/app/services/bibbi/product_mapping_service.py`
  - Function: `get_product_by_reseller_code(reseller_id: str, reseller_code: str, tenant_id: str) -> Optional[str]`
  - Logic:
    1. Query `product_reseller_mappings`: `.eq('tenant_id', 'bibbi').eq('reseller_id', reseller_id).eq('reseller_product_code', reseller_code)`
    2. If found: Return `product_id` (EAN)
    3. If not found: Return None (processor will log error)

- [ ] **Task 7.2**: Add fuzzy matching for product names
  - For Galilu: Product names may have typos or variations
  - Use `fuzzywuzzy` library for similarity matching
  - Threshold: 85% similarity
  - Log fuzzy matches for manual verification

- [ ] **Task 7.3**: Create product mapping admin interface
  - Location: `backend/app/api/bibbi_admin.py`
  - Endpoint: `POST /api/bibbi/admin/product-mappings`
  - Allows manual creation of mappings for unmapped products
  - **REQUIRES**: Business owner input for accurate mappings

- [ ] **Task 7.4**: Seed initial product mappings
  - Location: `backend/db/seed_bibbi_product_mappings.sql`
  - Map known reseller product codes → EANs
  - Priority resellers: Galilu, Liberty, Creme de la Creme
  - **REQUIRES**: Extract product lists from sample files, get EAN mappings from business owner

---

### PHASE 8: Sales Unified Insertion (Day 12)

#### 🔲 Final Data Pipeline
- [ ] **Task 8.1**: Create sales insertion service
  - Location: `backend/app/services/bibbi/sales_insertion_service.py`
  - Function: `insert_validated_sales(validated_rows: List[Dict]) -> InsertionResult`
  - Logic:
    1. For each validated row:
       - Enrich with calculated fields: `quarter = ceil(month/3)`, `week_of_year`
       - Get/create store_id via store service
       - Get product_id via mapping service (if needed)
       - Set `tenant_id = 'bibbi'`
    2. Batch insert into `sales_unified` table (batch size: 1000 rows)
    3. Handle duplicate violations (unique constraint on reseller+product+date+store)
    4. Return: `{inserted_count, duplicate_count, failed_count}`

- [ ] **Task 8.2**: Update upload status tracking
  - Set `upload_status = 'processed'` in uploads table
  - Record: `processed_at`, `total_rows`, `inserted_rows`, `failed_rows`
  - Link to sales_unified rows: Store `sales_ids` array in uploads metadata

- [ ] **Task 8.3**: Implement transaction safety
  - Wrap insertion in database transaction
  - Rollback on any failure
  - Update staging table: `staging_status = 'inserted'` or `'insertion_failed'`

#### 🔲 Duplicate Row Handling
- [ ] **Task 8.4**: Implement deduplication strategies
  - **Strategy 1**: File-level (living documents)
    - Check file hash before processing
    - If duplicate file: Skip entirely
  - **Strategy 2**: Row-level (same sale uploaded twice)
    - Unique constraint: `(tenant_id, reseller_id, product_id, sale_date, store_id, quantity)`
    - On conflict: Update `sales_eur`, `updated_at` (assume correction)
  - **Strategy 3**: Liberty double-rows
    - Deduplicate in processor before insertion
    - Group by `(ean, date, amount)`, keep first row only

- [ ] **Task 8.5**: Create deduplication report
  - Log all duplicate detections
  - Generate report: Duplicate Type, Count, Action Taken
  - Store in uploads metadata for transparency

---

### PHASE 9: Celery Task Integration (Day 13)

#### 🔲 Async Processing Pipeline
- [ ] **Task 9.1**: Create Celery task for BIBBI uploads
  - Location: `backend/app/workers/tasks/bibbi_upload_task.py`
  - Task: `process_bibbi_upload.delay(upload_id: str)`
  - Steps:
    1. Download file from storage
    2. Detect vendor
    3. Stage raw data
    4. Route to processor
    5. Extract & transform
    6. Validate
    7. Create stores
    8. Map products
    9. Insert into sales_unified
    10. Update upload status
    11. Send notification
  - Error handling: Retry 3 times with exponential backoff
  - Timeout: 30 minutes per file

- [ ] **Task 9.2**: Update Celery configuration
  - Location: `backend/app/workers/celery_app.py`
  - Add BIBBI-specific queue: `bibbi_uploads`
  - Priority: High (above general uploads)
  - Concurrency: 4 workers (allow 4 simultaneous BIBBI uploads)
  - Task routing: Route bibbi tasks to bibbi queue

- [ ] **Task 9.3**: Create progress tracking
  - Use Celery task.update_state() for progress updates
  - States: PENDING → STAGING → PROCESSING → VALIDATING → INSERTING → SUCCESS
  - Store progress in Redis: `bibbi:upload:{upload_id}:progress`
  - Frontend polls for progress updates

#### 🔲 Error Handling & Recovery
- [ ] **Task 9.4**: Implement task failure handling
  - On failure: Set upload_status = 'failed'
  - Store error details in uploads.error_message
  - Generate error report for user
  - Send failure notification email

- [ ] **Task 9.5**: Create manual retry endpoint
  - Endpoint: `POST /api/bibbi/uploads/{upload_id}/retry`
  - Validates: upload_status = 'failed'
  - Re-enqueues Celery task
  - Clears previous error state

---

### PHASE 10: Frontend Dashboard (Days 14-15)

#### 🔲 BIBBI Upload Interface
- [ ] **Task 10.1**: Create BIBBI upload page
  - Location: `frontend/src/pages/BibbıUpload.tsx`
  - Features:
    - Drag-and-drop Excel upload
    - Vendor auto-detection display
    - Real-time progress bar
    - Validation error display
    - Duplicate detection warnings
  - **TENANT CHECK**: Verify `tenant_id = 'bibbi'` in auth token before render

- [ ] **Task 10.2**: Create upload history table
  - Display: filename, vendor, upload_date, status, rows_processed, actions
  - Filters: vendor, date range, status
  - Actions: Download validation report, Retry failed, View details

- [ ] **Task 10.3**: Create upload detail view
  - Show: Processing stages with timestamps
  - Show: Validation errors grouped by type
  - Show: Store records created
  - Show: Product mapping issues
  - Download: Original file, Error report, Processed data summary

#### 🔲 Store Management Interface
- [ ] **Task 10.4**: Create store management page
  - Location: `frontend/src/pages/BibbıStores.tsx`
  - Display: All stores for bibbi tenant
  - Grouping: By reseller
  - Features: Edit store metadata, Merge duplicate stores, Deactivate stores

#### 🔲 Product Mapping Interface
- [ ] **Task 10.5**: Create product mapping page
  - Location: `frontend/src/pages/BibbıProductMappings.tsx`
  - Display: Unmapped products requiring attention
  - Features: Manual EAN assignment, Bulk mapping via CSV import
  - **REQUIRES**: Business owner to map products

---

### PHASE 11: Testing & Validation (Days 16-17)

#### 🔲 Unit Tests
- [ ] **Task 11.1**: Test vendor processors
  - Test file: `backend/tests/test_bibbi_processors.py`
  - Test each processor with sample files
  - Assert: Correct schema mapping
  - Assert: Store extraction working
  - Assert: Currency conversion accurate
  - Assert: Special handling (Liberty, Galilu, Skins SA)

- [ ] **Task 11.2**: Test validation service
  - Test file: `backend/tests/test_bibbi_validation.py`
  - Test invalid data scenarios
  - Assert: Error messages accurate
  - Assert: Valid data passes

- [ ] **Task 11.3**: Test store service
  - Test file: `backend/tests/test_bibbi_store_service.py`
  - Test store auto-creation
  - Test duplicate detection
  - Test online/physical classification

- [ ] **Task 11.4**: Test tenant isolation
  - Test file: `backend/tests/test_bibbi_tenant_isolation.py`
  - Assert: Non-bibbi tenant requests rejected
  - Assert: All queries filter by tenant_id
  - Assert: No cross-tenant data leakage

#### 🔲 Integration Tests
- [ ] **Task 11.5**: End-to-end upload test
  - Test file: `backend/tests/integration/test_bibbi_upload_e2e.py`
  - Upload sample file from each vendor
  - Assert: Complete pipeline success
  - Assert: Data in sales_unified table
  - Assert: Stores created
  - Assert: Upload status updated

- [ ] **Task 11.6**: Test with all 131 sample files
  - Location: `backend/BIBBI/Resellers/*/`
  - Run batch upload script
  - Collect success/failure statistics
  - Identify common failure patterns
  - Document required product mappings

#### 🔲 Performance Testing
- [ ] **Task 11.7**: Test concurrent uploads
  - Simulate 4 simultaneous uploads
  - Assert: No race conditions
  - Assert: All uploads processed correctly
  - Measure: Processing time per file

- [ ] **Task 11.8**: Test large file handling
  - Test with files >10,000 rows
  - Assert: Memory usage acceptable
  - Assert: Processing completes within timeout
  - Measure: Rows processed per second

---

### PHASE 12: Deployment & Documentation (Day 18)

#### 🔲 Deployment Preparation
- [ ] **Task 12.1**: Create deployment checklist
  - Verify: All environment variables set
  - Verify: Database migrations applied
  - Verify: Celery workers running
  - Verify: Redis accessible
  - Verify: S3 bucket configured

- [ ] **Task 12.2**: Create seed data script
  - Location: `backend/db/seed_bibbi_initial_data.sql`
  - Seed: Resellers (8 resellers for bibbi tenant)
  - Seed: Initial store records (known stores)
  - Seed: Product mappings (from business owner input)
  - **REQUIRES**: Business owner to provide reseller contracts, store lists

- [ ] **Task 12.3**: Update API documentation
  - Document all BIBBI-specific endpoints
  - Add tenant isolation notes
  - Include example requests/responses

#### 🔲 User Documentation
- [ ] **Task 12.4**: Create BIBBI upload guide
  - Location: `docs/bibbi_upload_guide.md`
  - Sections:
    - How to upload files
    - Understanding validation errors
    - Managing stores
    - Mapping products
    - Interpreting reports

- [ ] **Task 12.5**: Create reseller file format guide
  - Document expected format for each reseller
  - Include sample files (anonymized)
  - Explain special handling requirements

#### 🔲 Monitoring & Logging
- [ ] **Task 12.6**: Set up logging
  - Log all tenant checks: "Tenant check passed: bibbi"
  - Log file processing stages
  - Log validation errors
  - Log store creation events
  - Use structured logging (JSON format)

- [ ] **Task 12.7**: Create monitoring dashboard
  - Metrics:
    - Uploads per day (by vendor)
    - Processing success rate
    - Average processing time
    - Validation error rate
    - Store creation rate
  - Alerts:
    - Processing failure spike
    - High validation error rate
    - Queue backlog >10 uploads

---

## 🔑 Critical Success Factors

### 1. Tenant Isolation (BIBBI ONLY)
- **Verification**: Every database query must include `tenant_id = 'bibbi'`
- **Testing**: Attempt to upload with non-bibbi tenant → Must fail with 403
- **Code Review**: Search codebase for Supabase queries without tenant filter → None allowed

### 2. Store-Level Granularity
- **Verification**: All 8 resellers correctly extract store data
- **Testing**: Upload sample file from each reseller → Verify stores table populated
- **Validation**: Store count matches expected (e.g., Liberty = 2 stores, Selfridges = 5)

### 3. Data Quality
- **Verification**: Validation service catches all invalid data
- **Testing**: Upload file with intentional errors → All caught and reported
- **Metric**: Validation error rate <5% on real data

### 4. Duplicate Prevention
- **Verification**: Living documents don't create duplicate sales records
- **Testing**: Upload same file twice → Second upload skipped or updates existing
- **Metric**: Duplicate rate <1%

### 5. Special Case Handling
- **Liberty**: No duplicate rows, returns parsed correctly
- **Galilu**: All product names mapped to EANs
- **Skins SA**: Store codes correctly parsed from Column A
- **Testing**: Sample files from these vendors must process 100% successfully

---

## 📊 Progress Tracking

### Phase Completion Checklist
- [ ] Phase 1: Core Infrastructure (2 days)
- [ ] Phase 2: File Upload & Staging (2 days)
- [ ] Phase 3: Vendor Detection (1 day)
- [ ] Phase 4: Processor Adaptation (3 days)
- [ ] Phase 5: Validation Service (1 day)
- [ ] Phase 6: Store Service (1 day)
- [ ] Phase 7: Product Mapping (1 day)
- [ ] Phase 8: Sales Insertion (1 day)
- [ ] Phase 9: Celery Integration (1 day)
- [ ] Phase 10: Frontend Dashboard (2 days)
- [ ] Phase 11: Testing (2 days)
- [ ] Phase 12: Deployment (1 day)

### Estimated Timeline: 18 working days (3.5 weeks)

---

## 🚨 Blockers & Dependencies

### Business Owner Input Required
1. **Product Mappings**: Galilu product names → EANs (Task 4.5, 7.4)
2. **Reseller Contracts**: For gross margin analysis (Task 12.2)
3. **Store Lists**: Known store names for validation (Task 12.2)
4. **COGS Data**: Cost of goods per product (future enhancement)
5. **Commission Rates**: Per reseller for margin calculation (future enhancement)

### External Dependencies
1. **Supabase**: Database must be accessible with service key
2. **Redis**: Required for Celery + caching
3. **S3/Storage**: File storage for uploads and reports
4. **Email Service**: SendGrid for notifications
5. **OpenAI**: For future AI-assisted product matching (optional)

---

## 📝 Next Steps

1. **Review this plan** with business owner and technical team
2. **Prioritize tasks** if timeline needs compression
3. **Assign developers** to phases (can parallelize Phases 4-7)
4. **Schedule business owner input sessions** for product mappings
5. **Begin Phase 1** (Core Infrastructure Setup)

---

**Document Version**: 1.0
**Created**: 2025-10-17
**Author**: Claude Code (Ultrathink Mode)
**Target Tenant**: BIBBI ONLY (tenant_id = 'bibbi')
**Database Schema**: New 15-table design with sales_unified central fact table
