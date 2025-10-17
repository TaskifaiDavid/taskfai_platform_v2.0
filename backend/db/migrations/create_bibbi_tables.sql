-- ==================================================
-- BIBBI Multi-Reseller System Tables
-- ==================================================
-- Created: 2025-10-17
-- Tenant: bibbi ONLY (tenant_id = 'bibbi')
-- Purpose: Complete schema for 8-reseller Excel data processing
-- ==================================================

-- 1. STORES TABLE
-- Auto-creation of store records from reseller data
CREATE TABLE IF NOT EXISTS stores (
    store_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'bibbi',
    reseller_id UUID NOT NULL,
    store_identifier TEXT NOT NULL,  -- Reseller's internal store code
    store_name TEXT,
    store_type TEXT CHECK (store_type IN ('physical', 'online')),
    country TEXT,
    city TEXT,
    address TEXT,
    postal_code TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (tenant_id, reseller_id, store_identifier)
);

CREATE INDEX idx_stores_tenant_reseller ON stores(tenant_id, reseller_id);
CREATE INDEX idx_stores_active ON stores(is_active) WHERE is_active = true;

-- 2. PRODUCT_RESELLER_MAPPINGS TABLE
-- For resellers like Galilu that use product names instead of EANs
CREATE TABLE IF NOT EXISTS product_reseller_mappings (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'bibbi',
    reseller_id UUID NOT NULL,
    reseller_product_code TEXT NOT NULL,  -- Reseller's product name/code
    product_id TEXT NOT NULL,  -- EAN-13 code
    product_name TEXT,
    category TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    UNIQUE (tenant_id, reseller_id, reseller_product_code)
);

CREATE INDEX idx_product_mappings_tenant_reseller ON product_reseller_mappings(tenant_id, reseller_id);
CREATE INDEX idx_product_mappings_ean ON product_reseller_mappings(product_id);
CREATE INDEX idx_product_mappings_active ON product_reseller_mappings(is_active) WHERE is_active = true;

-- 3. SALES_STAGING TABLE
-- Raw upload metadata and validation tracking
CREATE TABLE IF NOT EXISTS sales_staging (
    staging_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'bibbi',
    upload_id UUID NOT NULL,
    upload_batch_id UUID NOT NULL,
    file_path TEXT NOT NULL,
    file_metadata JSONB,  -- {sheets: [...], total_sheets: N, headers: {...}}

    -- Vendor detection
    detected_vendor TEXT,
    detection_confidence DECIMAL(3, 2),
    detection_metadata JSONB,

    -- Processing status
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN
        ('pending', 'detecting', 'routing', 'processing', 'validating',
         'validated', 'inserting', 'completed', 'failed')),

    -- Validation results
    validation_status TEXT CHECK (validation_status IN
        ('pending', 'validated', 'validation_failed')),
    validation_errors JSONB,
    validated_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,

    FOREIGN KEY (upload_batch_id) REFERENCES upload_batches(upload_batch_id)
);

CREATE INDEX idx_sales_staging_tenant ON sales_staging(tenant_id);
CREATE INDEX idx_sales_staging_upload ON sales_staging(upload_id);
CREATE INDEX idx_sales_staging_status ON sales_staging(processing_status);

-- 4. SALES_UNIFIED TABLE
-- Central fact table for all reseller sales
CREATE TABLE IF NOT EXISTS sales_unified (
    sale_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'bibbi',

    -- Core identifiers
    reseller_id UUID NOT NULL,
    product_id TEXT NOT NULL,  -- EAN-13
    store_id UUID,
    upload_batch_id UUID NOT NULL,

    -- Sales data
    sale_date DATE NOT NULL,
    quantity INTEGER NOT NULL,
    sales_local_currency DECIMAL(10, 2),
    local_currency TEXT,
    sales_eur DECIMAL(10, 2) NOT NULL,

    -- Time dimensions
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    quarter INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),

    -- Metadata
    store_identifier TEXT,  -- Original store code from file
    transaction_type TEXT CHECK (transaction_type IN ('sale', 'return')),
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (reseller_id) REFERENCES resellers(reseller_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (upload_batch_id) REFERENCES upload_batches(upload_batch_id),

    -- Duplicate prevention: Same product, date, quantity, store from same reseller
    UNIQUE (tenant_id, reseller_id, product_id, sale_date, store_id, quantity)
);

CREATE INDEX idx_sales_unified_tenant ON sales_unified(tenant_id);
CREATE INDEX idx_sales_unified_reseller ON sales_unified(reseller_id);
CREATE INDEX idx_sales_unified_product ON sales_unified(product_id);
CREATE INDEX idx_sales_unified_store ON sales_unified(store_id);
CREATE INDEX idx_sales_unified_date ON sales_unified(sale_date);
CREATE INDEX idx_sales_unified_batch ON sales_unified(upload_batch_id);
CREATE INDEX idx_sales_unified_year_month ON sales_unified(year, month);

-- 5. UPDATE UPLOAD_BATCHES TABLE
-- Add BIBBI-specific columns if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'reseller_id') THEN
        ALTER TABLE upload_batches ADD COLUMN reseller_id UUID;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'vendor_name') THEN
        ALTER TABLE upload_batches ADD COLUMN vendor_name TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'total_rows') THEN
        ALTER TABLE upload_batches ADD COLUMN total_rows INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'processed_rows') THEN
        ALTER TABLE upload_batches ADD COLUMN processed_rows INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'failed_rows') THEN
        ALTER TABLE upload_batches ADD COLUMN failed_rows INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'duplicated_rows') THEN
        ALTER TABLE upload_batches ADD COLUMN duplicated_rows INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'processing_errors') THEN
        ALTER TABLE upload_batches ADD COLUMN processing_errors JSONB;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'processing_started_at') THEN
        ALTER TABLE upload_batches ADD COLUMN processing_started_at TIMESTAMP;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'upload_batches' AND column_name = 'processing_completed_at') THEN
        ALTER TABLE upload_batches ADD COLUMN processing_completed_at TIMESTAMP;
    END IF;
END $$;

-- ==================================================
-- Row-Level Security (RLS) Policies
-- ==================================================

-- Enable RLS on all tables
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_reseller_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_staging ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_unified ENABLE ROW LEVEL SECURITY;

-- Stores policies
CREATE POLICY stores_tenant_isolation ON stores
    FOR ALL
    USING (tenant_id = 'bibbi');

-- Product mappings policies
CREATE POLICY product_mappings_tenant_isolation ON product_reseller_mappings
    FOR ALL
    USING (tenant_id = 'bibbi');

-- Sales staging policies
CREATE POLICY sales_staging_tenant_isolation ON sales_staging
    FOR ALL
    USING (tenant_id = 'bibbi');

-- Sales unified policies
CREATE POLICY sales_unified_tenant_isolation ON sales_unified
    FOR ALL
    USING (tenant_id = 'bibbi');

-- ==================================================
-- Grant permissions to service role
-- ==================================================

GRANT ALL ON stores TO service_role;
GRANT ALL ON product_reseller_mappings TO service_role;
GRANT ALL ON sales_staging TO service_role;
GRANT ALL ON sales_unified TO service_role;

-- ==================================================
-- Verification
-- ==================================================

SELECT 'BIBBI tables created successfully!' AS status;
SELECT table_name,
       (SELECT COUNT(*) FROM information_schema.columns WHERE t.table_name = columns.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('stores', 'product_reseller_mappings', 'sales_staging', 'sales_unified', 'upload_batches')
ORDER BY table_name;
