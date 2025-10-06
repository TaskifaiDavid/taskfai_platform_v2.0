# Product Requirements Document: TaskifAI Multi-Tenant SaaS Platform

**Version:** 2.0

**Status:** Active Development

## 1. Introduction

### 1.1. Problem Statement

Businesses in retail and distribution lack a unified and timely view of product sales performance across a diverse landscape of third-party resellers. Each reseller provides data in a different, inconsistent format, requiring significant manual effort to clean, standardize, and aggregate. This process is slow, error-prone, and prevents effective analysis and decision-making.

**Multi-Tenant Challenge:** Each business needs complete data isolation from competitors while benefiting from a shared, continuously-improving SaaS platform.

### 1.2. Vision & Goal

To create a **multi-tenant SaaS platform** that provides each customer with a central, automated system for ingesting, cleaning, and standardizing sales data from all their resellers. The platform delivers:

- **Complete Data Isolation:** Each customer has their own dedicated database
- **Customizable Processing:** Tenant-specific vendor configurations without code changes
- **Scalable Architecture:** Database-per-tenant model for maximum security and flexibility
- **SaaS Efficiency:** Single codebase serves all customers with instant updates

## 2. User Personas

### 2.1. SaaS Customers (Tenants)

The platform serves multiple independent customers (tenants), each operating in retail/distribution:

- **Tenant Organization:** Company accessing via branded subdomain (e.g., customer1.taskifai.com)
- **Isolated Environment:** Dedicated database, custom configurations, separate user accounts
- **Self-Service:** Ability to customize vendor processing rules without vendor intervention

### 2.2. End Users (Within Each Tenant)

Within each customer organization, the intended users include:

-   **Sales Analysts:** Track performance, identify trends, and create detailed reports
-   **Account Managers:** Monitor the sales activity of their specific reseller partners
-   **Business Intelligence Teams:** Reliable, clean data source to feed into larger corporate analytics platforms
-   **Management:** High-level, aggregated overview of company-wide sales performance to inform strategic decisions

### 2.3. Platform Administrators

-   **TaskifAI Admins:** Manage tenant provisioning, platform updates, and system-wide configurations

## 3. Product & Feature Requirements

### 3.1. Epic: User Authentication & Management

-   **Secure Login:** Users must be able to log in to the system with an email and password.
-   **Session Management:** The system must provide secure session management (e.g., JWT) and a way for users to log out.
-   **User Roles:** The system must support at least two roles: `analyst` (standard user) and `admin` (can manage user accounts).

### 3.2. Epic: Data Ingestion & Processing

-   **File Upload:** Users must be able to upload sales data files (CSV, XLSX) via a web interface.
-   **Asynchronous Processing:** File processing must happen asynchronously in the background to keep the UI responsive. The user must be able to see the status of their upload (`Pending`, `Processing`, `Completed`, `Failed`).
-   **Upload History:** Users must be able to see a history of their past uploads.
-   **Flexible Cleaning Engine:** The system must have a configurable data processing pipeline capable of:
    -   **Column Mapping:** Mapping arbitrary source column names to standard system fields.
    -   **Data Type Conversion:** Converting text-based numbers and dates into standard formats.
    -   **Value Standardization:** Normalizing categorical values (e.g., country codes).
    -   **Entity Resolution:** Matching products in the file to the canonical product list in the database.
    -   **Calculated Fields:** Deriving new fields from existing ones (e.g., `total_revenue`).

### 3.3. Epic: AI-Powered Data Chat

-   **Natural Language Queries:** Users must be able to ask questions about their sales data in plain English without writing SQL queries.
-   **Conversation Memory:** The system must maintain conversation context, allowing users to ask follow-up questions that reference previous exchanges.
-   **Intent Detection:** The system must automatically detect query intent (online sales, offline sales, comparisons, time analysis, product analysis, reseller analysis).
-   **Multi-Channel Analysis:** The AI must intelligently route queries to appropriate data sources (offline B2B sales, online ecommerce sales, or combined).
-   **Secure Querying:** The system must validate all generated SQL queries to prevent data manipulation and ensure read-only access.
-   **User Data Isolation:** Each user must only be able to query their own sales data through the AI chat.

