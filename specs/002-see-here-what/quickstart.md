# Quickstart: Multi-Tenant Customer Onboarding

**Feature**: Multi-tenant customer onboarding with central login portal
**Estimated Time**: 15-20 minutes for complete validation

## Prerequisites

- ✅ Tenant registry Supabase database deployed
- ✅ Backend running on localhost:8000
- ✅ Frontend running on localhost:5173
- ✅ Demo tenant registered in registry
- ✅ Environment variables configured

## Test Scenarios

### Scenario 1: Regular User Single-Tenant Login

**Goal**: Verify regular user can discover their tenant and login successfully

**Steps**:

1. **Navigate to central portal**:
   ```bash
   # Open browser
   open http://localhost:5173
   # Should redirect to central login portal
   ```

2. **Enter user email**:
   - Input: `user@customer1.com`
   - Click "Continue"

3. **Verify automatic redirect**:
   - Expected URL: `http://customer1.localhost:5173/login?email=user@customer1.com`
   - Email field should be pre-filled

4. **Complete login**:
   - Enter password
   - Click "Login"

5. **Verify dashboard access**:
   - Should see Customer1 dashboard
   - Check browser dev tools → Application → Cookies
   - Verify JWT token present with `tenant_id=customer1`

**Validation**:
```bash
# Check tenant discovery API
curl -X POST http://localhost:8000/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email":"user@customer1.com"}'

# Expected response:
# {
#   "subdomain": "customer1",
#   "company_name": "Customer Company Inc",
#   "redirect_url": "http://customer1.localhost:5173/login?email=user@customer1.com"
# }
```

**Success Criteria**:
- ✅ Tenant discovery returns single tenant with redirect URL
- ✅ Automatic redirect to subdomain login
- ✅ Email pre-filled in login form
- ✅ Successful authentication
- ✅ JWT token includes correct tenant_id

---

### Scenario 2: Super Admin Multi-Tenant Access

**Goal**: Verify super admin can see tenant selector and access multiple tenants

**Steps**:

1. **Navigate to central portal**:
   ```bash
   open http://localhost:5173
   ```

2. **Enter super admin email**:
   - Input: `david@taskifai.com`
   - Click "Continue"

3. **Verify tenant selector displayed**:
   - Should see list of tenants:
     - TaskifAI Demo (demo)
     - Customer Company Inc (customer1)
     - [Any other registered tenants]

4. **Select demo tenant**:
   - Click on "TaskifAI Demo"
   - Verify redirect to: `http://demo.localhost:5173/login?email=david@taskifai.com`

5. **Complete login for demo**:
   - Enter password
   - Verify access to demo dashboard

6. **Repeat for customer1**:
   - Logout
   - Go to central portal
   - Enter `david@taskifai.com`
   - Select "Customer Company Inc"
   - Login with password
   - Verify access to customer1 dashboard

**Validation**:
```bash
# Check super admin tenant discovery
curl -X POST http://localhost:8000/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email":"david@taskifai.com"}'

# Expected response:
# {
#   "tenants": [
#     {"subdomain": "demo", "company_name": "TaskifAI Demo"},
#     {"subdomain": "customer1", "company_name": "Customer Company Inc"}
#   ]
# }
```

**Success Criteria**:
- ✅ Tenant discovery returns multiple tenants
- ✅ Tenant selector UI displayed
- ✅ Can select and access demo tenant
- ✅ Can select and access customer1 tenant
- ✅ JWT tokens have different tenant_id values

---

### Scenario 3: New Tenant Provisioning (Manual)

**Goal**: Verify complete tenant onboarding flow

**Steps**:

1. **Create Supabase project** (Manual via dashboard):
   - Name: `Customer2 TaskifAI`
   - Region: `us-east-1`
   - Wait for provisioning (~2 min)
   - Copy Project URL: `https://xxx.supabase.co`
   - Copy anon key and service_key from Settings → API

2. **Apply schema to new database**:
   - Open Supabase SQL Editor
   - Paste `backend/db/schema.sql`
   - Execute
   - Paste `backend/db/seed_vendor_configs.sql`
   - Execute

