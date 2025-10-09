# Implementation Plan: Multi-Tenant Customer Onboarding System

**Branch**: `002-see-here-what` | **Date**: 2025-10-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/david/TaskifAI_platform_v2.0/specs/002-see-here-what/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded feature spec successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ Tech stack identified: FastAPI, React 19, Supabase, existing multi-tenant infrastructure
   → ✅ Set Structure Decision: Web application (frontend + backend)
3. Fill the Constitution Check section based on the content of the constitution document.
   → ✅ Constitution loaded and analyzed
4. Evaluate Constitution Check section below
   → ✅ Multi-tenant security architecture requires enhancement (tenant registry, central login)
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → In Progress: Research existing tenant infrastructure and security patterns
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Implement multi-tenant customer onboarding system with database-per-tenant isolation, central login portal at app.taskifai.com, and secure tenant discovery. System will maintain tenant registry database for subdomain routing, implement JWT-based authentication with tenant claims, and provide super admin access for platform management while ensuring complete data isolation between customer organizations.

**Technical Approach**: Leverage existing multi-tenant infrastructure (TenantContext, TenantContextMiddleware) and extend with:
- Central tenant registry Supabase database with user-tenant mappings
- Tenant discovery API endpoint for email-based routing
- Central login portal at app.taskifai.com with subdomain redirection
- Enhanced security layers and super admin role support

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript 5.7 (frontend)
**Primary Dependencies**: FastAPI 0.115+, React 19, Supabase 2.10+, Pydantic v2, LangChain 0.3+
**Storage**: Supabase PostgreSQL 17 (tenant registry + per-tenant databases), Redis 5.0+ (Celery)
**Testing**: pytest 7.4+ (backend), React Testing Library (frontend)
**Target Platform**: Linux server (Docker), Web browsers (Chrome, Firefox, Safari)
**Project Type**: web (frontend + backend)
**Performance Goals**: <2s tenant discovery, <500ms subdomain routing, support 100+ concurrent tenants
**Constraints**: Database-per-tenant isolation (constitutional requirement), encrypted credentials at rest, super admin must access multiple tenants
**Scale/Scope**: Initial: 5-10 customers, Design for: 100+ customers, 1000+ users total

**Existing Infrastructure**:
- ✅ Tenant context extraction from subdomain (TenantContextManager)
- ✅ Middleware for tenant validation (TenantContextMiddleware)
- ✅ JWT authentication with tenant claims
- ✅ Tenant registry schema (tenants_schema.sql) - NOT deployed
- ✅ Demo tenant hardcoded fallback (needs registry migration)
- ❌ Tenant registry database not deployed
- ❌ User-tenant mapping table missing
- ❌ Central login portal missing
- ❌ Tenant discovery endpoint missing

**User Requirements** (from prompt):
- Supabase is critical infrastructure
- Security must be thoroughly considered
- Super user admin (David) needs multi-tenant access

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Multi-Tenant Security Architecture
- [x] Feature uses database-per-tenant isolation (no shared database patterns) → **COMPLIANT** (existing architecture, will be enforced in registry)
- [x] Subdomain routing properly extracts and validates tenant context → **COMPLIANT** (TenantContextMiddleware.extract_subdomain exists)
- [x] JWT tokens include tenant_id and subdomain claims → **COMPLIANT** (existing JWT implementation)
- [x] All database connections are tenant-scoped via middleware → **COMPLIANT** (TenantContext routing exists)
- [x] Cross-tenant data access is physically impossible → **COMPLIANT** (database-per-tenant guarantees this)
- [ ] Tenant credentials are encrypted at rest → **REQUIRES IMPLEMENTATION** (encryption functions exist in schema, need backend integration)

**Status**: Mostly compliant. Need to implement encrypted credential storage/retrieval in tenant registry service.

### II. Configuration-Driven Flexibility
- [x] Vendor-specific logic uses configuration, not hardcoded rules → **COMPLIANT** (vendor_configs table exists)
- [x] Tenant configurations stored in tenant database (vendor_configs table) → **COMPLIANT** (per-tenant databases)
- [x] Changes require configuration updates only, not code deployment → **COMPLIANT** (existing pattern)
- [x] System supports configuration inheritance and override → **COMPLIANT** (baseline + tenant override)

**Status**: Fully compliant. No changes needed.

