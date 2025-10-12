# Data Model: Dynamic Dashboard Configuration System

**Feature**: `003-check-file-implementation`
**Date**: 2025-10-12
**Phase**: 1 - Data Model Design

## Overview

This document defines the data structures for the dynamic dashboard configuration system. The model supports flexible, database-driven dashboard layouts with per-user and per-tenant customization.

---

## Entity Relationship Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                dynamic_dashboard_configs                      │
├──────────────────────────────────────────────────────────────┤
│ dashboard_id (PK)        UUID                                │
│ user_id (FK→users)       UUID NULL  (NULL = tenant default)  │
│ dashboard_name           VARCHAR(255)                         │
│ description              TEXT                                  │
│ layout                   JSONB      (array of widget configs) │
│ kpis                     JSONB      (array of KPI types)      │
│ filters                  JSONB      (default filter settings) │
│ is_default               BOOLEAN                              │
│ is_active                BOOLEAN                              │
│ display_order            INTEGER                              │
│ created_at               TIMESTAMPTZ                          │
│ updated_at               TIMESTAMPTZ                          │
└──────────────────────────────────────────────────────────────┘
         │
         │ user_id FK (nullable)
         ▼
┌──────────────────────┐
│       users          │
├──────────────────────┤
│ user_id (PK)    UUID │
│ tenant_id       UUID │
│ ...                  │
└──────────────────────┘
```

**Key Relationships**:
- **One-to-Many**: `users` → `dynamic_dashboard_configs` (nullable FK)
- **Tenant Defaults**: Configs with `user_id IS NULL` apply to all users in the tenant
- **User Overrides**: Configs with `user_id = <specific_user>` override tenant defaults

---

## 1. Dashboard Configuration Entity

### Database Schema

```sql
CREATE TABLE dynamic_dashboard_configs (
    -- Primary Key
    dashboard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ownership (NULL = tenant-wide default, specific UUID = user-specific)
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,

    -- Metadata
    dashboard_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Widget Configuration (JSONB for flexibility)
    layout JSONB NOT NULL,        -- Array of widget configurations
    kpis JSONB NOT NULL DEFAULT '[]'::jsonb,          -- Array of KPI type strings
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,       -- Default filter settings

    -- Status Flags
    is_default BOOLEAN DEFAULT false,  -- Is this the default dashboard for user/tenant?
    is_active BOOLEAN DEFAULT true,    -- Is this dashboard currently available?
    display_order INTEGER DEFAULT 0,   -- Sort order for dashboard list

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_display_order CHECK (display_order >= 0),
    CONSTRAINT non_empty_name CHECK (LENGTH(TRIM(dashboard_name)) > 0)
);
```

### Indexes

```sql
-- Primary lookup: Get configs for specific user
CREATE INDEX idx_dynamic_dashboard_configs_user_id
    ON dynamic_dashboard_configs (user_id)
    WHERE user_id IS NOT NULL;

-- Lookup tenant defaults
CREATE INDEX idx_dynamic_dashboard_configs_tenant_default
    ON dynamic_dashboard_configs ((user_id IS NULL))
    WHERE user_id IS NULL;

-- Find default dashboards quickly
CREATE INDEX idx_dynamic_dashboard_configs_is_default
    ON dynamic_dashboard_configs (is_default)
    WHERE is_default = true;

-- Find active dashboards
CREATE INDEX idx_dynamic_dashboard_configs_is_active
    ON dynamic_dashboard_configs (is_active)
    WHERE is_active = true;

-- Widget type queries (GIN index for JSONB)
CREATE INDEX idx_dynamic_dashboard_configs_layout
    ON dynamic_dashboard_configs USING GIN (layout);

-- Ensure only one default per user
CREATE UNIQUE INDEX idx_dynamic_dashboard_configs_unique_user_default
    ON dynamic_dashboard_configs (user_id)
    WHERE is_default = true AND user_id IS NOT NULL;

-- Ensure only one tenant-wide default
CREATE UNIQUE INDEX idx_dynamic_dashboard_configs_unique_tenant_default
    ON dynamic_dashboard_configs ((user_id IS NULL))
    WHERE is_default = true AND user_id IS NULL;
