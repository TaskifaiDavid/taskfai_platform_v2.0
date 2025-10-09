-- ============================================
-- TaskifAI - User-Tenant Mapping Table
-- Links users (by email) to their tenants
-- ============================================

-- User-tenant mapping table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS user_tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User identification (email-based before auth)
    email VARCHAR(255) NOT NULL,

    -- Tenant reference
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Role within tenant
    role VARCHAR(50) NOT NULL DEFAULT 'member',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(email, tenant_id),
    CONSTRAINT chk_role CHECK (role IN ('member', 'admin', 'super_admin')),
    CONSTRAINT chk_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_user_tenants_email ON user_tenants(email);
CREATE INDEX IF NOT EXISTS idx_user_tenants_tenant ON user_tenants(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_tenants_role ON user_tenants(role) WHERE role = 'super_admin';

-- ============================================
-- TRIGGERS
-- ============================================

-- Auto-update updated_at timestamp
CREATE TRIGGER update_user_tenants_updated_at
    BEFORE UPDATE ON user_tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- AUDIT LOG TRIGGER
-- ============================================

-- Log user-tenant mapping changes
CREATE OR REPLACE FUNCTION log_user_tenant_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO tenant_audit_log (tenant_id, action, performed_by, details)
        VALUES (
            NEW.tenant_id,
            'user_added',
            NEW.email,
            jsonb_build_object(
                'email', NEW.email,
                'role', NEW.role
            )
        );
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO tenant_audit_log (tenant_id, action, performed_by, details)
        VALUES (
            NEW.tenant_id,
            CASE
                WHEN OLD.role != NEW.role THEN 'role_changed'
                ELSE 'user_updated'
            END,
            NEW.email,
            jsonb_build_object(
                'email', NEW.email,
                'old_role', OLD.role,
                'new_role', NEW.role
            )
        );
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO tenant_audit_log (tenant_id, action, performed_by, details)
        VALUES (
            OLD.tenant_id,
            'user_removed',
            OLD.email,
            jsonb_build_object(
                'email', OLD.email,
                'role', OLD.role
            )
        );
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_tenant_changes_audit
    AFTER INSERT OR UPDATE OR DELETE ON user_tenants
    FOR EACH ROW
    EXECUTE FUNCTION log_user_tenant_changes();

-- ============================================
-- HELPER VIEWS
-- ============================================

-- View for user-tenant relationships with tenant details
CREATE OR REPLACE VIEW user_tenant_memberships AS
SELECT
    ut.id,
    ut.email,
    ut.role,
    t.tenant_id,
    t.company_name,
    t.subdomain,
    t.is_active as tenant_is_active,
    ut.created_at,
    ut.updated_at
FROM user_tenants ut
JOIN tenants t ON ut.tenant_id = t.tenant_id
WHERE t.is_active = TRUE
ORDER BY ut.email, t.company_name;

-- View for super admins
CREATE OR REPLACE VIEW super_admin_users AS
SELECT DISTINCT
    email,
    COUNT(tenant_id) as tenant_count,
    array_agg(tenant_id) as tenant_ids
FROM user_tenants
WHERE role = 'super_admin'
GROUP BY email;

-- ============================================
-- COMPLETED
-- ============================================

COMMENT ON TABLE user_tenants IS 'User-tenant mapping for multi-tenant access control';
COMMENT ON COLUMN user_tenants.email IS 'User email address (identifier before authentication)';
COMMENT ON COLUMN user_tenants.role IS 'User role within tenant: member, admin, or super_admin';
COMMENT ON COLUMN user_tenants.tenant_id IS 'Reference to tenant in registry';