### 3.4. Epic: External Dashboard Management

-   **Dashboard Embedding:** Users must be able to connect and embed external analytics dashboards (Looker, Tableau, Power BI, Metabase) into the platform.
-   **Multi-Dashboard Support:** The system must support multiple dashboards per user with a tab-based interface for easy switching.
-   **Dashboard CRUD:** Users must be able to create, view, update, and delete dashboard configurations.
-   **Fullscreen Mode:** Users must be able to view dashboards in fullscreen mode for presentations.
-   **External Access:** Users must be able to open dashboards in new tabs for multi-monitor workflows.
-   **Primary Dashboard:** Users must be able to designate one dashboard as primary, which loads by default.

### 3.5. Epic: Analytics & Reporting

-   **KPI Summary:** The main dashboard must display key performance indicators, including total revenue, total units sold, and top-selling products for a selected period.
-   **Multi-Channel Analytics:** The system must support analysis of both online (D2C ecommerce) and offline (B2B wholesale) sales channels.
-   **Geographic Analysis:** For online sales, the system must provide country and city-level performance metrics.
-   **Marketing Attribution:** The system must track and analyze UTM parameters (source, medium, campaign) and device types for online sales.
-   **Detailed Reporting:** Users must be able to view and export detailed, paginated reports of individual sales transactions.
-   **Multiple Export Formats:** Reports must be exportable in PDF (for presentations), CSV (for analysis), and Excel (for manipulation) formats.
-   **Filtering:** All dashboard widgets and reports must be filterable by date range, reseller, product, channel, and geography.

### 3.6. Epic: Error Handling

-   **Error Reports:** When a file fails to process, the user must be able to view a detailed error report that specifies the row number and a clear error message for each issue.
-   **Error Statistics:** Users must see aggregate error metrics (total errors, error types, affected rows).
-   **Partial Success:** The system must process valid rows even when some rows fail, reporting both success and error counts.

### 3.7. Epic: Email Notifications & Scheduled Reports

-   **Upload Notifications:** The system must send automatic email notifications to users upon success or failure of file uploads. Failure notifications must include a direct link to the error report.
-   **Success Summaries:** Success emails must include processing statistics (rows processed, total sales, date range, processing time).
-   **Scheduled Reports:** Users must be able to configure automated report delivery on daily, weekly, or monthly schedules.
-   **Report Format Selection:** Users must be able to choose report format for scheduled deliveries (PDF, CSV, Excel).
-   **Email Audit Log:** The system must maintain a log of all emails sent for compliance and troubleshooting.

### 3.8. Epic: Multi-Tenant Management & Configuration

-   **Tenant Provisioning:** Platform admins must be able to create new tenants (customers) via secure API
-   **Subdomain Assignment:** Each tenant must have a unique subdomain (customer1.taskifai.com)
-   **Database Isolation:** Each tenant must have a dedicated database (Supabase project)
-   **Vendor Configuration:** Tenants must be able to customize vendor processing rules via configuration (no code changes)
-   **Default Configurations:** System must provide baseline vendor configurations that tenants can override
-   **Configuration Inheritance:** Tenant configs must inherit from defaults and only override specific parameters
-   **Tenant Suspension:** Platform admins must be able to suspend/reactivate tenants
-   **Tenant Registry:** Secure master database must maintain subdomain→tenant_id→database_url mappings
-   **Connection Management:** System must dynamically route database connections based on tenant context
-   **Tenant Context Security:** All requests must be scoped to the authenticated tenant (no cross-tenant data access)

## 4. Data & System Requirements

### 4.1. Data Model

The system must capture the following data points for each sales transaction to enable in-depth analysis:

