# 13. Multi-Tenant Architecture

This document describes the TaskifAI multi-tenant SaaS architecture, including tenant isolation strategy, database management, and scalability considerations.

## 13.1. Architecture Overview

### Multi-Tenancy Model

TaskifAI implements a **database-per-tenant** architecture for maximum data isolation and security:

```
┌─────────────────────────────────────────────────────┐
│           customer1.taskifai.com                    │
│                      ↓                              │
│          [Subdomain Detection]                      │
│                      ↓                              │
│          [Tenant ID: "customer1"]                   │
│                      ↓                              │
│     [Database Routing → Supabase Project A]         │
│                      ↓                              │
│        [User Data from Database A Only]             │
└─────────────────────────────────────────────────────┘
```

### Architecture Benefits

- ✅ **Physical Isolation**: Each customer has separate database - impossible to query across tenants
- ✅ **Independent Scaling**: Tenants scale independently based on their data volume
- ✅ **Schema Flexibility**: Each tenant can have custom table structures
- ✅ **Compliance**: Meets strictest data residency and isolation requirements
- ✅ **Cost Transparency**: Clear per-tenant infrastructure costs ($25/month per tenant)

---

## 13.2. Tenant Context Flow

### Request Processing

```
1. User Request → customer1.taskifai.com
2. Extract Subdomain → "customer1"
3. Lookup Tenant Registry → tenant_id="abc-123"
4. Load DB Credentials → {url, key} (encrypted)
5. Create DB Connection → Supabase Client
6. Inject Tenant Context → All queries scoped to tenant DB
7. Return Response → Only tenant's data
```

### Tenant Context Middleware

```python
# Pseudocode for tenant context middleware
async def tenant_context_middleware(request):
    # Extract subdomain from request
    subdomain = extract_subdomain(request.host)

    # Lookup tenant from master registry
    tenant = await get_tenant_by_subdomain(subdomain)

    if not tenant or not tenant.is_active:
        raise HTTP_403_FORBIDDEN

    # Load tenant-specific database connection
    db_config = decrypt_db_credentials(tenant.database_credentials)
    request.state.db = create_supabase_client(db_config)
    request.state.tenant_id = tenant.tenant_id

    # Continue with request
    return await next_middleware(request)
```

---

## 13.3. Database Architecture

### Master Tenant Registry

**Stored in secure platform database:**

```sql
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subdomain VARCHAR(50) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    database_url TEXT NOT NULL,           -- Encrypted
    database_key TEXT NOT NULL,           -- Encrypted
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    suspended_at TIMESTAMP,
    metadata JSONB                        -- Custom tenant config
);

CREATE INDEX idx_tenants_subdomain ON tenants(subdomain);
```

### Tenant-Specific Databases

**Each tenant has own Supabase project:**

```
Tenant 1 → Supabase Project A
├── users
├── products
├── sellout_entries2
├── ecommerce_orders
├── vendor_configs       [Tenant-specific]
├── conversation_history
└── ...

Tenant 2 → Supabase Project B
├── users
├── products
├── sellout_entries2
├── ecommerce_orders
├── vendor_configs       [Different from Tenant 1]
└── ...
```

### Demo Database

```
Demo Tenant → Supabase Project Demo (Free Tier)
├── Same schema as production tenants
├── Used for development and testing
├── tenant_id = "demo"
└── subdomain = "demo"
```

---

## 13.4. Connection Management

### Dynamic Connection Pool

```python
# Connection pool per tenant
class TenantConnectionManager:
    def __init__(self):
        self.connections = {}  # tenant_id → connection pool
        self.max_connections_per_tenant = 10

    async def get_connection(self, tenant_id: str):
        if tenant_id not in self.connections:
            # Load tenant DB config
            tenant = await get_tenant(tenant_id)
            db_config = decrypt_credentials(tenant.db_credentials)

            # Create connection pool
            self.connections[tenant_id] = create_pool(
                db_config,
                max_connections=self.max_connections_per_tenant
            )

        return self.connections[tenant_id]
```

### Connection Caching

- **Cache tenant DB credentials**: 15-minute TTL
- **Connection pooling**: Max 10 connections per tenant
- **Automatic cleanup**: Close idle connections after 5 minutes
- **Health checks**: Validate connection before use

---

## 13.5. Subdomain Routing

### DNS Configuration

```
# Wildcard DNS record
*.taskifai.com → Frontend (Vercel)

# Frontend receives full hostname
customer1.taskifai.com → Extract "customer1" → Pass to backend
```

### Subdomain Extraction

```python
def extract_subdomain(hostname: str) -> str:
    """
    Extract subdomain from hostname

    Examples:
        customer1.taskifai.com → "customer1"
        demo.taskifai.com → "demo"
        taskifai.com → None (main domain)
    """
    parts = hostname.split('.')
    if len(parts) >= 3:
        return parts[0]
    return None
```

### Subdomain Validation

