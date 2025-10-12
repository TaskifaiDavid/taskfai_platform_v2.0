-- ============================================
-- Dynamic Dashboard Configurations Table
-- Migration: Add dynamic_dashboard_configs table
-- Purpose: Store user-customizable dashboard layouts with widgets and KPIs
-- ============================================

-- Create the dynamic dashboard configs table
CREATE TABLE IF NOT EXISTS dynamic_dashboard_configs (
    dashboard_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    dashboard_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- JSONB fields for flexible configuration
    layout JSONB NOT NULL,  -- Array of widget configurations with positions
    kpis JSONB NOT NULL,    -- Array of KPI types to display
    filters JSONB NOT NULL DEFAULT '{"date_range": "last_30_days", "vendor": "all"}'::jsonb,

    -- Configuration flags
    is_default BOOLEAN DEFAULT FALSE,  -- Only one default per user (or tenant-wide)
    is_active BOOLEAN DEFAULT TRUE,    -- Soft delete capability
    display_order INTEGER DEFAULT 0,   -- For sorting multiple dashboards

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Indexes for Performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_user_id
    ON dynamic_dashboard_configs(user_id);

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_is_default
    ON dynamic_dashboard_configs(is_default)
    WHERE is_default = true;

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_is_active
    ON dynamic_dashboard_configs(is_active)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_display_order
    ON dynamic_dashboard_configs(display_order);

-- ============================================
-- Row Level Security (RLS)
-- ============================================

-- Enable RLS on the table
ALTER TABLE dynamic_dashboard_configs ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can read their own dashboards OR tenant-wide defaults (user_id IS NULL)
CREATE POLICY "Users can read own dashboards or tenant defaults"
    ON dynamic_dashboard_configs FOR SELECT
    TO authenticated
    USING (user_id = auth.uid() OR user_id IS NULL);

-- RLS Policy: Users can create their own dashboards
CREATE POLICY "Users can create own dashboards"
    ON dynamic_dashboard_configs FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- RLS Policy: Users can update their own dashboards (not tenant defaults)
CREATE POLICY "Users can update own dashboards"
    ON dynamic_dashboard_configs FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid());

-- RLS Policy: Users can delete their own dashboards (not tenant defaults)
CREATE POLICY "Users can delete own dashboards"
    ON dynamic_dashboard_configs FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- ============================================
-- Triggers
-- ============================================

-- Trigger for auto-updating updated_at timestamp
-- Note: Requires update_updated_at_column() function to exist (should be in main schema.sql)
CREATE TRIGGER update_dynamic_dashboard_configs_updated_at
    BEFORE UPDATE ON dynamic_dashboard_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Verification Query
-- ============================================

-- Uncomment to verify table was created successfully
-- SELECT
--     column_name,
--     data_type,
--     is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'dynamic_dashboard_configs'
-- ORDER BY ordinal_position;
