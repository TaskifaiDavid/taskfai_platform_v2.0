-- ============================================
-- Seed Data: User-Tenant Mappings
-- Links existing demo user to demo tenant
-- ============================================

-- Note: This assumes:
-- 1. You have a user with email 'admin@demo.com' in the users table
-- 2. You have a tenant with subdomain 'demo' in the tenant registry

-- Link demo user to demo tenant (admin role)
INSERT INTO user_tenants (user_id, tenant_id, role)
SELECT
    u.user_id,
    -- Replace with actual tenant_id from your tenant registry
    -- You'll need to get this from: SELECT tenant_id FROM tenants WHERE subdomain = 'demo'
    '00000000-0000-0000-0000-000000000000'::UUID AS tenant_id,
    'admin' AS role
FROM users u
WHERE u.email = 'admin@demo.com'
ON CONFLICT (user_id, tenant_id) DO NOTHING;

-- INSTRUCTIONS FOR PRODUCTION USE:
-- 1. Get the actual tenant_id from your tenant registry:
--    SELECT tenant_id, subdomain FROM tenants WHERE subdomain = 'demo';
--
-- 2. Replace '00000000-0000-0000-0000-000000000000' with the actual tenant_id
--
-- 3. Run this SQL in Supabase SQL Editor

-- Example for multiple users/tenants:
-- INSERT INTO user_tenants (user_id, tenant_id, role)
-- VALUES
--     ('user-uuid-1', 'tenant-uuid-demo', 'admin'),
--     ('user-uuid-2', 'tenant-uuid-demo', 'member'),
--     ('user-uuid-1', 'tenant-uuid-acme', 'member')  -- Multi-tenant user
-- ON CONFLICT (user_id, tenant_id) DO NOTHING;
