# Implementation Plan: Dynamic Dashboard Configuration System

**Branch**: `003-check-file-implementation` | **Date**: 2025-10-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-check-file-implementation/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded: retrospective spec for already implemented system
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ All clarifications resolved by user
   → Detect Project Type: Web application (frontend + backend)
   → Set Structure Decision: Option 2 (backend/ + frontend/)
3. Fill Constitution Check section
   → ✅ Evaluated against TaskifAI constitutional principles
4. Evaluate Constitution Check section
   → ✅ All gates PASS - feature fully compliant
   → Update Progress Tracking: Initial Constitution Check ✅
5. Execute Phase 0 → research.md
   → ✅ Generated: technology decisions and architecture patterns
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ Generated: all Phase 1 artifacts
7. Re-evaluate Constitution Check
   → ✅ PASS - no new violations introduced
   → Update Progress Tracking: Post-Design Constitution Check ✅
8. Plan Phase 2 → Describe task generation approach
   → ✅ Documented: test-driven task ordering strategy
9. STOP - Ready for /tasks command ✅
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**Feature**: Database-driven dashboard configuration system enabling per-user and per-tenant customizable dashboard layouts without code changes.

**Primary Requirement**: Allow users to view personalized dashboards with configurable widgets (KPI grids, recent uploads, top products) that can be customized at the tenant or user level through database-stored configurations.

**Technical Approach**:
- Store dashboard configurations as JSONB in Supabase PostgreSQL
- Dynamic widget rendering based on configuration type
- Priority hierarchy: user-specific default > tenant-wide default
- RLS policies for tenant and user isolation
- RESTful API for configuration CRUD operations
- React Query for efficient configuration caching

## Technical Context
**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI 0.104+, React 19, React Query 5.x, Supabase PostgreSQL 17
**Storage**: Supabase PostgreSQL with JSONB for flexible configuration storage
**Testing**: pytest (backend), Vitest (frontend), contract tests for API validation
**Target Platform**: Linux server (backend), modern web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (backend API + frontend SPA)
**Performance Goals**: Dashboard render <5 seconds, API response <500ms, configuration fetch <200ms
**Constraints**: RLS policies must enforce tenant isolation, widget configuration must be extensible without schema changes
**Scale/Scope**: Support 100+ unique dashboard configurations per tenant, 10+ widget types, 50+ concurrent users

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Multi-Tenant Security Architecture
- [x] Feature uses database-per-tenant isolation (dashboard configs stored in tenant-specific Supabase database)
- [x] Subdomain routing extracts tenant context from JWT claims (existing middleware applies)
- [x] JWT tokens include tenant_id and subdomain claims (inherited from platform auth)
- [x] All database connections are tenant-scoped via middleware (Supabase client uses tenant context)
- [x] Cross-tenant data access is physically impossible (database-per-tenant architecture)
- [x] Tenant credentials are encrypted at rest (Supabase handles credential encryption)

### II. Configuration-Driven Flexibility
- [x] Dashboard configurations stored in tenant database (`dynamic_dashboard_configs` table)
- [x] Widget types and layouts defined via configuration, not hardcoded
- [x] New widget types can be added without database schema changes (JSONB layout column)
- [x] System supports configuration inheritance (tenant defaults + user overrides)
- [x] Configuration changes take effect immediately (no service restart required)

### III. Defense-in-Depth Security
- [x] Physical database isolation enforced (Layer 0) - database-per-tenant
- [x] HTTPS/TLS and subdomain validation implemented (Layer 1-2) - inherited from platform
- [x] JWT authentication with tenant claims (Layer 3) - inherited from platform
- [x] Tenant-specific database routing (Layer 4) - Supabase client routing
- [x] RLS policies on `dynamic_dashboard_configs` table (Layer 5)
  - Users can view own configs + tenant defaults (user_id = auth.uid() OR user_id IS NULL)
  - Users can only modify own configs (user_id = auth.uid())
  - Tenant defaults (user_id IS NULL) are read-only for regular users