### III. Defense-in-Depth Security
- [x] Physical database isolation enforced (Layer 0) → **COMPLIANT** (database-per-tenant)
- [x] HTTPS/TLS and subdomain validation implemented (Layer 1-2) → **COMPLIANT** (production deployment has TLS)
- [x] JWT authentication with tenant claims (Layer 3) → **COMPLIANT** (existing implementation)
- [x] Tenant-specific database routing (Layer 4) → **COMPLIANT** (TenantContext in middleware)
- [x] RLS policies on all tenant database tables (Layer 5) → **COMPLIANT** (Supabase RLS enabled)
- [x] Input validation prevents SQL injection (Layer 6) → **COMPLIANT** (Pydantic validation + parameterized queries)
- [x] Audit logging per tenant (Layer 7) → **REQUIRES ENHANCEMENT** (tenant registry audit exists, need user-tenant mapping audit)
- [x] AI chat queries: blocked SQL keywords, read-only access, parameterized queries → **COMPLIANT** (existing AI security)

**Status**: Mostly compliant. Need to add audit logging for user-tenant operations and super admin access.

### IV. Scalable SaaS Operations
- [ ] Tenant provisioning is automated and secure → **REQUIRES IMPLEMENTATION** (manual process exists, needs automation)
- [x] Independent tenant scaling supported → **COMPLIANT** (database-per-tenant enables this)
- [ ] Connection pooling isolated per tenant → **REQUIRES VERIFICATION** (Supabase client per tenant, need to verify pooling)
- [ ] Clear separation between platform admin and tenant admin functions → **REQUIRES IMPLEMENTATION** (super admin role needs definition)
- [ ] Per-tenant monitoring and audit logs → **PARTIAL** (audit schema exists, needs implementation)

**Status**: Partial compliance. Need to implement tenant provisioning automation and super admin workflows.

### Technology Stack Compliance
- [x] Backend uses FastAPI (Python 3.11+) → **COMPLIANT** (FastAPI 0.115.0, Python 3.11)
- [x] Frontend uses React 19 + TypeScript + Vite 6 → **COMPLIANT** (React 19.0.0, TS 5.7, Vite 6.0.0)
- [x] Database uses Supabase PostgreSQL 17 with RLS → **COMPLIANT** (Supabase 2.10+, PG 17)
- [x] No prohibited patterns: shared database, client-side tenant validation, hardcoded configs → **COMPLIANT**

**Status**: Fully compliant.

### Overall Assessment
**CONDITIONAL PASS** - Core architecture is constitutionally compliant. Implementation must add:
1. Encrypted credential storage/retrieval for tenant registry
2. Super admin role and access control
3. Audit logging for user-tenant operations
4. Automated tenant provisioning workflows

*Documented in Complexity Tracking below*

## Project Structure

### Documentation (this feature)
```
specs/002-see-here-what/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── tenant-discovery.yaml
│   ├── tenant-registry.yaml
│   └── login-portal.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── app/
│   ├── api/
│   │   ├── auth.py                    # Add /discover-tenant endpoint
│   │   └── admin/
│   │       └── tenants.py             # Tenant provisioning endpoints
│   ├── core/
│   │   ├── config.py                  # Add registry database config
│   │   └── tenant.py                  # Existing TenantContext (enhance)
│   ├── middleware/
│   │   └── tenant_context.py          # Modify: remove demo hardcoding
│   ├── models/
│   │   ├── tenant.py                  # Add TenantDiscovery models
│   │   └── user.py                    # Add UserTenant models
│   └── services/
│       └── tenant/
│           ├── registry.py            # NEW: Tenant registry service
│           └── discovery.py           # NEW: Tenant discovery logic
├── db/
│   ├── tenants_schema.sql            # Existing - will be deployed
│   ├── user_tenants.sql              # NEW: User-tenant mapping table
│   ├── seed_demo_tenant.sql          # NEW: Demo tenant registry entry
│   └── seed_customer1.sql            # NEW: First customer setup
└── tests/
    ├── contract/
    │   ├── test_tenant_discovery_contract.py
    │   └── test_tenant_registry_contract.py
    ├── integration/
    │   ├── test_tenant_onboarding_flow.py
    │   ├── test_super_admin_access.py
    │   └── test_central_login_portal.py
    └── unit/
        └── test_tenant_registry_service.py

frontend/
├── src/
│   ├── pages/
│   │   ├── LoginPortal.tsx           # NEW: Central login at app.taskifai.com
│   │   └── Login.tsx                 # Modify: accept email query param
│   ├── components/
│   │   └── auth/
│   │       ├── TenantSelector.tsx    # NEW: Multi-tenant selector for super admin
│   │       └── LoginForm.tsx         # Modify: pre-fill email
│   ├── api/
│   │   └── tenant.ts                 # NEW: Tenant discovery API
│   ├── App.tsx                       # Modify: routing for app.taskifai.com
│   └── lib/
│       └── api.ts                    # Existing API client (may need CORS update)
└── tests/
    └── integration/
        ├── test_login_portal.spec.ts
        └── test_tenant_selector.spec.ts
```