3. **Register tenant via API** (requires super admin JWT):
   ```bash
   # Get super admin token first
   TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"david@taskifai.com","password":"admin123"}' \
     | jq -r '.access_token')

   # Register new tenant
   curl -X POST http://localhost:8000/api/admin/tenants \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "subdomain": "customer2",
       "company_name": "Customer Two Corp",
       "admin_email": "admin@customer2.com",
       "database_url": "https://xxx.supabase.co",
       "database_credentials": {
         "anon_key": "eyJ...",
         "service_key": "eyJ..."
       }
     }'
   ```

4. **Verify tenant registered**:
   ```bash
   # List all tenants
   curl -X GET http://localhost:8000/api/admin/tenants \
     -H "Authorization: Bearer $TOKEN"

   # Should include customer2 in response
   ```

5. **Test customer2 login**:
   - Navigate to: `http://customer2.localhost:5173/login`
   - Enter: `admin@customer2.com` and password
   - Should successfully login to customer2 workspace

**Validation**:
```bash
# Verify tenant in registry
curl -X POST http://localhost:8000/api/auth/discover-tenant \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@customer2.com"}'

# Expected:
# {
#   "subdomain": "customer2",
#   "company_name": "Customer Two Corp",
#   "redirect_url": "..."
# }
```

**Success Criteria**:
- ✅ Supabase project created and schema applied
- ✅ Tenant registered in registry with encrypted credentials
- ✅ User-tenant mapping created for admin
- ✅ Tenant discovery works for new admin email
- ✅ Login succeeds on customer2 subdomain
- ✅ Data isolated from other tenants

---

### Scenario 4: Data Isolation Verification

**Goal**: Verify complete data isolation between tenants

**Steps**:

1. **Login as customer1 user**:
   ```bash
   # Get customer1 token
   TOKEN_C1=$(curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@customer1.com","password":"password123"}' \
     | jq -r '.access_token')
   ```

2. **Upload file to customer1**:
   ```bash
   curl -X POST http://localhost:8000/api/uploads \
     -H "Authorization: Bearer $TOKEN_C1" \
     -F "file=@test_data.xlsx"
   ```

3. **Verify data in customer1 dashboard**:
   - Login to customer1.localhost:5173
   - Navigate to dashboard
   - Should see uploaded data

4. **Login as customer2 user**:
   ```bash
   # Get customer2 token
   TOKEN_C2=$(curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@customer2.com","password":"password123"}' \
     | jq -r '.access_token')
   ```

5. **Verify customer2 dashboard empty**:
   - Login to customer2.localhost:5173
   - Navigate to dashboard
   - Should show NO data (empty state)

6. **Attempt cross-tenant data access** (should fail):
   ```bash
   # Try to access customer1 data with customer2 token
   curl -X GET http://localhost:8000/api/analytics/overview \
     -H "Authorization: Bearer $TOKEN_C2" \
     -H "X-Tenant-Subdomain: customer1"

   # Expected: Still returns customer2 data (JWT tenant_id enforced)
   ```

**Validation**:
```bash
# Inspect JWT tokens
echo $TOKEN_C1 | jwt decode -
# Should show: "tenant_id": "customer1-uuid"

echo $TOKEN_C2 | jwt decode -
# Should show: "tenant_id": "customer2-uuid"
```

**Success Criteria**:
- ✅ Customer1 data visible only in customer1 workspace
- ✅ Customer2 workspace shows empty state (no data)
- ✅ JWT tenant_id enforced regardless of subdomain header
- ✅ No cross-tenant data leakage possible

---

### Scenario 5: Security Audit Trail

**Goal**: Verify audit logging captures tenant operations

**Steps**:

1. **Check audit logs in tenant registry**:
   ```bash
   # Connect to tenant registry database
   # Execute query:
   SELECT
     action,
     performed_by,
     details->>'subdomain' as subdomain,
     created_at
   FROM tenant_audit_log
   ORDER BY created_at DESC
   LIMIT 10;
   ```

2. **Verify logged actions**:
   - Should see:
     - `created` - customer2 tenant creation
     - `user_added` - admin@customer2.com mapping
     - `updated` - any tenant modifications

3. **Test suspension audit**:
   ```bash
   # Suspend customer2 (super admin only)
   curl -X PATCH http://localhost:8000/api/admin/tenants/customer2-uuid \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"is_active": false}'

   # Verify audit entry created
   SELECT * FROM tenant_audit_log
   WHERE action = 'suspended'
   AND tenant_id = 'customer2-uuid';
   ```