- [x] Input validation prevents injection (Layer 6) - Pydantic models validate all inputs
- [x] Audit logging per tenant (Layer 7) - timestamps track creation/updates
- [x] Not applicable: AI chat not used in this feature

### IV. Scalable SaaS Operations
- [x] Dashboard configurations scale independently per tenant
- [x] Connection pooling isolated per tenant (Supabase handles pooling)
- [x] Clear separation between tenant admin and user functions
  - Tenant admins can create tenant-wide defaults (user_id IS NULL)
  - Regular users can create personal dashboards (user_id = their ID)
- [x] Per-tenant monitoring via configuration metrics (active configs, widget usage)

### Technology Stack Compliance
- [x] Backend uses FastAPI (Python 3.11+) - `/backend/app/api/dashboard_config.py`
- [x] Frontend uses React 19 + TypeScript + Vite 6 - `/frontend/src/components/dashboard/`
- [x] Database uses Supabase PostgreSQL 17 with RLS - migration `004_create_dynamic_dashboard_configs.sql`
- [x] No prohibited patterns: ✅ No shared database, ✅ No client-side tenant validation, ✅ No hardcoded configs

**Gate Status**: ✅ **PASS** - All constitutional requirements satisfied

## Project Structure

### Documentation (this feature)
```
specs/003-check-file-implementation/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output - technology decisions
├── data-model.md        # Phase 1 output - entity and schema design
├── quickstart.md        # Phase 1 output - testing and validation steps
├── contracts/           # Phase 1 output - API contracts
│   ├── dashboard-config-api.yaml    # OpenAPI spec for dashboard config endpoints
│   └── widget-types.json            # Widget type definitions and schemas
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── app/
│   ├── api/
│   │   └── dashboard_config.py      # Dashboard config CRUD endpoints
│   ├── models/
│   │   └── dashboard_config.py      # Pydantic request/response models
│   └── services/
│       └── dashboard_service.py     # Business logic (if needed)
├── db/
│   ├── migrations/
│   │   └── 004_create_dynamic_dashboard_configs.sql
│   └── seed_dashboard_configs.sql
└── tests/
    ├── contract/
    │   └── test_dashboard_config_api.py   # Contract tests for API
    ├── integration/
    │   └── test_dashboard_workflows.py    # User story validation
    └── unit/
        └── test_dashboard_models.py       # Model validation tests

frontend/
├── src/
│   ├── components/
│   │   └── dashboard/
│   │       ├── DynamicDashboard.tsx       # Main orchestrator
│   │       └── widgets/
│   │           ├── KPIGridWidget.tsx
│   │           ├── RecentUploadsWidget.tsx
│   │           └── TopProductsWidget.tsx
│   ├── api/
│   │   └── dashboardConfig.ts             # API client + React Query hooks
│   ├── types/
│   │   └── dashboardConfig.ts             # TypeScript type definitions
│   └── pages/
│       └── Dashboard.tsx                   # Modified to use DynamicDashboard
└── tests/
    ├── components/
    │   └── dashboard/
    │       └── DynamicDashboard.test.tsx  # Component tests
    └── integration/
        └── dashboard-workflows.test.tsx   # E2E user story tests
```

**Structure Decision**: Web application (Option 2) - separate `backend/` and `frontend/` directories detected in repository. Feature follows existing backend API patterns and frontend component organization.

## Phase 0: Outline & Research

**Status**: ✅ Complete (see [research.md](./research.md))

### Research Objectives Completed

1. **Technology Stack Decisions**:
   - ✅ JSONB vs separate tables for widget configuration → **JSONB chosen** (flexibility without schema changes)
   - ✅ RLS policy design for multi-level defaults (tenant vs user) → **Partial indexes + OR conditions**
   - ✅ React Query cache strategy for configuration data → **staleTime: 5 minutes, refetch on window focus**
   - ✅ Dynamic component rendering patterns in React → **Switch-case with component registry**

