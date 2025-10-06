# Tasks: TaskifAI Multi-Tenant SaaS Platform

**Input**: Design documents from `/home/david/BIBBI_v2/specs/001-read-the-documents/`
**Prerequisites**: plan.md (required), research.md
**Current Status**: Phase 1 Complete (Single-Tenant MVP) → Upgrading to Full Multi-Tenant

## Current State Analysis

### ✅ Phase 1 Completed (MARK THESE AS DONE BELOW)
- [x] Backend structure: FastAPI app, API routes, core services
- [x] Authentication: JWT-based auth with login/register endpoints
- [x] File uploads: Upload API, file validation, temporary storage
- [x] Background processing: Celery + Redis configured
- [x] Vendor processing: Base processor, detector, config loader, Boxnox processor
- [x] Email: SendGrid client, notifier service
- [x] Database: Supabase schema with 10 tables + RLS policies
- [x] Models: User, Tenant (partial), VendorConfig
- [x] Frontend: Basic structure (minimal - 5 files)
- [x] Tenant registry schema: tenants_schema.sql with encryption functions

### ⚠️ Partially Implemented (IN PROGRESS)
- Multi-tenant: TenantContext exists, models defined, schema created, BUT hardcoded to "demo" mode
- Vendor processors: Only Boxnox done, need 8 more vendors
- Middleware: No tenant context middleware or auth middleware
- Frontend: Minimal structure, needs full implementation

### ❌ Missing (NEED TO IMPLEMENT)
- Multi-tenant infrastructure: Middleware, DB manager, subdomain routing (actual implementation)
- AI chat system: LangGraph agent, intent detection, security
- Dashboard management: Full API and frontend
- Analytics API: KPIs, sales data, export
- Admin API: Tenant provisioning, suspension
- Frontend: Complete React 19 UI with all features
- Security: Full 7-layer defense implementation

### ✅ Phase 3.2 Completed
- Testing: Comprehensive test suite (30 test files, 6,910 lines, 200+ test cases)
  - Multi-tenant core tests (6 files)
  - API contract tests (15 files)
  - Security tests (4 files)
  - Integration tests (4 files)
  - Test infrastructure (conftest.py with 20+ fixtures)

---

## Total Tasks: 218 (100 completed ✅, 118 remaining ⏳)

**Estimated Remaining Timeline**: 8-10 weeks
**Priority**: Multi-Tenant Infrastructure → Missing Features → Frontend → Polish
**Phase 3.2 Status**: ✅ COMPLETED (All TDD tests written - 28 test files, 200+ test cases)

---

## Phase 3.0: Setup & Foundation (COMPLETED ✅)

### Project Structure
- [x] T001 Create backend directory structure (app/, core/, api/, services/, models/, workers/, tests/)
- [x] T002 Create frontend directory structure (src/, components/, pages/, hooks/, stores/, api/)
- [x] T003 Initialize Python project with requirements.txt (FastAPI, Pydantic v2, python-jose, passlib, Celery, Redis)
- [x] T004 Initialize Node.js project with package.json (React 19, Vite 6, TypeScript 5.7+, Tailwind v4)
- [x] T005 [P] Configure linting: ruff for Python, ESLint for TypeScript
- [x] T006 [P] Configure formatting: black for Python, Prettier for TypeScript
- [x] T007 [P] Set up Git repository with .gitignore for Python and Node.js

### Database Setup
- [x] T008 Create database schema in backend/db/schema.sql (10 tables with RLS policies)
- [x] T009 Create tenant registry schema in backend/db/tenants_schema.sql
- [x] T010 Create vendor configs table in backend/db/vendor_configs_table.sql
- [x] T011 Create seed data in backend/db/seed_vendor_configs.sql (Boxnox config)
- [x] T012 [P] Create DB init script: Connect to Supabase, apply schema
- [x] T013 [P] Create DB seeding script: Load default vendor configs

### Core Backend Configuration
- [x] T014 Create config.py in backend/app/core/config.py: Settings with Pydantic v2, environment variables
- [x] T015 Create security.py in backend/app/core/security.py: JWT token generation, password hashing with bcrypt
- [x] T016 Create dependencies.py in backend/app/core/dependencies.py: FastAPI dependency injection
- [x] T017 Create tenant.py in backend/app/core/tenant.py: TenantContext dataclass, TenantContextManager (demo mode)
- [x] T018 [P] Create main.py in backend/app/main.py: FastAPI app initialization, CORS middleware

