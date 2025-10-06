-- ============================================
-- TaskifAI - Tenant Registry Schema
-- Master database for multi-tenant management
-- ============================================

-- Enable encryption extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- TENANTS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Tenant identification
    company_name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(50) UNIQUE NOT NULL,

    -- Database connection (encrypted)
    database_url TEXT NOT NULL,           -- Encrypted Supabase URL
    database_credentials TEXT NOT NULL,   -- Encrypted JSON with keys

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    suspended_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CONSTRAINT chk_subdomain_format CHECK (
        subdomain ~ '^[a-z0-9-]+$' AND
        subdomain NOT LIKE '-%' AND
        subdomain NOT LIKE '%-'
    )
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX IF NOT EXISTS idx_tenants_active ON tenants(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_tenants_created ON tenants(created_at);

-- ============================================
-- TENANT CONFIGURATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS tenant_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Configuration data
    max_file_size_mb INTEGER DEFAULT 100,
    allowed_vendors TEXT[],  -- NULL = all vendors allowed
    custom_branding JSONB,
    features_enabled JSONB DEFAULT '{
        "ai_chat": true,
        "dashboards": true,
        "email_reports": true,
        "api_access": false
    }'::jsonb,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- One config per tenant
    UNIQUE(tenant_id)
);

-- ============================================
-- AUDIT LOG
-- ============================================

CREATE TABLE IF NOT EXISTS tenant_audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE SET NULL,

    -- Action details
    action VARCHAR(100) NOT NULL,  -- 'created', 'updated', 'suspended', 'activated', etc.
    performed_by VARCHAR(255),     -- Admin user who performed action
    details JSONB,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant ON tenant_audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON tenant_audit_log(created_at);

-- ============================================
-- ENCRYPTION FUNCTIONS
-- ============================================

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_data(data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(
        pgp_sym_encrypt(data, key),
        'base64'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_data(encrypted_data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(
        decode(encrypted_data, 'base64'),
        key
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_configs_updated_at
    BEFORE UPDATE ON tenant_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Audit log trigger
CREATE OR REPLACE FUNCTION log_tenant_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO tenant_audit_log (tenant_id, action, details)
        VALUES (NEW.tenant_id, 'created', row_to_json(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO tenant_audit_log (tenant_id, action, details)
        VALUES (
            NEW.tenant_id,
            CASE
                WHEN OLD.is_active = TRUE AND NEW.is_active = FALSE THEN 'suspended'
                WHEN OLD.is_active = FALSE AND NEW.is_active = TRUE THEN 'activated'
                ELSE 'updated'
            END,
            jsonb_build_object(
                'old', row_to_json(OLD),
                'new', row_to_json(NEW)
            )
        );
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO tenant_audit_log (tenant_id, action, details)
        VALUES (OLD.tenant_id, 'deleted', row_to_json(OLD));
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenant_changes_audit
    AFTER INSERT OR UPDATE OR DELETE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION log_tenant_changes();

-- ============================================
-- SEED DEMO TENANT
-- ============================================

-- Insert demo tenant (for development/testing)
INSERT INTO tenants (
    tenant_id,
    company_name,
    subdomain,
    database_url,
    database_credentials,
    is_active,
    metadata
) VALUES (
    'demo-tenant-id-00000000-0000-0000',
    'TaskifAI Demo',
    'demo',
    'PLACEHOLDER_ENCRYPT_LATER',  -- Should be encrypted with actual Supabase URL
    'PLACEHOLDER_ENCRYPT_LATER',  -- Should be encrypted with actual credentials JSON
    TRUE,
    '{"type": "demo", "description": "Demo tenant for development and testing"}'::jsonb
) ON CONFLICT (subdomain) DO NOTHING;

-- Insert demo tenant config
INSERT INTO tenant_configs (
    tenant_id,
    max_file_size_mb,
    features_enabled
) VALUES (
    'demo-tenant-id-00000000-0000-0000',
    100,
    '{
        "ai_chat": true,
        "dashboards": true,
        "email_reports": true,
        "api_access": false
    }'::jsonb
) ON CONFLICT (tenant_id) DO NOTHING;

-- ============================================
-- HELPER VIEWS
-- ============================================

-- Active tenants view (excludes sensitive data)
CREATE OR REPLACE VIEW active_tenants AS
SELECT
    tenant_id,
    company_name,
    subdomain,
    is_active,
    created_at,
    updated_at,
    metadata
FROM tenants
WHERE is_active = TRUE
ORDER BY created_at DESC;

-- Tenant stats view
CREATE OR REPLACE VIEW tenant_stats AS
SELECT
    COUNT(*) as total_tenants,
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_tenants,
    COUNT(*) FILTER (WHERE is_active = FALSE) as suspended_tenants,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as new_tenants_30d
FROM tenants;

-- ============================================
-- COMPLETED
-- ============================================

COMMENT ON TABLE tenants IS 'Master tenant registry for multi-tenant architecture';
COMMENT ON COLUMN tenants.database_url IS 'Encrypted Supabase project URL';
COMMENT ON COLUMN tenants.database_credentials IS 'Encrypted JSON containing anon_key and service_key';