2. **Best Practices Research**:
   - ✅ FastAPI async patterns for Supabase integration
   - ✅ Pydantic validation for JSONB configuration schemas
   - ✅ TypeScript strict mode for dashboard configuration types
   - ✅ React component composition for widget extensibility

3. **Integration Patterns**:
   - ✅ Supabase RLS with JWT claims for user/tenant isolation
   - ✅ React Query DevTools for configuration debugging
   - ✅ OpenAPI schema generation from Pydantic models

**Output**: [research.md](./research.md) - All technical decisions documented with rationale and alternatives

## Phase 1: Design & Contracts

**Status**: ✅ Complete

### Artifacts Generated

1. **Data Model** ([data-model.md](./data-model.md)):
   - `DashboardConfiguration` entity with JSONB fields (layout, kpis, filters)
   - Widget position schema (row, col, width, height)
   - Widget properties schema (extensible per widget type)
   - Configuration priority hierarchy (user > tenant)
   - RLS policies for read/write isolation

2. **API Contracts** ([contracts/](./contracts/)):
   - `dashboard-config-api.yaml` - OpenAPI 3.0 specification:
     - `GET /api/dashboard-configs/default` - Fetch default config for user
     - `GET /api/dashboard-configs` - List all configs for user
     - `GET /api/dashboard-configs/{id}` - Get specific config
     - `POST /api/dashboard-configs` - Create new config
     - `PUT /api/dashboard-configs/{id}` - Update config
     - `DELETE /api/dashboard-configs/{id}` - Delete config
   - `widget-types.json` - Widget type registry with schemas

3. **Contract Tests** (generated but not implemented):
   - `backend/tests/contract/test_dashboard_config_api.py` - API contract validation
   - Tests assert request/response schemas match OpenAPI spec
   - Tests must fail initially (no implementation)

4. **Integration Test Scenarios** (from user stories):
   - Story 1: First-time user sees default dashboard → Test default config retrieval
   - Story 2: User with custom config sees personalized layout → Test user config priority
   - Story 3: Admin creates tenant-wide config → Test tenant default creation
   - Story 4: Config changes reflect on refresh → Test configuration update flow
   - Story 5: Multiple users have independent configs → Test user isolation

5. **Agent Context Update** ([CLAUDE.md](../../CLAUDE.md)):
   - Added dynamic dashboard configuration section
   - Documented dashboard config API patterns
   - Added widget registry extension points
   - Preserved existing manual additions
   - Updated recent changes log

