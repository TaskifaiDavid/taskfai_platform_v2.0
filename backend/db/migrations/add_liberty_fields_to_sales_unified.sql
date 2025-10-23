-- ============================================
-- Migration: Add Liberty Required Fields to sales_unified
-- Date: 2025-01-23
-- Description:
--   1. Add missing columns: customer_id, functional_name, sales_channel, country, city
--   2. Rename product_id to product_ean for clarity
--   3. Update constraints and indexes
-- ============================================

BEGIN;

-- Step 1: Add new columns
ALTER TABLE sales_unified
    ADD COLUMN IF NOT EXISTS customer_id UUID,
    ADD COLUMN IF NOT EXISTS functional_name TEXT,
    ADD COLUMN IF NOT EXISTS sales_channel TEXT CHECK (sales_channel IN ('online', 'retail', 'B2B', 'B2C')),
    ADD COLUMN IF NOT EXISTS country TEXT,
    ADD COLUMN IF NOT EXISTS city TEXT;

-- Step 2: Rename product_id to product_ean
-- Check if column exists before renaming
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sales_unified'
        AND column_name = 'product_id'
    ) THEN
        ALTER TABLE sales_unified RENAME COLUMN product_id TO product_ean;
        RAISE NOTICE 'Column product_id renamed to product_ean';
    ELSE
        RAISE NOTICE 'Column product_id not found, skipping rename';
    END IF;
END $$;

-- Step 3: Update UNIQUE constraint
-- Drop old constraint (may have different generated name in Supabase)
DO $$
BEGIN
    -- Try to drop constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name = 'sales_unified'
        AND constraint_name LIKE '%product_id%'
    ) THEN
        -- Get the actual constraint name and drop it
        EXECUTE (
            SELECT 'ALTER TABLE sales_unified DROP CONSTRAINT ' || constraint_name || ';'
            FROM information_schema.table_constraints
            WHERE table_name = 'sales_unified'
            AND constraint_name LIKE '%product_id%'
            LIMIT 1
        );
        RAISE NOTICE 'Old unique constraint dropped';
    END IF;
END $$;

-- Create new UNIQUE constraint with product_ean
ALTER TABLE sales_unified
    DROP CONSTRAINT IF EXISTS sales_unified_unique_sale;

ALTER TABLE sales_unified
    ADD CONSTRAINT sales_unified_unique_sale
    UNIQUE (tenant_id, reseller_id, product_ean, sale_date, store_id, quantity);

-- Step 4: Update indexes
-- Drop old product_id index
DROP INDEX IF EXISTS idx_sales_unified_product;

-- Create new product_ean index
CREATE INDEX IF NOT EXISTS idx_sales_unified_product_ean ON sales_unified(product_ean);

-- Add new indexes for performance
CREATE INDEX IF NOT EXISTS idx_sales_unified_functional_name ON sales_unified(functional_name);
CREATE INDEX IF NOT EXISTS idx_sales_unified_sales_channel ON sales_unified(sales_channel);
CREATE INDEX IF NOT EXISTS idx_sales_unified_country ON sales_unified(country);
CREATE INDEX IF NOT EXISTS idx_sales_unified_city ON sales_unified(city);

-- Step 5: Add column comments
COMMENT ON COLUMN sales_unified.product_ean IS 'EAN-13 barcode or temporary vendor code (prefixed with vendor name if no match)';
COMMENT ON COLUMN sales_unified.functional_name IS 'Product display name from products table, or vendor product name if no match';
COMMENT ON COLUMN sales_unified.customer_id IS 'Customer reference (NULL for B2B reseller data like Liberty, Galilu)';
COMMENT ON COLUMN sales_unified.sales_channel IS 'Sales channel: online (e-commerce), retail (physical store), B2B, B2C';
COMMENT ON COLUMN sales_unified.country IS 'Country of sale (e.g., UK, Poland, South Africa)';
COMMENT ON COLUMN sales_unified.city IS 'City of sale (e.g., London, Warsaw) or "online" for e-commerce';

COMMIT;

-- Verification queries (run after migration)
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'sales_unified'
-- AND column_name IN ('product_ean', 'functional_name', 'customer_id', 'sales_channel', 'country', 'city')
-- ORDER BY column_name;
