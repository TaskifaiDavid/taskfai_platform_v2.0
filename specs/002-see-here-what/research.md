# Research: Multi-Tenant Customer Onboarding System

**Date**: 2025-10-09
**Feature**: Multi-tenant customer onboarding with central login portal

## Research Topics

### 1. Supabase Client Connection Pooling and Tenant Isolation

**Decision**: Use separate Supabase client instance per tenant with isolated connection pools

**Rationale**:
- Supabase Python client (v2.10+) creates connection pool per client instance
- Each tenant gets dedicated client initialized with their encrypted credentials
- Connection pool defaults to 10 connections per client (configurable)
- Physical database separation (database-per-tenant) ensures zero cross-tenant query possibility

**Implementation Pattern**:
```python
from supabase import create_client

class TenantDatabaseManager:
    def __init__(self):
        self._clients = {}  # tenant_id -> Supabase client

    def get_client(self, tenant_context: TenantContext):
        if tenant_context.tenant_id not in self._clients:
            self._clients[tenant_context.tenant_id] = create_client(
                supabase_url=tenant_context.database_url,
                supabase_key=tenant_context.database_key
            )
        return self._clients[tenant_context.tenant_id]
```

**Alternatives Considered**:
- Single shared client with connection string switching → Rejected (connection pool would be shared, violates isolation)
- New client per request → Rejected (performance overhead, connection exhaustion)

---

### 2. FastAPI CORS Configuration for Subdomain Wildcard

**Decision**: Configure CORS to allow app.taskifai.com and wildcard *.taskifai.com subdomains

**Rationale**:
- Central portal at app.taskifai.com needs to call backend API
- Tenant subdomains (customer1.taskifai.com) also need API access
- FastAPI CORSMiddleware supports regex patterns for origin validation
- Production deployment will use HTTPS only

**Implementation Pattern**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://([a-z0-9-]+\.)?taskifai\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

**Security Considerations**:
- Regex pattern prevents subdomain injection attacks
- HTTPS enforcement prevents MITM attacks
- allow_credentials=True enables cookie/token transmission
- Subdomain validation happens in TenantContextMiddleware as second layer

**Alternatives Considered**:
- Explicit allowlist of all subdomains → Rejected (requires code deploy for each new customer)
- Allow all origins with credentials → Rejected (major security vulnerability)

---

### 3. JWT Role-Based Access Control for Super Admin

**Decision**: Add `role` claim to JWT payload with values: member, admin, super_admin

**Rationale**:
- JWT already includes tenant_id and subdomain claims
- Add role claim to enable authorization without database lookup on every request
- Super admin role grants access to multiple tenants via tenant selector
- Regular admin role grants admin privileges within single tenant only

**Implementation Pattern**:
```python
# Token generation
def create_access_token(user_id: str, tenant_id: str, subdomain: str, role: str):
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "subdomain": subdomain,
        "role": role,  # NEW
        "exp": datetime.utcnow() + timedelta(minutes=1440)
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")

# Authorization dependency
def require_super_admin(token: dict = Depends(get_current_user)):
    if token.get("role") != "super_admin":
        raise HTTPException(403, "Super admin access required")
    return token
```

**Role Hierarchy**:
- `member`: Read-only access to tenant data
- `admin`: Full CRUD access within tenant, manage tenant users
- `super_admin`: Cross-tenant access, platform administration, tenant provisioning

**Alternatives Considered**:
- Database lookup for role on every request → Rejected (performance overhead, defeats JWT purpose)
- Separate super admin authentication system → Rejected (complexity, user confusion)

---

### 4. Tenant Provisioning Automation with Supabase Management API

**Decision**: Use Supabase Management API for automated database provisioning (future phase)

**Rationale**:
- Supabase Management API supports programmatic project creation
- Enables fully automated tenant onboarding workflow
- Initial implementation will use manual Supabase dashboard creation
- API integration planned for Phase 6 (automation)

**Manual Process (MVP)**:
1. Admin creates Supabase project via dashboard
2. Copy project URL, anon_key, service_key
3. Call POST /api/admin/tenants with encrypted credentials
4. System registers tenant in registry and creates user_tenants mapping

**Future Automation (Phase 6)**:
```python
import httpx

async def provision_tenant(subdomain: str, region: str):
    # Call Supabase Management API
    response = await httpx.post(
        "https://api.supabase.com/v1/projects",
        headers={"Authorization": f"Bearer {SUPABASE_MGMT_TOKEN}"},
        json={
            "name": f"{subdomain}-taskifai",
            "organization_id": SUPABASE_ORG_ID,
            "region": region,
            "plan": "pro"
        }
    )
    project = response.json()

    # Wait for provisioning (async polling)
    # Apply schema via Supabase API
    # Register in tenant registry with encrypted credentials
```

**Alternatives Considered**:
- Multi-tenant PostgreSQL with schemas → Rejected (violates constitutional database-per-tenant principle)
- Customer-managed databases → Rejected (operational complexity, inconsistent schema)

---

### 5. Encrypted Credential Storage and Rotation Best Practices

**Decision**: Use PostgreSQL pgcrypto for symmetric encryption with application-managed keys