**Structure Decision**: Web application (frontend + backend). Feature spans both layers with new central login portal (frontend), tenant discovery API (backend), and tenant registry infrastructure (backend + database). Existing multi-tenant patterns will be extended, not replaced.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Encryption implementation for tenant credentials ✅ (pgcrypto functions exist)
   - Connection pooling isolation per tenant (Supabase client behavior)
   - CORS configuration for app.taskifai.com subdomain
   - Super admin role implementation patterns
   - Tenant provisioning automation best practices

2. **Generate and dispatch research agents**:
   - Research: Supabase client connection pooling and tenant isolation
   - Research: FastAPI CORS configuration for subdomain wildcard
   - Research: JWT role-based access control for super admin
   - Research: Tenant provisioning automation patterns with Supabase Management API
   - Research: Best practices for encrypted credential storage and rotation
   - Research: Security patterns for central login portals with redirect flows

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:

   **Entity: Tenant**
   - Fields: tenant_id (UUID, PK), company_name, subdomain (unique), database_url (encrypted), database_credentials (encrypted), is_active, metadata (JSONB)
   - Relationships: One tenant → Many user_tenants
   - Validation: subdomain must match ^[a-z0-9-]+$ pattern
   - State transitions: active ↔ suspended

   **Entity: UserTenant (NEW)**
   - Fields: id (UUID, PK), email, tenant_id (FK), role (member|admin|super_admin), created_at
   - Relationships: Many-to-one with Tenant
   - Validation: Unique constraint on (email, tenant_id), email format validation
   - Business rules: Super admin can belong to multiple tenants, regular users belong to one tenant

   **Entity: TenantConfig**
   - Fields: config_id (UUID, PK), tenant_id (FK), max_file_size_mb, allowed_vendors, features_enabled (JSONB)
   - Relationships: One-to-one with Tenant

   **Entity: TenantAuditLog**
   - Fields: log_id (UUID, PK), tenant_id (FK), action, performed_by, details (JSONB), created_at
   - Business rules: Immutable audit trail for compliance

2. **Generate API contracts** from functional requirements:

   **POST /api/auth/discover-tenant** (Tenant Discovery)
   - Request: `{ email: string }`
   - Response (single tenant): `{ subdomain: string, company_name: string, redirect_url: string }`
   - Response (multi-tenant): `{ tenants: [{ subdomain: string, company_name: string }] }`
   - Error: 404 if email not found

   **POST /api/admin/tenants** (Tenant Provisioning - Super Admin Only)
   - Request: `{ subdomain: string, company_name: string, admin_email: string, region: string }`
   - Response: `{ tenant_id: string, status: "provisioning", database_url: string }`
   - Error: 409 if subdomain exists, 403 if not super admin

   **GET /api/admin/tenants** (List Tenants - Super Admin Only)
   - Response: `{ tenants: [{ tenant_id, company_name, subdomain, is_active, created_at }] }`

   **PATCH /api/admin/tenants/{tenant_id}** (Update Tenant - Super Admin Only)
   - Request: `{ is_active?: boolean, company_name?: string }`
   - Response: `{ tenant_id, is_active, updated_at }`

   Output OpenAPI schema to `/contracts/tenant-discovery.yaml`, `/contracts/tenant-registry.yaml`

3. **Generate contract tests** from contracts:
   - `tests/contract/test_tenant_discovery_contract.py` - Assert /discover-tenant request/response schemas
   - `tests/contract/test_tenant_registry_contract.py` - Assert admin endpoints schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:

   **Integration Test: Regular User Login Flow**
   - Navigate to app.taskifai.com
   - Enter email "user@customer1.com"
   - Assert redirect to customer1.taskifai.com/login?email=user@customer1.com
   - Complete login with password
   - Assert access to customer1 dashboard only

   **Integration Test: Super Admin Multi-Tenant Access**
   - Navigate to app.taskifai.com
   - Enter email "david@taskifai.com" (super admin)
   - Assert tenant selector displayed with demo, customer1, customer2
   - Select customer1
   - Assert redirect to customer1.taskifai.com
   - Assert access to customer1 data

   **Integration Test: Tenant Provisioning**
   - Call POST /api/admin/tenants with customer2 data
   - Assert tenant created in registry with encrypted credentials
   - Assert user_tenants entry created for admin
   - Navigate to customer2.taskifai.com/login
   - Assert successful login and data isolation

