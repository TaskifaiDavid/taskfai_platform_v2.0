Multi-Tenant Customer Onboarding Implementation Plan

  🎯 Architecture Decisions (Confirmed)

  1. Database-Per-Tenant: ✅ Each customer = separate Supabase project
  2. Central Login Portal: ✅ Build app.taskifai.com for tenant discovery
  3. User Multi-Tenancy: ✅ ONLY for admin super user (David), regular users = single tenant

  ---
  📊 Current State Analysis

  What Works Now:
  - demo.taskifai.com → Demo tenant (bypasses registry, uses main Supabase)
  - Subdomain routing middleware extracts tenant from hostname
  - JWT tokens include tenant claims (tenant_id, subdomain)
  - Tenant provisioning infrastructure exists but unused
  - Admin API endpoints for tenant CRUD operations

  What's Missing:
  - Tenant registry database not deployed (only schema exists)
  - No user→tenant mapping (can't discover which tenant user belongs to)
  - No central login portal at app.taskifai.com
  - Demo tenant not registered in tenant registry

  ---
  🚀 Implementation Plan - 4 Phases

  Phase 1: Deploy Tenant Registry Database (30 min)

  Goal: Create master database for tenant management

  Steps:
  1. Create new Supabase project: "TaskifAI Tenant Registry"
    - Region: us-east-1
    - Plan: Free tier (low usage)
  2. Apply tenant registry schema:
    - Run backend/db/tenants_schema.sql in Supabase SQL Editor
    - Creates tables: tenants, tenant_configs, tenant_audit_log
    - Creates encryption functions and triggers
  3. Create user_tenants mapping table:
  CREATE TABLE user_tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('member', 'admin', 'super_admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(email, tenant_id)
  );

  CREATE INDEX idx_user_tenants_email ON user_tenants(email);
  CREATE INDEX idx_user_tenants_tenant ON user_tenants(tenant_id);
  4. Update backend .env with registry credentials:
  TENANT_REGISTRY_URL=https://xxx.supabase.co
  TENANT_REGISTRY_ANON_KEY=eyJxxx...
  TENANT_REGISTRY_SERVICE_KEY=eyJxxx...

  Files to Modify:
  - backend/app/core/config.py → Add registry environment variables
  - backend/app/services/tenant/registry.py → Connect to registry database

  ---
  Phase 2: Register Demo Tenant (15 min)

  Goal: Migrate demo tenant into registry

  Steps:
  1. Encrypt demo tenant credentials using backend encryption functions
  2. Insert demo tenant into registry:
  INSERT INTO tenants (
    tenant_id,
    company_name,
    subdomain,
    database_url,
    database_credentials,
    is_active,
    metadata
  ) VALUES (
    'demo-0000-0000-0000-000000000000',
    'TaskifAI Demo',
    'demo',
    encrypt_data('https://afualzsndhnbsuruwese.supabase.co', 'SECRET_KEY'),
    encrypt_data('{"anon_key":"eyJ...", "service_key":"eyJ..."}', 'SECRET_KEY'),
    TRUE,
    '{"type":"demo"}'::jsonb
  );
  3. Register David as super admin:
  INSERT INTO user_tenants (email, tenant_id, role)
  VALUES ('david@taskifai.com', 'demo-0000-0000-0000-000000000000', 'super_admin');
  4. Update TenantContextMiddleware to use registry for demo (remove hardcoded fallback)

  Files to Modify:
  - backend/app/middleware/tenant_context.py → Remove demo hardcoding, always query registry
  - backend/db/seed_demo_tenant.sql → Create seeding script with encrypted values

  ---
  Phase 3: Build Central Login Portal (2-3 hours)

  Goal: app.taskifai.com → tenant discovery → redirect to subdomain

  3.1 Backend: Tenant Discovery Endpoint

  Create /api/auth/discover-tenant endpoint:

  # backend/app/api/auth.py

  @router.post("/discover-tenant")
  async def discover_tenant(email: str):
      """
      Discover which tenant(s) user belongs to
      
      Returns:
      - Single tenant: {subdomain, company_name, redirect_url}
      - Multiple tenants: [{subdomain, company_name}, ...]
      - Not found: 404 error
      """
      # Query tenant registry
      query = """
          SELECT t.subdomain, t.company_name, t.tenant_id, ut.role
          FROM user_tenants ut
          JOIN tenants t ON ut.tenant_id = t.tenant_id
          WHERE ut.email = $1 AND t.is_active = TRUE
          ORDER BY ut.role DESC, t.created_at ASC
      """

      results = await registry_db.fetch(query, email)

      if not results:
          raise HTTPException(404, "No tenant found for this email")

      # Super admin (David) gets all tenants
      # Regular users get only their tenant

      if len(results) == 1:
          tenant = results[0]
          return {
              "subdomain": tenant['subdomain'],
              "company_name": tenant['company_name'],
              "redirect_url": f"https://{tenant['subdomain']}.taskifai.com/login?email={email}"
          }
      else:
          # Multiple tenants (super admin only)
          return {
              "tenants": [
                  {"subdomain": t['subdomain'], "company_name": t['company_name']}
                  for t in results
              ]
          }

  Files to Create/Modify:
  - backend/app/api/auth.py → Add /discover-tenant endpoint
  - backend/app/models/user.py → Add TenantDiscoveryRequest/Response models

  3.2 Frontend: Login Portal Page

  Create frontend/src/pages/LoginPortal.tsx:

  // Step 1: Email input
  // Step 2: Call /auth/discover-tenant
  // Step 3a: Single tenant → Auto redirect to {subdomain}.taskifai.com/login?email={email}
  // Step 3b: Multiple tenants → Show tenant selector → Redirect on selection

  export function LoginPortal() {
    const [email, setEmail] = useState('')
    const [tenants, setTenants] = useState([])
    const [loading, setLoading] = useState(false)

    const handleEmailSubmit = async () => {
      const response = await api.post('/auth/discover-tenant', { email })

      if (response.redirect_url) {
        // Single tenant - auto redirect
        window.location.href = response.redirect_url
      } else {
        // Multiple tenants - show selector
        setTenants(response.tenants)
      }
    }

    const handleTenantSelect = (subdomain: string) => {
      window.location.href = `https://${subdomain}.taskifai.com/login?email=${email}`
    }

    return (
      <div>
        <input value={email} onChange={(e) => setEmail(e.target.value)} />
        <button onClick={handleEmailSubmit}>Continue</button>

        {tenants.length > 0 && (
          <div>
            <h3>Select your organization:</h3>
            {tenants.map(t => (
              <button onClick={() => handleTenantSelect(t.subdomain)}>
                {t.company_name}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  }

  Files to Create:
  - frontend/src/pages/LoginPortal.tsx → Central login page
  - frontend/src/api/tenant.ts → Tenant discovery API calls
  - frontend/src/components/auth/TenantSelector.tsx → Tenant selection UI component

  3.3 Frontend: Routing Setup

  Update App routing to handle central portal:

  // frontend/src/App.tsx

  function App() {
    const hostname = window.location.hostname
    const isAppPortal = hostname === 'app.taskifai.com' || hostname === 'localhost:5173'

    if (isAppPortal) {
      return (
        <Routes>
          <Route path="/" element={<LoginPortal />} />
          <Route path="/login" element={<LoginPortal />} />
        </Routes>
      )
    }

    // Existing subdomain routing
    return <MainApp />
  }

  Files to Modify:
  - frontend/src/App.tsx → Add routing logic for app.taskifai.com
  - frontend/src/main.tsx → Ensure routing works for all subdomains

  3.4 Enhanced Login Page for Pre-filled Email

  Modify existing login to accept email query parameter:

  // frontend/src/pages/Login.tsx

  export function Login() {
    const [searchParams] = useSearchParams()
    const prefillEmail = searchParams.get('email')

    return <LoginForm initialEmail={prefillEmail} />
  }

  Files to Modify:
  - frontend/src/pages/Login.tsx → Accept email query param
  - frontend/src/components/auth/LoginForm.tsx → Pre-fill email input

  ---
  Phase 4: Provision First Customer (30 min)

  Goal: Onboard customer1.taskifai.com

  4.1 Create Customer Supabase Project

  Option A: Manual (Recommended for first customer)
  1. Go to Supabase dashboard → New Project
  2. Name: "Customer1 TaskifAI"
  3. Region: us-east-1 (or customer preference)
  4. Database password: Generate secure password
  5. Wait for provisioning (~2 minutes)

  Option B: Automated (Using provisioner API)
  POST /admin/tenants
  {
    "subdomain": "customer1",
    "company_name": "Customer Company Inc",
    "admin_email": "admin@customer1.com",
    "region": "us-east-1"
  }
  # Auto-provisions Supabase project via Management API

  4.2 Apply Schema & Seed Data

  1. Copy backend/db/schema.sql → Supabase SQL Editor → Execute
  2. Copy backend/db/seed_vendor_configs.sql → Execute
  3. Verify tables created correctly

  4.3 Register Tenant in Registry

  -- In tenant registry database
  INSERT INTO tenants (
    company_name,
    subdomain,
    database_url,
    database_credentials,
    is_active
  ) VALUES (
    'Customer Company Inc',
    'customer1',
    encrypt_data('https://customer1-project.supabase.co', 'SECRET_KEY'),
    encrypt_data('{"anon_key":"eyJ...", "service_key":"eyJ..."}', 'SECRET_KEY'),
    TRUE
  );

  -- Get tenant_id from above insert
  -- Register customer admin user
  INSERT INTO user_tenants (email, tenant_id, role)
  VALUES ('admin@customer1.com', '<tenant_id>', 'admin');

  4.4 DNS Configuration

  Option A: Wildcard (Recommended)
  Type: CNAME
  Name: *.taskifai.com
  Value: your-server-domain.com
  TTL: 300

  Option B: Specific Subdomain
  Type: CNAME
  Name: customer1.taskifai.com
  Value: your-server-domain.com

  4.5 Test Customer Login Flow

  1. Go to app.taskifai.com
  2. Enter email: admin@customer1.com
  3. Should redirect to customer1.taskifai.com/login?email=admin@customer1.com
  4. Complete login with password
  5. Should see customer1's dashboard

  Files to Create:
  - backend/db/seed_customer1.sql → Customer-specific setup script

  ---
  🔧 Technical Implementation Details

  Database Architecture

  Master Tenant Registry (Single Supabase project):
  - tenants (company_name, subdomain, encrypted_credentials)
  - user_tenants (email, tenant_id, role)
  - tenant_configs (settings per tenant)
  - tenant_audit_log (change tracking)

  Per-Tenant Database (Separate Supabase project per customer):
  - users (tenant-specific users with hashed passwords)
  - products, resellers, ecommerce_orders, sellout_entries2
  - All existing tables from schema.sql

  Authentication Flow

  Central Portal Login (app.taskifai.com):
  1. User enters email
  2. Backend queries user_tenants table in registry
  3. Returns matching tenant(s)
  4. Redirect to {subdomain}.taskifai.com/login?email={email}

  Subdomain Login (customer1.taskifai.com):
  1. Middleware extracts subdomain → queries tenant registry → loads tenant context
  2. User completes login with password
  3. Backend validates against tenant's Supabase database
  4. JWT token includes tenant claims
  5. All API requests scoped to tenant

  Super Admin Access (David)

  David's email registered in multiple tenants:
  -- Demo tenant
  INSERT INTO user_tenants VALUES ('david@taskifai.com', 'demo-tenant-id', 'super_admin');

  -- Customer1 tenant  
  INSERT INTO user_tenants VALUES ('david@taskifai.com', 'customer1-tenant-id', 'super_admin');

  -- Customer2 tenant
  INSERT INTO user_tenants VALUES ('david@taskifai.com', 'customer2-tenant-id', 'super_admin');

  When David logs in at app.taskifai.com:
  - Shows tenant selector with all accessible tenants
  - Can switch between customers via portal

  ---
  📋 File Creation Checklist

  Backend (8 files)

  - backend/app/core/config.py - Add tenant registry config
  - backend/app/services/tenant/discovery.py - Tenant lookup logic
  - backend/app/api/auth.py - Add /discover-tenant endpoint
  - backend/app/models/tenant.py - Add discovery models
  - backend/db/user_tenants.sql - User-tenant mapping schema
  - backend/db/seed_demo_tenant.sql - Demo tenant registration
  - backend/db/seed_customer1.sql - First customer setup
  - backend/app/middleware/tenant_context.py - Remove demo hardcoding

  Frontend (6 files)

  - frontend/src/pages/LoginPortal.tsx - Central login page
  - frontend/src/components/auth/TenantSelector.tsx - Tenant picker UI
  - frontend/src/api/tenant.ts - Tenant API client
  - frontend/src/App.tsx - Portal routing logic
  - frontend/src/pages/Login.tsx - Accept email param
  - frontend/src/components/auth/LoginForm.tsx - Pre-fill email

  ---
  🎯 Success Criteria

  Phase 1: ✅ Tenant registry database deployed and accessible
  Phase 2: ✅ Demo tenant registered, David can access demo.taskifai.com
  Phase 3: ✅ app.taskifai.com portal works, redirects to correct subdomain
  Phase 4: ✅ customer1.taskifai.com fully functional, admin@customer1.com can login

  ---
  ⏱️ Time Estimates

  - Phase 1: Deploy Tenant Registry - 30 minutes
  - Phase 2: Register Demo Tenant - 15 minutes
  - Phase 3: Build Central Portal - 2-3 hours
  - Phase 4: Provision First Customer - 30 minutes

  Total: 3.5-4.5 hours for complete implementation

  ---
  🚨 Critical Considerations

  1. Encryption Keys: Use same SECRET_KEY for encrypting tenant credentials
  2. DNS Propagation: Wildcard DNS may take 5-60 minutes to propagate
  3. CORS Configuration: Update backend to allow app.taskifai.com origin
  4. Session Management: Cookies won't work across subdomains (use redirect flow)
  5. Cost: Each customer = $25/month Supabase Pro plan (or Free tier for testing)