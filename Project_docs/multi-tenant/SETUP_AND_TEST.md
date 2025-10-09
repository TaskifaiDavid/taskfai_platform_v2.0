# Multi-Tenant Login - Setup and Testing Guide

## ✅ Database Status

Your Supabase database is **already configured correctly**!

### Existing Tables
- ✅ `tenants` - Tenant registry with demo tenant
- ✅ `user_tenants` - User-tenant mappings (email-based)
- ✅ `users` - User authentication data

### Existing Data
```
User: david@taskifai.com
Tenant: demo (subdomain)
Tenant ID: d69c83d5-c13b-42e2-8376-acdd96b106b9
Role: super_admin
```

## 🚀 Quick Start

### 1. Start Backend Server

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verify Backend is Running:**
```bash
curl http://localhost:8000/api/health
# Expected: {"status": "healthy"} or similar
```

### 2. Test Login-and-Discover API

```bash
curl -X POST http://localhost:8000/api/auth/login-and-discover \
  -H "Content-Type: application/json" \
  -d '{
    "email": "david@taskifai.com",
    "password": "YOUR_PASSWORD_HERE"
  }'
```

**Expected Response (Single Tenant):**
```json
{
  "type": "single",
  "subdomain": "demo",
  "company_name": "TaskifAI Demo Organization",
  "redirect_url": "https://demo.taskifai.com/dashboard",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 3. Start Frontend

```bash
cd frontend
npm run dev
```

**Open in Browser:**
- Go to: `http://localhost:5173/portal`
- Enter: `david@taskifai.com` + your password
- Click "Sign In"
- Should redirect to dashboard

## 🔧 Configuration

### Backend `.env`
```bash
# API Configuration
SECRET_KEY=your_secret_key_min_32_chars

# Tenant Registry (Supabase)
TENANT_REGISTRY_URL=https://afualzsndhnbsuruwese.supabase.co
TENANT_REGISTRY_ANON_KEY=your_anon_key_here
```

### Frontend `.env`
```bash
VITE_API_URL=http://localhost:8000
```

## 🧪 Testing Scenarios

### Test 1: API Authentication

```bash
# Test with correct credentials
curl -X POST http://localhost:8000/api/auth/login-and-discover \
  -H "Content-Type: application/json" \
  -d '{"email": "david@taskifai.com", "password": "correct_password"}'

# Expected: 200 OK with access_token

# Test with wrong password
curl -X POST http://localhost:8000/api/auth/login-and-discover \
  -H "Content-Type: application/json" \
  -d '{"email": "david@taskifai.com", "password": "wrong_password"}'

# Expected: 401 Unauthorized

# Test with non-existent user
curl -X POST http://localhost:8000/api/auth/login-and-discover \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent@example.com", "password": "password"}'

# Expected: 401 Unauthorized
```

### Test 2: Frontend Login Flow

1. **Access Login Portal:**
   - URL: `http://localhost:5173/portal`
   - Should see email + password form

2. **Enter Credentials:**
   - Email: `david@taskifai.com`
   - Password: Your password
   - Click "Sign In"

3. **Expected Behavior:**
   - Single tenant: Auto-redirect to `demo.taskifai.com/dashboard`
   - Loading indicator during authentication
   - Error message if credentials invalid

### Test 3: Multi-Tenant User (Future)

To test multi-tenant selector:

```sql
-- Add user to second tenant in Supabase SQL Editor
INSERT INTO user_tenants (email, tenant_id, role)
VALUES ('david@taskifai.com', 'another-tenant-id', 'admin');
```

Then login should show tenant selector.

## 🛠️ Troubleshooting

### Error: `ERR_CONNECTION_REFUSED`

**Cause:** Backend not running
**Fix:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Error: `401 Unauthorized`

**Cause:** Wrong credentials or user not in database
**Fix:** Check password or create user in Supabase:
```sql
-- Verify user exists
SELECT email, user_id FROM users WHERE email = 'david@taskifai.com';

-- Check user_tenants mapping
SELECT ut.*, t.subdomain
FROM user_tenants ut
JOIN tenants t ON ut.tenant_id = t.tenant_id
WHERE ut.email = 'david@taskifai.com';
```

### Error: `No tenant found for user`

**Cause:** User not linked to any tenant in `user_tenants`
**Fix:**
```sql
INSERT INTO user_tenants (email, tenant_id, role)
SELECT
    'david@taskifai.com',
    'd69c83d5-c13b-42e2-8376-acdd96b106b9',  -- demo tenant ID
    'super_admin'
WHERE NOT EXISTS (
    SELECT 1 FROM user_tenants
    WHERE email = 'david@taskifai.com'
);
```

### CORS Errors

**Cause:** Frontend and backend on different origins
**Fix:** Backend CORS is configured for localhost:5173, should work automatically

## 📊 Database Queries

### Check Current Setup

```sql
-- View all tenants
SELECT tenant_id, subdomain, company_name, is_active FROM tenants;

-- View user-tenant mappings
SELECT
    ut.email,
    ut.role,
    t.subdomain,
    t.company_name
FROM user_tenants ut
JOIN tenants t ON ut.tenant_id = t.tenant_id;

-- View users
SELECT user_id, email, full_name, tenant_id FROM users;
```

### Add New Tenant

```sql
-- Create new tenant
INSERT INTO tenants (company_name, subdomain, database_url, database_credentials)
VALUES (
    'Acme Corp',
    'acme',
    'encrypted_db_url_here',
    'encrypted_credentials_here'
);

-- Link user to new tenant
INSERT INTO user_tenants (email, tenant_id, role)
VALUES ('david@taskifai.com', 'new-tenant-id', 'admin');
```

## 🎯 What Was Fixed

### Original Problem
The migration `add_user_tenants.sql` failed because it tried to create foreign keys to `users(user_id)`, but:
1. Your database already had a `user_tenants` table
2. The existing table uses **email-based lookup** (better design!)
3. No cross-database foreign keys needed

### Solution Applied
Updated `backend/app/services/tenant_auth_discovery.py`:
- Changed `_get_user_tenants(user_id)` → `_get_user_tenants(email)`
- Query now uses `.eq('email', email)` instead of `.eq('user_id', user_id)`
- Works with your existing email-based schema

## 🔐 Security Notes

- **Rate Limiting:** 10 login attempts per minute per IP
- **JWT Tokens:** HS256 signed, configurable expiration
- **Temp Tokens:** 5-minute expiration for tenant selection
- **Password Hashing:** bcrypt with 12 rounds
- **Input Validation:** Email format, subdomain regex

## 📝 Next Steps

1. ✅ Backend service updated (DONE)
2. ✅ Database schema correct (ALREADY DONE)
3. 🔄 Test login API (DO THIS NOW)
4. 🔄 Test frontend flow (AFTER API WORKS)
5. 🎯 Deploy to production (AFTER TESTING)

## 💡 Tips

- Check backend logs: Look at terminal where uvicorn is running
- Check frontend console: Browser DevTools → Console tab
- Check network requests: Browser DevTools → Network tab
- Use verbose curl: Add `-v` flag for detailed output

**Ready to test!** Start with the Quick Start section above.
