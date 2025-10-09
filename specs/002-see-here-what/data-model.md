# Data Model: Multi-Tenant Customer Onboarding System

**Date**: 2025-10-09
**Feature**: Multi-tenant customer onboarding with central login portal

## Entity Relationship Diagram

```
┌─────────────────┐
│     Tenant      │
├─────────────────┤
│ tenant_id (PK)  │───┐
│ company_name    │   │
│ subdomain (UK)  │   │
│ database_url    │   │
│ db_credentials  │   │
│ is_active       │   │
│ metadata        │   │
│ created_at      │   │
│ updated_at      │   │
└─────────────────┘   │
                      │
                      │ 1:N
                      │
┌─────────────────┐   │
│  UserTenant     │◄──┘
├─────────────────┤
│ id (PK)         │
│ email           │
│ tenant_id (FK)  │
│ role            │
│ created_at      │
└─────────────────┘
         │
         │ UK: (email, tenant_id)
         │

┌─────────────────┐
│  TenantConfig   │
├─────────────────┤
│ config_id (PK)  │
│ tenant_id (FK)  │───► tenant_id
│ max_file_size   │
│ allowed_vendors │
│ features        │
│ created_at      │
│ updated_at      │
└─────────────────┘

┌──────────────────┐
│ TenantAuditLog   │
├──────────────────┤
│ log_id (PK)      │
│ tenant_id (FK)   │───► tenant_id
│ action           │
│ performed_by     │
│ details          │
│ created_at       │
└──────────────────┘
```

## Entity Specifications

### Tenant (Master Registry)

**Purpose**: Master registry of all customer organizations in the platform

**Table**: `tenants` (in central tenant registry database)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| tenant_id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique tenant identifier |
| company_name | VARCHAR(255) | NOT NULL | Customer organization name |
| subdomain | VARCHAR(50) | UNIQUE, NOT NULL | Tenant subdomain (e.g., "customer1") |
| database_url | TEXT | NOT NULL | Encrypted Supabase project URL |
| database_credentials | TEXT | NOT NULL | Encrypted JSON with anon_key and service_key |
| is_active | BOOLEAN | DEFAULT TRUE | Tenant active status (for suspension) |
| metadata | JSONB | DEFAULT '{}' | Additional tenant metadata |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Tenant creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |
| suspended_at | TIMESTAMPTZ | NULL | Suspension timestamp (if applicable) |

**Validation Rules**:
- `subdomain` must match regex: `^[a-z0-9-]+$`
- `subdomain` cannot start or end with hyphen
- `database_credentials` must be valid JSON with keys: anon_key, service_key
- Encrypted fields use pgcrypto: `encrypt_data(plaintext, secret_key)`

**State Transitions**:
```
active (is_active=true) ──┐
                          │
                          ├──► suspended (is_active=false, suspended_at=NOW())
                          │
suspended ────────────────┘──► active (is_active=true, suspended_at=NULL)
```

**Business Rules**:
1. Subdomain uniqueness enforced at database level
2. Credentials always encrypted at rest
3. Updates trigger audit log entry
4. Soft delete via is_active flag (preserve audit trail)

---

### UserTenant (User-Tenant Mapping)

**Purpose**: Maps users (by email) to authorized tenants with roles

**Table**: `user_tenants` (in central tenant registry database)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique mapping ID |
| email | VARCHAR(255) | NOT NULL | User email address |
| tenant_id | UUID | NOT NULL, FK → tenants(tenant_id) CASCADE | Tenant reference |
| role | VARCHAR(50) | NOT NULL, DEFAULT 'member' | User role in tenant |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Mapping creation timestamp |

**Constraints**:
- UNIQUE(email, tenant_id) - User can only have one role per tenant
- CHECK(role IN ('member', 'admin', 'super_admin'))
- ON DELETE CASCADE for tenant_id (if tenant deleted, mappings deleted)

**Indexes**:
- `idx_user_tenants_email` on email (tenant discovery queries)
- `idx_user_tenants_tenant` on tenant_id (tenant user listing)

**Role Definitions**:
- `member`: Read-only access to tenant data
- `admin`: Full CRUD access within tenant, manage tenant users
- `super_admin`: Cross-tenant access, platform administration

