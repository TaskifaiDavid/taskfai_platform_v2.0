# BIBBI v2 - Quick Start Guide

Get Phase 1 running in under 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] Redis running (locally or Docker)
- [ ] Supabase project created
- [ ] SendGrid account (free tier works)

---

## 🚀 5-Minute Setup

### Step 1: Clone and Configure (2 min)

```bash
cd BIBBI_v2

# Backend setup
cd backend
cp .env.example .env

# Edit .env with your credentials
# REQUIRED: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
# REQUIRED: SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
# REQUIRED: SECRET_KEY (generate with: openssl rand -hex 32)
nano .env  # or use your favorite editor
```

### Step 2: Install Dependencies (3 min)

```bash
# Backend (inside backend directory)
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend (in new terminal)
cd frontend
npm install
```

### Step 3: Start Services (3 min)

**Terminal 1 - Redis:**
```bash
redis-server
# Or with Docker: docker run -d -p 6379:6379 redis:latest
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

**Terminal 3 - Backend API:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 4 - Frontend:**
```bash
cd frontend
npm run dev
```

### Step 4: Test Upload (2 min)

1. Open browser: `http://localhost:5173`
2. Create test user (use register endpoint)
3. Create Excel file with sheet "Sell Out by EAN"
4. Upload and watch processing

---

## 🐳 Docker Compose (Alternative)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

---

## ✅ Verify Installation

### Check Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"2.0.0"}
```

### Check Redis Connection
```bash
redis-cli ping
# Expected: PONG
```

### Check Celery Worker
```bash
# In Celery terminal, you should see:
# [INFO] celery@hostname ready
```

### Check Frontend
```bash
# Open browser: http://localhost:5173
# Should see BIBBI login page
```

---

## 🧪 Test with Sample Data

### Create Test File

**Option 1: Use Generator (requires openpyxl)**
```bash
cd backend
source venv/bin/activate
python scripts/generate_test_data.py
```

**Option 2: Manual Excel File**

Create `test_boxnox.xlsx`:
- Sheet name: "Sell Out by EAN"
- Headers: Product EAN | Functional Name | Sold Qty | Sales Amount (EUR) | Reseller | Month | Year
- Sample row: `1234567890123 | Test Product | 10 | 99.99 | Retailer A | 1 | 2025`

### Upload Test File

**Via UI:**
1. Go to `http://localhost:5173`
2. Navigate to Upload
3. Select mode: Append
4. Drop test file
5. Click Upload

**Via API:**
```bash
# Get auth token first (register/login)
TOKEN="your-token"

curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@backend/test_data/test_boxnox.xlsx" \
  -F "mode=append"
```

---

## 🔧 Common Issues

### "Redis connection refused"
```bash
# Start Redis
redis-server

# Or check if already running
redis-cli ping
```

### "Celery worker not processing"
```bash
# Check Redis is running
redis-cli ping

# Restart Celery with verbose logging
celery -A app.workers.celery_app worker --loglevel=debug --pool=solo
```

### "Database connection error"
```bash
# Verify Supabase credentials in .env
# Check SUPABASE_URL and SUPABASE_SERVICE_KEY
# Ensure RLS policies are applied (see database/schema.sql)
```

### "Email not sent"
```bash
# Verify SendGrid API key
# Check FROM email is verified in SendGrid dashboard
# Look for errors in email_logs table
```

### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Backend
# or
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📁 Project Structure Quick Reference

```
BIBBI_v2/
├── backend/
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   │   ├── auth.py
│   │   │   └── uploads.py ✅ NEW
│   │   ├── services/         # Business logic
│   │   │   ├── file_validator.py ✅ NEW
│   │   │   ├── file_storage.py ✅ NEW
│   │   │   ├── data_inserter.py ✅ NEW
│   │   │   ├── email/
│   │   │   │   ├── sendgrid_client.py ✅ NEW
│   │   │   │   ├── notifier.py ✅ NEW
│   │   │   │   └── templates/
│   │   │   └── vendors/
│   │   │       ├── detector.py ✅ NEW
│   │   │       └── boxnox_processor.py ✅ NEW
│   │   ├── workers/          # Celery tasks
│   │   │   ├── celery_app.py ✅ NEW
│   │   │   └── tasks.py ✅ NEW
│   │   └── main.py
│   ├── scripts/
│   │   └── generate_test_data.py ✅ NEW
│   ├── test_data/
│   │   └── README.md ✅ NEW
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── FileUpload.tsx ✅ NEW
│   │   ├── hooks/
│   │   │   └── useUploadProgress.ts ✅ NEW
│   │   └── pages/
│   └── package.json
│
├── IMPLEMENTATION_PLAN.md
├── PHASE1_IMPLEMENTATION_COMPLETE.md ✅ NEW
├── QUICKSTART.md ✅ NEW (this file)
└── PROJECT_STATUS.md
```

---

## 🎯 What's Working Now (Phase 1)

✅ **File Upload**
- Drag-and-drop UI with validation
- File size/type checking
- Append vs Replace modes

✅ **Background Processing**
- Celery task queue
- Redis broker
- Async file processing

✅ **Vendor Detection**
- Auto-detect Boxnox files
- Confidence scoring
- Extensible for other vendors

✅ **Data Processing**
- Excel file parsing
- Data transformation
- Validation (EAN, dates, etc.)

✅ **Database**
- Row-level security (RLS)
- User data isolation
- Duplicate detection

✅ **Email Notifications**
- Success/failure emails
- SendGrid integration
- Email logging

---

## 📚 Documentation

- **Setup**: This file (QUICKSTART.md)
- **Phase 1 Complete**: PHASE1_IMPLEMENTATION_COMPLETE.md
- **Full Plan**: IMPLEMENTATION_PLAN.md
- **Project Status**: PROJECT_STATUS.md
- **Test Data**: backend/test_data/README.md

---

## 🆘 Getting Help

### Check Logs

**Backend:**
```bash
# In uvicorn terminal - see API requests
```

**Celery:**
```bash
# In celery terminal - see task processing
```

**Redis:**
```bash
# Check queue status
redis-cli
> KEYS *
> LLEN celery
```

**Database:**
```sql
-- In Supabase SQL Editor
SELECT * FROM upload_batches ORDER BY uploaded_at DESC LIMIT 5;
SELECT * FROM sellout_entries2 ORDER BY created_at DESC LIMIT 10;
SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 5;
```

### Debug Mode

**Enable verbose logging:**
```bash
# Backend
DEBUG=true uvicorn app.main:app --reload --log-level debug

# Celery
celery -A app.workers.celery_app worker --loglevel=debug --pool=solo
```

---

## ✨ Next: Phase 2

Once Phase 1 is working:
1. Test with real Boxnox files
2. Verify email notifications
3. Check database for inserted records
4. Ready to add more vendors in Phase 2!

**Phase 2 Adds:**
- 8 more vendor processors
- Currency conversion
- Enhanced error reporting
- UI improvements

**Estimated Time:** 2 weeks

---

**Last Updated:** October 3, 2025
**Phase 1 Status:** ✅ Complete and Ready for Testing