```

### Row-Level Security (RLS) Policies

```sql
-- Enable RLS
ALTER TABLE dynamic_dashboard_configs ENABLE ROW LEVEL SECURITY;

-- Read Policy: Users can view their own configs + tenant defaults
CREATE POLICY select_dashboard_configs
    ON dynamic_dashboard_configs
    FOR SELECT
    USING (
        user_id = auth.uid()  -- User's own configurations
        OR
        (user_id IS NULL AND auth.uid() IS NOT NULL)  -- Tenant defaults (available to all authenticated users)
    );

-- Insert Policy: Users can only create their own configs
CREATE POLICY insert_dashboard_configs
    ON dynamic_dashboard_configs
    FOR INSERT
    WITH CHECK (
        user_id = auth.uid()  -- Must be creating for themselves
        OR
        (user_id IS NULL AND has_tenant_admin_role(auth.uid()))  -- Or admin creating tenant default
    );

-- Update Policy: Users can only update their own configs
CREATE POLICY update_dashboard_configs
    ON dynamic_dashboard_configs
    FOR UPDATE
    USING (
        user_id = auth.uid()  -- Must own the config
        OR
        (user_id IS NULL AND has_tenant_admin_role(auth.uid()))  -- Or admin updating tenant default
    )
    WITH CHECK (
        user_id = auth.uid()
        OR
        (user_id IS NULL AND has_tenant_admin_role(auth.uid()))
    );

-- Delete Policy: Users can only delete their own configs
CREATE POLICY delete_dashboard_configs
    ON dynamic_dashboard_configs
    FOR DELETE
    USING (
        user_id = auth.uid()  -- Must own the config
        OR
        (user_id IS NULL AND has_tenant_admin_role(auth.uid()))  -- Or admin deleting tenant default
    );