5. **Update CLAUDE.md incrementally** (O(1) operation):
   - Run: `.specify/scripts/bash/update-agent-context.sh claude`
   - Add: Tenant registry service patterns, user-tenant mapping, central login portal routing
   - Preserve: Existing vendor processing, AI chat, multi-tenant patterns
   - Update: Recent changes section with multi-tenant onboarding feature
   - Keep under 150 lines for token efficiency

**Output**: data-model.md, contracts/, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 design docs in TDD order:

   **Phase 1: Database & Schema (4 tasks)**
   - Deploy tenant registry Supabase database
   - Apply tenants_schema.sql
   - Create user_tenants mapping table
   - Seed demo tenant with encrypted credentials

   **Phase 2: Backend - Tenant Registry Service (6 tasks) [P]**
   - Create tenant registry service with encryption (tests first)
   - Implement tenant discovery service (tests first)
   - Add /discover-tenant endpoint contract tests
   - Implement /discover-tenant endpoint
   - Add admin tenant CRUD endpoint contract tests [P]
   - Implement admin tenant CRUD endpoints [P]

   **Phase 3: Backend - Middleware & Auth (4 tasks)**
   - Update TenantContextMiddleware to use registry (remove demo hardcoding)
   - Add super_admin role to JWT claims
   - Create super admin authorization middleware
   - Update config.py with registry database credentials

   **Phase 4: Frontend - Central Login Portal (6 tasks) [P]**
   - Create LoginPortal component contract tests
   - Implement LoginPortal page (email input + tenant discovery) [P]
   - Create TenantSelector component contract tests
   - Implement TenantSelector component (multi-tenant picker) [P]
   - Update App.tsx routing for app.taskifai.com
   - Modify Login.tsx to accept email query param [P]

   **Phase 5: Integration & Testing (5 tasks)**
   - Test regular user single-tenant login flow
   - Test super admin multi-tenant access flow
   - Test tenant provisioning end-to-end
   - Test data isolation between tenants
   - Verify audit logging for tenant operations

   **Phase 6: Security & Deployment (4 tasks)**
   - Update CORS for app.taskifai.com
   - Configure DNS wildcard for *.taskifai.com
   - Verify encryption at rest for tenant credentials
   - Security audit: subdomain spoofing prevention

**Ordering Strategy**:
- TDD order: Contract tests → Implementation → Integration tests
- Dependency order: Database schema → Backend services → Middleware → Frontend → Integration
- Mark [P] for parallel execution where files are independent

**Estimated Output**: 29 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Encrypted credentials not yet implemented | Tenant registry requires secure storage of database connection strings | Plaintext storage violates security principle III (Layer 0 isolation requires credential protection) |
| Super admin role not defined | Platform admin must access multiple tenant databases for support | Single-tenant admin insufficient for SaaS platform operations |
| Tenant provisioning not automated | Manual Supabase project creation doesn't scale beyond 5 customers | Manual process violates operational principle IV (scalable SaaS operations) |

**Mitigation Plan**:
1. Implement pgcrypto encryption functions for credential storage (Phase 2)
2. Add super_admin role to JWT claims and authorization middleware (Phase 3)
3. Automate tenant provisioning via Supabase Management API (Phase 6)

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅ research.md created
- [x] Phase 1: Design complete (/plan command) ✅ data-model.md, contracts/, quickstart.md, CLAUDE.md updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅ Task generation strategy documented
- [x] Phase 3: Tasks generated (/tasks command) ✅ tasks.md created with 41 implementation tasks
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: CONDITIONAL PASS (3 violations documented with mitigation)
- [x] Post-Design Constitution Check: PASS ✅ Design complies with constitutional requirements
- [x] All NEEDS CLARIFICATION resolved ✅ All technical unknowns researched and documented
- [x] Complexity deviations documented ✅ Mitigation plan in place for encryption, super admin, provisioning

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
