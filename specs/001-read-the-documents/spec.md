# Feature Specification: TaskifAI Multi-Tenant SaaS Platform

**Feature Branch**: `001-read-the-documents`
**Created**: 2025-10-06
**Status**: Draft
**Input**: User description: "Read the documents in ./project_docs to get an understanding of what I want to build."

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing

### Primary User Story

**Tenant Organization (e.g., Retail Company)**

A retail company sells products through multiple third-party resellers (distributors, online marketplaces, retail partners). Each reseller sends monthly sales reports in different formats (Excel, CSV) with inconsistent column names, currencies, and data structures. The company needs to:

1. Upload sales files from various resellers to a centralized platform
2. Have the system automatically detect the reseller format and clean/standardize the data
3. View consolidated sales analytics across all resellers
4. Ask questions about their sales data in plain English without writing SQL
5. Embed external analytics dashboards (Looker, Tableau, Power BI) for advanced visualization
6. Receive email notifications when uploads succeed or fail
7. Export reports in multiple formats (PDF, CSV, Excel)

**End User Personas within Tenant:**
- **Sales Analysts**: Track product performance, identify trends, create reports
- **Account Managers**: Monitor specific reseller partner sales activity
- **BI Teams**: Access clean, standardized data for corporate analytics
- **Management**: High-level sales performance overview for strategic decisions

**Platform Administrator (TaskifAI Admin)**

A platform administrator manages multiple independent customer organizations (tenants):

1. Provision new tenants with dedicated databases and subdomain access
2. Monitor platform-wide performance and resource usage
3. Suspend or reactivate tenant accounts as needed
4. Manage system-wide updates that automatically propagate to all tenants

### Acceptance Scenarios

#### Scenario 1: File Upload & Processing
1. **Given** a user has sales data from reseller "Galilu" in Excel format, **When** they upload the file via the web interface, **Then** the system automatically detects it as Galilu format, processes it asynchronously, and notifies the user via email upon completion
2. **Given** a file contains 500 valid rows and 10 invalid rows, **When** processing completes, **Then** the system saves the 500 valid rows, generates an error report for the 10 failed rows, and displays both success and error counts

#### Scenario 2: AI-Powered Data Chat
1. **Given** a user has uploaded sales data, **When** they ask "What were my top 5 products last month?", **Then** the system generates and executes a SQL query, returns results in natural language, and maintains conversation context for follow-up questions
2. **Given** a user asks "Compare online vs offline sales", **When** the query is processed, **Then** the AI intelligently routes the query to both data sources and presents a combined analysis

#### Scenario 3: Multi-Tenant Isolation
1. **Given** Customer A and Customer B both use the platform, **When** Customer A uploads their sales data, **Then** Customer B cannot access, view, or query Customer A's data under any circumstances
2. **Given** a tenant accesses via subdomain customer1.taskifai.com, **When** they authenticate, **Then** all database operations are automatically scoped to their dedicated database

#### Scenario 4: Dashboard Management
1. **Given** a user has a Looker Studio dashboard, **When** they configure the dashboard URL and authentication, **Then** the dashboard is embedded in the platform and accessible via tabs
2. **Given** a user has multiple dashboards, **When** they designate one as primary, **Then** that dashboard loads by default on the dashboards page

#### Scenario 5: Tenant Provisioning
1. **Given** a platform admin wants to onboard a new customer, **When** they create a tenant via admin API with company name and subdomain, **Then** the system automatically provisions a dedicated database, applies schema, seeds configurations, and sends welcome email

### Edge Cases

- What happens when a user uploads a file format the system doesn't recognize?
  - System should display a clear error message identifying that the vendor format is unknown and suggest manual configuration or support contact

- How does the system handle duplicate file uploads?
  - User should be warned if uploading a file with the same name/checksum and given options to append or replace existing data

- What happens if a tenant exceeds their database storage limit?
  - System should notify tenant admin via email and prevent new uploads until storage is increased or data is deleted

- How does AI chat handle ambiguous queries?
  - System should ask clarifying questions (e.g., "Did you mean online sales or offline sales?") rather than guessing

- What happens if external dashboard URL becomes invalid?
  - System should detect the error, display a user-friendly message in the iframe, and allow user to update the configuration

- How does the system handle tenant suspension?
  - When a tenant is suspended, all users of that tenant should be immediately logged out and prevented from accessing the system until reactivation

---

