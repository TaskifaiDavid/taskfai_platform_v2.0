# 14. Tenant Provisioning Guide

**Step-by-step guide for adding new customers to the TaskifAI platform**

This document provides detailed instructions for TaskifAI platform administrators to provision new tenants (customers) once the multi-tenant base is complete.

---

## 14.1. Prerequisites

Before provisioning a new tenant, ensure you have:

- ✅ Platform administrator access (admin JWT token)
- ✅ Supabase account with API access
- ✅ DNS management access for taskifai.com
- ✅ Customer information (company name, admin email, subdomain preference)
- ✅ Base schema.sql file ready for deployment
- ✅ Default vendor configurations prepared

---

## 14.2. Provisioning Workflow Overview

```
┌─────────────────────────────────────────────────┐
│  Step 1: Create Supabase Project                │
│  Step 2: Initialize Database Schema              │
│  Step 3: Seed Default Configurations            │
│  Step 4: Create Tenant Record                   │
│  Step 5: Configure DNS (if needed)              │
│  Step 6: Create Initial Admin User              │
│  Step 7: Send Welcome Email                     │
│  Step 8: Verify & Test                          │
└─────────────────────────────────────────────────┘
```

---

## 14.3. Step-by-Step Provisioning

### Step 1: Create Supabase Project

**Via Supabase Dashboard:**

