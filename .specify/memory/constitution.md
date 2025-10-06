<!--
Sync Impact Report:
Version: 1.0.0 (Initial Ratification)
Date: 2025-10-06

This is the first ratification of the TaskifAI constitution.

Principles Defined:
1. Multi-Tenant Security Architecture
2. Configuration-Driven Flexibility
3. Defense-in-Depth Security
4. Scalable SaaS Operations

Additional Sections:
- Technology Stack Constraints
- Development Workflow & Quality Gates
- Governance & Compliance

Templates Requiring Updates:
✅ .specify/templates/plan-template.md - Constitution Check section updated
✅ .specify/templates/spec-template.md - Verified alignment
✅ .specify/templates/tasks-template.md - Tenant-aware testing categories added

Follow-up Actions: None (all sections completed)
-->

# TaskifAI Multi-Tenant SaaS Platform Constitution

## Core Principles

### I. Multi-Tenant Security Architecture

**Principle**: The system MUST implement database-per-tenant isolation with subdomain-based routing, ensuring complete physical data separation between customers while maintaining secure, tenant-scoped operations through middleware validation and JWT-based authentication with tenant claims.

**Requirements**:
- Each customer (tenant) MUST have a dedicated Supabase database instance - no shared databases between tenants
- Subdomain routing MUST extract tenant context from hostname (e.g., customer1.taskifai.com → tenant_id)
- All database connections MUST be dynamically routed based on authenticated tenant context
- JWT tokens MUST include `tenant_id` and `subdomain` claims for validation
- Cross-tenant queries MUST be physically impossible due to database isolation
- Tenant registry MUST be stored in secure master database with encrypted credentials
- Middleware MUST validate subdomain→tenant_id mapping before processing requests
- Connection pooling MUST be isolated per tenant (no connection sharing)

**Rationale**: Physical database separation provides the highest level of data isolation, meeting strictest compliance requirements while preventing any possibility of cross-tenant data access even in the event of SQL injection or application bugs.

### II. Configuration-Driven Flexibility

**Principle**: The platform MUST use a configuration-driven vendor processing engine allowing tenant-specific data transformation rules without code changes, enabling customizable data cleaning pipelines while maintaining a single shared codebase that serves all customers.

**Requirements**:
- Vendor configurations MUST be stored in tenant-specific databases (vendor_configs table)
- Each tenant MUST be able to override default vendor processing rules via configuration
- Configuration schema MUST support: column mapping, data type conversion, value standardization, calculated fields
- System MUST provide baseline vendor configurations that tenants inherit and customize
- Vendor detection MUST be automatic based on file structure and content patterns
- No code deployments MUST be required for tenant-specific vendor customization
- Configuration changes MUST take effect immediately without service restart
- Shared codebase MUST serve all tenants through dynamic configuration loading

**Rationale**: Configuration-driven processing enables per-tenant customization while maintaining operational simplicity through a single codebase, reducing deployment complexity and enabling rapid tenant-specific adaptations.

### III. Defense-in-Depth Security

**Principle**: Security MUST be implemented through multiple layers including physical database isolation (Layer 0), subdomain validation (Layer 1-2), JWT authentication (Layer 3), tenant-specific database routing (Layer 4), RLS policies for user-level isolation (Layer 5), comprehensive input validation to prevent injection attacks (Layer 6), and audit logging (Layer 7).

**Security Layers** (all MUST be enforced):
- **Layer 0 - Physical Isolation**: Database-per-tenant architecture (impossible cross-tenant queries)
- **Layer 1 - Network Security**: HTTPS/TLS enforcement, subdomain DNS validation
- **Layer 2 - Tenant Context**: Subdomain→TenantID mapping validation and verification
- **Layer 3 - Authentication**: JWT tokens with tenant_id claims, bcrypt password hashing
- **Layer 4 - Authorization**: Tenant-specific database routing, role-based access control
- **Layer 5 - User Isolation**: Row Level Security (RLS) policies on all tenant databases
- **Layer 6 - Input Validation**: SQL injection prevention, file upload validation, parameterized queries
- **Layer 7 - Audit Logging**: Per-tenant security event tracking and compliance logs

**AI Chat Security** (MUST enforce):
- Block all SQL modification keywords (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE)
- Read-only database user for AI-generated queries
- Automatic user_id filter injection into all queries
- Parameterized queries only (no string concatenation)
- Conversation isolation per user via session_id

**Rationale**: Multi-layered security ensures that a breach at one layer cannot compromise the entire system, with physical database isolation as the ultimate safeguard against data leakage.

### IV. Scalable SaaS Operations

**Principle**: The architecture MUST prioritize operational efficiency through automated tenant provisioning, independent tenant scaling with connection pooling, comprehensive audit logging per tenant, and clear separation between platform administration (tenant management) and tenant-specific configurations (vendor rules, user access).