### Pydantic Models (Phase 1)
- [x] T019 [P] User model in backend/app/models/user.py: user_id, email, password_hash, role, validation
- [x] T020 [P] Tenant model in backend/app/models/tenant.py: TenantBase, TenantCreate, TenantUpdate with subdomain validation
- [x] T021 [P] VendorConfig model in backend/app/models/vendor_config.py: vendor_name, column_mappings, conversions

### Authentication System
- [x] T022 POST /api/auth/register in backend/app/api/auth.py: Create user, hash password, return JWT
- [x] T023 POST /api/auth/login in backend/app/api/auth.py: Validate credentials, return JWT with user claims
- [x] T024 POST /api/auth/logout in backend/app/api/auth.py: Token invalidation logic
- [x] T025 GET /api/auth/me in backend/app/api/auth.py: Return current user from JWT
- [x] T026 Include auth router in backend/app/main.py

### File Upload System
- [x] T027 Create file validator in backend/app/services/file_validator.py: Validate CSV/Excel, size limit, format
- [x] T028 Create file storage in backend/app/services/file_storage.py: Save to temp location, generate unique filename
- [x] T029 POST /api/uploads in backend/app/api/uploads.py: Accept multipart file, validate, save, queue Celery task
- [x] T030 GET /api/uploads in backend/app/api/uploads.py: List user's upload history
- [x] T031 GET /api/uploads/{batch_id} in backend/app/api/uploads.py: Upload details and status
- [x] T032 GET /api/uploads/{batch_id}/errors in backend/app/api/uploads.py: Error report
- [x] T033 Include uploads router in backend/app/main.py

### Background Worker Setup
- [x] T034 Create Celery app in backend/app/workers/celery_app.py: Configure Redis broker, result backend
- [x] T035 Create file processing task in backend/app/workers/tasks.py: Process uploaded file asynchronously
- [x] T036 Create data inserter in backend/app/services/data_inserter.py: Insert processed data into tenant database

### Vendor Processing System
- [x] T037 Create base vendor processor in backend/app/services/vendors/ (abstract base class)
- [x] T038 Create vendor detector in backend/app/services/vendors/detector.py: Auto-detect format from file structure
- [x] T039 Create config loader in backend/app/services/vendors/config_loader.py: Load tenant vendor configs from DB
- [x] T040 [P] Boxnox processor in backend/app/services/vendors/boxnox_processor.py: Column mapping, transformations

### Email Notification System
- [x] T041 Create SendGrid client in backend/app/services/email/sendgrid_client.py: Send email via SendGrid API
- [x] T042 Create email notifier in backend/app/services/email/notifier.py: Upload success/failure notifications
- [x] T043 [P] Create email templates: upload_success.html, upload_failure.html in backend/app/services/email/templates/

### Frontend Foundation
- [x] T044 Create main.tsx in frontend/src/main.tsx: React 19 app entry point
- [x] T045 Create App.tsx in frontend/src/App.tsx: Root component with basic routing
- [x] T046 Create vite.config.ts in frontend/vite.config.ts: Vite 6 configuration
- [x] T047 [P] Create FileUpload component in frontend/src/components/FileUpload.tsx: Basic file upload UI
- [x] T048 [P] Create useUploadProgress hook in frontend/src/hooks/useUploadProgress.ts: Track upload status

### Documentation
- [x] T049 [P] Create backend README.md: Setup instructions, API overview
- [x] T050 [P] Create frontend README.md: Setup instructions, development guide
- [x] T051 [P] Create root README.md: Project overview, architecture, getting started

---

## Phase 3.1: Multi-Tenant Infrastructure Completion (HIGH PRIORITY ⏳)

### Core Multi-Tenant System
- [ ] T052 Enhance Tenant model in backend/app/models/tenant.py: Add database_url encryption, validation, is_active checks
- [ ] T053 Create TenantRegistry service in backend/app/services/tenant/registry.py: CRUD operations for tenant master registry, subdomain validation
- [ ] T054 Implement subdomain→tenant lookup in backend/app/core/tenant.py: Replace demo hardcode with actual registry lookup
- [ ] T055 Create tenant context middleware in backend/app/middleware/tenant_context.py: Extract subdomain from hostname, lookup tenant, inject into request.state
- [ ] T056 Create dynamic DB connection manager in backend/app/core/db_manager.py: Per-tenant connection pools (max 10), 15-min credential cache, asyncpg
- [ ] T057 Implement credential encryption in backend/app/core/security.py: AES-256 encrypt/decrypt for database_url and database_key
- [ ] T058 Create auth middleware in backend/app/middleware/auth.py: Validate JWT, extract user and tenant, verify tenant_id matches request tenant
- [ ] T059 Update JWT token generation in backend/app/core/security.py: Include tenant_id and subdomain claims in all tokens
- [ ] T060 Add middleware to FastAPI app in backend/app/main.py: Register tenant_context middleware and auth middleware
- [ ] T061 Create logging middleware in backend/app/middleware/logging.py: Log tenant_id, user_id, request path, response status, duration

