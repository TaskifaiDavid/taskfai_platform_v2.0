# 2. System Architecture

This document outlines the high-level architecture of the TaskifAI multi-tenant SaaS platform. It is designed as a modern web application with a decoupled frontend and backend, supported by a background processing system, with tenant-aware data isolation.

## 2.1. Multi-Tenant Architecture Model

TaskifAI implements a **database-per-tenant** architecture for maximum data isolation and security:

### Tenant Isolation Strategy
- **Dedicated Database:** Each customer (tenant) has their own Supabase PostgreSQL database
- **Physical Separation:** Complete data isolation - impossible to query across tenants
- **Custom Schemas:** Each tenant can have unique table structures and configurations
- **Independent Scaling:** Tenants scale independently based on their data volume

### Tenant Context Flow
```
User Request → Subdomain Detection → Tenant Identification → Database Routing → Response
```

1. User accesses `customer1.taskifai.com`
2. System extracts subdomain → identifies tenant_id
3. Loads tenant-specific database configuration
4. All operations execute against tenant's database
5. Response returned to user

### Demo vs Production
- **Demo Mode:** Single database with `tenant_id = "demo"` for initial testing
- **Production Mode:** Database-per-tenant with dynamic connection management

## 2.2. Core Components

The system consists of eight main components:

1.  **Frontend Application:** A single-page application (SPA) built with a modern JavaScript framework. It is responsible for all user interface elements, interactions, data visualization, AI chat interface, and dashboard embedding. It does not contain any business logic.

2.  **Backend API Server:** A central HTTP server that exposes a RESTful API. It handles all business logic, including:
    - User authentication and authorization
    - Data validation and upload processing
    - Serving analytics data to the frontend
    - AI chat query coordination
    - Dashboard configuration management
    - Email notification triggering

3.  **Background Worker:** An asynchronous task processing system that executes long-running jobs, including:
    - Ingestion and cleaning of large data files
    - Vendor-specific data transformations
    - Report generation (PDF, CSV, Excel)
    - Scheduled email delivery

4.  **AI Chat Engine:** An intelligent query processing component that:
    - Accepts natural language questions from users
    - Detects query intent (online sales, offline sales, comparisons, etc.)
    - Generates and validates SQL queries
    - Interfaces with OpenAI GPT-4 for response generation
    - Maintains conversation memory

5.  **Email Service:** A dedicated email handling component that:
    - Sends upload success/failure notifications
    - Generates and delivers scheduled reports
    - Manages email templates and SMTP configuration
    - Logs all email activity for audit trails

6.  **Database:** A relational database (e.g., PostgreSQL/Supabase) that serves as the single source of truth. It stores:
    - User accounts and authentication data
    - Product catalogs
    - Multi-channel sales records (offline B2B and online D2C)
    - Upload history and error reports
    - Conversation history
    - Dashboard configurations
    - Email logs

7.  **External Services:**
    - **OpenAI API:** For AI chat natural language processing
    - **External Dashboards:** Third-party analytics platforms (Looker, Tableau, Power BI, Metabase) embedded via iframes
    - **SMTP Provider:** Email delivery service (SendGrid, Amazon SES, etc.)

8. **Tenant Management Service:** A dedicated component for multi-tenant operations:
    - Tenant provisioning and deprovisioning
    - Subdomain to tenant_id mapping
    - Database connection management and pooling
    - Tenant-specific configuration storage
    - Vendor configuration per tenant

## 2.3. Complete System Architecture Diagram

