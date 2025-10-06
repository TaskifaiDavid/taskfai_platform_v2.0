# Phase 3.3: Implementation Guide - Make Tests Pass

**Status**: Ready to Begin
**Prerequisites**: Phase 3.2 Complete (All tests written)
**Objective**: Implement features to make all 28 test files pass
**Approach**: TDD Red-Green-Refactor cycle

## Quick Start

### 1. Environment Setup (30 minutes)

Create test environment configuration:

```bash
# Create .env.test file
cat > backend/.env.test << 'EOF'
# Application
SECRET_KEY=test_secret_key_for_jwt_signing_minimum_32_chars
DEBUG=True

# Database (Test)
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=test_anon_key
SUPABASE_SERVICE_KEY=test_service_key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db

# Redis (Test)
REDIS_URL=redis://localhost:6379/1

# OpenAI (Test - can use mock)
OPENAI_API_KEY=sk-test-key

# SendGrid (Test - can use mock)
SENDGRID_API_KEY=test_sendgrid_key
SENDGRID_FROM_EMAIL=test@taskifai.com
SENDGRID_FROM_NAME=TaskifAI Test
EOF

# Run tests to verify setup
cd backend
source venv/bin/activate
pytest tests/ -v --tb=short -x
```

### 2. Implementation Priority Order

Follow this sequence to incrementally pass tests:

#### Week 1: Multi-Tenant Infrastructure Core (T052-T063)

**Goal**: Make T064-T069 pass (multi-tenant core tests)

**Tasks**:
1. **T052**: Enhance Tenant model with encryption
   - File: `backend/app/models/tenant.py`
   - Add: `database_url`, `database_key`, `is_active` validation
   - Tests passing: None yet

2. **T053**: Create TenantRegistry service
   - File: `backend/app/services/tenant/registry.py`
   - CRUD operations for master tenant registry
   - Tests passing: T065 (subdomain routing) starts passing

3. **T054**: Implement subdomain→tenant lookup
   - File: `backend/app/core/tenant.py`
   - Replace demo hardcode with registry lookup
   - Tests passing: T065 fully passes

4. **T055**: Create tenant context middleware
   - File: `backend/app/middleware/tenant_context.py`
   - Extract subdomain, lookup tenant, inject into request.state
   - Tests passing: T064, T065 pass

5. **T056**: Create dynamic DB connection manager
   - File: `backend/app/core/db_manager.py`
   - Per-tenant connection pools (max 10)
   - 15-min credential cache
   - Tests passing: T067, T068 pass

6. **T057**: Implement credential encryption
   - File: `backend/app/core/security.py`
   - Add: `encrypt_credential()`, `decrypt_credential()`
   - AES-256 encryption
   - Tests passing: T069 passes

7. **T058**: Create auth middleware
   - File: `backend/app/middleware/auth.py`
   - Validate JWT, verify tenant_id matches
   - Tests passing: T064, T066 pass

8. **T059**: Update JWT token generation
   - File: `backend/app/core/security.py`
   - Include tenant_id and subdomain claims
   - Tests passing: T066 fully passes

**Validation**: Run `pytest tests/integration/test_multi_tenant*.py tests/unit/test_jwt*.py tests/security/test_credential*.py -v`

Expected: All T064-T069 tests should be GREEN ✅

---

#### Week 2: API Contract Tests Setup (T070-T084)

**Goal**: Set up API endpoint stubs to pass contract tests

**Tasks**:
1. **T121-T124**: Chat API endpoints
   - Files: `backend/app/api/chat.py`
   - POST /api/chat/query
   - GET /api/chat/history
   - DELETE /api/chat/history
   - Tests passing: T070-T072 pass

2. **T125-T130**: Dashboard API endpoints
   - Files: `backend/app/api/dashboards.py`
   - CRUD operations + set primary
   - Tests passing: T073-T077 pass

3. **T131-T134**: Analytics API endpoints
   - Files: `backend/app/api/analytics.py`
   - KPIs, sales, export
   - Tests passing: T078-T080 pass

4. **T135-T139**: Admin API endpoints
   - Files: `backend/app/api/admin.py`
   - Tenant management (create, list, suspend, reactivate)
   - Tests passing: T081-T084 pass

**Implementation Pattern** (Example for chat query):
```python
# backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException
from app.models.conversation import ChatQueryRequest, ChatQueryResponse
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/query", response_model=ChatQueryResponse)
async def chat_query(
    request: ChatQueryRequest,
    current_user = Depends(get_current_user)
):
    """Handle chat query - Phase 3.3 implementation"""
    # TODO: Implement AI chat logic
    return ChatQueryResponse(
        response="Implementation pending",
        sql_generated="SELECT 1",
        conversation_id="temp-id",
        timestamp="2025-10-06T10:00:00Z"
    )
```

**Validation**: Run `pytest tests/contract/ -v`

Expected: All contract tests should return 200/201 status codes (minimal implementation)

---

#### Week 3: AI Chat System (T109-T113)

**Goal**: Make T070-T072 and T088 fully pass

**Tasks**:
1. **T109**: Create LangGraph SQL agent
   - File: `backend/app/services/ai_chat/agent.py`
   - GPT-4o with SQL tool
   - MemorySaver checkpointer

2. **T110**: Create intent detection
   - File: `backend/app/services/ai_chat/intent.py`
   - Detect: online, offline, comparison, time, product, reseller

3. **T111**: Create query security validator
   - File: `backend/app/services/ai_chat/security.py`
   - Block: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE
   - Inject user_id filter
   - Parameterized queries only

4. **T112**: Create conversation memory service
   - File: `backend/app/services/ai_chat/memory.py`
   - Database-backed checkpointer
   - thread_id for sessions

