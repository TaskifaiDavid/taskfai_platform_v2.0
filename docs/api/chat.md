# AI Chat API

Natural language interface for querying sales data using OpenAI-powered SQL generation and Supabase execution.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [POST /api/chat/query](#post-query)
  - [GET /api/chat/history](#get-history)
  - [DELETE /api/chat/history](#delete-history)
  - [GET /api/chat/sessions](#get-sessions)
- [Query Types & Intent Detection](#query-types--intent-detection)
- [Database Schema Context](#database-schema-context)
- [Security & Validation](#security--validation)
- [Example Queries](#example-queries)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)
- [Limitations](#limitations)

---

## Overview

The AI Chat API provides a natural language interface for querying sales data. Users can ask questions in plain English, and the system generates SQL queries, executes them securely, and returns results in natural language.

### Key Features

- **Natural Language Processing**: Ask questions in plain English
- **SQL Generation**: OpenAI GPT-4 generates optimized SQL queries
- **Secure Execution**: Automatic user_id filtering and SQL injection prevention
- **Intent Detection**: Recognizes query types (analytics, prediction, comparison)
- **Multi-Table Support**: Queries both online and offline sales data
- **Conversational Context**: Session-based memory for follow-up questions

### Architecture

**Hybrid SQL Agent:**
1. User submits natural language query
2. OpenAI generates SQL from query + database schema
3. Security validator ensures safe SQL and injects user_id filter
4. Supabase executes SQL via REST API (exec_sql RPC function)
5. OpenAI generates natural language response from results

**Why Hybrid Approach:**
- **Flexibility**: OpenAI can handle complex, creative queries
- **Security**: SQL validation prevents injection attacks
- **Performance**: Direct database execution via Supabase REST API
- **No IPv6 Required**: Works with standard HTTP/HTTPS connections

---

## Architecture

### System Flow

```
┌─────────────┐
│   User      │
│  "What are  │
│  my top 5   │
│  products?" │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│      FastAPI Chat Endpoint          │
│   POST /api/chat/query              │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│     Intent Detector                 │
│  (Classify query type)              │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   OpenAI GPT-4 SQL Generator        │
│  (Natural language → SQL)           │
│  + Database Schema Context          │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Security Validator                │
│  - Check for dangerous operations   │
│  - Inject user_id filter            │
│  - Validate table access            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Supabase MCP (REST API)           │
│   Execute SQL via exec_sql RPC      │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   OpenAI GPT-4 Response Generator   │
│  (SQL results → Natural language)   │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Response to User                  │
│  "Your top 5 products are..."       │
└─────────────────────────────────────┘
```

### Components

**1. SQLDatabaseAgent** (`app.services.ai_chat.agent`)
- Orchestrates query processing pipeline
- Manages OpenAI API calls
- Coordinates SQL generation and execution

**2. IntentDetector** (`app.services.ai_chat.intent`)
- Classifies query into types: ANALYTICS, PREDICTION, ADVANCED_ANALYSIS, etc.
- Routes queries to appropriate processing logic
- Detects time-series and forecasting requests

**3. QuerySecurityValidator** (`app.services.ai_chat.security`)
- Prevents SQL injection attacks
- Ensures user_id filtering on all queries
- Blocks dangerous operations (INSERT, UPDATE, DELETE, DROP)
- Validates table access permissions

**4. Supabase MCP Executor**
- Executes SQL via Supabase REST API
- Uses `exec_sql` RPC function for direct SQL execution
- Returns results as JSON

---

## Authentication

All Chat endpoints require JWT authentication.

**Headers Required:**
```http
Authorization: Bearer <your_jwt_token>
X-Tenant-ID: <tenant_id>
```

**User Context:**
- Queries automatically filtered by authenticated `user_id`
- Security validator injects `WHERE user_id = '{user_id}'` into all SQL
- Users can only query their own data

---

## Endpoints

### POST /api/chat/query

Send natural language query to AI chat agent.

**Endpoint:** `POST /api/chat/query`

#### Request Body

```json
{
  "query": "What are my top 5 products by revenue?",
  "session_id": "session_user123_1729267200"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Natural language question about sales data |
| `session_id` | string | No | Optional session ID for conversation continuity |

#### Response

**Status Code:** `200 OK`

```json
{
  "response": "Based on your sales data, here are your top 5 products by revenue:\n\n1. **Premium Face Serum** - €18,500.00 (425 units sold)\n2. **Hydrating Moisturizer** - €15,230.50 (378 units sold)\n3. **Anti-Aging Night Cream** - €12,840.25 (312 units sold)\n4. **Vitamin C Serum** - €10,560.00 (264 units sold)\n5. **Eye Repair Cream** - €9,340.75 (245 units sold)\n\nThese 5 products account for €66,471.50 in total revenue.",
  "sql_generated": "SELECT functional_name, product_ean, SUM(sales_eur) as revenue, SUM(quantity) as units FROM ecommerce_orders WHERE user_id = 'user123' GROUP BY functional_name, product_ean ORDER BY revenue DESC LIMIT 5",
  "session_id": "session_user123_1729267200"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | Natural language answer to the query |
| `sql_generated` | string | SQL query that was executed (for debugging) |
| `session_id` | string | Session ID for follow-up queries |

#### Error Responses

**400 Bad Request - Security Validation Failed:**
```json
{
  "detail": "Security validation failed: Query contains potentially dangerous operations"
}
```

**500 Internal Server Error - Query Processing Failed:**
```json
{
  "detail": "Query processing failed: Invalid SQL syntax"
}
```

#### Query Processing Flow

1. **Intent Detection**:
   - Analyze query to determine type (analytics, prediction, etc.)
   - Extract entities (dates, products, metrics)

2. **SQL Generation**:
   - OpenAI generates SQL based on query + database schema
   - Includes table structure, column names, relationships
   - Optimizes for performance (LIMIT, GROUP BY, indexes)

3. **Security Validation**:
   - Check for dangerous operations (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE)
   - Verify user_id filter is present
   - Inject user_id if missing
   - Validate table access

4. **Execution**:
   - Execute SQL via Supabase REST API
   - Handle errors and timeouts
   - Return results as JSON

5. **Response Generation**:
   - OpenAI converts SQL results to natural language
   - Formats numbers and dates
   - Highlights key insights
   - Uses business-friendly terminology

#### Example Requests

**Basic Query:**
```bash
curl -X POST "https://api.taskifai.com/api/chat/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is my total revenue this month?"
  }'
```

**Follow-up Query with Session:**
```bash
curl -X POST "https://api.taskifai.com/api/chat/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What about last month?",
    "session_id": "session_user123_1729267200"
  }'
```

**Python Example:**
```python
import requests

def ask_question(query: str, session_id: str = None):
    """Send natural language query to AI chat"""
    payload = {
        "query": query,
        "session_id": session_id
    }

    response = requests.post(
        "https://api.taskifai.com/api/chat/query",
        json=payload,
        headers={"Authorization": f"Bearer {jwt_token}"}
    )

    result = response.json()
    print(f"Question: {query}")
    print(f"Answer: {result['response']}")
    print(f"SQL Generated: {result['sql_generated']}")

    return result['session_id']

# Usage
session_id = ask_question("What are my top 5 products by revenue?")

# Follow-up question
ask_question("Which countries bought these products?", session_id=session_id)
```

**JavaScript Example:**
```javascript
import axios from 'axios';

async function askQuestion(query, sessionId = null) {
  const { data } = await axios.post('/api/chat/query', {
    query,
    session_id: sessionId
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });

  console.log(`Question: ${query}`);
  console.log(`Answer: ${data.response}`);
  console.log(`SQL: ${data.sql_generated}`);

  return data.session_id;
}

// Usage
const sessionId = await askQuestion('What are my top 5 products by revenue?');

// Follow-up question
await askQuestion('Which countries bought these products?', sessionId);
```

---

### GET /api/chat/history

Get conversation history for current user.

**Endpoint:** `GET /api/chat/history`

**Status:** Currently disabled - conversation history not implemented in current architecture.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `session_id` | string | No | - | Filter by specific session ID |
| `limit` | integer | No | 50 | Number of conversations to return (max 100) |
| `offset` | integer | No | 0 | Pagination offset |

#### Response

**Status Code:** `200 OK`

```json
{
  "conversation_id": "temp",
  "session_id": "temp",
  "messages": [],
  "created_at": "2025-10-18T10:30:00Z"
}
```

**Note:** This endpoint is intentionally disabled in the current implementation. Conversation history is not persisted to the database. Each query is processed independently.

---

### DELETE /api/chat/history

Clear conversation history.

**Endpoint:** `DELETE /api/chat/history`

**Status:** Currently disabled - conversation history not implemented in current architecture.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | No | Clear specific session. If omitted, clears all user conversations |

#### Response

**Status Code:** `204 NO CONTENT`

**Note:** This endpoint is intentionally disabled in the current implementation.

---

### GET /api/chat/sessions

List all chat sessions for current user.

**Endpoint:** `GET /api/chat/sessions`

**Status:** Currently disabled - conversation history not implemented in current architecture.

#### Response

**Status Code:** `200 OK`

```json
[]
```

**Note:** This endpoint is intentionally disabled in the current implementation. Returns empty array.

---

## Query Types & Intent Detection

The AI Chat system classifies queries into different types to optimize processing:

### Intent Types

**1. ANALYTICS (Standard SQL Queries)**
- **Description**: Standard sales data queries
- **Examples**:
  - "What is my total revenue this month?"
  - "Show me sales by country"
  - "Which products sold best in Germany?"
- **Processing**: Direct SQL generation and execution

**2. PREDICTION (Time-Series Forecasting)**
- **Description**: Forecast future sales or trends
- **Examples**:
  - "What will my sales be next month?"
  - "Predict revenue for Q4 2025"
  - "Will product X continue to grow?"
- **Processing**: Fetch historical data → AI-powered trend analysis → Forecast generation

**3. ADVANCED_ANALYSIS (Complex Insights)**
- **Description**: Deep analysis requiring statistical methods
- **Examples**:
  - "What are the key drivers of my sales?"
  - "Identify anomalies in my data"
  - "Which products have seasonal patterns?"
- **Processing**: Fetch data → AI-powered analysis → Comprehensive insights

**4. COMPARISON**
- **Description**: Compare time periods, products, or channels
- **Examples**:
  - "Compare this month to last month"
  - "How do online sales compare to offline?"
  - "Which reseller performs best?"
- **Processing**: Multiple SQL queries → Aggregation → Comparison report

### Intent Detection Logic

**Keyword Matching:**
- **Prediction**: "predict", "forecast", "next month", "future", "will be"
- **Analysis**: "why", "analyze", "insights", "trends", "patterns", "anomalies"
- **Comparison**: "compare", "vs", "versus", "difference between"
- **Analytics**: All other queries default to standard SQL

**Time References:**
- **Absolute**: "January 2025", "Q3 2024", "2024-01-01"
- **Relative**: "last month", "this year", "past 6 months", "yesterday"
- **Future**: "next month", "next quarter", "2026"

---

## Database Schema Context

The AI Chat system has context about your database schema to generate accurate SQL:

### Tables (Priority Order)

**1. ecommerce_orders (PRIMARY - ALWAYS QUERY FIRST)**
```sql
-- D2C/Online sales data
Columns:
  - order_id: UUID (primary key)
  - user_id: UUID (auto-filtered)
  - product_ean: VARCHAR(13)
  - functional_name: VARCHAR(255) -- Internal product ID
  - product_name: VARCHAR(255)
  - sales_eur: DECIMAL(10,2)
  - quantity: INTEGER
  - cost_of_goods: DECIMAL(10,2)
  - stripe_fee: DECIMAL(10,2)
  - order_date: DATE
  - country: VARCHAR(100)
  - city: VARCHAR(100)
  - utm_source: VARCHAR(255)
  - utm_medium: VARCHAR(255)
  - utm_campaign: VARCHAR(255)
  - device_type: VARCHAR(50)
  - reseller: VARCHAR(255) -- Usually NULL for D2C

IMPORTANT: Contains functional_name directly - NO JOIN to products table needed
```

**2. sellout_entries2 (B2B/Offline Sales)**
```sql
-- B2B/Offline sales data
Columns:
  - sale_id: UUID (primary key)
  - user_id: UUID (auto-filtered)
  - product_id: UUID (foreign key to products)
  - reseller_id: UUID (foreign key to resellers)
  - functional_name: VARCHAR(255)
  - product_ean: VARCHAR(13)
  - reseller: VARCHAR(255)
  - sales_eur: DECIMAL(10,2)
  - quantity: INTEGER
  - currency: VARCHAR(3)
  - month: INTEGER (1-12)
  - year: INTEGER
  - created_at: TIMESTAMP

IMPORTANT: Requires JOIN to products table for product_name
```

**3. products (Product Catalog)**
```sql
-- Product reference table
Columns:
  - product_id: UUID (primary key)
  - sku: VARCHAR(100)
  - product_name: VARCHAR(255)
  - product_ean: VARCHAR(13)
  - functional_name: VARCHAR(255)
  - category: VARCHAR(100)
```

**4. resellers (Reseller Directory)**
```sql
-- Reseller reference table
Columns:
  - reseller_id: UUID (primary key)
  - name: VARCHAR(255)
  - country: VARCHAR(100)
```

### SQL Generation Rules

**CRITICAL RULES:**

1. **ALWAYS filter by user_id**: `WHERE user_id = '{user_id}'`
2. **Query ecommerce_orders FIRST**: It's the primary sales table with most data
3. **NO JOIN for ecommerce_orders**: functional_name is built-in
4. **Only query sellout_entries2** if user explicitly asks for "B2B", "offline", or "reseller" data
5. **Use ONLY SELECT queries**: No INSERT, UPDATE, DELETE, DROP, ALTER, CREATE
6. **Time queries**:
   - ecommerce_orders: Use `order_date` column (DATE type)
   - sellout_entries2: Use `month` and `year` columns (INTEGER types)
7. **Aggregate for totals**: Use SUM, COUNT, AVG for summaries
8. **Use LIMIT**: Max 1000 rows to prevent timeout
9. **Handle NULL values**: Use COALESCE for safety

**Query Best Practices:**

- **Meaningful aliases**: `SUM(sales_eur) as total_revenue`
- **Logical ORDER BY**: DESC for top results, ASC for trends
- **GROUP BY**: Group by appropriate dimensions
- **Clear formatting**: Format monetary values
- **Performance**: Use indexes, avoid full table scans

---

## Security & Validation

### SQL Injection Prevention

**QuerySecurityValidator** prevents SQL injection attacks:

**Blocked Operations:**
- `INSERT`, `UPDATE`, `DELETE` - Data modification
- `DROP`, `ALTER`, `CREATE` - Schema changes
- `TRUNCATE` - Data deletion
- `GRANT`, `REVOKE` - Permission changes
- SQL comments: `--`, `/*`, `*/`
- Multiple statements: `;` (semicolon)

**Example Blocked Query:**
```sql
-- User attempts injection
Query: "Show sales'; DROP TABLE ecommerce_orders; --"

-- Security validator detects dangerous operation
Error: "Query contains potentially dangerous operations: DROP"
```

### User ID Filtering

**Automatic Injection:**
- Security validator scans SQL for `WHERE user_id = '{user_id}'`
- If missing, automatically injects filter
- Prevents cross-user data access

**Example:**

**Generated SQL (without user_id):**
```sql
SELECT SUM(sales_eur) as revenue FROM ecommerce_orders
```

**After Security Validation:**
```sql
SELECT SUM(sales_eur) as revenue FROM ecommerce_orders WHERE user_id = 'user123'
```

### Table Access Control

**Allowed Tables:**
- `ecommerce_orders` (with user_id filter)
- `sellout_entries2` (with user_id filter)
- `products` (read-only reference)
- `resellers` (read-only reference)

**Blocked Tables:**
- `users` (sensitive user data)
- `tenants` (multi-tenant configuration)
- `upload_batches` (internal processing)
- System tables

---

## Example Queries

### Basic Analytics

**Total Revenue:**
```
Query: "What is my total revenue this month?"

Generated SQL:
SELECT SUM(sales_eur) as total_revenue
FROM ecommerce_orders
WHERE user_id = 'user123'
  AND order_date >= '2025-10-01'
  AND order_date < '2025-11-01'

Response: "Your total revenue for October 2025 is €45,680.50."
```

**Top Products:**
```
Query: "What are my top 5 products by revenue?"

Generated SQL:
SELECT
  functional_name,
  product_ean,
  SUM(sales_eur) as revenue,
  SUM(quantity) as units
FROM ecommerce_orders
WHERE user_id = 'user123'
GROUP BY functional_name, product_ean
ORDER BY revenue DESC
LIMIT 5

Response: "Your top 5 products by revenue are:
1. Premium Face Serum - €18,500.00
2. Hydrating Moisturizer - €15,230.50
3. Anti-Aging Night Cream - €12,840.25
4. Vitamin C Serum - €10,560.00
5. Eye Repair Cream - €9,340.75"
```

**Sales by Country:**
```
Query: "Show me sales by country for this year"

Generated SQL:
SELECT
  country,
  SUM(sales_eur) as revenue,
  SUM(quantity) as units,
  COUNT(*) as orders
FROM ecommerce_orders
WHERE user_id = 'user123'
  AND order_date >= '2025-01-01'
  AND order_date < '2026-01-01'
GROUP BY country
ORDER BY revenue DESC

Response: "Here are your sales by country for 2025:
1. Germany: €28,340.50 (748 units, 532 orders)
2. France: €21,560.25 (589 units, 428 orders)
3. Netherlands: €18,920.75 (512 units, 389 orders)
..."
```

### Time-Based Queries

**Month-over-Month:**
```
Query: "Compare this month's sales to last month"

Generated SQL (2 queries):
-- This month
SELECT SUM(sales_eur) as revenue, SUM(quantity) as units
FROM ecommerce_orders
WHERE user_id = 'user123'
  AND order_date >= '2025-10-01' AND order_date < '2025-11-01'

-- Last month
SELECT SUM(sales_eur) as revenue, SUM(quantity) as units
FROM ecommerce_orders
WHERE user_id = 'user123'
  AND order_date >= '2025-09-01' AND order_date < '2025-10-01'

Response: "October 2025: €45,680.50 (1,245 units)
September 2025: €52,340.75 (1,398 units)

Your sales decreased by €6,660.25 (-12.7%) from September to October."
```

**Year-over-Year:**
```
Query: "How do this year's sales compare to last year?"

Generated SQL:
-- Current year
SELECT SUM(sales_eur) as revenue, SUM(quantity) as units
FROM ecommerce_orders
WHERE user_id = 'user123'
  AND order_date >= '2025-01-01' AND order_date < '2026-01-01'

-- Previous year
SELECT SUM(sales_eur) as revenue, SUM(quantity) as units
FROM ecommerce_orders
WHERE user_id = 'user123'
  AND order_date >= '2024-01-01' AND order_date < '2025-01-01'

Response: "2025: €542,680.50 (14,520 units)
2024: €489,320.25 (13,102 units)

Your sales increased by €53,360.25 (+10.9%) year-over-year."
```

### Advanced Analysis

**Product Performance:**
```
Query: "Which products have the highest profit margin?"

Generated SQL:
SELECT
  functional_name,
  SUM(sales_eur) as revenue,
  SUM(cost_of_goods) as cogs,
  SUM(stripe_fee) as fees,
  SUM(sales_eur - cost_of_goods - stripe_fee) as profit,
  (SUM(sales_eur - cost_of_goods - stripe_fee) / SUM(sales_eur) * 100) as profit_margin
FROM ecommerce_orders
WHERE user_id = 'user123'
  AND cost_of_goods IS NOT NULL
GROUP BY functional_name
ORDER BY profit_margin DESC
LIMIT 10

Response: "Your top 10 products by profit margin are:
1. Eye Repair Cream - 68.5% margin (€9,340 revenue, €6,398 profit)
2. Vitamin C Serum - 65.2% margin (€10,560 revenue, €6,885 profit)
..."
```

**Channel Analysis:**
```
Query: "Compare online vs offline sales"

Generated SQL (2 queries):
-- Online
SELECT
  'online' as channel,
  SUM(sales_eur) as revenue,
  SUM(quantity) as units,
  COUNT(*) as transactions
FROM ecommerce_orders
WHERE user_id = 'user123'

-- Offline
SELECT
  'offline' as channel,
  SUM(sales_eur) as revenue,
  SUM(quantity) as units,
  COUNT(*) as transactions
FROM sellout_entries2
WHERE user_id = 'user123'

Response: "Online (D2C): €342,680.50 (9,245 units, 6,532 transactions)
Offline (B2B): €200,000.00 (5,275 units, 1,890 transactions)

Your online channel represents 63.2% of total revenue."
```

### Prediction & Forecasting

**Revenue Forecast:**
```
Query: "What will my revenue be next month?"

Processing:
1. Fetch last 12 months of sales data
2. Calculate monthly trends and growth rate
3. Detect seasonality patterns
4. Apply AI-powered forecasting
5. Generate prediction with confidence range

Response: "Based on your historical sales data, here's my forecast for November 2025:

**Forecasted Revenue: €48,500 ± €4,200**
(Confidence: Medium - based on 12 months of data)

**Key Insights:**
- Average monthly growth: +3.2%
- Seasonal pattern: November typically sees +8% increase vs October
- Recent momentum: Last 3 months trending upward
- Risk factors: Limited holiday season data

**Recommendation:** Stock inventory for 1,320 units (10% safety buffer) to meet expected demand."
```

### Complex Queries

**Reseller Performance:**
```
Query: "Which reseller had the best performance in Q3 2025?"

Generated SQL:
SELECT
  reseller,
  SUM(sales_eur) as revenue,
  SUM(quantity) as units,
  COUNT(*) as transactions,
  AVG(sales_eur) as avg_transaction_value
FROM sellout_entries2
WHERE user_id = 'user123'
  AND year = 2025
  AND month >= 7 AND month <= 9
GROUP BY reseller
ORDER BY revenue DESC
LIMIT 1

Response: "Your best performing reseller in Q3 2025 was Galilu Beauty (Poland):
- Revenue: €78,450.25
- Units Sold: 2,100
- Transactions: 890
- Average Transaction Value: €88.15"
```

**UTM Source Analysis:**
```
Query: "Which marketing channel brings the most revenue?"

Generated SQL:
SELECT
  COALESCE(utm_source, 'direct') as source,
  SUM(sales_eur) as revenue,
  SUM(quantity) as units,
  COUNT(*) as orders,
  AVG(sales_eur) as avg_order_value
FROM ecommerce_orders
WHERE user_id = 'user123'
GROUP BY utm_source
ORDER BY revenue DESC

Response: "Your top marketing channels by revenue:
1. Google Ads: €124,560.50 (3,420 orders, €36.42 AOV)
2. Instagram: €89,320.25 (2,580 orders, €34.62 AOV)
3. Direct: €67,890.75 (1,920 orders, €35.36 AOV)
4. Facebook: €45,680.00 (1,290 orders, €35.41 AOV)"
```

---

## Code Examples

### Complete Python Chat Client

```python
import requests
from typing import Optional, Dict, Any

class TaskifAIChat:
    """Python client for TaskifAI AI Chat API"""

    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.headers = {"Authorization": f"Bearer {jwt_token}"}
        self.session_id = None

    def ask(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a natural language question

        Args:
            query: Natural language question
            session_id: Optional session ID for follow-up questions

        Returns:
            Dict with response, sql_generated, session_id
        """
        payload = {
            "query": query,
            "session_id": session_id or self.session_id
        }

        response = requests.post(
            f"{self.base_url}/api/chat/query",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()

        result = response.json()

        # Store session ID for follow-up questions
        self.session_id = result.get('session_id')

        return result

    def ask_and_print(self, query: str):
        """Ask question and print formatted response"""
        print(f"\n{'=' * 60}")
        print(f"Q: {query}")
        print(f"{'=' * 60}")

        result = self.ask(query)

        print(f"\nAnswer:\n{result['response']}")

        if result.get('sql_generated'):
            print(f"\n[SQL Generated]")
            print(result['sql_generated'])

        print(f"\n{'=' * 60}\n")

        return result

# Usage example
if __name__ == "__main__":
    chat = TaskifAIChat(
        base_url="https://api.taskifai.com",
        jwt_token="your_jwt_token_here"
    )

    # Ask initial question
    chat.ask_and_print("What are my top 5 products by revenue?")

    # Follow-up question (uses session_id automatically)
    chat.ask_and_print("Which countries bought these products?")

    # Another follow-up
    chat.ask_and_print("Compare this to last month")

    # Reset conversation (new session)
    chat.session_id = None
    chat.ask_and_print("What is my total revenue this year?")
```

### Complete JavaScript/TypeScript Client

```typescript
import axios, { AxiosInstance } from 'axios';

interface ChatQueryRequest {
  query: string;
  session_id?: string;
}

interface ChatQueryResponse {
  response: string;
  sql_generated: string;
  session_id: string;
}

class TaskifAIChat {
  private client: AxiosInstance;
  private sessionId: string | null = null;

  constructor(baseURL: string, jwtToken: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        Authorization: `Bearer ${jwtToken}`
      }
    });
  }

  async ask(query: string, sessionId?: string): Promise<ChatQueryResponse> {
    const { data } = await this.client.post<ChatQueryResponse>('/api/chat/query', {
      query,
      session_id: sessionId || this.sessionId
    });

    // Store session ID for follow-up questions
    this.sessionId = data.session_id;

    return data;
  }

  async askAndPrint(query: string): Promise<ChatQueryResponse> {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Q: ${query}`);
    console.log('='.repeat(60));

    const result = await this.ask(query);

    console.log(`\nAnswer:\n${result.response}`);

    if (result.sql_generated) {
      console.log('\n[SQL Generated]');
      console.log(result.sql_generated);
    }

    console.log(`\n${'='.repeat(60)}\n`);

    return result;
  }

  resetSession(): void {
    this.sessionId = null;
  }
}

// Usage example
async function main() {
  const chat = new TaskifAIChat(
    'https://api.taskifai.com',
    'your_jwt_token_here'
  );

  // Ask initial question
  await chat.askAndPrint('What are my top 5 products by revenue?');

  // Follow-up question (uses session_id automatically)
  await chat.askAndPrint('Which countries bought these products?');

  // Another follow-up
  await chat.askAndPrint('Compare this to last month');

  // Reset conversation (new session)
  chat.resetSession();
  await chat.askAndPrint('What is my total revenue this year?');
}

main().catch(console.error);
```

### React Hook for Chat Interface

```typescript
import { useState, useCallback } from 'react';
import axios from 'axios';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sql?: string;
  timestamp: Date;
}

export function useChatBot(apiBaseURL: string, jwtToken: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (query: string) => {
    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: query,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    setIsLoading(true);
    setError(null);

    try {
      const { data } = await axios.post(
        `${apiBaseURL}/api/chat/query`,
        {
          query,
          session_id: sessionId
        },
        {
          headers: { Authorization: `Bearer ${jwtToken}` }
        }
      );

      // Update session ID
      setSessionId(data.session_id);

      // Add assistant message
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response,
        sql: data.sql_generated,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);

    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to process query';
      setError(errorMessage);

      // Add error message
      const errorChatMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorChatMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseURL, jwtToken, sessionId]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearHistory
  };
}

// Usage in component
function ChatInterface() {
  const { messages, isLoading, sendMessage } = useChatBot(
    'https://api.taskifai.com',
    'your_jwt_token_here'
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const input = e.currentTarget.querySelector('input') as HTMLInputElement;
    if (input.value.trim()) {
      sendMessage(input.value);
      input.value = '';
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="content">{msg.content}</div>
            {msg.sql && (
              <details className="sql-details">
                <summary>SQL Generated</summary>
                <pre>{msg.sql}</pre>
              </details>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask a question about your sales data..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Processing...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
```

---

## Best Practices

### Query Optimization

**Be Specific:**
- ✅ "What are my top 5 products by revenue in Germany this month?"
- ❌ "Show me products"

**Use Time Ranges:**
- ✅ "Compare Q3 2025 to Q3 2024"
- ❌ "Compare quarters" (ambiguous)

**Request Exact Metrics:**
- ✅ "Show revenue, units sold, and profit margin"
- ❌ "Show me everything" (generates large queries)

### Session Management

**Use Session IDs for Follow-ups:**
```python
# Initial question
result1 = chat.ask("What are my top products?")

# Follow-up question (uses session context)
result2 = chat.ask("Which countries bought them?", session_id=result1['session_id'])
```

**Reset Sessions for New Topics:**
```python
# Reset when changing topic
chat.session_id = None
chat.ask("What is my total revenue?")
```

### Error Handling

**Handle Common Errors:**

```python
def safe_ask(chat, query: str, max_retries: int = 3):
    """Ask question with retry logic"""
    for attempt in range(max_retries):
        try:
            result = chat.ask(query)
            return result
        except requests.HTTPError as e:
            if e.response.status_code == 400:
                # Bad request - user error, don't retry
                print(f"Invalid query: {e.response.json()['detail']}")
                return None
            elif e.response.status_code == 500:
                # Server error - retry
                print(f"Attempt {attempt + 1} failed, retrying...")
                continue
            else:
                raise
        except requests.Timeout:
            print(f"Timeout on attempt {attempt + 1}, retrying...")
            continue

    print("Max retries exceeded")
    return None
```

### Security Considerations

**Never Bypass Security:**
- Do not attempt SQL injection
- Do not request access to other users' data
- Do not try to modify database schema

**Validate Responses:**
- Check `sql_generated` for suspicious operations
- Verify data belongs to your user
- Report security concerns to support

### Performance Tips

**Limit Result Sets:**
- Request specific data instead of "all"
- Use time ranges to reduce query scope
- Ask for top N results instead of full lists

**Cache Common Queries:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_monthly_revenue(chat, month: str):
    """Cache monthly revenue queries"""
    return chat.ask(f"What is my total revenue for {month}?")
```

---

## Limitations

### Current Limitations

**1. No Persistent Conversation History**
- Conversation history endpoints are disabled
- Each query is independent (session context not persisted)
- Follow-up questions require explicit session_id

**2. Data Scope**
- Only queries user's own data (user_id filtered)
- Cannot query other users or cross-tenant data
- Cannot access system tables

**3. Query Complexity**
- Complex multi-step analysis may require multiple queries
- No support for stored procedures or custom functions
- Limited to SELECT operations only

**4. Time Constraints**
- Query timeout: 30 seconds
- Large datasets may require filtering or pagination
- Real-time streaming not supported

**5. Language Support**
- English language queries only
- SQL generated in PostgreSQL dialect
- Natural language responses in English

### Known Issues

**Date Handling:**
- Offline sales (sellout_entries2) use month/year, not exact dates
- Time zones not explicitly handled (assumes UTC)
- Relative dates like "last month" depend on current server date

**Product Names:**
- ecommerce_orders has functional_name directly
- sellout_entries2 requires JOIN to products table for product_name
- Inconsistencies possible if product data not synced

**NULL Handling:**
- Cost of goods and fees may be NULL for offline sales
- Profit calculations only work for online sales with complete data
- Missing data may affect aggregations

---

## Related Documentation

- [Analytics API](./analytics.md) - Programmatic analytics queries
- [Authentication API](./authentication.md) - JWT token generation
- [Database Schema](../reference/database-schema.md) - Complete table structures
- [Security Architecture](../architecture/security-architecture.md) - RLS and data isolation
- [AI Chat System Guide](../guides/user/ai-chat.md) - End-user guide

---

## Support

For questions or issues with the AI Chat API:

- **Documentation:** [docs.taskifai.com](https://docs.taskifai.com)
- **Support Email:** support@taskifai.com
- **GitHub Issues:** [github.com/taskifai/platform/issues](https://github.com/taskifai/platform/issues)

---

**Last Updated:** 2025-10-18
**API Version:** 2.0
**Status:** Production
