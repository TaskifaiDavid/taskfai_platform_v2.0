-- ============================================
-- Dashboard Templates - Pre-built Dashboard Configurations
-- Purpose: Provide ready-to-use dashboards for common use cases
-- Date: 2025-10-12
-- ============================================
--
-- This file contains 5 pre-built dashboard templates:
-- 1. Overview Dashboard (Default - already exists)
-- 2. Europe Sales Dashboard
-- 3. US Market Dashboard
-- 4. Weekly Best Sellers
-- 5. Monthly Performance
-- 6. Last Quarter Review
--
-- Usage: Execute in Supabase SQL Editor
-- Note: These are tenant-wide templates (user_id = NULL)
-- ============================================

-- ============================================
-- Template 2: Europe Sales Dashboard 🇪🇺
-- ============================================
-- Purpose: Track European market D2C sales performance
-- Filters: European countries, last 30 days
-- Target Users: European sales teams, regional managers

INSERT INTO dynamic_dashboard_configs (
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
    NULL,  -- Tenant-wide template
    'Europe Sales Dashboard',
    'Track sales performance across European markets including Germany, France, UK, Netherlands, and Poland',

    -- Widget Layout (same as default for now, future: add Europe-specific widgets)
    '[
        {
            "id": "kpi-grid-europe",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "kpis": ["total_revenue", "total_units", "avg_price"]
            }
        },
        {
            "id": "recent-uploads-europe",
            "type": "recent_uploads",
            "position": {"row": 2, "col": 0, "width": 6, "height": 4},
            "props": {
                "title": "Recent Uploads (Europe)",
                "description": "Latest European sales data uploads",
                "limit": 5
            }
        },
        {
            "id": "top-products-europe",
            "type": "top_products",
            "position": {"row": 2, "col": 6, "width": 6, "height": 4},
            "props": {
                "title": "Top Products (Europe)",
                "description": "Best performing products in European markets",
                "limit": 5
            }
        }
    ]'::jsonb,

    -- KPIs
    '["total_revenue", "total_units", "avg_price"]'::jsonb,

    -- Filters - Europe focus
    '{
        "date_range": "last_30_days",
        "vendor": "all",
        "country": ["Germany", "France", "United Kingdom", "Netherlands", "Poland", "Italy", "Spain", "Belgium", "Austria"]
    }'::jsonb,

    false,  -- Not default
    true,   -- Active
    1       -- Display order
) ON CONFLICT DO NOTHING;

-- ============================================
-- Template 3: US Market Dashboard 🇺🇸
-- ============================================
-- Purpose: Monitor United States ecommerce performance
-- Filters: USA only, last 30 days
-- Target Users: US sales teams, North American managers

INSERT INTO dynamic_dashboard_configs (
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
    NULL,  -- Tenant-wide template
    'US Market Dashboard',
    'Monitor sales performance and trends in the United States market',

    -- Widget Layout
    '[
        {
            "id": "kpi-grid-us",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "kpis": ["total_revenue", "total_units", "avg_price"]
            }
        },
        {
            "id": "recent-uploads-us",
            "type": "recent_uploads",
            "position": {"row": 2, "col": 0, "width": 6, "height": 4},
            "props": {
                "title": "Recent Uploads (US)",
                "description": "Latest US sales data uploads",
                "limit": 5
            }
        },
        {
            "id": "top-products-us",
            "type": "top_products",
            "position": {"row": 2, "col": 6, "width": 6, "height": 4},
            "props": {
                "title": "Top Products (US)",
                "description": "Best selling products in the US market",
                "limit": 5
            }
        }
    ]'::jsonb,

    -- KPIs
    '["total_revenue", "total_units", "avg_price"]'::jsonb,

    -- Filters - US only
    '{
        "date_range": "last_30_days",
        "vendor": "all",
        "country": ["United States"]
    }'::jsonb,

    false,  -- Not default
    true,   -- Active
    2       -- Display order
) ON CONFLICT DO NOTHING;

-- ============================================
-- Template 4: Weekly Best Sellers 📈
-- ============================================
-- Purpose: Quick view of current week's top performing products
-- Filters: All regions, last 7 days
-- Target Users: Sales managers, daily/weekly review meetings

INSERT INTO dynamic_dashboard_configs (
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
    NULL,  -- Tenant-wide template
    'Weekly Best Sellers',
    'Quick snapshot of this week''s top performing products across all markets',

    -- Widget Layout - Focus on top products
    '[
        {
            "id": "kpi-grid-weekly",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "kpis": ["total_revenue", "total_units", "avg_price"]
            }
        },
        {
            "id": "top-products-weekly-revenue",
            "type": "top_products",
            "position": {"row": 2, "col": 0, "width": 6, "height": 4},
            "props": {
                "title": "Top Products by Revenue (7 Days)",
                "description": "Highest revenue generators this week",
                "limit": 10
            }
        },
        {
            "id": "top-products-weekly-units",
            "type": "top_products",
            "position": {"row": 2, "col": 6, "width": 6, "height": 4},
            "props": {
                "title": "Top Products by Units (7 Days)",
                "description": "Most sold products this week",
                "limit": 10
            }
        }
    ]'::jsonb,

    -- KPIs
    '["total_revenue", "total_units", "avg_price"]'::jsonb,

    -- Filters - Last 7 days, all regions
    '{
        "date_range": "last_7_days",
        "vendor": "all"
    }'::jsonb,

    false,  -- Not default
    true,   -- Active
    3       -- Display order
) ON CONFLICT DO NOTHING;

