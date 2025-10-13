-- Fix RLS for dynamic_dashboard_configs - allow service_role to query
-- Copy this ENTIRE file and paste into Supabase SQL Editor

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Service role can read all configs" ON dynamic_dashboard_configs;

-- Create policy for service_role
CREATE POLICY "Service role can read all configs"
    ON dynamic_dashboard_configs
    FOR SELECT
    TO service_role
    USING (true);

-- Verify policies were created
SELECT policyname, roles FROM pg_policies WHERE tablename = 'dynamic_dashboard_configs';
