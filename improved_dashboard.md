# Improved Dashboard System - Implementation Plan

## Context
Date: 2025-10-12
Status: Dashboard system working after fixing authentication issues
Request: Add ability to have multiple dashboards with different filters (Europe, US, Best Sellers, etc.)

## Current State ✅

### Backend (Fully Implemented)
- **Database Schema**: `dynamic_dashboard_configs` table with full support for multiple dashboards
- **API Endpoints**: All CRUD operations available in `backend/app/api/dashboard_config.py`
  - GET `/api/dashboard-configs/default` - Get default dashboard
  - GET `/api/dashboard-configs` - List all dashboards
  - GET `/api/dashboard-configs/{id}` - Get specific dashboard
  - POST `/api/dashboard-configs` - Create new dashboard
  - PUT `/api/dashboard-configs/{id}` - Update dashboard
  - DELETE `/api/dashboard-configs/{id}` - Delete dashboard

### Frontend (Basic Implementation)
- **Current**: Single dashboard view loading default config
- **Missing**: Dashboard selector, creator, editor UI components

## Recent Fixes Applied
1. **Fixed duplicate tenant-wide default configs** - Deleted duplicate dashboard config from database
2. **Fixed dict attribute access** - Changed `current_user.user_id` to `current_user["user_id"]` (commit 04477fe)
3. **Fixed None response handling** - Added None checks for Supabase response objects (commit 4b725e5)

All fixes deployed and working in production.

---

## Implementation Plan

### Phase 1: Dashboard Selector UI (High Priority)
**Goal**: Allow users to switch between existing dashboards

#### 1.1 Create DashboardSelector Component
**File**: `frontend/src/components/dashboard/DashboardSelector.tsx`

**Features**:
- Dropdown/tabs to show all available dashboards
- Display dashboard name and description
- Highlight current active dashboard
- Switch dashboard on click
- Show "Default" badge on default dashboard

**API Integration**:
```typescript
// Use existing API endpoint
GET /api/dashboard-configs?include_tenant_defaults=true
// Returns list of user's dashboards + tenant-wide defaults
```

**State Management**:
```typescript
// Add to existing dashboard state
const [dashboards, setDashboards] = useState<DashboardConfig[]>([]);
const [currentDashboardId, setCurrentDashboardId] = useState<string>();
```

#### 1.2 Update Dashboard Page
**File**: `frontend/src/pages/Dashboard.tsx`

**Changes**:
- Add `<DashboardSelector>` at top of page
- Load selected dashboard config when user switches
- Persist selected dashboard in localStorage

**Layout**:
```
┌─────────────────────────────────────────────┐
│  Dashboard Selector: [Overview ▼]  [+ New] │
├─────────────────────────────────────────────┤
│  KPI Grid                                   │
├───────────────────┬─────────────────────────┤
│  Recent Uploads   │  Top Products           │
└───────────────────┴─────────────────────────┘
```

---

### Phase 2: Pre-built Dashboard Templates (Quick Win)
**Goal**: Provide ready-to-use dashboards for common use cases

#### 2.1 Create Seed Data File
**File**: `backend/db/seed_dashboard_templates.sql`

**Templates to Create**:

1. **Overview Dashboard** (Default - Already exists)
   - All regions, last 30 days
   - KPIs: Total Revenue, Total Units, Avg Price, Total Uploads
   - Widgets: KPI Grid, Recent Uploads, Top Products

2. **Europe Sales Dashboard**
   - Filter: `country` IN ('Germany', 'France', 'UK', 'Netherlands', 'Poland', etc.)
   - Date: Last 30 days
   - KPIs: Total Revenue, Total Units, Top Products, Reseller Performance
   - Widgets: Revenue Chart (Europe only), Category Revenue, Top Resellers

3. **US Market Dashboard**
   - Filter: `country = 'United States'`
   - Date: Last 30 days
   - KPIs: Total Revenue, Total Units, YoY Growth
   - Widgets: Sales Trend, Top Products (US), Regional Performance

