# Liberty Reseller Data Processing - Implementation Summary

## Overview
Completed comprehensive fix for Liberty reseller data processing issues. All 7 data quality problems have been resolved.

## Issues Fixed ✅

### 1. customer_id Missing
- **Solution**: Added `customer_id UUID` column to sales_unified
- **Implementation**: Liberty processor sets to NULL (B2B reseller data has no customer info)
- **File**: `liberty_processor.py:461`

### 2. product_id → product_ean (Wrong Matching Logic)
- **Solution**:
  - Renamed column `product_id` to `product_ean` throughout schema
  - Fixed matching to use Liberty product NAME (not internal code)
  - Match against `products.liberty_name` column
  - Fallback to Liberty product name if no match found
- **Files**:
  - `liberty_processor.py:331-374` (matching logic)
  - All processor files updated (8 total)
  - `sales_insertion_service.py` (field filtering)

### 3. sales_channel Empty
- **Solution**: Added `sales_channel TEXT` column with CHECK constraint
- **Implementation**:
  - "online" for internet/online stores
  - "retail" for physical stores (flagship)
- **File**: `liberty_processor.py:467-474`

### 4. country Not Posting
- **Solution**: Added `country TEXT` column
- **Implementation**: Always set to "UK" for Liberty
- **File**: `liberty_processor.py:464`

### 5. city Not Posting
- **Solution**: Added `city TEXT` column
- **Implementation**:
  - "online" for internet/e-commerce sales
  - "London" for physical store sales
- **File**: `liberty_processor.py:467-474`

### 6. upload_id Not Posting
- **Solution**: Explicitly set `upload_batch_id` field
- **Implementation**: Uses batch_id parameter (which is actually upload_batch_id)
- **File**: `liberty_processor.py:479`

### 7. functional_name Wrong
- **Solution**: Added `functional_name TEXT` column
- **Implementation**:
  - Extracted from matched product via `products.functional_name`
  - Fallback to Liberty product name if no match
- **File**: `liberty_processor.py:362-367`

---

## Files Modified

### Database Migration
1. **`backend/db/migrations/add_liberty_fields_to_sales_unified.sql`** (NEW)
   - Adds 5 new columns to sales_unified
   - Renames product_id → product_ean
   - Updates constraints and indexes
   - ⚠️ **MUST BE APPLIED MANUALLY** to BIBBI Supabase

### Processor Updates
2. **`backend/app/services/bibbi/processors/liberty_processor.py`**
   - Fixed product matching logic (use NAME not code)
   - Added all missing field population
   - Changed product_id → product_ean

### Service Layer Updates
3. **`backend/app/services/bibbi/sales_insertion_service.py`**
   - Updated field filtering for new schema
   - Changed product_id → product_ean in error reporting
   - Fixed upload_batch_id handling

### Other Processor Updates
4. **All BIBBI Processors** (7 files)
   - `galilu_processor.py`
   - `boxnox_processor.py`
   - `skins_sa_processor.py`
   - `selfridges_processor.py`
   - `cdlc_processor.py`
   - `skins_nl_processor.py`
   - `aromateque_processor.py`
   - **Change**: product_id → product_ean

### Verification Tools
5. **`backend/db/migrations/verify_liberty_fields.sql`** (NEW)
   - Comprehensive verification queries
   - Data quality checks
   - Success criteria validation

---

## Deployment Steps

### Step 1: Apply Database Migration ⚠️ REQUIRED
```bash
# Option A: Via Supabase SQL Editor (Recommended)
1. Open BIBBI Supabase dashboard (edckqdrbgtnnjfnshjfq)
2. Navigate to SQL Editor
3. Copy contents of: backend/db/migrations/add_liberty_fields_to_sales_unified.sql
4. Execute migration
5. Verify success (no errors)

# Option B: Via supabase CLI
supabase db execute --db-url "postgresql://..." --file backend/db/migrations/add_liberty_fields_to_sales_unified.sql
```

### Step 2: Deploy Code Changes
```bash
# Backend deployment (example - adjust for your deployment method)
git add backend/
git commit -m "fix: Liberty reseller data processing (T038)"
git push

# Restart backend service
systemctl restart taskifai-backend  # or your deployment command
```

### Step 3: Test with Liberty File
```bash
# Upload a Liberty file via UI or API
# Then verify data using verify_liberty_fields.sql
```

---

## Verification Checklist

