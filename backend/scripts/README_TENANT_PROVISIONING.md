# Tenant Provisioning Guide

This guide shows you how to add new tenants to TaskifAI without using the admin UI.

## Quick Start

```bash
# 1. Edit tenant details
nano backend/scripts/tenants_to_add.md

# 2. Generate SQL
python backend/scripts/add_tenant.py

# 3. Execute SQL in Supabase
# Copy contents of backend/scripts/add_tenants.sql
# Paste into Supabase SQL Editor → Run
```

## Detailed Steps

### Step 1: Get Supabase Credentials

For each new tenant, you need a Supabase project:

1. Go to https://supabase.com/dashboard
2. Create new project (or use existing)
3. Go to: **Settings → API**
4. Copy:
   - **Project URL**: `https://abcdefgh.supabase.co`
   - **anon public key**: Starts with `eyJh...`
   - **service_role secret key**: Starts with `eyJh...`

### Step 2: Fill Tenant Template

Edit `backend/scripts/tenants_to_add.md`:

```yaml
company_name: "Bibbi Skincare"
subdomain: "bibbi"
database_url: "https://your-project.supabase.co"
service_key: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
anon_key: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
is_active: true
metadata:
  industry: "Skincare"
  contact_email: "admin@bibbi.com"
```

**Important:**
- `subdomain`: Lowercase, no spaces (becomes `bibbi.taskifai.com`)
- `database_url`: Full Supabase project URL
- `service_key`: Service role key (has admin access)
- `anon_key`: Public anon key (for RLS)

### Step 3: Generate SQL

```bash
cd /path/to/TaskifAI_platform_v2.0
python backend/scripts/add_tenant.py
```

**Output:**
```
✅ Generated SQL for tenant: bibbi (Bibbi Skincare)

✅ Generated SQL file: backend/scripts/add_tenants.sql
   Tenants processed: 1

📋 Next steps:
   1. Review backend/scripts/add_tenants.sql
   2. Execute in Supabase SQL Editor (tenant registry database)
   3. Verify tenants: SELECT * FROM tenants ORDER BY created_at DESC;
```

### Step 4: Execute SQL in Supabase

**Option A: Supabase Dashboard (Recommended)**
1. Go to your **tenant registry** Supabase project
2. Click **SQL Editor**
3. Open `backend/scripts/add_tenants.sql`
4. Copy entire contents
5. Paste into SQL Editor
6. Click **Run**

**Option B: Command Line (psql)**
```bash
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres" \
  -f backend/scripts/add_tenants.sql
```

**Option C: Supabase MCP (if enabled)**
```bash
# Via Claude Code with Supabase MCP
# Use mcp__supabase__execute_sql tool
```

### Step 5: Verify Tenant

```sql
-- Check tenant was added
SELECT
    company_name,
    subdomain,
    database_url,
    is_active,
    created_at
FROM tenants
WHERE subdomain = 'bibbi';

-- Check tenant config
SELECT
    t.company_name,
    tc.max_file_size_mb,
    tc.features_enabled
FROM tenants t
JOIN tenant_configs tc ON t.tenant_id = tc.tenant_id
WHERE t.subdomain = 'bibbi';
```

### Step 6: Test Access

1. Go to: `https://bibbi.taskifai.com`
2. Should see login page
3. Login with user credentials (create user first in tenant's database)

## Creating First User for New Tenant

After adding tenant, create an admin user in the tenant's Supabase project:

```sql
-- Run this in the TENANT'S database (not tenant registry)
INSERT INTO users (email, hashed_password, full_name, role)
VALUES (
    'admin@bibbi.com',
    '$2b$12$...',  -- Generate with bcrypt
    'Admin User',
    'admin'
);
```

**Or use the backend API:**
```bash
POST https://bibbi.taskifai.com/api/auth/register
{
  "email": "admin@bibbi.com",
  "password": "secure_password",
  "full_name": "Admin User"
}
```

## Security Notes

⚠️ **IMPORTANT:**

1. **Generated SQL contains unencrypted credentials**
   - Delete `add_tenants.sql` after execution
   - Don't commit to git

2. **Production Encryption:**
   ```sql
   -- Use encrypt_data() function in production:
   INSERT INTO tenants (..., encrypted_credentials, ...)
   VALUES (..., encrypt_data('{"service_key":"..."}', 'ENCRYPTION_KEY'), ...);
   ```

3. **Subdomain DNS:**
   - Add `CNAME` record: `bibbi.taskifai.com` → `demo.taskifai.com`
   - Or configure wildcard: `*.taskifai.com` → App Platform

## Troubleshooting

### "Subdomain already exists"
```sql
-- Check existing subdomain
SELECT * FROM tenants WHERE subdomain = 'bibbi';

-- Update instead of insert (script handles this with ON CONFLICT)
```

### "Cannot connect to tenant database"
- Verify `database_url` is correct
- Check `service_key` has admin permissions
- Ensure tenant's Supabase project is active

### "User not found" after tenant creation
- Create user in tenant's database (not registry)
- Or use `/api/auth/register` endpoint

## File Reference

```
backend/scripts/
├── tenants_to_add.md          # Template you edit
├── add_tenant.py              # Script to generate SQL
├── add_tenants.sql            # Generated SQL (don't commit)
└── README_TENANT_PROVISIONING.md  # This file
```

## Example: Add Multiple Tenants

Edit `tenants_to_add.md`:

```yaml
company_name: "Bibbi Skincare"
subdomain: "bibbi"
database_url: "https://project1.supabase.co"
service_key: "key1..."
anon_key: "anon1..."
is_active: true
metadata:
  industry: "Skincare"

---

company_name: "Demo Company"
subdomain: "democompany"
database_url: "https://project2.supabase.co"
service_key: "key2..."
anon_key: "anon2..."
is_active: true
metadata:
  industry: "Retail"
```

Run `python add_tenant.py` → Generates SQL for both tenants.

## Questions?

- Check: `backend/db/tenants_schema.sql` for database schema
- Check: `backend/app/services/tenant_registry.py` for tenant service
- Check: `backend/app/core/tenant.py` for tenant context logic
