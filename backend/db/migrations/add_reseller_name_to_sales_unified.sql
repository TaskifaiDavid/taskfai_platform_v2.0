-- ==================================================
-- Add reseller_name to sales_unified (Denormalization)
-- ==================================================
-- Purpose: Enable AI to understand reseller names in natural language queries
-- Example: "Show me Liberty's sales" now works without complex JOINs
-- Created: 2025-10-31
-- Tenant: bibbi (affects sales_unified table)
-- ==================================================

-- Step 1: Add reseller_name column to sales_unified
-- This denormalizes the reseller name for faster queries and better AI understanding
ALTER TABLE sales_unified
ADD COLUMN IF NOT EXISTS reseller_name TEXT;

COMMENT ON COLUMN sales_unified.reseller_name IS 'Denormalized reseller name for AI queries. Populated from resellers.name during upload.';

-- Step 2: Backfill existing data from resellers table
-- Updates all existing sales_unified records with reseller names
-- NOTE: BIBBI resellers table uses 'id' (not 'reseller_id') and 'reseller' (not 'name')
UPDATE sales_unified s
SET reseller_name = r.reseller
FROM resellers r
WHERE s.reseller_id = r.id
  AND s.reseller_name IS NULL;

-- Step 3: Create index for performance
-- Enables fast filtering by reseller name in AI queries
CREATE INDEX IF NOT EXISTS idx_sales_unified_reseller_name
ON sales_unified(reseller_name);

-- Step 4: Optional - Add NOT NULL constraint for data integrity
-- Uncomment if you want to enforce that all records must have reseller_name
-- ALTER TABLE sales_unified
-- ALTER COLUMN reseller_name SET NOT NULL;

-- ==================================================
-- Verification Query
-- ==================================================
-- Run this to verify the migration worked correctly
SELECT
    reseller_name,
    COUNT(*) as record_count,
    MIN(sale_date) as earliest_sale,
    MAX(sale_date) as latest_sale,
    SUM(sales_eur) as total_revenue
FROM sales_unified
WHERE reseller_name IS NOT NULL
GROUP BY reseller_name
ORDER BY record_count DESC;

-- Expected output: Should show Liberty and any other resellers with data
