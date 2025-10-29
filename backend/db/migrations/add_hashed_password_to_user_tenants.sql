-- ============================================
-- Add hashed_password column to user_tenants table
-- Sync passwords from users table
-- ============================================

-- Step 1: Add hashed_password column
ALTER TABLE user_tenants
ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);

-- Step 2: Sync passwords from users table to user_tenants
-- This updates existing user_tenants records with passwords from users table
UPDATE user_tenants ut
SET hashed_password = u.hashed_password
FROM users u
WHERE ut.email = u.email
AND ut.hashed_password IS NULL;

-- Step 3: Insert BIBBI admin user into user_tenants if not exists
INSERT INTO user_tenants (email, tenant_id, role, hashed_password)
SELECT
    u.email,
    u.tenant_id,
    'admin' as role,
    u.hashed_password
FROM users u
WHERE u.email = 'admin@bibbi-parfum.com'
ON CONFLICT (email, tenant_id)
DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    role = EXCLUDED.role;

-- Step 4: Create index on email for faster lookups (if not exists)
CREATE INDEX IF NOT EXISTS idx_user_tenants_email ON user_tenants(email);