**Requirements**:
- Tenant provisioning MUST be fully automated via secure admin API
- Each tenant MUST scale independently based on their data volume and usage
- Connection pooling MUST support max 10 connections per tenant with health checks
- Tenant database credentials MUST be encrypted at rest (AES-256)
- Tenant suspension MUST be immediate via is_active flag toggle
- Platform admins MUST have separate authentication from tenant users
- Tenant-specific audit logs MUST be stored in tenant databases (not shared)
- Monitoring MUST track per-tenant metrics: database size, query performance, upload volume
- Backup strategy MUST support independent tenant restore without affecting others
- Cost tracking MUST be transparent per tenant (infrastructure + storage + bandwidth)

**Operational Boundaries**:
- Platform Admin Scope: Tenant provisioning, suspension, platform-wide monitoring, master registry
- Tenant Admin Scope: User management, vendor configurations, data access within their database
- Clear separation enforced via distinct API endpoints and authentication

**Rationale**: Operational clarity through role separation and automated provisioning enables the platform to scale to hundreds of tenants while maintaining security, cost transparency, and administrative efficiency.

## Technology Stack Constraints

### Mandatory Technologies
- **Backend Framework**: FastAPI (Python 3.11+) for async API with type safety
- **Frontend Framework**: React 19 + TypeScript + Vite 6 for modern, type-safe UI
- **Database**: Supabase PostgreSQL 17 with Row Level Security
- **Authentication**: JWT tokens with Supabase Auth or custom implementation
- **AI Engine**: OpenAI GPT-4 + LangChain for natural language query processing
- **Background Processing**: Celery + Redis for asynchronous task execution
- **Email Service**: SendGrid or equivalent SMTP provider
- **Multi-Tenancy**: Database-per-tenant via Supabase projects

### Technology Rationale
- FastAPI: Type safety, async support, automatic API documentation
- React 19: Modern concurrent features, optimal performance
- Supabase: PostgreSQL 17 + RLS + real-time + automatic API generation
- Database-per-tenant: Maximum isolation and compliance vs shared schema approaches

### Prohibited Patterns
- ❌ Shared database with tenant_id column (insufficient isolation)
- ❌ Client-side tenant validation only (security vulnerability)
- ❌ Hardcoded tenant configurations in codebase (defeats flexibility)
- ❌ Cross-tenant database queries (architectural violation)
- ❌ Unencrypted storage of tenant database credentials

## Development Workflow & Quality Gates

### Test-Driven Development (NON-NEGOTIABLE)
- All features MUST follow TDD: Write tests → User approval → Tests fail → Implement
- Contract tests MUST be written for all API endpoints before implementation
- Integration tests MUST validate multi-tenant isolation
- Tenant isolation MUST be tested: verify Customer A cannot access Customer B data
- AI chat queries MUST be tested for SQL injection prevention

### Security Gates (MUST PASS)
- [ ] Subdomain validation prevents spoofing and injection
- [ ] JWT tokens include and validate tenant_id claims
- [ ] Database connections are tenant-scoped (no cross-tenant access possible)
- [ ] RLS policies are enabled on all tenant database tables
- [ ] AI-generated SQL queries are validated against blocked patterns
- [ ] File uploads are validated for type, size, and malware
- [ ] Dashboard URLs are validated and sandboxed in iframes

### Multi-Tenant Testing Requirements
- Test tenant provisioning end-to-end (API → database creation → user setup)
- Test subdomain routing with multiple mock tenants
- Test tenant suspension and reactivation flows
- Test connection pool isolation under load
- Test vendor configuration inheritance and override
- Verify audit logs are written to correct tenant database

### Code Review Checklist
- No hardcoded tenant_id or database URLs
- All database operations use tenant context from middleware
- Vendor configurations loaded from tenant database, not hardcoded
- Security layers enforced (especially Layer 0-4)
- Error messages do not leak tenant information
- Performance tested with multi-tenant load

## Governance & Compliance

### Amendment Procedure
- Constitution amendments require:
  1. Documented proposal with rationale and impact analysis
  2. Review by technical leadership
  3. Migration plan for existing code if backward incompatible
  4. Version bump following semantic versioning (MAJOR.MINOR.PATCH)
  5. Update to all dependent templates and documentation

### Versioning Policy
- **MAJOR**: Backward incompatible principle removals or architectural changes
- **MINOR**: New principles added or existing principles materially expanded
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Compliance Requirements
- All pull requests MUST verify constitutional compliance
- Architecture decisions that deviate from principles MUST be justified and documented
- Security principles (I, III) are NON-NEGOTIABLE - no exceptions allowed
- Flexibility principles (II) may have temporary workarounds with migration plan
- Operational principles (IV) should be optimized but may be temporarily relaxed for MVP

### Constitutional Review
- Quarterly review of principle adherence across codebase
- Annual review of principles for relevance and effectiveness
- Post-incident review if security breach or data leak occurs
- Complexity deviations tracked in feature plan.md files

### Enforcement
- Automated checks in CI/CD pipeline where possible:
  - Database connection tenant scoping validation
  - JWT token claim verification
  - SQL injection pattern detection
  - Cross-tenant query attempt monitoring (should always be zero)
- Manual review gates for:
  - Tenant provisioning code changes
  - Security layer modifications
  - Vendor configuration schema changes

**Version**: 1.0.0 | **Ratified**: 2025-10-06 | **Last Amended**: 2025-10-06
