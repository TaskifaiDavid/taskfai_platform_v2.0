-- Migration: Add Comprehensive Analytics Dashboard for Bibbi
-- Description: Updates Bibbi's default dashboard with 7 KPIs + 2 bar charts + 3 metrics cards
-- Date: 2025-10-26

-- Update Bibbi's default dashboard configuration with comprehensive analytics
UPDATE dynamic_dashboard_configs
SET
  kpis = '["total_revenue", "total_units", "average_order_value", "units_per_transaction",
           "order_count", "fast_moving_products", "slow_moving_products"]'::jsonb,

  layout = '[
    {
      "id": "kpi-grid-1",
      "type": "kpi_grid",
      "position": {"row": 1, "col": 1, "width": 12, "height": 2},
      "props": {
        "kpis": ["total_revenue", "total_units", "average_order_value", "units_per_transaction",
                 "order_count", "fast_moving_products", "slow_moving_products"]
      }
    },
    {
      "id": "top-products-chart-1",
      "type": "top_products_chart",
      "position": {"row": 3, "col": 1, "width": 6, "height": 3},
      "props": {}
    },
    {
      "id": "top-resellers-chart-1",
      "type": "top_resellers_chart",
      "position": {"row": 3, "col": 7, "width": 6, "height": 3},
      "props": {}
    },
    {
      "id": "channel-mix-1",
      "type": "channel_mix",
      "position": {"row": 6, "col": 1, "width": 4, "height": 2},
      "props": {}
    },
    {
      "id": "top-markets-1",
      "type": "top_markets",
      "position": {"row": 6, "col": 5, "width": 4, "height": 2},
      "props": {}
    },
    {
      "id": "top-stores-1",
      "type": "top_stores",
      "position": {"row": 6, "col": 9, "width": 4, "height": 2},
      "props": {}
    },
    {
      "id": "recent-uploads-1",
      "type": "recent_uploads",
      "position": {"row": 8, "col": 1, "width": 12, "height": 2},
      "props": {}
    }
  ]'::jsonb,

  updated_at = NOW()

WHERE
  -- Apply to Bibbi tenant's default dashboard
  tenant_id = 'bibbi'
  AND (user_id IS NULL OR user_id IN (
    SELECT user_id FROM users WHERE tenant_id = 'bibbi'
  ))
  AND (dashboard_name = 'Overview Dashboard' OR is_default = true);

-- Verify the update
SELECT
  dashboard_id,
  tenant_id,
  dashboard_name,
  user_id,
  is_default,
  jsonb_array_length(kpis) as kpi_count,
  jsonb_array_length(layout) as widget_count,
  kpis,
  updated_at
FROM dynamic_dashboard_configs
WHERE tenant_id = 'bibbi'
  AND (dashboard_name = 'Overview Dashboard' OR is_default = true);

-- Expected result:
-- - kpi_count = 7
-- - widget_count = 7 (KPI grid + 2 charts + 3 metrics + recent uploads)
