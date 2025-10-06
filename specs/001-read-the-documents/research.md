# Research: TaskifAI Multi-Tenant SaaS Platform

**Feature**: 001-read-the-documents
**Date**: 2025-10-06
**Status**: Complete

## Executive Summary

This research document validates technology choices and architectural patterns for TaskifAI, a multi-tenant SaaS platform for sales data analytics. All technical decisions align with constitutional requirements for multi-tenant security, configuration-driven flexibility, defense-in-depth security, and scalable operations.

**Key Findings**:
- Database-per-tenant architecture provides required isolation and compliance
- Subdomain routing enables professional multi-tenant UX
- Configuration-driven vendor processing eliminates code deployments
- Modern tech stack (React 19, FastAPI, PostgreSQL 17) supports all requirements

---

## 1. Multi-Tenant Database Architecture

### Decision
**Database-per-tenant** using Supabase PostgreSQL 17 projects

### Rationale
- **Maximum Isolation**: Physical database separation makes cross-tenant queries impossible
- **Compliance**: Meets strictest data residency and isolation requirements (GDPR, SOC 2)
- **Independent Scaling**: Each tenant database scales based on their usage patterns
- **Schema Flexibility**: Tenants can have custom table structures without affecting others
- **Cost Transparency**: Clear per-tenant infrastructure costs ($25/month Supabase Pro per tenant)

### Alternatives Considered

**Option 1: Shared Database with Row-Level Security (RLS)**
- ❌ Rejected - Insufficient isolation for SaaS platform
- Risk: Single SQL injection or RLS bypass compromises all tenants
- Risk: Schema changes affect all tenants simultaneously
- Risk: One tenant's queries can impact others' performance

**Option 2: Schema-per-tenant in Single Database**
- ❌ Rejected - Better than RLS but still shares resources
- Risk: Connection pool competition between tenants
- Risk: Database-level failures affect all tenants
- Risk: Backup/restore is all-or-nothing

**Option 3: Database-per-tenant** ✅ **CHOSEN**
- ✅ Physical isolation - impossible to query across tenants
- ✅ Independent scaling, backups, and recovery
- ✅ Security: Even with SQL injection, only one tenant affected
- ✅ Operational: Easy to suspend, migrate, or delete individual tenants

### Implementation Details

**Supabase Project per Tenant**:
```
Tenant "customer1" → Supabase Project A
- Database URL: https://xyz-customer1.supabase.co
- Anon Key: tenant-specific anon key
- Service Key: tenant-specific service role key
- Cost: $25/month (Pro tier)

Tenant "customer2" → Supabase Project B
- Database URL: https://abc-customer2.supabase.co
- Anon Key: different anon key
- Service Key: different service role key
- Cost: $25/month (Pro tier)

Demo Tenant → Supabase Project Demo
- Database URL: https://demo.supabase.co
- Cost: $0/month (Free tier for development)
```

**Master Tenant Registry**:
Stored in separate secure database (not tenant-accessible):
```sql
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subdomain VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    database_url TEXT NOT NULL,          -- Encrypted with AES-256
    database_key TEXT NOT NULL,          -- Encrypted with AES-256
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    suspended_at TIMESTAMP,
    metadata JSONB
);
```

**Connection Management**:
- Dynamic connection pooling per tenant
- Max 10 connections per tenant (prevents resource exhaustion)
- 15-minute credential cache TTL (balance security vs. performance)
- Automatic cleanup of idle connections after 5 minutes

---

## 2. Subdomain Routing Strategy

### Decision
**Wildcard DNS (*.taskifai.com)** with middleware-based tenant extraction

### Rationale
- **Professional UX**: Each customer gets branded subdomain (customer1.taskifai.com)
- **Simple Implementation**: Standard DNS configuration, works with any hosting provider
- **Scalability**: No routing table updates needed for new tenants
- **Security**: Tenant context established at request entry point
- **SEO/Marketing**: Tenants can market their custom subdomain

