# 2. System Architecture

This document outlines the high-level architecture of the system. It is designed as a modern web application with a decoupled frontend and backend, supported by a background processing system.

## 2.1. Core Components

The system consists of seven main components:

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

## 2.2. Complete System Architecture Diagram

```
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
        │  │ • Authentication & Authorization (JWT)           │  │
        │  │ • Upload Endpoints                               │  │
        │  │ • Chat Endpoints                                 │  │
        │  │ • Dashboard Management Endpoints                 │  │
        │  │ • Email Notification Endpoints                   │  │
        │  │ • Analytics Endpoints                            │  │
        │  └──────────────────────────────────────────────────┘  │
        └─┬──────────┬──────────────┬────────────────────────┬──┘
          │          │              │                        │
          │          │              │                        │
          ↓          ↓              ↓                        ↓
    ┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐
    │Background│  │ AI Chat  │  │Email Service │  │   Database        │
    │ Worker   │  │ Engine   │  │              │  │  (PostgreSQL/     │
    │          │  │          │  │              │  │   Supabase)       │
    │ • File   │  │• LangChain│ │• Notification│  │                   │
    │   Process│  │• OpenAI  │  │• Reports     │  │• Users            │
    │ • Vendor │  │  GPT-4   │  │• Templates   │  │• Products         │
    │   Detec  │  │• Intent  │  │• SMTP        │  │• sellout_entries2 │
    │ • Data   │  │  Detect  │  │              │  │• ecommerce_orders │
    │   Clean  │  │• Memory  │  │              │  │• conversation_    │
    │ • Report │  │• SQL     │  │              │  │  history          │
    │   Gen    │  │  Validate│  │              │  │• dashboard_configs│
    └─────┬───┘  └────┬─────┘  └──────┬───────┘  │• email_logs       │
      │   │           │                │          │• upload_batches   │
      │   │           │                │          │• error_reports    │
      │   └───────────┴────────────────┴──────────┤                   │
      │                                            └───────────────────┘
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

## 2.3. Key Data Flows

### File Upload & Processing Flow:

1.  User uploads file via **Frontend Application**
2.  File sent to **Backend API Server** upload endpoint
3.  API creates processing job and queues it for **Background Worker**
4.  Background Worker:
    - Detects vendor format
    - Applies vendor-specific normalization
    - Validates and cleans data
    - Writes to **Database** (sellout_entries2 or ecommerce_orders)
5.  **Email Service** sends success/failure notification
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
