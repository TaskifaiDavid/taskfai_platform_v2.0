-- ============================================
-- Add vendor_name Column to BIBBI uploads Table
-- ============================================
--
-- ABOUTME: Adds vendor_name column to BIBBI uploads table for frontend display consistency
-- ABOUTME: Enables vendor detection to be shown immediately in upload history UI

-- Add vendor_name column
ALTER TABLE uploads
ADD COLUMN IF NOT EXISTS vendor_name VARCHAR(100);

-- Add index for vendor filtering
CREATE INDEX IF NOT EXISTS idx_uploads_vendor_name ON uploads(vendor_name);

-- Add comment
COMMENT ON COLUMN uploads.vendor_name IS 'Auto-detected vendor name (liberty, boxnox, galilu, etc.)';

-- Backfill vendor_name from parser_class for existing records
-- Extract vendor name from parser_class (e.g., "liberty_processor" -> "liberty")
UPDATE uploads
SET vendor_name = LOWER(REPLACE(parser_class, '_processor', ''))
WHERE vendor_name IS NULL
  AND parser_class IS NOT NULL
  AND parser_class LIKE '%_processor';

-- Verification query
SELECT
    COUNT(*) as total_uploads,
    COUNT(vendor_name) as uploads_with_vendor,
    COUNT(DISTINCT vendor_name) as unique_vendors
FROM uploads;