## Requirements

### Functional Requirements

#### Multi-Tenancy & Security
- **FR-001**: System MUST provide complete data isolation between tenants using dedicated databases per customer
- **FR-002**: Each tenant MUST access the platform via a unique subdomain (e.g., customer1.taskifai.com, customer2.taskifai.com)
- **FR-003**: System MUST validate subdomain on every request and route all database operations to the correct tenant database
- **FR-004**: Cross-tenant data access MUST be physically impossible due to database-per-tenant architecture
- **FR-005**: Platform administrators MUST have separate authentication and cannot access tenant user data
- **FR-006**: All tenant database credentials MUST be encrypted at rest
- **FR-007**: System MUST support tenant suspension that immediately blocks all access for that tenant's users

#### User Authentication & Management
- **FR-008**: Users MUST be able to log in with email and password
- **FR-009**: System MUST use secure session management with token-based authentication
- **FR-010**: System MUST support two roles within each tenant: "analyst" (standard user) and "admin" (user management)
- **FR-011**: Tenant admins MUST be able to create, update, and delete user accounts within their organization
- **FR-012**: Each user's data MUST be isolated within their tenant database using row-level security

#### Data Ingestion & Processing
- **FR-013**: Users MUST be able to upload sales data files in CSV and Excel formats via web interface
- **FR-014**: File processing MUST occur asynchronously in the background without blocking the UI
- **FR-015**: System MUST display upload status (Pending, Processing, Completed, Failed) in real-time
- **FR-016**: Users MUST be able to view a history of all their past uploads with status and timestamps
- **FR-017**: System MUST automatically detect vendor format based on file structure and content patterns
- **FR-018**: System MUST support configurable data processing per tenant for vendor-specific transformations
- **FR-019**: Processing pipeline MUST support: column mapping, data type conversion, value standardization, entity resolution, calculated fields
- **FR-020**: System MUST support at least 9 different vendor formats: Galilu, Boxnox, Skins SA, CDLC, Selfridges, Liberty, Ukraine Distributors, Continuity Suppliers, Skins NL
- **FR-021**: Tenant configurations MUST be stored in tenant databases and loaded dynamically without code changes
- **FR-022**: System MUST process valid rows even when some rows fail, reporting both success and error counts

#### AI-Powered Data Chat
- **FR-023**: Users MUST be able to ask questions about their sales data in natural language (plain English)
- **FR-024**: System MUST maintain conversation context to allow follow-up questions that reference previous exchanges
- **FR-025**: System MUST automatically detect query intent: online sales, offline sales, comparisons, time analysis, product analysis, reseller analysis
- **FR-026**: AI MUST intelligently route queries to appropriate data sources (offline B2B, online D2C, or combined)
- **FR-027**: All AI-generated SQL queries MUST be validated to prevent data manipulation and ensure read-only access
- **FR-028**: AI chat MUST block all SQL modification keywords (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE)
- **FR-029**: Each user MUST only be able to query their own sales data through AI chat (automatic user_id filtering)
- **FR-030**: System MUST use parameterized queries only (no string concatenation) for SQL injection prevention

#### External Dashboard Management
- **FR-031**: Users MUST be able to connect and embed external analytics dashboards (Looker, Tableau, Power BI, Metabase)
- **FR-032**: System MUST support multiple dashboards per user with tab-based interface for switching
- **FR-033**: Users MUST be able to create, view, update, and delete dashboard configurations
- **FR-034**: Users MUST be able to view dashboards in fullscreen mode for presentations
- **FR-035**: Users MUST be able to open dashboards in new browser tabs for multi-monitor workflows
- **FR-036**: Users MUST be able to designate one dashboard as primary, which loads by default
- **FR-037**: Dashboard URLs MUST be validated and sandboxed in iframes for security
- **FR-038**: Dashboard authentication credentials MUST be encrypted before storage

#### Analytics & Reporting
- **FR-039**: System MUST display key performance indicators: total revenue, total units sold, top-selling products for selected period
- **FR-040**: System MUST support analysis of both online (D2C ecommerce) and offline (B2B wholesale) sales channels
- **FR-041**: For online sales, system MUST provide country and city-level performance metrics
- **FR-042**: System MUST track and analyze marketing attribution: UTM source, medium, campaign, device type
- **FR-043**: Users MUST be able to view detailed, paginated reports of individual sales transactions
- **FR-044**: Reports MUST be exportable in PDF (presentations), CSV (analysis), and Excel (manipulation) formats
- **FR-045**: All dashboard widgets and reports MUST be filterable by date range, reseller, product, channel, and geography

