-- ============================================
-- Migration: Remove quantity > 0 constraint from sales_unified
-- Date: 2025-01-27
-- Description:
--   Allow negative quantities and negative prices for return transactions
--   Standard accounting practice: returns = negative values
-- ============================================

BEGIN;

-- Step 1: Drop CHECK constraints on quantity column
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Find and drop any CHECK constraint involving quantity column
    FOR r IN (
        SELECT DISTINCT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_name = 'sales_unified'
        AND tc.constraint_type = 'CHECK'
        AND ccu.column_name = 'quantity'
    ) LOOP
        EXECUTE 'ALTER TABLE sales_unified DROP CONSTRAINT IF EXISTS ' || r.constraint_name || ' CASCADE;';
        RAISE NOTICE 'Dropped CHECK constraint: %', r.constraint_name;
    END LOOP;

    -- Also try common constraint names
    BEGIN
        ALTER TABLE sales_unified DROP CONSTRAINT IF EXISTS quantity_positive CASCADE;
        RAISE NOTICE 'Dropped constraint: quantity_positive';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Constraint quantity_positive does not exist';
    END;

    BEGIN
        ALTER TABLE sales_unified DROP CONSTRAINT IF EXISTS sales_unified_quantity_check CASCADE;
        RAISE NOTICE 'Dropped constraint: sales_unified_quantity_check';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Constraint sales_unified_quantity_check does not exist';
    END;
END $$;

-- Step 2: Drop any triggers that validate quantity
DROP TRIGGER IF EXISTS validate_quantity_positive ON sales_unified CASCADE;
DROP TRIGGER IF EXISTS check_quantity_positive ON sales_unified CASCADE;
DROP TRIGGER IF EXISTS enforce_positive_quantity ON sales_unified CASCADE;
DROP TRIGGER IF EXISTS validate_sales_record ON sales_unified CASCADE;

-- Step 3: Drop validation functions (if they exist)
DROP FUNCTION IF EXISTS validate_quantity_positive() CASCADE;
DROP FUNCTION IF EXISTS check_quantity_value() CASCADE;
DROP FUNCTION IF EXISTS enforce_positive_quantity() CASCADE;
DROP FUNCTION IF EXISTS validate_sales_quantity() CASCADE;

-- Step 4: Verification - Show remaining constraints on sales_unified
DO $$
DECLARE
    constraint_record RECORD;
    constraint_count INTEGER := 0;
BEGIN
    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Remaining constraints on sales_unified:';
    RAISE NOTICE '==========================================';

    FOR constraint_record IN (
        SELECT
            constraint_name,
            constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'sales_unified'
        ORDER BY constraint_type, constraint_name
    ) LOOP
        RAISE NOTICE '% - %', constraint_record.constraint_type, constraint_record.constraint_name;
        constraint_count := constraint_count + 1;
    END LOOP;

    IF constraint_count = 0 THEN
        RAISE NOTICE 'No constraints found (besides built-in constraints)';
    END IF;

    RAISE NOTICE '==========================================';
    RAISE NOTICE 'Total constraints: %', constraint_count;
    RAISE NOTICE '==========================================';
END $$;

-- Step 5: Add documentation comment
COMMENT ON COLUMN sales_unified.quantity IS 'Quantity sold (positive) or returned (negative). Negative values indicate return transactions.';
COMMENT ON COLUMN sales_unified.sales_eur IS 'Sales amount in EUR. Negative values indicate refunds for returns.';

COMMIT;

-- ============================================
-- Post-migration verification queries
-- ============================================
-- Run these after migration to verify:
--
-- 1. Check for any remaining quantity constraints:
-- SELECT constraint_name, constraint_type, check_clause
-- FROM information_schema.check_constraints cc
-- JOIN information_schema.table_constraints tc USING (constraint_name)
-- WHERE tc.table_name = 'sales_unified' AND check_clause LIKE '%quantity%';
--
-- 2. Test inserting a return transaction:
-- INSERT INTO sales_unified (
--     reseller_id, product_ean, store_id, upload_id,
--     sale_date, quantity, sales_eur, sales_local_currency, currency,
--     year, month, quarter, sales_channel
-- ) VALUES (
--     '14b2a64e-013b-4c2d-9c42-379699b5823d',
--     '5060697920939',
--     'cde4fe95-1955-43fb-afdf-726160583aa1',
--     (SELECT id FROM uploads ORDER BY uploaded_at DESC LIMIT 1),
--     '2025-09-21',
--     -1,           -- Negative quantity = return
--     -240.00,      -- Negative price = refund
--     -240.00,
--     'GBP',
--     2025, 9, 3,
--     'B2B'
-- );
--
-- 3. Verify the insert succeeded:
-- SELECT quantity, sales_eur, product_ean, sale_date
-- FROM sales_unified
-- WHERE quantity < 0
-- ORDER BY created_at DESC
-- LIMIT 5;