4. **This Month Best Sellers**
   - Filter: `date_range = 'this_month'`
   - All regions
   - KPIs: Top Products, Total Units, Revenue
   - Widgets: Top 10 Products Table, Category Mix Chart

5. **Year-over-Year Analysis**
   - Filter: `date_range = 'this_year'` vs `date_range = 'last_year'`
   - All regions
   - KPIs: YoY Growth, Total Revenue (current), Total Revenue (previous)
   - Widgets: Growth Trend Chart, Category Comparison

#### 2.2 SQL Structure
```sql
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
    'Track sales performance across European markets',
    '[
        {
            "id": "revenue-chart",
            "type": "revenue_chart",
            "position": {"row": 0, "col": 0, "width": 12, "height": 3},
            "props": {
                "title": "Europe Revenue Trend",
                "filter": {"regions": ["Europe"]}
            }
        },
        ...
    ]'::jsonb,
    '["total_revenue", "total_units", "top_products"]'::jsonb,
    '{
        "date_range": "last_30_days",
        "vendor": "all",
        "category": null,
        "country": ["Germany", "France", "United Kingdom", "Netherlands", "Poland"]
    }'::jsonb,
    false,
    true,
    1
);
```

#### 2.3 Apply Templates
Run seed SQL in Supabase SQL Editor to create templates.

---

### Phase 3: Dashboard Creator UI (Medium Priority)
**Goal**: Allow users to create custom dashboards

#### 3.1 Create DashboardCreatorModal Component
**File**: `frontend/src/components/dashboard/DashboardCreatorModal.tsx`

**Form Fields**:
1. Dashboard Name (text input)
2. Description (textarea)
3. Region Filter (multi-select: All, Europe, US, Asia, etc.)
4. Date Range (select: Last 7 days, 30 days, This month, etc.)
5. Vendor Filter (select: All, specific vendors)
6. KPIs to Display (checkbox group: Revenue, Units, Avg Price, etc.)
7. Set as Default (checkbox)

**API Call**:
```typescript
POST /api/dashboard-configs
{
    "dashboard_name": "My Custom Dashboard",
    "description": "Sales for Europe, last 7 days",
    "layout": [...],  // Default widget layout
    "kpis": ["total_revenue", "total_units"],
    "filters": {
        "date_range": "last_7_days",
        "vendor": "all",
        "country": ["Germany", "France"]
    },
    "is_default": false,
    "is_active": true,
    "display_order": 0
}
```

#### 3.2 Add "Create Dashboard" Button
**Location**: Next to DashboardSelector
**Action**: Opens DashboardCreatorModal

---

### Phase 4: Dashboard Editor UI (Low Priority)
**Goal**: Allow users to edit existing dashboards

#### 4.1 Create DashboardEditorModal Component
**File**: `frontend/src/components/dashboard/DashboardEditorModal.tsx`

**Features**:
- Same form as creator, but pre-filled with existing values
- Add "Delete Dashboard" button (with confirmation)
- Widget layout editor (drag-and-drop for advanced users)

**API Calls**:
```typescript
// Update dashboard
PUT /api/dashboard-configs/{id}
{
    "dashboard_name": "Updated Name",
    "filters": {...},
    ...
}

// Delete dashboard
DELETE /api/dashboard-configs/{id}
```

#### 4.2 Add Edit Button
**Location**: In DashboardSelector dropdown (gear icon next to each dashboard)

---

### Phase 5: Advanced Filtering (Future Enhancement)
**Goal**: Dynamic filter controls on dashboard page

#### 5.1 Create FilterBar Component
**File**: `frontend/src/components/dashboard/FilterBar.tsx`

**Features**:
- Date range picker (override dashboard default)
- Region multi-select
- Vendor select
- Category select
- "Apply Filters" button
- "Reset to Dashboard Defaults" button

