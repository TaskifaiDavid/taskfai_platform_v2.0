# Quickstart: Dynamic Dashboard Configuration System

**Feature**: `003-check-file-implementation`
**Date**: 2025-10-12
**Purpose**: Rapid validation and testing guide

## Prerequisites

- Backend API running on `http://localhost:8000`
- Frontend dev server running on `http://localhost:5173`
- PostgreSQL database with migration 004 applied
- Valid JWT token for authentication

## Quick Test Scenarios

### 1. Verify Default Dashboard Loads (2 min)

**Test**: First-time user sees tenant default dashboard

```bash
# 1. Get JWT token
TOKEN="<your_jwt_token>"

# 2. Fetch default dashboard config
curl -X GET http://localhost:8000/api/dashboard-configs/default \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Expected: 200 OK with Overview Dashboard configuration
# Should contain: kpi_grid, recent_uploads, top_products widgets
```

**Success Criteria**:
- ✅ Returns 200 status code
- ✅ Response contains `dashboard_name`: "Overview Dashboard"
- ✅ `layout` array has 3 widgets
- ✅ `is_default`: true
- ✅ `user_id`: null (tenant default)

---

### 2. Create User-Specific Dashboard (3 min)

**Test**: User creates personal custom dashboard

```bash
# Create new dashboard config
curl -X POST http://localhost:8000/api/dashboard-configs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "My Sales Dashboard",
    "description": "Custom sales analysis view",
    "layout": [
      {
        "id": "my-kpis",
        "type": "kpi_grid",
        "position": {"row": 0, "col": 0, "width": 12, "height": 2},
        "props": {
          "kpis": ["total_revenue", "total_units"]
        }
      },
      {
        "id": "my-uploads",
        "type": "recent_uploads",
        "position": {"row": 2, "col": 0, "width": 12, "height": 3},
        "props": {
          "title": "Latest Uploads",
          "limit": 10
        }
      }
    ],
    "kpis": ["total_revenue", "total_units"],
    "filters": {"date_range": "last_90_days"},
    "is_default": true,
    "is_active": true
  }'

# Expected: 201 Created with new dashboard ID
```

**Success Criteria**:
- ✅ Returns 201 status code
- ✅ Response includes `dashboard_id` (UUID)
- ✅ `user_id` matches authenticated user
- ✅ `is_default`: true

---

### 3. Verify User Config Overrides Tenant Default (2 min)

**Test**: After creating user-specific default, it takes priority

```bash
# Fetch default again (should return user config now)
curl -X GET http://localhost:8000/api/dashboard-configs/default \
  -H "Authorization: Bearer $TOKEN"

# Expected: User's "My Sales Dashboard" instead of tenant default
```

**Success Criteria**:
- ✅ Returns user-created dashboard
- ✅ `dashboard_name`: "My Sales Dashboard"
- ✅ `user_id`: <authenticated_user_id>
- ✅ NOT the tenant default "Overview Dashboard"

---

### 4. Update Dashboard Configuration (2 min)

**Test**: User modifies existing dashboard

```bash
# Get dashboard ID from previous response
DASHBOARD_ID="<dashboard_id_from_create>"

# Update dashboard
curl -X PUT http://localhost:8000/api/dashboard-configs/$DASHBOARD_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "Updated Sales Dashboard",
    "description": "Modified description",
    "layout": [
      {
        "id": "updated-kpis",
        "type": "kpi_grid",
        "position": {"row": 0, "col": 0, "width": 12, "height": 2},
        "props": {
          "kpis": ["total_revenue", "avg_price", "total_uploads"]
        }
      }
    ]
  }'

# Expected: 200 OK with updated config
```

**Success Criteria**:
- ✅ Returns 200 status code
- ✅ `dashboard_name`: "Updated Sales Dashboard"
- ✅ `description`: "Modified description"
- ✅ `updated_at` timestamp changed

---

### 5. List All Dashboards (1 min)

**Test**: User can see all accessible dashboards

```bash
# List all dashboards
curl -X GET http://localhost:8000/api/dashboard-configs \
  -H "Authorization: Bearer $TOKEN"

# Expected: Array with user's dashboards + tenant default
```

**Success Criteria**:
- ✅ Returns 200 status code
- ✅ Array contains at least 2 items (user config + tenant default)
- ✅ Can see both `user_id: <user>` and `user_id: null` configs

---

### 6. Delete Dashboard (1 min)

**Test**: User can delete their own dashboard

```bash
# Delete dashboard
curl -X DELETE http://localhost:8000/api/dashboard-configs/$DASHBOARD_ID \
  -H "Authorization: Bearer $TOKEN"

# Expected: 204 No Content
```

**Success Criteria**:
- ✅ Returns 204 status code
- ✅ Subsequent GET /default returns tenant default again
- ✅ Deleted dashboard not in list

---

### 7. Frontend Widget Rendering (5 min)

**Test**: Frontend dynamically renders widgets from config

**Manual Steps**:
1. Open browser to `http://localhost:5173/dashboard`
2. Login with test user credentials
3. Observe dashboard loads with widgets

**Success Criteria**:
- ✅ Dashboard page loads without errors
- ✅ Widgets render in correct grid positions
- ✅ KPI cards display mock/real data
- ✅ Recent uploads table appears
- ✅ Top products list appears
- ✅ No console errors
- ✅ Page loads in <5 seconds

---

### 8. RLS Policy Validation (3 min)

**Test**: Users cannot access other users' dashboards