4. **Verify suspended tenant blocked**:
   ```bash
   # Try to login to suspended tenant
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@customer2.com","password":"password123"}'

   # Expected: 403 Forbidden or "Tenant suspended" error
   ```

**Success Criteria**:
- ✅ All tenant operations logged in audit table
- ✅ Logs capture who, what, when for compliance
- ✅ Suspension logged with old/new state
- ✅ Suspended tenants blocked from login
- ✅ No PII in audit logs (only emails, actions, UUIDs)

---

## Performance Validation

### Load Test: Concurrent Tenant Discovery

**Goal**: Verify system handles multiple concurrent tenant discovery requests

```bash
# Run 100 concurrent requests
ab -n 100 -c 10 -T 'application/json' \
  -p tenant_discovery_payload.json \
  http://localhost:8000/api/auth/discover-tenant

# Check payload file:
echo '{"email":"user@customer1.com"}' > tenant_discovery_payload.json
```

**Expected Results**:
- Requests/sec: >100
- Mean response time: <50ms
- 99th percentile: <200ms
- 0% errors

### Database Connection Pooling

**Goal**: Verify connection pools isolated per tenant

```bash
# Monitor active connections
psql -h localhost -U postgres -c "
  SELECT
    datname,
    count(*) as active_connections
  FROM pg_stat_activity
  WHERE datname LIKE '%taskifai%'
  GROUP BY datname
  ORDER BY active_connections DESC;
"
```

**Expected**:
- Each tenant database: 1-10 connections
- Tenant registry: 1-5 connections
- No connection sharing between tenant databases

---

## Rollback Procedure

If validation fails, rollback using:

```bash
# 1. Remove new tenant from registry
psql -h <registry-db> -c "
  DELETE FROM user_tenants WHERE tenant_id = 'customer2-uuid';
  DELETE FROM tenants WHERE tenant_id = 'customer2-uuid';
"

# 2. Remove Supabase project (manual via dashboard)
# Settings → General → Danger Zone → Delete Project

# 3. Clear any test data
# No action needed (data was isolated in deleted tenant DB)
```

---

## Success Checklist

- [ ] Scenario 1: Regular user single-tenant login works
- [ ] Scenario 2: Super admin multi-tenant access works
- [ ] Scenario 3: New tenant provisioning successful
- [ ] Scenario 4: Data isolation verified (no cross-tenant access)
- [ ] Scenario 5: Audit logging captures all operations
- [ ] Performance: Tenant discovery <200ms p99
- [ ] Security: Encrypted credentials never exposed in API
- [ ] Security: JWT tenant_id enforced on all requests

---

## Troubleshooting

### Issue: "No tenant found for email"

**Solution**:
```bash
# Check user_tenants mapping
psql -h <registry-db> -c "
  SELECT * FROM user_tenants WHERE email = 'user@example.com';
"
# If missing, add mapping:
# INSERT INTO user_tenants (email, tenant_id, role)
# VALUES ('user@example.com', 'tenant-uuid', 'member');
```

### Issue: "Tenant suspended" error

**Solution**:
```bash
# Activate tenant
curl -X PATCH http://localhost:8000/api/admin/tenants/tenant-uuid \
  -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" \
  -d '{"is_active": true}'
```

### Issue: Credentials decryption fails

**Solution**:
```bash
# Verify SECRET_KEY matches between encryption and decryption
echo $SECRET_KEY
# Re-encrypt with correct key if needed
```

---

## Next Steps

After successful validation:

1. **Production Deployment**:
   - Configure DNS wildcard: `*.taskifai.com`
   - Update CORS for production domains
   - Rotate SECRET_KEY (re-encrypt credentials)
   - Enable rate limiting on discovery endpoint

2. **Customer Onboarding**:
   - Document customer provisioning workflow
   - Create admin scripts for automated provisioning
   - Setup monitoring for tenant health

3. **Future Automation** (Phase 6):
   - Integrate Supabase Management API
   - Automate database provisioning
   - Implement self-service tenant creation

---

**Estimated Total Time**: 15-20 minutes for complete validation
**Status**: Ready for /tasks command to generate implementation tasks
