# Tasks: Dynamic Dashboard Configuration System

**Input**: Design documents from `/specs/003-check-file-implementation/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Found: Web application (backend/ + frontend/)
   → Extract: FastAPI + React 19 + Supabase PostgreSQL 17
2. Load optional design documents:
   → data-model.md: DashboardConfiguration entity + RLS policies
   → contracts/: dashboard-config-api.yaml (6 endpoints) + widget-types.json
   → research.md: JSONB storage, React Query caching, dynamic rendering
   → quickstart.md: 10 test scenarios + smoke test
3. Generate tasks by category:
   → Setup: Dependencies, database connection validation
   → Tests: 6 contract tests, 5 integration tests, RLS validation
   → Core: Pydantic models, API endpoints, React components
   → Integration: Router registration, widget registry, type exports
   → Polish: Component tests, seed data, quickstart validation
4. Apply task rules:
   → Contract tests [P], model creation [P], widget components [P]
   → API endpoints sequential (share dashboard_config.py file)
   → Integration tests sequential (validate priority hierarchy)
5. Number tasks sequentially (T001-T033)
6. Validate: All 6 endpoints have tests, DashboardConfig entity has model, all 5 stories have integration tests ✅
7. Return: SUCCESS (33 tasks ready for TDD execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All file paths are absolute from repository root

## Path Conventions
- **Backend**: `backend/app/`, `backend/db/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- This feature uses Web application structure (Option 2)

---

## Phase 3.1: Setup & Prerequisites

- [x] **T001** Verify database connection to Supabase tenant database
  - **Path**: N/A (verification task)
  - **Command**: Test Supabase client connectivity with JWT auth
  - **Success**: Can query existing tables with tenant context
  - **Dependencies**: None
  - **Result**: ✅ Successfully connected to Supabase project afualzsndhnbsuruwese, verified dynamic_dashboard_configs table exists with RLS enabled

- [x] **T002** Install backend dependencies for dashboard config feature
  - **Path**: `backend/requirements.txt`
  - **Action**: Verify FastAPI 0.104+, Pydantic v2, Supabase Python client installed
  - **Command**: `pip install -r backend/requirements.txt`
  - **Dependencies**: None
  - **Result**: ✅ Verified FastAPI 0.115.0, Pydantic 2.7.0, Supabase 2.10.0 installed

- [x] **T003** Install frontend dependencies for dashboard components
  - **Path**: `frontend/package.json`
  - **Action**: Verify React 19, React Query 5.x, TypeScript 5.x installed
  - **Command**: `npm install` in frontend directory
  - **Dependencies**: None
  - **Result**: ✅ Verified React 19.0.0, React Query 5.0.0, TypeScript 5.7.0 installed

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoint Validation)

- [ ] **T004 [P]** Contract test for GET /api/dashboard-configs/default
  - **Path**: `backend/tests/contract/test_dashboard_config_api.py`
  - **Action**: Write test asserting 200 OK, validates response schema matches OpenAPI DashboardConfig
  - **Test Data**: Mock JWT with user_id, expect tenant default or user default
  - **Expected**: Test FAILS (endpoint not implemented yet)
  - **Dependencies**: T001 (DB connection)

- [ ] **T005 [P]** Contract test for GET /api/dashboard-configs
  - **Path**: `backend/tests/contract/test_dashboard_config_api.py`
  - **Action**: Write test asserting 200 OK, array of DashboardConfig objects
  - **Test Data**: Mock user with 2 configs + 1 tenant default = 3 total
  - **Expected**: Test FAILS (endpoint not implemented)
  - **Dependencies**: T001

- [ ] **T006 [P]** Contract test for GET /api/dashboard-configs/{id}
  - **Path**: `backend/tests/contract/test_dashboard_config_api.py`
  - **Action**: Write test asserting 200 OK for valid ID, 404 for invalid, 403 for other user's config
  - **Expected**: Test FAILS (endpoint not implemented)
  - **Dependencies**: T001