```

### Validation Rules

| Field | Validation | Rationale |
|-------|-----------|-----------|
| `dashboard_name` | NOT NULL, 1-255 characters, non-blank | Required for UI display |
| `layout` | NOT NULL, valid JSONB array | Dashboard must have at least structure defined |
| `kpis` | Valid JSONB array of strings | Defaults to empty array if not provided |
| `filters` | Valid JSONB object | Defaults to empty object if not provided |
| `is_default` | BOOLEAN, unique per (user_id OR tenant) | Only one default at each scope level |
| `display_order` | INTEGER >= 0 | Negative ordering doesn't make semantic sense |

---

## 2. Widget Configuration Schema (JSONB)

### Layout Structure

The `layout` column stores an array of widget configurations in JSONB format:

```json
[
  {
    "id": "widget-unique-id",
    "type": "widget_type_identifier",
    "position": {
      "row": 0,
      "col": 0,
      "width": 12,
      "height": 2
    },
    "props": {
      "title": "Widget Title",
      "limit": 5,
      ...  // Widget-specific properties
    }
  }
]
```

### Widget Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for widget instance within dashboard |
| `type` | string | Yes | Widget type identifier (e.g., "kpi_grid", "recent_uploads") |
| `position` | object | Yes | Grid positioning (row, col, width, height) |
| `props` | object | Yes | Widget-specific configuration properties |

### Position Schema

```json
{
  "row": 0,        // Starting row (0-indexed)
  "col": 0,        // Starting column (0-indexed, 12-column grid)
  "width": 12,     // Column span (1-12)
  "height": 2      // Row span (positive integer)
}
```

**Constraints**:
- `row >= 0`
- `col >= 0`
- `width >= 1 AND width <= 12` (12-column grid system)
- `height >= 1`
- `col + width <= 12` (widgets must fit within grid)

### Widget Props Schema

Widget-specific properties stored in `props` object. Each widget type defines its own schema:

**KPI Grid Widget**:
```json
{
  "type": "kpi_grid",
  "props": {
    "kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"],
    "showTrends": true,
    "period": "last_30_days"
  }
}
```

**Recent Uploads Widget**:
```json
{
  "type": "recent_uploads",
  "props": {
    "title": "Recent Uploads",
    "limit": 5,
    "showVendor": true,
    "showStatus": true
  }
}
```

**Top Products Widget**:
```json
{
  "type": "top_products",
  "props": {
    "title": "Top Products",
    "limit": 10,
    "sortBy": "revenue",  // or "units"
    "period": "last_90_days"
  }
}
```

---

## 3. KPI Configuration Schema (JSONB)

The `kpis` column stores an array of KPI type identifiers:

```json
["total_revenue", "total_units", "avg_price", "total_uploads", "reseller_count"]
```

**Supported KPI Types**:
- `total_revenue`: Sum of all sales revenue
- `total_units`: Sum of units sold
- `avg_price`: Average price per unit
- `total_uploads`: Count of data uploads
- `reseller_count`: Number of active resellers (B2B)
- `category_mix`: Revenue distribution by category
- `top_vendor`: Highest-volume vendor

---

## 4. Filter Configuration Schema (JSONB)

The `filters` column stores default filter settings:

```json
{
  "date_range": "last_30_days",
  "vendor": null,
  "category": null,
  "reseller": null,
  "status": "all"
}
```

**Filter Fields**:
| Field | Type | Options | Default |
|-------|------|---------|---------|
| `date_range` | string | "last_7_days", "last_30_days", "last_90_days", "this_month", "last_month", "custom" | "last_30_days" |
| `vendor` | string | null | Vendor name or null (all vendors) | null |
| `category` | string | null | Category name or null (all categories) | null |
| `reseller` | string | null | Reseller name or null (all resellers) | null |
| `status` | string | "all", "active", "inactive" | "all" |

---

## 5. Configuration Priority Hierarchy

**Query Order**:
1. **User-specific default** (`user_id = <user>` AND `is_default = true`)
2. **Tenant-wide default** (`user_id IS NULL` AND `is_default = true`)
3. **Fallback**: System-generated default (if no configs exist)

**Example Query**:
```sql
-- Get default dashboard for user
WITH user_default AS (
    SELECT * FROM dynamic_dashboard_configs
    WHERE user_id = $1 AND is_default = true AND is_active = true
    LIMIT 1
),
tenant_default AS (
    SELECT * FROM dynamic_dashboard_configs
    WHERE user_id IS NULL AND is_default = true AND is_active = true
    LIMIT 1
)
SELECT * FROM user_default
UNION ALL
SELECT * FROM tenant_default
LIMIT 1;
```

---

## 6. State Transitions

### Dashboard Lifecycle States

```
┌─────────────┐     create dashboard      ┌─────────────┐
│   NONE      │──────────────────────────▶│   ACTIVE    │
└─────────────┘                            └─────────────┘
                                                  │
                                                  │ set is_active = false
                                                  ▼
                                           ┌─────────────┐
                                           │  INACTIVE   │
                                           └─────────────┘
                                                  │
                                                  │ set is_active = true
                                                  ▼
                                           ┌─────────────┐
                                           │   ACTIVE    │◀───┐
                                           └─────────────┘    │
                                                  │            │
                                                  │ delete     │
                                                  ▼            │ restore
                                           ┌─────────────┐    │
                                           │  DELETED    │────┘
                                           └─────────────┘
```

**State Descriptions**:
- **ACTIVE** (`is_active = true`): Dashboard is available for viewing/editing
- **INACTIVE** (`is_active = false`): Dashboard exists but hidden from UI
- **DELETED**: Physical deletion from database (CASCADE deletes via FK)

### Default Dashboard State Machine

```
User creates dashboard
     │
     ▼
  is_default = false  ───set as default──▶  is_default = true
     ▲                                              │
     │                                              │
     └─────────────unset as default─────────────────┘
```

**Rules**:
- Only one dashboard can be `is_default = true` per user
- Only one dashboard can be `is_default = true` per tenant (where `user_id IS NULL`)
- Setting a dashboard as default automatically unsets previous default

---

## 7. Data Migration Strategy

### Initial Migration

```sql
-- Migration 004: Create dynamic_dashboard_configs table
-- Filename: 004_create_dynamic_dashboard_configs.sql

-- Create table (see schema above)
CREATE TABLE dynamic_dashboard_configs (...);

-- Create indexes (see indexes above)
CREATE INDEX ...;

-- Enable RLS and create policies (see RLS policies above)
ALTER TABLE dynamic_dashboard_configs ENABLE ROW LEVEL SECURITY;
CREATE POLICY ...;