### Master Tenant Registry Database
- [ ] T062 Create tenant registry initialization script: Set up master database connection, apply schema
- [ ] T063 Seed demo tenant in registry: Add demo tenant to master registry with proper credentials (encrypted)

---

## Phase 3.2: Tests First (TDD) ✅ COMPLETED

**Status**: All 28 test files written (6,910 lines of code, 200+ test cases)
**Completion Date**: October 6, 2025
**Documentation**: See `claudedocs/phase_3_2_completion_summary.md`

### Multi-Tenant Core Tests (✅ ALL COMPLETED)
- [x] T064 [P] Tenant isolation test in backend/tests/integration/test_multi_tenant_isolation.py: Verify Customer A cannot access Customer B data
- [x] T065 [P] Subdomain routing test in backend/tests/integration/test_subdomain_routing.py: Test middleware extracts correct subdomain and routes to correct tenant DB
- [x] T066 [P] JWT tenant claims test in backend/tests/unit/test_jwt_claims.py: Verify tenant_id and subdomain in generated tokens
- [x] T067 [P] Database connection scoping test in backend/tests/integration/test_db_scoping.py: Verify queries go to correct tenant database
- [x] T068 [P] Connection pool isolation test in backend/tests/integration/test_connection_pools.py: Verify max 10 connections per tenant, no cross-tenant sharing
- [x] T069 [P] Credential encryption test in backend/tests/security/test_credential_encryption.py: Verify AES-256 encryption of database credentials

### Chat API Contract Tests (✅ ALL COMPLETED)
- [x] T070 [P] Contract test POST /api/chat/query in backend/tests/contract/test_chat_query.py
- [x] T071 [P] Contract test GET /api/chat/history in backend/tests/contract/test_chat_history.py
- [x] T072 [P] Contract test DELETE /api/chat/history in backend/tests/contract/test_chat_clear.py

### Dashboard API Contract Tests (✅ ALL COMPLETED)
- [x] T073 [P] Contract test POST /api/dashboards in backend/tests/contract/test_dashboards_create.py
- [x] T074 [P] Contract test GET /api/dashboards in backend/tests/contract/test_dashboards_list.py
- [x] T075 [P] Contract test PUT /api/dashboards/{id} in backend/tests/contract/test_dashboards_update.py
- [x] T076 [P] Contract test DELETE /api/dashboards/{id} in backend/tests/contract/test_dashboards_delete.py
- [x] T077 [P] Contract test PATCH /api/dashboards/{id}/primary in backend/tests/contract/test_dashboards_primary.py

### Analytics API Contract Tests (✅ ALL COMPLETED)
- [x] T078 [P] Contract test GET /api/analytics/kpis in backend/tests/contract/test_analytics_kpis.py
- [x] T079 [P] Contract test GET /api/analytics/sales in backend/tests/contract/test_analytics_sales.py
- [x] T080 [P] Contract test POST /api/analytics/export in backend/tests/contract/test_analytics_export.py

### Admin API Contract Tests (✅ ALL COMPLETED)
- [x] T081 [P] Contract test POST /api/admin/tenants in backend/tests/contract/test_admin_tenants_create.py
- [x] T082 [P] Contract test GET /api/admin/tenants in backend/tests/contract/test_admin_tenants_list.py
- [x] T083 [P] Contract test PATCH /api/admin/tenants/{id}/suspend in backend/tests/contract/test_admin_suspend.py
- [x] T084 [P] Contract test PATCH /api/admin/tenants/{id}/reactivate in backend/tests/contract/test_admin_reactivate.py

### Security Tests (✅ ALL COMPLETED)
- [x] T085 [P] SQL injection prevention test in backend/tests/security/test_sql_injection.py: Test AI chat blocks DROP, DELETE, UPDATE, INSERT, ALTER, CREATE
- [x] T086 [P] RLS policy enforcement test in backend/tests/security/test_rls_policies.py: Verify user_id filtering on all tenant DB queries
- [x] T087 [P] Subdomain spoofing test in backend/tests/security/test_subdomain_spoofing.py: Verify validation prevents malicious subdomains