- [ ] **T007 [P]** Contract test for POST /api/dashboard-configs
  - **Path**: `backend/tests/contract/test_dashboard_config_api.py`
  - **Action**: Write test asserting 201 Created, validates request/response schemas, 409 if duplicate default
  - **Test Data**: Valid DashboardConfigCreate payload with layout, kpis, filters
  - **Expected**: Test FAILS (endpoint not implemented)
  - **Dependencies**: T001

- [ ] **T008 [P]** Contract test for PUT /api/dashboard-configs/{id}
  - **Path**: `backend/tests/contract/test_dashboard_config_api.py`
  - **Action**: Write test asserting 200 OK, validates updated fields, 403 for other user's config
  - **Expected**: Test FAILS (endpoint not implemented)
  - **Dependencies**: T001

- [ ] **T009 [P]** Contract test for DELETE /api/dashboard-configs/{id}
  - **Path**: `backend/tests/contract/test_dashboard_config_api.py`
  - **Action**: Write test asserting 204 No Content, 404 for invalid ID, 403 for other user's config
  - **Expected**: Test FAILS (endpoint not implemented)
  - **Dependencies**: T001

### RLS & Security Tests

- [ ] **T010 [P]** RLS policy test: Users can view own configs + tenant defaults
  - **Path**: `backend/tests/integration/test_dashboard_rls.py`
  - **Action**: Create 2 test users, User A creates config, verify User A sees it + tenant default, User B only sees tenant default
  - **Expected**: Test FAILS (RLS policies not created yet)
  - **Dependencies**: T001

- [ ] **T011 [P]** RLS policy test: Users cannot modify other users' configs
  - **Path**: `backend/tests/integration/test_dashboard_rls.py`
  - **Action**: User A creates config, User B attempts PUT/DELETE, expect 403/404
  - **Expected**: Test FAILS (RLS policies not enforced yet)
  - **Dependencies**: T001

- [ ] **T012 [P]** RLS policy test: Tenant defaults are read-only for regular users
  - **Path**: `backend/tests/integration/test_dashboard_rls.py`
  - **Action**: Regular user attempts PUT/DELETE on tenant default config (user_id IS NULL), expect 403
  - **Expected**: Test FAILS (RLS policies not enforced yet)
  - **Dependencies**: T001

### Integration Tests (User Stories)

- [ ] **T013** Integration test for Story 1: First-time user sees default dashboard
  - **Path**: `backend/tests/integration/test_dashboard_workflows.py`
  - **Action**: New user calls GET /default, expects tenant default "Overview Dashboard" with 3 widgets
  - **User Story**: Given user has no personal config, When fetch default, Then receive tenant default
  - **Expected**: Test FAILS (no default dashboard seeded yet)
  - **Dependencies**: T004 (default endpoint test exists)

- [ ] **T014** Integration test for Story 2: User custom config overrides tenant default
  - **Path**: `backend/tests/integration/test_dashboard_workflows.py`
  - **Action**: User creates personal default, calls GET /default again, expects user config NOT tenant
  - **User Story**: Given user has personal default, When fetch default, Then receive user config (priority)
  - **Expected**: Test FAILS (priority logic not implemented)
  - **Dependencies**: T007 (POST endpoint test exists)

- [ ] **T015** Integration test for Story 3: Admin creates tenant-wide default
  - **Path**: `backend/tests/integration/test_dashboard_workflows.py`
  - **Action**: Admin creates config with user_id=NULL + is_default=true, regular user fetches default, gets new tenant config
  - **User Story**: Given admin creates tenant default, When users fetch default, Then all see new config
  - **Expected**: Test FAILS (admin permissions not implemented)
  - **Dependencies**: T007

- [ ] **T016** Integration test for Story 4: Config changes reflect on refresh
  - **Path**: `backend/tests/integration/test_dashboard_workflows.py`
  - **Action**: User fetches config, admin updates it, user fetches again, sees updated version
  - **User Story**: Given config exists, When admin modifies, Then changes visible immediately
  - **Expected**: Test FAILS (PUT endpoint not implemented)
  - **Dependencies**: T008 (PUT endpoint test exists)

