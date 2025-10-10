# TaskifAI Platform - System Architecture Overview

**Version**: 2.0
**Last Updated**: 2025-10-10
**Status**: Production-Ready

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Technology Stack](#technology-stack)
3. [System Components](#system-components)
4. [Data Flow](#data-flow)
5. [Multi-Tenant Architecture](#multi-tenant-architecture)
6. [Security Model](#security-model)
7. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

TaskifAI is a **multi-tenant SaaS platform** for sales data analytics with AI-powered insights. The system follows a **microservices-inspired monolithic architecture** with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  React 19 SPA (Vite 6 + TypeScript + Tailwind CSS v4)           │
│  - Multi-tenant routing (subdomain-based)                        │
│  - Dynamic dashboard widgets                                     │
│  - Real-time file upload tracking                                │
│  - AI chat interface                                             │
└──────────────────┬──────────────────────────────────────────────┘
                   │ HTTPS / REST API
┌──────────────────▼──────────────────────────────────────────────┐
│                     API GATEWAY LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Python 3.11+)                                  │
│  - Middleware Stack (CORS, Auth, Tenant Context, Logging)       │
│  - Rate Limiting (10 req/min per IP)                             │
│  - JWT Authentication with tenant claims                         │
│  - RESTful API endpoints                                         │
└──────┬──────────────────┬──────────────────┬───────────────────┘
       │                  │                  │
       │ Service Layer    │ Task Queue       │ Database
       │                  │                  │
┌──────▼────────┐  ┌──────▼────────┐  ┌──────▼────────┐
│   Business    │  │  Background   │  │   Database    │
│   Logic       │  │    Workers    │  │   Layer       │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ - Vendor      │  │ Celery Worker │  │ Supabase      │
│   Detection   │  │ - File        │  │ (PostgreSQL   │
│ - Data        │  │   Processing  │  │  17 + RLS)    │
│   Processing  │  │ - Email       │  │               │
│ - AI Agent    │  │   Sending     │  │ - ecommerce_  │
│ - Tenant      │  │               │  │   orders      │
│   Discovery   │  │ Redis Broker  │  │ - sellout_    │
│               │  │ (Task Queue)  │  │   entries2    │
│               │  │               │  │ - products    │
│               │  │               │  │ - users       │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Technology Stack

### Frontend
- **Framework**: React 19 (latest features: automatic batching, transitions)
- **Build Tool**: Vite 6 (fast dev server, optimized builds)
- **Language**: TypeScript 5.x (type safety)
- **Styling**: Tailwind CSS v4 (utility-first CSS)
- **State Management**: Zustand (lightweight, no boilerplate)
- **HTTP Client**: Axios (centralized API client with interceptors)
- **Routing**: React Router v6 (subdomain-aware routing)

### Backend
- **Framework**: FastAPI 0.115+ (Python async web framework)
- **Language**: Python 3.11+ (performance improvements, type hints)
- **Validation**: Pydantic v2 (data validation and serialization)
- **Task Queue**: Celery 5.x (async task processing)
- **Message Broker**: Redis 7.x (Celery broker + caching)
- **Database**: Supabase (PostgreSQL 17 with built-in RLS)
- **AI/LLM**: LangChain + OpenAI GPT-4o-mini (SQL generation)

### Infrastructure
- **Hosting**: DigitalOcean App Platform (managed PaaS)
- **Database**: Supabase Cloud (managed PostgreSQL)
- **CDN**: Cloudflare (DDoS protection, SSL)
- **Email**: SendGrid (transactional emails)
- **Monitoring**: Supabase Dashboard + DigitalOcean Insights

---

## System Components

### 1. Frontend Application (`frontend/src/`)

**Purpose**: Single-page application for user interaction

**Key Components**:
```
components/
├─ features/          # Feature-specific components (future refactor)
│  ├─ auth/           # LoginForm, TenantSelector, ProtectedRoute
│  ├─ upload/         # FileUpload, UploadStatus, UploadHistory
│  ├─ analytics/      # SalesTable, KPICard, ExportButton
│  └─ dashboard/      # DynamicDashboard, widgets/
├─ ui/                # Reusable UI primitives (buttons, cards, dialogs)
└─ layout/            # App shell (Sidebar, Header, Layout)

pages/                # Route-level pages
├─ LoginPortal.tsx    # Central login (app.taskifai.com)
├─ Login.tsx          # Tenant-specific login
├─ Dashboard.tsx      # Main analytics dashboard
├─ Uploads.tsx        # File upload interface
├─ Chat.tsx           # AI chat assistant
├─ Analytics.tsx      # Advanced analytics
└─ Admin.tsx          # Admin panel (role-based access)

stores/               # Zustand state management
└─ auth.ts            # Global authentication state

api/                  # API service layer
├─ auth.ts            # Authentication requests
├─ uploads.ts         # File upload requests
├─ analytics.ts       # Analytics queries
└─ dashboardConfig.ts # Dashboard configuration
```

**Patterns**:
- **Protected Routes**: HOC wrapping for authentication
- **Subdomain Routing**: Extract tenant from `X-Tenant-Subdomain` header
- **Token Management**: Axios interceptors for JWT injection
- **Error Handling**: Global error boundary + toast notifications

---

### 2. Backend API (`backend/app/`)

**Purpose**: RESTful API server with business logic

**Module Structure**:
```
api/                  # API route handlers (thin controllers)
├─ auth.py            # User authentication (register, login, logout)
├─ tenant_discovery.py # Tenant routing (discover, login-and-discover, exchange)
├─ uploads.py         # File upload endpoints
├─ chat.py            # AI chat interface
├─ analytics.py       # Data analytics queries
├─ dashboards.py      # Dashboard management
├─ dashboard_config.py # Dashboard configuration CRUD
└─ admin.py           # Admin operations

core/                 # Core utilities and configuration
├─ config.py          # Settings (env vars, Pydantic BaseSettings)
├─ security.py        # JWT creation/validation, password hashing
├─ dependencies.py    # FastAPI dependencies (Supabase client)
├─ rate_limiter.py    # In-memory rate limiting (production: use Redis)
├─ rate_limit_dependency.py # FastAPI rate limit dependency
└─ token_blacklist.py # One-time use token enforcement

models/               # Pydantic request/response models
├─ user.py            # User, UserCreate, UserLogin, AuthResponse
├─ tenant.py          # Tenant discovery models
├─ upload.py          # Upload request/response models
└─ dashboard_config.py # Dashboard configuration models

services/             # Business logic layer
├─ vendors/           # Vendor-specific file processors
│  ├─ detector.py     # Auto-detect vendor from file structure
│  ├─ boxnox_processor.py
│  ├─ galilu_processor.py
│  └─ ...            # 9+ vendor processors
├─ ai_chat/           # AI chat system
│  ├─ agent.py        # LangChain SQL agent
│  └─ security.py     # SQL security validation
├─ email/             # Email notifications
├─ tenant_discovery.py # Tenant lookup logic
└─ tenant_auth_discovery.py # Combined auth + tenant discovery

middleware/           # Request/response middleware
├─ auth.py            # JWT validation, tenant match verification
├─ tenant_context.py  # Subdomain extraction, tenant resolution
└─ logging.py         # Request logging

workers/              # Celery background tasks
├─ celery_app.py      # Celery configuration
└─ tasks.py           # Task definitions (file processing, emails)

db/                   # Database schema and migrations
├─ schema.sql         # Full database schema
├─ seed_vendor_configs.sql # Vendor configuration data
└─ migrations/        # Manual migration scripts
```

**Middleware Stack (Execution Order)**:
```
Request → TenantContext → Auth → Logging → Route Handler → Response
          (FIRST)         (2nd)   (LAST)
```

**Key Patterns**:
- **Dependency Injection**: FastAPI's `Depends()` for Supabase client, rate limiting
- **Middleware Composition**: LIFO stack (last added executes first)
- **Service Layer**: Thin controllers delegate to service classes
- **Error Handling**: HTTPException with structured error responses

---

### 3. Background Workers (`backend/app/workers/`)

**Purpose**: Async task processing for long-running operations

**Architecture**:
```
┌────────────┐        ┌────────────┐        ┌────────────┐
│  FastAPI   │──task─→│   Redis    │◄──poll─│  Celery    │
│  Backend   │        │  (Broker)  │        │  Worker    │
└────────────┘        └────────────┘        └────────────┘
                                                   │
                                                   │ execute
                                                   ▼
                                            ┌──────────────┐
                                            │  Task Logic  │
                                            │ - File Parse │
                                            │ - Vendor     │
                                            │   Detection  │
                                            │ - Data       │
                                            │   Transform  │
                                            │ - DB Insert  │
                                            └──────────────┘
```

**Configuration**:
- **Concurrency**: `worker_prefetch_multiplier=4` (24 concurrent tasks)
- **Task Queues**: `file_processing`, `notifications`
- **Time Limit**: 30 minutes per task
- **Result Backend**: Redis (task status tracking)

**Task Types**:
1. **File Processing** (`process_upload`):
   - Vendor auto-detection
   - File parsing (CSV, XLSX, JSON)
   - Data normalization
   - Batch insert to Supabase

2. **Email Notifications** (`send_upload_notification`):
   - SendGrid integration
   - Upload success/failure emails

---

### 4. Database Layer (Supabase)

**Purpose**: Persistent data storage with Row-Level Security

**Key Tables**:

| Table | Purpose | RLS Enabled |
|-------|---------|-------------|
| `users` | User accounts (per tenant) | ✅ Yes |
| `ecommerce_orders` | D2C/online sales (primary) | ✅ Yes |
| `sellout_entries2` | B2B/offline sales | ✅ Yes |
| `products` | Product catalog | ✅ Yes |
| `vendor_configs` | Vendor-specific parsing rules | ❌ No (global) |
| `uploads` | File upload tracking | ✅ Yes |
| `dashboard_configs` | User dashboard layouts | ✅ Yes |

**Critical Pattern**:
```python
# Backend uses service_key (bypasses RLS)
# MUST manually filter by user_id

query = supabase.table("ecommerce_orders")\
    .select("*")\
    .eq("user_id", user_id)\  # REQUIRED!
    .execute()
```

**RLS Policies** (enforced by Supabase):
- `SELECT`: `WHERE user_id = auth.uid()`
- `INSERT`: `WHERE user_id = auth.uid()`
- `UPDATE`: `WHERE user_id = auth.uid()`
- `DELETE`: `WHERE user_id = auth.uid()`

---

## Data Flow

### 1. File Upload Flow
```
User Upload → FastAPI Endpoint → Validate File → Save to /tmp
                                                     │
                                                     ▼
                                            Celery Task (Async)
                                                     │
                                ┌────────────────────┴──────────────────────┐
                                │                                           │
                         Vendor Detection                           Parse File
                         (9+ processors)                          (CSV/XLSX/JSON)
                                │                                           │
                                └────────────────┬──────────────────────────┘
                                                 │
                                          Normalize Data
                                          (Unified Schema)
                                                 │
                                          Batch Insert
                                          (Supabase)
                                                 │
                                          Send Email
                                          (SendGrid)
```

### 2. AI Chat Flow
```
User Question → FastAPI /chat → LangChain Agent
                                      │
                                      ├─ Intent Detection
                                      ├─ SQL Generation (GPT-4o-mini)
                                      ├─ Security Validation (no INSERT/UPDATE/DELETE)
                                      ├─ User Filter Injection (WHERE user_id = '...')
                                      │
                                      ▼
                               Execute SQL (Supabase)
                                      │
                                      ▼
                               Generate Response (Natural Language)
                                      │
                                      ▼
                               Return to User
```

### 3. Multi-Tenant Login Flow
```
User Email → /auth/discover-tenant → Registry DB Lookup
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                              │
              Single Tenant                                 Multi-Tenant
                    │                                              │
           Redirect to                                   Return Tenant List
           tenant.taskifai.com/login                              │
                    │                                              │
           /auth/login                                    User Selects Tenant
                    │                                              │
           JWT Token                                      /auth/exchange-token
                    │                                              │
           Dashboard                                      JWT Token → Dashboard
```

---

## Multi-Tenant Architecture

**Strategy**: Subdomain-based tenant isolation with centralized registry

**Components**:
1. **Tenant Registry** (Separate Supabase project):
   - `tenants` table (subdomain → tenant_id mapping)
   - `user_tenants` table (email → tenant associations)

2. **Tenant Context Middleware**:
   - Extracts subdomain from request
   - Resolves tenant from registry
   - Injects `request.state.tenant`

3. **JWT Claims**:
   ```json
   {
     "sub": "user_id",
     "email": "user@example.com",
     "role": "analyst",
     "tenant_id": "uuid",
     "subdomain": "acme"
   }
   ```

**Data Isolation**:
- ✅ **Application-Level**: `WHERE user_id = '...'` in all queries
- ✅ **Database-Level**: Supabase RLS policies
- ✅ **Frontend-Level**: Subdomain routing

---

## Security Model

### Authentication
- **JWT Tokens**: HS256 algorithm, 24-hour expiry
- **Password Hashing**: bcrypt (12 rounds)
- **Rate Limiting**: 10 requests/minute per IP (prevent brute force)

### Authorization
- **Role-Based Access Control** (RBAC):
  - `analyst`: Standard user (read analytics, upload files)
  - `admin`: Full access (manage users, settings)

### Data Security
- **Row-Level Security** (RLS): Database-enforced data isolation
- **SQL Injection Prevention**: Parameterized queries, LangChain validation
- **XSS Prevention**: React auto-escaping, CSP headers
- **CSRF Protection**: JWT in headers (not cookies)

### API Security
- **CORS**: Restricted to `*.taskifai.com` + localhost
- **HTTPS Only**: TLS 1.3 (Cloudflare)
- **Token Blacklist**: One-time use enforcement for temp tokens

---

## Deployment Architecture

**Production Setup** (DigitalOcean App Platform):

```
┌─────────────────────────────────────────────────────────────┐
│                      Cloudflare CDN                          │
│  - DDoS Protection                                           │
│  - SSL/TLS (*.taskifai.com wildcard cert)                   │
│  - DNS Management (subdomain routing)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│             DigitalOcean App Platform                        │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Static Site)                                      │
│  - React build artifacts                                     │
│  - Served via Nginx                                          │
│                                                              │
│  Backend (Web Service)                                       │
│  - uvicorn (1 worker for faster startup)                    │
│  - Auto-scaling: 1-3 instances                              │
│                                                              │
│  Worker (Worker Service)                                     │
│  - Celery worker (24 concurrent tasks)                      │
│  - Auto-scaling: 1-2 instances                              │
│                                                              │
│  Redis (Managed Database)                                    │
│  - Celery broker + cache                                     │
│  - Shared across backend + worker                           │
└─────────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Supabase Cloud                               │
│  - PostgreSQL 17 (primary database)                          │
│  - Row-Level Security (RLS)                                  │
│  - Automatic backups                                         │
│  - Connection pooling (pgbouncer)                            │
└─────────────────────────────────────────────────────────────┘
```

**Environment Variables** (Critical):
- `SECRET_KEY`: JWT signing key (min 32 chars)
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Bypass RLS (backend only)
- `OPENAI_API_KEY`: AI chat functionality
- `REDIS_URL`: Celery broker connection
- `SENDGRID_API_KEY`: Email notifications

---

## Performance Characteristics

**Frontend**:
- Initial Load: < 2s (Vite optimized build)
- Time to Interactive: < 3s
- Bundle Size: ~500KB (gzipped)

**Backend**:
- API Response Time: < 200ms (median)
- File Upload Processing: 10-30 seconds (10,000 rows)
- Concurrent Uploads: 24 simultaneous files

**Database**:
- Query Response Time: < 100ms (indexed queries)
- Connection Pool: 20 connections (pgbouncer)
- RLS Overhead: ~10ms per query

---

## Monitoring & Observability

**Application Logs**:
- FastAPI: Request/response logging (middleware)
- Celery: Task execution logs
- Frontend: Error boundary + Sentry (future)

**Metrics**:
- Supabase Dashboard: Query performance, connection usage
- DigitalOcean Insights: CPU, memory, network
- Redis Metrics: Queue length, task latency

**Alerts**:
- Supabase: High query latency, connection pool exhaustion
- DigitalOcean: High error rate, resource exhaustion
- SendGrid: Bounce rate, delivery failures

---

## Future Architecture Improvements

1. **Service Layer Extraction** (In Progress):
   - Move business logic from API routes to service classes
   - Improve testability and separation of concerns

2. **Redis-Based Rate Limiting**:
   - Replace in-memory rate limiter with Redis
   - Enable distributed rate limiting across instances

3. **Caching Layer**:
   - Add Redis caching for frequently accessed data
   - Reduce database load for analytics queries

4. **Event-Driven Architecture**:
   - Implement event bus (Redis Streams)
   - Decouple components for better scalability

5. **Microservices Migration** (Long-term):
   - Split into: Auth Service, Upload Service, Analytics Service, AI Service
   - Enable independent scaling and deployment

---

## Related Documentation

- [Refactoring Improvements](./REFACTORING_IMPROVEMENTS.md)
- [API Reference](../api/)
- [Development Guide](../development/GETTING_STARTED.md)
- [Deployment Guide](../../DEPLOYMENT_GUIDES/)
