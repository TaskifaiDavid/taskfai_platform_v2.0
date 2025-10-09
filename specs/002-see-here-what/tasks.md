# Tasks: Multi-Tenant Customer Onboarding System

**Input**: Design documents from `/home/david/TaskifAI_platform_v2.0/specs/002-see-here-what/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/ (all available)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Loaded: Tech stack FastAPI/React 19, web app structure
2. Load optional design documents:
   → ✅ data-model.md: 4 entities (Tenant, UserTenant, TenantConfig, TenantAuditLog)
   → ✅ contracts/: 2 files (tenant-discovery.yaml, tenant-registry.yaml)
   → ✅ research.md: 6 technical decisions documented
3. Generate tasks by category:
   → Setup: Database deployment, env config, dependencies
   → Tests: 2 contract tests, 5 integration tests, multi-tenant isolation
   → Core: 4 models, 2 services, 2 API endpoints, middleware, frontend
   → Integration: Encryption, CORS, DNS, audit logging
   → Polish: Security audit, performance, documentation
4. Apply task rules:
   → Different files = marked [P] for parallel
   → Same file = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T041)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → ✅ All contracts have tests (2/2)
   → ✅ All entities have models (4/4)
   → ✅ All endpoints implemented (8/8)
9. Return: SUCCESS (41 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- Web app structure: `backend/app/`, `frontend/src/`
- Tests: `backend/tests/`, `frontend/tests/`
- Database: `backend/db/`

---

## Phase 3.1: Setup & Database

### Database Deployment
- [ ] **T001** Deploy tenant registry Supabase database
  - Create new Supabase project: "TaskifAI Tenant Registry"
  - Region: us-east-1
  - Copy URL, anon_key, service_key to .env
  - Path: External (Supabase dashboard)

- [ ] **T002** Apply tenant registry schema
  - Execute `backend/db/tenants_schema.sql` in Supabase SQL Editor
  - Verify tables created: tenants, tenant_configs, tenant_audit_log
  - Verify encryption functions: encrypt_data(), decrypt_data()
  - Path: `backend/db/tenants_schema.sql`

- [ ] **T003** Create user_tenants mapping table
  - Create SQL file `backend/db/user_tenants.sql`:
    ```sql
    CREATE TABLE user_tenants (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      email VARCHAR(255) NOT NULL,
      tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
      role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('member', 'admin', 'super_admin')),
      created_at TIMESTAMPTZ DEFAULT NOW(),
      UNIQUE(email, tenant_id)
    );
    CREATE INDEX idx_user_tenants_email ON user_tenants(email);
    CREATE INDEX idx_user_tenants_tenant ON user_tenants(tenant_id);
    ```
  - Execute in Supabase SQL Editor
  - Path: `backend/db/user_tenants.sql` (NEW)

- [ ] **T004** Seed demo tenant with encrypted credentials
  - Create `backend/db/seed_demo_tenant.sql`
  - Encrypt demo Supabase credentials using encrypt_data()
  - Insert demo tenant into registry
  - Insert user_tenants mapping: david@taskifai.com → demo → super_admin
  - Path: `backend/db/seed_demo_tenant.sql` (NEW)

### Backend Configuration
- [ ] **T005** Add tenant registry database config
  - Update `backend/app/core/config.py`
  - Add fields: TENANT_REGISTRY_URL, TENANT_REGISTRY_ANON_KEY, TENANT_REGISTRY_SERVICE_KEY
  - Load from environment variables
  - Path: `backend/app/core/config.py`

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (Parallel)
- [ ] **T006 [P]** Contract test: POST /api/auth/discover-tenant
  - Create `backend/tests/contract/test_tenant_discovery_contract.py`
  - Test request schema: `{ "email": "user@example.com" }`
  - Test single tenant response: `{ "subdomain", "company_name", "redirect_url" }`
  - Test multi-tenant response: `{ "tenants": [...] }`
  - Test 404 error: "No tenant found for this email"
  - Path: `backend/tests/contract/test_tenant_discovery_contract.py` (NEW)

- [ ] **T007 [P]** Contract test: Tenant admin endpoints
  - Create `backend/tests/contract/test_tenant_registry_contract.py`
  - Test POST /api/admin/tenants (create tenant)
  - Test GET /api/admin/tenants (list tenants)
  - Test GET /api/admin/tenants/{id} (get tenant)
  - Test PATCH /api/admin/tenants/{id} (update tenant)
  - Test POST /api/admin/tenants/{id}/users (add user)
  - All require super_admin role in JWT
  - Path: `backend/tests/contract/test_tenant_registry_contract.py` (NEW)

### Multi-Tenant Isolation Tests (Parallel)
- [ ] **T008 [P]** Tenant isolation test: Customer A cannot access Customer B data
  - Create `backend/tests/integration/test_tenant_isolation.py`
  - Login as customer1 user → upload data → verify visible
  - Login as customer2 user → verify customer1 data NOT visible
  - Attempt cross-tenant API call → verify fails
  - Path: `backend/tests/integration/test_tenant_isolation.py` (NEW)

- [ ] **T009 [P]** Subdomain routing test: Extract and validate tenant context
  - Create `backend/tests/integration/test_subdomain_routing.py`
  - Mock request with Host: customer1.taskifai.com
  - Verify TenantContextMiddleware extracts subdomain="customer1"
  - Verify tenant context injected into request.state.tenant
  - Test demo/localhost fallback
  - Path: `backend/tests/integration/test_subdomain_routing.py` (NEW)

- [ ] **T010 [P]** JWT tenant claims test: Verify tenant_id in token
  - Create `backend/tests/integration/test_jwt_tenant_claims.py`
  - Generate JWT with tenant_id, subdomain, role claims
  - Decode and verify claims present
  - Test token validation enforces tenant_id
  - Test super_admin role in token
  - Path: `backend/tests/integration/test_jwt_tenant_claims.py` (NEW)

- [ ] **T011 [P]** Database connection scoping test: Verify tenant-specific DB routing
  - Create `backend/tests/integration/test_database_scoping.py`
  - Create TenantContext for customer1
  - Get Supabase client → verify connected to customer1 database
  - Create TenantContext for customer2
  - Get Supabase client → verify connected to customer2 database
  - Verify clients are isolated (different connection pools)
  - Path: `backend/tests/integration/test_database_scoping.py` (NEW)

### Integration Tests from User Stories (Parallel)
- [ ] **T012 [P]** Integration test: Regular user single-tenant login flow
  - Create `backend/tests/integration/test_regular_user_login.py`
  - POST /auth/discover-tenant with user@customer1.com
  - Assert single tenant response with redirect_url
  - Follow redirect → complete login
  - Assert JWT has tenant_id=customer1
  - Path: `backend/tests/integration/test_regular_user_login.py` (NEW)

- [ ] **T013 [P]** Integration test: Super admin multi-tenant access
  - Create `backend/tests/integration/test_super_admin_access.py`
  - POST /auth/discover-tenant with david@taskifai.com
  - Assert multi-tenant response with tenant selector
  - Select demo tenant → redirect → login
  - Assert JWT has tenant_id=demo, role=super_admin
  - Verify can access demo data
  - Path: `backend/tests/integration/test_super_admin_access.py` (NEW)

- [ ] **T014 [P]** Integration test: New tenant provisioning flow
  - Create `backend/tests/integration/test_tenant_provisioning.py`
  - Super admin calls POST /api/admin/tenants
  - Assert tenant created in registry with encrypted credentials
  - Assert user_tenants mapping created
  - Test login to new tenant subdomain
  - Assert data isolation from other tenants
  - Path: `backend/tests/integration/test_tenant_provisioning.py` (NEW)

### Frontend Tests (Parallel)
- [ ] **T015 [P]** Frontend test: Central login portal component
  - Create `frontend/tests/integration/test_login_portal.spec.ts`
  - Render LoginPortal component
  - Enter email → click Continue
  - Mock /discover-tenant API response
  - Verify redirect for single tenant
  - Verify tenant selector for multi-tenant
  - Path: `frontend/tests/integration/test_login_portal.spec.ts` (NEW)

- [ ] **T016 [P]** Frontend test: Tenant selector component
  - Create `frontend/tests/integration/test_tenant_selector.spec.ts`
  - Render TenantSelector with multiple tenants
  - Click on tenant option
  - Verify redirect to subdomain login
  - Verify email passed in query param
  - Path: `frontend/tests/integration/test_tenant_selector.spec.ts` (NEW)

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Backend Models (Parallel)
- [ ] **T017 [P]** Tenant model in Pydantic
  - Create `backend/app/models/tenant.py`
  - Define TenantCreate, TenantUpdate, TenantResponse models
  - Include validation: subdomain pattern, email format
  - Path: `backend/app/models/tenant.py` (NEW)

- [ ] **T018 [P]** UserTenant model in Pydantic
  - Create `backend/app/models/user_tenant.py`
  - Define UserTenantCreate, UserTenantResponse models
  - Role enum: member, admin, super_admin
  - Path: `backend/app/models/user_tenant.py` (NEW)

### Backend Services (Sequential - shared DB access patterns)
- [ ] **T019** Tenant registry service with encryption
  - Create `backend/app/services/tenant/registry.py`
  - Implement TenantRegistryService class
  - Methods: create_tenant(), get_by_subdomain(), list_tenants(), update_tenant()
  - Integrate pgcrypto encrypt_data() for credentials
  - Integrate pgcrypto decrypt_data() for credentials
  - Connect to tenant registry Supabase database
  - Path: `backend/app/services/tenant/registry.py` (NEW)

- [ ] **T020** Tenant discovery service
  - Create `backend/app/services/tenant/discovery.py`
  - Implement TenantDiscoveryService class
  - Method: discover_tenants_by_email(email) → queries user_tenants
  - Returns single tenant with redirect_url OR multiple tenants for selector
  - Handle email not found → raise 404
  - Path: `backend/app/services/tenant/discovery.py` (NEW)

### Backend API Endpoints (Sequential - same file)
- [ ] **T021** POST /api/auth/discover-tenant endpoint
  - Update `backend/app/api/auth.py`
  - Add discover_tenant route
  - Use TenantDiscoveryService
  - Return SingleTenantResponse or MultiTenantResponse
  - Include rate limiting (prevent email enumeration)
  - Path: `backend/app/api/auth.py`

- [ ] **T022** Tenant admin endpoints (super admin only)
  - Create `backend/app/api/admin/tenants.py`
  - POST /api/admin/tenants - create tenant (requires super_admin)
  - GET /api/admin/tenants - list tenants (requires super_admin)
  - GET /api/admin/tenants/{id} - get tenant details
  - PATCH /api/admin/tenants/{id} - update tenant (activate/suspend)
  - POST /api/admin/tenants/{id}/users - add user to tenant
  - All endpoints require super_admin role in JWT
  - Path: `backend/app/api/admin/tenants.py` (NEW)

### Backend Middleware & Auth Enhancement
- [ ] **T023** Update TenantContextMiddleware to use registry
  - Update `backend/app/middleware/tenant_context.py`
  - Remove demo hardcoded fallback
  - Always query tenant registry for subdomain lookup
  - Use TenantRegistryService.get_by_subdomain()
  - Decrypt credentials and create TenantContext
  - Path: `backend/app/middleware/tenant_context.py`

- [ ] **T024** Add super_admin role to JWT claims
  - Update `backend/app/core/security.py` (or auth.py if JWT logic there)
  - Modify create_access_token() to include role claim
  - Add get_user_role() function to determine role from user_tenants
  - JWT payload: `{ "sub": user_id, "tenant_id": ..., "subdomain": ..., "role": ... }`
  - Path: `backend/app/core/security.py` (or appropriate auth file)

- [ ] **T025** Create super admin authorization dependency
  - Create `backend/app/api/dependencies.py` (if not exists)
  - Add require_super_admin() dependency
  - Extract role from JWT token
  - Raise 403 if role != "super_admin"
  - Path: `backend/app/api/dependencies.py` (NEW or update existing)

### Frontend Components (Parallel)
- [ ] **T026 [P]** Central login portal page
  - Create `frontend/src/pages/LoginPortal.tsx`
  - Email input form
  - Call POST /api/auth/discover-tenant
  - Handle single tenant → auto redirect to subdomain
  - Handle multiple tenants → show TenantSelector
  - Handle 404 → display error message
  - Path: `frontend/src/pages/LoginPortal.tsx` (NEW)

- [ ] **T027 [P]** Tenant selector component
  - Create `frontend/src/components/auth/TenantSelector.tsx`
  - Display list of tenants (company_name, subdomain)
  - Click handler → redirect to https://{subdomain}.taskifai.com/login?email={email}
  - Validate redirect URL before navigation (prevent open redirect)
  - Path: `frontend/src/components/auth/TenantSelector.tsx` (NEW)

- [ ] **T028 [P]** Tenant discovery API client
  - Create `frontend/src/api/tenant.ts`
  - discoverTenant(email) function
  - Call POST /api/auth/discover-tenant
  - Type definitions for SingleTenantResponse, MultiTenantResponse
  - Path: `frontend/src/api/tenant.ts` (NEW)

### Frontend Routing & Integration
- [ ] **T029** Update App routing for central portal
  - Update `frontend/src/App.tsx`
  - Detect hostname: if app.taskifai.com or localhost → show LoginPortal
  - Else (subdomain) → show existing MainApp
  - Path: `frontend/src/App.tsx`

- [ ] **T030** Modify Login page to accept email query param
  - Update `frontend/src/pages/Login.tsx`
  - Extract email from query params using useSearchParams()
  - Pass pre-filled email to LoginForm component
  - Path: `frontend/src/pages/Login.tsx`

- [ ] **T031** Update LoginForm to pre-fill email
  - Update `frontend/src/components/auth/LoginForm.tsx`
  - Accept initialEmail prop
  - Pre-fill email input if initialEmail provided
  - Path: `frontend/src/components/auth/LoginForm.tsx`

---

## Phase 3.4: Integration & Security

- [ ] **T032** Update CORS for app.taskifai.com and subdomains
  - Update `backend/app/main.py` (or wherever CORS configured)
  - Use allow_origin_regex: `r"https://([a-z0-9-]+\.)?taskifai\.com"`
  - Enable allow_credentials=True for cookie/token transmission
  - Path: `backend/app/main.py`

- [ ] **T033** Tenant database credential encryption integration
  - Verify encrypt_data() used in TenantRegistryService.create_tenant()
  - Verify decrypt_data() used in TenantRegistryService.get_by_subdomain()
  - Test encryption round-trip with actual SECRET_KEY
  - Path: Validation in `backend/app/services/tenant/registry.py`

- [ ] **T034** Connection pool management per tenant
  - Create `backend/app/core/tenant_db_manager.py`
  - TenantDatabaseManager class with client cache (tenant_id → Supabase client)
  - get_client(tenant_context) method
  - Lazy initialization of clients (only when needed)
  - Path: `backend/app/core/tenant_db_manager.py` (NEW)

- [ ] **T035** User-tenant mapping audit logging
  - Update `backend/db/user_tenants.sql` to add trigger
  - Log user_added, user_removed, role_changed actions
  - Insert into tenant_audit_log table
  - Path: `backend/db/user_tenants.sql`

---

## Phase 3.5: Polish & Validation

### Security & Compliance
- [ ] **T036** Security audit: Subdomain spoofing prevention
  - Review TenantContextMiddleware subdomain extraction
  - Verify subdomain regex validation prevents injection
  - Test with malicious subdomains: `../admin`, `<script>`, `customer1--admin`
  - Path: Manual security testing + `backend/app/middleware/tenant_context.py`

- [ ] **T037** Verify constitutional compliance
  - ✅ Database-per-tenant isolation (check connection scoping)
  - ✅ Encrypted credentials at rest (check pgcrypto integration)
  - ✅ Super admin role implemented (check JWT claims + middleware)
  - ✅ Audit logging for tenant operations (check triggers)
  - ✅ Defense-in-depth security (all 7 layers)
  - Path: Manual verification against `.specify/memory/constitution.md`

- [ ] **T038** Rate limiting on tenant discovery endpoint
  - Add rate limiting to POST /api/auth/discover-tenant
  - Limit: 10 requests per minute per IP
  - Prevents email enumeration attacks
  - Path: `backend/app/api/auth.py` (add rate limiting middleware)

### Performance & Testing
- [ ] **T039** Performance test: Tenant discovery <2s
  - Load test POST /api/auth/discover-tenant
  - 100 concurrent requests
  - Verify p99 < 2000ms
  - Path: `backend/tests/performance/test_tenant_discovery_load.py` (NEW)

- [ ] **T040** Execute quickstart validation scenarios
  - Run all scenarios from `specs/002-see-here-what/quickstart.md`
  - Scenario 1: Regular user login ✅
  - Scenario 2: Super admin multi-tenant ✅
  - Scenario 3: Tenant provisioning ✅
  - Scenario 4: Data isolation ✅
  - Scenario 5: Audit trail ✅
  - Path: Manual execution following `specs/002-see-here-what/quickstart.md`

### Documentation
- [ ] **T041** Update CLAUDE.md with multi-tenant patterns
  - Already done via update-agent-context.sh
  - Verify: Tenant registry patterns documented
  - Verify: User-tenant mapping explained
  - Verify: Central login portal flow described
  - Path: `CLAUDE.md` (already updated)

---

## Dependencies

**Critical Path**:
- T001-T005 (Setup) → T006-T016 (Tests) → T017-T031 (Implementation) → T032-T035 (Integration) → T036-T041 (Polish)

**Detailed Dependencies**:
- **T006-T016** (All tests) must complete BEFORE any implementation (T017-T031)
- **T001-T004** (Database setup) blocks T006-T016 (tests need DB schema)
- **T005** (Config) blocks T019 (registry service needs config)
- **T019** (Registry service) blocks T020 (discovery service uses registry)
- **T019** (Registry service) blocks T023 (middleware uses registry)
- **T020** (Discovery service) blocks T021 (endpoint uses service)
- **T017-T018** (Models) blocks T019-T020 (services use models)
- **T024** (JWT role) blocks T025 (super admin dependency uses JWT)
- **T025** (Super admin dependency) blocks T022 (admin endpoints use dependency)
- **T021** (Discover endpoint) blocks T026 (portal calls endpoint)
- **T028** (API client) blocks T026 (portal uses API client)
- **T026-T027** (Components) blocks T029 (routing uses components)
- **T029** (Routing) blocks T030-T031 (login flow uses routing)
- **T032-T035** (Integration) blocks T036-T041 (Polish needs working system)

**Parallel Execution Opportunities**:
- T006-T007 (Contract tests - different files)
- T008-T011 (Isolation tests - different files)
- T012-T016 (Integration tests - different files)
- T017-T018 (Models - different files)
- T026-T028 (Frontend components - different files)

---

## Parallel Execution Examples

### Phase 1: Contract Tests (T006-T007)
```bash
# Launch both contract tests in parallel
Task: "Contract test POST /api/auth/discover-tenant in backend/tests/contract/test_tenant_discovery_contract.py"
Task: "Contract test: Tenant admin endpoints in backend/tests/contract/test_tenant_registry_contract.py"
```

### Phase 2: Multi-Tenant Isolation Tests (T008-T011)
```bash
# Launch all isolation tests in parallel
Task: "Tenant isolation test: Customer A cannot access Customer B data in backend/tests/integration/test_tenant_isolation.py"
Task: "Subdomain routing test in backend/tests/integration/test_subdomain_routing.py"
Task: "JWT tenant claims test in backend/tests/integration/test_jwt_tenant_claims.py"
Task: "Database connection scoping test in backend/tests/integration/test_database_scoping.py"
```

### Phase 3: User Story Integration Tests (T012-T016)
```bash
# Launch all user story tests in parallel
Task: "Integration test: Regular user login in backend/tests/integration/test_regular_user_login.py"
Task: "Integration test: Super admin access in backend/tests/integration/test_super_admin_access.py"
Task: "Integration test: Tenant provisioning in backend/tests/integration/test_tenant_provisioning.py"
Task: "Frontend test: Login portal in frontend/tests/integration/test_login_portal.spec.ts"
Task: "Frontend test: Tenant selector in frontend/tests/integration/test_tenant_selector.spec.ts"
```

### Phase 4: Backend Models (T017-T018)
```bash
# Launch model creation in parallel
Task: "Create Tenant Pydantic model in backend/app/models/tenant.py"
Task: "Create UserTenant Pydantic model in backend/app/models/user_tenant.py"
```

### Phase 5: Frontend Components (T026-T028)
```bash
# Launch frontend components in parallel
Task: "Create LoginPortal page in frontend/src/pages/LoginPortal.tsx"
Task: "Create TenantSelector component in frontend/src/components/auth/TenantSelector.tsx"
Task: "Create tenant API client in frontend/src/api/tenant.ts"
```

---

## Notes

- **[P] tasks** = different files, no dependencies, can run in parallel
- **TDD Critical**: All tests (T006-T016) MUST fail before implementation starts
- **Commit Strategy**: Commit after each task completion for rollback capability
- **Multi-Tenant Focus**: All tests must verify tenant isolation and security
- **Constitutional Compliance**: T037 validates all 4 constitutional principles
- **Performance Targets**: T039 verifies <2s tenant discovery requirement

---

## Task Generation Rules Applied

1. **From Contracts**:
   - ✅ tenant-discovery.yaml → T006 (contract test)
   - ✅ tenant-registry.yaml → T007 (contract test)
   - ✅ POST /auth/discover-tenant → T021 (implementation)
   - ✅ 5 admin endpoints → T022 (implementation)

2. **From Data Model**:
   - ✅ Tenant entity → T017 (Pydantic model)
   - ✅ UserTenant entity → T018 (Pydantic model)
   - ✅ TenantConfig (exists in schema, no new code)
   - ✅ TenantAuditLog (exists in schema, trigger in T035)
   - ✅ Relationships → T019-T020 (services)

3. **From User Stories** (quickstart.md):
   - ✅ Scenario 1 (regular user) → T012 (integration test)
   - ✅ Scenario 2 (super admin) → T013 (integration test)
   - ✅ Scenario 3 (provisioning) → T014 (integration test)
   - ✅ Scenario 4 (isolation) → T008 (integration test)
   - ✅ Scenario 5 (audit) → T035 (audit logging)

4. **Ordering**:
   - ✅ Setup (T001-T005) → Tests (T006-T016) → Models (T017-T018) → Services (T019-T020) → Endpoints (T021-T022) → Middleware (T023-T025) → Frontend (T026-T031) → Integration (T032-T035) → Polish (T036-T041)

---

## Validation Checklist

- [x] All contracts have corresponding tests (2/2)
- [x] All entities have model tasks (4/4 - 2 new Pydantic, 2 existing DB)
- [x] All tests come before implementation (T006-T016 before T017-T031)
- [x] Parallel tasks truly independent (verified file paths)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Multi-tenant isolation tests included (T008-T011)
- [x] Security tests included (T036-T038)
- [x] Performance tests included (T039)
- [x] Constitutional compliance verification (T037)

---

**Total Tasks**: 41
**Estimated Completion Time**: 3.5-4.5 hours (as per original plan)
**Ready for Execution**: ✅ All tasks are specific, actionable, and dependency-ordered
