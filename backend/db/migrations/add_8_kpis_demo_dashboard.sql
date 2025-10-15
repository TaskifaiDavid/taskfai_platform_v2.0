-- Migration: Add 4 New KPIs to Demo Dashboard
-- Description: Updates default dashboard config to show 8 KPIs instead of 4
-- New KPIs: gross_profit, profit_margin, unique_countries, order_count
-- Date: 2025-10-15

-- Update the default dashboard configuration to include all 8 KPIs
UPDATE dynamic_dashboard_configs
SET
  kpis = '["total_revenue", "total_units", "avg_price", "total_uploads",
           "gross_profit", "profit_margin", "unique_countries", "order_count"]'::jsonb,

  layout = jsonb_set(
    layout,
    '{0,props,kpis}',
    '["total_revenue", "total_units", "avg_price", "total_uploads",
      "gross_profit", "profit_margin", "unique_countries", "order_count"]'::jsonb
  ),

  updated_at = NOW()

WHERE
  -- Apply to default dashboard (tenant-wide)
  (user_id IS NULL AND dashboard_name = 'Overview Dashboard' AND is_default = true)

  OR

  -- Apply to demo user's dashboard
  user_id IN (
    SELECT user_id
    FROM users
    WHERE email = 'test@demo.com'
      AND tenant_id = 'demo'
  );

-- Verify the update
SELECT
  dashboard_id,
  dashboard_name,
  user_id,
  is_default,
  jsonb_array_length(kpis) as kpi_count,
  kpis,
  layout->0->'props'->'kpis' as widget_kpis,
  updated_at
FROM dynamic_dashboard_configs
WHERE dashboard_name = 'Overview Dashboard'
   OR user_id IN (SELECT user_id FROM users WHERE email = 'test@demo.com');

-- Expected result: kpi_count = 8 for demo dashboard