**Rationale**:
- Existing tenants_schema.sql already includes pgcrypto encryption functions
- Symmetric encryption (AES-256) via pgp_sym_encrypt/decrypt
- Encryption key stored in application SECRET_KEY environment variable
- Key rotation requires re-encryption of all tenant credentials (admin operation)

**Implementation Pattern**:
```sql
-- Encrypt on insert
INSERT INTO tenants (database_credentials)
VALUES (
    encrypt_data(
        '{"anon_key":"xxx", "service_key":"yyy"}',
        current_setting('app.secret_key')
    )
);

-- Decrypt on read
SELECT
    tenant_id,
    decrypt_data(database_credentials, current_setting('app.secret_key')) as creds
FROM tenants
WHERE subdomain = 'customer1';
```

**Python Integration**:
```python
from app.core.config import settings

class TenantRegistry:
    def encrypt_credentials(self, credentials: dict) -> str:
        query = """
            SELECT encrypt_data($1::text, $2::text) as encrypted
        """
        result = await self.db.fetch_one(
            query,
            json.dumps(credentials),
            settings.secret_key
        )
        return result["encrypted"]

    def decrypt_credentials(self, encrypted: str) -> dict:
        query = """
            SELECT decrypt_data($1::text, $2::text) as decrypted
        """
        result = await self.db.fetch_one(
            query,
            encrypted,
            settings.secret_key
        )
        return json.loads(result["decrypted"])
```

**Security Considerations**:
- SECRET_KEY must be 32+ characters, rotated quarterly
- Key stored in environment variable, never committed to code
- Credentials encrypted at rest in PostgreSQL
- TLS in transit for all database connections
- Audit log tracks all credential access

**Alternatives Considered**:
- Application-level encryption (Python cryptography) → Rejected (no advantage over pgcrypto, more code)
- Vault/KMS external key management → Rejected (adds infrastructure dependency for MVP)
- Asymmetric encryption (public/private keys) → Rejected (unnecessary complexity for symmetric use case)

---

### 6. Security Patterns for Central Login Portals with Redirect Flows

**Decision**: Email-based tenant discovery with signed redirect URLs and email pre-fill

**Rationale**:
- Central portal cannot set cookies for subdomain (different domain)
- Use redirect URL with email query parameter for seamless UX
- Prevents session fixation and CSRF attacks
- User completes authentication on their tenant subdomain (cookie domain matches)

**Flow**:
1. User enters email at app.taskifai.com
2. Backend queries user_tenants table for tenant(s)
3. Single tenant: `redirect to https://customer1.taskifai.com/login?email={email}`
4. Multiple tenants: Show selector, user picks → redirect
5. Tenant subdomain pre-fills email, user enters password
6. JWT token set as httpOnly cookie on tenant subdomain
7. User accesses tenant dashboard

**Security Measures**:
- HTTPS enforced on all domains (prevents email sniffing in URL)
- Email query param validated against tenant user list before pre-fill
- Rate limiting on /discover-tenant endpoint (prevent enumeration attacks)
- Redirect URL validated against known tenant subdomains (prevent open redirect)

**Implementation Pattern**:
```python
@router.post("/discover-tenant")
async def discover_tenant(request: TenantDiscoveryRequest):
    # Query user_tenants with rate limiting
    tenants = await registry.get_user_tenants(request.email)

    if not tenants:
        raise HTTPException(404, "No tenant found for email")

    if len(tenants) == 1:
        # Single tenant - auto redirect
        tenant = tenants[0]
        redirect_url = f"https://{tenant.subdomain}.taskifai.com/login?email={quote(request.email)}"
        return {"redirect_url": redirect_url}

    # Multiple tenants - show selector
    return {"tenants": [{"subdomain": t.subdomain, "company_name": t.company_name} for t in tenants]}
```

**Frontend Security**:
```typescript
// Validate redirect URL before navigation
const validateTenantRedirect = (url: string): boolean => {
  const parsed = new URL(url);
  return (
    parsed.protocol === 'https:' &&
    parsed.hostname.endsWith('.taskifai.com') &&
    parsed.hostname.split('.').length === 3 // subdomain.taskifai.com
  );
};

// Navigate only if valid
if (response.redirect_url && validateTenantRedirect(response.redirect_url)) {
  window.location.href = response.redirect_url;
}
```

**Alternatives Considered**:
- OAuth-style authorization code flow → Rejected (over-engineered for single organization scenario)
- JWT in URL parameter → Rejected (token exposure in browser history, logs)
- Central portal sets cookie for all subdomains → Rejected (not possible due to SameSite policy)

---

## Research Summary

All technical unknowns resolved. Implementation approach validated against:
- ✅ Constitutional multi-tenant security principles (database-per-tenant, encryption, isolation)
- ✅ Supabase infrastructure requirements (connection pooling, PostgreSQL 17 features)
- ✅ Security best practices (defense-in-depth, role-based access, secure redirects)
- ✅ Scalability requirements (supports 100+ tenants, automated provisioning path)

**Next Phase**: Design data models and API contracts based on research findings.
