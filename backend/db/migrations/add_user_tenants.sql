-- ============================================
-- User-Tenant Mapping Table
-- Links users to their accessible tenants with role-based permissions
-- ============================================

CREATE TABLE IF NOT EXISTS user_tenants (
    user_tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member' CHECK (role IN ('member', 'admin', 'super_admin')),

    -- Audit fields
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    added_by UUID REFERENCES users(user_id) ON DELETE SET NULL,

    -- Prevent duplicate user-tenant pairs
    UNIQUE(user_id, tenant_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_tenants_user_id ON user_tenants(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tenants_tenant_id ON user_tenants(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_tenants_role ON user_tenants(role);

-- Row-Level Security
ALTER TABLE user_tenants ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can read their own tenant memberships
CREATE POLICY "Users can read own tenant memberships"
    ON user_tenants FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- RLS Policy: Admins can manage tenant memberships
CREATE POLICY "Admins can manage tenant memberships"
    ON user_tenants FOR ALL
    TO authenticated
    USING (
        role IN ('admin', 'super_admin') AND
        tenant_id IN (
            SELECT tenant_id FROM user_tenants
            WHERE user_id = auth.uid() AND role IN ('admin', 'super_admin')
        )
    );

-- ============================================
-- Audit Logging Triggers
-- ============================================

CREATE TABLE IF NOT EXISTS tenant_audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_tenant_id UUID REFERENCES user_tenants(user_tenant_id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL CHECK (action IN ('user_added', 'role_changed', 'user_removed')),
    performed_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    old_role VARCHAR(50),
    new_role VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_audit_log_user_tenant ON tenant_audit_log(user_tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_audit_log_timestamp ON tenant_audit_log(timestamp);

-- Trigger: Log user additions
CREATE OR REPLACE FUNCTION log_user_tenant_addition()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO tenant_audit_log (user_tenant_id, action, performed_by, new_role)
    VALUES (NEW.user_tenant_id, 'user_added', NEW.added_by, NEW.role);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_user_tenant_addition
    AFTER INSERT ON user_tenants
    FOR EACH ROW
    EXECUTE FUNCTION log_user_tenant_addition();

-- Trigger: Log role changes
CREATE OR REPLACE FUNCTION log_user_tenant_role_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.role <> NEW.role THEN
        INSERT INTO tenant_audit_log (user_tenant_id, action, old_role, new_role)
        VALUES (NEW.user_tenant_id, 'role_changed', OLD.role, NEW.role);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_user_tenant_role_change
    AFTER UPDATE ON user_tenants
    FOR EACH ROW
    EXECUTE FUNCTION log_user_tenant_role_change();

-- Trigger: Log user removals
CREATE OR REPLACE FUNCTION log_user_tenant_removal()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO tenant_audit_log (user_tenant_id, action, old_role)
    VALUES (OLD.user_tenant_id, 'user_removed', OLD.role);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_user_tenant_removal
    BEFORE DELETE ON user_tenants
    FOR EACH ROW
    EXECUTE FUNCTION log_user_tenant_removal();
