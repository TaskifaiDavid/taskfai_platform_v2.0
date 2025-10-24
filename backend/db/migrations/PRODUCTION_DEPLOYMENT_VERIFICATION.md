# Production Deployment Verification - Liberty Fix (T038)

## What Was Fixed

### Database Migration (APPLIED ✅)
**Migration**: `rename_product_id_to_product_ean_final`
**Applied to**: BIBBI Supabase (edckqdrbgtnnjfnshjfq.supabase.co)
**Date**: 2025-01-24

**Changes**:
- ✅ Renamed `product_id` → `product_ean`
- ✅ Deleted 1 duplicate record
- ✅ Created new unique constraint on (reseller_id, product_ean, sale_date, store_id, quantity)
- ✅ Created indexes: product_ean, functional_name, sales_channel, country, city
- ✅ Added column comments for documentation

### Code Changes (DEPLOYED ✅)
**Commit**: `58ba89b` - "fix: correct resellers table query column name (T038)"
**PR**: #36 - feature/liberty-multi-store-detection

**Changes**:
- ✅ Fixed resellers table query: `.eq("reseller_id", ...)` → `.eq("id", ...)`
- ✅ Prevents "column resellers.reseller_id does not exist" error

---

## Production Verification Steps

### Step 1: Verify Database Schema

```sql
-- Connect to BIBBI Supabase: edckqdrbgtnnjfnshjfq.supabase.co
-- Execute in SQL Editor:

-- Verify product_ean column exists (not product_id)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'sales_unified'
AND column_name IN ('product_id', 'product_ean', 'functional_name', 'sales_channel', 'country', 'city')
ORDER BY column_name;
```

**Expected Result**:
```
column_name      | data_type           | is_nullable
-----------------+---------------------+-------------
city             | character varying   | YES
country          | character varying   | YES
customer_id      | uuid                | YES
functional_name  | character varying   | YES
product_ean      | text                | NO          ← RENAMED from product_id
sales_channel    | character varying   | YES
```

**❌ If you see `product_id`**: Migration NOT applied (will cause insert failures)
**✅ If you see `product_ean`**: Migration applied correctly

---

### Step 2: Deploy Latest Code

**Backend Deployment**:
```bash
# Pull latest changes (includes commit 58ba89b)
git fetch origin
git checkout feature/liberty-multi-store-detection
git pull origin feature/liberty-multi-store-detection

# Restart backend service (adjust for your deployment method)
# Example for systemd:
sudo systemctl restart taskifai-backend

# Example for Docker:
docker-compose restart backend worker

# Example for DigitalOcean App Platform:
# Trigger deployment from dashboard or via doctl CLI
```

**Verify Backend Running**:
```bash
# Check backend health
curl -s https://your-backend-url.com/health

# Check logs for startup errors
# Systemd:
sudo journalctl -u taskifai-backend -f

# Docker:
docker-compose logs -f backend

# DigitalOcean:
doctl apps logs <app-id> --component backend
```

---

### Step 3: Test Liberty Upload

**Manual Upload Test**:
1. Navigate to production UI (demo.taskifai.com or bibbi.taskifai.com)
2. Upload a Liberty Excel file
3. Monitor Celery worker logs

**Expected Logs** (SUCCESS):
```
[Liberty] Starting processing: /tmp/uploads/liberty_file.xlsx
[Liberty] Extracted 2 stores
[Liberty] Extracted 45 rows
[Liberty] Processing complete: 45 success, 0 failed
[BibbιValidation] Validating 45 rows...
[BibbιValidation] Validation complete: 45 valid, 0 invalid
[BibbιSalesInsertion] Inserting 45 rows (batch size: 1000)...
[BibbιSalesInsertion] Batch insert complete: 45 inserted, 0 duplicates, 0 failed
```

**❌ OLD ERRORS (before fix)**:
```
[BibbιSalesInsertion] Batch insert failed:
{'message': "Could not find the 'product_ean' column of 'sales_unified' in the schema cache", 'code': 'PGRST204'}
[BibbiProcessor] Error fetching reseller details: {'message': 'column resellers.reseller_id does not exist', 'code': '42703'}
Result: 0/45 records inserted
```

