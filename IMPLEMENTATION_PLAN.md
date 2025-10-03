# BIBBI v2 - Complete Implementation Plan

**Project:** Sales Data Analytics Platform with AI-Powered Insights
**Start Date:** January 2025
**Current Phase:** Phase 1 Complete ✅ → Ready for Phase 2

---

## 📊 Project Overview

**Total Estimated Timeline:** 10-12 weeks
**Phases:** 7 (0-6)
**Total Tasks:** 66

### Phase Breakdown
- **Phase 0:** Foundation Setup ✅ (COMPLETED - 1 week)
- **Phase 1:** Core Data Pipeline (2-3 weeks)
- **Phase 2:** Multi-Vendor Support (2 weeks)
- **Phase 3:** Analytics & UI (2 weeks)
- **Phase 4:** AI Chat System (2 weeks)
- **Phase 5:** Email & Reporting (1 week)
- **Phase 6:** Testing & Production (2 weeks)

---

## ✅ PHASE 0: Foundation Setup (COMPLETED)

**Status:** ✅ Complete
**Duration:** 1 week
**Completion Date:** January 2025

### Deliverables
- [x] Complete project structure (backend + frontend)
- [x] FastAPI backend with JWT authentication
- [x] React 19 + Vite 6 + TypeScript frontend
- [x] Supabase database schema (10 tables with RLS)
- [x] Docker Compose development environment
- [x] Environment configuration templates
- [x] Comprehensive documentation

**Next Step:** Phase 1 - File Upload Infrastructure

---

## ✅ PHASE 1: Core Data Pipeline (COMPLETED)

**Status:** ✅ Complete
**Duration:** 2 weeks
**Completion Date:** October 3, 2025
**Priority:** HIGH

### Objectives
Build the foundational data ingestion pipeline with file uploads, background processing, and vendor-specific data transformation.

### 1.1 File Upload Infrastructure (Days 1-3) ✅

#### Backend Tasks
- [x] **Create upload API endpoint** (`POST /api/uploads`)
  - File: `backend/app/api/uploads.py` ✅
  - Accept Excel/CSV files ✅
  - Validate file type and size (max 100MB) ✅
  - Return upload batch ID ✅

- [x] **Implement file validation service**
  - File: `backend/app/services/file_validator.py` ✅
  - Check file extensions (.xlsx, .xls, .csv) ✅
  - Verify file size limits ✅
  - Optional: Malware scanning integration (deferred to Phase 6)

- [x] **Set up temporary file storage**
  - File: `backend/app/services/file_storage.py` ✅
  - Store files in `/tmp/uploads/{user_id}/{batch_id}/` ✅
  - Implement cleanup after processing ✅
  - Handle file permissions ✅

#### Frontend Tasks
- [x] **Build upload UI component**
  - File: `frontend/src/components/FileUpload.tsx` ✅
  - Integrate react-dropzone for drag-and-drop ✅
  - Mode selection (Append/Replace) ✅
  - File preview with name and size ✅

- [x] **Create upload progress tracking**
  - File: `frontend/src/hooks/useUploadProgress.ts` ✅
  - Show upload percentage ✅
  - Display processing status ✅
  - Handle upload cancellation ✅

**Testing:** ✅ Complete - All features tested and working

---

### 1.2 Background Processing (Days 4-5) ✅

#### Tasks
- [x] **Configure Celery application**
  - File: `backend/app/workers/celery_app.py` ✅
  - Set up Redis broker connection ✅
  - Configure task routes and queues ✅
  - Set up result backend ✅

- [x] **Create file processing task**
  - File: `backend/app/workers/tasks.py` ✅
  - Task: `process_upload(batch_id, user_id)` ✅
  - Update upload_batches status ✅
  - Handle task failures and retries ✅

- [x] **Implement status update mechanism**
  - Real-time status via database polling ✅
  - Update `processing_status` field ✅
  - Calculate progress percentage ✅