-- Seed tenant-wide default dashboard
INSERT INTO dynamic_dashboard_configs (
    user_id, dashboard_name, description, layout, kpis, filters, is_default, is_active
) VALUES (
    NULL,  -- Tenant-wide default
    'Overview Dashboard',
    'Real-time overview of sales performance and key metrics',
    '[
        {
            "id": "kpi-grid",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {"kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"]}
        },
        {
            "id": "recent-uploads",
            "type": "recent_uploads",
            "position": {"row": 2, "col": 0, "width": 6, "height": 4},
            "props": {"title": "Recent Uploads", "limit": 5}
        },
        {
            "id": "top-products",
            "type": "top_products",
            "position": {"row": 2, "col": 6, "width": 6, "height": 4},
            "props": {"title": "Top Products", "limit": 5}
        }
    ]'::jsonb,
    '["total_revenue", "total_units", "avg_price", "total_uploads"]'::jsonb,
    '{"date_range": "last_30_days", "vendor": null, "category": null, "status": "all"}'::jsonb,
    true,  -- is_default
    true   -- is_active
);
```

### Rollback Strategy

```sql
-- Migration 004 Rollback
DROP TABLE IF EXISTS dynamic_dashboard_configs CASCADE;
```

---

## 8. Example Data

### Tenant Default Dashboard

```json
{
  "dashboard_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": null,
  "dashboard_name": "Overview Dashboard",
  "description": "Real-time overview of sales performance and key metrics",
  "layout": [
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
      "props": {"title": "Recent Uploads", "limit": 5}
    },
    {
      "id": "top-products",
      "type": "top_products",
      "position": {"row": 2, "col": 6, "width": 6, "height": 4},
      "props": {"title": "Top Products", "limit": 5, "sortBy": "revenue"}
    }
  ],
  "kpis": ["total_revenue", "total_units", "avg_price", "total_uploads"],
  "filters": {
    "date_range": "last_30_days",
    "vendor": null,
    "category": null,
    "status": "all"
  },
  "is_default": true,
  "is_active": true,
  "display_order": 0,
  "created_at": "2025-10-10T12:00:00Z",
  "updated_at": "2025-10-10T12:00:00Z"
}
```

### User-Specific Custom Dashboard

```json
{
  "dashboard_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "user_id": "user-abc-123",
  "dashboard_name": "Sales Analysis Dashboard",
  "description": "Deep dive into sales patterns and trends",
  "layout": [
    {
      "id": "revenue-chart",
      "type": "revenue_chart",
      "position": {"row": 0, "col": 0, "width": 12, "height": 3},
      "props": {"title": "Revenue Trend", "period": "last_90_days", "chartType": "line"}
    },
    {
      "id": "category-breakdown",
      "type": "category_revenue",
      "position": {"row": 3, "col": 0, "width": 6, "height": 3},
      "props": {"title": "Category Revenue Mix", "showPercentages": true}
    },
    {
      "id": "reseller-performance",
      "type": "reseller_performance",
      "position": {"row": 3, "col": 6, "width": 6, "height": 3},
      "props": {"title": "Top Resellers", "limit": 10}
    }
  ],
  "kpis": ["total_revenue", "reseller_count", "category_mix"],
  "filters": {
    "date_range": "last_90_days",
    "vendor": null,
    "category": null,
    "reseller": "all",
    "status": "active"
  },
  "is_default": true,
  "is_active": true,
  "display_order": 0,
  "created_at": "2025-10-11T15:30:00Z",
  "updated_at": "2025-10-11T15:30:00Z"
}
```

---

## Summary

**Key Design Decisions**:
1. **JSONB for Layout**: Allows adding new widget types without schema migrations
2. **Nullable user_id**: Supports both tenant-wide and user-specific configurations
3. **Partial Unique Indexes**: Enforces single default per scope (user OR tenant)
4. **RLS Policies**: Automatic tenant/user isolation via Supabase auth
5. **Configuration Priority**: Clear hierarchy (user > tenant > system default)

**Validation Strategy**:
- Database constraints enforce data integrity
- Pydantic models validate JSONB structure at API layer
- TypeScript interfaces provide compile-time safety in frontend

**Next Phase**: Generate API contracts from this data model (Phase 1 continued)