**✅ NEW SUCCESS (after fix)**:
```
Result: 45/45 records inserted
Upload status: completed
```

---

### Step 4: Verify Data Quality

```sql
-- Connect to BIBBI Supabase
-- Get Liberty reseller_id first
SELECT id, reseller FROM resellers WHERE LOWER(reseller) LIKE '%liberty%';

-- Verify recent Liberty upload (replace <reseller_id> with actual ID)
SELECT
    product_ean,           -- ✅ Should have EAN codes or TEMP_LIBERTY_* identifiers
    functional_name,       -- ✅ Should have product names (not NULL)
    customer_id,           -- ✅ Should be NULL (B2B reseller data)
    sales_channel,         -- ✅ Should be 'online' or 'retail' (not NULL)
    country,               -- ✅ Should be 'UK' (not NULL)
    city,                  -- ✅ Should be 'London' or 'online' (not NULL)
    upload_id,             -- ✅ Should have UUID (not NULL)
    sale_date,
    quantity,
    sales_eur
FROM sales_unified
WHERE reseller_id = '<reseller_id>'
ORDER BY created_at DESC
LIMIT 10;
```

**Expected Data Quality**:
- ✅ `product_ean`: Valid EAN-13 codes OR `TEMP_LIBERTY_{product_name}_{hash}`
- ✅ `functional_name`: Product display names (e.g., "TROISIEME 10ML")
- ✅ `customer_id`: ALL NULL (Liberty is B2B)
- ✅ `sales_channel`: "online" OR "retail" (no NULLs)
- ✅ `country`: "UK" (no NULLs)
- ✅ `city`: "London" OR "online" (no NULLs)
- ✅ `upload_id`: Valid UUIDs (no NULLs)

---

### Step 5: Monitor for Errors

**Watch Celery Worker Logs**:
```bash
# Look for these error patterns (should NOT appear):
grep -i "Could not find the 'product_ean' column" /var/log/celery-worker.log
grep -i "column resellers.reseller_id does not exist" /var/log/celery-worker.log
grep -i "SyncClient.*attribute.*client" /var/log/celery-worker.log

# If any errors found, check:
# 1. Database migration applied? (Step 1)
# 2. Latest code deployed? (Step 2)
# 3. Backend restarted? (Step 2)
```

---

## Success Criteria

All must be TRUE:

- [ ] Database schema has `product_ean` column (not `product_id`)
- [ ] Latest code deployed (commit `58ba89b` or later)
- [ ] Backend service restarted successfully
- [ ] Liberty file uploads complete without errors
- [ ] Insert success rate: 100% (45/45 records, not 0/45)
- [ ] Data quality checks pass (all required fields populated)
- [ ] No "product_ean column not found" errors in logs
- [ ] No "reseller_id does not exist" errors in logs

---

## Rollback Plan (If Needed)

**If critical issues occur**:

### Database Rollback
```sql
BEGIN;

-- Rename product_ean back to product_id
ALTER TABLE sales_unified RENAME COLUMN product_ean TO product_id;

-- Drop new constraint
ALTER TABLE sales_unified DROP CONSTRAINT IF EXISTS sales_unified_unique_sale;

-- Recreate old constraint
ALTER TABLE sales_unified
    ADD CONSTRAINT sales_unified_product_id_reseller_id_store_id_sale_date_ord_key
    UNIQUE (reseller_id, product_id, sale_date, store_id, quantity);

-- Update indexes
DROP INDEX IF EXISTS idx_sales_unified_product_ean;
CREATE INDEX IF NOT EXISTS idx_sales_unified_product ON sales_unified(product_id);

COMMIT;
```

### Code Rollback
```bash
# Revert to previous commit
git revert 58ba89b
git push origin feature/liberty-multi-store-detection

# Restart backend
sudo systemctl restart taskifai-backend  # or your deployment method
```

---

## Contact

For issues or questions:
- Check Supabase SQL Editor logs
- Review Celery worker logs for processor errors
- Verify products.liberty_name has proper product mappings
- Check stores table has Liberty stores configured (flagship, internet)

## Status

**Database Migration**: ✅ APPLIED (2025-01-24)
**Code Deployment**: ✅ READY (commit 58ba89b)
**Verification**: ⏳ PENDING (follow steps above)