**Behavior**:
- Filters apply temporarily (not saved to dashboard config)
- Use React Query to refetch KPIs with new filters
- Show "Filtered" badge when active

---

## Technical Details

### Database Schema Reference
```sql
CREATE TABLE dynamic_dashboard_configs (
    dashboard_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    dashboard_name VARCHAR(255) NOT NULL,
    description TEXT,
    layout JSONB NOT NULL,  -- Widget configurations
    kpis JSONB NOT NULL,    -- Array of KPI types
    filters JSONB NOT NULL, -- date_range, vendor, category, reseller, country
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### KPI Types (Enum)
```typescript
enum KPIType {
    TOTAL_REVENUE = "total_revenue",
    TOTAL_UNITS = "total_units",
    AVG_PRICE = "avg_price",
    TOTAL_UPLOADS = "total_uploads",
    RESELLER_COUNT = "reseller_count",
    CATEGORY_MIX = "category_mix",
    YOY_GROWTH = "yoy_growth",
    TOP_PRODUCTS = "top_products"
}
```

### Widget Types (Enum)
```typescript
enum WidgetType {
    KPI_GRID = "kpi_grid",
    RECENT_UPLOADS = "recent_uploads",
    TOP_PRODUCTS = "top_products",
    RESELLER_PERFORMANCE = "reseller_performance",
    CATEGORY_REVENUE = "category_revenue",
    REVENUE_CHART = "revenue_chart",
    SALES_TREND = "sales_trend"
}
```

### Filter Schema
```typescript
interface DashboardFilters {
    date_range: string;  // "last_7_days" | "last_30_days" | "this_month" | etc.
    vendor: string;      // "all" | specific vendor name
    category?: string;   // Optional category filter
    reseller?: string;   // Optional reseller filter
    country?: string[];  // Optional array of country names
}
```

---

## Implementation Priority

### Phase 1: Dashboard Selector (2-3 hours)
**Why First**: Enables immediate value - users can switch between existing dashboards
**Files to Create**:
- `frontend/src/components/dashboard/DashboardSelector.tsx`
- Update `frontend/src/pages/Dashboard.tsx`

### Phase 2: Templates (1 hour)
**Why Second**: Provides ready-to-use dashboards for common scenarios
**Files to Create**:
- `backend/db/seed_dashboard_templates.sql`

### Phase 3: Dashboard Creator (3-4 hours)
**Why Third**: Allows users to create custom dashboards
**Files to Create**:
- `frontend/src/components/dashboard/DashboardCreatorModal.tsx`

### Phase 4: Dashboard Editor (2-3 hours)
**Why Fourth**: Enables editing existing dashboards
**Files to Create**:
- `frontend/src/components/dashboard/DashboardEditorModal.tsx`

### Phase 5: Advanced Filtering (4-5 hours)
**Why Last**: Nice-to-have for dynamic filtering
**Files to Create**:
- `frontend/src/components/dashboard/FilterBar.tsx`

**Total Estimated Time**: 12-16 hours

---

## API Endpoints Already Available

All backend endpoints are ready to use:

1. **GET `/api/dashboard-configs/default`**
   - Returns the default dashboard config for current user

2. **GET `/api/dashboard-configs`**
   - Returns all dashboards (user's + tenant-wide defaults)
   - Query param: `include_tenant_defaults=true`

3. **GET `/api/dashboard-configs/{dashboard_id}`**
   - Returns specific dashboard config by ID

4. **POST `/api/dashboard-configs`**
   - Creates new dashboard config
   - Body: `DashboardConfigCreate` model

5. **PUT `/api/dashboard-configs/{dashboard_id}`**
   - Updates existing dashboard config
   - Body: `DashboardConfigUpdate` model

6. **DELETE `/api/dashboard-configs/{dashboard_id}`**
   - Deletes dashboard config
   - Cannot delete tenant-wide defaults

---

## Example: Creating "Europe Sales" Dashboard

### Frontend API Call
```typescript
import { apiClient } from '@/lib/api';

