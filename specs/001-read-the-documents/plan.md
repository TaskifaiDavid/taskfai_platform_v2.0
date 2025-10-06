# Implementation Plan: TaskifAI Multi-Tenant SaaS Platform

**Branch**: `001-read-the-documents` | **Date**: 2025-10-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/home/david/TaskifAI_platform_v2.0/specs/001-read-the-documents/spec.md`

## Summary

TaskifAI is a multi-tenant SaaS platform for retail and distribution companies to centralize, clean, and analyze sales data from multiple third-party resellers. The platform provides:

- **Database-per-tenant isolation** with subdomain routing for maximum security
- **Automated vendor format detection** and configurable data processing (9+ formats)
- **AI-powered natural language querying** with SQL injection prevention
- **External dashboard embedding** (Looker, Tableau, Power BI, Metabase)
- **Multi-channel analytics** for online (D2C) and offline (B2B) sales
- **Email notifications** and automated reporting
- **Tenant provisioning and management** via secure admin API

**Technical Approach**: Web application with React 19 frontend, FastAPI backend, Celery background workers, Supabase PostgreSQL 17 database-per-tenant, OpenAI GPT-4 for AI chat, and configuration-driven vendor processing engine.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.7+ (frontend), Node.js 20.19+
**Primary Dependencies**: FastAPI 0.115+, React 19, Vite 6, Supabase PostgreSQL 17, LangChain 0.3+, LangGraph 0.2+, OpenAI GPT-4o, Celery, Redis
**Storage**: Supabase PostgreSQL 17 (database-per-tenant model), Redis (task queue + cache)
**Testing**: pytest + pytest-asyncio + httpx (backend), Vitest (frontend)
**Target Platform**: Web (modern browsers - Baseline Widely Available), Linux server (backend)
**Project Type**: web (frontend + backend + background worker)
**Performance Goals**:
- File processing: 1-2 minutes for 500-5000 rows
- AI chat: <5 seconds average response time
- Dashboard loading: <3 seconds (network permitting)
- API endpoints: <200ms p95 latency

**Constraints**:
- Multi-tenant: Each customer MUST have isolated database
- File uploads: Maximum 100MB per file
- Concurrent connections: Max 10 per tenant database
- Security: Defense-in-depth 7-layer model required
- Configuration: Vendor processing via config, no code deployments

**Scale/Scope**:
- Target: 100-500 tenants initially, scaling to 1000+
- Per-tenant: 10-100 users, 100k-1M sales records per year
- Vendors: 9+ supported formats with extensible configuration system
- Features: 64 functional requirements across 7 epics

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Multi-Tenant Security Architecture
- [x] Feature uses database-per-tenant isolation (no shared database patterns)
- [x] Subdomain routing properly extracts and validates tenant context
- [x] JWT tokens include tenant_id and subdomain claims
- [x] All database connections are tenant-scoped via middleware
- [x] Cross-tenant data access is physically impossible
- [x] Tenant credentials are encrypted at rest

### II. Configuration-Driven Flexibility
- [x] Vendor-specific logic uses configuration, not hardcoded rules
- [x] Tenant configurations stored in tenant database (vendor_configs table)
- [x] Changes require configuration updates only, not code deployment
- [x] System supports configuration inheritance and override

### III. Defense-in-Depth Security
- [x] Physical database isolation enforced (Layer 0)
- [x] HTTPS/TLS and subdomain validation implemented (Layer 1-2)
- [x] JWT authentication with tenant claims (Layer 3)
- [x] Tenant-specific database routing (Layer 4)
- [x] RLS policies on all tenant database tables (Layer 5)
- [x] Input validation prevents SQL injection (Layer 6)
- [x] Audit logging per tenant (Layer 7)
- [x] AI chat queries: blocked SQL keywords, read-only access, parameterized queries

### IV. Scalable SaaS Operations
- [x] Tenant provisioning is automated and secure
- [x] Independent tenant scaling supported
- [x] Connection pooling isolated per tenant
- [x] Clear separation between platform admin and tenant admin functions
- [x] Per-tenant monitoring and audit logs

### Technology Stack Compliance
- [x] Backend uses FastAPI (Python 3.11+)
- [x] Frontend uses React 19 + TypeScript + Vite 6
- [x] Database uses Supabase PostgreSQL 17 with RLS
- [x] No prohibited patterns: shared database, client-side tenant validation, hardcoded configs

**Constitutional Compliance**: ✅ PASS - All principles satisfied by design

## Project Structure

### Documentation (this feature)
```
specs/001-read-the-documents/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── auth.openapi.yaml
│   ├── uploads.openapi.yaml
│   ├── chat.openapi.yaml
│   ├── dashboards.openapi.yaml
│   ├── analytics.openapi.yaml
│   └── admin.openapi.yaml
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── app/
│   ├── api/                    # FastAPI routes
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── uploads.py         # File upload endpoints
│   │   ├── chat.py            # AI chat endpoints
│   │   ├── dashboards.py      # Dashboard management endpoints
│   │   ├── analytics.py       # Analytics endpoints
│   │   └── admin.py           # Platform admin endpoints
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Settings (Pydantic v2)
│   │   ├── security.py        # JWT, password hashing
│   │   ├── dependencies.py    # Dependency injection
│   │   ├── tenant.py          # Tenant context management
│   │   └── db_manager.py      # Multi-tenant DB connection manager
│   ├── models/                 # Pydantic models
│   │   ├── user.py
│   │   ├── upload.py
│   │   ├── sales.py
│   │   ├── conversation.py
│   │   ├── dashboard.py
│   │   └── tenant.py
│   ├── middleware/             # Request middleware
│   │   ├── tenant_context.py  # Subdomain extraction and routing
│   │   ├── auth.py            # JWT validation
│   │   └── logging.py         # Request/response logging
│   ├── services/               # Business logic
│   │   ├── vendors/           # Vendor-specific processors
│   │   │   ├── base.py        # Base vendor processor
│   │   │   ├── config_loader.py  # Load tenant vendor configs
│   │   │   ├── detector.py    # Auto-detect vendor format
│   │   │   └── processors/    # Vendor implementations
│   │   ├── ai_chat/           # LangChain + LangGraph agents
│   │   │   ├── agent.py       # SQL agent with memory
│   │   │   ├── intent.py      # Intent detection
│   │   │   └── security.py    # Query validation
│   │   ├── email/             # Email service
│   │   │   ├── sender.py      # SendGrid integration
│   │   │   └── templates/     # HTML email templates
│   │   └── tenant/            # Tenant management
│   │       ├── provisioner.py # Automated tenant provisioning
│   │       └── registry.py    # Master tenant registry
│   ├── workers/                # Celery tasks
│   │   ├── celery_app.py      # Celery configuration
│   │   ├── file_processor.py  # Async file processing
│   │   └── report_generator.py # Report generation
│   └── main.py                 # FastAPI application entry
├── tests/
│   ├── contract/               # Contract tests
│   ├── integration/            # Integration tests (multi-tenant)
│   └── unit/                   # Unit tests
├── requirements.txt
├── Dockerfile
└── README.md

