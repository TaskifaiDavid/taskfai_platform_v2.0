-- ============================================
-- Migration: Fix Liberty sales_channel Values
-- Date: 2025-10-23
-- Description:
--   Update existing Liberty records to use correct sales_channel value.
--
--   Before: sales_channel = "online" or "retail" (distribution channel)
--   After:  sales_channel = "B2B" (business model from resellers table)
--
--   Background:
--   The Liberty processor was incorrectly overriding sales_channel with
--   store type ("online"/"retail") instead of using the reseller's
--   business model ("B2B"). This migration corrects existing data.
-- ============================================

BEGIN;

-- Step 1: Identify Liberty reseller ID(s)
-- This query will show all Liberty resellers
-- SELECT reseller_id, reseller, sales_channel
-- FROM resellers
-- WHERE LOWER(reseller) LIKE '%liberty%';

-- Step 2: Update sales_channel for all Liberty records
-- Change from "online"/"retail" to "B2B"
UPDATE sales_unified
SET sales_channel = 'B2B'
WHERE reseller_id IN (
    SELECT reseller_id
    FROM resellers
    WHERE LOWER(reseller) LIKE '%liberty%'
)
AND sales_channel IN ('online', 'retail');

-- Step 3: Verify the update
-- This should return 0 rows after migration
-- SELECT COUNT(*) as remaining_incorrect_records
-- FROM sales_unified su
-- JOIN resellers r ON su.reseller_id = r.reseller_id
-- WHERE LOWER(r.reseller) LIKE '%liberty%'
-- AND su.sales_channel IN ('online', 'retail');

-- Step 4: Verify correct values
-- This should show all Liberty records have sales_channel='B2B'
-- SELECT
--     sales_channel,
--     COUNT(*) as record_count,
--     MIN(sale_date) as earliest_sale,
--     MAX(sale_date) as latest_sale
-- FROM sales_unified su
-- JOIN resellers r ON su.reseller_id = r.reseller_id
-- WHERE LOWER(r.reseller) LIKE '%liberty%'
-- GROUP BY sales_channel;

COMMIT;

-- Rollback Plan (if needed):
-- If you need to revert this migration, you can restore the original
-- values by matching store_identifier:
--
-- BEGIN;
-- UPDATE sales_unified
-- SET sales_channel = CASE
--     WHEN store_identifier IN ('online', 'internet') THEN 'online'
--     ELSE 'retail'
-- END
-- WHERE reseller_id IN (
--     SELECT reseller_id FROM resellers WHERE LOWER(reseller) LIKE '%liberty%'
-- );
-- COMMIT;
