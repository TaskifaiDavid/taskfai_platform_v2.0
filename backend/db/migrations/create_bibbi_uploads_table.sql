-- ============================================
-- Create BIBBI uploads Table
-- ============================================
-- ABOUTME: Creates uploads table for BIBBI tenant to track file upload history
-- ABOUTME: Supports vendor file processing workflow with status tracking and row counts

-- Create uploads table
CREATE TABLE IF NOT EXISTS uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    filename TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    rows_processed INTEGER,
    rows_cleaned INTEGER,
    processing_time_ms INTEGER,
    vendor_name VARCHAR(100),
    parser_class TEXT,
    rows_total INTEGER,
    rows_inserted INTEGER,
    rows_invalid INTEGER,
    processing_completed_at TIMESTAMP,

    CONSTRAINT uploads_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_uploads_user_id ON uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_uploads_status ON uploads(status);
CREATE INDEX IF NOT EXISTS idx_uploads_uploaded_at ON uploads(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_uploads_vendor_name ON uploads(vendor_name);

-- Add comments
COMMENT ON TABLE uploads IS 'BIBBI file upload history and processing status tracking';
COMMENT ON COLUMN uploads.id IS 'Unique upload identifier (UUID)';
COMMENT ON COLUMN uploads.user_id IS 'User who uploaded the file';
COMMENT ON COLUMN uploads.filename IS 'Original filename';
COMMENT ON COLUMN uploads.file_size IS 'File size in bytes';
COMMENT ON COLUMN uploads.uploaded_at IS 'Upload timestamp';
COMMENT ON COLUMN uploads.status IS 'Processing status: pending, processing, completed, failed';
COMMENT ON COLUMN uploads.error_message IS 'Error details if status is failed';
COMMENT ON COLUMN uploads.rows_processed IS 'Number of rows successfully processed';
COMMENT ON COLUMN uploads.rows_cleaned IS 'Number of rows after data cleaning';
COMMENT ON COLUMN uploads.processing_time_ms IS 'Processing duration in milliseconds';
COMMENT ON COLUMN uploads.vendor_name IS 'Auto-detected vendor name (liberty, boxnox, galilu, etc.)';
COMMENT ON COLUMN uploads.parser_class IS 'Processor class used for parsing';
COMMENT ON COLUMN uploads.rows_total IS 'Total rows in uploaded file';
COMMENT ON COLUMN uploads.rows_inserted IS 'Number of rows successfully inserted into database';
COMMENT ON COLUMN uploads.rows_invalid IS 'Number of invalid/rejected rows';
COMMENT ON COLUMN uploads.processing_completed_at IS 'When processing finished';

-- Enable Row-Level Security
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Allow service role full access
CREATE POLICY uploads_service_role_access ON uploads
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- RLS Policy: Users can only see their own uploads
CREATE POLICY uploads_user_isolation ON uploads
    FOR ALL
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Grant permissions
GRANT ALL ON uploads TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON uploads TO authenticated;

-- Verification query
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE t.table_name = columns.table_name) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name = 'uploads';

SELECT 'BIBBI uploads table created successfully!' AS status;