```python
# Security checks
def validate_subdomain(subdomain: str) -> bool:
    # Alphanumeric and hyphens only
    if not re.match(r'^[a-z0-9-]+$', subdomain):
        return False

    # Reserved subdomains
    if subdomain in ['www', 'api', 'admin', 'app', 'staging']:
        return False

    # Length limits
    if len(subdomain) < 3 or len(subdomain) > 50:
        return False

    return True
```

---

## 13.6. Tenant Provisioning Workflow

### Automated Provisioning

```
1. Admin creates tenant via API:
   POST /admin/tenants
   {
     "company_name": "Customer Inc",
     "subdomain": "customerinc",
     "admin_email": "admin@customer.com"
   }

2. System creates:
   a. Unique tenant_id (UUID)
   b. New Supabase project via API
   c. Database credentials (encrypted)
   d. Subdomain DNS record

3. Database initialization:
   a. Run schema.sql on new database
   b. Seed default vendor configurations
   c. Apply RLS policies
   d. Create initial admin user

4. Tenant activation:
   a. Add to tenant registry
   b. Set is_active = true
   c. Send welcome email to admin
   d. Tenant ready to use!
```

### Provisioning Security

- ✅ Admin-only API endpoint (requires platform admin JWT)
- ✅ Multi-factor authentication for provisioning
- ✅ Atomic operations (rollback on failure)
- ✅ Audit logging of all provisioning steps
- ✅ Email verification before activation

---

## 13.7. Tenant Isolation Security

### Security Layers

```
Layer 1: Physical Isolation
    ↓ Each tenant = separate database
Layer 2: Subdomain Validation
    ↓ Prevent subdomain spoofing
Layer 3: Tenant Context
    ↓ All operations scoped to tenant
Layer 4: JWT Claims
    ↓ tenant_id in token payload
Layer 5: RLS Policies
    ↓ User-level isolation within tenant
```

### Cross-Tenant Prevention

**Impossible Scenarios:**
```python
# Even with SQL injection, cannot access other tenant data
# because connection is scoped to tenant's database

# Customer 1 (Database A)
SELECT * FROM sellout_entries2;
# Returns only Customer 1 data from Database A

# Customer 2 (Database B)
SELECT * FROM sellout_entries2;
# Returns only Customer 2 data from Database B

# No way to query Database A from Database B
```

---

## 13.8. Migration from Demo to Production

### Current State (Demo Mode)

```
Single Database (Demo)
├── All users in same database
├── RLS for user isolation
└── tenant_id = "demo" (hardcoded)
```

### Production Multi-Tenant

```
Database-per-Tenant
├── Customer 1 → Database A
├── Customer 2 → Database B
├── Demo → Database Demo
└── Dynamic tenant routing
```

### Migration Path

```
1. Build tenant infrastructure:
   - Tenant registry database
   - Connection management layer
   - Subdomain routing middleware

2. Create demo tenant:
   - Migrate demo data to dedicated DB
   - Add demo to tenant registry
   - subdomain = "demo"

3. Test with demo tenant:
   - Verify subdomain routing
   - Test database connection
   - Validate data isolation

4. Add first customer:
   - Provision new Supabase project
   - Configure subdomain
   - Import customer data
   - Go live!

5. Scale:
   - Add more customers
   - Each gets own database
   - No code changes needed
```

---

## 13.9. Operational Considerations

### Monitoring

**Per-Tenant Metrics:**
- Database size and growth
- Query performance
- Connection pool usage
- Upload volume and frequency
- Active user count

**Platform Metrics:**
- Total tenant count
- System-wide resource usage
- Provisioning success rate
- Cross-tenant query attempts (should be zero)

### Backup Strategy

- Each tenant database backed up independently
- Point-in-time recovery per tenant
- Restore without affecting other tenants
- Backup retention: 30 days

### Cost Management

```
Infrastructure Costs per Tenant:
- Supabase Pro: $25/month
- Storage: ~$0.10/GB/month
- Bandwidth: $0.09/GB

Estimated Total: $25-30/month per tenant
```

### Scaling Limits

- **Current Architecture**: 100-500 tenants
- **With Optimizations**: 1000+ tenants
- **Bottlenecks**: Connection pool limits, DNS routing
- **Solution**: Tenant sharding, dedicated DB cluster per region

---

## 13.10. Best Practices

### ✅ DO

- Always extract tenant_id from subdomain
- Validate subdomain before tenant lookup
- Encrypt database credentials at rest
- Cache tenant configs with TTL
- Log all tenant operations for audit
- Test tenant isolation thoroughly
- Monitor per-tenant resource usage

### ❌ DON'T

- Hardcode tenant_id or database URLs
- Share database connections across tenants
- Store unencrypted credentials
- Allow cross-tenant queries
- Skip subdomain validation
- Forget to scope operations to tenant
- Mix tenant data in logs

---

## 13.11. Summary

TaskifAI's database-per-tenant architecture provides:

✅ **Maximum Security**: Physical data isolation
✅ **Scalability**: Independent tenant scaling
✅ **Flexibility**: Custom schemas per tenant
✅ **Compliance**: Meets strictest requirements
✅ **Simplicity**: Easy to provision and manage

The architecture is built for **secure multi-tenancy from day one** while maintaining operational simplicity and cost efficiency.
