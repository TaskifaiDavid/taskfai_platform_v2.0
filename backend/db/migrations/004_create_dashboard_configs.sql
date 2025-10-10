-- Migration: Create dashboard_configs table for flexible per-tenant dashboard customization
-- Option 1: Database-Driven Dashboards implementation

CREATE TABLE IF NOT EXISTS dashboard_configs (
    dashboard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    dashboard_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Widget layout configuration (array of widget definitions)
    layout JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- KPI configuration (which metrics to display)
    kpis JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Default filters for this dashboard
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Dashboard metadata
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_layout CHECK (jsonb_typeof(layout) = 'array'),
    CONSTRAINT valid_kpis CHECK (jsonb_typeof(kpis) = 'array'),
    CONSTRAINT valid_filters CHECK (jsonb_typeof(filters) = 'object'),

    -- Ensure only one default dashboard per user
    CONSTRAINT unique_default_per_user UNIQUE NULLS NOT DISTINCT (user_id, is_default)
        WHERE is_default = true
);

-- Create indexes for performance
CREATE INDEX idx_dashboard_configs_user_id ON dashboard_configs(user_id);
CREATE INDEX idx_dashboard_configs_is_default ON dashboard_configs(is_default) WHERE is_default = true;
CREATE INDEX idx_dashboard_configs_is_active ON dashboard_configs(is_active) WHERE is_active = true;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_dashboard_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_dashboard_configs_updated_at
    BEFORE UPDATE ON dashboard_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_dashboard_configs_updated_at();

-- Row-Level Security (RLS) Policies
ALTER TABLE dashboard_configs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view their own dashboard configs or tenant-wide defaults
CREATE POLICY dashboard_configs_select_policy ON dashboard_configs
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR user_id IS NULL  -- Tenant-wide defaults
    );

-- Policy: Users can only insert their own dashboard configs
CREATE POLICY dashboard_configs_insert_policy ON dashboard_configs
    FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Policy: Users can only update their own dashboard configs
CREATE POLICY dashboard_configs_update_policy ON dashboard_configs
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Policy: Users can only delete their own dashboard configs
CREATE POLICY dashboard_configs_delete_policy ON dashboard_configs
    FOR DELETE
    USING (user_id = auth.uid());

-- Comments for documentation
COMMENT ON TABLE dashboard_configs IS 'Stores flexible dashboard configurations per user/tenant for dynamic UI rendering';
COMMENT ON COLUMN dashboard_configs.layout IS 'JSON array of widget definitions: [{"type": "kpi", "props": {...}, "position": {...}}]';
COMMENT ON COLUMN dashboard_configs.kpis IS 'JSON array of KPI identifiers to display: ["total_revenue", "units_sold", "avg_price"]';
COMMENT ON COLUMN dashboard_configs.filters IS 'JSON object of default dashboard filters: {"date_range": "last_30_days", "vendor": "all"}';
COMMENT ON COLUMN dashboard_configs.user_id IS 'User who owns this config. NULL = tenant-wide default for all users';
COMMENT ON COLUMN dashboard_configs.is_default IS 'Whether this is the default dashboard shown on login';