**Output**: data-model.md, contracts/*, failing contract tests, quickstart.md, CLAUDE.md updated

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

### Task Generation Strategy

**Source Documents**:
- Phase 1 contracts (dashboard-config-api.yaml, widget-types.json)
- Phase 1 data model (DashboardConfiguration entity, RLS policies)
- User stories from spec.md (5 acceptance scenarios)

**Task Categories**:

1. **Contract Test Tasks** [P] - Can run in parallel:
   - Task: Write contract test for `GET /api/dashboard-configs/default`
   - Task: Write contract test for `POST /api/dashboard-configs`
   - Task: Write contract test for `PUT /api/dashboard-configs/{id}`
   - Task: Write contract test for `DELETE /api/dashboard-configs/{id}`
   - Task: Write contract test for `GET /api/dashboard-configs` (list)

2. **Database & Model Tasks** [P] - Parallel after schema creation:
   - Task: Create migration `004_create_dynamic_dashboard_configs.sql` (table, indexes, RLS)
   - Task: Apply migration to development database
   - Task: Create Pydantic models in `backend/app/models/dashboard_config.py`
   - Task: Write unit tests for Pydantic model validation

3. **Backend Implementation Tasks** (Sequential dependencies):
   - Task: Implement `GET /default` endpoint (depends on: models)
   - Task: Implement `POST /api/dashboard-configs` endpoint (depends on: models)
   - Task: Implement `PUT /api/dashboard-configs/{id}` endpoint (depends on: models)
   - Task: Implement `DELETE /api/dashboard-configs/{id}` endpoint (depends on: models)
   - Task: Implement `GET /api/dashboard-configs` list endpoint (depends on: models)
   - Task: Register router in `backend/app/main.py`

4. **Frontend Type & API Tasks** [P]:
   - Task: Create TypeScript types in `frontend/src/types/dashboardConfig.ts`
   - Task: Create API client with React Query hooks in `frontend/src/api/dashboardConfig.ts`
   - Task: Write unit tests for React Query hooks

5. **Frontend Component Tasks** (Sequential dependencies):
   - Task: Create `KPIGridWidget` component (depends on: types)
   - Task: Create `RecentUploadsWidget` component (depends on: types)
   - Task: Create `TopProductsWidget` component (depends on: types)
   - Task: Create `DynamicDashboard` orchestrator (depends on: widgets)
   - Task: Update `Dashboard.tsx` to use `DynamicDashboard`
   - Task: Write component tests for widgets [P]

6. **Integration Test Tasks**:
   - Task: Write integration test for Story 1 (first-time user default dashboard)
   - Task: Write integration test for Story 2 (user custom config priority)
   - Task: Write integration test for Story 3 (tenant admin creates default)
   - Task: Write integration test for Story 4 (config changes reflect)
   - Task: Write integration test for Story 5 (user config isolation)

7. **Seed Data & Documentation Tasks**:
   - Task: Create `seed_dashboard_configs.sql` with default "Overview Dashboard"
   - Task: Apply seed data to development database
   - Task: Update OpenAPI documentation with examples
   - Task: Run quickstart validation steps

### Ordering Strategy

**TDD Order**: Contract tests → Models → Implementation → Integration tests
**Dependency Order**: Database schema → Backend models → API endpoints → Frontend types → Components
**Parallel Markers [P]**: Independent tasks that can execute concurrently

**Example Task Sequence**:
1-5. [P] Write all contract tests (fail initially)
6. Create database migration
7. Apply migration
8-9. [P] Create Pydantic models + unit tests
10-14. Implement API endpoints sequentially
15. Register router
16-18. [P] Create frontend types + API client + tests
19-21. [P] Create widget components
22. Create DynamicDashboard orchestrator
23. Update Dashboard.tsx
24-25. [P] Write component tests
26-30. Write integration tests sequentially
31-32. Create and apply seed data
33. Run quickstart validation

**Estimated Output**: 33 numbered, dependency-ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, verify 5-second render goal)

**Validation Checklist for Phase 5**:
- [ ] All contract tests pass (API schemas validated)
- [ ] All integration tests pass (user stories verified)
- [ ] Dashboard renders in <5 seconds on demo.taskifai.com
- [ ] RLS policies enforce tenant/user isolation (test with multiple users)
- [ ] Widget configurations are extensible (add new widget type without migration)
- [ ] Default dashboard loads for new users
- [ ] User-specific configs override tenant defaults correctly

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: ✅ No complexity violations detected

This feature fully adheres to all constitutional principles:
- ✅ Database-per-tenant isolation maintained
- ✅ Configuration-driven widget system (no hardcoded layouts)
- ✅ Defense-in-depth security with RLS policies
- ✅ Scalable per-tenant operations
- ✅ Technology stack compliance (FastAPI, React, Supabase)

No deviations or justifications required.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md generated
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, CLAUDE.md
- [x] Phase 2: Task planning complete (/plan command - approach documented above)
- [ ] Phase 3: Tasks generated (/tasks command - NEXT STEP)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (no violations)
- [x] Post-Design Constitution Check: PASS (no new violations)
- [x] All NEEDS CLARIFICATION resolved (user edited spec)
- [x] Complexity deviations documented (none required)

**Implementation Notes**:
- This is a **retrospective plan** for an already implemented feature
- Implementation files already exist (verified in IMPLEMENTATION_SUMMARY_DYNAMIC_DASHBOARDS.md)
- Plan serves as documentation and validation of constitutional compliance
- Can be used as template for future dashboard enhancements (Phase 2-4 widgets)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
