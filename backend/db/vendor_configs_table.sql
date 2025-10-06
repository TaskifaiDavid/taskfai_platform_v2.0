-- ============================================
-- TaskifAI - Vendor Configurations Table
-- Configuration-driven vendor processing
-- ============================================

-- This table should be created in EACH tenant database

CREATE TABLE IF NOT EXISTS vendor_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Tenant identification (NULL for system defaults)
    tenant_id UUID,  -- NULL = system default config

    -- Vendor identification
    vendor_name VARCHAR(100) NOT NULL,

    -- Configuration data (JSONB for flexibility)
    config_data JSONB NOT NULL,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,  -- True for system defaults

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- User who created/modified
    created_by UUID,  -- References users(user_id)

    -- Constraints: One active config per vendor per tenant
    UNIQUE(tenant_id, vendor_name, is_active) WHERE is_active = TRUE
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_vendor_configs_tenant ON vendor_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vendor_configs_vendor ON vendor_configs(vendor_name);
CREATE INDEX IF NOT EXISTS idx_vendor_configs_active ON vendor_configs(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_vendor_configs_default ON vendor_configs(is_default) WHERE is_default = TRUE;

-- GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_vendor_configs_data ON vendor_configs USING GIN (config_data);

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_vendor_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_vendor_configs_updated_at
    BEFORE UPDATE ON vendor_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_vendor_config_timestamp();

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to get active config for a vendor
CREATE OR REPLACE FUNCTION get_vendor_config(
    p_tenant_id UUID,
    p_vendor_name VARCHAR
) RETURNS JSONB AS $$
DECLARE
    v_config JSONB;
BEGIN
    -- Try to get tenant-specific config first
    SELECT config_data INTO v_config
    FROM vendor_configs
    WHERE tenant_id = p_tenant_id
      AND vendor_name = p_vendor_name
      AND is_active = TRUE
    LIMIT 1;

    -- If not found, get system default
    IF v_config IS NULL THEN
        SELECT config_data INTO v_config
        FROM vendor_configs
        WHERE tenant_id IS NULL
          AND vendor_name = p_vendor_name
          AND is_default = TRUE
        LIMIT 1;
    END IF;

    RETURN v_config;
END;
$$ LANGUAGE plpgsql;

-- Function to list all vendors with their configs
CREATE OR REPLACE FUNCTION list_vendor_configs(p_tenant_id UUID)
RETURNS TABLE (
    vendor_name VARCHAR,
    config_data JSONB,
    is_custom BOOLEAN,
    source VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(tc.vendor_name, dc.vendor_name) as vendor_name,
        COALESCE(tc.config_data, dc.config_data) as config_data,
        (tc.config_id IS NOT NULL) as is_custom,
        CASE
            WHEN tc.config_id IS NOT NULL THEN 'tenant_override'
            ELSE 'system_default'
        END as source
    FROM
        (SELECT DISTINCT vendor_name FROM vendor_configs WHERE is_default = TRUE) vendors
    LEFT JOIN
        vendor_configs tc ON vendors.vendor_name = tc.vendor_name
            AND tc.tenant_id = p_tenant_id
            AND tc.is_active = TRUE
    LEFT JOIN
        vendor_configs dc ON vendors.vendor_name = dc.vendor_name
            AND dc.tenant_id IS NULL
            AND dc.is_default = TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VIEWS
-- ============================================

-- Active configurations view
CREATE OR REPLACE VIEW active_vendor_configs AS
SELECT
    config_id,
    tenant_id,
    vendor_name,
    config_data,
    is_active,
    is_default,
    CASE
        WHEN tenant_id IS NOT NULL THEN 'tenant_override'
        ELSE 'system_default'
    END as source,
    created_at,
    updated_at
FROM vendor_configs
WHERE is_active = TRUE
ORDER BY vendor_name, tenant_id NULLS FIRST;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE vendor_configs IS 'Configuration-driven vendor processing rules';
COMMENT ON COLUMN vendor_configs.tenant_id IS 'NULL for system defaults, UUID for tenant overrides';
COMMENT ON COLUMN vendor_configs.config_data IS 'JSONB containing vendor processing configuration';
COMMENT ON COLUMN vendor_configs.is_default IS 'True for system-provided default configurations';

-- ============================================
-- COMPLETED
-- ============================================