**Business Rules**:
1. Regular users belong to exactly one tenant
2. Super admins can belong to multiple tenants
3. Super admin role reserved for platform administrators only
4. Email format validated via Pydantic EmailStr
5. Role changes trigger audit log

**Query Patterns**:
```sql
-- Tenant discovery by email
SELECT t.subdomain, t.company_name, t.tenant_id, ut.role
FROM user_tenants ut
JOIN tenants t ON ut.tenant_id = t.tenant_id
WHERE ut.email = 'user@example.com' AND t.is_active = TRUE;

-- List tenant users
SELECT email, role, created_at
FROM user_tenants
WHERE tenant_id = 'uuid-here'
ORDER BY role DESC, created_at ASC;
```

---

### TenantConfig (Per-Tenant Configuration)

**Purpose**: Store tenant-specific configuration and feature flags

**Table**: `tenant_configs` (in central tenant registry database)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| config_id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique config ID |
| tenant_id | UUID | UNIQUE, FK → tenants(tenant_id) CASCADE | One config per tenant |
| max_file_size_mb | INTEGER | DEFAULT 100 | Max upload file size in MB |
| allowed_vendors | TEXT[] | NULL (NULL = all allowed) | Vendor whitelist |
| custom_branding | JSONB | NULL | Custom UI branding config |
| features_enabled | JSONB | DEFAULT (see below) | Feature flags |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Config creation timestamp |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update timestamp |

**Default Features**:
```json
{
  "ai_chat": true,
  "dashboards": true,
  "email_reports": true,
  "api_access": false
}
```

**Business Rules**:
1. One-to-one relationship with Tenant
2. Inherits platform defaults, can override per tenant
3. Changes take effect immediately (no restart required)
4. Updates trigger audit log

---

### TenantAuditLog (Audit Trail)

**Purpose**: Immutable audit trail for tenant operations and changes

**Table**: `tenant_audit_log` (in central tenant registry database)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| log_id | UUID | PRIMARY KEY, DEFAULT uuid_generate_v4() | Unique log entry ID |
| tenant_id | UUID | FK → tenants(tenant_id) SET NULL | Tenant reference (nullable) |
| action | VARCHAR(100) | NOT NULL | Action performed |
| performed_by | VARCHAR(255) | NULL | Admin user who performed action |
| details | JSONB | NULL | Action details and context |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Timestamp of action |

**Indexes**:
- `idx_audit_tenant` on tenant_id (tenant audit history)
- `idx_audit_created` on created_at (chronological queries)

**Action Types**:
- `created` - Tenant created
- `updated` - Tenant modified
- `suspended` - Tenant suspended
- `activated` - Tenant activated
- `deleted` - Tenant deleted
- `credentials_rotated` - Credentials changed
- `user_added` - User-tenant mapping added
- `user_removed` - User-tenant mapping removed
- `role_changed` - User role modified

**Business Rules**:
1. Append-only table (no updates or deletes)
2. Triggered automatically by database triggers
3. Captures old and new state for updates
4. Retention policy: keep all logs indefinitely for compliance

**Trigger Logic**:
```sql
CREATE TRIGGER tenant_changes_audit
    AFTER INSERT OR UPDATE OR DELETE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION log_tenant_changes();
```

---

## Data Flow Diagrams

### Tenant Discovery Flow

```
User → Central Portal
         ↓
      POST /discover-tenant { email }
         ↓
      Query user_tenants table
         ↓
      ┌─────────────────┐
      │ Single tenant?  │
      └─────────────────┘
         ↓            ↓
       YES           NO
         ↓            ↓
    Redirect URL   Tenant List
         ↓            ↓
    Subdomain      User Selects
    Login Page     → Redirect URL
```

### Tenant Provisioning Flow (Manual MVP)

```
Super Admin → POST /admin/tenants
                ↓
             Validate subdomain unique
                ↓
             Manual Supabase project creation
                ↓
             Admin copies credentials
                ↓
             Call API with encrypted creds
                ↓
             ┌─────────────────────┐
             │ Insert into tenants │
             │ with encryption     │
             └─────────────────────┘
                ↓
             Insert user_tenants mapping
                ↓
             Audit log entry
                ↓
             Return tenant_id + success
```