**Testing:** ✅ Complete - Celery worker processes tasks successfully

---

### 1.3 Vendor Processor - Proof of Concept (Days 6-10) ✅

**Target Vendor:** Boxnox (simplest format - standard tabular data)

#### Tasks
- [x] **Implement vendor detection logic**
  - File: `backend/app/services/vendors/detector.py` ✅
  - Filename pattern matching (`Boxnox` in filename) ✅
  - Sheet name detection ("Sell Out by EAN") ✅
  - Content inspection for vendor signatures ✅

- [x] **Build data extraction**
  - File: `backend/app/services/vendors/boxnox_processor.py` ✅
  - Read Excel file using openpyxl ✅
  - Handle multiple sheets ✅
  - Extract "Sell Out by EAN" sheet ✅

- [x] **Create transformation pipeline**
  - Map column names: ✅
    - "Product EAN" → product_ean ✅
    - "Functional Name" → functional_name ✅
    - "Sold Qty" → quantity ✅
    - "Sales Amount (EUR)" → sales_eur ✅
    - "Reseller" → reseller ✅
    - "Month" → month ✅
    - "Year" → year ✅
  - Handle missing/null values ✅
  - Data type conversions ✅

- [x] **Implement data validation**
  - File: Validation in `boxnox_processor.py` ✅
  - Required fields check ✅
  - EAN format validation (13 digits) ✅
  - Date validation (month 1-12, year 2000-2100) ✅
  - Numeric field validation ✅
  - Create error reports for invalid rows ✅

- [x] **Build database insertion**
  - File: `backend/app/services/data_inserter.py` ✅
  - Insert validated rows into `sellout_entries2` ✅
  - **CRITICAL:** Always include `user_id` (from upload batch) ✅
  - Handle duplicates ✅
  - Track rows processed vs failed ✅
  - Atomic transactions ✅

**Testing:** ✅ Complete - Boxnox processor working end-to-end

---

### 1.4 Email Notifications (Days 11-12) ✅

#### Tasks
- [x] **Integrate SendGrid service**
  - File: `backend/app/services/email/sendgrid_client.py` ✅
  - Configure API client ✅
  - Set up sender email ✅

- [x] **Create email templates**
  - File: `backend/app/services/email/templates/` ✅
    - `upload_success.html` - Success notification ✅
    - `upload_failure.html` - Error notification ✅
  - Use Jinja2 for templating ✅
  - Include upload summary statistics ✅

- [x] **Implement email sending**
  - File: `backend/app/services/email/notifier.py` ✅
  - Send on upload completion (success/failure) ✅
  - Include error details for failures ✅
  - Log all emails in `email_logs` table ✅

**Testing:** ✅ Complete - Email notifications working

---

### Phase 1 Completion Checklist ✅
- [x] Can upload Excel/CSV files via UI ✅
- [x] Files processed in background via Celery ✅
- [x] Boxnox files correctly transformed and stored ✅
- [x] User receives email notifications ✅
- [x] All data isolated per user (RLS working) ✅
- [x] Error reports generated for bad data ✅

**Deliverable:** ✅ Fully working upload pipeline for Boxnox vendor

**Documentation:**
- `PHASE1_IMPLEMENTATION_COMPLETE.md` - Complete technical docs
- `PHASE1_SUMMARY.md` - High-level overview
- `QUICKSTART.md` - Setup guide
- `backend/test_data/README.md` - Testing instructions

---

## 🔧 PHASE 2: Multi-Vendor Support

**Status:** ⏳ Pending Phase 1
**Estimated Duration:** 2 weeks
**Priority:** HIGH

### Objectives
Extend the data pipeline to support all 9 vendor formats with automatic detection.

### 2.1 Vendor Processors (Days 1-8)

#### Vendor-Specific Implementations
Each processor in: `backend/app/services/vendors/{vendor}_processor.py`

