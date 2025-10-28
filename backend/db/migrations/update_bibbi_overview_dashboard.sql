-- ABOUTME: Update Bibbi's Overview Dashboard to display comprehensive analytics
-- ABOUTME: Adds 7 KPIs and 7 widgets to the default Overview Dashboard

-- Update the Overview Dashboard configuration for Bibbi
UPDATE dynamic_dashboard_configs
SET
  kpis = '[
    "total_revenue",
    "total_units",
    "average_order_value",
    "units_per_transaction",
    "order_count",
    "fast_moving_products",
    "slow_moving_products"
  ]'::jsonb,

  layout = '[
    {
      "id": "kpi-grid-1",
      "type": "kpi_grid",
      "position": {
        "x": 0,
        "y": 0,
        "w": 12,
        "h": 2
      },
      "props": {
        "kpis": [
          "total_revenue",
          "total_units",
          "average_order_value",
          "units_per_transaction",
          "order_count",
          "fast_moving_products",
          "slow_moving_products"
        ]
      }
    },
    {
      "id": "top-products-chart-1",
      "type": "top_products_chart",
      "position": {
        "x": 0,
        "y": 2,
        "w": 6,
        "h": 4
      },
      "props": {}
    },
    {
      "id": "top-resellers-chart-1",
      "type": "top_resellers_chart",
      "position": {
        "x": 6,
        "y": 2,
        "w": 6,
        "h": 4
      },
      "props": {}
    },
    {
      "id": "channel-mix-1",
      "type": "channel_mix",
      "position": {
        "x": 0,
        "y": 6,
        "w": 4,
        "h": 3
      },
      "props": {}
    },
    {
      "id": "top-markets-1",
      "type": "top_markets",
      "position": {
        "x": 4,
        "y": 6,
        "w": 4,
        "h": 3
      },
      "props": {}
    },
    {
      "id": "top-stores-1",
      "type": "top_stores",
      "position": {
        "x": 8,
        "y": 6,
        "w": 4,
        "h": 3
      },
      "props": {}
    },
    {
      "id": "recent-uploads-1",
      "type": "recent_uploads",
      "position": {
        "x": 0,
        "y": 9,
        "w": 12,
        "h": 2
      },
      "props": {
        "limit": 5
      }
    }
  ]'::jsonb,

  updated_at = NOW()

WHERE
  dashboard_id = '21f73c49-7510-4f20-9f9b-a1208a7bb43d'
  OR (user_id IS NULL AND dashboard_name = 'Overview Dashboard' AND is_default = true);