### Authentication Flow with Tenant Context

```
Request → TenantContextMiddleware
            ↓
         Extract subdomain
            ↓
         Query tenants table
            ↓
         Decrypt credentials
            ↓
         Create TenantContext
            ↓
         Inject into request.state.tenant
            ↓
         Route Handler → Uses tenant context
                          ↓
                       Supabase client per tenant
```

---

## Migration Strategy

### Phase 1: Deploy Tenant Registry (Initial)

1. Create new Supabase project for tenant registry
2. Apply `tenants_schema.sql` (tables + triggers + encryption functions)
3. Create `user_tenants` table
4. Seed demo tenant with encrypted credentials
5. Register super admin (David) with demo tenant mapping

### Phase 2: Migrate Demo Tenant

1. Extract demo Supabase credentials from current .env
2. Encrypt credentials using pgcrypto functions
3. Insert demo tenant into registry with encrypted values
4. Create user_tenants mapping for David → demo
5. Update TenantContextMiddleware to use registry (remove hardcoding)

### Phase 3: Add First Customer

1. Manual Supabase project creation for customer1
2. Apply schema.sql + seed_vendor_configs.sql to customer1 database
3. Register customer1 in tenant registry with encrypted credentials
4. Create user_tenants mapping for customer admin
5. Test login flow via central portal

---

## Security Considerations

### Encryption at Rest

**Credentials**:
- Database URL encrypted using pgcrypto `pgp_sym_encrypt`
- Credentials JSON encrypted using same method
- Encryption key: application SECRET_KEY (32+ chars)
- Key rotation: quarterly, requires re-encryption of all tenants

**Access Control**:
- Tenant registry uses RLS policies (only super admins)
- Encrypted fields never exposed in API responses
- Decryption only happens in backend service layer

### Data Isolation

**Physical Separation**:
- Each tenant has dedicated Supabase database
- No shared tables between tenants
- Cross-tenant queries physically impossible

**Logical Separation**:
- User-tenant mappings enforce access boundaries
- JWT tokens include tenant_id claim for validation
- Middleware validates tenant context on every request

### Audit Requirements

**Compliance**:
- All tenant operations logged immutably
- Captures who, what, when for regulatory compliance
- Audit logs retained indefinitely
- No PII in audit logs (only email, action, tenant_id)

---

## Performance Considerations

### Indexing Strategy

**High-frequency queries**:
- `user_tenants.email` - tenant discovery (every login)
- `tenants.subdomain` - tenant resolution (every request)
- `tenants.is_active` - active tenant filtering

**Index Coverage**:
```sql
CREATE INDEX idx_user_tenants_email ON user_tenants(email);
CREATE INDEX idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX idx_tenants_active ON tenants(is_active) WHERE is_active = TRUE;
```

### Connection Pooling

**Per-Tenant Clients**:
- Supabase client cached per tenant_id
- Each client maintains 10 connection pool
- Clients reused across requests for same tenant
- Memory usage: ~5MB per tenant client

**Scaling Limits**:
- 100 tenants = 1000 max connections (10 per tenant)
- PostgreSQL max_connections typically 100-200
- Tenant registry needs dedicated connection pool
- Monitor connection usage, implement eviction policy if needed

---

## Validation Rules Summary

### Tenant Entity
- ✅ Subdomain: lowercase alphanumeric + hyphens only
- ✅ Subdomain: no leading/trailing hyphens
- ✅ Subdomain: unique across all tenants
- ✅ Database credentials: valid encrypted JSON
- ✅ Company name: 1-255 characters

### UserTenant Entity
- ✅ Email: valid email format (Pydantic EmailStr)
- ✅ Role: one of [member, admin, super_admin]
- ✅ Unique: (email, tenant_id) combination
- ✅ Foreign key: tenant_id must exist in tenants

### TenantConfig Entity
- ✅ Max file size: positive integer
- ✅ Allowed vendors: array of valid vendor codes
- ✅ Features: valid JSON with boolean values
- ✅ One config per tenant

### TenantAuditLog Entity
- ✅ Action: valid action type from enum
- ✅ Performed by: email or system identifier
- ✅ Details: valid JSON
- ✅ Immutable: no updates or deletes allowed

---

**Next Step**: Generate API contracts from these data models