### Integration Tests (✅ ALL COMPLETED)
- [x] T088 [P] AI chat flow integration test in backend/tests/integration/test_ai_chat_flow.py: Query → Intent → SQL → Response → Memory
- [x] T089 [P] Dashboard embedding integration test in backend/tests/integration/test_dashboard_embedding.py: Config → Validate → Encrypt → Display
- [x] T090 [P] Tenant provisioning integration test in backend/tests/integration/test_tenant_provisioning.py: Admin API → Supabase project → Schema → Seed
- [x] T091 [P] Report generation integration test in backend/tests/integration/test_report_generation.py: Query → PDF/CSV/Excel → Email

---

## Phase 3.3: Missing Backend Features

### Pydantic Models (Complete the Set)
- [ ] T092 [P] Sales model in backend/app/models/sales.py: OfflineSale (B2B) and OnlineSale (D2C) schemas with validation
- [ ] T093 [P] Product model in backend/app/models/product.py: product_id, functional_name, product_ean, category
- [ ] T094 [P] Reseller model in backend/app/models/reseller.py: reseller_id, reseller_name, country, contact_info
- [ ] T095 [P] Upload model in backend/app/models/upload.py: Enhance with vendor_detected field, error_details
- [ ] T096 [P] Conversation model in backend/app/models/conversation.py: conversation_id, user_id, session_id, messages, sql_generated
- [ ] T097 [P] Dashboard model in backend/app/models/dashboard.py: config_id, dashboard_name, type, url, encrypted_auth, is_primary
- [ ] T098 [P] Email log model in backend/app/models/email.py: log_id, email_type, recipient, subject, sent_at, status

### Vendor Processors (Add Missing 8 Vendors)
- [ ] T099 [P] Galilu processor in backend/app/services/vendors/processors/galilu.py: Column mapping, PLN→EUR conversion, specific transformations
- [ ] T100 [P] Skins SA processor in backend/app/services/vendors/processors/skins_sa.py: Column mapping, ZAR→EUR conversion
- [ ] T101 [P] CDLC processor in backend/app/services/vendors/processors/cdlc.py: Column mapping, multi-month aggregation
- [ ] T102 [P] Selfridges processor in backend/app/services/vendors/processors/selfridges.py: Column mapping, GBP→EUR conversion
- [ ] T103 [P] Liberty processor in backend/app/services/vendors/processors/liberty.py: Column mapping, GBP→EUR conversion
- [ ] T104 [P] Ukraine processor in backend/app/services/vendors/processors/ukraine.py: Column mapping, UAH→EUR conversion
- [ ] T105 [P] Continuity processor in backend/app/services/vendors/processors/continuity.py: Column mapping, special fields handling
- [ ] T106 [P] Skins NL processor in backend/app/services/vendors/processors/skins_nl.py: Column mapping, EUR native (no conversion)
- [ ] T107 Update vendor detector in backend/app/services/vendors/detector.py: Add detection logic for all 9 vendors
- [ ] T108 Update seed_vendor_configs.sql in backend/db/seed_vendor_configs.sql: Verify all 9 vendor default configs present

### AI Chat System (Net New)
- [ ] T109 Create LangGraph SQL agent in backend/app/services/ai_chat/agent.py: GPT-4o with SQL tool, MemorySaver checkpointer for conversation
- [ ] T110 Create intent detection in backend/app/services/ai_chat/intent.py: Detect query type (online, offline, comparison, time, product, reseller)
- [ ] T111 Create query security validator in backend/app/services/ai_chat/security.py: Block modification keywords, inject user_id filter, parameterized queries only
- [ ] T112 Create conversation memory service in backend/app/services/ai_chat/memory.py: Database-backed checkpointer with thread_id for sessions
- [ ] T113 Install AI dependencies: langchain>=0.3.0, langchain-openai>=0.2.0, langgraph>=0.2.0

### Dashboard Management Service (Net New)
- [ ] T114 Create dashboard service in backend/app/services/dashboard/manager.py: CRUD for dashboard configs, URL validation, credential encryption
- [ ] T115 Create dashboard URL validator in backend/app/services/dashboard/validator.py: Validate HTTPS, check domain whitelist (optional), block localhost in prod

### Analytics Service (Net New)
- [ ] T116 Create KPI calculator in backend/app/services/analytics/kpis.py: Calculate total revenue, units sold, top products for date range
- [ ] T117 Create sales data aggregator in backend/app/services/analytics/sales.py: Query with filters (date, reseller, product, channel), pagination
- [ ] T118 Enhance report generator in backend/app/workers/report_generator.py: Generate PDF with ReportLab, CSV/Excel with pandas

