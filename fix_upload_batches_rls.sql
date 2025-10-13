-- Fix RLS for upload_batches - allow service_role to query
-- Copy this ENTIRE file and paste into Supabase SQL Editor

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Service role can read all upload batches" ON upload_batches;

-- Create policy for service_role
CREATE POLICY "Service role can read all upload batches"
    ON upload_batches
    FOR SELECT
    TO service_role
    USING (true);

-- Verify policies were created
SELECT policyname, roles FROM pg_policies WHERE tablename = 'upload_batches';