### Pre-Deployment
- [ ] Database migration file created
- [ ] All processor files updated (product_id → product_ean)
- [ ] Sales insertion service updated
- [ ] No syntax errors in modified files

### During Deployment
- [ ] Database migration applied successfully
- [ ] No constraint violation errors
- [ ] All indexes created
- [ ] Backend service restarted without errors

### Post-Deployment Testing
Run verification SQL:
```sql
-- Get Liberty reseller_id
SELECT reseller_id FROM resellers WHERE LOWER(reseller) LIKE '%liberty%';

-- Verify recent upload (replace <reseller_id>)
SELECT
    product_ean,           -- ✅ Should have values (no NULLs)
    functional_name,       -- ✅ Should have product names
    customer_id,           -- ✅ Should be NULL
    sales_channel,         -- ✅ Should be 'online' or 'retail'
    country,               -- ✅ Should be 'UK'
    city,                  -- ✅ Should be 'London' or 'online'
    upload_batch_id        -- ✅ Should have UUID
FROM sales_unified
WHERE reseller_id = '<reseller_id>'
ORDER BY created_at DESC
LIMIT 10;
```

**Expected Results:**
- ✅ product_ean: EAN barcodes or `TEMP_LIBERTY_{name}` (no NULLs)
- ✅ functional_name: Product display names (no NULLs)
- ✅ customer_id: ALL NULL
- ✅ sales_channel: "online" or "retail" (no NULLs)
- ✅ country: "UK" (no NULLs)
- ✅ city: "London" or "online" (no NULLs)
- ✅ upload_batch_id: Valid UUIDs (no NULLs)

---

## Technical Details

### Product Matching Flow
```
1. Extract product name from Liberty "Item" column
2. Match against products.liberty_name
   - Exact match on liberty_name column
   - Fuzzy match on product name/description
   - Auto-create with temporary EAN if no match
3. Extract product_ean from matched product
4. Extract functional_name from matched product
5. Fallback to Liberty name if no functional_name found
```

### Geography Logic
```
if store_identifier in ['online', 'internet']:
    city = 'online'
    sales_channel = 'online'
else:  # Physical stores
    city = 'London'
    sales_channel = 'retail'

country = 'UK'  # Always UK for Liberty
```

### Schema Changes
```sql
-- New columns
customer_id UUID
functional_name TEXT
sales_channel TEXT CHECK (sales_channel IN ('online', 'retail', 'B2B', 'B2C'))
country TEXT
city TEXT

-- Renamed column
product_id → product_ean

-- Updated constraints
UNIQUE (tenant_id, reseller_id, product_ean, sale_date, store_id, quantity)

-- New indexes
idx_sales_unified_product_ean
idx_sales_unified_functional_name
idx_sales_unified_sales_channel
idx_sales_unified_country
idx_sales_unified_city
```

---

## Rollback Plan (If Needed)

If issues occur after deployment:

```sql
-- Rollback migration (reverse changes)
BEGIN;

-- Rename product_ean back to product_id
ALTER TABLE sales_unified RENAME COLUMN product_ean TO product_id;

-- Drop new columns
ALTER TABLE sales_unified
    DROP COLUMN IF EXISTS customer_id,
    DROP COLUMN IF EXISTS functional_name,
    DROP COLUMN IF EXISTS sales_channel,
    DROP COLUMN IF EXISTS country,
    DROP COLUMN IF EXISTS city;

-- Restore old constraint (adjust name if needed)
ALTER TABLE sales_unified DROP CONSTRAINT sales_unified_unique_sale;
ALTER TABLE sales_unified
    ADD CONSTRAINT sales_unified_tenant_id_reseller_id_product_id_sale_date_sto_key
    UNIQUE (tenant_id, reseller_id, product_id, sale_date, store_id, quantity);

-- Restore old index
DROP INDEX idx_sales_unified_product_ean;
CREATE INDEX idx_sales_unified_product ON sales_unified(product_id);

COMMIT;
```

Then revert code changes via git:
```bash
git revert <commit_hash>
git push
```

---

## Support

For questions or issues:
1. Check verification SQL results
2. Review backend logs for processor errors
3. Verify products.liberty_name has proper mappings
4. Check stores table has Liberty stores configured

## Completion Status

✅ **All 7 issues fixed**
✅ **Database migration created**
✅ **All code updated**
✅ **Verification scripts created**
⏳ **Ready for deployment** (migration must be applied manually)