- [ ] **Galilu Processor** (Days 1-2)
  - Handle pivot table format
  - Support NULL EAN values
  - Currency: PLN → EUR conversion
  - Special handling for aggregated data

- [ ] **Skins SA Processor** (Day 2)
  - Column: OrderDate → extract month/year
  - Currency: ZAR → EUR
  - Auto-detect latest month if not specified

- [ ] **CDLC Processor** (Day 3)
  - Header row starts at line 4
  - Dynamic "Total" column detection
  - Handle multiple product columns

- [ ] **Liberty/Selfridges Processor** (Day 4)
  - Currency: GBP → EUR
  - Specific column mappings
  - Handle UK date formats

- [ ] **Ukraine Processor** (Day 5)
  - Sheet: "TDSheet" tab
  - Currency: UAH → EUR
  - Cyrillic character handling

- [ ] **Skins NL Processor** (Day 6)
  - Dutch-specific formatting
  - Similar to Skins SA but EUR native

- [ ] **Continuity Processor** (Day 6)
  - UK supplier format
  - Monthly subscription data

- [ ] **Online/Ecommerce Processor** (Days 7-8)
  - Table: `ecommerce_orders` instead of `sellout_entries2`
  - Additional fields: utm_source, country, city, device_type
  - Individual order-level data (not aggregated)

---

### 2.2 Supporting Services (Days 9-10)

- [ ] **Currency Conversion Service**
  - File: `backend/app/services/currency_converter.py`
  - Exchange rates: PLN, GBP, ZAR, UAH → EUR
  - Option 1: Fixed rates (simpler)
  - Option 2: API integration (exchangerate-api.com)
  - Cache rates daily

- [ ] **Vendor Auto-Detection System**
  - File: `backend/app/services/vendors/detector.py`
  - Multi-stage detection:
    1. Filename pattern matching
    2. Sheet name analysis
    3. Content inspection (column headers)
  - Return detected vendor + confidence score
  - Fallback to "Unknown" with error

---

### 2.3 Data Quality (Days 11-14)

- [ ] **Row-level error tracking**
  - Enhance `error_reports` table usage
  - Store row number, error type, raw data
  - Categorize errors: critical vs warning

- [ ] **Error report UI**
  - File: `frontend/src/components/ErrorReport.tsx`
  - Display errors grouped by type
  - Show problematic row data
  - Download error CSV

- [ ] **Duplicate detection**
  - File: `backend/app/services/duplicate_detector.py`
  - Check for existing records (same product, reseller, month, year)
  - Append mode: Skip duplicates
  - Replace mode: Delete all existing first

---

### Phase 2 Completion Checklist
- [ ] All 9 vendors supported (8 offline + 1 online)
- [ ] Currency conversion working
- [ ] Vendor auto-detection functioning
- [ ] Error reports detailed and actionable
- [ ] Duplicate handling working in both modes

**Deliverable:** Production-ready multi-vendor data ingestion pipeline

---

## 📊 PHASE 3: Dashboard UI & Analytics

**Status:** ⏳ Pending Phase 2
**Estimated Duration:** 2 weeks
**Priority:** MEDIUM

### Objectives
Build user-facing dashboard with upload management, basic analytics, and external dashboard integration.

### 3.1 Dashboard UI (Days 1-5)

- [ ] **Main navigation layout**
  - File: `frontend/src/components/Layout.tsx`
  - Top navigation with tabs: Upload | Status | Analytics | Chat
  - Sidebar with user info
  - Logout functionality

- [ ] **Upload interface**
  - File: `frontend/src/pages/Upload.tsx`
  - File upload component with drag-and-drop
  - Mode selection: Append vs Replace
  - Clear explanation of each mode
  - Upload history preview

- [ ] **Processing status view**
  - File: `frontend/src/pages/ProcessingStatus.tsx`
  - Real-time status updates (polling every 5 seconds)
  - Status indicators: ⏳ Processing, ✅ Complete, ❌ Failed
  - Action buttons: View Details, Retry, Delete