#### Error Handling & Notifications
- **FR-046**: When file processing fails, users MUST be able to view detailed error reports with row numbers and error messages
- **FR-047**: Users MUST see aggregate error metrics: total errors, error types, affected rows
- **FR-048**: System MUST send automatic email notifications upon upload success or failure
- **FR-049**: Failure notification emails MUST include direct link to error report
- **FR-050**: Success notification emails MUST include processing statistics: rows processed, total sales, date range, processing time
- **FR-051**: Users MUST be able to configure automated report delivery on daily, weekly, or monthly schedules
- **FR-052**: Users MUST be able to choose report format for scheduled deliveries (PDF, CSV, Excel)
- **FR-053**: System MUST maintain audit log of all emails sent for compliance and troubleshooting

#### Tenant Provisioning & Management
- **FR-054**: Platform admins MUST be able to create new tenants via secure admin API
- **FR-055**: Each tenant MUST have a unique subdomain assigned during provisioning
- **FR-056**: System MUST automatically create a dedicated database for each new tenant
- **FR-057**: Tenant provisioning MUST include: database creation, schema application, default vendor configurations, initial admin user setup
- **FR-058**: Tenants MUST be able to customize vendor processing rules via configuration without code changes
- **FR-059**: System MUST provide baseline vendor configurations that tenants can override
- **FR-060**: Configuration changes MUST take effect immediately without service restart
- **FR-061**: Platform admins MUST be able to suspend and reactivate tenants via is_active flag
- **FR-062**: System MUST maintain secure master registry mapping subdomain → tenant_id → database_url
- **FR-063**: Connection pooling MUST support maximum 10 connections per tenant with health checks
- **FR-064**: System MUST track per-tenant metrics: database size, query performance, upload volume, active user count

### Key Entities

#### Multi-Tenant Infrastructure
- **Tenant**: Represents a customer organization; attributes include tenant_id, subdomain, company_name, database_url (encrypted), database_key (encrypted), is_active status, created_at timestamp, suspended_at timestamp
- **Master Tenant Registry**: Secure mapping of subdomain to tenant_id to database credentials; stored separately from tenant databases

#### User & Authentication
- **User**: Represents an individual within a tenant organization; attributes include user_id, email, password_hash, role (analyst/admin), tenant_id (implicit via database), created_at
- **Session**: Authentication token with tenant_id and subdomain claims for secure tenant routing

#### Data Processing
- **Upload Batch**: Represents a file upload; attributes include batch_id, user_id, filename, status (Pending/Processing/Completed/Failed), upload_date, processing_time, rows_processed, errors_count, vendor_detected
- **Vendor Configuration**: Tenant-specific processing rules; attributes include config_id, tenant_id (implicit), vendor_name, column_mappings, data_type_conversions, value_standardization_rules, currency, default_fields
- **Product**: Canonical product catalog; attributes include product_id, functional_name, product_ean, category
- **Reseller**: Partner organization selling products; attributes include reseller_id, reseller_name, country, contact_info

#### Sales Data (Multi-Channel)
- **Offline Sales (B2B)**: Monthly aggregated wholesale sales; attributes include sale_id, user_id, product_id, reseller_id, upload_batch_id, month, year, quantity, sales_eur, currency (original)
- **Online Sales (D2C)**: Individual ecommerce orders; attributes include order_id, user_id, product_name, product_ean, order_date, quantity, sales_eur, cost_of_goods, stripe_fee, country, city, utm_source, utm_medium, utm_campaign, device_type

#### AI Chat
- **Conversation**: Chat session history; attributes include conversation_id, user_id, session_id, user_message, ai_response, sql_generated (for debugging), timestamp

#### Dashboard Management
- **Dashboard Configuration**: External dashboard settings; attributes include config_id, user_id, dashboard_name, dashboard_type (Looker/Tableau/PowerBI/Metabase), dashboard_url, authentication_method, authentication_config (encrypted), is_primary, is_active

#### Notifications
- **Email Log**: Audit trail of sent emails; attributes include log_id, user_id, email_type (upload_success/upload_failure/scheduled_report), recipient_email, subject, sent_at, status, error_message

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (none - documentation is comprehensive)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
