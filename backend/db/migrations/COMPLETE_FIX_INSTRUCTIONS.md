# Complete Dashboard KPI Fix Instructions

## Status: Ready to Apply

You have 2 configs in Supabase but dashboard still shows 500 error. This is because:
- ✅ Table exists: `dynamic_dashboard_configs`
- ✅ Data exists: 2 configs in database
- ❌ **RLS blocks service_role**: Backend uses `service_key` but only `authenticated` role has SELECT policy

## Quick Fix (2 Steps)

### Step 1: Apply RLS Fix to Supabase
1. Go to: https://supabase.com/dashboard/project/gzrcawkeqcpixjjwvoxm/sql
2. Click: **SQL Editor** → **New Query**
3. Copy/paste: `backend/db/migrations/fix_dashboard_rls_service_role.sql`
4. Click: **Run**

You should see output showing 5 policies including the new one:
```
"Service role can read all configs" | {service_role} | SELECT
```

### Step 2: Deploy Code Changes
The code fix is already done in your local files:
- Fixed: `.is_("user_id", "null")` → `.is_("user_id", None)` in 2 places

Now deploy to production:

```bash
# Commit changes
git add backend/app/api/dashboard_config.py
git add backend/db/migrations/
git commit -m "fix: add service_role RLS policy for dashboard configs

- Add service_role SELECT policy to dynamic_dashboard_configs
- Fix .is_() query syntax from 'null' string to None
- Resolves 500 error on /api/dashboard-configs/default endpoint"

# Push to trigger deployment
git push origin master
```

### Step 3: Wait & Test (5 minutes)
1. Wait for DigitalOcean deployment (~3-5 minutes)
2. Refresh: https://demo.taskifai.com
3. Dashboard KPIs should load: Total Revenue, Total Units, etc.
4. Browser console: 200 OK (not 500)

---

## What Was Wrong

### Problem 1: RLS Too Restrictive
```sql
-- Only authenticated role could read
CREATE POLICY "Users can read own dashboards or tenant defaults"
    ON dynamic_dashboard_configs FOR SELECT
    TO authenticated  -- ❌ Backend uses service_role, not authenticated
    USING (user_id = auth.uid() OR user_id IS NULL);
```

### Solution: Add Service Role Policy
```sql
-- Now service_role can read too
CREATE POLICY "Service role can read all configs"
    ON dynamic_dashboard_configs FOR SELECT
    TO service_role  -- ✅ Allows backend service_key queries
    USING (true);
```

### Problem 2: Wrong Query Syntax
```python
# Wrong - checks for string "null"
.is_("user_id", "null")

# Correct - checks for NULL value
.is_("user_id", None)
```

---

## How Backend Auth Works

```
Request Flow:
User Browser → JWT Token → Backend API
                           ↓
                    get_current_user()
                    validates JWT
                           ↓
                    get_supabase_client()
                    uses service_key ← Uses service_role, not authenticated role!
                           ↓
                    Query database with service_role
                    (bypasses user RLS but still needs policies!)
```

**Key Point**: Backend uses `service_key` which has `service_role` permission, not `authenticated` role. So user-only policies don't apply!

---

## Files Modified

### Created
- ✅ `migrations/fix_dashboard_rls_service_role.sql` - RLS policy fix

### Updated
- ✅ `app/api/dashboard_config.py` - Fixed query syntax (2 locations)

---

## Verification

After deployment, test the endpoint:
```bash
# Should return 200 with dashboard config JSON
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://demo.taskifai.com/api/dashboard-configs/default
```

Or check in browser console:
```javascript
// Should see 200 OK, not 500
GET https://demo.taskifai.com/api/dashboard-configs/default
```

---

## Need to Customize Dashboard?

Once it's working, you can customize KPIs via SQL:

```sql
UPDATE dynamic_dashboard_configs
SET kpis = '["total_revenue", "reseller_count", "yoy_growth", "top_products"]'::jsonb
WHERE is_default = true AND user_id IS NULL;
```

Available KPIs: `total_revenue`, `total_units`, `avg_price`, `total_uploads`, `reseller_count`, `category_mix`, `yoy_growth`, `top_products`