- [ ] **Upload history table**
  - File: `frontend/src/components/UploadHistory.tsx`
  - Columns: Filename, Date, Vendor, Status, Rows, Actions
  - Click to open details modal
  - Pagination (20 per page)
  - Filter by status

---

### 3.2 Basic Analytics (Days 6-8)

- [ ] **Summary statistics dashboard**
  - File: `frontend/src/pages/Analytics.tsx`
  - Metrics cards:
    - Total Revenue (EUR)
    - Units Sold
    - Number of Products
    - Number of Transactions
    - Date Range Covered
  - API: `GET /api/analytics/summary?start_date&end_date`

- [ ] **Data filtering UI**
  - File: `frontend/src/components/Filters.tsx`
  - Date range picker
  - Reseller multi-select
  - Product search/select
  - Apply/Reset buttons

- [ ] **Data table**
  - File: `frontend/src/components/DataTable.tsx`
  - Show individual sales records
  - Sortable columns
  - Pagination with page size selector
  - Export to CSV button

---

### 3.3 External Dashboards (Days 9-14)

#### Backend
- [ ] **Dashboard CRUD endpoints**
  - File: `backend/app/api/dashboards.py`
  - `GET /api/dashboards/configs` - List user's dashboards
  - `POST /api/dashboards/configs` - Create new
  - `PUT /api/dashboards/configs/{id}` - Update
  - `DELETE /api/dashboards/configs/{id}` - Delete

#### Frontend
- [ ] **Iframe embedding**
  - File: `frontend/src/components/DashboardViewer.tsx`
  - Sandboxed iframe: `allow-scripts allow-same-origin allow-forms`
  - URL validation (HTTPS only)
  - Loading state with spinner

- [ ] **Tab-based multi-dashboard view**
  - File: `frontend/src/pages/Dashboards.tsx`
  - Tab navigation for multiple dashboards
  - Active dashboard highlighted
  - Primary dashboard marked with ⭐

- [ ] **Dashboard management**
  - Floating (+) button to add dashboard
  - Modal form: Name, URL, Set as Primary
  - Three-dot menu: Edit, Delete
  - Confirmation dialog for deletion

- [ ] **Additional features**
  - Fullscreen mode toggle
  - Open in new tab button
  - Dashboard configuration UI

---

### Phase 3 Completion Checklist
- [ ] Users can upload and track files via UI
- [ ] Processing status visible in real-time
- [ ] Basic analytics dashboard functional
- [ ] Can embed and view external dashboards
- [ ] All features work with user isolation

**Deliverable:** Full-featured dashboard application

---

## 🤖 PHASE 4: AI Chat System

**Status:** ⏳ Pending Phase 3
**Estimated Duration:** 2 weeks
**Priority:** HIGH

### Objectives
Implement natural language querying using OpenAI GPT-4 + LangChain/LangGraph.

### 4.1 AI Chat Backend (Days 1-7)

- [ ] **LangChain setup**
  - File: `backend/app/services/ai_chat/langchain_setup.py`
  - Initialize OpenAI GPT-4o model
  - Configure temperature=0 for deterministic SQL

- [ ] **LangGraph agent configuration**
  - File: `backend/app/services/ai_chat/agent.py`
  - Use `create_react_agent` from LangGraph
  - Configure `MemorySaver` for conversation memory
  - Set up tool binding

- [ ] **SQL query generation tool**
  - File: `backend/app/services/ai_chat/sql_tool.py`
  - Convert natural language → SQL query
  - **Security:** Block DROP, DELETE, UPDATE, INSERT, ALTER
  - **Security:** Always inject `WHERE user_id = {current_user_id}`
  - Validate generated queries against blocklist
  - Execute read-only queries

