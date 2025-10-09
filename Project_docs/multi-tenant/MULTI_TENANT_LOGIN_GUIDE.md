# Multi-Tenant Login Implementation Guide (Flow B)

## Overview

You now have a **centralized login portal** at `app.taskifai.com` that:
1. Accepts email + password
2. Authenticates user
3. Discovers associated tenants
4. Redirects to tenant dashboard (single tenant) or shows tenant selector (multi-tenant)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  app.taskifai.com (LoginPortal)                          │
│  ┌────────────────────────────────────────┐             │
│  │ Email: admin@demo.com                  │             │
│  │ Password: ********                     │             │
│  │ [Sign In]                              │             │
│  └────────────────────────────────────────┘             │
│       │                                                  │
│       │ POST /api/auth/login-and-discover               │
│       ├─→ 1. Authenticate (users table)                 │
│       ├─→ 2. Query user_tenants                         │
│       │                                                  │
│       ├─→ Single tenant: {token, redirect_url}          │
│       │   → demo.taskifai.com/dashboard                 │
│       │                                                  │
│       └─→ Multi tenant: {temp_token, tenants[]}         │
│           → Show TenantSelector → dashboard             │
└─────────────────────────────────────────────────────────┘
```

## Database Schema

### New Tables

**user_tenants** - Links users to tenants
```sql
CREATE TABLE user_tenants (
    user_tenant_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    tenant_id UUID,  -- References tenants in tenant registry
    role VARCHAR(50) CHECK (role IN ('member', 'admin', 'super_admin')),
    UNIQUE(user_id, tenant_id)
);
```

**tenant_audit_log** - Tracks user-tenant changes
```sql
CREATE TABLE tenant_audit_log (
    audit_id UUID PRIMARY KEY,
    user_tenant_id UUID REFERENCES user_tenants(user_tenant_id),
    action VARCHAR(50),
    performed_by UUID,
    old_role VARCHAR(50),
    new_role VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

## Deployment Steps

### Phase 1: Database Setup ✅

1. **Execute migrations in Supabase SQL Editor:**

   ```bash
   # Step 1: Create user_tenants table
   # Copy contents of: backend/db/migrations/add_user_tenants.sql
   # Paste in Supabase SQL Editor → Run
   ```

2. **Get your tenant_id from tenant registry:**
   ```sql
   SELECT tenant_id, subdomain FROM tenants WHERE subdomain = 'demo';
   ```

3. **Update seed data with actual tenant_id:**
   ```bash
   # Open: backend/db/migrations/seed_user_tenants.sql
   # Replace '00000000-0000-0000-0000-000000000000' with actual tenant_id
   # Run in Supabase SQL Editor
   ```

### Phase 2: Backend Configuration ✅

4. **Ensure environment variables are set:**
   ```bash
   # backend/.env
   TENANT_REGISTRY_URL=https://your-tenant-registry.supabase.co
   TENANT_REGISTRY_ANON_KEY=your_anon_key
   SECRET_KEY=your_secret_key_min_32_chars
   ```

5. **Start backend server:**
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify backend is running:**
   ```bash
   curl http://localhost:8000/api/health
   # Should return: {"status": "healthy"}
   ```

### Phase 3: Frontend Configuration ✅

7. **Ensure API URL is configured:**
   ```bash
   # frontend/.env
   VITE_API_URL=http://localhost:8000
   ```

8. **Start frontend dev server:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### Phase 4: Testing the Flow

9. **Test centralized login:**

   **Option A: Browser Testing**
   - Open: `http://localhost:5173/portal` (or your frontend URL)
   - Enter credentials:
     - Email: `admin@demo.com`
     - Password: `password` (or whatever you set in users table)
   - Click "Sign In"

   **Expected Results:**
   - ✅ Single tenant user: Auto-redirect to `demo.taskifai.com/dashboard`
   - ✅ Multi-tenant user: Show tenant selector with list of organizations

   **Option B: API Testing (cURL)**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login-and-discover \
     -H "Content-Type: application/json" \
     -d '{
       "email": "admin@demo.com",
       "password": "password"
     }'
   ```

   **Expected Response (Single Tenant):**
   ```json
   {
     "type": "single",
     "subdomain": "demo",
     "company_name": "Demo Company",
     "redirect_url": "https://demo.taskifai.com/dashboard",
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }
   ```

   **Expected Response (Multi-Tenant):**
   ```json
   {
     "type": "multi",
     "tenants": [
       {
         "subdomain": "demo",
         "company_name": "Demo Company"
       },
       {
         "subdomain": "acme",
         "company_name": "Acme Corp"
       }
     ],
     "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }
   ```

## Troubleshooting

### Error: `ERR_CONNECTION_REFUSED`

**Cause:** Backend server not running
**Fix:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Error: `401 Unauthorized - Invalid email or password`

**Causes:**
1. User doesn't exist in `users` table
2. Password is incorrect
3. Email case mismatch (emails are lowercased)

**Fix:**
```sql
-- Check if user exists
SELECT user_id, email, full_name FROM users WHERE email = 'admin@demo.com';

-- Reset password (optional)
UPDATE users
SET hashed_password = '$2b$12$...'  -- Use proper bcrypt hash
WHERE email = 'admin@demo.com';
```

### Error: `404 - No tenant found for user`

**Cause:** User not linked to any tenant in `user_tenants` table

**Fix:**
```sql
-- Check user_tenants mapping
SELECT ut.*, u.email, t.subdomain
FROM user_tenants ut
JOIN users u ON ut.user_id = u.user_id
LEFT JOIN tenants t ON ut.tenant_id = t.tenant_id
WHERE u.email = 'admin@demo.com';

-- If empty, add mapping
INSERT INTO user_tenants (user_id, tenant_id, role)
SELECT u.user_id, 'YOUR_TENANT_ID', 'admin'
FROM users u WHERE u.email = 'admin@demo.com';
```

### Error: Tenant registry connection issues

**Cause:** `TENANT_REGISTRY_URL` or `TENANT_REGISTRY_ANON_KEY` not set

**Fix:**
```bash
# backend/.env
TENANT_REGISTRY_URL=https://your-registry.supabase.co
TENANT_REGISTRY_ANON_KEY=your_anon_key
```

## Security Considerations

### Rate Limiting
- Login endpoint: 10 requests/minute per IP
- Prevents brute force attacks
- Returns `429 Too Many Requests` when exceeded

### Token Security
- **Access Token**: Long-lived (configurable), stores tenant context
- **Temp Token**: 5-minute expiration, for tenant selection only
- Both use JWT with HMAC-SHA256 signing

### Input Validation
- Email: Validated format, lowercase normalization
- Password: Required, passed to bcrypt verification
- Subdomain: Regex validation, prevents injection attacks

### RLS Policies
- `user_tenants` table has RLS enabled
- Users can only read their own tenant memberships
- Admins can manage tenant memberships within their tenants

## Production Deployment

### Environment Variables

**Backend**
```bash
SECRET_KEY=your_production_secret_key_min_32_chars
TENANT_REGISTRY_URL=https://prod-registry.supabase.co
TENANT_REGISTRY_ANON_KEY=prod_anon_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
```

**Frontend**
```bash
VITE_API_URL=https://api.taskifai.com
VITE_ENVIRONMENT=production
```

### DNS Configuration

**Required DNS Records:**
```
app.taskifai.com      → Frontend (Login Portal)
demo.taskifai.com     → Frontend (Tenant-specific)
acme.taskifai.com     → Frontend (Tenant-specific)
api.taskifai.com      → Backend API
```

### CORS Configuration

Update `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.taskifai\.com",  # All subdomains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps (Optional Enhancements)

### 1. Token Exchange Endpoint
For multi-tenant users, implement token exchange:
```python
@router.post("/exchange-token")
async def exchange_temp_token(temp_token: str, subdomain: str):
    # Verify temp token
    # Generate new token with tenant context
    # Return access token
```

### 2. Password Reset Flow
Add password reset for central login:
```python
@router.post("/forgot-password")
@router.post("/reset-password")
```

### 3. OAuth Integration
Add social login (Google, GitHub, Microsoft):
```python
@router.get("/oauth/{provider}")
@router.get("/oauth/{provider}/callback")
```

### 4. Session Management
Track active sessions per tenant:
```sql
CREATE TABLE user_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID,
    tenant_id UUID,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP,
    last_active TIMESTAMP
);
```

## Summary

You've successfully implemented **Flow B** multi-tenant login:

✅ Centralized authentication at `app.taskifai.com`
✅ Combined login + discovery in single request
✅ User-tenant mapping with role-based permissions
✅ Single tenant: Direct redirect to dashboard
✅ Multi-tenant: Tenant selector with temp tokens
✅ Rate limiting and security validation
✅ Audit logging for tenant changes

**Test it now:**
```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev

# Browser
# Open: http://localhost:5173/portal
# Login with: admin@demo.com / password
```

## Support

If you encounter issues:
1. Check backend logs: `uvicorn` output in terminal
2. Check frontend console: Browser DevTools → Console
3. Verify database: Supabase Dashboard → Table Editor
4. Check network requests: Browser DevTools → Network tab

**Key Files Modified:**
- `backend/app/api/auth.py` - New login-and-discover endpoint
- `backend/app/services/tenant_auth_discovery.py` - Auth + discovery service
- `backend/app/models/tenant.py` - New request/response models
- `backend/app/core/security.py` - Updated token creation
- `backend/app/middleware/tenant_context.py` - Skip central endpoints
- `frontend/src/pages/LoginPortal.tsx` - Password field + new flow
- `frontend/src/api/loginAndDiscover.ts` - New API client
- `frontend/src/components/auth/TenantSelector.tsx` - Dashboard redirect

Good luck! 🚀
