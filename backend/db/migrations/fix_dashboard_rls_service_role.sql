-- ============================================
-- Fix RLS Policy for Service Role Access
-- ============================================
-- Problem: Backend uses service_key (service_role) but RLS only allows authenticated role
-- Solution: Add explicit policy for service_role to read all dashboard configs
-- ============================================

-- Drop existing service_role policy if it exists (for idempotency)
DROP POLICY IF EXISTS "Service role can read all configs" ON dynamic_dashboard_configs;

-- Add policy for service_role to read all dashboard configs
-- Service role needs this to:
-- 1. Read tenant-wide defaults (user_id IS NULL)
-- 2. Serve API requests that bypass user-level RLS
CREATE POLICY "Service role can read all configs"
    ON dynamic_dashboard_configs FOR SELECT
    TO service_role
    USING (true);  -- Service role can read everything


-- ============================================
-- Verification Query
-- ============================================

-- Check all policies on the table
SELECT
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE tablename = 'dynamic_dashboard_configs'
ORDER BY policyname;

-- This should show:
-- 1. "Users can read own dashboards or tenant defaults" (authenticated role)
-- 2. "Users can create own dashboards" (authenticated role)
-- 3. "Users can update own dashboards" (authenticated role)
-- 4. "Users can delete own dashboards" (authenticated role)
-- 5. "Service role can read all configs" (service_role) ← NEW