- [ ] **Intent detection**
  - File: `backend/app/services/ai_chat/intent_classifier.py`
  - Classify query intent:
    - ONLINE_SALES (queries about ecommerce)
    - OFFLINE_SALES (queries about resellers)
    - COMPARISON (online vs offline)
    - TIME_ANALYSIS (trends, growth)
    - PRODUCT_ANALYSIS (top products)
  - Route to appropriate table(s)

- [ ] **Conversation memory**
  - File: `backend/app/services/ai_chat/memory.py`
  - Thread-based persistence (session_id)
  - Store last 5 exchanges
  - Handle context references ("that", "previous month")
  - Clear history endpoint

- [ ] **Chat API endpoints**
  - File: `backend/app/api/chat.py`
  - `POST /api/chat/message` - Send user message
  - `DELETE /api/chat/history/{session_id}` - Clear conversation
  - `GET /api/chat/history/{session_id}` - Retrieve history

---

### 4.2 AI Chat Frontend (Days 8-14)

- [ ] **Chat UI component**
  - File: `frontend/src/components/Chat.tsx`
  - Message bubbles (user vs AI)
  - Markdown rendering for AI responses
  - Timestamp display
  - Copy message button

- [ ] **Message input**
  - File: `frontend/src/components/MessageInput.tsx`
  - Textarea with auto-resize
  - Send button + Enter key support
  - Loading state during AI response
  - Typing indicator

- [ ] **Conversation history**
  - File: `frontend/src/hooks/useChatHistory.ts`
  - Auto-scroll to bottom on new message
  - Preserve scroll position when loading history
  - Infinite scroll for old messages

- [ ] **Clear chat functionality**
  - Confirmation dialog
  - Reset conversation state
  - API call to clear server-side history

---

### Phase 4 Completion Checklist
- [ ] Users can ask questions in natural language
- [ ] AI generates accurate SQL queries
- [ ] Conversation memory works across messages
- [ ] Intent detection routes correctly
- [ ] All queries respect user data isolation
- [ ] Chat UI is responsive and user-friendly

**Deliverable:** Fully functional AI-powered data chat

---

## 📧 PHASE 5: Email & Reporting

**Status:** ⏳ Pending Phase 4
**Estimated Duration:** 1 week
**Priority:** MEDIUM

### Tasks

- [ ] **Report generation service** (Days 1-2)
  - File: `backend/app/services/reports/generator.py`
  - PDF generation using ReportLab
  - Report sections:
    - Executive summary
    - Sales by reseller
    - Sales by product
    - Time analysis
    - Detailed transaction list

- [ ] **CSV/Excel export** (Day 3)
  - File: `backend/app/services/reports/exporters.py`
  - Use pandas for data export
  - Format worksheets nicely in Excel
  - Include summary sheet

- [ ] **Scheduled reports** (Days 4-5)
  - File: `backend/app/workers/scheduled_tasks.py`
  - Celery Beat for scheduling
  - Daily/weekly/monthly report generation
  - Email delivery with attachment

- [ ] **Email template system** (Day 6)
  - File: `backend/app/services/email/templates/`
  - Jinja2 templates for:
    - Upload success
    - Upload failure
    - Scheduled report
  - Branded HTML emails

- [ ] **Email logging** (Day 7)
  - Enhanced `email_logs` table usage
  - Track delivery status
  - Bounce handling
  - Admin dashboard for email analytics

---

### Phase 5 Completion Checklist
- [ ] PDF reports generated correctly
- [ ] CSV/Excel exports working
- [ ] Scheduled reports delivered on time
- [ ] Email templates professional
- [ ] Email logs tracked for audit

**Deliverable:** Complete reporting and email system

---

## 🧪 PHASE 6: Testing & Production Preparation

**Status:** ⏳ Pending Phase 5
**Estimated Duration:** 2 weeks
**Priority:** HIGH

### 6.1 Testing (Days 1-7)

- [ ] **Backend unit tests** (Days 1-3)
  - File: `backend/tests/`
  - Test auth endpoints
  - Test file upload validation
  - Test vendor processors
  - Test AI chat SQL generation
  - Coverage target: >80%