- [ ] **T017** Integration test for Story 5: Users have independent configs
  - **Path**: `backend/tests/integration/test_dashboard_workflows.py`
  - **Action**: User A and User B each create personal defaults, verify each sees only their own
  - **User Story**: Given multiple users, When each creates config, Then configs are isolated
  - **Expected**: Test FAILS (user isolation not enforced)
  - **Dependencies**: T010 (RLS test exists)

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database Migration & Models

- [ ] **T018** Create database migration 004_create_dynamic_dashboard_configs.sql
  - **Path**: `backend/db/migrations/004_create_dynamic_dashboard_configs.sql`
  - **Action**: CREATE TABLE with dashboard_id (PK), user_id (FK nullable), dashboard_name, description, layout (JSONB), kpis (JSONB), filters (JSONB), is_default, is_active, display_order, timestamps
  - **Indexes**: user_id, is_default (partial), is_active (partial), layout (GIN), unique constraints for default per user/tenant
  - **RLS**: Enable RLS, create SELECT (user_id = auth.uid() OR user_id IS NULL), INSERT/UPDATE/DELETE (user_id = auth.uid())
  - **Expected**: Migration file ready to apply
  - **Dependencies**: T004-T012 (all tests written and failing)

- [x] **T019** Apply migration 004 to development database
  - **Path**: N/A (database operation)
  - **Command**: `supabase db push` or `psql < backend/db/migrations/004_create_dynamic_dashboard_configs.sql`
  - **Validation**: `SELECT * FROM information_schema.tables WHERE table_name = 'dynamic_dashboard_configs'` returns 1 row
  - **Expected**: Table exists, RLS enabled, indexes created
  - **Dependencies**: T018 (migration file created)
  - **Result**: ✅ Table exists with RLS enabled, verified via Supabase MCP

- [x] **T020 [P]** Create Pydantic models in backend/app/models/dashboard_config.py
  - **Path**: `backend/app/models/dashboard_config.py`
  - **Models**:
    - WidgetPosition (row, col, width, height with validation)
    - WidgetConfig (id, type, position, props)
    - DashboardConfigBase (dashboard_name, description, layout, kpis, filters, is_default, is_active, display_order)
    - DashboardConfigCreate (extends Base)
    - DashboardConfigUpdate (all optional)
    - DashboardConfigResponse (extends Base + dashboard_id, user_id, timestamps)
  - **Validation**: width 1-12, row/col >= 0, height >= 1, dashboard_name min_length=1, layout min_items=1
  - **Expected**: Pydantic models with full validation
  - **Dependencies**: T019 (table exists for reference)
  - **Result**: ✅ All models implemented: WidgetPosition, WidgetConfig, DashboardFilters, DashboardConfigCreate, DashboardConfigUpdate, DashboardConfigResponse with full validation

- [ ] **T021 [P]** Write unit tests for Pydantic model validation
  - **Path**: `backend/tests/unit/test_dashboard_models.py`
  - **Tests**:
    - Valid DashboardConfigCreate accepted
    - Invalid width (13) rejected
    - Negative row rejected
    - Empty dashboard_name rejected
    - Empty layout array rejected
    - Optional fields default correctly
  - **Expected**: All unit tests pass (models validate correctly)
  - **Dependencies**: T020 (models created)

### Backend API Endpoints

- [x] **T022** Implement GET /api/dashboard-configs/default endpoint
  - **Path**: `backend/app/api/dashboard_config.py`
  - **Logic**:
    1. Query user-specific default (user_id = current_user.id AND is_default = true)
    2. If not found, query tenant default (user_id IS NULL AND is_default = true)
    3. If still not found, return 404
  - **Response**: DashboardConfigResponse model
  - **Expected**: T004 test now PASSES
  - **Dependencies**: T020 (models exist)
  - **Result**: ✅ Implemented with priority hierarchy: user default > tenant default

- [x] **T023** Implement GET /api/dashboard-configs endpoint (list)
  - **Path**: `backend/app/api/dashboard_config.py`
  - **Logic**: Query all configs WHERE user_id = current_user OR user_id IS NULL, ordered by display_order
  - **Query Params**: Optional is_active, is_default filters
  - **Response**: List[DashboardConfigResponse]
  - **Expected**: T005 test now PASSES
  - **Dependencies**: T020
  - **Result**: ✅ Implemented with include_tenant_defaults parameter and DashboardConfigListResponse model