**Offline Sales (B2B/Wholesale):**
-   **Identifiers:** `sale_id`, `user_id`, `product_id`, `reseller_id`, `upload_batch_id`
-   **Product:** `functional_name`, `product_ean` (nullable)
-   **Temporal:** `month`, `year`
-   **Financial:** `quantity`, `sales_eur`, `currency` (original currency)
-   **Source:** `reseller` (partner name)

**Online Sales (D2C/Ecommerce):**
-   **Identifiers:** `order_id`, `user_id`
-   **Product:** `functional_name`, `product_ean`, `product_name`
-   **Temporal:** `order_date` (full date)
-   **Financial:** `quantity`, `sales_eur`, `cost_of_goods`, `stripe_fee`
-   **Geographic:** `country`, `city`
-   **Marketing:** `utm_source`, `utm_medium`, `utm_campaign`, `device_type`

**AI Chat Memory:**
-   **Conversation:** `conversation_id`, `user_id`, `session_id`, `user_message`, `ai_response`, `timestamp`

**Dashboard Configurations:**
-   **Dashboard:** `config_id`, `user_id`, `dashboard_name`, `dashboard_type`, `dashboard_url`, `authentication_method`, `is_active`

**Email Audit:**
-   **Email Log:** `log_id`, `user_id`, `email_type`, `recipient_email`, `subject`, `sent_at`, `status`, `error_message`

### 4.2. System Architecture

The system will be composed of:
-   A **Subdomain Routing Layer** for tenant identification
-   A **Decoupled Frontend Application** (SPA) - shared across all tenants
-   A **Backend API Server** with tenant context middleware
-   A **Background Worker** for tenant-aware asynchronous processing
-   A **Database-per-Tenant Architecture** (multiple Supabase projects)
-   A **Master Tenant Registry** for subdomain→tenant_id→database mapping
-   A **Configuration-Driven Vendor Processing Engine** for tenant customization

## 5. Technical Implementation Notes

### 5.1. AI Chat System
-   **AI Provider:** OpenAI GPT-4 for natural language understanding and response generation
-   **Framework:** LangChain for SQL agent orchestration
-   **Memory:** Database-backed conversation persistence (short-term: 10 messages, long-term: full history)
-   **Security:** SQL injection prevention, read-only queries, user data isolation

### 5.2. Multi-Channel Data
-   **Offline Channel:** Monthly aggregated B2B sales from reseller partners (`sellout_entries2` table)
-   **Online Channel:** Individual D2C ecommerce orders with marketing attribution (`ecommerce_orders` table)
-   **Normalization:** All sales converted to EUR for consistent analysis

### 5.3. Vendor Support
The system must support automated detection and processing of the following vendor formats:
-   Galilu (Poland) - PLN, pivot format, NULL EAN support
-   Boxnox (Europe) - EUR, "Sell Out by EAN" sheet
-   Skins SA (South Africa) - ZAR, OrderDate column, auto-month detection
-   CDLC (Europe) - EUR, header row 4, dynamic Total column
-   Selfridges (UK) - GBP, retail format
-   Liberty (UK) - GBP, supplier report
-   Ukraine Distributors - UAH, TDSheet format
-   Continuity Suppliers (UK) - GBP, size reports
-   Skins NL (Netherlands) - EUR, SalesPerSKU sheet

### 5.4. Performance Requirements
-   **File Processing:** Support files up to 100MB
-   **Processing Time:** Typical files (500-5000 rows) should process in 1-2 minutes
-   **AI Chat Response:** Average response time under 5 seconds
-   **Dashboard Loading:** External dashboards should load within 3 seconds (network permitting)

## 6. Out of Scope (Version 1.0)

The following features will not be included in the initial release:

-   Direct, real-time API integration with reseller systems
-   Advanced, customizable user roles and permissions beyond `admin` and `analyst`
-   User-configurable cleaning rules via the UI (rules configured at application level)
-   Machine learning-based sales forecasting
-   AI chat visualization generation (charts in response)
-   Voice input for AI chat queries
-   Multi-language support (English only for v1.0)
-   Webhook integrations with external systems
-   Mobile native applications (web-responsive only)
