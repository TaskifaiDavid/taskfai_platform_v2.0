# Login Troubleshooting Guide

## Issue: Cannot Login After Computer Crash

### ✅ FIXED: Frontend Configuration
The root cause has been identified and fixed:
- Frontend was pointing to `localhost:8000` (stopped after crash)
- Now points to production backend: `taskifai-demo-ak4kq.ondigitalocean.app`
- Frontend rebuilt with correct configuration

### Deployment Status
- ✅ Configuration updated: `frontend/.env`
- ✅ Frontend rebuilt: `frontend/dist/`
- ⏳ **Pending**: Upload dist/ to DigitalOcean Spaces
- ⏳ **Pending**: Clear browser cache

---

## Step-by-Step Recovery

### 1. Deploy Updated Frontend
```bash
# Option A: Use deployment script
./scripts/deploy-frontend.sh

# Option B: Manual deployment
cd frontend
npm run build
# Upload dist/ contents to DigitalOcean Spaces
```

### 2. Clear Browser Data
Open browser console (F12) and run:
```javascript
// Clear all stored data
localStorage.clear();
sessionStorage.clear();

// Reload the page
location.reload();
```

### 3. Test Login
- Navigate to: https://demo.taskifai.com
- Email: `david@taskifai.com`
- Password: Your actual password (not "test123")

---

## Common Issues & Solutions

### Issue: "Invalid Credentials" or 401 Error
**Cause**: Wrong password or user not found
**Solution**:
1. Verify your password (it's the one you set during registration)
2. Check user exists:
   ```bash
   # Via Supabase dashboard, run:
   SELECT email, role FROM users WHERE email = 'david@taskifai.com';
   ```

### Issue: "Network Error" or Failed to Fetch
**Cause**: Frontend still pointing to localhost or CORS issue
**Solution**:
1. Check browser DevTools → Network tab
2. Verify API calls go to: `taskifai-demo-ak4kq.ondigitalocean.app`
3. If still showing localhost:
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   - Clear cache: localStorage.clear()
   - Check deployed files have latest build

### Issue: 500 Internal Server Error
**Cause**: Backend issue (password verification, database connection, etc.)
**Check**:
1. Backend health: `curl https://taskifai-demo-ak4kq.ondigitalocean.app/health`
2. Backend logs via DigitalOcean dashboard
3. Environment variables are set correctly

### Issue: 404 Not Found on /api/auth/login
**Cause**: Trying to access API through static site domain
**Solution**: API must be called at `taskifai-demo-ak4kq.ondigitalocean.app`, not `demo.taskifai.com`

---

## Verification Checklist

### ✅ Backend Infrastructure
- [ ] Health check responds: `curl https://taskifai-demo-ak4kq.ondigitalocean.app/health`
- [ ] Returns: `{"status":"healthy","version":"2.0.0"}`

### ✅ Database
- [ ] Supabase main DB (afualzsndhnbsuruwese): ACTIVE
- [ ] Supabase tenant registry (jzyvvmzkhprmqrqmxzdv): ACTIVE
- [ ] User exists with valid password hash

### ✅ Frontend Configuration
- [ ] `frontend/.env` has production URL
- [ ] Frontend rebuilt: `npm run build` completed
- [ ] dist/ directory exists with index.html
- [ ] Files uploaded to DigitalOcean Spaces

### ✅ CORS Configuration
Test CORS preflight:
```bash
curl -X OPTIONS \
  -H "Origin: https://demo.taskifai.com" \
  -H "Access-Control-Request-Method: POST" \
  https://taskifai-demo-ak4kq.ondigitalocean.app/api/auth/login \
  -I
```
Should return:
- `access-control-allow-origin: https://demo.taskifai.com`
- `access-control-allow-methods: POST`

### ✅ Browser State
- [ ] Browser cache cleared
- [ ] localStorage cleared
- [ ] No old tokens stored
- [ ] Hard refresh performed

---

## Testing Login Flow

### Test 1: Backend Health
```bash
curl https://taskifai-demo-ak4kq.ondigitalocean.app/health
# Expected: {"status":"healthy","version":"2.0.0"}
```

### Test 2: User Exists
Query via Supabase dashboard:
```sql
SELECT user_id, email, role, LENGTH(hashed_password) as hash_len
FROM users
WHERE email = 'david@taskifai.com';
```
Expected: 1 row with valid user_id and hash_len = 60

### Test 3: Frontend API URL
Open https://demo.taskifai.com
- Open DevTools → Application → Local Storage
- Check if old tokens exist (clear if so)
- Try login and watch Network tab
- API calls should go to `taskifai-demo-ak4kq.ondigitalocean.app`

---

## Password Reset (If Needed)

If you've forgotten your password, update via Supabase:

```python
# Generate new password hash
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_hash = pwd_context.hash("YOUR_NEW_PASSWORD")
print(new_hash)
```

Then update in Supabase:
```sql
UPDATE users
SET hashed_password = 'PASTE_HASH_HERE'
WHERE email = 'david@taskifai.com';
```

---

## Environment Switching

### For Local Development
```bash
# Use local backend
cp frontend/.env.local frontend/.env
docker-compose up -d
cd frontend && npm run dev
```

### For Production
```bash
# Use production backend
cp frontend/.env.production frontend/.env  # Or edit .env directly
cd frontend && npm run build
# Deploy dist/ to hosting
```

---

## Contact Support

If issues persist:
1. Check DigitalOcean app logs in dashboard
2. Check Supabase logs for database errors
3. Verify all environment variables in DigitalOcean app settings
4. Ensure DNS/Cloudflare settings haven't changed

## Summary of Fix

**Problem**: Frontend hardcoded to localhost, which stopped working after crash
**Solution**: Updated frontend to use production backend URL
**Status**: Configuration fixed, awaiting deployment and browser cache clear
