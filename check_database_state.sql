-- Check database state
-- Copy this ENTIRE file and paste into Supabase SQL Editor

-- Check if upload batches exist
SELECT COUNT(*) as total_upload_batches FROM upload_batches;

-- Check if dashboard configs exist
SELECT COUNT(*) as total_dashboard_configs FROM dynamic_dashboard_configs;

-- Check upload_batches policies
SELECT policyname, roles FROM pg_policies WHERE tablename = 'upload_batches';

-- Check dynamic_dashboard_configs policies
SELECT policyname, roles FROM pg_policies WHERE tablename = 'dynamic_dashboard_configs';