-- ============================================
-- Template 5: Monthly Performance 📊
-- ============================================
-- Purpose: Current month tracking for monthly business reviews
-- Filters: Current month (dynamic), all regions
-- Target Users: Management, monthly business review meetings

INSERT INTO dynamic_dashboard_configs (
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
    NULL,  -- Tenant-wide template
    'Monthly Performance',
    'Track month-to-date performance across all sales channels and regions',

    -- Widget Layout
    '[
        {
            "id": "kpi-grid-monthly",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"]
            }
        },
        {
            "id": "recent-uploads-monthly",
            "type": "recent_uploads",
            "position": {"row": 2, "col": 0, "width": 6, "height": 4},
            "props": {
                "title": "Recent Uploads (This Month)",
                "description": "Latest data uploads for current month",
                "limit": 5
            }
        },
        {
            "id": "top-products-monthly",
            "type": "top_products",
            "position": {"row": 2, "col": 6, "width": 6, "height": 4},
            "props": {
                "title": "Top Products (This Month)",
                "description": "Best performers month-to-date",
                "limit": 5
            }
        }
    ]'::jsonb,

    -- KPIs
    '["total_revenue", "total_units", "avg_price", "total_uploads"]'::jsonb,

    -- Filters - Current month
    '{
        "date_range": "this_month",
        "vendor": "all"
    }'::jsonb,

    false,  -- Not default
    true,   -- Active
    4       -- Display order
) ON CONFLICT DO NOTHING;

-- ============================================
-- Template 6: Last Quarter Review 📅
-- ============================================
-- Purpose: 90-day performance analysis for quarterly planning
-- Filters: Last 90 days, all regions
-- Target Users: Executives, quarterly business planning

INSERT INTO dynamic_dashboard_configs (
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
    NULL,  -- Tenant-wide template
    'Last Quarter Review',
    'Comprehensive 90-day performance analysis for quarterly business planning and forecasting',

    -- Widget Layout
    '[
        {
            "id": "kpi-grid-quarterly",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"]
            }
        },
        {
            "id": "recent-uploads-quarterly",
            "type": "recent_uploads",
            "position": {"row": 2, "col": 0, "width": 6, "height": 4},
            "props": {
                "title": "Recent Uploads (Last 90 Days)",
                "description": "Data uploads from the last quarter",
                "limit": 5
            }
        },
        {
            "id": "top-products-quarterly",
            "type": "top_products",
            "position": {"row": 2, "col": 6, "width": 6, "height": 4},
            "props": {
                "title": "Top Products (Last 90 Days)",
                "description": "Quarterly best performers",
                "limit": 5
            }
        }
    ]'::jsonb,

    -- KPIs
    '["total_revenue", "total_units", "avg_price", "total_uploads"]'::jsonb,

    -- Filters - Last 90 days
    '{
        "date_range": "last_90_days",
        "vendor": "all"
    }'::jsonb,

    false,  -- Not default
    true,   -- Active
    5       -- Display order
) ON CONFLICT DO NOTHING;

-- ============================================
-- Verification Query
-- ============================================
-- Run this to verify all templates were created successfully

SELECT
    dashboard_id,
    dashboard_name,
    description,
    user_id,
    is_default,
    is_active,
    display_order,
    jsonb_array_length(layout) as widget_count,
    jsonb_array_length(kpis) as kpi_count,
    filters->>'date_range' as date_range,
    filters->>'country' as country_filter,
    created_at,
    updated_at
FROM dynamic_dashboard_configs
WHERE user_id IS NULL  -- Tenant-wide templates
ORDER BY display_order ASC, dashboard_name ASC;

-- Expected Result: 6 dashboards total
-- 1. Overview Dashboard (is_default = true, display_order = 0)
-- 2. Europe Sales Dashboard (display_order = 1)
-- 3. US Market Dashboard (display_order = 2)
-- 4. Weekly Best Sellers (display_order = 3)
-- 5. Monthly Performance (display_order = 4)
-- 6. Last Quarter Review (display_order = 5)

-- ============================================
-- Usage Instructions
-- ============================================
--
-- 1. Copy this entire SQL file
-- 2. Go to Supabase Dashboard → SQL Editor
-- 3. Create a new query
-- 4. Paste and execute
-- 5. Run the verification query at the bottom
-- 6. Refresh your TaskifAI dashboard page
-- 7. You should see all 6 dashboards in the dropdown
--
-- Note: If you need to reset and recreate templates:
--
-- DELETE FROM dynamic_dashboard_configs WHERE user_id IS NULL AND dashboard_name != 'Overview Dashboard';
--
-- Then re-run this SQL file
-- ============================================
