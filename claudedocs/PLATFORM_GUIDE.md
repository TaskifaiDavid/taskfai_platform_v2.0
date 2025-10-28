# TaskifAI Platform - Complete Guide

**What It Does, How It Works, and Why It Matters**

**Last Updated**: 2025-10-25
**Version**: 2.0
**Status**: Production (BIBBI Tenant Active)

---

## Table of Contents

1. [What is TaskifAI?](#what-is-taskifai)
2. [Who Uses TaskifAI?](#who-uses-taskifai)
3. [How It Works - User Perspective](#how-it-works---user-perspective)
4. [How It Works - Technical Perspective](#how-it-works---technical-perspective)
5. [Key Features Deep Dive](#key-features-deep-dive)
6. [Multi-Tenant Architecture](#multi-tenant-architecture)
7. [Recent Platform Improvements](#recent-platform-improvements)
8. [Getting Started](#getting-started)

---

## What is TaskifAI?

### The Problem

Fashion and beauty brands sell through complex multi-channel networks:
- **Direct-to-Consumer (D2C)**: Own e-commerce websites
- **Business-to-Business (B2B)**: Reseller partners (department stores, specialty retailers, online marketplaces)

Each channel provides sales data in different formats:
- Liberty sends Excel files with specific column layouts
- Galilu provides CSV exports with different field names
- Selfridges has unique data structures
- Online platforms use JSON exports

**Analysts spend 60-80% of their time** manually cleaning, normalizing, and consolidating this data before they can even begin analysis. This is:
- Time-consuming and error-prone
- Prevents real-time decision making
- Makes comparative analysis difficult
- Requires technical Excel skills

### The Solution

**TaskifAI is a multi-tenant SaaS platform that automatically:**

1. **Ingests** sales data from multiple vendor formats (9+ supported)
2. **Detects** the vendor automatically from file structure
3. **Cleans** and normalizes data into a unified schema
4. **Stores** data with user-level security isolation
5. **Analyzes** data with AI-powered natural language queries
6. **Visualizes** insights through customizable dashboards

**Result**: Analysts go from data receipt to insights in **minutes instead of hours**.

### Core Value Proposition

| Before TaskifAI | With TaskifAI |
|-----------------|---------------|
| 4-8 hours manual data cleaning | 30 seconds automated processing |
| Excel formulas and pivot tables | Natural language AI chat: "Show me Liberty sales trends" |
| Separate files per vendor | Unified multi-channel analytics |
| Manual error checking | Automated validation and error reporting |
| Static monthly reports | Real-time dashboards with drill-down |
| Technical barrier to insights | Self-service analytics for all roles |

---

## Who Uses TaskifAI?

### Primary User Persona: Sales Analyst

**Meet Emma** - Sales Analyst at BIBBI Parfum
- Receives monthly sales files from 8+ reseller partners
- Needs to report on regional performance, product trends, channel comparison
- Non-technical background (marketing degree)
- Frustrated with Excel limitations

**Emma's Workflow with TaskifAI**:
1. **Monday Morning**: Receives Liberty sales file via email
2. **Upload** (30 seconds): Drags file to TaskifAI upload interface
3. **Automated Processing**: TaskifAI detects it's Liberty, extracts multi-store data, validates EANs, normalizes formats
4. **Chat Analysis**: "Which Liberty stores had highest sales growth this month?"
5. **Dashboard Update**: Real-time dashboard automatically includes new Liberty data
6. **Report Generation**: Exports polished PDF for management review

**Time Saved**: 6 hours per week

### Secondary Personas

**Brand Manager** - Strategic Decision Maker
- Uses dashboards to monitor brand health across channels
- Asks AI chat: "Compare online vs offline sales for our premium line"
- Needs high-level insights, not raw data

**Operations Director** - Data Quality Overseer
- Reviews upload error reports
- Monitors data freshness (when was last update?)
- Ensures analysts have tools they need

**Future Personas** (Platform Designed For):
- Multi-brand corporations (manage multiple sub-brands)
- Retail chains (aggregate store-level data)
- Consultants (multi-client analytics)

---

## How It Works - User Perspective

### The Complete User Journey

#### Phase 1: Access & Authentication

```
User visits: bibbi.taskifai.com
     ↓
Login with email + password
     ↓
Optional: Two-factor authentication (TOTP)
     ↓
JWT token issued (valid 24 hours)
     ↓
Redirected to personalized dashboard
```

**Multi-Tenant Login**: Users with access to multiple tenants see a tenant selector. Single-tenant users go directly to their dashboard.

#### Phase 2: File Upload

**Step-by-Step**:

1. **Navigate to Upload Page**
   - Click "Upload Data" in sidebar
   - See upload history (past uploads, status, row counts)

2. **Select File**
   - Drag & drop OR click to browse
   - Supported formats: `.xlsx`, `.xls`, `.csv`
   - File size limit: 100MB

3. **Choose Upload Mode**
   - **Replace**: Clear existing data, insert new data
   - **Append**: Add new data to existing records
   - **Validate Only**: Check for errors without inserting

4. **Upload Processing** (Automatic Background Job)
   ```
   File Uploaded
        ↓
   Vendor Auto-Detection (98% accuracy)
        ↓
   Vendor-Specific Parser Loads
        ↓
   Excel → Rows → Data Dictionary
        ↓
   Validation (EANs, dates, quantities, prices)
        ↓
   Multi-Store Detection (Liberty, Selfridges, etc.)
        ↓
   Data Transformation (normalize to unified schema)
        ↓
   Database Insertion (batched for performance)
        ↓
   Email Notification (success/failure)
   ```

5. **Real-Time Status**
   - Progress bar shows: "Processing 1,234 of 5,678 rows"
   - Live error count: "3 rows failed validation"
   - Estimated time remaining

6. **Results**
   - **Success**: Green checkmark, row count, processing time
   - **Partial Success**: Yellow warning, valid rows inserted, error report available
   - **Failure**: Red error, detailed error log with row numbers and issues

#### Phase 3: Analytics & Insights

**Three Ways to Analyze**:

1. **Dashboard Widgets** (Visual Overview)
   - KPI Cards: Total sales, YoY growth, average order value
   - Sales Trends Chart: Time series with drill-down
   - Channel Breakdown: Pie chart (online vs offline)
   - Top Products Table: Sortable, filterable
   - Geographic Heatmap: Sales by region

2. **AI Chat Assistant** (Natural Language)
   ```
   User: "What were our top 5 selling products last quarter?"

   TaskifAI:
   - Analyzes intent
   - Generates SQL: SELECT product_name, SUM(quantity) ...
   - Executes query (with user_id filter for security)
   - Formats results in natural language

   Response: "Based on Q3 2024 data, your top 5 products were:
   1. Midnight Rose EDP (4,234 units)
   2. Citrus Bloom EDT (3,891 units)
   3. Ocean Breeze Travel Set (3,102 units)
   4. Vanilla Dream Body Lotion (2,876 units)
   5. Lavender Night Cream (2,543 units)

   Total units sold: 16,646 across all 5 products."
   ```

   **Follow-Up Questions**:
   ```
   User: "Show me Liberty-specific sales for Midnight Rose"
   User: "Compare online vs offline for that product"
   User: "What's the trend over the last 6 months?"
   ```

3. **Advanced Analytics** (Export & Reports)
   - Export to Excel: Full data dump with filters applied
   - Export to PDF: Formatted report with charts
   - Scheduled Reports: Daily/weekly email summaries (future)

#### Phase 4: Dashboard Customization

**Create Custom Dashboard**:
1. Click "Create Dashboard"
2. Name it (e.g., "Liberty Performance Dashboard")
3. Add widgets:
   - KPI: Liberty Total Sales
   - Chart: Liberty Sales by Store
   - Table: Top Products at Liberty
4. Arrange layout with drag-and-drop
5. Set as primary dashboard (loads on login)

**Embed External Dashboards**:
- Looker, Tableau, Power BI, Metabase
- Secure iframe embedding with encrypted credentials
- Seamless user experience (no separate login)

---

## How It Works - Technical Perspective

### Architecture Overview

TaskifAI follows a **modern, scalable SaaS architecture**:

```
┌──────────────────────────────────────────────────┐
│           FRONTEND (Client-Side)                 │
│  React 19 + TypeScript + Tailwind CSS v4        │
│  - Vite 6 (fast builds, HMR)                    │
│  - Zustand (state management)                    │
│  - Axios (API client with interceptors)         │
└─────────────┬────────────────────────────────────┘
              │ HTTPS/REST
┌─────────────▼────────────────────────────────────┐
│           BACKEND (API Layer)                    │
│  FastAPI + Python 3.11 + Pydantic v2            │
│  - JWT authentication                            │
│  - Rate limiting (10 req/min per IP)            │
│  - Multi-tenant routing (subdomain extraction)  │
│  - RESTful endpoints (73 routes)                │
└──┬───────────┬───────────────┬───────────────────┘
   │           │               │
   │ Services  │ Task Queue    │ Database
   │           │               │
   ▼           ▼               ▼
┌──────┐  ┌─────────┐  ┌──────────────┐
│Vendor│  │ Celery  │  │  Supabase    │
│ Auto-│  │ Worker  │  │ PostgreSQL17 │
│Detect│  │         │  │ + RLS        │
│      │  │ Redis   │  │              │
│AI    │  │ Broker  │  │ Row-Level    │
│Agent │  │         │  │ Security     │
└──────┘  └─────────┘  └──────────────┘
```

### System Components Explained

#### 1. Frontend Application

**Technology**: React 19 SPA (Single-Page Application)

**Why React 19?**
- Automatic batching (performance optimization)
- Concurrent rendering (smooth UX during heavy operations)
- Latest ecosystem compatibility

**Key Frontend Patterns**:

```typescript
// Centralized API Client (lib/api.ts)
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Auto-inject JWT token in all requests
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-extract tenant from subdomain
const hostname = window.location.hostname;
const subdomain = hostname.split('.')[0];
config.headers['X-Tenant-Subdomain'] = subdomain;
```

**State Management** (Zustand):
```typescript
// stores/auth.ts
const useAuthStore = create((set) => ({
  user: null,
  token: null,
  login: (user, token) => set({ user, token }),
  logout: () => set({ user: null, token: null })
}));
```

**Routing** (React Router v6):
```typescript
<Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
<Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
<Route path="/chat" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
<Route path="/login" element={<Login />} />
```

#### 2. Backend API (FastAPI)

**Technology**: FastAPI + Python 3.11

**Why FastAPI?**
- Native async support (handle concurrent uploads)
- Automatic OpenAPI docs (Swagger UI)
- Pydantic v2 integration (data validation)
- High performance (comparable to Node.js/Go)

**Middleware Stack** (Execution Order):

```python
# 1. FIRST: Tenant Context (extract subdomain)
app.add_middleware(TenantContextMiddleware)
# Runs first, sets request.state.tenant

# 2. SECOND: Authentication (validate JWT)
app.add_middleware(AuthMiddleware)
# Checks token, sets request.state.user

# 3. LAST: Logging (record request/response)
app.add_middleware(LoggingMiddleware)
# Logs after auth succeeds
```

**API Route Pattern**:
```python
# api/uploads.py
@router.post("/uploads")
async def upload_file(
    file: UploadFile,
    user: dict = Depends(get_current_user),  # Auto-injected
    tenant: dict = Depends(get_tenant_context)  # Auto-injected
):
    # Save file to /tmp
    file_path = save_upload(file)

    # Enqueue background task (async processing)
    task = process_upload.delay(file_path, user["id"], tenant["id"])

    return {"task_id": task.id, "status": "processing"}
```

#### 3. Vendor Processor System

**The Core Innovation**: Automatic vendor detection and format normalization

**How Vendor Auto-Detection Works**:

```python
# services/vendors/detector.py
VENDOR_PATTERNS = {
    "liberty": {
        "required_columns": ["Article", "Barcode", "Store Name"],
        "unique_patterns": ["Liberty London", "LIB-"],
        "file_name_patterns": ["liberty", "LBY"]
    },
    "galilu": {
        "required_columns": ["EAN", "Product Name", "Quantity"],
        "unique_patterns": ["GALILU", "GAL-"],
        "file_name_patterns": ["galilu", "GAL"]
    },
    # ... 9+ vendor patterns
}

def detect_vendor(file_path: str) -> str:
    """
    Auto-detect vendor from file structure

    Detection Strategy:
    1. Check filename patterns (fastest)
    2. Load first 10 rows of file
    3. Extract column headers
    4. Match against vendor patterns
    5. Return best match (98% accuracy)
    """
    # Load file
    df = pd.read_excel(file_path, nrows=10)
    columns = set(df.columns)

    # Score each vendor
    scores = {}
    for vendor_name, patterns in VENDOR_PATTERNS.items():
        score = 0

        # Required columns present? (+10 points each)
        for required_col in patterns["required_columns"]:
            if required_col in columns:
                score += 10

        # Unique patterns in data? (+5 points each)
        for pattern in patterns["unique_patterns"]:
            if df.astype(str).str.contains(pattern).any().any():
                score += 5

        scores[vendor_name] = score

    # Return highest scoring vendor
    return max(scores, key=scores.get)
```

**Vendor Processor Base Class** (Template Method Pattern):

```python
# services/bibbi/processors/base.py
class BibbiBseProcessor(ABC):
    """
    Template for all BIBBI vendor processors

    Why Template Pattern?
    - Enforces consistent processing flow
    - Vendor-specific logic isolated to transform_row()
    - Shared utilities reused (DRY principle)
    """

    def process(self, file_path: str, batch_id: str) -> ProcessingResult:
        # TEMPLATE METHOD (fixed flow)
        raw_rows = self.extract_rows(file_path)
        stores = self.extract_stores(file_path)  # Multi-store detection

        transformed_data = []
        errors = []

        for row in raw_rows:
            try:
                # HOOK METHOD (vendor-specific)
                transformed = self.transform_row(row, batch_id)
                transformed_data.append(transformed)
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        # Insert to database (batched)
        self.insert_batch(transformed_data)

        return ProcessingResult(
            total_rows=len(raw_rows),
            successful_rows=len(transformed_data),
            failed_rows=len(errors),
            transformed_data=transformed_data,
            errors=errors
        )

    # Abstract methods (must be implemented by vendor processors)
    @abstractmethod
    def transform_row(self, raw_row: dict, batch_id: str) -> dict:
        """Convert vendor row to unified schema"""
        pass

    @abstractmethod
    def extract_stores(self, file_path: str) -> List[dict]:
        """Extract store information (for multi-store vendors)"""
        pass
```

**Example: Liberty Processor** (Concrete Implementation):

```python
# services/bibbi/processors/liberty_processor.py
class LibertyProcessor(BibbiBseProcessor):
    """
    Liberty sends files with multi-store data

    File Structure:
    | Store Name | Article | Barcode | Quantity | Price |
    |------------|---------|---------|----------|-------|
    | Liberty London | BIBBI-001 | 1234567890123 | 10 | 45.00 |
    | Liberty Birmingham | BIBBI-002 | 9876543210987 | 5 | 45.00 |

    Challenges:
    - Multiple stores in one file
    - Inconsistent store naming ("Liberty London" vs "London")
    - Some products have multiple barcodes (EANs)
    - Currency is GBP (needs conversion to EUR)
    """

    def get_vendor_name(self) -> str:
        return "liberty"

    def get_currency(self) -> str:
        return "GBP"

    def extract_stores(self, file_path: str) -> List[dict]:
        """
        Extract unique stores from Liberty file

        Returns:
            [
                {"store_identifier": "LIB-LON", "store_name": "Liberty London"},
                {"store_identifier": "LIB-BIR", "store_name": "Liberty Birmingham"}
            ]
        """
        df = pd.read_excel(file_path)
        unique_stores = df["Store Name"].unique()

        stores = []
        for store_name in unique_stores:
            # Normalize store name
            identifier = self._generate_store_identifier(store_name)
            stores.append({
                "store_identifier": identifier,
                "store_name": store_name.strip(),
                "store_type": "physical",
                "reseller_id": self.reseller_id
            })

        return stores

    def transform_row(self, raw_row: dict, batch_id: str) -> dict:
        """
        Transform Liberty row to unified schema

        Input (Liberty format):
            {"Store Name": "Liberty London", "Barcode": "1234567890123", ...}

        Output (Unified schema):
            {"product_ean": "1234567890123", "store_id": "...", ...}
        """
        # Create base row (common fields)
        base = self._create_base_row(batch_id)

        # Validate and transform fields
        base["product_ean"] = self._validate_ean(raw_row.get("Barcode"), required=True)
        base["quantity"] = self._to_int(raw_row.get("Quantity"), "Quantity")
        base["unit_price"] = self._to_float(raw_row.get("Price"), "Price")

        # Convert GBP → EUR
        base["unit_price"] = self._convert_currency(base["unit_price"], "GBP")

        # Store association
        store_name = raw_row.get("Store Name")
        base["store_id"] = self._get_store_id(store_name)

        # Dates
        base["sale_month"] = self._validate_month(raw_row.get("Month"))
        base["sale_year"] = self._validate_year(raw_row.get("Year"))
        base["quarter"] = self._calculate_quarter(base["sale_month"])

        return base
```

**Shared Utilities** (DRY Refactoring Result):

```python
# utils/validation.py
def validate_ean(value: Any, required: bool = True, strict: bool = True) -> Optional[str]:
    """
    Validate EAN-13 barcode

    Handles Excel artifacts:
    - "1234567890123.0" → "1234567890123"  (float conversion)
    - 1234567890123 (int) → "1234567890123" (string conversion)
    - "  1234567890123  " → "1234567890123" (whitespace trim)

    Args:
        value: EAN value (str, int, or float)
        required: Raise error if None/empty
        strict: Raise error if invalid (vs return None)

    Returns:
        Validated 13-digit EAN string or None

    Raises:
        ValueError: If required=True and empty, or strict=True and invalid
    """
    if not value:
        if required:
            raise ValueError("EAN cannot be empty")
        return None

    # Convert to string and remove decimals
    ean_str = str(value).strip()
    if '.' in ean_str:
        ean_str = ean_str.split('.')[0]

    # Validate length and digits
    if len(ean_str) != 13 or not ean_str.isdigit():
        if strict:
            raise ValueError(f"Invalid EAN format: {ean_str}")
        return None

    return ean_str
```

#### 4. Background Worker System (Celery)

**Why Async Processing?**
- File uploads can take 30+ seconds for large files
- Don't block user's browser while processing
- Enable concurrent uploads (up to 24 files simultaneously)

**Celery Configuration**:
```python
# workers/celery_app.py
celery = Celery(
    "taskifai_worker",
    broker="redis://localhost:6379/0",  # Task queue
    backend="redis://localhost:6379/1"  # Result storage
)

celery.conf.update(
    task_queues={
        "file_processing": Queue("file_processing", routing_key="file.#"),
        "notifications": Queue("notifications", routing_key="notify.#")
    },
    worker_prefetch_multiplier=4,  # 4 tasks per worker
    task_time_limit=1800,  # 30 minute timeout
    task_soft_time_limit=1500  # Warning at 25 minutes
)
```

**Task Definition**:
```python
# workers/tasks.py
@celery.task(bind=True, name="process_upload")
def process_upload(self, file_path: str, user_id: str, batch_id: str):
    """
    Background task for file processing

    Workflow:
    1. Detect vendor
    2. Load appropriate processor
    3. Process file
    4. Insert to database
    5. Send email notification
    6. Clean up temp file
    """
    try:
        # Update task progress
        self.update_state(state="PROCESSING", meta={"progress": 0})

        # Detect vendor
        vendor = detect_vendor(file_path)
        self.update_state(state="PROCESSING", meta={"progress": 10, "vendor": vendor})

        # Load processor
        processor = get_processor(vendor, reseller_id=...)

        # Process file (progress updates via callback)
        result = processor.process(
            file_path,
            batch_id,
            progress_callback=lambda p: self.update_state(
                state="PROCESSING",
                meta={"progress": 10 + int(p * 80)}
            )
        )

        # Send email
        send_upload_notification.delay(user_id, result)
        self.update_state(state="PROCESSING", meta={"progress": 95})

        # Cleanup
        os.remove(file_path)

        return {
            "status": "success",
            "total_rows": result.total_rows,
            "successful_rows": result.successful_rows,
            "failed_rows": result.failed_rows
        }

    except Exception as e:
        # Email error notification
        send_error_notification.delay(user_id, str(e))
        raise
```

#### 5. AI Chat System (LangChain + OpenAI)

**Architecture**: Hybrid approach (AI generates SQL → Backend executes)

**Why Not Direct Database Access for AI?**
- Security: AI could potentially read other users' data
- Cost: Direct DB access charges more tokens
- Control: We validate and filter all queries

**LangChain Agent Flow**:

```python
# services/ai_chat/agent.py
class TaskifAIChatAgent:
    """
    AI Chat Agent for natural language analytics

    Architecture:
    1. User question → Intent detection
    2. Generate SQL query (GPT-4o-mini)
    3. Validate security (no INSERT/UPDATE/DELETE)
    4. Inject user_id filter (WHERE user_id = '...')
    5. Execute via Supabase
    6. Format results in natural language
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Database schema context (for SQL generation)
        self.schema_context = """
        You have access to these tables:

        1. ecommerce_orders (PRIMARY - D2C/online sales):
           - order_id, product_ean, functional_name, quantity, unit_price
           - sale_date, sale_month, sale_year, quarter
           - sales_channel, country, user_id

        2. sellout_entries2 (B2B/offline sales):
           - product_ean, quantity, unit_price, month, year
           - reseller_name, store_name, user_id
           - REQUIRES JOIN to products table for product names

        IMPORTANT RULES:
        - ALWAYS query ecommerce_orders FIRST (has functional_name directly)
        - ONLY use sellout_entries2 if user specifically asks for "reseller" or "B2B" data
        - ALL queries MUST filter by user_id (security requirement)
        - Use functional_name for product names (NOT product_name)
        """

    async def query(self, user_question: str) -> dict:
        """Process user question and return answer"""

        # Step 1: Detect intent
        intent = self._detect_intent(user_question)

        # Step 2: Generate SQL
        sql_query = self._generate_sql(user_question, intent)

        # Step 3: Validate security
        self._validate_sql_security(sql_query)

        # Step 4: Inject user filter
        sql_query = self._inject_user_filter(sql_query)

        # Step 5: Execute query
        results = self._execute_query(sql_query)

        # Step 6: Generate natural language response
        response = self._format_response(user_question, results)

        return {
            "question": user_question,
            "sql_query": sql_query,
            "results": results,
            "answer": response
        }

    def _generate_sql(self, question: str, intent: str) -> str:
        """Use LLM to generate SQL query"""

        prompt = f"""
        {self.schema_context}

        User question: "{question}"
        Detected intent: {intent}

        Generate a SQL query to answer this question.

        Requirements:
        - Return ONLY the SQL query, no explanations
        - Use proper SQL syntax for PostgreSQL 17
        - Include column aliases for clarity
        - Limit results to 100 rows (add LIMIT 100)
        - DO NOT include WHERE user_id filter (will be injected)
        """

        response = self.llm.invoke(prompt)
        return response.content.strip()

    def _inject_user_filter(self, sql: str) -> str:
        """
        Inject user_id filter for security

        Before: SELECT * FROM ecommerce_orders
        After:  SELECT * FROM ecommerce_orders WHERE user_id = 'uuid-...'
        """
        # Find main table
        table_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if not table_match:
            raise ValueError("Could not identify main table in query")

        # Add WHERE clause
        if 'WHERE' in sql.upper():
            sql = sql.replace('WHERE', f"WHERE user_id = '{self.user_id}' AND", 1)
        else:
            # Insert before ORDER BY, GROUP BY, or LIMIT
            insert_pos = len(sql)
            for keyword in ['ORDER BY', 'GROUP BY', 'LIMIT']:
                pos = sql.upper().find(keyword)
                if pos != -1:
                    insert_pos = min(insert_pos, pos)

            sql = sql[:insert_pos] + f" WHERE user_id = '{self.user_id}' " + sql[insert_pos:]

        return sql
```

**Security Validation**:
```python
# services/ai_chat/security.py
def validate_sql_security(sql: str) -> None:
    """
    Validate SQL query for security

    BLOCK:
    - INSERT, UPDATE, DELETE, DROP, TRUNCATE
    - ; (multiple statements)
    - -- (comments that could hide malicious code)

    ALLOW:
    - SELECT only
    - JOINs
    - WHERE, GROUP BY, ORDER BY
    """
    sql_upper = sql.upper()

    # Block dangerous operations
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE']
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            raise ValueError(f"Forbidden SQL operation: {keyword}")

    # Block multiple statements
    if ';' in sql:
        raise ValueError("Multiple SQL statements not allowed")

    # Block comments
    if '--' in sql or '/*' in sql:
        raise ValueError("SQL comments not allowed")
```

#### 6. Database Layer (Supabase + RLS)

**Technology**: Supabase (managed PostgreSQL 17 with Row-Level Security)

**Why Supabase?**
- Built-in Row-Level Security (RLS) - database-enforced data isolation
- Real-time subscriptions (future feature)
- Auto-generated REST API (not used, but available)
- Connection pooling (pgbouncer)
- Automatic backups

**Critical Security Pattern**:

```python
# Backend uses service_key which BYPASSES RLS
# Therefore, ALL queries MUST manually filter by user_id

# ❌ WRONG - Leaks data from all users
query = supabase.table("ecommerce_orders").select("*").execute()

# ✅ CORRECT - Filtered to current user only
query = supabase.table("ecommerce_orders")\
    .select("*")\
    .eq("user_id", user_id)\
    .execute()
```

**Database Schema** (Simplified):

```sql
-- Users (per tenant)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'analyst',
    tenant_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- D2C/Online Sales (PRIMARY TABLE)
CREATE TABLE ecommerce_orders (
    order_id UUID PRIMARY KEY,
    product_ean VARCHAR(13) NOT NULL,
    functional_name VARCHAR(255),  -- Product name (directly available!)
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    sale_date DATE NOT NULL,
    sale_month INTEGER NOT NULL,
    sale_year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    sales_channel VARCHAR(50),  -- 'online', 'marketplace', etc.
    country VARCHAR(100),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- B2B/Offline Sales
CREATE TABLE sellout_entries2 (
    id SERIAL PRIMARY KEY,
    product_ean VARCHAR(13) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    reseller_name VARCHAR(255),
    store_name VARCHAR(255),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products (catalog)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    ean VARCHAR(13) UNIQUE NOT NULL,
    functional_name VARCHAR(255),
    brand VARCHAR(255),
    category VARCHAR(255),
    size VARCHAR(50),
    user_id UUID NOT NULL REFERENCES users(id)
);

-- Upload Tracking
CREATE TABLE upload_batches (
    batch_id UUID PRIMARY KEY,
    vendor_name VARCHAR(100),
    file_name VARCHAR(255),
    upload_timestamp TIMESTAMP DEFAULT NOW(),
    processing_status VARCHAR(50),  -- 'pending', 'processing', 'completed', 'failed'
    total_rows INTEGER,
    successful_rows INTEGER,
    failed_rows INTEGER,
    user_id UUID NOT NULL REFERENCES users(id)
);

-- RLS Policies
ALTER TABLE ecommerce_orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own data" ON ecommerce_orders
    FOR SELECT USING (user_id = auth.uid());

ALTER TABLE sellout_entries2 ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own data" ON sellout_entries2
    FOR SELECT USING (user_id = auth.uid());
```

**Indexing Strategy**:
```sql
-- Performance indexes
CREATE INDEX idx_ecommerce_user_date ON ecommerce_orders(user_id, sale_date);
CREATE INDEX idx_ecommerce_user_product ON ecommerce_orders(user_id, product_ean);
CREATE INDEX idx_sellout_user_month ON sellout_entries2(user_id, year, month);

-- Full-text search indexes
CREATE INDEX idx_product_name ON ecommerce_orders USING gin(to_tsvector('english', functional_name));
```

---

## Key Features Deep Dive

### Feature 1: Multi-Vendor Data Ingestion

**The Challenge**: Each vendor has unique data formats

**Example Vendor Variations**:

| Vendor | Format | Key Characteristics |
|--------|--------|---------------------|
| Liberty | Excel (.xlsx) | Multi-store in one file, GBP currency, store name column |
| Galilu | CSV | Single store, EUR currency, product codes instead of EANs |
| Selfridges | Excel (.xls) | Multi-store, special product naming, quarterly reports |
| BoxNox | CSV | Monthly aggregates, no individual orders, custom date format |
| Skins SA | Excel (.xlsx) | Regional data, multiple currencies, complex product hierarchy |

**How TaskifAI Handles This**:

1. **Vendor Detection Algorithm**:
   ```python
   # Pattern matching across 3 dimensions
   def detect_vendor(file_path):
       score = 0

       # Dimension 1: Filename patterns (fast)
       if "liberty" in filename.lower():
           score["liberty"] += 20

       # Dimension 2: Column headers (medium)
       if "Store Name" in headers and "Barcode" in headers:
           score["liberty"] += 30

       # Dimension 3: Data patterns (slow, only if needed)
       if any("Liberty London" in row for row in first_10_rows):
           score["liberty"] += 50

       return max(score, key=score.get)
   ```

2. **Vendor-Specific Transformations**:
   - Liberty: Extract stores, convert GBP→EUR, normalize store names
   - Galilu: Map product codes to EANs via lookup table
   - Selfridges: Parse quarterly date formats, aggregate weekly data
   - BoxNox: Expand monthly aggregates to daily estimates
   - Skins SA: Flatten hierarchical product structure

3. **Unified Output Schema**:
   ```python
   {
       "product_ean": "1234567890123",
       "functional_name": "Midnight Rose EDP 50ml",
       "quantity": 10,
       "unit_price": 45.00,  # Always in EUR
       "sale_date": "2024-10-15",
       "sale_month": 10,
       "sale_year": 2024,
       "quarter": 4,
       "sales_channel": "offline",
       "reseller_name": "Liberty",
       "store_name": "Liberty London",
       "country": "United Kingdom",
       "user_id": "uuid-..."
   }
   ```

### Feature 2: AI-Powered Natural Language Chat

**The Magic**: Ask questions in plain English, get SQL-powered answers

**Behind the Scenes**:

1. **Intent Classification**:
   ```python
   INTENT_PATTERNS = {
       "sales_trends": ["trend", "over time", "growth", "month", "quarter"],
       "top_products": ["top", "best", "highest", "most popular"],
       "comparison": ["compare", "vs", "versus", "difference"],
       "aggregation": ["total", "sum", "average", "count"],
       "filter": ["for", "in", "at", "during", "where"]
   }
   ```

2. **SQL Generation** (LLM-powered):
   ```
   User: "What were Liberty sales last quarter?"

   LLM generates:
   SELECT
       functional_name,
       SUM(quantity) as total_units,
       SUM(quantity * unit_price) as total_revenue
   FROM ecommerce_orders
   WHERE
       reseller_name = 'Liberty'
       AND quarter = 3
       AND sale_year = 2024
   GROUP BY functional_name
   ORDER BY total_revenue DESC
   LIMIT 10
   ```

3. **Security Injection**:
   ```sql
   -- Before execution, system injects:
   WHERE user_id = 'current-user-uuid' AND ...
   ```

4. **Natural Language Response**:
   ```
   Based on Q3 2024 data for Liberty, here are your top products:

   1. Midnight Rose EDP - 1,234 units (€55,530)
   2. Citrus Bloom EDT - 891 units (€40,095)
   3. Ocean Breeze Travel Set - 567 units (€28,350)

   Total Liberty Q3 revenue: €123,975
   ```

**Advanced Features**:
- **Follow-up Context**: "What about Q2?" remembers we're talking about Liberty
- **Multi-turn Conversations**: Chat history maintained for context
- **Clarification Questions**: "Which quarter did you mean - Q3 2023 or Q3 2024?"

### Feature 3: Dashboard Configuration

**Dynamic Widgets**: Users customize their view

**Widget Types**:

1. **KPI Cards**:
   - Total Sales
   - YoY Growth %
   - Average Order Value
   - Units Sold
   - Custom calculations

2. **Charts**:
   - Line: Sales trends over time
   - Bar: Channel comparison
   - Pie: Product category breakdown
   - Area: Cumulative revenue

3. **Tables**:
   - Top Products (sortable)
   - Recent Orders
   - Store Performance
   - Custom queries

4. **External Embeds**:
   - Looker dashboards
   - Tableau reports
   - Power BI analytics
   - Metabase queries

**Configuration Storage**:
```json
{
  "dashboard_id": "uuid-...",
  "name": "Liberty Performance Dashboard",
  "layout": [
    {
      "widget_type": "kpi_card",
      "title": "Liberty Total Sales",
      "query": {
        "metric": "SUM(quantity * unit_price)",
        "table": "ecommerce_orders",
        "filters": {"reseller_name": "Liberty"}
      },
      "position": {"x": 0, "y": 0, "w": 3, "h": 2}
    },
    {
      "widget_type": "line_chart",
      "title": "Liberty Sales Trend (12 months)",
      "query": {
        "x_axis": "sale_month",
        "y_axis": "SUM(quantity * unit_price)",
        "group_by": "sale_month",
        "filters": {"reseller_name": "Liberty"},
        "date_range": "last_12_months"
      },
      "position": {"x": 3, "y": 0, "w": 9, "h": 4}
    }
  ]
}
```

### Feature 4: Email Notifications

**Automated Alerts**:

1. **Upload Success**:
   ```
   Subject: ✅ Upload Complete - Liberty Sales Data

   Your file "liberty_september_2024.xlsx" has been processed successfully.

   Summary:
   - Total rows: 1,234
   - Successfully imported: 1,230
   - Errors: 4

   [View Upload Details] [Go to Dashboard]
   ```

2. **Upload Failure**:
   ```
   Subject: ❌ Upload Failed - Action Required

   Your file "liberty_september_2024.xlsx" could not be processed.

   Error: Invalid EAN format in rows 45, 67, 89, 102

   [Download Error Report] [Upload New File]
   ```

3. **Scheduled Reports** (Future):
   - Daily sales summary
   - Weekly KPI report
   - Monthly executive summary

**Email Service**: SendGrid integration

---

## Multi-Tenant Architecture

### Current State: BIBBI Focus

**Active Tenant**: BIBBI Parfum
- Subdomain: `bibbi.taskifai.com`
- Database: Dedicated Supabase project
- Users: ~10 analysts and managers
- Data: 8+ reseller partners, 100K+ sales records

**Paused Tenant**: Demo
- Subdomain: `demo.taskifai.com`
- Database: Paused (cost optimization)
- Purpose: Reference implementation, testing, demos

**Future Tenants**: Architecture supports unlimited tenants

### Multi-Tenant Design Principles

**1. Subdomain-Based Routing**:
```
User visits: bibbi.taskifai.com
     ↓
Middleware extracts: subdomain = "bibbi"
     ↓
Registry lookup: tenant_id = "uuid-for-bibbi"
     ↓
Inject into request: request.state.tenant
     ↓
All queries filtered: WHERE user_id IN (SELECT id FROM users WHERE tenant_id = '...')
```

**2. Tenant Registry** (Centralized):
```sql
-- Separate Supabase project for tenant registry
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    tenant_name VARCHAR(255) NOT NULL,
    supabase_url VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active'
);

CREATE TABLE user_tenants (
    user_email VARCHAR(255) NOT NULL,
    tenant_id UUID REFERENCES tenants(tenant_id),
    PRIMARY KEY (user_email, tenant_id)
);
```

**3. Data Isolation Layers**:

| Layer | Isolation Method | Enforcement |
|-------|-----------------|-------------|
| Database | Separate Supabase projects per tenant | ✅ Physical |
| Application | user_id filtering in all queries | ✅ Code-enforced |
| RLS | Supabase Row-Level Security policies | ✅ Database-enforced |
| Frontend | Subdomain extraction | ✅ Client-enforced |

**4. Shared vs Tenant-Specific Resources**:

**Shared Across All Tenants**:
- FastAPI application code
- Celery workers
- Redis broker
- Vendor processors (code)
- AI chat agent (code)

**Tenant-Specific**:
- Supabase database instance
- User accounts
- Sales data
- Dashboard configurations
- Upload history

### Multi-Tenant Login Flow

**Scenario 1: Single-Tenant User**:
```
1. User enters email at: app.taskifai.com/login
2. System looks up tenants for email
3. Finds 1 tenant: BIBBI
4. Redirects to: bibbi.taskifai.com/login
5. User enters password
6. JWT issued with tenant_id claim
7. Dashboard loads
```

**Scenario 2: Multi-Tenant User**:
```
1. User enters email at: app.taskifai.com/login
2. System looks up tenants for email
3. Finds 2 tenants: BIBBI, Demo
4. Shows tenant selector: "Which account?"
   - BIBBI Parfum
   - Demo Account
5. User selects BIBBI
6. Redirects to: bibbi.taskifai.com/login
7. User enters password
8. JWT issued with tenant_id claim
9. Dashboard loads
```

### Tenant Isolation in Practice

**Example: Two Companies, Same Platform**:

| Aspect | BIBBI Parfum | AcmeCorp (Future) |
|--------|--------------|-------------------|
| Subdomain | bibbi.taskifai.com | acme.taskifai.com |
| Database | Supabase project #1 | Supabase project #2 |
| Users | 10 analysts | 25 analysts |
| Data | 100K records | 500K records |
| Vendors | Liberty, Galilu, Selfridges | Amazon, Walmart, Target |
| Visible Data | BIBBI only | AcmeCorp only |

**BIBBI analyst cannot:**
- See AcmeCorp data (different database)
- Access acme.taskifai.com (JWT tenant_id mismatch)
- Query acme database (no credentials)

**AcmeCorp analyst cannot:**
- See BIBBI data (different database)
- Access bibbi.taskifai.com (JWT tenant_id mismatch)
- Query bibbi database (no credentials)

---

## Recent Platform Improvements

### DRY Refactoring (October 2025)

**Problem**: Code duplication across 11 vendor processors

**Before Refactoring**:
```python
# Repeated in EVERY processor file (11 files × 150 LOC = 1,650 LOC)
class LibertyProcessor:
    def _validate_ean(self, value):
        # 15 lines of validation logic
        ...

    def _to_int(self, value, field_name):
        # 8 lines of conversion logic
        ...

    def _to_float(self, value, field_name):
        # 10 lines of conversion logic
        ...

    # ... 10+ more utility methods
```

**After Refactoring**:
```python
# Shared utilities in app/utils/validation.py
from app.utils.validation import validate_ean, to_int, to_float

class LibertyProcessor(BibbiBseProcessor):
    def transform_row(self, raw_row, batch_id):
        # Use shared utilities (no duplication)
        ean = validate_ean(raw_row.get("Barcode"), required=True)
        quantity = to_int(raw_row.get("Quantity"), "Quantity")
        price = to_float(raw_row.get("Price"), "Price")
        ...
```

**Impact**:
- ✅ Eliminated ~1,500 lines of duplicated code
- ✅ Single source of truth for validation logic
- ✅ Consistent error messages across all processors
- ✅ Easier to add new processors (inherit base + implement 30-50 LOC)

**Modules Created**:
1. **`app/utils/validation.py`**: EAN validation, type conversions, date validation
2. **`app/utils/excel.py`**: Excel parsing, row extraction, header validation
3. **`app/services/vendors/base.py`**: General vendor processor base class
4. **Enhanced `app/services/bibbi/processors/base.py`**: BIBBI-specific base class

**Testing**:
- Created 115 unit tests (100% passing)
- 82% code coverage
- Zero breaking changes

**Documentation**:
- `/claudedocs/refactoring_summary.md` - Complete refactoring details
- `/claudedocs/architecture_clarity.md` - Multi-tenant design rationale
- `/claudedocs/adding_vendor_processors.md` - Developer guide

### Liberty Processor Development (Ongoing)

**Status**: Active development, not yet complete

**Challenges Being Addressed**:
1. **Multi-Store Detection**: Liberty sends one file with multiple stores
2. **EAN Validation**: Preventing wrong EAN generation for products
3. **Sales Insertion**: Resolving 0/45 insertion failures
4. **Data Quality**: Critical bugs fixed (4 major issues resolved)

**Recent Fixes** (from git history):
- `fbfeee3`: Fix Liberty upload 0/45 insertion failures
- `e020240`: Prevent wrong EAN generation for Liberty products
- `58ba89b`: Correct resellers table query column name
- `f15c496`: Resolve 4 critical/major issues in Liberty processor
- `afe0812`: Address code review recommendations

**Why Liberty is Complex**:
- Multiple stores in one file (need store extraction)
- Inconsistent store naming ("Liberty London" vs "London - Liberty")
- Some products have multiple EANs
- GBP currency (requires conversion)
- Quarterly reporting format (aggregated data)

### Architecture Decisions Preserved

**Decision 1: Keep `/services/vendors/` Directory**

**Rationale**:
- Platform designed for multi-tenancy
- Demo tenant may restart in future
- Future tenants will need general processors
- Clear separation: `/vendors/` = general, `/bibbi/processors/` = BIBBI-specific

**Decision 2: Two Base Processor Classes**

**Rationale**:
- `VendorProcessor` (utils/vendors/base.py) = Pure utilities, no business logic
- `BibbiBseProcessor` (bibbi/processors/base.py) = BIBBI requirements:
  - 3-stage processing pipeline
  - Multi-store detection
  - Reseller sales_channel integration
  - Tenant ID injection

**Decision 3: Conservative Refactoring**

**Rationale**:
- Extract utilities first (foundation)
- Refactor processors later (when stable)
- Liberty actively being developed (don't touch)
- Other processors need rewriting anyway (vendor format changes)

---

## Getting Started

### For End-Users (Analysts)

1. **Access Your Tenant**:
   - Visit `your-company.taskifai.com/login`
   - Enter your credentials
   - Enable 2FA (recommended)

2. **Upload Your First File**:
   - Click "Upload Data"
   - Drag & drop your vendor file
   - Choose "Append" mode
   - Wait for processing (30 seconds - 2 minutes)

3. **Explore Your Data**:
   - View dashboard (auto-loads)
   - Click on KPI cards for details
   - Use filters (date range, channel, vendor)

4. **Ask AI Questions**:
   - Click "AI Chat"
   - Type: "What were my top selling products last month?"
   - Review generated insights
   - Ask follow-up questions

### For Developers

1. **Local Setup** (Docker):
   ```bash
   git clone <repo-url>
   cd TaskifAI_platform_v2.0

   # Set up environment
   cd backend && cp .env.example .env
   cd ../frontend && cp .env.example .env

   # Start all services
   cd .. && docker-compose up -d

   # Access:
   # - Frontend: http://localhost:3000
   # - Backend: http://localhost:8000
   # - API Docs: http://localhost:8000/api/docs
   ```

2. **Add New Vendor Processor**:
   - See `/claudedocs/adding_vendor_processors.md`
   - Inherit from `BibbiBseProcessor` (BIBBI) or `VendorProcessor` (general)
   - Implement `transform_row()` method
   - Add detection patterns to `detector.py`
   - Test with sample file

3. **Run Tests**:
   ```bash
   cd backend
   pytest
   pytest --cov=app tests/  # With coverage
   ```

### For Administrators

1. **Tenant Onboarding**:
   - Create Supabase project
   - Run schema.sql
   - Add tenant to registry
   - Configure subdomain (DNS)
   - Create first user account

2. **Monitoring**:
   - Supabase Dashboard: Query performance
   - DigitalOcean Insights: Application health
   - Redis: Queue length, worker status
   - SendGrid: Email delivery rates

---

## Related Documentation

### Technical Deep Dives
- [System Architecture](../docs/architecture/SYSTEM_OVERVIEW.md) - Complete technical architecture
- [API Reference](../docs/api/README.md) - REST API documentation
- [Database Schema](../docs/architecture/04_Data_Model.md) - Complete data model

### Development Guides
- [Adding Vendor Processors](./adding_vendor_processors.md) - Step-by-step guide
- [Developer Guide](./DEVELOPER_GUIDE.md) - Common workflows and patterns
- [Testing Strategy](../backend/tests/README.md) - Testing approach

### Recent Changes
- [Refactoring Summary](./refactoring_summary.md) - DRY refactoring details
- [Architecture Clarity](./architecture_clarity.md) - Multi-tenant design rationale

### User Guides
- [User Guide](./USER_GUIDE.md) - End-user documentation
- [AI Chat Examples](./ai_chat_examples.md) - Effective chat prompts

---

**Questions?** See [FAQ](./FAQ.md) or contact support.

**Contributing?** See [Contributing Guide](../CONTRIBUTING.md).

**Last Updated**: 2025-10-25
**Next Review**: After Liberty processor completion