### Alternatives Considered

**Option 1: Path-based routing** (/tenant/customer1/)
- ❌ Rejected - Less professional, confusing URLs
- User sees: https://taskifai.com/tenant/customer1/dashboard
- Problem: Tenant ID exposed in URL, less clean for end users

**Option 2: Query parameter** (?tenant=customer1)
- ❌ Rejected - Insecure (easily manipulated), unprofessional
- User sees: https://taskifai.com/dashboard?tenant=customer1
- Problem: User could change tenant parameter

**Option 3: Subdomain routing** ✅ **CHOSEN**
- ✅ Professional: https://customer1.taskifai.com/dashboard
- ✅ Secure: Subdomain extracted from hostname (can't be manipulated)
- ✅ Branded: Each customer feels like they have their own platform
- ✅ Isolates: Cookies/sessions automatically scoped to subdomain

### Implementation Details

**DNS Configuration**:
```
Wildcard DNS record:
*.taskifai.com → Frontend deployment (Vercel)

Examples:
customer1.taskifai.com → Vercel routes to frontend
customer2.taskifai.com → Vercel routes to frontend
demo.taskifai.com → Vercel routes to frontend
```

**Tenant Extraction Middleware (Backend)**:
```python
async def tenant_context_middleware(request: Request, call_next):
    # Extract subdomain from Host header
    hostname = request.headers.get("host", "")
    subdomain = extract_subdomain(hostname)  # "customer1" from "customer1.taskifai.com"

    # Validate subdomain format
    if not validate_subdomain(subdomain):
        raise HTTPException(status_code=400, detail="Invalid subdomain")

    # Lookup tenant from master registry
    tenant = await get_tenant_by_subdomain(subdomain)

    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant not found or suspended")

    # Load tenant database credentials (decrypt)
    db_config = decrypt_credentials(tenant.database_credentials)

    # Inject tenant context into request state
    request.state.tenant_id = tenant.tenant_id
    request.state.db = create_tenant_connection(db_config)

    # Process request
    response = await call_next(request)
    return response
```

**Security Validations**:
- Subdomain must match pattern: `^[a-z0-9-]{3,50}$` (lowercase alphanumeric + hyphens)
- Reserved subdomains blocked: www, api, admin, app, staging, test
- Subdomain→tenant_id mapping verified against master registry
- Tenant active status checked on every request

---

## 3. Connection Pool Management

### Decision
**Per-tenant connection pools** with 10 max connections and 15-minute credential cache

### Rationale
- **Isolation**: Each tenant's connections are separate (no cross-tenant pollution)
- **Resource Protection**: Prevents any single tenant from exhausting database connections
- **Performance**: Connection pooling reduces overhead of creating new connections
- **Security**: Credentials cached briefly to avoid constant decryption, short TTL limits exposure

### Alternatives Considered

**Option 1: Single global connection pool**
- ❌ Rejected - No tenant isolation
- Problem: All tenants share same pool, one busy tenant affects others
- Problem: Can't limit connections per tenant

**Option 2: Unlimited connections per tenant**
- ❌ Rejected - Resource exhaustion risk
- Problem: Tenant with runaway queries could exhaust database connections
- Problem: Cost increases with connection count

**Option 3: Per-tenant pools with limits** ✅ **CHOSEN**
- ✅ Isolated: Each tenant has dedicated pool
- ✅ Protected: Max 10 connections per tenant prevents exhaustion
- ✅ Efficient: Reuses connections within pool
- ✅ Secure: Credentials cached with short TTL (15 minutes)

### Implementation Details

**TenantConnectionManager Class**:
```python
class TenantConnectionManager:
    def __init__(self):
        self.pools = {}  # tenant_id → asyncpg connection pool
        self.credentials_cache = {}  # tenant_id → (credentials, expire_time)
        self.max_connections_per_tenant = 10
        self.credential_cache_ttl = 900  # 15 minutes

    async def get_connection(self, tenant_id: str):
        # Check if pool exists
        if tenant_id not in self.pools:
            # Load credentials (with caching)
            credentials = await self.get_cached_credentials(tenant_id)

            # Create connection pool
            self.pools[tenant_id] = await asyncpg.create_pool(
                host=credentials['host'],
                port=credentials['port'],
                user=credentials['user'],
                password=credentials['password'],
                database=credentials['database'],
                min_size=1,
                max_size=self.max_connections_per_tenant,
                max_inactive_connection_lifetime=300  # 5 minutes
            )

        return self.pools[tenant_id]

    async def get_cached_credentials(self, tenant_id: str):
        # Check cache
        if tenant_id in self.credentials_cache:
            creds, expire_time = self.credentials_cache[tenant_id]
            if time.time() < expire_time:
                return creds

        # Cache miss - load from registry and decrypt
        tenant = await get_tenant(tenant_id)
        credentials = decrypt_credentials(tenant.database_credentials)

        # Store in cache with TTL
        self.credentials_cache[tenant_id] = (credentials, time.time() + self.credential_cache_ttl)

        return credentials
```

**Health Checks**:
- Connection validity checked before use
- Stale connections automatically closed after 5 minutes idle
- Pool recreated if health check fails

---

## 4. Vendor Configuration Storage

### Decision
**JSONB column** in `vendor_configs` table per tenant database

### Rationale
- **Flexibility**: JSON schema allows arbitrary configuration without schema migrations
- **Tenant-Specific**: Each tenant database has own vendor_configs table
- **No Code Deployments**: Configuration changes don't require code changes or deployments
- **Validation**: JSONB supports schema validation via CHECK constraints or application layer
- **Queryable**: PostgreSQL JSONB supports indexing and queries

### Alternatives Considered

**Option 1: Hardcoded vendor processors**
- ❌ Rejected - Violates Configuration-Driven Flexibility principle
- Problem: Every tenant customization requires code change and deployment
- Problem: Can't support tenant-specific vendor formats

**Option 2: External configuration service** (e.g., Consul, etcd)
- ❌ Rejected - Adds infrastructure complexity
- Problem: Another service to manage and secure
- Problem: Doesn't benefit from tenant database isolation

**Option 3: JSONB in tenant database** ✅ **CHOSEN**
- ✅ Flexible: Arbitrary JSON structure for vendor-specific rules
- ✅ Isolated: Each tenant's configs in their own database
- ✅ No Deployments: Update via SQL or admin UI, no code changes
- ✅ Inheritance: Support default configs with tenant overrides

### Implementation Details

**vendor_configs Table Schema**:
```sql
CREATE TABLE vendor_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_name VARCHAR(100) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Column mapping: source_column → target_field
    column_mappings JSONB NOT NULL DEFAULT '{}',

    -- Data type conversions: field → conversion_rule
    data_type_conversions JSONB NOT NULL DEFAULT '{}',

    -- Value standardization: field → standardization_rules
    value_standardization JSONB NOT NULL DEFAULT '{}',

    -- Default currency
    currency VARCHAR(3) DEFAULT 'EUR',

    -- Default/calculated fields
    default_fields JSONB NOT NULL DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Example Configuration (Galilu Vendor)**:
```json
{
  "vendor_name": "galilu",
  "column_mappings": {
    "Product": "functional_name",
    "EAN": "product_ean",
    "Quantity": "quantity",
    "Sales Value": "sales_pln"
  },
  "data_type_conversions": {
    "quantity": {
      "type": "integer",
      "null_handling": "skip_row"
    },
    "sales_pln": {
      "type": "decimal",
      "precision": 2,
      "currency_conversion": {
        "from": "PLN",
        "to": "EUR",
        "rate_source": "api"
      }
    }
  },
  "value_standardization": {
    "product_ean": {
      "null_values": ["NULL", "N/A", ""],
      "null_action": "allow"
    }
  },
  "currency": "PLN",
  "default_fields": {
    "reseller": "Galilu Poland"
  }
}
```

**Configuration Inheritance**:
1. System provides default vendor configs (seeded during tenant provisioning)
2. Tenant can override specific fields without modifying entire config
3. Tenant can add custom vendor configs for their unique resellers

---

## 5. AI Chat Memory Strategy

### Decision
**LangGraph checkpointer** with database persistence (conversation_history table)

### Rationale
- **Conversation Context**: Maintains chat history for follow-up questions
- **Durable**: Database storage survives server restarts
- **Modern Pattern**: LangGraph is 2025 best practice for stateful AI agents
- **Session Tracking**: thread_id enables per-user conversation isolation
- **Debugging**: Stores generated SQL for troubleshooting and auditing

### Alternatives Considered

**Option 1: Stateless (no memory)**
- ❌ Rejected - Poor user experience
- Problem: Every question treated independently
- Problem: Can't ask follow-up questions like "Show me more details"

**Option 2: Redis-only memory**
- ❌ Rejected - Not durable
- Problem: Conversation lost on Redis restart or eviction
- Problem: Can't query historical conversations

**Option 3: LangGraph + Database** ✅ **CHOSEN**
- ✅ Contextual: Remembers conversation across questions
- ✅ Durable: Database persistence survives restarts
- ✅ Auditable: Full conversation history with SQL queries
- ✅ Isolated: Each user's conversations stored in their tenant database

### Implementation Details

**conversation_history Table**:
```sql
CREATE TABLE conversation_history (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    session_id VARCHAR(100) NOT NULL,  -- thread_id for LangGraph
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    sql_generated TEXT,  -- For debugging and auditing
    timestamp TIMESTAMP DEFAULT NOW(),

    INDEX idx_session (session_id),
    INDEX idx_user (user_id)
);
```

**LangGraph Agent with Memory**:
```python
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Initialize model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Create memory checkpointer (database-backed)
memory = MemorySaver()

# Create agent with tools and memory
agent = create_react_agent(
    model,
    tools=[sql_query_tool],
    checkpointer=memory
)

# Invoke with session tracking
result = agent.invoke(
    {"messages": [("user", "What were my top 5 products last month?")]},
    config={"configurable": {"thread_id": f"user_{user_id}"}}
)

# Save to conversation_history table
await save_conversation(
    user_id=user_id,
    session_id=f"user_{user_id}",
    user_message="What were my top 5 products last month?",
    ai_response=result['messages'][-1].content,
    sql_generated=extract_sql_from_tool_calls(result)
)
```

**Memory Retention**:
- Short-term: Last 10 messages in memory for immediate context
- Long-term: Full conversation history in database
- User can clear conversation via DELETE /api/chat/history

---

## 6. File Upload Flow

### Decision
**Direct upload to backend** → temp storage → **async Celery processing**

### Rationale
- **Simplicity**: Single upload path, easy to secure and validate
- **Async**: Celery prevents UI blocking, handles long-running file processing
- **Reliability**: Celery has built-in retry logic and monitoring
- **Tenant-Aware**: Processing task includes tenant_id for database routing
- **Large Files**: Supports up to 100MB files without frontend timeout

### Alternatives Considered

**Option 1: Direct upload to S3/cloud storage**
- ❌ Rejected - Adds complexity for MVP
- Problem: Requires pre-signed URLs, S3 credentials management
- Problem: Still need backend processing step, just delayed

**Option 2: Synchronous processing in API**
- ❌ Rejected - Blocks UI
- Problem: 500-5000 row files take 1-2 minutes to process
- Problem: HTTP request timeout issues

**Option 3: Backend upload + Celery** ✅ **CHOSEN**
- ✅ Simple: One upload endpoint
- ✅ Async: UI remains responsive, user gets immediate feedback
- ✅ Reliable: Celery handles retries if processing fails
- ✅ Scalable: Celery workers can scale independently

### Implementation Details

**Upload Flow**:
```
1. User uploads file via frontend (react-dropzone)
   ↓
2. POST /api/uploads (multipart/form-data)
   - Validate file type (CSV, XLSX)
   - Validate file size (<100MB)
   - Save to temporary location
   - Create upload_batch record (status: Pending)
   - Queue Celery task
   - Return batch_id to user
   ↓
3. Frontend polls GET /api/uploads/{batch_id} for status
   ↓
4. Celery worker (background):
   - Load tenant database credentials
   - Read file from temp location
   - Detect vendor format (auto-detection)
   - Load vendor config from tenant database
   - Apply transformations (column mapping, type conversion, standardization)
   - Validate and clean data
   - Insert into tenant database (sellout_entries2 or ecommerce_orders)
   - Update upload_batch (status: Completed or Failed)
   - Delete temp file
   - Send email notification
   ↓
5. Frontend receives status update
   - If Completed: Show success message with stats
   - If Failed: Show error message with link to error report
```

**Celery Task**:
```python
@celery_app.task(bind=True, max_retries=3)
def process_upload_file(self, batch_id: str, tenant_id: str):
    try:
        # Load tenant database connection
        db = get_tenant_connection(tenant_id)

        # Load upload batch
        batch = db.query(UploadBatch).filter_by(batch_id=batch_id).first()
        batch.status = "Processing"
        db.commit()

        # Process file (vendor detection + transformation)
        result = process_file(batch.file_path, tenant_id)

        # Update batch
        batch.status = "Completed"
        batch.rows_processed = result.rows_processed
        batch.errors_count = result.errors_count
        batch.processing_time = result.processing_time
        db.commit()

        # Send success email
        send_upload_success_email(batch.user_id, batch_id)

    except Exception as e:
        batch.status = "Failed"
        batch.error_message = str(e)
        db.commit()

        # Send failure email
        send_upload_failure_email(batch.user_id, batch_id)

        # Retry if not max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)  # Retry after 1 minute
```

---

## 7. Dashboard Embedding Security

### Decision
**iframe with sandbox attributes** + URL validation + credential encryption

### Rationale
- **Security**: Sandbox prevents malicious dashboards from accessing parent page or cookies
- **Validation**: Whitelist trusted dashboard domains (Looker, Tableau, Power BI, Metabase)
- **Encryption**: Dashboard authentication credentials encrypted at rest
- **User Control**: Users configure their own dashboards, platform validates

### Alternatives Considered

**Option 1: No sandboxing (unrestricted iframe)**
- ❌ Rejected - Security risk
- Problem: Malicious dashboard could access parent page DOM
- Problem: Could steal user tokens or hijack session

**Option 2: Proxy dashboards through backend**
- ❌ Rejected - Complexity and performance cost
- Problem: Backend becomes bottleneck for dashboard content
- Problem: Doesn't work well with dashboard authentication

**Option 3: Sandboxed iframe + validation** ✅ **CHOSEN**
- ✅ Secure: Sandbox restricts what iframe can do
- ✅ Simple: Browser-native security mechanism
- ✅ Compatible: Works with all major dashboard tools
- ✅ Performant: Direct loading from dashboard provider

### Implementation Details

**Iframe Sandboxing**:
```tsx
<iframe
  src={dashboard.dashboard_url}
  sandbox="allow-scripts allow-same-origin allow-forms"
  title={dashboard.dashboard_name}
  className="w-full h-full border-0"
  allow="fullscreen"
/>
```

**Sandbox Attributes Explained**:
- `allow-scripts`: JavaScript for dashboard interactivity (required)
- `allow-same-origin`: Access to same-origin resources (required for auth)
- `allow-forms`: Form submission within dashboard (required for filters)
- **NOT allowed**: `allow-top-navigation` (prevents hijacking parent), `allow-popups`, `allow-modals`

**URL Validation** (Optional - can be strict or permissive):
```python
ALLOWED_DASHBOARD_DOMAINS = [
    'lookerstudio.google.com',
    'public.tableau.com',
    'app.powerbi.com',
    'metabase.company.com',
]

def validate_dashboard_url(url: str, strict: bool = False):
    parsed = urlparse(url)

    # MUST be HTTPS
    if parsed.scheme != 'https':
        raise ValidationError("Dashboard URL must use HTTPS")

    # Check domain whitelist (optional)
    if strict and parsed.netloc not in ALLOWED_DASHBOARD_DOMAINS:
        raise ValidationError(f"Domain {parsed.netloc} not in whitelist")

    # Block localhost in production
    if 'localhost' in parsed.netloc or '127.0.0.1' in parsed.netloc:
        raise ValidationError("Localhost URLs not allowed")

    return True
```

**Credential Encryption**:
```python
from cryptography.fernet import Fernet

# Encryption key stored in environment
DASHBOARD_ENCRYPTION_KEY = os.getenv("DASHBOARD_ENCRYPTION_KEY")
cipher = Fernet(DASHBOARD_ENCRYPTION_KEY)

# Encrypt before storing
def encrypt_dashboard_auth(auth_config: dict) -> str:
    json_data = json.dumps(auth_config)
    encrypted = cipher.encrypt(json_data.encode())
    return encrypted.decode()

# Decrypt when needed
def decrypt_dashboard_auth(encrypted_config: str) -> dict:
    decrypted = cipher.decrypt(encrypted_config.encode())
    return json.loads(decrypted.decode())
```

---

## 8. Tenant Provisioning Automation

### Decision
**Admin API** → Supabase Management API → Schema migration → Seed configs

### Rationale
- **Fully Automated**: No manual steps, consistent setup
- **Auditable**: All provisioning logged in master registry
- **Atomic**: Either complete success or complete rollback
- **Scalable**: Can provision hundreds of tenants programmatically
- **Secure**: Admin-only endpoint with MFA requirement

### Alternatives Considered

**Option 1: Manual setup**
- ❌ Rejected - Doesn't scale beyond a few tenants
- Problem: Time-consuming, error-prone
- Problem: Inconsistent configurations

**Option 2: Terraform/IaC (future enhancement)**
- ⚠️ Not for MVP - Adds complexity
- Future: Terraform for infrastructure-as-code
- Current: Direct API calls simpler for MVP

**Option 3: Automated API provisioning** ✅ **CHOSEN**
- ✅ Fast: Provision tenant in minutes
- ✅ Consistent: Same setup for every tenant
- ✅ Auditable: All steps logged
- ✅ Secure: Admin authentication + audit trail

### Implementation Details

**Provisioning Flow**:
```
1. Platform Admin: POST /api/admin/tenants
   {
     "company_name": "Customer Inc",
     "subdomain": "customerinc",
     "admin_email": "admin@customer.com"
   }
   ↓
2. Validate Request:
   - Check admin authentication (MFA required)
   - Validate subdomain availability and format
   - Verify company_name not duplicate
   ↓
3. Create Supabase Project:
   - Call Supabase Management API
   - Create new PostgreSQL 17 project
   - Store database_url and anon_key (encrypted)
   ↓
4. Initialize Database:
   - Connect to new database
   - Run Alembic migrations (schema.sql)
   - Create tables with RLS policies
   - Enable PostgreSQL extensions
   ↓
5. Seed Default Configurations:
   - Insert default vendor_configs (9 vendors)
   - Create initial admin user
   - Set up email templates
   ↓
6. Register Tenant:
   - Add to master tenant registry
   - Set is_active = true
   - Generate audit log entry
   ↓
7. Send Welcome Email:
   - Email to admin_email with login credentials
   - Include subdomain URL (customerinc.taskifai.com)
   ↓
8. Return Response:
   {
     "tenant_id": "uuid-123",
     "subdomain": "customerinc",
     "database_url": "https://xyz.supabase.co",
     "status": "active"
   }
```

**Rollback on Failure**:
- If any step fails, rollback all previous steps
- Delete Supabase project if created
- Remove tenant from registry
- Log failure for investigation

**Supabase Management API Usage**:
```python
import httpx

async def create_supabase_project(company_name: str, subdomain: str):
    response = await httpx.post(
        "https://api.supabase.com/v1/projects",
        headers={
            "Authorization": f"Bearer {SUPABASE_MANAGEMENT_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "name": f"{company_name} - TaskifAI",
            "organization_id": SUPABASE_ORG_ID,
            "plan": "pro",  # $25/month
            "region": "us-east-1",
            "db_pass": generate_secure_password()
        }
    )

    if response.status_code != 201:
        raise ProvisioningError("Failed to create Supabase project")

    project_data = response.json()
    return {
        "database_url": project_data["database"]["host"],
        "anon_key": project_data["anon_key"],
        "service_key": project_data["service_role_key"]
    }
```

---

## 9. Technology Stack Validation

All technology choices validated against:
- Constitutional requirements (FastAPI, React 19, Supabase PostgreSQL 17)
- Feature requirements (64 functional requirements across 7 epics)
- Performance goals (<200ms API, <5s AI chat, 1-2min file processing)
- Scale targets (100-500 tenants, 10-100 users per tenant)

### Frontend Stack ✅ VALIDATED

**React 19** (latest 2025):
- ✅ Concurrent rendering for responsive UI
- ✅ Removed forwardRef requirement (cleaner code)
- ✅ Enhanced hooks (use hook for promises/context)
- ✅ Strong TypeScript 5.7+ support
- ✅ Rich ecosystem for file upload, chat UI, iframe embedding

**Vite 6+**:
- ✅ Lightning-fast HMR (Hot Module Replacement)
- ✅ Modern ES modules with Rollup 4
- ✅ Built-in TypeScript support
- ✅ Requires Node.js 20.19+ (current version)

**Tailwind CSS v4** + **shadcn/ui**:
- ✅ New @theme directive for CSS variables
- ✅ OKLCH colors for better accuracy
- ✅ shadcn/ui React 19 compatible (no forwardRef)
- ✅ Copy-paste components (not npm dependency)

**TanStack Query v5** + **Zustand**:
- ✅ TanStack Query for server state (API calls)
- ✅ Zustand for UI state (modals, sidebar)
- ✅ Both fully compatible with React 19

### Backend Stack ✅ VALIDATED

**FastAPI 0.115+** (Python 3.11+):
- ✅ Async/await for file processing and AI chat
- ✅ Automatic OpenAPI documentation
- ✅ Excellent Pydantic v2 integration for validation
- ✅ Native LangChain compatibility
- ✅ WebSocket support for real-time features

**Pydantic v2**:
- ✅ Data validation with improved performance
- ✅ Settings management (pydantic-settings)
- ✅ Type safety throughout application

**Authentication** (python-jose + passlib):
- ✅ JWT token generation/validation with tenant claims
- ✅ bcrypt password hashing (12 rounds)
- ✅ Secure session management (24-hour tokens)

### AI Stack ✅ VALIDATED

**LangChain 0.3+** + **LangGraph 0.2+**:
- ✅ Modern agent patterns with state management
- ✅ Built-in SQL agent for data querying
- ✅ Database checkpointer for conversation memory
- ✅ React integration guides available

**OpenAI GPT-4o**:
- ✅ Best natural language understanding
- ✅ Accurate SQL generation
- ✅ gpt-4o-mini for cost optimization on simple queries

### Database Stack ✅ VALIDATED

**Supabase PostgreSQL 17**:
- ✅ PostgreSQL 17 currently supported (PostgreSQL 18 coming soon)
- ✅ Built-in Row Level Security (RLS)
- ✅ Real-time subscriptions
- ✅ Python client library (supabase-py 2.10+)
- ✅ Vector database support (future AI features)

**PostgreSQL 18 Features** (when available):
- Asynchronous I/O (3x performance gains)
- uuidv7() for timestamp-ordered UUIDs
- Virtual generated columns
- OAuth authentication support

### Worker Stack ✅ VALIDATED

**Celery** + **Redis**:
- ✅ Python-native task queue
- ✅ Reliable async processing
- ✅ Built-in retry logic
- ✅ Scheduled tasks support
- ✅ Monitoring with Flower

**File Processing** (pandas + openpyxl):
- ✅ Excel and CSV reading
- ✅ Data transformation and validation
- ✅ Type conversion and cleaning

### Email Stack ✅ VALIDATED

**SendGrid**:
- ✅ Reliable delivery (99.99% uptime)
- ✅ Free tier (100 emails/day)
- ✅ Template management
- ✅ Analytics and tracking

**Report Generation**:
- ✅ ReportLab for PDFs
- ✅ pandas for CSV/Excel export

---

## 10. Risk Assessment

### High Priority Risks

**Risk 1: Multi-Tenant Complexity**
- **Impact**: High - Architecture foundation
- **Probability**: Medium
- **Mitigation**: Extensive testing of tenant isolation, subdomain routing, connection management
- **Contingency**: Start with demo tenant, add multi-tenancy after MVP validation

**Risk 2: Vendor Format Diversity**
- **Impact**: Medium - Core feature
- **Probability**: High - Each vendor has unique format
- **Mitigation**: Configuration-driven processing, start with 3 vendors for MVP
- **Contingency**: Manual import tool as fallback

**Risk 3: AI Chat SQL Injection**
- **Impact**: Critical - Security violation
- **Probability**: Low - Multiple security layers
- **Mitigation**: SQL keyword blocking, read-only user, parameterized queries, query validation
- **Contingency**: Disable AI chat if vulnerability found, fix before re-enabling

### Medium Priority Risks

**Risk 4: Connection Pool Exhaustion**
- **Impact**: Medium - Performance degradation
- **Probability**: Low - 10 connections per tenant limit
- **Mitigation**: Connection pool monitoring, automatic cleanup, health checks
- **Contingency**: Increase limit per tenant, add connection queueing

**Risk 5: Supabase Pricing**
- **Impact**: Medium - Operating costs
- **Probability**: Medium - $25/tenant/month adds up
- **Mitigation**: Pass costs to customers in pricing, offer tiered plans
- **Contingency**: Migrate to self-hosted PostgreSQL if costs unsustainable

### Low Priority Risks

**Risk 6: Dashboard Embedding Compatibility**
- **Impact**: Low - Feature-specific
- **Probability**: Low - Standard iframe approach
- **Mitigation**: Test with major dashboard providers, document requirements
- **Contingency**: Direct link to dashboard if embedding fails

---

## Conclusion

All technical decisions validated and aligned with:
- ✅ Constitutional principles (multi-tenant security, config-driven, defense-in-depth, scalable)
- ✅ Functional requirements (64 requirements across 7 epics)
- ✅ Performance goals (<200ms API, <5s AI, 1-2min processing)
- ✅ Technology constraints (FastAPI, React 19, PostgreSQL 17)

**Recommendation**: Proceed to Phase 1 (Design & Contracts)

**Key Success Factors**:
1. Multi-tenant testing at every layer (critical!)
2. Configuration-driven vendor processing (flexibility)
3. Comprehensive security testing (7-layer defense)
4. Performance monitoring per tenant (scalability)

**Next Steps**:
- Generate data-model.md with entity definitions
- Create OpenAPI contracts for 6 API domains
- Write failing contract tests
- Create integration test scenarios
- Generate quickstart.md for development setup