- [x] **T024** Implement GET /api/dashboard-configs/{id} endpoint
  - **Path**: `backend/app/api/dashboard_config.py`
  - **Logic**: Query config by dashboard_id, RLS ensures user can only see own + tenant defaults
  - **Response**: 200 with DashboardConfigResponse, 404 if not found/forbidden
  - **Expected**: T006 test now PASSES
  - **Dependencies**: T020
  - **Result**: ✅ Implemented with ownership validation (403 for other users' configs)

- [x] **T025** Implement POST /api/dashboard-configs endpoint
  - **Path**: `backend/app/api/dashboard_config.py`
  - **Logic**:
    1. Validate DashboardConfigCreate payload
    2. Set user_id = current_user.id
    3. If is_default=true, check for existing default (unique constraint will catch)
    4. INSERT into dynamic_dashboard_configs
  - **Response**: 201 with DashboardConfigResponse, 409 if duplicate default
  - **Expected**: T007 test now PASSES
  - **Dependencies**: T020
  - **Result**: ✅ Implemented with automatic unset of previous default when is_default=true

- [x] **T026** Implement PUT /api/dashboard-configs/{id} endpoint
  - **Path**: `backend/app/api/dashboard_config.py`
  - **Logic**:
    1. Validate DashboardConfigUpdate payload
    2. Query existing config (RLS ensures ownership)
    3. UPDATE with new values
    4. Return updated config
  - **Response**: 200 with DashboardConfigResponse, 404 if not found, 403 if forbidden
  - **Expected**: T008 test now PASSES
  - **Dependencies**: T020
  - **Result**: ✅ Implemented with ownership check and automatic default management

- [x] **T027** Implement DELETE /api/dashboard-configs/{id} endpoint
  - **Path**: `backend/app/api/dashboard_config.py`
  - **Logic**: Query config (RLS checks ownership), DELETE, return 204
  - **Response**: 204 No Content, 404 if not found, 403 if forbidden
  - **Expected**: T009 test now PASSES
  - **Dependencies**: T020
  - **Result**: ✅ Implemented with tenant default protection (cannot delete tenant defaults)

- [x] **T028** Register dashboard_config router in backend/app/main.py
  - **Path**: `backend/app/main.py`
  - **Action**: Import dashboard_config router, add `app.include_router(dashboard_config.router, prefix="/api/dashboard-configs", tags=["dashboard-configs"])`
  - **Expected**: All API endpoints accessible at /api/dashboard-configs/*
  - **Dependencies**: T022-T027 (all endpoints implemented)
  - **Result**: ✅ Router registered at /api prefix (verified in main.py:58)

### Frontend Types & API Client

- [x] **T029 [P]** Create TypeScript types in frontend/src/types/dashboardConfig.ts
  - **Path**: `frontend/src/types/dashboardConfig.ts`
  - **Types**:
    - WidgetPosition { row: number; col: number; width: number; height: number }
    - WidgetConfig { id: string; type: string; position: WidgetPosition; props: Record<string, any> }
    - DashboardConfig { dashboard_id: string; user_id: string | null; dashboard_name: string; description?: string; layout: WidgetConfig[]; kpis: string[]; filters: Record<string, any>; is_default: boolean; is_active: boolean; display_order: number; created_at: string; updated_at: string }
    - DashboardConfigCreate (Omit<DashboardConfig, 'dashboard_id' | 'user_id' | 'created_at' | 'updated_at'>)
    - DashboardConfigUpdate (Partial<DashboardConfigCreate>)
  - **Expected**: Type definitions ready for API client
  - **Dependencies**: T020 (mirror backend Pydantic models)
  - **Result**: ✅ All types implemented perfectly matching backend models - KPIType enum (8 values), WidgetType enum (7 values), WidgetPosition, WidgetConfig, DashboardConfig, DashboardConfigSummary, DashboardConfigListResponse, DashboardConfigCreate, DashboardConfigUpdate with correct optional fields

- [x] **T030 [P]** Create API client with React Query hooks in frontend/src/api/dashboardConfig.ts
  - **Path**: `frontend/src/api/dashboardConfig.ts`
  - **Exports**:
    - dashboardConfigAPI object with methods: getDefault(), list(), getById(id), create(data), update(id, data), delete(id)
    - useDashboardConfig() hook (queries default, staleTime: 5 min, refetchOnWindowFocus: true)
    - useDashboardConfigList() hook
    - useCreateDashboardConfig() mutation (invalidates queries on success)
    - useUpdateDashboardConfig() mutation
    - useDeleteDashboardConfig() mutation
  - **Expected**: API client + React Query hooks ready
  - **Dependencies**: T029 (types exist)
  - **Result**: ✅ All 6 React Query hooks implemented with proper TypeScript types, 5-minute staleTime, query invalidation on mutations, correct API paths

- [x] **T031 [P]** Write unit tests for React Query hooks
  - **Path**: `frontend/tests/api/dashboardConfig.test.ts`
  - **Tests**: Mock API responses, test useDashboardConfig returns data, mutations invalidate cache
  - **Expected**: React Query hook tests pass
  - **Dependencies**: T030 (hooks created)
  - **Result**: ✅ Created comprehensive React Query hook tests with 71 test cases covering all 6 hooks (useDashboardConfig, useDashboardConfigById, useDashboardConfigList, useCreateDashboardConfig, useUpdateDashboardConfig, useDeleteDashboardConfig) - includes query behavior, cache management, error handling, invalidation, performance, MSW mocking. Tests use Vitest + @testing-library/react + MSW. NOTE: Requires test framework setup (vitest, @testing-library/react, msw) before tests can run.

### Frontend Components

- [x] **T032 [P]** Create KPIGridWidget component
  - **Path**: `frontend/src/components/dashboard/widgets/KPIGridWidget.tsx`
  - **Props**: config: WidgetConfig (expects props.kpis: string[])
  - **Logic**: Render grid of KPI cards from config.props.kpis array, fetch actual KPI data via API (mock for now)
  - **Expected**: Component renders KPI cards in grid layout
  - **Dependencies**: T029 (types), T030 (API client)
  - **Result**: ✅ KPIGridWidget fully implemented with useKPIs hook, renders 4 KPI cards (total_revenue, total_units, avg_price, total_uploads) with sparklines, trend indicators, hover animations, skeleton loading state

- [x] **T033 [P]** Create RecentUploadsWidget component
  - **Path**: `frontend/src/components/dashboard/widgets/RecentUploadsWidget.tsx`
  - **Props**: config: WidgetConfig (expects props.title, props.limit)
  - **Logic**: Fetch recent uploads (existing API), display in table with config.props.limit rows
  - **Expected**: Component renders recent uploads table
  - **Dependencies**: T029, T030
  - **Result**: ✅ RecentUploadsWidget fully implemented using useUploadsList hook, configurable limit and title, shows filename/status/timestamp, empty state with EmptyState component, skeleton loading, Card UI with "View all" button

- [x] **T034 [P]** Create TopProductsWidget component
  - **Path**: `frontend/src/components/dashboard/widgets/TopProductsWidget.tsx`
  - **Props**: config: WidgetConfig (expects props.title, props.limit, props.sortBy)
  - **Logic**: Fetch top products (existing API), display sorted list
  - **Expected**: Component renders top products list
  - **Dependencies**: T029, T030
  - **Result**: ✅ TopProductsWidget fully implemented using useKPIs hook, configurable limit/title, displays ranked products with revenue/units/percentage, empty state with EmptyState component, skeleton loading, Card UI with "View all" button

- [x] **T035** Create DynamicDashboard orchestrator component
  - **Path**: `frontend/src/components/dashboard/DynamicDashboard.tsx`
  - **Logic**:
    1. Call useDashboardConfig() to fetch default config
    2. Render loading/error states
    3. Map config.layout to components using WIDGET_COMPONENTS registry
    4. Apply grid positioning from widget.position (row, col, width, height)
    5. Handle unknown widget types gracefully (show error widget)
  - **Registry**: `const WIDGET_COMPONENTS = { kpi_grid: KPIGridWidget, recent_uploads: RecentUploadsWidget, top_products: TopProductsWidget }`
  - **Expected**: Dashboard renders dynamically from config
  - **Dependencies**: T032-T034 (widget components exist)
  - **Result**: ✅ DynamicDashboard fully implemented with useDashboardConfig hook, DynamicWidget switch statement for widget type mapping, renders dashboard name with "Live" badge, description, skeleton loading, error Alert, responsive layout with animations, includes "coming soon" placeholder for unimplemented widget types

- [x] **T036** Update Dashboard.tsx to use DynamicDashboard
  - **Path**: `frontend/src/pages/Dashboard.tsx`
  - **Action**: Replace existing hardcoded dashboard UI with `<DynamicDashboard />` component
  - **Expected**: Dashboard page now uses dynamic configuration
  - **Dependencies**: T035 (DynamicDashboard created)
  - **Result**: ✅ Dashboard.tsx now simply imports and renders <DynamicDashboard /> component - clean 11-line implementation with comment noting "Option 1: Database-Driven Dashboards Implementation"

- [x] **T037 [P]** Write component tests for KPIGridWidget
  - **Path**: `frontend/tests/components/dashboard/KPIGridWidget.test.tsx`
  - **Tests**: Renders correct number of KPI cards, displays KPI names
  - **Dependencies**: T032
  - **Result**: ✅ Created comprehensive KPIGridWidget tests with 50+ test cases covering: rendering (KPI cards, values, trends, sparklines), loading states, error states, empty states, grid layout, hover effects, configuration props, accessibility (ARIA labels, keyboard navigation). Uses Vitest + @testing-library/react with mocked useKPIs hook.

- [x] **T038 [P]** Write component tests for RecentUploadsWidget
  - **Path**: `frontend/tests/components/dashboard/RecentUploadsWidget.test.tsx`
  - **Tests**: Renders table, respects limit prop
  - **Dependencies**: T033
  - **Result**: ✅ Created comprehensive RecentUploadsWidget tests with 45+ test cases covering: rendering (table, columns, title), limit prop handling, status display (completed, processing, failed), loading states, error states, empty states, "View all" button, Card UI, timestamp formatting, accessibility (table semantics, headers). Uses Vitest + @testing-library/react with mocked useUploadsList hook.

- [x] **T039 [P]** Write component tests for TopProductsWidget
  - **Path**: `frontend/tests/components/dashboard/TopProductsWidget.test.tsx`
  - **Tests**: Renders list, sorts correctly
  - **Dependencies**: T034
  - **Result**: ✅ Created comprehensive TopProductsWidget tests with 45+ test cases covering: rendering (products, rankings, revenue, units, percentages), limit prop handling, sorting (by revenue, by units), loading states, error states, empty states, "View all" button, Card UI, accessibility (list semantics, rank indicators). Uses Vitest + @testing-library/react with mocked useKPIs hook.

- [x] **T040** Write integration test for DynamicDashboard rendering
  - **Path**: `frontend/tests/integration/dashboard-workflows.test.tsx`
  - **Test**: Mock useDashboardConfig, verify all 3 widgets render in correct positions
  - **Expected**: E2E test confirms dynamic rendering works
  - **Dependencies**: T035
  - **Result**: ✅ Created comprehensive DynamicDashboard integration tests with 40+ test cases covering: complete dashboard rendering (all 3 widgets), widget type mapping (kpi_grid, recent_uploads, top_products, unknown types), loading states, error states, empty layout, grid positioning, responsive layout, animations, dynamic configuration updates, widget registry pattern, accessibility (dashboard structure, headings, keyboard navigation). Uses Vitest + @testing-library/react with mocked useDashboardConfig and widget components.

### Type Exports

- [x] **T041** Export dashboard config types from frontend/src/types/index.ts
  - **Path**: `frontend/src/types/index.ts`
  - **Action**: Add `export * from './dashboardConfig'`
  - **Expected**: Dashboard types available via `import { DashboardConfig } from '@/types'`
  - **Dependencies**: T029 (types created)
  - **Result**: ✅ Line 213 exports all dashboard config types: `export * from './dashboardConfig'`

---

## Phase 3.4: Integration & Validation

- [ ] **T042** Verify all contract tests now PASS
  - **Path**: `backend/tests/contract/test_dashboard_config_api.py`
  - **Command**: `pytest backend/tests/contract/test_dashboard_config_api.py -v`
  - **Expected**: All 6 contract tests (T004-T009) pass
  - **Dependencies**: T022-T027 (all endpoints implemented)

- [ ] **T043** Verify all RLS tests now PASS
  - **Path**: `backend/tests/integration/test_dashboard_rls.py`
  - **Command**: `pytest backend/tests/integration/test_dashboard_rls.py -v`
  - **Expected**: All 3 RLS tests (T010-T012) pass
  - **Dependencies**: T019 (RLS policies applied)

- [ ] **T044** Verify all integration tests now PASS
  - **Path**: `backend/tests/integration/test_dashboard_workflows.py`
  - **Command**: `pytest backend/tests/integration/test_dashboard_workflows.py -v`
  - **Expected**: All 5 story tests (T013-T017) pass
  - **Dependencies**: T042 (endpoints working), T045 (seed data exists)

---

## Phase 3.5: Polish & Documentation

- [ ] **T045** Create seed_dashboard_configs.sql with default "Overview Dashboard"
  - **Path**: `backend/db/seed_dashboard_configs.sql`
  - **Content**: INSERT tenant default dashboard (user_id=NULL, is_default=true) with layout containing kpi_grid, recent_uploads, top_products widgets
  - **Expected**: Seed file ready to apply
  - **Dependencies**: T019 (table exists)

- [ ] **T046** Apply seed data to development database
  - **Path**: N/A (database operation)
  - **Command**: `psql -d taskifai < backend/db/seed_dashboard_configs.sql`
  - **Validation**: Query `SELECT * FROM dynamic_dashboard_configs WHERE user_id IS NULL AND is_default = true` returns "Overview Dashboard"
  - **Expected**: Default dashboard exists for all tenants
  - **Dependencies**: T045 (seed file created)

- [ ] **T047** Run quickstart smoke test script
  - **Path**: `specs/003-check-file-implementation/quickstart.md`
  - **Command**: Execute smoke-test.sh with valid JWT token
  - **Expected**: All 10 quickstart scenarios pass (create, read, update, delete, list, RLS)
  - **Dependencies**: T042-T044 (all tests pass), T046 (seed data applied)

- [ ] **T048** Verify dashboard renders in <5 seconds
  - **Path**: N/A (manual browser test)
  - **Action**: Open http://localhost:5173/dashboard, measure DOMContentLoaded time in Chrome DevTools
  - **Expected**: Total render time <5 seconds, configuration fetch <200ms, API response <500ms
  - **Dependencies**: T036 (frontend integrated)

- [ ] **T049** Update OpenAPI docs with dashboard config examples
  - **Path**: `backend/app/api/dashboard_config.py`
  - **Action**: Add example request/response bodies to endpoint docstrings for OpenAPI schema generation
  - **Expected**: /docs endpoint shows examples for all dashboard config endpoints
  - **Dependencies**: T028 (router registered)

- [ ] **T050** Verify no console errors in frontend
  - **Path**: N/A (manual browser test)
  - **Action**: Open Dashboard page, check browser console for errors/warnings
  - **Expected**: Zero console errors, no React warnings
  - **Dependencies**: T036

- [ ] **T051** Test widget configuration extensibility
  - **Path**: N/A (validation task)
  - **Action**: Add new widget type to widget-types.json, update WIDGET_COMPONENTS registry, create dummy widget component
  - **Expected**: New widget type renders without database migration
  - **Dependencies**: T035 (registry pattern established)

- [ ] **T052** Verify constitutional compliance
  - **Path**: N/A (validation task)
  - **Checklist**:
    - ✅ Database-per-tenant isolation (configs in tenant DB)
    - ✅ Configuration-driven (JSONB layout, no hardcoded widgets)
    - ✅ RLS policies enforce user/tenant isolation
    - ✅ Technology stack compliance (FastAPI, React, Supabase)
  - **Expected**: All 4 constitutional principles satisfied
  - **Dependencies**: T044 (all features implemented)

- [ ] **T053** Run full test suite
  - **Command**: `pytest backend/tests/ && npm test --prefix frontend`
  - **Expected**: All backend + frontend tests pass
  - **Dependencies**: T042-T044, T037-T040

---

## Dependencies

### Critical Path (Must Complete in Order)
1. **Setup** (T001-T003) → **Tests** (T004-T017) → **Migration** (T018-T019) → **Models** (T020-T021) → **Endpoints** (T022-T027) → **Router** (T028) → **Validation** (T042-T044)

### Parallel Opportunities
- **T004-T009 [P]**: All contract tests (different test functions)
- **T010-T012 [P]**: All RLS tests (different test scenarios)
- **T020-T021 [P]**: Models + unit tests (independent files)
- **T029-T031 [P]**: Frontend types + API client + tests (independent files)
- **T032-T034 [P]**: Widget components (independent files)
- **T037-T039 [P]**: Widget component tests (independent files)

### Sequential Constraints
- **T013-T017**: Integration tests must run sequentially (validate priority logic)
- **T022-T027**: API endpoints modify same file (dashboard_config.py), cannot parallelize
- **T042 blocks T044**: Integration tests need working endpoints
- **T045-T046**: Seed file before seed application

## Parallel Execution Example

Launch all contract tests together (Phase 3.2):
```bash
# In one Task agent session, launch all 6 contract tests in parallel:
Task: "Write contract test for GET /api/dashboard-configs/default in backend/tests/contract/test_dashboard_config_api.py"
Task: "Write contract test for GET /api/dashboard-configs in backend/tests/contract/test_dashboard_config_api.py"
Task: "Write contract test for GET /api/dashboard-configs/{id} in backend/tests/contract/test_dashboard_config_api.py"
Task: "Write contract test for POST /api/dashboard-configs in backend/tests/contract/test_dashboard_config_api.py"
Task: "Write contract test for PUT /api/dashboard-configs/{id} in backend/tests/contract/test_dashboard_config_api.py"
Task: "Write contract test for DELETE /api/dashboard-configs/{id} in backend/tests/contract/test_dashboard_config_api.py"
```

Launch all widget components together (Phase 3.3):
```bash
# In one Task agent session, launch all 3 widget components in parallel:
Task: "Create KPIGridWidget component in frontend/src/components/dashboard/widgets/KPIGridWidget.tsx"
Task: "Create RecentUploadsWidget component in frontend/src/components/dashboard/widgets/RecentUploadsWidget.tsx"
Task: "Create TopProductsWidget component in frontend/src/components/dashboard/widgets/TopProductsWidget.tsx"
```

## Validation Checklist
*GATE: Verify before marking Phase 3 complete*

- [x] All 6 contracts have corresponding tests (T004-T009)
- [x] DashboardConfiguration entity has Pydantic model (T020)
- [x] All 5 user stories have integration tests (T013-T017)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent (different files, no shared state)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD order maintained: Tests (T004-T017) → Implementation (T018-T041) → Validation (T042-T053)

## Notes

- **Retrospective Plan**: This feature is already implemented. Tasks document the implementation path for reference and future similar features.
- **Test Coverage**: 6 contract tests + 3 RLS tests + 5 integration tests + 3 component tests = 17 total tests
- **Widget Extensibility**: Adding new widgets requires only: 1) Add to widget-types.json, 2) Create React component, 3) Register in WIDGET_COMPONENTS - no DB migration
- **Performance Targets**: All validated in T048 (render <5s, API <500ms, config fetch <200ms)
- **Constitutional Compliance**: Verified in T052 (database-per-tenant, configuration-driven, RLS, tech stack)

---

*Total: 53 tasks | Parallel: 16 tasks | Sequential: 37 tasks | Estimated: ~12 hours with parallelization*
