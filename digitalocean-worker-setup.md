# DigitalOcean Celery Worker Setup

## Problem
Upload functionality fails because Celery worker is not running on DigitalOcean App Platform.

**Error**: `kombu.exceptions.OperationalError: Connection closed by server.`

**Root Cause**: DigitalOcean app only runs the backend API service. The Celery worker (which processes upload tasks) is defined in docker-compose but not deployed to DigitalOcean.

---

## Solution: Add Worker Component

### Option 1: Via DigitalOcean Console (Recommended)

1. **Navigate to your app**:
   - Go to: https://cloud.digitalocean.com/apps
   - Select: `taskifai-demo` app

2. **Add Worker Component**:
   - Click: **"Settings"** → **"Components"**
   - Click: **"Add Component"**
   - Select: **"Worker"**

3. **Configure Worker**:
   ```
   Name: celery-worker
   Source: Same as backend (GitHub: TaskifaiDavid/taskfai_platform_v2.0)
   Branch: master
   Source Directory: /backend
   Dockerfile Path: backend/Dockerfile (or leave default)

   Run Command:
   celery -A app.workers.celery_app worker --loglevel=info

   Instance Size: Basic (512 MB RAM)
   Instance Count: 1
   ```

4. **Environment Variables** (should inherit from app level):
   - `REDIS_URL` - Your Redis connection string (rediss://...)
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_SERVICE_KEY` - Supabase service role key
   - `SECRET_KEY` - Your JWT secret key
   - `OPENAI_API_KEY` - OpenAI API key
   - `SENDGRID_API_KEY` - SendGrid key (optional for now)

5. **Save and Deploy**:
   - Click: **"Save"**
   - DigitalOcean will deploy the worker component
   - Wait for deployment to complete (~3-5 minutes)

---

### Option 2: Via App Spec (YAML)

If you prefer infrastructure-as-code, create `.do/app.yaml`:

```yaml
name: taskifai-demo
region: nyc
services:
  - name: backend
    github:
      repo: TaskifaiDavid/taskfai_platform_v2.0
      branch: master
      deploy_on_push: true
    source_dir: backend
    dockerfile_path: backend/Dockerfile
    http_port: 8000
    instance_count: 1
    instance_size_slug: basic-xxs
    routes:
      - path: /
    envs:
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${REDIS_URL}
      - key: SUPABASE_URL
        scope: RUN_TIME
        value: ${SUPABASE_URL}
      - key: SUPABASE_SERVICE_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SUPABASE_SERVICE_KEY}
      - key: SECRET_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SECRET_KEY}
      - key: OPENAI_API_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${OPENAI_API_KEY}

workers:
  - name: celery-worker
    github:
      repo: TaskifaiDavid/taskfai_platform_v2.0
      branch: master
      deploy_on_push: true
    source_dir: backend
    dockerfile_path: backend/Dockerfile
    instance_count: 1
    instance_size_slug: basic-xxs
    run_command: celery -A app.workers.celery_app worker --loglevel=info
    envs:
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${REDIS_URL}
      - key: SUPABASE_URL
        scope: RUN_TIME
        value: ${SUPABASE_URL}
      - key: SUPABASE_SERVICE_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SUPABASE_SERVICE_KEY}
      - key: SECRET_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${SECRET_KEY}
      - key: OPENAI_API_KEY
        scope: RUN_TIME
        type: SECRET
        value: ${OPENAI_API_KEY}

static_sites:
  - name: frontend
    github:
      repo: TaskifaiDavid/taskfai_platform_v2.0
      branch: master
      deploy_on_push: true
    source_dir: frontend
    build_command: npm run build
    output_dir: dist
    routes:
      - path: /
    envs:
      - key: VITE_API_URL
        scope: BUILD_TIME
        value: https://taskifai-demo-ak4kq.ondigitalocean.app
```

Then update your app:
```bash
doctl apps update <app-id> --spec .do/app.yaml
```

---

## Verification Steps

After adding the worker:

1. **Check Worker Logs**:
   ```bash
   doctl apps logs <app-id> --type worker --tail 50
   ```

   Expected output:
   ```
   [2025-10-12 11:30:00] celery@worker ready.
   [2025-10-12 11:30:00] celery.worker.strategy: Connected to redis://...
   ```

2. **Test Upload**:
   - Go to: https://demo.taskifai.com
   - Try uploading a file
   - Should succeed without 500 error

3. **Monitor Task Processing**:
   ```bash
   # Check active tasks
   celery -A app.workers.celery_app inspect active

   # Check worker status
   celery -A app.workers.celery_app inspect stats
   ```

---

## Cost Estimate

**Worker Component**:
- Basic (512 MB RAM): $5/month
- Professional (1 GB RAM): $12/month

**Recommendation**: Start with Basic ($5/month). You can scale up if needed.

---

## Troubleshooting

### Worker Not Starting
**Check logs for errors**:
```bash
doctl apps logs <app-id> --type worker --tail 100
```

Common issues:
- Missing environment variables
- Redis connection string incorrect
- Dockerfile not building correctly

### Tasks Not Processing
**Verify Redis connection**:
```bash
# From backend container
redis-cli -u $REDIS_URL ping
# Expected: PONG
```

**Check Celery can connect to Redis**:
```bash
celery -A app.workers.celery_app inspect ping
# Expected: celery@worker: OK
```

### Upload Still Failing
**Check backend logs**:
```bash
doctl apps logs <app-id> --type run --tail 50
```

Look for:
- ✅ `Celery task queued: process_upload`
- ✅ `Task completed successfully`
- ❌ Any Redis connection errors

---

## Alternative: Temporary Workaround (Not Recommended)

If you need uploads working immediately while setting up the worker, you can make uploads synchronous:

**File**: `backend/app/api/uploads.py` (line 88)

```python
# Current (async with Celery):
process_upload.delay(batch_id, user_id)

# Temporary synchronous (blocks API):
from app.workers.tasks import process_upload
process_upload(batch_id, user_id)
```

**⚠️ Warning**: This will make the upload endpoint slow (blocks until processing completes). Only use for testing!

---

## Summary

✅ **Action Required**: Add Worker component to DigitalOcean app
✅ **Run Command**: `celery -A app.workers.celery_app worker --loglevel=info`
✅ **Environment Variables**: Same as backend (REDIS_URL, SUPABASE_*, etc.)
✅ **Cost**: $5/month (Basic instance)

Once the worker is deployed, upload functionality will work!