### Tenant Management Service (Net New)
- [ ] T119 Create tenant provisioner in backend/app/services/tenant/provisioner.py: Supabase Management API client, create project, run migrations, seed configs
- [ ] T120 Create tenant suspension service in backend/app/services/tenant/manager.py: Set is_active=false, invalidate connections, log suspension

### API Endpoints - Chat (Net New)
- [ ] T121 POST /api/chat/query in backend/app/api/chat.py: Accept natural language query, invoke LangGraph agent, return response, save conversation
- [ ] T122 GET /api/chat/history in backend/app/api/chat.py: Return conversation history for current user's session (thread_id)
- [ ] T123 DELETE /api/chat/history in backend/app/api/chat.py: Clear conversation history for current user
- [ ] T124 Include chat router in backend/app/main.py: app.include_router(chat.router, prefix="/api")

### API Endpoints - Dashboards (Net New)
- [ ] T125 POST /api/dashboards in backend/app/api/dashboards.py: Create dashboard config, validate URL, encrypt auth
- [ ] T126 GET /api/dashboards in backend/app/api/dashboards.py: List user's dashboards with primary flag
- [ ] T127 PUT /api/dashboards/{id} in backend/app/api/dashboards.py: Update dashboard config
- [ ] T128 DELETE /api/dashboards/{id} in backend/app/api/dashboards.py: Delete dashboard config
- [ ] T129 PATCH /api/dashboards/{id}/primary in backend/app/api/dashboards.py: Set as primary dashboard
- [ ] T130 Include dashboards router in backend/app/main.py: app.include_router(dashboards.router, prefix="/api")

### API Endpoints - Analytics (Net New)
- [ ] T131 GET /api/analytics/kpis in backend/app/api/analytics.py: Calculate and return KPIs for date range
- [ ] T132 GET /api/analytics/sales in backend/app/api/analytics.py: Return detailed sales with pagination and filters
- [ ] T133 POST /api/analytics/export in backend/app/api/analytics.py: Queue report generation, return task_id
- [ ] T134 Include analytics router in backend/app/main.py: app.include_router(analytics.router, prefix="/api")

### API Endpoints - Admin (Net New)
- [ ] T135 POST /api/admin/tenants in backend/app/api/admin.py: Create tenant via provisioner, return tenant details
- [ ] T136 GET /api/admin/tenants in backend/app/api/admin.py: List all tenants with status and metrics
- [ ] T137 PATCH /api/admin/tenants/{id}/suspend in backend/app/api/admin.py: Suspend tenant
- [ ] T138 PATCH /api/admin/tenants/{id}/reactivate in backend/app/api/admin.py: Reactivate tenant
- [ ] T139 Include admin router in backend/app/main.py: app.include_router(admin.router, prefix="/api/admin")

---

## Phase 3.4: Frontend Implementation (Major Work Needed)

### Frontend Setup & Dependencies
- [ ] T140 Install missing dependencies in frontend/package.json: TanStack Query v5, Zustand, react-dropzone, react-markdown, react-syntax-highlighter
- [ ] T141 Configure shadcn/ui in frontend: Add components directory, configure tailwind.config.js for shadcn
- [ ] T142 Install shadcn/ui components: Button, Input, Form, Table, Card, Badge, Tabs, Dialog, Select, Dropdown, Textarea

### Frontend Core Infrastructure
- [ ] T143 Create API client in frontend/src/lib/api.ts: Axios/fetch wrapper with JWT injection, tenant headers, error handling
- [ ] T144 Create tenant context hook in frontend/src/hooks/useTenant.ts: Extract subdomain from window.location.hostname
- [ ] T145 Create auth hook in frontend/src/hooks/useAuth.ts: Login, logout, register, current user
- [ ] T146 Create Zustand auth store in frontend/src/stores/auth.ts: User state, token storage, login/logout actions
- [ ] T147 Create Zustand UI store in frontend/src/stores/ui.ts: Modal state, sidebar state, notifications
- [ ] T148 Set up React Router in frontend/src/App.tsx: Routes for all pages (login, dashboard, uploads, chat, analytics, dashboards, admin)

