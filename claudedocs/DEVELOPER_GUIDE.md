# TaskifAI Developer Guide

**Practical Workflows, Patterns, and Best Practices**

**Last Updated**: 2025-10-25
**Version**: 2.0

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure Walkthrough](#project-structure-walkthrough)
3. [Common Development Workflows](#common-development-workflows)
4. [Adding a New Vendor Processor](#adding-a-new-vendor-processor)
5. [Debugging Guide](#debugging-guide)
6. [Testing Strategy](#testing-strategy)
7. [Code Patterns and Conventions](#code-patterns-and-conventions)
8. [Git Workflow](#git-workflow)

---

## Development Environment Setup

### Prerequisites

```bash
# Required
- Node.js 20+
- Python 3.11+
- Docker & Docker Compose
- Git

# Recommended
- VS Code with extensions:
  - Python
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense
```

### Quick Start (Docker - Recommended)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd TaskifAI_platform_v2.0

# 2. Set up environment variables
cd backend
cp .env.example .env
# Edit .env with your credentials:
# - SUPABASE_URL, SUPABASE_SERVICE_KEY (from Supabase dashboard)
# - OPENAI_API_KEY (from OpenAI)
# - SENDGRID_API_KEY (from SendGrid)
# - SECRET_KEY (generate: openssl rand -hex 32)

cd ../frontend
cp .env.example .env
# Edit .env:
# - VITE_API_URL=http://localhost:8000/api

# 3. Start all services
cd ..
docker-compose up -d

# 4. Verify services
docker-compose ps

# Expected output:
# - backend_api (port 8000)
# - backend_worker (Celery)
# - frontend (port 3000)
# - postgres (port 5432)
# - redis (port 6379)

# 5. View logs
docker-compose logs -f backend_api
docker-compose logs -f backend_worker

# 6. Access application
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
```

### Manual Setup (Without Docker)

#### Backend

```bash
cd backend

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# 4. Set up database
# Option A: Supabase (recommended)
# - Go to Supabase dashboard
# - Open SQL Editor
# - Copy & paste contents of db/schema.sql
# - Execute script

# Option B: Local PostgreSQL
createdb taskifai
psql -U postgres -d taskifai -f db/schema.sql

# 5. Start backend server (terminal 1)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start Celery worker (terminal 2)
celery -A app.workers.celery_app worker --loglevel=info

# 7. Start Redis (terminal 3, if not using Docker)
redis-server
```

#### Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Set up environment variables
cp .env.example .env
# Edit .env:
# VITE_API_URL=http://localhost:8000/api

# 3. Start development server
npm run dev

# Access: http://localhost:3000
```

### Verifying Setup

```bash
# Test backend health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Test API docs (should open in browser)
open http://localhost:8000/api/docs

# Test frontend (should show login page)
open http://localhost:3000

# Test Celery worker
# Check logs for: "celery@hostname ready"
```

---

## Project Structure Walkthrough

### Backend (`/backend/`)

```
backend/
├── app/
│   ├── api/                  # API route handlers (controllers)
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── uploads.py        # File upload endpoints
│   │   ├── bibbi_uploads.py  # BIBBI-specific uploads
│   │   ├── analytics.py      # Analytics endpoints
│   │   ├── chat.py           # AI chat endpoints
│   │   ├── dashboards.py     # Dashboard management
│   │   └── admin.py          # Admin endpoints
│   │
│   ├── core/                 # Core configuration and utilities
│   │   ├── config.py         # Settings (environment variables)
│   │   ├── security.py       # JWT, password hashing
│   │   ├── dependencies.py   # FastAPI dependencies
│   │   └── rate_limiter.py   # Rate limiting logic
│   │
│   ├── models/               # Pydantic request/response models
│   │   ├── user.py           # User models
│   │   ├── upload.py         # Upload models
│   │   └── dashboard_config.py
│   │
│   ├── services/             # Business logic layer
│   │   ├── vendors/          # General vendor processors
│   │   │   ├── base.py       # Base class for general processors
│   │   │   ├── detector.py   # Vendor auto-detection
│   │   │   └── *_processor.py # Vendor-specific processors
│   │   │
│   │   ├── bibbi/            # BIBBI-specific logic
│   │   │   └── processors/
│   │   │       ├── base.py   # BIBBI base class
│   │   │       └── *_processor.py
│   │   │
│   │   ├── ai_chat/          # AI chat system
│   │   │   ├── agent.py      # LangChain agent
│   │   │   └── security.py   # SQL validation
│   │   │
│   │   └── email/            # Email notifications
│   │
│   ├── utils/                # Shared utilities (DRY)
│   │   ├── validation.py     # Data validation functions
│   │   └── excel.py          # Excel parsing utilities
│   │
│   ├── middleware/           # Request/response middleware
│   │   ├── auth.py           # JWT validation
│   │   ├── tenant_context.py # Tenant extraction
│   │   └── logging.py        # Request logging
│   │
│   ├── workers/              # Celery background tasks
│   │   ├── celery_app.py     # Celery configuration
│   │   └── tasks.py          # Task definitions
│   │
│   ├── db/                   # Database schemas and migrations
│   │   ├── schema.sql        # Full database schema
│   │   └── seed_vendor_configs.sql
│   │
│   └── main.py               # FastAPI application entry point
│
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── conftest.py           # Pytest fixtures
│
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker image definition
└── .env.example             # Environment template
```

### Frontend (`/frontend/`)

```
frontend/
├── src/
│   ├── components/           # Reusable React components
│   │   ├── ui/              # UI primitives (buttons, cards, etc.)
│   │   ├── features/        # Feature-specific components
│   │   │   ├── auth/        # Login, logout, protected routes
│   │   │   ├── upload/      # File upload components
│   │   │   ├── analytics/   # Analytics components
│   │   │   └── dashboard/   # Dashboard widgets
│   │   └── layout/          # App layout (sidebar, header)
│   │
│   ├── pages/               # Route-level page components
│   │   ├── LoginPortal.tsx  # Central login portal
│   │   ├── Login.tsx        # Tenant-specific login
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── Uploads.tsx      # Upload interface
│   │   ├── Chat.tsx         # AI chat
│   │   ├── Analytics.tsx    # Advanced analytics
│   │   └── Admin.tsx        # Admin panel
│   │
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.ts       # Authentication hook
│   │   ├── useUpload.ts     # Upload management
│   │   └── useAnalytics.ts  # Analytics data fetching
│   │
│   ├── stores/              # Zustand state management
│   │   └── auth.ts          # Global auth state
│   │
│   ├── api/                 # API service layer
│   │   ├── auth.ts          # Auth API calls
│   │   ├── uploads.ts       # Upload API calls
│   │   ├── analytics.ts     # Analytics API calls
│   │   └── dashboardConfig.ts
│   │
│   ├── lib/                 # Utilities and helpers
│   │   ├── api.ts           # Axios client configuration
│   │   └── utils.ts         # Helper functions
│   │
│   ├── App.tsx              # Root component
│   └── main.tsx             # Entry point
│
├── package.json             # Node dependencies
├── vite.config.ts           # Vite configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── .env.example             # Environment template
```

---

## Common Development Workflows

### Workflow 1: Add New API Endpoint

**Example**: Add endpoint to get upload statistics

```python
# 1. Create Pydantic model (backend/app/models/upload.py)
from pydantic import BaseModel

class UploadStats(BaseModel):
    total_uploads: int
    successful_uploads: int
    failed_uploads: int
    total_rows_processed: int

# 2. Add endpoint (backend/app/api/uploads.py)
from app.models.upload import UploadStats
from app.core.dependencies import get_current_user, get_supabase_client

@router.get("/uploads/stats", response_model=UploadStats)
async def get_upload_stats(
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Get upload statistics for current user"""

    # Query Supabase (ALWAYS filter by user_id!)
    result = supabase.table("upload_batches")\
        .select("processing_status, total_rows")\
        .eq("user_id", user["id"])\
        .execute()

    batches = result.data

    # Calculate stats
    total = len(batches)
    successful = sum(1 for b in batches if b["processing_status"] == "completed")
    failed = sum(1 for b in batches if b["processing_status"] == "failed")
    total_rows = sum(b["total_rows"] or 0 for b in batches)

    return UploadStats(
        total_uploads=total,
        successful_uploads=successful,
        failed_uploads=failed,
        total_rows_processed=total_rows
    )

# 3. Test with curl
curl -X GET "http://localhost:8000/api/uploads/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Check API docs (automatic!)
# Open http://localhost:8000/api/docs
# New endpoint should appear under "Uploads" section
```

**Frontend Integration**:

```typescript
// 1. Add to API service (frontend/src/api/uploads.ts)
interface UploadStats {
  total_uploads: number;
  successful_uploads: number;
  failed_uploads: number;
  total_rows_processed: number;
}

export async function getUploadStats(): Promise<UploadStats> {
  const response = await apiClient.get<UploadStats>('/uploads/stats');
  return response.data;
}

// 2. Create React component (frontend/src/components/features/upload/UploadStats.tsx)
import { useEffect, useState } from 'react';
import { getUploadStats } from '@/api/uploads';

export function UploadStats() {
  const [stats, setStats] = useState<UploadStats | null>(null);

  useEffect(() => {
    getUploadStats().then(setStats);
  }, []);

  if (!stats) return <div>Loading...</div>;

  return (
    <div className="grid grid-cols-4 gap-4">
      <StatCard title="Total Uploads" value={stats.total_uploads} />
      <StatCard title="Successful" value={stats.successful_uploads} />
      <StatCard title="Failed" value={stats.failed_uploads} />
      <StatCard title="Rows Processed" value={stats.total_rows_processed} />
    </div>
  );
}

// 3. Add to page (frontend/src/pages/Uploads.tsx)
import { UploadStats } from '@/components/features/upload/UploadStats';

export function UploadsPage() {
  return (
    <div>
      <h1>File Uploads</h1>
      <UploadStats />
      {/* ... rest of page */}
    </div>
  );
}
```

### Workflow 2: Add Database Column

**Example**: Add `notes` column to `upload_batches` table

```sql
-- 1. Create migration file (backend/db/migrations/add_upload_notes.sql)
ALTER TABLE upload_batches
ADD COLUMN notes TEXT;

-- 2. Apply migration
# If using Supabase:
# - Go to SQL Editor in Supabase dashboard
# - Paste SQL above
# - Execute

# If using local PostgreSQL:
psql -U postgres -d taskifai -f backend/db/migrations/add_upload_notes.sql

-- 3. Update Pydantic model (backend/app/models/upload.py)
class UploadBatch(BaseModel):
    batch_id: UUID
    vendor_name: str
    # ... other fields
    notes: Optional[str] = None  # NEW FIELD

-- 4. Update endpoint (backend/app/api/uploads.py)
@router.patch("/uploads/batches/{batch_id}/notes")
async def update_upload_notes(
    batch_id: UUID,
    notes: str,
    user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """Add notes to upload batch"""

    result = supabase.table("upload_batches")\
        .update({"notes": notes})\
        .eq("batch_id", str(batch_id))\
        .eq("user_id", user["id"])\
        .execute()

    return {"success": True}

-- 5. Test
curl -X PATCH "http://localhost:8000/api/uploads/batches/{uuid}/notes" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Corrected Liberty data for September"}'
```

### Workflow 3: Add Celery Background Task

**Example**: Send weekly report emails

```python
# 1. Define task (backend/app/workers/tasks.py)
from app.workers.celery_app import celery
from app.services.email.email_service import EmailService

@celery.task(name="send_weekly_report")
def send_weekly_report(user_id: str):
    """
    Send weekly sales report via email

    Runs every Monday at 9 AM
    """
    # Fetch user
    user = get_user_by_id(user_id)

    # Generate report
    report_data = generate_weekly_report(user_id)

    # Send email
    email_service = EmailService()
    email_service.send_template_email(
        to_email=user["email"],
        template_id="weekly_report",
        template_data={
            "user_name": user["full_name"],
            "total_sales": report_data["total_sales"],
            "top_products": report_data["top_products"],
            "week_start": report_data["week_start"],
            "week_end": report_data["week_end"]
        }
    )

    return {"status": "sent", "user_id": user_id}

# 2. Schedule task (backend/app/workers/celery_app.py)
from celery.schedules import crontab

celery.conf.beat_schedule = {
    "weekly-report-mondays": {
        "task": "send_weekly_report",
        "schedule": crontab(day_of_week="monday", hour=9, minute=0),
        "args": []  # Will run for all active users
    }
}

# 3. Start Celery beat scheduler (in addition to worker)
celery -A app.workers.celery_app beat --loglevel=info

# 4. Trigger manually for testing
from app.workers.tasks import send_weekly_report
task = send_weekly_report.delay(user_id="uuid-...")
print(f"Task ID: {task.id}")
print(f"Task status: {task.status}")
```

---

## Adding a New Vendor Processor

### Step-by-Step Guide

**Scenario**: Add processor for "Harrods" vendor

#### Step 1: Create Processor File

```python
# backend/app/services/bibbi/processors/harrods_processor.py

from typing import List, Dict, Any, Optional
from app.services.bibbi.processors.base import BibbiBseProcessor

class HarrodsProcessor(BibbiBseProcessor):
    """
    Harrods vendor data processor

    File Format:
    - Excel (.xlsx)
    - Columns: Product Code, Description, Quantity Sold, Unit Price, Month, Year
    - Single store (Harrods London)
    - Currency: GBP
    - Monthly aggregated data
    """

    def get_vendor_name(self) -> str:
        return "harrods"

    def get_currency(self) -> str:
        return "GBP"

    def extract_rows(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract rows from Harrods Excel file"""

        # Load workbook
        workbook = self._load_workbook(file_path, data_only=True)
        sheet = workbook.active

        # Get headers
        headers = self._get_sheet_headers(sheet, header_row=1)

        # Validate required columns
        required = ["Product Code", "Description", "Quantity Sold", "Unit Price", "Month", "Year"]
        self._validate_required_headers(sheet, required)

        # Extract rows (starting from row 2)
        rows = []
        for row_idx, row_cells in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            # Skip empty rows
            if all(cell is None for cell in row_cells):
                continue

            # Create dictionary
            row_dict = {headers[i]: row_cells[i] for i in range(len(headers))}
            rows.append(row_dict)

        workbook.close()
        return rows

    def extract_stores(self, file_path: str) -> List[Dict[str, Any]]:
        """Harrods is a single store"""

        return [{
            "store_identifier": "HAR-LON",
            "store_name": "Harrods London",
            "store_type": "physical",
            "reseller_id": self.reseller_id
        }]

    def transform_row(self, raw_row: Dict[str, Any], batch_id: str) -> Optional[Dict[str, Any]]:
        """Transform Harrods row to unified schema"""

        # Create base row
        base = self._create_base_row(batch_id)

        # Map Harrods fields to unified schema
        try:
            # Product identification
            # Note: Harrods uses product codes, need to map to EANs
            product_code = raw_row.get("Product Code")
            base["product_ean"] = self._map_product_code_to_ean(product_code)

            # Product name
            base["functional_name"] = self._to_string(raw_row.get("Description"))

            # Quantities and pricing
            base["quantity"] = self._to_int(raw_row.get("Quantity Sold"), "Quantity Sold")
            base["unit_price"] = self._to_float(raw_row.get("Unit Price"), "Unit Price")

            # Convert GBP to EUR
            base["unit_price"] = self._convert_currency(base["unit_price"], "GBP")

            # Dates
            base["sale_month"] = self._validate_month(raw_row.get("Month"))
            base["sale_year"] = self._validate_year(raw_row.get("Year"))
            base["quarter"] = self._calculate_quarter(base["sale_month"])

            # Store (Harrods is always same store)
            base["store_identifier"] = "HAR-LON"
            base["store_name"] = "Harrods London"

            return base

        except Exception as e:
            # Log error with row context
            print(f"Error transforming row: {raw_row}")
            print(f"Error: {str(e)}")
            raise

    def _map_product_code_to_ean(self, product_code: str) -> str:
        """
        Map Harrods product code to EAN

        Harrods uses internal codes like "HAR-BIBBI-001"
        Need to lookup in products table or mapping file
        """

        # Query Supabase for product mapping
        result = self.supabase.table("products")\
            .select("ean")\
            .eq("product_code", product_code)\
            .eq("user_id", self.user_id)\
            .execute()

        if result.data:
            return result.data[0]["ean"]

        # Fallback: raise error if not found
        raise ValueError(f"Product code not found in catalog: {product_code}")
```

#### Step 2: Add Vendor Detection Patterns

```python
# backend/app/services/vendors/detector.py

VENDOR_PATTERNS = {
    # ... existing vendors

    "harrods": {
        "required_columns": ["Product Code", "Description", "Quantity Sold", "Unit Price"],
        "unique_patterns": ["Harrods", "HAR-"],
        "file_name_patterns": ["harrods", "HAR"]
    }
}
```

#### Step 3: Register Processor

```python
# backend/app/services/bibbi/vendor_router.py

from app.services.bibbi.processors.harrods_processor import HarrodsProcessor

PROCESSOR_MAP = {
    # ... existing processors
    "harrods": HarrodsProcessor
}
```

#### Step 4: Add Vendor Configuration

```sql
-- backend/db/seed_vendor_configs.sql

INSERT INTO vendor_configs (vendor_name, config) VALUES
('harrods', '{
    "expected_columns": ["Product Code", "Description", "Quantity Sold", "Unit Price", "Month", "Year"],
    "currency": "GBP",
    "data_type": "monthly_aggregate",
    "requires_product_mapping": true
}'::jsonb);
```

#### Step 5: Test with Sample File

```python
# Create test file (tests/fixtures/harrods_sample.xlsx)
# Then test processor:

import pytest
from app.services.bibbi.processors.harrods_processor import HarrodsProcessor

def test_harrods_processor():
    processor = HarrodsProcessor(reseller_id="test-reseller")

    result = processor.process(
        file_path="tests/fixtures/harrods_sample.xlsx",
        batch_id="test-batch-123"
    )

    assert result.total_rows > 0
    assert result.successful_rows > 0
    assert result.vendor == "harrods"

    # Verify data transformation
    first_row = result.transformed_data[0]
    assert "product_ean" in first_row
    assert "quantity" in first_row
    assert first_row["vendor_name"] == "harrods"
```

---

## Debugging Guide

### Backend Debugging

#### FastAPI Request Debugging

```python
# Add debug logging to endpoint
import logging
logger = logging.getLogger(__name__)

@router.post("/uploads")
async def upload_file(file: UploadFile, user: dict = Depends(get_current_user)):
    logger.info(f"Upload request from user: {user['id']}")
    logger.info(f"File: {file.filename}, size: {file.size}")

    try:
        # ... process file
        pass
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise

# View logs
docker-compose logs -f backend_api
```

#### Celery Task Debugging

```python
# Enable detailed task logging
@celery.task(bind=True)
def process_upload(self, file_path: str, user_id: str):
    # Log task start
    print(f"[TASK {self.request.id}] Started processing: {file_path}")

    try:
        # Update progress
        self.update_state(state="PROCESSING", meta={"progress": 10})

        # ... processing logic

        print(f"[TASK {self.request.id}] Completed successfully")

    except Exception as e:
        print(f"[TASK {self.request.id}] Error: {str(e)}")
        raise

# Monitor Celery worker logs
docker-compose logs -f backend_worker

# Check task status
from celery.result import AsyncResult
task = AsyncResult(task_id)
print(f"Status: {task.status}")
print(f"Result: {task.result}")
```

#### Database Query Debugging

```python
# Enable SQL query logging
import logging
logging.getLogger("supabase").setLevel(logging.DEBUG)

# Or add manual logging
result = supabase.table("ecommerce_orders").select("*").eq("user_id", user_id).execute()
print(f"Query returned {len(result.data)} rows")
print(f"First row: {result.data[0] if result.data else 'None'}")
```

### Frontend Debugging

#### API Call Debugging

```typescript
// Enable request/response logging
// In lib/api.ts

apiClient.interceptors.request.use(
  config => {
    console.log('[API Request]', config.method?.toUpperCase(), config.url);
    console.log('[API Headers]', config.headers);
    return config;
  },
  error => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  response => {
    console.log('[API Response]', response.status, response.config.url);
    console.log('[API Data]', response.data);
    return response;
  },
  error => {
    console.error('[API Response Error]', error.response?.status, error.config?.url);
    console.error('[API Error Data]', error.response?.data);
    return Promise.reject(error);
  }
);
```

#### React State Debugging

```typescript
// Use React DevTools browser extension
// Or add console logs in components

function UploadPage() {
  const [file, setFile] = useState<File | null>(null);

  // Debug state changes
  useEffect(() => {
    console.log('[UploadPage] File state changed:', file);
  }, [file]);

  // ...
}
```

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| 401 Unauthorized | API calls failing | Check JWT token in localStorage, verify not expired |
| Celery task stuck | Task shows "PENDING" forever | Check Redis connection, restart Celery worker |
| CORS error | Frontend can't reach backend | Verify CORS settings in `app/main.py`, check VITE_API_URL |
| RLS blocking queries | No data returned despite existing records | Verify `user_id` filter in query, check RLS policies |
| Upload processing slow | Files take >5 minutes | Check Celery worker is running, verify Redis connection |

---

## Testing Strategy

### Backend Testing

#### Unit Tests

```python
# tests/unit/test_harrods_processor.py

import pytest
from app.services.bibbi.processors.harrods_processor import HarrodsProcessor

class TestHarrodsProcessor:
    @pytest.fixture
    def processor(self):
        return HarrodsProcessor(reseller_id="test-reseller")

    def test_transform_row_valid_data(self, processor):
        """Test transforming valid Harrods row"""

        raw_row = {
            "Product Code": "HAR-BIBBI-001",
            "Description": "Midnight Rose EDP 50ml",
            "Quantity Sold": 10,
            "Unit Price": 45.00,
            "Month": 9,
            "Year": 2024
        }

        result = processor.transform_row(raw_row, "batch-123")

        assert result["product_ean"] == "1234567890123"
        assert result["functional_name"] == "Midnight Rose EDP 50ml"
        assert result["quantity"] == 10
        assert result["unit_price"] == 52.65  # Converted from GBP to EUR
        assert result["sale_month"] == 9
        assert result["sale_year"] == 2024
        assert result["quarter"] == 3

    def test_transform_row_invalid_month(self, processor):
        """Test error handling for invalid month"""

        raw_row = {
            "Product Code": "HAR-BIBBI-001",
            "Description": "Product",
            "Quantity Sold": 10,
            "Unit Price": 45.00,
            "Month": 13,  # INVALID
            "Year": 2024
        }

        with pytest.raises(ValueError, match="Invalid month"):
            processor.transform_row(raw_row, "batch-123")
```

#### Integration Tests

```python
# tests/integration/test_upload_flow.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_upload_flow():
    """Test complete file upload workflow"""

    # 1. Login to get token
    login_response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 2. Upload file
    with open("tests/fixtures/harrods_sample.xlsx", "rb") as f:
        upload_response = client.post(
            "/api/uploads",
            files={"file": ("harrods.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert upload_response.status_code == 202  # Accepted
    task_id = upload_response.json()["task_id"]

    # 3. Check upload status
    status_response = client.get(
        f"/api/uploads/batches/{task_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert status_response.status_code == 200
    # Task might still be processing, so status could be "processing" or "completed"
```

### Frontend Testing

```typescript
// tests/components/UploadPage.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { UploadPage } from '@/pages/Uploads';

describe('UploadPage', () => {
  it('renders file upload form', () => {
    render(<UploadPage />);

    expect(screen.getByText('Upload Sales Data')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
  });

  it('shows error for invalid file type', async () => {
    render(<UploadPage />);

    const file = new File(['content'], 'data.txt', { type: 'text/plain' });
    const input = screen.getByLabelText(/choose file/i);

    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText(/invalid file type/i)).toBeInTheDocument();
  });
});
```

---

## Code Patterns and Conventions

### Backend Patterns

#### Always Filter by user_id

```python
# ❌ WRONG - Leaks data from all users
result = supabase.table("ecommerce_orders").select("*").execute()

# ✅ CORRECT
result = supabase.table("ecommerce_orders")\
    .select("*")\
    .eq("user_id", user["id"])\
    .execute()
```

#### Use Dependency Injection

```python
# Prefer
@router.get("/data")
async def get_data(user: dict = Depends(get_current_user)):
    # user is auto-injected, JWT validated
    pass

# Over
@router.get("/data")
async def get_data(authorization: str = Header(...)):
    # Manual JWT parsing - error-prone
    token = authorization.split(" ")[1]
    # ...
```

#### Error Handling

```python
from fastapi import HTTPException

@router.get("/resource/{id}")
async def get_resource(id: str):
    result = supabase.table("resources").select("*").eq("id", id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Resource not found")

    return result.data[0]
```

### Frontend Patterns

#### API Calls in Hooks

```typescript
// Prefer
function useUploadStats() {
  const [stats, setStats] = useState<UploadStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    getUploadStats()
      .then(setStats)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { stats, loading, error };
}

// Use in component
function StatsDisplay() {
  const { stats, loading, error } = useUploadStats();

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <Stats data={stats} />;
}
```

#### State Management

```typescript
// For global state (auth, tenant), use Zustand store
import { useAuthStore } from '@/stores/auth';

function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header>
      <span>{user?.email}</span>
      <button onClick={logout}>Logout</button>
    </header>
  );
}

// For component-local state, use useState
function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  // ...
}
```

---

## Git Workflow

### Branch Strategy

```bash
# Feature branches
git checkout -b feature/add-harrods-processor
git checkout -b fix/liberty-ean-validation
git checkout -b refactor/simplify-detector

# Never commit directly to main/master
# Always use feature branches + PR
```

### Commit Message Format

```bash
# Format: type(scope): description

# Types: feat, fix, refactor, test, docs, chore

# Examples:
git commit -m "feat(processors): add Harrods vendor processor"
git commit -m "fix(liberty): prevent wrong EAN generation"
git commit -m "refactor(utils): extract shared validation functions"
git commit -m "test(harrods): add unit tests for processor"
git commit -m "docs(readme): update setup instructions"
```

### Pull Request Workflow

```bash
# 1. Create feature branch
git checkout -b feature/harrods-processor

# 2. Make changes, commit frequently
git add .
git commit -m "feat(processors): add Harrods processor base"

# 3. Push to remote
git push origin feature/harrods-processor

# 4. Create Pull Request on GitHub
# - Describe changes
# - Link to related issues
# - Request review

# 5. Address review feedback
git add .
git commit -m "fix(harrods): address code review feedback"
git push origin feature/harrods-processor

# 6. Merge when approved
# Use "Squash and merge" for clean history
```

---

## Related Documentation

- [Platform Guide](./PLATFORM_GUIDE.md) - What the app does and how it works
- [Adding Vendor Processors](./adding_vendor_processors.md) - Detailed processor guide
- [API Reference](../docs/api/README.md) - Complete API documentation
- [Architecture Overview](../docs/architecture/SYSTEM_OVERVIEW.md) - Technical architecture

---

**Questions?** Check [FAQ](./FAQ.md) or open an issue on GitHub.

**Last Updated**: 2025-10-25
