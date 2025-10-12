-- ============================================
-- COMPLETE FIX: Dynamic Dashboard Configurations
-- ============================================
-- This file combines table creation + seeding
-- Run this entire file in Supabase SQL Editor
-- ============================================

-- STEP 1: Create the dynamic_dashboard_configs table
-- ============================================

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

-- Indexes for performance
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

-- Enable Row Level Security
ALTER TABLE dynamic_dashboard_configs ENABLE ROW LEVEL SECURITY;

-- RLS Policies
DROP POLICY IF EXISTS "Users can read own dashboards or tenant defaults" ON dynamic_dashboard_configs;
CREATE POLICY "Users can read own dashboards or tenant defaults"
    ON dynamic_dashboard_configs FOR SELECT
    TO authenticated
    USING (user_id = auth.uid() OR user_id IS NULL);

DROP POLICY IF EXISTS "Users can create own dashboards" ON dynamic_dashboard_configs;
CREATE POLICY "Users can create own dashboards"
    ON dynamic_dashboard_configs FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can update own dashboards" ON dynamic_dashboard_configs;
CREATE POLICY "Users can update own dashboards"
    ON dynamic_dashboard_configs FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can delete own dashboards" ON dynamic_dashboard_configs;
CREATE POLICY "Users can delete own dashboards"
    ON dynamic_dashboard_configs FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- Trigger for auto-updating updated_at timestamp
DROP TRIGGER IF EXISTS update_dynamic_dashboard_configs_updated_at ON dynamic_dashboard_configs;
CREATE TRIGGER update_dynamic_dashboard_configs_updated_at
    BEFORE UPDATE ON dynamic_dashboard_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- STEP 2: Seed default dashboard configuration
-- ============================================

-- Default Dashboard Configuration (tenant-wide)
-- This will be used as fallback when users don't have custom configs
INSERT INTO dynamic_dashboard_configs (
    dashboard_id,
    user_id,
    dashboard_name,
    description,
    layout,
    kpis,
    filters,
    is_default,
    is_active,
    display_order
) VALUES (
    gen_random_uuid(),
    NULL,  -- Tenant-wide default (NULL user_id)
    'Overview Dashboard',
    'Real-time overview of sales performance and key metrics',

    -- Layout: Matches current Dashboard.tsx structure
    '[
        {
            "id": "kpi-grid",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"]
            }
        },
        {
            "id": "recent-uploads",
            "type": "recent_uploads",
            "position": {"row": 2, "col": 0, "width": 6, "height": 4},
            "props": {
                "title": "Recent Uploads",
                "description": "Latest file uploads and processing status",
                "limit": 5
            }
        },
        {
            "id": "top-products",
            "type": "top_products",
            "position": {"row": 2, "col": 6, "width": 6, "height": 4},
            "props": {
                "title": "Top Products",
                "description": "Best performing products by revenue",
                "limit": 5
            }
        }
    ]'::jsonb,

    -- KPIs to display
    '[
        "total_revenue",
        "total_units",
        "avg_price",
        "total_uploads"
    ]'::jsonb,

    -- Default filters
    '{
        "date_range": "last_30_days",
        "vendor": "all"
    }'::jsonb,

    true,   -- is_default
    true,   -- is_active
    0       -- display_order
) ON CONFLICT DO NOTHING;


-- STEP 3: Verify the setup
-- ============================================

SELECT
    'SUCCESS: dynamic_dashboard_configs table created and seeded' as status,
    COUNT(*) as config_count
FROM dynamic_dashboard_configs;

SELECT
    dashboard_id,
    dashboard_name,
    user_id,
    is_default,
    is_active,
    jsonb_array_length(layout) as widget_count,
    jsonb_array_length(kpis) as kpi_count,
    created_at
FROM dynamic_dashboard_configs
ORDER BY is_default DESC, display_order ASC;
