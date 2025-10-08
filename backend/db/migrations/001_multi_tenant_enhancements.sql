-- ============================================
-- Migration: Multi-Tenant Enhancements
-- Description: Add tenant-aware columns and optimize for multi-tenant architecture
-- Date: 2025-10-07
-- ============================================

-- ============================================
-- ADD TENANT_ID COLUMNS (if not exists)
-- ============================================

-- Add tenant_id to users table for tenant association
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE users ADD COLUMN tenant_id UUID;
        CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);

        COMMENT ON COLUMN users.tenant_id IS 'Associates user with their tenant for multi-tenant isolation';
    END IF;
END $$;

-- Add tenant_id to resellers table for tenant-specific reseller data
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'resellers' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE resellers ADD COLUMN tenant_id UUID;
        CREATE INDEX IF NOT EXISTS idx_resellers_tenant_id ON resellers(tenant_id);

        -- Update unique constraint to be tenant-scoped
        ALTER TABLE resellers DROP CONSTRAINT IF EXISTS resellers_name_key;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_resellers_name_tenant ON resellers(name, tenant_id);

        COMMENT ON COLUMN resellers.tenant_id IS 'Tenant-scoped reseller data isolation';
    END IF;
END $$;

-- Add tenant_id to products table for tenant-specific product catalogs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE products ADD COLUMN tenant_id UUID;
        CREATE INDEX IF NOT EXISTS idx_products_tenant_id ON products(tenant_id);

        -- Update unique constraint to be tenant-scoped
        ALTER TABLE products DROP CONSTRAINT IF EXISTS products_sku_key;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_tenant ON products(sku, tenant_id);

        COMMENT ON COLUMN products.tenant_id IS 'Tenant-scoped product catalog isolation';
    END IF;
END $$;

-- ============================================
-- OPTIMIZE EXISTING INDEXES FOR MULTI-TENANT
-- ============================================

-- Composite indexes for better query performance with tenant filtering
CREATE INDEX IF NOT EXISTS idx_sellout_tenant_user_date
    ON sellout_entries2(user_id, year, month)
    WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ecommerce_tenant_user_date
    ON ecommerce_orders(user_id, order_date)
    WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_conversation_tenant_session
    ON conversation_history(user_id, session_id, timestamp)
    WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_dashboard_tenant_active
    ON dashboard_configs(user_id, is_active)
    WHERE user_id IS NOT NULL;

-- ============================================
-- ENHANCED RLS POLICIES FOR TENANT ISOLATION
-- ============================================

-- Drop and recreate users table RLS if tenant_id column exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'tenant_id'
    ) THEN
        -- Enable RLS on users table
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;

        -- Users can only see other users in their tenant
        DROP POLICY IF EXISTS "Users can read tenant users" ON users;
        CREATE POLICY "Users can read tenant users"
            ON users FOR SELECT
            TO authenticated
            USING (tenant_id = (SELECT tenant_id FROM users WHERE user_id = auth.uid()));

        -- Users can only update their own record
        DROP POLICY IF EXISTS "Users can update own record" ON users;
        CREATE POLICY "Users can update own record"
            ON users FOR UPDATE
            TO authenticated
            USING (user_id = auth.uid());
    END IF;
END $$;

-- Enhanced RLS for resellers (tenant-scoped)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'resellers' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE resellers ENABLE ROW LEVEL SECURITY;

        DROP POLICY IF EXISTS "Users can read tenant resellers" ON resellers;
        CREATE POLICY "Users can read tenant resellers"
            ON resellers FOR SELECT
            TO authenticated
            USING (tenant_id = (SELECT tenant_id FROM users WHERE user_id = auth.uid()));

        DROP POLICY IF EXISTS "Users can create tenant resellers" ON resellers;
        CREATE POLICY "Users can create tenant resellers"
            ON resellers FOR INSERT
            TO authenticated
            WITH CHECK (tenant_id = (SELECT tenant_id FROM users WHERE user_id = auth.uid()));
    END IF;
END $$;

-- Enhanced RLS for products (tenant-scoped)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE products ENABLE ROW LEVEL SECURITY;

        DROP POLICY IF EXISTS "Users can read tenant products" ON products;
        CREATE POLICY "Users can read tenant products"
            ON products FOR SELECT
            TO authenticated
            USING (tenant_id = (SELECT tenant_id FROM users WHERE user_id = auth.uid()));

        DROP POLICY IF EXISTS "Users can create tenant products" ON products;
        CREATE POLICY "Users can create tenant products"
            ON products FOR INSERT
            TO authenticated
            WITH CHECK (tenant_id = (SELECT tenant_id FROM users WHERE user_id = auth.uid()));
    END IF;
END $$;

-- ============================================
-- ADD AUDIT COLUMNS FOR COMPLIANCE
-- ============================================

-- Add updated_by tracking to critical tables
DO $$
BEGIN
    -- sellout_entries2
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sellout_entries2' AND column_name = 'updated_by'
    ) THEN
        ALTER TABLE sellout_entries2 ADD COLUMN updated_by UUID REFERENCES users(user_id);
        ALTER TABLE sellout_entries2 ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
    END IF;

    -- ecommerce_orders
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ecommerce_orders' AND column_name = 'updated_by'
    ) THEN
        ALTER TABLE ecommerce_orders ADD COLUMN updated_by UUID REFERENCES users(user_id);
        ALTER TABLE ecommerce_orders ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- ============================================
-- PERFORMANCE OPTIMIZATIONS
-- ============================================

-- Add BRIN index for time-series data (more efficient for large datasets)
CREATE INDEX IF NOT EXISTS idx_sellout_entries2_created_at_brin
    ON sellout_entries2 USING BRIN (created_at);

CREATE INDEX IF NOT EXISTS idx_ecommerce_orders_created_at_brin
    ON ecommerce_orders USING BRIN (created_at);

CREATE INDEX IF NOT EXISTS idx_upload_batches_timestamp_brin
    ON upload_batches USING BRIN (upload_timestamp);

-- Add GIN index for JSONB columns for faster queries
CREATE INDEX IF NOT EXISTS idx_error_reports_raw_data_gin
    ON error_reports USING GIN (raw_data);

CREATE INDEX IF NOT EXISTS idx_dashboard_configs_auth_config_gin
    ON dashboard_configs USING GIN (authentication_config);

-- ============================================
-- ADD CONSTRAINTS FOR DATA INTEGRITY
-- ============================================

-- Ensure is_active flag is unique per user (only one active dashboard per user)
CREATE UNIQUE INDEX IF NOT EXISTS idx_dashboard_configs_user_active
    ON dashboard_configs(user_id)
    WHERE is_active = TRUE;

-- Ensure email is lowercase for consistent lookups
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_email_lowercase_check'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_email_lowercase_check
            CHECK (email = LOWER(email));
    END IF;
END $$;

-- ============================================
-- STATISTICS AND VACUUMING
-- ============================================

-- Update statistics for query planner optimization
ANALYZE users;
ANALYZE resellers;
ANALYZE products;
ANALYZE sellout_entries2;
ANALYZE ecommerce_orders;
ANALYZE upload_batches;
ANALYZE error_reports;
ANALYZE conversation_history;
ANALYZE dashboard_configs;
ANALYZE email_logs;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Multi-tenant enhancements migration completed successfully';
    RAISE NOTICE 'Added tenant_id columns to users, resellers, products';
    RAISE NOTICE 'Enhanced indexes for multi-tenant query performance';
    RAISE NOTICE 'Updated RLS policies for tenant isolation';
    RAISE NOTICE 'Added audit columns and data integrity constraints';
END $$;