1. Log into Supabase dashboard (https://supabase.com)
2. Click "New Project"
3. Fill in project details:
   ```
   Name: TaskifAI - Customer Name
   Database Password: [Generate secure password]
   Region: [Choose closest to customer]
   Plan: Pro ($25/month)
   ```
4. Wait for project creation (~2 minutes)
5. Save the following credentials:
   - Project URL: `https://[project-ref].supabase.co`
   - Project API Key (anon): `eyJh...`
   - Project API Key (service): `eyJh...`

**Via Supabase CLI (Alternative):**

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Create new project
supabase projects create "TaskifAI - Customer Name" \
  --org-id YOUR_ORG_ID \
  --db-password SECURE_PASSWORD \
  --region us-east-1 \
  --plan pro
```

---

### Step 2: Initialize Database Schema

**Run the base schema on the new database:**

```bash
# Method 1: Via Supabase Dashboard
# 1. Go to SQL Editor in new project
# 2. Paste contents of backend/db/schema.sql
# 3. Click "Run"

# Method 2: Via psql
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" \
  -f backend/db/schema.sql

# Method 3: Via Supabase CLI
supabase db push --project-ref [PROJECT-REF] \
  --db-url "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres" \
  --file backend/db/schema.sql
```

**Verify schema creation:**
```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public';

-- Expected tables:
-- users, products, resellers, sellout_entries2,
-- ecommerce_orders, upload_batches, error_reports,
-- conversation_history, dashboard_configs, email_logs,
-- vendor_configs
```

---

### Step 3: Seed Default Configurations

**Seed vendor configurations:**

```sql
-- Insert default Boxnox configuration
INSERT INTO vendor_configs (vendor_name, config_data, is_active) VALUES
('boxnox', '{
  "currency": "EUR",
  "header_row": 0,
  "pivot_format": false,
  "column_mapping": {
    "Product EAN": "product_ean",
    "Functional Name": "functional_name",
    "Sold Qty": "quantity",
    "Sales Amount (EUR)": "sales_eur",
    "Reseller": "reseller",
    "Month": "month",
    "Year": "year"
  },
  "validation_rules": {
    "ean_length": 13,
    "month_range": [1, 12],
    "required_fields": ["product_ean", "quantity", "month", "year"]
  }
}'::jsonb, true);

-- Repeat for other default vendors (Galilu, Skins, etc.)
```

**Seed sample resellers (optional):**

```sql
INSERT INTO resellers (name, country) VALUES
('Galilu', 'Poland'),
('Boxnox', 'Europe'),
('Skins SA', 'South Africa')
ON CONFLICT (name) DO NOTHING;
```

---

### Step 4: Create Tenant Record

**Add tenant to master registry:**

```python
# Via Admin API endpoint
POST https://api.taskifai.com/admin/tenants
Authorization: Bearer {ADMIN_JWT_TOKEN}

{
  "company_name": "Customer Inc",
  "subdomain": "customerinc",
  "database_url": "https://[project-ref].supabase.co",
  "database_anon_key": "eyJh...",
  "database_service_key": "eyJh...",
  "admin_email": "admin@customer.com",
  "admin_name": "John Doe"
}
```

**Response:**
```json
{
  "tenant_id": "abc-123-def-456",
  "subdomain": "customerinc",
  "database_url": "https://xyz.supabase.co",
  "is_active": true,
  "created_at": "2025-10-06T10:00:00Z",
  "access_url": "https://customerinc.taskifai.com"
}
```

**Manual Database Insert (Alternative):**

```sql
-- In master platform database
INSERT INTO tenants (
  company_name,
  subdomain,
  database_url,
  database_key,
  is_active
) VALUES (
  'Customer Inc',
  'customerinc',
  encrypt('https://[project-ref].supabase.co'),  -- Encrypted
  encrypt('eyJh...'),                             -- Encrypted
  true
) RETURNING tenant_id, subdomain;
```

---

### Step 5: Configure DNS (Automatic with Wildcard)

**DNS should already be configured with wildcard:**

```
# Existing wildcard DNS
*.taskifai.com  →  Vercel (Frontend)
```

**Verify subdomain works:**

```bash
# Should resolve to Vercel
dig customerinc.taskifai.com

# Test in browser
curl https://customerinc.taskifai.com
# Should return frontend app
```

**Manual DNS (If wildcard not set up):**

```
# Add CNAME record
customerinc.taskifai.com  →  cname.vercel-dns.com
```

---

### Step 6: Create Initial Admin User

**Create admin user in tenant's database:**

```python
# Via API endpoint
POST https://customerinc.taskifai.com/api/auth/register

{
  "email": "admin@customer.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "admin"
}
```

**Manual SQL (Alternative):**

```sql
-- In tenant's database
INSERT INTO users (
  email,
  hashed_password,
  full_name,
  role
) VALUES (
  'admin@customer.com',
  crypt('SecurePassword123!', gen_salt('bf')),
  'John Doe',
  'admin'
);
```

---

### Step 7: Send Welcome Email

**Automated via provisioning API:**

```python
# API automatically sends welcome email with:
- Tenant subdomain URL
- Admin credentials
- Getting started guide
- Support contact
```

**Manual Email Template:**

```
Subject: Welcome to TaskifAI - Your Account is Ready!

Hi {admin_name},

Your TaskifAI account has been successfully created!

Access your dashboard:
https://{subdomain}.taskifai.com

Login Credentials:
Email: {admin_email}
Password: {temporary_password}

Getting Started:
1. Log in and change your password
2. Upload your first sales data file
3. Explore the AI chat assistant
4. Configure external dashboards

Need help? Reply to this email or visit docs.taskifai.com

Welcome aboard!
The TaskifAI Team
```

---

### Step 8: Verify & Test

**Verification Checklist:**

```bash
# 1. Test subdomain access
curl https://customerinc.taskifai.com
✅ Should return frontend

# 2. Test tenant context
curl https://customerinc.taskifai.com/api/health
✅ Should include tenant_id in response

# 3. Test login
curl -X POST https://customerinc.taskifai.com/api/auth/login \
  -d '{"email":"admin@customer.com","password":"..."}' \
✅ Should return JWT with tenant_id claim

# 4. Test database isolation
curl https://customerinc.taskifai.com/api/uploads/batches \
  -H "Authorization: Bearer {TOKEN}"
✅ Should return empty array (new tenant)

# 5. Test file upload
# Upload test file via UI
✅ Should process successfully
```

**Database Verification:**

```sql
-- Verify tenant record
SELECT * FROM tenants WHERE subdomain = 'customerinc';

-- Verify tenant database
-- Switch to tenant DB
SELECT COUNT(*) FROM users;  -- Should have 1 admin user
SELECT COUNT(*) FROM vendor_configs;  -- Should have defaults
```

---

## 14.4. Automated Provisioning Script

**For production use, create automated script:**

```python
# provision_tenant.py
import os
import requests
from supabase import create_client

def provision_tenant(
    company_name: str,
    subdomain: str,
    admin_email: str,
    admin_name: str
):
    """
    Automated tenant provisioning

    Usage:
        python provision_tenant.py \
          --company "Customer Inc" \
          --subdomain "customerinc" \
          --email "admin@customer.com" \
          --name "John Doe"
    """

    # 1. Create Supabase project
    project = create_supabase_project(company_name)

    # 2. Initialize schema
    run_schema_migration(project.url, project.password)

    # 3. Seed configurations
    seed_default_configs(project.url, project.service_key)

    # 4. Create tenant record
    tenant = create_tenant_record(
        company_name=company_name,
        subdomain=subdomain,
        database_url=project.url,
        database_key=project.anon_key
    )

    # 5. Create admin user
    admin_user = create_admin_user(
        tenant_db_url=project.url,
        email=admin_email,
        name=admin_name
    )

    # 6. Send welcome email
    send_welcome_email(
        to=admin_email,
        subdomain=subdomain,
        password=admin_user.temp_password
    )

    # 7. Verify
    verify_tenant(subdomain)

    print(f"✅ Tenant provisioned successfully!")
    print(f"   URL: https://{subdomain}.taskifai.com")
    print(f"   Tenant ID: {tenant.tenant_id}")

if __name__ == "__main__":
    # Run provisioning
    provision_tenant(...)
```

---

## 14.5. Deprovisioning / Tenant Suspension

**Suspend tenant (disable access):**

```sql
-- In master database
UPDATE tenants
SET is_active = false,
    suspended_at = NOW()
WHERE subdomain = 'customerinc';
```

**Delete tenant (permanent):**

```bash
# 1. Backup tenant database
supabase db dump --project-ref [PROJECT-REF] \
  --file backups/customerinc-$(date +%Y%m%d).sql

# 2. Delete Supabase project
supabase projects delete [PROJECT-REF]

# 3. Remove from tenant registry
DELETE FROM tenants WHERE subdomain = 'customerinc';

# 4. Archive in cold storage (optional)
mv backups/customerinc-*.sql archives/
```

---

## 14.6. Troubleshooting

### Issue: Subdomain not resolving

```bash
# Check DNS
dig customerinc.taskifai.com

# Verify wildcard
dig random-subdomain.taskifai.com
# Both should resolve to same IP

# Solution: Wait for DNS propagation (up to 48h)
# Or add specific CNAME record
```

### Issue: Database connection fails

```bash
# Test connection
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Check credentials
SELECT * FROM tenants WHERE subdomain = 'customerinc';
# Decrypt and verify database_url and database_key
```

### Issue: Tenant not found

```bash
# Check tenant registry
SELECT * FROM tenants WHERE subdomain = 'customerinc';

# Verify is_active = true
UPDATE tenants SET is_active = true WHERE subdomain = 'customerinc';
```

### Issue: Cross-tenant data leak

```bash
# THIS SHOULD NEVER HAPPEN
# If it does, immediately:
1. Suspend all tenants
2. Investigate tenant context middleware
3. Check database connection routing
4. Audit all recent database queries
5. Notify affected customers
```

---

## 14.7. Quick Reference

### Essential Commands

```bash
# Create tenant
curl -X POST https://api.taskifai.com/admin/tenants \
  -H "Authorization: Bearer {ADMIN_TOKEN}" \
  -d '{"company_name":"...","subdomain":"...","admin_email":"..."}'

# Check tenant status
curl https://api.taskifai.com/admin/tenants/{tenant_id} \
  -H "Authorization: Bearer {ADMIN_TOKEN}"

# Suspend tenant
curl -X PATCH https://api.taskifai.com/admin/tenants/{tenant_id}/suspend \
  -H "Authorization: Bearer {ADMIN_TOKEN}"

# Reactivate tenant
curl -X PATCH https://api.taskifai.com/admin/tenants/{tenant_id}/activate \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

### Typical Timeline

```
- Supabase project creation: 2 minutes
- Schema initialization: 1 minute
- Configuration seeding: 30 seconds
- Tenant record creation: 10 seconds
- DNS propagation: 0-10 minutes (if wildcard exists: instant)
- Admin user creation: 10 seconds
- Welcome email: 5 seconds

Total: ~5-15 minutes per tenant
```

---

## 14.8. Summary

Tenant provisioning with TaskifAI is:

✅ **Fast**: 5-15 minutes per tenant
✅ **Secure**: Encrypted credentials, isolated databases
✅ **Automated**: Script-based provisioning available
✅ **Scalable**: Process identical for 1 or 100 tenants
✅ **Reversible**: Easy suspension and restoration

Once the base infrastructure is built, adding new customers is a simple, repeatable process!