frontend/
├── src/
│   ├── components/             # React components
│   │   ├── auth/              # Login, signup
│   │   ├── upload/            # File upload with react-dropzone
│   │   ├── chat/              # AI chat UI
│   │   ├── dashboard/         # Dashboard embedding (iframe)
│   │   ├── analytics/         # Analytics widgets
│   │   └── ui/                # shadcn/ui components
│   ├── pages/                  # Page components
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Uploads.tsx
│   │   ├── Chat.tsx
│   │   └── Analytics.tsx
│   ├── hooks/                  # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useTenant.ts       # Tenant context
│   │   └── useChat.ts
│   ├── lib/                    # Utilities
│   │   ├── api.ts             # API client with tenant headers
│   │   ├── utils.ts
│   │   └── tenant.ts          # Subdomain extraction
│   ├── stores/                 # Zustand stores
│   │   ├── auth.ts            # Auth state
│   │   └── ui.ts              # UI state (modals, sidebar)
│   ├── api/                    # TanStack Query hooks
│   │   ├── auth.ts
│   │   ├── uploads.ts
│   │   ├── chat.ts
│   │   └── dashboards.ts
│   ├── App.tsx
│   └── main.tsx
├── tests/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── Dockerfile
```

**Structure Decision**: Web application with decoupled frontend and backend. Backend serves RESTful API + WebSocket for real-time updates. Frontend is SPA with client-side routing. Background worker handles async file processing and report generation. Database-per-tenant model requires dynamic connection management.

## Phase 0: Outline & Research

**Purpose**: Validate technology choices, establish patterns, resolve any remaining uncertainties.

### Research Tasks

1. **Multi-Tenant Database Architecture**
   - Decision: Database-per-tenant vs schema-per-tenant vs row-per-tenant
   - Rationale: Database-per-tenant chosen for maximum isolation, compliance, independent scaling
   - Alternatives considered: Shared database with RLS (rejected - insufficient isolation for SaaS)
   - Implementation: Supabase project per tenant ($25/month per tenant)

2. **Subdomain Routing Strategy**
   - Decision: Wildcard DNS (*.taskifai.com) + middleware extraction
   - Rationale: Simple, scalable, works with any hosting provider
   - Alternatives considered: Path-based routing /tenant/{id}/ (rejected - less professional)
   - Implementation: Vercel wildcard DNS → Backend extracts subdomain from hostname

3. **Connection Pool Management**
   - Decision: Per-tenant connection pools with 10 max connections, 15-min credential cache
   - Rationale: Prevents connection exhaustion, enables tenant isolation
   - Alternatives considered: Single global pool (rejected - no isolation), unlimited (rejected - resource exhaustion)
   - Implementation: Custom TenantConnectionManager class with asyncpg pools

4. **Vendor Configuration Storage**
   - Decision: JSON column in vendor_configs table per tenant database
   - Rationale: Flexible schema, easy updates, tenant-specific without code changes
   - Alternatives considered: Hardcoded (rejected - no flexibility), external config service (rejected - added complexity)
   - Implementation: JSONB column with validation schema

5. **AI Chat Memory Strategy**
   - Decision: LangGraph checkpointer with database persistence
   - Rationale: Maintains conversation context, supports follow-up questions
   - Alternatives considered: Stateless (rejected - poor UX), Redis only (rejected - not durable)
   - Implementation: conversation_history table with thread_id for session tracking

6. **File Upload Flow**
   - Decision: Direct upload to backend → temp storage → async Celery processing
   - Rationale: Simple, reliable, supports large files, async prevents UI blocking
   - Alternatives considered: Direct to S3 (rejected - adds complexity for MVP), sync processing (rejected - blocks UI)
   - Implementation: multipart/form-data → FastAPI → Celery task → tenant DB

7. **Dashboard Embedding Security**
   - Decision: iframe with sandbox attributes + URL validation + credential encryption
   - Rationale: Prevents malicious dashboards from accessing parent page, validates trusted domains
   - Alternatives considered: No sandboxing (rejected - security risk), proxy (rejected - complexity)
   - Implementation: sandbox="allow-scripts allow-same-origin allow-forms"

8. **Tenant Provisioning Automation**
   - Decision: Admin API → Create Supabase project via API → Schema migration → Seed configs
   - Rationale: Fully automated, consistent, auditable
   - Alternatives considered: Manual setup (rejected - doesn't scale), Terraform (future enhancement)
   - Implementation: Supabase Management API + Alembic migrations

9. **Technology Stack Validation**
   - Frontend: React 19 + Vite 6 + Tailwind v4 + shadcn/ui + TanStack Query v5 + Zustand ✅
   - Backend: FastAPI 0.115+ + Pydantic v2 + python-jose + bcrypt ✅
   - AI: LangChain 0.3+ + LangGraph 0.2+ + OpenAI GPT-4o ✅
   - Database: Supabase PostgreSQL 17 (multi-tenant) ✅
   - Worker: Celery + Redis ✅
   - Email: SendGrid ✅

**Output**: research.md documenting all decisions with rationale

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

### 1. Data Model Extraction

Generate `data-model.md` with complete entity definitions:

**Multi-Tenant Infrastructure**
- Tenant (master registry): tenant_id, subdomain, company_name, database_url (encrypted), database_key (encrypted), is_active, created_at, suspended_at
- Connection Pool: Per-tenant pools with credentials cache

**User & Authentication**
- User: user_id, email, password_hash, role (analyst|admin), created_at
- Session: JWT with tenant_id + subdomain claims, 24-hour expiration

**Data Processing**
- Upload Batch: batch_id, user_id, filename, status, upload_date, processing_time, rows_processed, errors_count, vendor_detected
- Vendor Configuration: config_id, vendor_name, column_mappings (JSONB), data_type_conversions (JSONB), value_standardization (JSONB), currency, default_fields (JSONB)
- Product: product_id, functional_name, product_ean, category
- Reseller: reseller_id, reseller_name, country, contact_info

**Sales Data**
- Offline Sales (B2B): sale_id, user_id, product_id, reseller_id, upload_batch_id, month, year, quantity, sales_eur, currency
- Online Sales (D2C): order_id, user_id, product_name, product_ean, order_date, quantity, sales_eur, cost_of_goods, stripe_fee, country, city, utm_source, utm_medium, utm_campaign, device_type

**AI Chat**
- Conversation: conversation_id, user_id, session_id, user_message, ai_response, sql_generated, timestamp

**Dashboard Management**
- Dashboard Configuration: config_id, user_id, dashboard_name, dashboard_type, dashboard_url, authentication_method, authentication_config (encrypted), is_primary, is_active

**Notifications**
- Email Log: log_id, user_id, email_type, recipient_email, subject, sent_at, status, error_message

### 2. API Contract Generation

Generate OpenAPI schemas in `/contracts/`:

**auth.openapi.yaml**:
- POST /api/auth/register (tenant_id in JWT after registration)
- POST /api/auth/login (returns JWT with tenant_id + subdomain claims)
- POST /api/auth/logout
- GET /api/auth/me (current user info)

**uploads.openapi.yaml**:
- POST /api/uploads (multipart/form-data file upload)
- GET /api/uploads (list user's upload history)
- GET /api/uploads/{batch_id} (upload details)
- GET /api/uploads/{batch_id}/errors (error report)

**chat.openapi.yaml**:
- POST /api/chat/query (natural language question)
- GET /api/chat/history (conversation history)
- DELETE /api/chat/history (clear conversation)

**dashboards.openapi.yaml**:
- POST /api/dashboards (create dashboard config)
- GET /api/dashboards (list user's dashboards)
- PUT /api/dashboards/{config_id} (update dashboard)
- DELETE /api/dashboards/{config_id} (delete dashboard)
- PATCH /api/dashboards/{config_id}/primary (set as primary)

**analytics.openapi.yaml**:
- GET /api/analytics/kpis (key performance indicators)
- GET /api/analytics/sales (detailed sales data, paginated)
- POST /api/analytics/export (generate report in PDF/CSV/Excel)

**admin.openapi.yaml** (platform admin only):
- POST /api/admin/tenants (create new tenant)
- GET /api/admin/tenants (list all tenants)
- PATCH /api/admin/tenants/{tenant_id}/suspend (suspend tenant)
- PATCH /api/admin/tenants/{tenant_id}/reactivate (reactivate tenant)

### 3. Contract Test Generation

Generate failing tests:
- `tests/contract/test_auth.py` - Auth endpoint contract tests
- `tests/contract/test_uploads.py` - Upload endpoint contract tests
- `tests/contract/test_chat.py` - Chat endpoint contract tests
- `tests/contract/test_dashboards.py` - Dashboard endpoint contract tests
- `tests/contract/test_analytics.py` - Analytics endpoint contract tests
- `tests/contract/test_admin.py` - Admin endpoint contract tests

**Multi-Tenant Test Requirements**:
- Test subdomain extraction and tenant routing
- Test JWT tenant_id claim validation
- Test cross-tenant data isolation (Customer A cannot access Customer B)
- Test tenant suspension flow
- Test connection pool isolation

### 4. Integration Test Scenarios

Generate integration tests from user stories:
- `tests/integration/test_file_upload_flow.py` - End-to-end file upload
- `tests/integration/test_ai_chat_flow.py` - Natural language query flow
- `tests/integration/test_multi_tenant_isolation.py` - Cross-tenant security
- `tests/integration/test_tenant_provisioning.py` - Automated tenant creation
- `tests/integration/test_dashboard_embedding.py` - Dashboard iframe flow

### 5. Quickstart Guide

Generate `quickstart.md` with:
- Local development setup (Docker Compose)
- Demo tenant creation
- Sample file upload
- AI chat query example
- Dashboard configuration
- Expected outcomes for validation

### 6. Agent Context Update

Run update script:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

Creates/updates `CLAUDE.md` at repository root with:
- Project overview (multi-tenant SaaS platform)
- Tech stack (React 19, FastAPI, Supabase PostgreSQL 17, LangChain, Celery)
- Key architectural patterns (database-per-tenant, subdomain routing, config-driven vendors)
- Recent changes (Phase 1 design complete)
- Development guidelines (TDD, multi-tenant testing, constitutional compliance)

**Output**: data-model.md, 6x OpenAPI contracts, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

1. **From Contracts** (6 OpenAPI files):
   - Each endpoint → contract test task [P]
   - Auth: 4 endpoints → 4 contract test tasks
   - Uploads: 4 endpoints → 4 contract test tasks
   - Chat: 3 endpoints → 3 contract test tasks
   - Dashboards: 5 endpoints → 5 contract test tasks
   - Analytics: 3 endpoints → 3 contract test tasks
   - Admin: 4 endpoints → 4 contract test tasks
   - **Total**: ~23 contract test tasks

2. **From Data Model** (10+ entities):
   - Each entity → Pydantic model task [P]
   - Tenant, User, Upload, Vendor Config, Product, Reseller, Sales (2), Conversation, Dashboard, Email Log
   - **Total**: ~11 model tasks

3. **Multi-Tenant Infrastructure Tasks**:
   - Tenant context middleware
   - Dynamic DB connection manager
   - Tenant registry service
   - Subdomain extraction and validation
   - JWT tenant claim generation/validation
   - **Total**: ~5 infrastructure tasks

4. **Vendor Processing Tasks**:
   - Base vendor processor
   - Config loader from tenant DB
   - Vendor format detector
   - 9x vendor processor implementations
   - **Total**: ~12 vendor tasks

5. **AI Chat Tasks**:
   - LangGraph agent with SQL tool
   - Intent detection service
   - Query validation and SQL blocking
   - Conversation memory (database checkpointer)
   - **Total**: ~4 AI tasks

6. **Integration & Polish**:
   - Multi-tenant isolation tests (critical!)
   - Tenant provisioning automation
   - Email notification service
   - Report generation (PDF, CSV, Excel)
   - Dashboard iframe security
   - RLS policy creation
   - **Total**: ~10 integration tasks

**Ordering Strategy**:
- **TDD Strict**: All tests before implementation
- **Dependency Order**: Infrastructure → Models → Services → API → UI
- **Parallel Marking**: [P] for independent files, sequential for same-file modifications
- **Critical Path**: Multi-tenant infrastructure must come first (foundation for everything)

**Estimated Output**: 80-100 numbered, dependency-ordered tasks in tasks.md

**Complexity Considerations**:
- This is a large-scale project (7 epics, 64 requirements)
- Multi-tenant architecture adds complexity to all layers
- Expect 3-6 months development time for full feature set
- MVP could focus on: Auth + Upload + Vendor Processing + Basic Analytics

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

*No constitutional violations - all principles satisfied by design*

| Constitutional Principle | Compliance Status | Notes |
|-------------------------|-------------------|-------|
| Multi-Tenant Security | ✅ PASS | Database-per-tenant from day 1 |
| Configuration-Driven | ✅ PASS | Vendor configs in tenant DB, JSONB schema |
| Defense-in-Depth | ✅ PASS | All 7 layers implemented |
| Scalable Operations | ✅ PASS | Automated provisioning, per-tenant pools |

**Justification**: N/A - no deviations required

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