**Setup**:
```bash
# Create dashboard as User A
TOKEN_A="<user_a_token>"
DASHBOARD_A=$(curl -X POST http://localhost:8000/api/dashboard-configs \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "User A Dashboard",
    "layout": [...],
    "is_default": false
  }' | jq -r '.dashboard_id')

# Try to access as User B
TOKEN_B="<user_b_token>"
curl -X GET http://localhost:8000/api/dashboard-configs/$DASHBOARD_A \
  -H "Authorization: Bearer $TOKEN_B"

# Expected: 403 Forbidden or 404 Not Found
```

**Success Criteria**:
- ✅ User B cannot read User A's dashboard
- ✅ User B cannot update User A's dashboard
- ✅ User B cannot delete User A's dashboard
- ✅ User B CAN see tenant default (user_id IS NULL)

---

### 9. Tenant Default Read-Only for Users (2 min)

**Test**: Regular users cannot modify tenant defaults

```bash
# Get tenant default dashboard ID
TENANT_DEFAULT_ID=$(curl -X GET http://localhost:8000/api/dashboard-configs \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[] | select(.user_id == null and .is_default == true) | .dashboard_id')

# Try to update tenant default as regular user
curl -X PUT http://localhost:8000/api/dashboard-configs/$TENANT_DEFAULT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dashboard_name": "Hacked Tenant Default"}'

# Expected: 403 Forbidden
```

**Success Criteria**:
- ✅ Returns 403 status code
- ✅ Tenant default remains unchanged

---

### 10. Performance Validation (3 min)

**Test**: Dashboard renders within 5-second performance goal

```bash
# Measure API response time
time curl -X GET http://localhost:8000/api/dashboard-configs/default \
  -H "Authorization: Bearer $TOKEN" \
  -o /dev/null -s -w "Total: %{time_total}s\n"

# Expected: <200ms
```

**Browser Test**:
1. Open DevTools → Network tab
2. Navigate to `/dashboard`
3. Measure time to "DOMContentLoaded"

**Success Criteria**:
- ✅ API response <500ms
- ✅ Configuration fetch <200ms
- ✅ Total dashboard render <5 seconds
- ✅ No widget rendering blocking main thread >100ms

---

## Smoke Test Script

Run all tests automatically:

```bash
#!/bin/bash
# smoke-test.sh

set -e

TOKEN="$1"
BASE_URL="http://localhost:8000"

echo "🧪 Running Dashboard Config Smoke Tests..."

# Test 1: Get default
echo "Test 1: Get default dashboard..."
curl -s -X GET "$BASE_URL/api/dashboard-configs/default" \
  -H "Authorization: Bearer $TOKEN" | jq '.dashboard_name'

# Test 2: Create dashboard
echo "Test 2: Create custom dashboard..."
DASHBOARD_ID=$(curl -s -X POST "$BASE_URL/api/dashboard-configs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "Test Dashboard",
    "layout": [{
      "id": "test",
      "type": "kpi_grid",
      "position": {"row": 0, "col": 0, "width": 12, "height": 2},
      "props": {"kpis": ["total_revenue"]}
    }],
    "is_default": true
  }' | jq -r '.dashboard_id')

echo "Created: $DASHBOARD_ID"

# Test 3: Verify user override
echo "Test 3: Verify user config priority..."
curl -s -X GET "$BASE_URL/api/dashboard-configs/default" \
  -H "Authorization: Bearer $TOKEN" | jq '.dashboard_name'

# Test 4: Update
echo "Test 4: Update dashboard..."
curl -s -X PUT "$BASE_URL/api/dashboard-configs/$DASHBOARD_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dashboard_name": "Updated Test"}' | jq '.dashboard_name'

# Test 5: List
echo "Test 5: List all dashboards..."
curl -s -X GET "$BASE_URL/api/dashboard-configs" \
  -H "Authorization: Bearer $TOKEN" | jq 'length'

# Test 6: Delete
echo "Test 6: Delete dashboard..."
curl -s -X DELETE "$BASE_URL/api/dashboard-configs/$DASHBOARD_ID" \
  -H "Authorization: Bearer $TOKEN" -w "Status: %{http_code}\n"

echo "✅ All smoke tests passed!"
```

**Usage**:
```bash
chmod +x smoke-test.sh
./smoke-test.sh "your_jwt_token_here"
```

---

## Troubleshooting

### Dashboard Not Loading
```bash
# Check if migration applied
psql -d taskifai -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dynamic_dashboard_configs');"

# Check if tenant default exists
psql -d taskifai -c "SELECT dashboard_id, dashboard_name FROM dynamic_dashboard_configs WHERE user_id IS NULL AND is_default = true;"
```

### API Errors
- **401 Unauthorized**: JWT token expired or invalid
- **403 Forbidden**: Trying to access another user's dashboard
- **404 Not Found**: No default dashboard configured
- **409 Conflict**: Trying to create second default dashboard

### Frontend Not Rendering
1. Check browser console for JavaScript errors
2. Verify API response in Network tab
3. Confirm widget type exists in WIDGET_COMPONENTS registry
4. Check React Query DevTools for cache state

---

## Success Metrics

**All Tests Pass** ✅
- Default dashboard retrieval works
- User can create custom dashboards
- User configs override tenant defaults
- Updates and deletes work correctly
- RLS policies enforce isolation
- Performance goals met (<5s render)
- No console errors
- No security violations

**Ready for Production** when:
- All 10 test scenarios pass
- Smoke test script runs without errors
- Frontend renders all widget types
- Performance metrics under thresholds
- RLS policies verified with multiple test users

---

## Next Steps

After quickstart validation:
1. Run full integration test suite: `pytest backend/tests/integration/`
2. Run frontend component tests: `npm test`
3. Performance profiling with Chrome DevTools
4. Security audit with multiple tenant accounts
5. Deploy to staging environment