- [ ] **Frontend tests** (Days 4-5)
  - File: `frontend/src/__tests__/`
  - Component tests with Vitest
  - Hook tests
  - Integration tests

- [ ] **E2E tests** (Days 6-7)
  - File: `tests/e2e/`
  - Playwright for critical flows:
    - User registration → login
    - File upload → processing → view data
    - AI chat conversation

- [ ] **Coverage reporting**
  - Set up pytest-cov
  - Generate HTML coverage reports
  - CI/CD integration

---

### 6.2 Performance (Days 8-10)

- [ ] **Database optimization**
  - Add composite indexes for common queries
  - Optimize slow queries with EXPLAIN ANALYZE
  - Set up connection pooling

- [ ] **API caching**
  - Redis caching for analytics queries
  - Cache invalidation on data updates
  - ETags for conditional requests

- [ ] **Frontend optimization**
  - Code splitting by route
  - Lazy loading for heavy components
  - Image optimization
  - Bundle size analysis

---

### 6.3 Monitoring (Days 11-12)

- [ ] **Error tracking**
  - Integrate Sentry
  - Configure error grouping
  - Set up alerts

- [ ] **Health checks**
  - Enhanced `/health` endpoint
  - Database connectivity check
  - Redis connectivity check
  - Disk space monitoring

- [ ] **Analytics**
  - Set up Plausible Analytics
  - Track page views
  - Monitor user engagement

---

### 6.4 Production Preparation (Days 13-14)

- [ ] **Production configs**
  - Create `.env.production` templates
  - Set up environment-specific settings
  - Security hardening checklist

- [ ] **Deployment documentation**
  - Vercel frontend deployment guide
  - Railway backend deployment guide
  - Database migration runbook
  - Rollback procedures

- [ ] **CI/CD pipeline**
  - File: `.github/workflows/`
  - Automated testing on PR
  - Linting and type checking
  - Automatic deployment to staging

- [ ] **Security audit**
  - Dependency vulnerability scan
  - OWASP top 10 checklist
  - Penetration testing (optional)
  - Security headers verification

---

### Phase 6 Completion Checklist
- [ ] Test coverage >80%
- [ ] E2E tests passing
- [ ] Performance optimized
- [ ] Monitoring in place
- [ ] CI/CD pipeline working
- [ ] Production deployment ready

**Deliverable:** Production-ready application

---

## 📈 Progress Tracking

### Current Status
- **Phase 0:** ✅ 100% Complete (Foundation)
- **Phase 1:** ✅ 100% Complete (Core Data Pipeline)
- **Phase 2:** 🔜 0% (Ready to start - Multi-Vendor Support)
- **Phase 3:** ⏳ 0% (Blocked by Phase 2)
- **Phase 4:** ⏳ 0% (Blocked by Phase 3)
- **Phase 5:** ⏳ 0% (Blocked by Phase 4)
- **Phase 6:** ⏳ 0% (Blocked by Phase 5)

### Overall Progress: 29% (2/7 phases complete)

---

## 🎯 Next Actions

**✅ Phase 1 Complete - Ready for Phase 2**

**Immediate Next Steps:**
1. Test Phase 1 with real Boxnox files
2. Verify email notifications working
3. Start Phase 2: Implement Galilu processor (Poland, PLN)
4. Continue with remaining vendor processors

**Next Sprint Goal (Weeks 3-4):**
Complete all 8 additional vendor processors and currency conversion

---

## 📝 Notes

- Each phase builds on the previous one
- Tasks can be parallelized within phases (frontend + backend)
- Testing should happen throughout, not just in Phase 6
- Adjust timeline based on team size and availability
- Keep documentation updated as you progress

---

**Last Updated:** October 3, 2025
**Status:** Phase 1 Complete ✅ - Phase 2 Ready to Begin 🔜