```
                    ┌──────────────────────────────────────────┐
                    │   Subdomain Routing Layer                │
                    │   customer1.taskifai.com → Tenant ID     │
                    └──────────────────┬───────────────────────┘
                                       ↓
                    ┌─────────────────────────────────────────┐
                    │      Frontend Application (SPA)         │
                    │  ┌───────────────────────────────────┐  │
                    │  │ • File Upload Interface           │  │
                    │  │ • AI Chat Interface               │  │
                    │  │ • Dashboard Embedding (iframes)   │  │
                    │  │ • Analytics Visualizations        │  │
                    │  └───────────────────────────────────┘  │
                    └────────┬────────────────────┬───────────┘
                             │ HTTPS/JSON         │
                             ↓                    ↓
        ┌────────────────────────────────────────────────────────┐
        │           Backend API Server (FastAPI)                 │
        │  ┌──────────────────────────────────────────────────┐  │
        │  │ • Tenant Context Middleware (Subdomain→TenantID) │  │
        │  │ • Authentication & Authorization (JWT)           │  │
        │  │ • Upload Endpoints                               │  │
        │  │ • Chat Endpoints                                 │  │
        │  │ • Dashboard Management Endpoints                 │  │
        │  │ • Email Notification Endpoints                   │  │
        │  │ • Analytics Endpoints                            │  │
        │  │ • Tenant Management API (Admin)                  │  │
        │  └──────────────────────────────────────────────────┘  │
        └─┬──────────┬──────────────┬────────────────────────┬──┘
          │          │              │                        │
          │          │              │                        │
          ↓          ↓              ↓                        ↓
    ┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐
    │Background│  │ AI Chat  │  │Email Service │  │Tenant DB Manager  │
    │ Worker   │  │ Engine   │  │              │  │                   │
    │          │  │          │  │              │  │• Connection Pool  │
    │ • File   │  │• LangChain│ │• Notification│  │• Dynamic Routing  │
    │   Process│  │• OpenAI  │  │• Reports     │  │• Tenant Registry  │
    │ • Vendor │  │  GPT-4   │  │• Templates   │  │                   │
    │   Detec  │  │• Intent  │  │• SMTP        │  │                   │
    │ • Config │  │  Detect  │  │              │  │                   │
    │   Driven │  │• Memory  │  │              │  │                   │
    │ • Report │  │• SQL     │  │              │  │                   │
    │   Gen    │  │  Validate│  │              │  │                   │
    └─────┬───┘  └────┬─────┘  └──────┬───────┘  └─────────┬─────────┘
      │   │           │                │                    │
      │   │           │                │                    ↓
      │   │           │                │          ┌─────────────────────┐
      │   │           │                │          │ Tenant Databases    │
      │   │           │                │          │ (Supabase Projects) │
      │   │           │                │          │                     │
      │   │           │                │          │ Tenant 1 DB         │
      │   └───────────┴────────────────┴──────────┤ • Users             │
      │                                            │ • Products          │
      │                                            │ • sellout_entries2  │
      │                                            │ • vendor_configs    │
      │                                            │ • ...               │
      │                                            │                     │
      │                                            │ Tenant 2 DB         │
      │                                            │ (separate instance) │
      │                                            │                     │
      │                                            │ Demo DB             │
      │                                            │ (initial testing)   │
      │                                            └─────────────────────┘
      │
      └─────────────────────────────────────┐
                                            ↓
                        ┌───────────────────────────────────┐
                        │    External Services              │
                        │  ┌─────────────────────────────┐  │
                        │  │ • OpenAI API (GPT-4)        │  │
                        │  │ • SMTP Provider (SendGrid)  │  │
                        │  │ • External Dashboards:      │  │
                        │  │   - Looker Studio           │  │
                        │  │   - Tableau                 │  │
                        │  │   - Power BI                │  │
                        │  │   - Metabase                │  │
                        │  └─────────────────────────────┘  │
                        └───────────────────────────────────┘
```

## 2.4. Key Data Flows

### Tenant-Aware Request Flow:

1. User accesses `customer1.taskifai.com`
2. **Subdomain Detection**: Middleware extracts subdomain
3. **Tenant Identification**: Maps subdomain → tenant_id from registry
4. **Database Routing**: Loads tenant-specific database connection
5. **Request Processing**: All operations execute against tenant's database
6. **Response**: Data returned to user (only from their database)

### File Upload & Processing Flow (Tenant-Aware):

1.  User uploads file via **Frontend Application** (on customer1.taskifai.com)
2.  File sent to **Backend API Server** upload endpoint (with tenant context)
3.  API creates processing job with tenant_id and queues it for **Background Worker**
4.  Background Worker (tenant-aware):
    - Loads tenant-specific database connection
    - Detects vendor format
    - Loads vendor configuration from tenant's database
    - Applies configuration-driven normalization
    - Validates and cleans data
    - Writes to tenant's **Database** (sellout_entries2 or ecommerce_orders)
5.  **Email Service** sends success/failure notification (tenant-branded)
6.  Frontend polls status endpoint for completion

### AI Chat Query Flow:

1.  User types question in **Frontend Application** chat interface
2.  Question sent to **Backend API Server** chat endpoint
3.  API forwards to **AI Chat Engine**:
    - Loads conversation memory from **Database**
    - Detects intent (online/offline/comparison)
    - Queries appropriate sales data from **Database**
    - Sends data + question to **OpenAI API**
    - Receives natural language response
    - Saves conversation to **Database**
4.  Response returned to Frontend

### Dashboard Embedding Flow:

1.  User configures dashboard via **Frontend Application**
2.  Configuration saved to **Backend API Server**
3.  Backend stores in **Database** (dashboard_configs table)
4.  Frontend embeds external dashboard URL in iframe
5.  External dashboard content loads from **External Services**

### Scheduled Report Flow:

1.  **Background Worker** triggers on schedule
2.  Queries sales data from **Database**
3.  Generates report (PDF/CSV/Excel)
4.  Sends to **Email Service**
5.  Email delivered via **SMTP Provider**
6.  Activity logged in **Database** (email_logs)
