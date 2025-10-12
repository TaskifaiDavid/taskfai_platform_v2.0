-- Seed default dashboard configurations
-- This creates the default dashboard layout matching the current hardcoded Dashboard.tsx

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
    NULL,  -- Tenant-wide default
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

-- Example: BIBBI Custom Dashboard (different layout for specific client)
-- Uncomment when you have a BIBBI user_id
/*
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
    'YOUR_BIBBI_USER_ID_HERE'::uuid,  -- Replace with actual BIBBI user_id
    'BIBBI Sales Dashboard',
    'Reseller-focused dashboard with category breakdown',

    -- Different layout for BIBBI
    '[
        {
            "id": "kpi-grid",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "kpis": ["total_revenue", "total_units", "reseller_count", "category_mix"]
            }
        },
        {
            "id": "reseller-breakdown",
            "type": "reseller_performance",
            "position": {"row": 2, "col": 0, "width": 12, "height": 4},
            "props": {
                "title": "Reseller Performance",
                "description": "Sales breakdown by reseller",
                "limit": 10
            }
        },
        {
            "id": "category-mix",
            "type": "category_revenue",
            "position": {"row": 6, "col": 0, "width": 6, "height": 4},
            "props": {
                "title": "Category Revenue Mix",
                "description": "Revenue distribution by product category"
            }
        },
        {
            "id": "top-products",
            "type": "top_products",
            "position": {"row": 6, "col": 6, "width": 6, "height": 4},
            "props": {
                "title": "Top Products",
                "description": "Best performing products overall",
                "limit": 5
            }
        }
    ]'::jsonb,

    -- Different KPIs for BIBBI
    '[
        "total_revenue",
        "total_units",
        "reseller_count",
        "category_mix",
        "yoy_growth"
    ]'::jsonb,

    -- Different default filters
    '{
        "date_range": "last_90_days",
        "reseller": "all",
        "category": "all"
    }'::jsonb,

    true,   -- is_default
    true,   -- is_active
    0       -- display_order
) ON CONFLICT DO NOTHING;
*/

-- Verify inserted configs
SELECT
    dashboard_id,
    dashboard_name,
    user_id,
    is_default,
    is_active,
    jsonb_array_length(layout) as widget_count,
    jsonb_array_length(kpis) as kpi_count
FROM dynamic_dashboard_configs
ORDER BY is_default DESC, display_order ASC;