const createEuropeDashboard = async () => {
    const response = await apiClient.post('/api/dashboard-configs', {
        dashboard_name: 'Europe Sales',
        description: 'Track sales performance across European markets',
        layout: [
            {
                id: 'kpi-grid',
                type: 'kpi_grid',
                position: { row: 0, col: 0, width: 12, height: 2 },
                props: { kpis: ['total_revenue', 'total_units', 'top_products'] }
            },
            {
                id: 'revenue-chart',
                type: 'revenue_chart',
                position: { row: 2, col: 0, width: 12, height: 4 },
                props: { title: 'Revenue Trend - Europe' }
            }
        ],
        kpis: ['total_revenue', 'total_units', 'top_products'],
        filters: {
            date_range: 'last_30_days',
            vendor: 'all',
            country: ['Germany', 'France', 'United Kingdom', 'Netherlands', 'Poland']
        },
        is_default: false,
        is_active: true,
        display_order: 1
    });

    return response.data;
};
```

---

## Testing Plan

### Phase 1 Testing
1. Load dashboard page → Should show DashboardSelector
2. Click selector → Should show list of available dashboards
3. Select different dashboard → Should load that dashboard's config
4. Refresh page → Should remember selected dashboard

### Phase 2 Testing
1. Run seed SQL in Supabase
2. Verify templates created: `SELECT * FROM dynamic_dashboard_configs WHERE user_id IS NULL`
3. Load dashboard page → Should see new templates in selector
4. Switch to "Europe Sales" → Should see Europe-filtered data

### Phase 3 Testing
1. Click "+ New Dashboard" → Should open creator modal
2. Fill form and submit → Should create new dashboard
3. New dashboard should appear in selector
4. Switch to new dashboard → Should load with correct filters

---

## Future Enhancements

### Short-term (Next Sprint)
- Dashboard sharing between users
- Dashboard export/import (JSON)
- Dashboard duplication ("Copy as Template")
- Favorite dashboards (star icon)

### Medium-term (Next Month)
- Widget marketplace (community-contributed widgets)
- Scheduled dashboard reports (email/PDF)
- Dashboard analytics (track which dashboards are most used)
- Dashboard version history (rollback changes)

### Long-term (Next Quarter)
- AI-powered dashboard recommendations
- Natural language dashboard queries ("Show me Europe sales last month")
- Real-time dashboard updates (WebSocket)
- Mobile dashboard app

---

## Notes for Implementation

### Code Organization
```
frontend/src/components/dashboard/
├── DashboardSelector.tsx          # Phase 1
├── DashboardCreatorModal.tsx      # Phase 3
├── DashboardEditorModal.tsx       # Phase 4
├── FilterBar.tsx                  # Phase 5
├── widgets/                       # Existing widget components
│   ├── KPIGridWidget.tsx
│   ├── RecentUploadsWidget.tsx
│   └── TopProductsWidget.tsx
└── index.ts                       # Export all components
```

### State Management
- Use React Query for server state (dashboard configs)
- Use Zustand or Context for UI state (selected dashboard, active filters)
- Persist selected dashboard ID in localStorage

### Performance Considerations
- Lazy load dashboard templates (don't fetch all at once)
- Cache dashboard configs in React Query with 5-minute stale time
- Use React.memo for expensive widget components
- Debounce filter changes to avoid excessive API calls

### Error Handling
- Show toast notifications for API errors
- Graceful fallback if dashboard config is invalid
- Validate filter values before applying
- Handle deleted dashboards (redirect to default)

---

## Contact & Questions

For any questions or clarifications during implementation:
1. Review this document
2. Check existing API endpoints in `backend/app/api/dashboard_config.py`
3. Refer to Pydantic models in `backend/app/models/dashboard_config.py`
4. Test API endpoints with curl or Postman

---

**Last Updated**: 2025-10-12
**Status**: Ready for implementation
**Next Step**: Start with Phase 1 (Dashboard Selector UI)
