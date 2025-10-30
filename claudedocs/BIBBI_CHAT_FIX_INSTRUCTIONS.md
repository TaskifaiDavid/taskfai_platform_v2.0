# BIBBI Chat System Fix - Manual Migration Required

## What Was Fixed

The BIBBI chat system was failing with error:
```
Could not find the function public.exec_sql(query) in the schema cache
```

### Root Causes Identified:
1. **Missing RPC Function**: `exec_sql()` didn't exist in BIBBI database
2. **Wrong Database Routing**: Chat endpoint bypassed tenant routing system
3. **Schema Mismatch**: Chat agent didn't know about BIBBI's `sales_unified` table

### Code Changes Applied ✅

**1. Chat API (backend/app/api/chat.py)**
- ✅ Added `get_supabase_client()` dependency for tenant routing
- ✅ Passes tenant-routed Supabase client to SQL execution
- ✅ Ensures BIBBI requests → BIBBI database

**2. Chat Agent (backend/app/services/ai_chat/agent.py)**
- ✅ Added `tenant_subdomain` parameter
- ✅ Created `DATABASE_SCHEMA_BIBBI` with `sales_unified` table
- ✅ Agent now selects correct schema based on tenant
- ✅ Updated SQL generation to be tenant-agnostic

**3. SQL Migration (backend/db/migrations/create_exec_sql_rpc_function.sql)**
- ✅ Created secure `exec_sql()` RPC function
- ✅ Only allows SELECT queries (security)
- ✅ Prevents SQL injection
- ✅ Returns JSON results with error handling

---

## Manual Migration Required ⚠️

You need to apply the `exec_sql()` function to the **BIBBI database**.

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to https://supabase.com/dashboard/project/edckqdrbgtnnjfnshjfq
2. Click **SQL Editor** in left sidebar
3. Click **New Query**
4. Copy the entire contents of:
   ```
   backend/db/migrations/create_exec_sql_rpc_function.sql
   ```
5. Paste into SQL Editor
6. Click **Run** button
7. Verify success message appears

### Option 2: Using Local psql (if available)

```bash
# From project root
PGPASSWORD='Tdsommar11!' psql \
  -h db.edckqdrbgtnnjfnshjfq.supabase.co \
  -U postgres \
  -d postgres \
  -f backend/db/migrations/create_exec_sql_rpc_function.sql
```

### Option 3: Using Docker (if psql not installed locally)

```bash
docker run --rm -i postgres:15 psql \
  "postgresql://postgres:Tdsommar11!@db.edckqdrbgtnnjfnshjfq.supabase.co:5432/postgres" \
  < backend/db/migrations/create_exec_sql_rpc_function.sql
```

---

## Verification

After applying the migration, test the chat system:

1. **Login to BIBBI** at https://bibbi.taskifai.com (or demo app)
2. **Open AI Chat** section
3. **Send test query**: "What were my sales last month?"
4. **Expected Result**: Should show sales data from `sales_unified` table
5. **Check Backend Logs**: Should see successful SQL execution, not "exec_sql not found" error

### Verification SQL Query

Run this in Supabase SQL Editor to verify function exists:

```sql
SELECT
  proname as function_name,
  prosrc as source_code
FROM pg_proc
WHERE proname = 'exec_sql';
```

Should return 1 row showing the `exec_sql` function.

---

## What the Migration Does

The `exec_sql()` function:

1. **Accepts**: SQL SELECT query as TEXT parameter
2. **Security Checks**:
   - ✅ Only allows SELECT queries
   - ✅ Blocks DDL (CREATE, DROP, ALTER, TRUNCATE)
   - ✅ Blocks DML (INSERT, UPDATE, DELETE)
   - ✅ Prevents multiple statements (SQL injection protection)
3. **Returns**: JSONB array of query results
4. **Error Handling**: Returns error details as JSON if query fails

### Example Usage

```sql
-- This works (SELECT query)
SELECT exec_sql('SELECT * FROM sales_unified LIMIT 5');

-- This is blocked (INSERT query)
SELECT exec_sql('INSERT INTO sales_unified VALUES (...)');
-- ERROR: Only SELECT queries are allowed

-- This is blocked (multiple statements)
SELECT exec_sql('SELECT * FROM sales_unified; DROP TABLE sales_unified;');
-- ERROR: Multiple statements are not allowed
```

---

## BIBBI Tables Now Available to Chat

After migration, BIBBI chat agent can query:

### 1. **sales_unified** (PRIMARY TABLE)
- All reseller sales data
- Columns: `sale_id`, `user_id`, `product_name`, `functional_name`, `quantity`, `sales_eur`, `month`, `year`, `store_name`, etc.

### 2. **stores**
- Store/location directory
- Columns: `store_id`, `reseller_id`, `store_name`, `city`, `country`

### 3. **product_reseller_mappings**
- Product-to-reseller relationships
- Columns: `product_ean`, `product_name`, `functional_name`, `reseller_sku`

---

## Troubleshooting

### Error: "Function exec_sql not found"
**Solution**: Migration not applied yet. Follow steps above to apply migration.

### Error: "permission denied for function exec_sql"
**Solution**: Re-run migration to ensure GRANT statements execute:
```sql
GRANT EXECUTE ON FUNCTION public.exec_sql(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.exec_sql(TEXT) TO service_role;
```

### Chat returns: "Could not find table sales_unified"
**Check**: Verify BIBBI database has `sales_unified` table:
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'sales_unified';
```

### Chat generates SQL for wrong tables (ecommerce_orders instead of sales_unified)
**Issue**: Tenant routing not working properly. Check:
1. User JWT has correct `subdomain: "bibbi"` claim
2. Backend logs show `[TenantContextMiddleware] Set tenant via override: BIBBI`
3. Chat agent receives `tenant_subdomain="bibbi"` parameter

---

## Next Steps

1. ✅ **Apply migration** to BIBBI database (see instructions above)
2. ✅ **Deploy to production** (changes now in master)
3. ✅ **Test chat** in BIBBI app to verify it works
4. ✅ **Monitor logs** for any remaining issues

## Questions?

If chat still doesn't work after applying migration:
1. Check backend logs for errors
2. Verify JWT token has `subdomain: "bibbi"` claim
3. Test SQL function directly in Supabase SQL Editor
4. Check that BIBBI database URL/credentials are configured in backend environment variables