5. **T113**: Install AI dependencies
   ```bash
   pip install langchain>=0.3.0 langchain-openai>=0.2.0 langgraph>=0.2.0
   ```

**Validation**: Run `pytest tests/contract/test_chat*.py tests/integration/test_ai_chat_flow.py tests/security/test_sql_injection.py -v`

Expected: Chat APIs fully functional, security tests pass

---

#### Week 4: Dashboard & Analytics Services (T114-T118)

**Goal**: Make T073-T080 and T089 fully pass

**Tasks**:
1. **T114-T115**: Dashboard management
   - File: `backend/app/services/dashboard/manager.py`
   - CRUD, URL validation, credential encryption

2. **T116**: KPI calculator
   - File: `backend/app/services/analytics/kpis.py`
   - Total revenue, units sold, top products

3. **T117**: Sales data aggregator
   - File: `backend/app/services/analytics/sales.py`
   - Filters: date, reseller, product, channel
   - Pagination

4. **T118**: Report generator
   - File: `backend/app/workers/report_generator.py`
   - PDF (ReportLab), CSV/Excel (pandas)

**Validation**: Run `pytest tests/contract/test_dashboards*.py tests/contract/test_analytics*.py tests/integration/test_dashboard*.py -v`

Expected: Dashboard and analytics fully functional

---

#### Week 5: Admin & Tenant Management (T119-T120, T135-T139)

**Goal**: Make T081-T084 and T090 fully pass

**Tasks**:
1. **T119**: Tenant provisioner
   - File: `backend/app/services/tenant/provisioner.py`
   - Supabase Management API client
   - Create project, run migrations, seed configs

2. **T120**: Tenant suspension service
   - File: `backend/app/services/tenant/manager.py`
   - Set is_active=false
   - Invalidate connections
   - Audit logging

**Validation**: Run `pytest tests/contract/test_admin*.py tests/integration/test_tenant_provisioning.py -v`

Expected: Admin APIs fully functional, tenant provisioning works

---

#### Week 6: Security Hardening (T085-T087)

**Goal**: Make all security tests pass

**Tasks**:
1. Verify SQL injection prevention (T085)
   - Test all malicious query patterns
   - Ensure all blocked or sanitized

2. Verify RLS policies (T086)
   - Test user_id filtering on all queries
   - Verify no cross-user data leakage

3. Verify subdomain spoofing prevention (T087)
   - Test all malicious subdomain patterns
   - Ensure JWT tenant_id matches subdomain

**Validation**: Run `pytest tests/security/ -v`

Expected: All security tests GREEN ✅

---

#### Week 7: Integration Testing & Bug Fixes (T088-T091)

**Goal**: Make all integration tests pass

**Tasks**:
1. Test complete AI chat flow (T088)
2. Test dashboard embedding flow (T089)
3. Test tenant provisioning flow (T090)
4. Test report generation flow (T091)
5. Fix any bugs discovered during integration testing

**Validation**: Run `pytest tests/integration/ -v`

Expected: All integration tests GREEN ✅

---

#### Week 8: Final Validation & Cleanup

**Goal**: All tests pass, production ready

**Tasks**:
1. Run complete test suite
   ```bash
   pytest tests/ -v --cov=app --cov-report=html
   ```

2. Verify test coverage >80%

3. Fix remaining failures

4. Clean up TODOs and temporary code

5. Update documentation

**Validation**: Run `pytest tests/ -v`

Expected: **ALL 200+ tests GREEN ✅**

---

## TDD Development Workflow

### Daily Cycle

```bash
# 1. Pick next failing test
pytest tests/contract/test_chat_query.py::TestChatQueryContract::test_chat_query_success_response -v

# 2. Read the test - understand what it expects

# 3. Implement minimal code to make it pass

# 4. Run test again
pytest tests/contract/test_chat_query.py::TestChatQueryContract::test_chat_query_success_response -v

# 5. If GREEN: Refactor and move to next test
# 6. If RED: Debug and iterate

# 7. Run related tests to ensure no regressions
pytest tests/contract/test_chat*.py -v
```

### Red-Green-Refactor

1. **RED**: Test fails (current state for all tests)
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Clean up code while keeping test green

### Commit Strategy

```bash
# Commit after each test passes
git add .
git commit -m "feat: implement chat query endpoint - T070 passing"

# Push after each major milestone
git push origin 001-read-the-documents
```

## Success Criteria

- [ ] All 28 test files pass (200+ test cases)
- [ ] Test coverage >80%
- [ ] No failing tests
- [ ] All security tests pass
- [ ] All integration tests pass
- [ ] Documentation updated
- [ ] Ready for Phase 4 (Frontend)

## Troubleshooting

### Common Issues

**Issue**: Tests fail with import errors
**Fix**: Ensure all dependencies in requirements.txt installed

**Issue**: Database connection errors
**Fix**: Check .env.test configuration, ensure test DB exists

**Issue**: JWT validation fails
**Fix**: Verify SECRET_KEY in .env.test, check token generation logic

**Issue**: Subdomain routing fails
**Fix**: Check middleware order in main.py, verify tenant registry

**Issue**: Security tests fail
**Fix**: Review security.py implementations, ensure all keywords blocked

## Getting Help

- Review test file for expected behavior
- Check existing implementation in Phase 1 code
- Refer to design documents in `/specs/001-read-the-documents/`
- Run individual tests with `-vv` for detailed output

## Next Steps After Phase 3.3

Once all tests pass:
1. **Phase 3.4**: Frontend implementation
2. **Phase 3.5**: Integration & Polish
3. **Production Deployment**: Deploy to staging environment
4. **User Acceptance Testing**: Validate with stakeholders
