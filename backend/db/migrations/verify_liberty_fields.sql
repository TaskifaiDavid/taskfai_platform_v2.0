-- ============================================
-- Verification Script: Liberty Sales Data Quality
-- Run this after applying migration and uploading a Liberty file
-- ============================================

-- 1. Verify schema changes were applied
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'sales_unified'
AND column_name IN ('product_ean', 'functional_name', 'customer_id', 'sales_channel', 'country', 'city', 'upload_batch_id')
ORDER BY column_name;

-- Expected output:
-- city              | text    | YES
-- country           | text    | YES
-- customer_id       | uuid    | YES
-- functional_name   | text    | YES
-- product_ean       | text    | NO
-- sales_channel     | text    | YES
-- upload_batch_id   | uuid    | NO

-- 2. Verify constraints and indexes
SELECT
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'sales_unified'
AND constraint_name LIKE '%product%'
ORDER BY constraint_name;

-- Expected: sales_unified_unique_sale with product_ean

SELECT indexname
FROM pg_indexes
WHERE tablename = 'sales_unified'
AND indexname LIKE '%product%';

-- Expected: idx_sales_unified_product_ean

-- 3. Get Liberty reseller_id for testing
SELECT reseller_id, reseller, sales_channel, country
FROM resellers
WHERE LOWER(reseller) LIKE '%liberty%';

-- Save the reseller_id for next queries

-- 4. Verify Liberty data after upload (REPLACE <liberty_reseller_id>)
SELECT
    sale_id,
    product_ean,           -- Should have EAN or TEMP_LIBERTY_* value
    functional_name,       -- Should have product name
    customer_id,           -- Should be NULL (B2B)
    sales_channel,         -- Should be 'online' or 'retail'
    country,               -- Should be 'UK'
    city,                  -- Should be 'London' or 'online'
    upload_batch_id,       -- Should have UUID
    store_identifier,      -- Should be 'flagship' or 'internet'
    quantity,
    sales_eur,
    sale_date,
    created_at
FROM sales_unified
WHERE reseller_id = '<liberty_reseller_id>'  -- Replace with actual UUID
ORDER BY created_at DESC
LIMIT 10;

-- 5. Data quality checks
-- Count records by sales_channel
SELECT
    sales_channel,
    COUNT(*) as record_count,
    COUNT(DISTINCT product_ean) as unique_products,
    SUM(sales_eur) as total_sales_eur
FROM sales_unified
WHERE reseller_id = '<liberty_reseller_id>'  -- Replace with actual UUID
GROUP BY sales_channel;

-- Expected: online and retail channels

-- 6. Verify geography data completeness
SELECT
    country,
    city,
    sales_channel,
    COUNT(*) as records
FROM sales_unified
WHERE reseller_id = '<liberty_reseller_id>'  -- Replace with actual UUID
GROUP BY country, city, sales_channel
ORDER BY records DESC;

-- Expected: All records should have country='UK', city='London'/'online'

-- 7. Check for NULL values that shouldn't be NULL
SELECT
    COUNT(*) FILTER (WHERE product_ean IS NULL) as null_product_ean,
    COUNT(*) FILTER (WHERE functional_name IS NULL) as null_functional_name,
    COUNT(*) FILTER (WHERE sales_channel IS NULL) as null_sales_channel,
    COUNT(*) FILTER (WHERE country IS NULL) as null_country,
    COUNT(*) FILTER (WHERE city IS NULL) as null_city,
    COUNT(*) FILTER (WHERE upload_batch_id IS NULL) as null_upload_batch_id,
    COUNT(*) FILTER (WHERE customer_id IS NOT NULL) as non_null_customer_id,  -- Should be 0
    COUNT(*) as total_records
FROM sales_unified
WHERE reseller_id = '<liberty_reseller_id>';  -- Replace with actual UUID

-- Expected: All counts should be 0 except total_records

-- 8. Sample records for manual inspection
SELECT
    product_ean,
    functional_name,
    CASE
        WHEN product_ean LIKE 'TEMP_LIBERTY_%' THEN 'Temporary EAN (no match found)'
        ELSE 'Real EAN (matched in products)'
    END as ean_status,
    sales_channel,
    country,
    city,
    quantity,
    sales_eur
FROM sales_unified
WHERE reseller_id = '<liberty_reseller_id>'  -- Replace with actual UUID
ORDER BY created_at DESC
LIMIT 20;

-- ============================================
-- SUCCESS CRITERIA
-- ============================================
-- ✅ All 7 fields exist in schema
-- ✅ product_ean: Contains EAN or TEMP_LIBERTY_* values (no NULLs)
-- ✅ functional_name: Contains product names (no NULLs)
-- ✅ customer_id: All NULL for Liberty B2B data
-- ✅ sales_channel: 'online' or 'retail' (no NULLs)
-- ✅ country: 'UK' (no NULLs)
-- ✅ city: 'London' or 'online' (no NULLs)
-- ✅ upload_batch_id: Valid UUIDs (no NULLs)
-- ============================================