### TanStack Query Hooks
- [ ] T149 [P] Auth queries in frontend/src/api/auth.ts: useLogin, useRegister, useLogout, useCurrentUser mutations
- [ ] T150 [P] Upload queries in frontend/src/api/uploads.ts: useUploadFile, useUploadsList, useUploadDetails, useUploadErrors
- [ ] T151 [P] Chat queries in frontend/src/api/chat.ts: useChatQuery, useChatHistory, useClearHistory
- [ ] T152 [P] Dashboard queries in frontend/src/api/dashboards.ts: useDashboards, useCreateDashboard, useUpdateDashboard, useDeleteDashboard, useSetPrimary
- [ ] T153 [P] Analytics queries in frontend/src/api/analytics.ts: useKPIs, useSalesData, useExportReport

### Pages (Complete UI)
- [ ] T154 [P] Login page in frontend/src/pages/Login.tsx: Full login/register form with shadcn/ui, tenant context display
- [ ] T155 [P] Dashboard page in frontend/src/pages/Dashboard.tsx: Overview with KPIs, recent uploads, quick actions
- [ ] T156 [P] Uploads page in frontend/src/pages/Uploads.tsx: Enhanced with upload history table, status tracking, error reports
- [ ] T157 [P] Chat page in frontend/src/pages/Chat.tsx: AI chat interface with message list, input, markdown rendering
- [ ] T158 [P] Analytics page in frontend/src/pages/Analytics.tsx: KPI cards, sales table with filters, export button
- [ ] T159 [P] Dashboards page in frontend/src/pages/Dashboards.tsx: Tab interface for multiple dashboards, iframe embedding
- [ ] T160 [P] Admin page in frontend/src/pages/Admin.tsx: Platform admin view for tenant management

### Components - Authentication
- [ ] T161 [P] LoginForm component in frontend/src/components/auth/LoginForm.tsx: Email/password form with validation
- [ ] T162 [P] RegisterForm component in frontend/src/components/auth/RegisterForm.tsx: Registration with tenant display
- [ ] T163 [P] ProtectedRoute wrapper in frontend/src/components/auth/ProtectedRoute.tsx: Auth check, redirect to login

### Components - Upload (Enhance Existing)
- [ ] T164 Enhance FileUpload in frontend/src/components/upload/FileUpload.tsx: Add better validation feedback, preview
- [ ] T165 [P] UploadStatus component in frontend/src/components/upload/UploadStatus.tsx: Status badge with icon and color
- [ ] T166 [P] UploadHistory component in frontend/src/components/upload/UploadHistory.tsx: Table with pagination
- [ ] T167 [P] ErrorReport component in frontend/src/components/upload/ErrorReport.tsx: Display errors with row numbers and details

### Components - Chat
- [ ] T168 [P] MessageList component in frontend/src/components/chat/MessageList.tsx: Chat messages with auto-scroll
- [ ] T169 [P] ChatInput component in frontend/src/components/chat/ChatInput.tsx: Input with send button, Enter key handling
- [ ] T170 [P] Message component in frontend/src/components/chat/Message.tsx: User vs AI styling, markdown rendering
- [ ] T171 [P] ChatHistory component in frontend/src/components/chat/ChatHistory.tsx: Sidebar with conversation sessions

### Components - Dashboards
- [ ] T172 [P] DashboardIframe component in frontend/src/components/dashboard/DashboardIframe.tsx: Sandboxed iframe with security attrs
- [ ] T173 [P] DashboardTabs component in frontend/src/components/dashboard/DashboardTabs.tsx: Tab switcher with primary indicator
- [ ] T174 [P] DashboardForm component in frontend/src/components/dashboard/DashboardForm.tsx: Create/edit dashboard form
- [ ] T175 [P] DashboardCard component in frontend/src/components/dashboard/DashboardCard.tsx: Dashboard preview card with actions

### Components - Analytics
- [ ] T176 [P] KPICard component in frontend/src/components/analytics/KPICard.tsx: Metric display with icon, value, trend
- [ ] T177 [P] SalesTable component in frontend/src/components/analytics/SalesTable.tsx: Paginated table with filters and sorting
- [ ] T178 [P] ExportButton component in frontend/src/components/analytics/ExportButton.tsx: Dropdown for PDF/CSV/Excel export
- [ ] T179 [P] FilterPanel component in frontend/src/components/analytics/FilterPanel.tsx: Date range, reseller, product, channel filters

### Components - Layout & Shared
- [ ] T180 [P] Layout component in frontend/src/components/ui/Layout.tsx: Header, sidebar, main content area
- [ ] T181 [P] Sidebar component in frontend/src/components/ui/Sidebar.tsx: Navigation with active state, user menu
- [ ] T182 [P] Header component in frontend/src/components/ui/Header.tsx: Tenant name, user avatar, notifications
- [ ] T183 [P] TenantBadge component in frontend/src/components/ui/TenantBadge.tsx: Display current tenant subdomain

---

## Phase 3.5: Integration & Polish

### Database Enhancements
- [ ] T184 Review tenant database schema in backend/db/schema.sql: Add conversation_history table, dashboard_configs table if missing
- [ ] T185 Create migration for multi-tenant changes: Add tenant-aware columns where needed
- [ ] T186 Verify RLS policies in backend/db/schema.sql: Ensure all tables have user_id filtering policies

### Testing & Validation
- [ ] T187 [P] Unit test for subdomain extraction in backend/tests/unit/test_subdomain.py
- [ ] T188 [P] Unit test for vendor detection in backend/tests/unit/test_vendor_detection.py
- [ ] T189 [P] Unit test for config loader in backend/tests/unit/test_config_loader.py
- [ ] T190 Performance test: API latency <200ms in backend/tests/performance/test_api_latency.py
- [ ] T191 Performance test: File processing 1-2min for 500-5000 rows in backend/tests/performance/test_file_processing.py
- [ ] T192 Performance test: AI chat <5 seconds in backend/tests/performance/test_chat_latency.py

### Security Audits
- [ ] T193 Security audit: Verify all 7 defense layers (Layer 0: DB isolation → Layer 7: Audit logging)
- [ ] T194 Security audit: Test SQL injection prevention in AI chat
- [ ] T195 Security audit: Test cross-tenant data isolation (attempt to access other tenant's data)
- [ ] T196 Security audit: Verify credential encryption (check no plaintext secrets in DB)

### Documentation Updates
- [x] T197 [P] Update backend README.md with multi-tenant setup instructions
- [x] T198 [P] Update frontend README.md with routing and auth setup
- [x] T199 [P] Create API documentation: Document all endpoints with request/response examples
- [x] T200 [P] Create deployment guide: Docker compose, environment variables, Supabase setup

### CI/CD Setup
- [ ] T201 [P] Create GitHub Actions workflow: Run tests on push
- [ ] T202 [P] Create Docker files: backend/Dockerfile, frontend/Dockerfile
- [ ] T203 [P] Create docker-compose.yml: Local development environment with all services
- [ ] T204 [P] Create production deployment script: Deploy to hosting provider

### Performance Optimization
- [ ] T205 [P] Add database indexes: Optimize queries based on usage patterns
- [ ] T206 [P] Implement caching: Redis for frequently accessed data
- [ ] T207 [P] Frontend optimization: Code splitting, lazy loading, bundle analysis
- [ ] T208 [P] API optimization: Response compression, pagination defaults

### Final Validation
- [ ] T209 Run all tests: pytest backend/tests, npm run test (frontend)
- [ ] T210 Load testing: Verify performance under load (100 concurrent users per tenant)
- [ ] T211 Security scan: Run OWASP ZAP or similar security scanner
- [ ] T212 Accessibility audit: WCAG compliance check on frontend
- [ ] T213 Browser compatibility: Test on Chrome, Firefox, Safari, Edge
- [ ] T214 Mobile responsiveness: Test on mobile devices and tablets
- [ ] T215 Documentation review: Ensure all docs are complete and accurate
- [ ] T216 Constitutional compliance: Final check against all 4 principles
- [ ] T217 Stakeholder demo: Present completed features for approval
- [ ] T218 Production readiness: Final checklist before deployment

---

## Dependencies

### Critical Path
- T001-T051 (Phase 1 Setup) ✅ COMPLETE → Enables all subsequent work
- T052-T063 (Multi-tenant infrastructure) blocks ALL other backend work
- T064-T069 (Multi-tenant tests) should be done before/parallel with T052-T063
- T070-T084 (API contract tests) before T121-T139 (API implementations)
- T140-T142 (Frontend setup) before all frontend components

### Major Blockers
- T052-T063 complete → Can implement T121-T139 (New APIs)
- T109-T112 (AI chat system) → Can implement T121-T124 (Chat API)
- T114-T115 (Dashboard service) → Can implement T125-T130 (Dashboard API)
- T116-T118 (Analytics service) → Can implement T131-T134 (Analytics API)
- T119-T120 (Tenant management) → Can implement T135-T139 (Admin API)

### Frontend Dependencies
- T143-T148 (Frontend core) before all components
- T149-T153 (TanStack Query hooks) before pages that use them
- T142 (shadcn/ui components) before T161-T183 (components using shadcn)

---

## Parallel Execution Examples

### Phase 1: Multi-Tenant Tests (Launch Together)
```bash
Task: "Create tenant isolation test in backend/tests/integration/test_multi_tenant_isolation.py"
Task: "Create subdomain routing test in backend/tests/integration/test_subdomain_routing.py"
Task: "Create JWT tenant claims test in backend/tests/unit/test_jwt_claims.py"
Task: "Create database connection scoping test in backend/tests/integration/test_db_scoping.py"
Task: "Create connection pool isolation test in backend/tests/integration/test_connection_pools.py"
Task: "Create credential encryption test in backend/tests/security/test_credential_encryption.py"
```

### Phase 2: API Contract Tests (Launch Together)
```bash
Task: "Create chat query contract test in backend/tests/contract/test_chat_query.py"
Task: "Create chat history contract test in backend/tests/contract/test_chat_history.py"
Task: "Create dashboard create contract test in backend/tests/contract/test_dashboards_create.py"
Task: "Create dashboard list contract test in backend/tests/contract/test_dashboards_list.py"
Task: "Create analytics KPIs contract test in backend/tests/contract/test_analytics_kpis.py"
# ... (all 15 API contract tests)
```

### Phase 3: Vendor Processors (Launch Together)
```bash
Task: "Create Galilu processor in backend/app/services/vendors/processors/galilu.py"
Task: "Create Skins SA processor in backend/app/services/vendors/processors/skins_sa.py"
Task: "Create CDLC processor in backend/app/services/vendors/processors/cdlc.py"
Task: "Create Selfridges processor in backend/app/services/vendors/processors/selfridges.py"
Task: "Create Liberty processor in backend/app/services/vendors/processors/liberty.py"
Task: "Create Ukraine processor in backend/app/services/vendors/processors/ukraine.py"
Task: "Create Continuity processor in backend/app/services/vendors/processors/continuity.py"
Task: "Create Skins NL processor in backend/app/services/vendors/processors/skins_nl.py"
```

### Phase 4: Pydantic Models (Launch Together)
```bash
Task: "Create Sales model in backend/app/models/sales.py"
Task: "Create Product model in backend/app/models/product.py"
Task: "Create Reseller model in backend/app/models/reseller.py"
Task: "Create Conversation model in backend/app/models/conversation.py"
Task: "Create Dashboard model in backend/app/models/dashboard.py"
Task: "Create Email log model in backend/app/models/email.py"
```

### Phase 5: Frontend Components (Launch Together)
```bash
Task: "Create Login page in frontend/src/pages/Login.tsx"
Task: "Create Dashboard page in frontend/src/pages/Dashboard.tsx"
Task: "Create Chat page in frontend/src/pages/Chat.tsx"
Task: "Create Analytics page in frontend/src/pages/Analytics.tsx"
Task: "Create Dashboards page in frontend/src/pages/Dashboards.tsx"
Task: "Create Admin page in frontend/src/pages/Admin.tsx"
# ... (all page and component tasks can run in parallel)
```

---

## Notes

- **Phase 1 COMPLETE ✅**: 72 tasks done - Setup, basic auth, file uploads, Celery, basic vendor processing, tenant schema
- **Main remaining work**: Multi-tenant upgrade (T052-T063), AI chat (T109-T113), dashboards (T114-T115), analytics (T116-T118), full frontend (T140-T183)
- **Test-first**: Write all contract tests (T070-T084) before implementing APIs
- **Multi-tenant testing critical**: Tests T064-T069 verify core security architecture
- **Frontend needs major work**: Only 5 files exist, need 40+ components
- **Vendor processors**: 8 more vendors to implement (only Boxnox done)

## Validation Checklist

*GATE: Must pass before considering complete*

- [ ] All multi-tenant tests passing (T064-T069)
- [ ] All API contract tests passing (T070-T084)
- [ ] All security audits passed (T193-T196)
- [ ] Cross-tenant isolation verified
- [ ] All 9 vendor processors implemented
- [ ] AI chat system working with conversation memory
- [ ] Dashboard embedding secure and functional
- [ ] Full frontend with all pages and components
- [ ] Constitutional compliance verified (all 4 principles)

---

**Completed**: 72/218 tasks (33%) ✅
**Remaining**: 146/218 tasks (67%) ⏳
**Estimated Remaining Timeline**: 8-12 weeks
**Priority Order**: Multi-Tenant (T052-T063) → Tests (T064-T091) → Backend Features (T092-T139) → Frontend (T140-T183) → Polish (T184-T218)

**Ready for implementation following TDD: Tests must fail before implementation begins.**
