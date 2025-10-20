# Analytics API

Analytics endpoints provide comprehensive sales data analysis, KPI calculations, and report generation capabilities.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [GET /api/analytics/kpis](#get-kpis)
  - [GET /api/analytics/sales](#get-sales-data)
  - [GET /api/analytics/sales/summary](#get-sales-summary)
  - [POST /api/analytics/export](#export-report-async)
  - [GET /api/analytics/export/{format}](#download-report-sync)
- [Data Models](#data-models)
- [Filtering & Aggregation](#filtering--aggregation)
- [Code Examples](#code-examples)
- [Best Practices](#best-practices)

---

## Overview

The Analytics API provides access to sales metrics, KPIs, and aggregated data across both online (D2C) and offline (B2B) sales channels. It supports:

- **KPI Calculation**: Revenue, units sold, average order value, profit margins
- **Sales Data Queries**: Paginated, filtered sales records
- **Aggregated Summaries**: Group by time, product, reseller, country
- **Report Export**: CSV, Excel, PDF formats (async and sync)
- **Multi-Channel Support**: Combined or separate analysis for online/offline channels

### Key Features

- Real-time KPI calculations from `ecommerce_orders` and `sellout_entries2` tables
- Date range filtering with flexible granularity
- Channel-specific insights (online vs offline)
- Top products and resellers ranking
- Export functionality for reporting and analysis

---

## Authentication

All Analytics endpoints require JWT authentication.

**Headers Required:**
```http
Authorization: Bearer <your_jwt_token>
X-Tenant-ID: <tenant_id>
```

**User Context:**
- All queries automatically filter by authenticated `user_id`
- RLS policies enforced via manual filtering (backend uses service_key)
- Users can only access their own sales data

---

## Endpoints

### GET /api/analytics/kpis

Get key performance indicators for the analytics dashboard.

**Endpoint:** `GET /api/analytics/kpis`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Start of date range (ISO 8601: YYYY-MM-DD) |
| `end_date` | date | No | End of date range (ISO 8601: YYYY-MM-DD) |
| `channel` | string | No | Filter by channel: `offline`, `online`, or omit for all |

#### Response

**Status Code:** `200 OK`

```json
{
  "total_revenue": 125750.50,
  "total_units": 3420,
  "avg_price": 36.78,
  "average_order_value": 36.78,
  "total_uploads": 45,
  "gross_profit": 45230.25,
  "profit_margin": 35.98,
  "unique_countries": 12,
  "order_count": 1256,
  "offline": {
    "transaction_count": 890,
    "total_revenue": 78450.25,
    "total_units": 2100,
    "avg_transaction_value": 88.15,
    "unique_resellers": 8,
    "unique_products": 45
  },
  "online": {
    "order_count": 1256,
    "total_revenue": 47300.25,
    "total_units": 1320,
    "avg_order_value": 37.65,
    "total_cogs": 18950.00,
    "total_fees": 1420.00,
    "gross_profit": 26930.25,
    "profit_margin": 56.95,
    "unique_countries": 12
  },
  "top_products": [
    {
      "product_name": "Premium Face Serum",
      "product_ean": "1234567890123",
      "revenue": 18500.00,
      "units": 425,
      "transactions": 320,
      "channel": "online"
    }
  ],
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-10-18"
  }
}
```

#### Field Descriptions

**Top-Level Metrics:**
- `total_revenue`: Combined revenue from all channels (EUR)
- `total_units`: Total units sold across channels
- `avg_price`: Average price per unit
- `average_order_value`: Same as avg_price (alias for frontend compatibility)
- `total_uploads`: Number of completed upload batches in date range
- `gross_profit`: Online profit after COGS and fees
- `profit_margin`: Gross profit as percentage of revenue
- `unique_countries`: Number of unique countries (online only)
- `order_count`: Total online orders

**Offline Metrics:**
- `transaction_count`: Number of B2B sales transactions
- `avg_transaction_value`: Average value per transaction
- `unique_resellers`: Number of distinct resellers
- `unique_products`: Number of distinct products sold

**Online Metrics:**
- `total_cogs`: Total cost of goods sold
- `total_fees`: Total payment processing fees (e.g., Stripe)

#### Aggregation Logic

**KPI Calculation Flow:**

1. **Offline (B2B) KPIs:**
   - Query `sellout_entries2` table filtered by `user_id`
   - Filter by date using `month` and `year` columns
   - Aggregate `sales_eur` and `quantity`

2. **Online (D2C) KPIs:**
   - Query `ecommerce_orders` table filtered by `user_id`
   - Filter by date using `order_date` column
   - Calculate profit: `revenue - cost_of_goods - stripe_fee`

3. **Combined Metrics:**
   - Sum offline and online totals
   - Calculate weighted averages
   - Count unique values where applicable

#### Example Requests

**Get KPIs for last 30 days:**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/kpis?start_date=2025-09-18&end_date=2025-10-18" \
  -H "Authorization: Bearer <token>"
```

**Get online-only KPIs:**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/kpis?channel=online" \
  -H "Authorization: Bearer <token>"
```

**Python Example:**
```python
import requests
from datetime import date, timedelta

# Calculate date range
end_date = date.today()
start_date = end_date - timedelta(days=30)

response = requests.get(
    "https://api.taskifai.com/api/analytics/kpis",
    params={
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "channel": "all"
    },
    headers={"Authorization": f"Bearer {jwt_token}"}
)

kpis = response.json()
print(f"Total Revenue: €{kpis['total_revenue']:,.2f}")
print(f"Profit Margin: {kpis['profit_margin']:.2f}%")
```

**JavaScript Example:**
```javascript
import axios from 'axios';

const endDate = new Date().toISOString().split('T')[0];
const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  .toISOString().split('T')[0];

const { data: kpis } = await axios.get('/api/analytics/kpis', {
  params: {
    start_date: startDate,
    end_date: endDate,
    channel: 'online'
  },
  headers: { Authorization: `Bearer ${token}` }
});

console.log(`Total Revenue: €${kpis.total_revenue.toLocaleString()}`);
console.log(`Top Product: ${kpis.top_products[0].product_name}`);
```

---

### GET /api/analytics/sales

Get detailed sales data with pagination and advanced filtering.

**Endpoint:** `GET /api/analytics/sales`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `channel` | string | No | `all` | Channel filter: `offline`, `online`, or `all` |
| `start_date` | date | No | - | Start of date range (ISO 8601) |
| `end_date` | date | No | - | End of date range (ISO 8601) |
| `reseller` | string | No | - | Reseller name filter (fuzzy search) |
| `product` | string | No | - | Product name filter (fuzzy search) |
| `country` | string | No | - | Country filter (online sales only) |
| `page` | integer | No | 1 | Page number (1-indexed) |
| `page_size` | integer | No | 50 | Results per page (max 100) |

#### Response

**Status Code:** `200 OK`

```json
{
  "data": [
    {
      "sale_id": "123e4567-e89b-12d3-a456-426614174000",
      "order_date": "2025-10-15",
      "product_name": "Premium Face Serum",
      "product_ean": "1234567890123",
      "functional_name": "SERUM_PREMIUM_50ML",
      "quantity": 2,
      "sales_eur": 89.90,
      "channel": "online",
      "country": "Germany",
      "reseller": null,
      "cost_of_goods": 35.00,
      "stripe_fee": 2.70,
      "profit": 52.20
    },
    {
      "sale_id": "987fcdeb-51ea-12d3-a456-426614174001",
      "order_date": "2025-10-14",
      "product_name": "Hydrating Moisturizer",
      "product_ean": "9876543210987",
      "functional_name": "MOISTURIZER_HYDRATING_75ML",
      "quantity": 1,
      "sales_eur": 45.00,
      "channel": "offline",
      "country": null,
      "reseller": "Galilu Beauty (Poland)",
      "cost_of_goods": null,
      "stripe_fee": null,
      "profit": null
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_records": 1842,
    "total_pages": 37,
    "has_next": true,
    "has_previous": false
  },
  "filters_applied": {
    "channel": "all",
    "start_date": "2025-09-01",
    "end_date": "2025-10-18",
    "reseller": null,
    "product": null,
    "country": null
  },
  "summary": {
    "total_revenue": 82560.50,
    "total_units": 2145,
    "average_price": 38.49
  }
}
```

#### Field Descriptions

**Sales Record Fields:**
- `sale_id`: Unique transaction identifier
- `order_date`: Transaction date (online) or month/year (offline)
- `product_name`: Display name of product
- `functional_name`: Internal product identifier
- `product_ean`: EAN-13 barcode
- `quantity`: Units sold in transaction
- `sales_eur`: Revenue in EUR
- `channel`: `online` or `offline`
- `country`: Country (online only)
- `reseller`: Reseller name (offline only)
- `cost_of_goods`: Product cost (online only)
- `stripe_fee`: Payment fee (online only)
- `profit`: Calculated profit (online only)

**Pagination:**
- Standard cursor-based pagination
- Maximum `page_size` is 100
- Use `has_next`/`has_previous` for navigation logic

**Summary:**
- Aggregated metrics for filtered dataset (not just current page)

#### Filtering Behavior

**Fuzzy Search:**
- `reseller` and `product` parameters use case-insensitive substring matching
- Example: `product=serum` matches "Premium Face Serum", "Anti-Aging Serum", etc.

**Channel Filtering:**
- `offline`: Only B2B sales from `sellout_entries2`
- `online`: Only D2C sales from `ecommerce_orders`
- `all`: Combined results from both tables

**Date Filtering:**
- Online: Exact date match via `order_date`
- Offline: Month/year based filtering
- Both dates required or both omitted

#### Example Requests

**Get online sales for Germany:**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/sales?channel=online&country=Germany&page=1&page_size=20" \
  -H "Authorization: Bearer <token>"
```

**Search for products containing "serum":**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/sales?product=serum" \
  -H "Authorization: Bearer <token>"
```

**Python Example:**
```python
import requests

def fetch_all_sales(channel='all', start_date=None, end_date=None):
    """Fetch all sales data with automatic pagination"""
    all_sales = []
    page = 1

    while True:
        response = requests.get(
            "https://api.taskifai.com/api/analytics/sales",
            params={
                "channel": channel,
                "start_date": start_date,
                "end_date": end_date,
                "page": page,
                "page_size": 100
            },
            headers={"Authorization": f"Bearer {jwt_token}"}
        )

        data = response.json()
        all_sales.extend(data['data'])

        if not data['pagination']['has_next']:
            break

        page += 1

    return all_sales

# Usage
sales = fetch_all_sales(
    channel='online',
    start_date='2025-10-01',
    end_date='2025-10-18'
)
print(f"Total sales records: {len(sales)}")
```

**JavaScript Example:**
```javascript
import axios from 'axios';

async function fetchSalesData(filters = {}) {
  const { data } = await axios.get('/api/analytics/sales', {
    params: {
      channel: filters.channel || 'all',
      start_date: filters.startDate,
      end_date: filters.endDate,
      reseller: filters.reseller,
      product: filters.product,
      country: filters.country,
      page: filters.page || 1,
      page_size: filters.pageSize || 50
    },
    headers: { Authorization: `Bearer ${token}` }
  });

  return {
    sales: data.data,
    pagination: data.pagination,
    summary: data.summary
  };
}

// Usage with filters
const result = await fetchSalesData({
  channel: 'online',
  startDate: '2025-10-01',
  endDate: '2025-10-18',
  country: 'Germany',
  page: 1,
  pageSize: 50
});

console.log(`Found ${result.sales.length} sales`);
console.log(`Total Revenue: €${result.summary.total_revenue}`);
```

---

### GET /api/analytics/sales/summary

Get aggregated sales summary grouped by dimension.

**Endpoint:** `GET /api/analytics/sales/summary`

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `group_by` | string | No | `month` | Grouping dimension: `month`, `product`, `reseller`, `country` |
| `channel` | string | No | `all` | Channel filter: `offline`, `online`, or `all` |
| `start_date` | date | No | - | Start of date range (ISO 8601) |
| `end_date` | date | No | - | End of date range (ISO 8601) |

#### Response

**Status Code:** `200 OK`

**Grouped by Month:**
```json
[
  {
    "dimension": "2025-10",
    "total_revenue": 45680.50,
    "total_units": 1245,
    "average_price": 36.69,
    "transaction_count": 892,
    "channels": {
      "online": 28450.25,
      "offline": 17230.25
    }
  },
  {
    "dimension": "2025-09",
    "total_revenue": 52340.75,
    "total_units": 1398,
    "average_price": 37.43,
    "transaction_count": 1024,
    "channels": {
      "online": 31200.50,
      "offline": 21140.25
    }
  }
]
```

**Grouped by Product:**
```json
[
  {
    "dimension": "Premium Face Serum",
    "product_ean": "1234567890123",
    "total_revenue": 18500.00,
    "total_units": 425,
    "average_price": 43.53,
    "transaction_count": 320
  },
  {
    "dimension": "Hydrating Moisturizer",
    "product_ean": "9876543210987",
    "total_revenue": 15230.50,
    "total_units": 378,
    "average_price": 40.29,
    "transaction_count": 285
  }
]
```

**Grouped by Reseller:**
```json
[
  {
    "dimension": "Galilu Beauty (Poland)",
    "reseller_id": "abc123",
    "total_revenue": 35680.00,
    "total_units": 890,
    "average_price": 40.09,
    "transaction_count": 456,
    "country": "Poland"
  }
]
```

**Grouped by Country:**
```json
[
  {
    "dimension": "Germany",
    "total_revenue": 28340.50,
    "total_units": 748,
    "average_price": 37.89,
    "transaction_count": 532
  },
  {
    "dimension": "France",
    "total_revenue": 21560.25,
    "total_units": 589,
    "average_price": 36.60,
    "transaction_count": 428
  }
]
```

#### Field Descriptions

**Common Fields:**
- `dimension`: The grouping value (month, product name, reseller name, or country)
- `total_revenue`: Sum of sales_eur for this group
- `total_units`: Sum of quantity for this group
- `average_price`: `total_revenue / total_units`
- `transaction_count`: Number of transactions in this group

**Dimension-Specific Fields:**
- Month: `channels` object with online/offline breakdown
- Product: `product_ean` for identification
- Reseller: `reseller_id` and `country`
- Country: No additional fields

#### Aggregation Logic

**Month Grouping:**
- Online: Group by `EXTRACT(YEAR_MONTH FROM order_date)`
- Offline: Group by `year || '-' || month`
- Sorted descending (most recent first)

**Product Grouping:**
- Group by `functional_name` + `product_ean`
- Sorted by `total_revenue` descending (top products first)

**Reseller Grouping:**
- Only available for offline sales
- Group by `reseller_id`
- Sorted by `total_revenue` descending

**Country Grouping:**
- Only available for online sales
- Group by `country`
- Sorted by `total_revenue` descending

#### Example Requests

**Get monthly trends:**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/sales/summary?group_by=month&start_date=2025-01-01&end_date=2025-10-18" \
  -H "Authorization: Bearer <token>"
```

**Get top products by revenue:**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/sales/summary?group_by=product&channel=online" \
  -H "Authorization: Bearer <token>"
```

**Python Example:**
```python
import requests
import pandas as pd

def get_monthly_trends(start_date, end_date):
    """Fetch monthly sales trends as pandas DataFrame"""
    response = requests.get(
        "https://api.taskifai.com/api/analytics/sales/summary",
        params={
            "group_by": "month",
            "start_date": start_date,
            "end_date": end_date,
            "channel": "all"
        },
        headers={"Authorization": f"Bearer {jwt_token}"}
    )

    data = response.json()
    df = pd.DataFrame(data)
    df['month'] = pd.to_datetime(df['dimension'])

    return df

# Usage
trends = get_monthly_trends('2025-01-01', '2025-10-18')
print(trends[['month', 'total_revenue', 'total_units']])
```

**JavaScript Example:**
```javascript
import axios from 'axios';

async function getTopProducts(limit = 10) {
  const { data } = await axios.get('/api/analytics/sales/summary', {
    params: {
      group_by: 'product',
      channel: 'all'
    },
    headers: { Authorization: `Bearer ${token}` }
  });

  return data.slice(0, limit);
}

// Usage
const topProducts = await getTopProducts(10);
topProducts.forEach((product, index) => {
  console.log(`${index + 1}. ${product.dimension}: €${product.total_revenue.toFixed(2)}`);
});
```

---

### POST /api/analytics/export

Export sales report asynchronously (queued for background processing).

**Endpoint:** `POST /api/analytics/export`

#### Request Body

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `format` | string | No | `pdf` | Export format: `pdf`, `csv`, or `excel` |
| `channel` | string | No | `all` | Channel filter |
| `start_date` | date | No | - | Start of date range |
| `end_date` | date | No | - | End of date range |
| `reseller` | string | No | - | Reseller filter |
| `product` | string | No | - | Product filter |

#### Response

**Status Code:** `202 ACCEPTED`

```json
{
  "task_id": "report_user123_1729267200",
  "status": "queued",
  "message": "Report generation queued. PDF report will be sent to user@example.com when ready."
}
```

#### Background Processing

1. **Task Queued:** Request returns immediately with `task_id`
2. **Report Generation:** Celery worker processes in background
3. **Email Delivery:** Report sent to user's email when ready
4. **Typical Processing Time:** 30 seconds to 5 minutes depending on data volume

#### Supported Formats

**PDF:**
- Professional formatted report
- Charts and visualizations
- Summary statistics
- Detailed transaction tables

**CSV:**
- Raw sales data
- All columns included
- UTF-8 encoding
- Compatible with Excel, Google Sheets

**Excel:**
- XLSX format
- Multiple sheets (summary + detailed data)
- Formatted tables with headers
- Formulas for totals

#### Example Requests

**Export PDF report for last month:**
```bash
curl -X POST "https://api.taskifai.com/api/analytics/export" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "pdf",
    "channel": "all",
    "start_date": "2025-09-01",
    "end_date": "2025-09-30"
  }'
```

**Export CSV for specific product:**
```bash
curl -X POST "https://api.taskifai.com/api/analytics/export" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "product": "serum"
  }'
```

**Python Example:**
```python
import requests

def export_report(format='pdf', filters=None):
    """Queue report export"""
    payload = {
        "format": format,
        "channel": filters.get('channel', 'all'),
        "start_date": filters.get('start_date'),
        "end_date": filters.get('end_date'),
        "reseller": filters.get('reseller'),
        "product": filters.get('product')
    }

    response = requests.post(
        "https://api.taskifai.com/api/analytics/export",
        json=payload,
        headers={"Authorization": f"Bearer {jwt_token}"}
    )

    result = response.json()
    print(f"Report queued: {result['task_id']}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")

    return result['task_id']

# Usage
task_id = export_report(
    format='excel',
    filters={
        'channel': 'online',
        'start_date': '2025-10-01',
        'end_date': '2025-10-18'
    }
)
```

**JavaScript Example:**
```javascript
import axios from 'axios';

async function exportReport(format, filters = {}) {
  const { data } = await axios.post('/api/analytics/export', {
    format: format || 'pdf',
    channel: filters.channel || 'all',
    start_date: filters.startDate,
    end_date: filters.endDate,
    reseller: filters.reseller,
    product: filters.product
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });

  console.log(`Report queued: ${data.task_id}`);
  console.log(`Status: ${data.status}`);

  return data.task_id;
}

// Usage
const taskId = await exportReport('excel', {
  channel: 'all',
  startDate: '2025-10-01',
  endDate: '2025-10-18'
});
```

---

### GET /api/analytics/export/{format}

Generate and download report immediately (synchronous).

**Endpoint:** `GET /api/analytics/export/{format}`

**Path Parameters:**
- `format`: Export format (`pdf`, `csv`, or `excel`)

#### Query Parameters

Same as POST `/api/analytics/export` (excluding format).

#### Response

**Status Code:** `200 OK`

**Headers:**
```http
Content-Type: application/pdf | text/csv | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="sales_report_2025-10-18.pdf"
```

**Body:** Binary file content

#### File Naming Convention

- PDF: `sales_report_{date}.pdf`
- CSV: `sales_report_{date}.csv`
- Excel: `sales_report_{date}.xlsx`

Where `{date}` is ISO 8601 date (YYYY-MM-DD)

#### Example Requests

**Download PDF report:**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/export/pdf?start_date=2025-10-01&end_date=2025-10-18" \
  -H "Authorization: Bearer <token>" \
  -o sales_report.pdf
```

**Download CSV:**
```bash
curl -X GET "https://api.taskifai.com/api/analytics/export/csv?channel=online" \
  -H "Authorization: Bearer <token>" \
  -o sales_data.csv
```

**Python Example:**
```python
import requests

def download_report(format='pdf', output_path=None, filters=None):
    """Download report immediately"""
    params = {
        "channel": filters.get('channel', 'all'),
        "start_date": filters.get('start_date'),
        "end_date": filters.get('end_date'),
        "reseller": filters.get('reseller'),
        "product": filters.get('product')
    }

    response = requests.get(
        f"https://api.taskifai.com/api/analytics/export/{format}",
        params=params,
        headers={"Authorization": f"Bearer {jwt_token}"},
        stream=True
    )

    # Extract filename from Content-Disposition header
    content_disp = response.headers.get('Content-Disposition', '')
    filename = content_disp.split('filename=')[1].strip('"') if 'filename=' in content_disp else f"report.{format}"

    output_path = output_path or filename

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Report downloaded: {output_path}")
    return output_path

# Usage
download_report(
    format='excel',
    output_path='sales_october_2025.xlsx',
    filters={
        'start_date': '2025-10-01',
        'end_date': '2025-10-18'
    }
)
```

**JavaScript Example (Browser):**
```javascript
import axios from 'axios';

async function downloadReport(format, filters = {}) {
  const response = await axios.get(`/api/analytics/export/${format}`, {
    params: {
      channel: filters.channel || 'all',
      start_date: filters.startDate,
      end_date: filters.endDate,
      reseller: filters.reseller,
      product: filters.product
    },
    headers: { Authorization: `Bearer ${token}` },
    responseType: 'blob'
  });

  // Extract filename from Content-Disposition header
  const contentDisp = response.headers['content-disposition'];
  const filename = contentDisp
    ? contentDisp.split('filename=')[1].replace(/"/g, '')
    : `sales_report.${format}`;

  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// Usage
await downloadReport('pdf', {
  startDate: '2025-10-01',
  endDate: '2025-10-18',
  channel: 'online'
});
```

---

## Data Models

### KPI Response

```typescript
interface KPIResponse {
  total_revenue: number;
  total_units: number;
  avg_price: number;
  average_order_value: number;
  total_uploads: number;
  gross_profit: number;
  profit_margin: number;
  unique_countries: number;
  order_count: number;
  offline: OfflineKPIs;
  online: OnlineKPIs;
  top_products: Product[];
  date_range: DateRange;
}

interface OfflineKPIs {
  transaction_count: number;
  total_revenue: number;
  total_units: number;
  avg_transaction_value: number;
  unique_resellers: number;
  unique_products: number;
}

interface OnlineKPIs {
  order_count: number;
  total_revenue: number;
  total_units: number;
  avg_order_value: number;
  total_cogs: number;
  total_fees: number;
  gross_profit: number;
  profit_margin: number;
  unique_countries: number;
}

interface Product {
  product_name: string;
  product_ean: string;
  revenue: number;
  units: number;
  transactions: number;
  channel: 'online' | 'offline';
}

interface DateRange {
  start: string | null;  // ISO 8601 date
  end: string | null;    // ISO 8601 date
}
```

### Sales Data Response

```typescript
interface SalesDataResponse {
  data: SalesRecord[];
  pagination: Pagination;
  filters_applied: FiltersApplied;
  summary: SalesSummary;
}

interface SalesRecord {
  sale_id: string;
  order_date: string;  // ISO 8601 date
  product_name: string;
  product_ean: string;
  functional_name: string;
  quantity: number;
  sales_eur: number;
  channel: 'online' | 'offline';
  country: string | null;
  reseller: string | null;
  cost_of_goods: number | null;
  stripe_fee: number | null;
  profit: number | null;
}

interface Pagination {
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

interface FiltersApplied {
  channel: string;
  start_date: string | null;
  end_date: string | null;
  reseller: string | null;
  product: string | null;
  country: string | null;
}

interface SalesSummary {
  total_revenue: number;
  total_units: number;
  average_price: number;
}
```

### Summary Response

```typescript
type SummaryResponse = MonthSummary[] | ProductSummary[] | ResellerSummary[] | CountrySummary[];

interface MonthSummary {
  dimension: string;  // YYYY-MM format
  total_revenue: number;
  total_units: number;
  average_price: number;
  transaction_count: number;
  channels: {
    online: number;
    offline: number;
  };
}

interface ProductSummary {
  dimension: string;  // Product name
  product_ean: string;
  total_revenue: number;
  total_units: number;
  average_price: number;
  transaction_count: number;
}

interface ResellerSummary {
  dimension: string;  // Reseller name
  reseller_id: string;
  total_revenue: number;
  total_units: number;
  average_price: number;
  transaction_count: number;
  country: string;
}

interface CountrySummary {
  dimension: string;  // Country name
  total_revenue: number;
  total_units: number;
  average_price: number;
  transaction_count: number;
}
```

---

## Filtering & Aggregation

### Channel Filtering

**Behavior:**
- `offline`: Queries `sellout_entries2` table only
- `online`: Queries `ecommerce_orders` table only
- `all`: Combines results from both tables

**Use Cases:**
- `offline`: B2B sales analysis, reseller performance
- `online`: D2C sales, country-specific analysis, profit margins
- `all`: Complete business overview, combined KPIs

### Date Range Filtering

**Online Sales (ecommerce_orders):**
- Uses `order_date` column (DATE type)
- Supports exact date matching
- Filters with `>= start_date AND <= end_date`

**Offline Sales (sellout_entries2):**
- Uses `month` and `year` columns (INTEGER types)
- Month-level granularity only
- Filters by comparing constructed date

**Best Practices:**
- Always provide both `start_date` and `end_date` or neither
- Use ISO 8601 format (YYYY-MM-DD)
- Consider time zones (all dates are UTC)

### Fuzzy Search

**Product Search:**
- Case-insensitive substring matching
- Searches `product_name` and `functional_name` columns
- Example: `product=serum` matches "Premium Face Serum", "SERUM_PREMIUM_50ML"

**Reseller Search:**
- Case-insensitive substring matching
- Searches `reseller` column (offline only)
- Example: `reseller=galilu` matches "Galilu Beauty (Poland)"

### Aggregation Functions

**Revenue:**
- `SUM(sales_eur)` across all transactions
- Currency: EUR (hardcoded)

**Units:**
- `SUM(quantity)` across all transactions

**Average Price:**
- Calculated as `total_revenue / total_units`
- Not averaged across transactions (weighted by quantity)

**Profit (Online Only):**
- Formula: `sales_eur - cost_of_goods - stripe_fee`
- Profit Margin: `(profit / sales_eur) * 100`

---

## Code Examples

### Complete Python Analytics Client

```python
import requests
from datetime import date, timedelta
from typing import Optional, Dict, Any, List

class TaskifAIAnalytics:
    """Python client for TaskifAI Analytics API"""

    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.headers = {"Authorization": f"Bearer {jwt_token}"}

    def get_kpis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get KPIs"""
        params = {}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        if channel:
            params['channel'] = channel

        response = requests.get(
            f"{self.base_url}/api/analytics/kpis",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_sales(
        self,
        channel: str = 'all',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        reseller: Optional[str] = None,
        product: Optional[str] = None,
        country: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Get sales data with filters"""
        params = {
            'channel': channel,
            'page': page,
            'page_size': page_size
        }
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        if reseller:
            params['reseller'] = reseller
        if product:
            params['product'] = product
        if country:
            params['country'] = country

        response = requests.get(
            f"{self.base_url}/api/analytics/sales",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_summary(
        self,
        group_by: str = 'month',
        channel: str = 'all',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get aggregated summary"""
        params = {
            'group_by': group_by,
            'channel': channel
        }
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()

        response = requests.get(
            f"{self.base_url}/api/analytics/sales/summary",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def export_report(
        self,
        format: str = 'pdf',
        channel: str = 'all',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        reseller: Optional[str] = None,
        product: Optional[str] = None
    ) -> str:
        """Queue report export (returns task_id)"""
        payload = {'format': format, 'channel': channel}
        if start_date:
            payload['start_date'] = start_date.isoformat()
        if end_date:
            payload['end_date'] = end_date.isoformat()
        if reseller:
            payload['reseller'] = reseller
        if product:
            payload['product'] = product

        response = requests.post(
            f"{self.base_url}/api/analytics/export",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['task_id']

    def download_report(
        self,
        format: str,
        output_path: str,
        channel: str = 'all',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        reseller: Optional[str] = None,
        product: Optional[str] = None
    ):
        """Download report immediately"""
        params = {'channel': channel}
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        if reseller:
            params['reseller'] = reseller
        if product:
            params['product'] = product

        response = requests.get(
            f"{self.base_url}/api/analytics/export/{format}",
            params=params,
            headers=self.headers,
            stream=True
        )
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path

# Usage example
if __name__ == "__main__":
    client = TaskifAIAnalytics(
        base_url="https://api.taskifai.com",
        jwt_token="your_jwt_token_here"
    )

    # Get KPIs for last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    kpis = client.get_kpis(start_date=start_date, end_date=end_date)
    print(f"Total Revenue: €{kpis['total_revenue']:,.2f}")
    print(f"Profit Margin: {kpis['profit_margin']:.2f}%")

    # Get top products
    summary = client.get_summary(group_by='product', channel='online')
    print("\nTop 5 Products:")
    for i, product in enumerate(summary[:5], 1):
        print(f"{i}. {product['dimension']}: €{product['total_revenue']:,.2f}")

    # Download monthly report
    client.download_report(
        format='excel',
        output_path='monthly_report.xlsx',
        start_date=start_date,
        end_date=end_date
    )
    print("\nReport downloaded: monthly_report.xlsx")
```

### Complete JavaScript/TypeScript Client

```typescript
import axios, { AxiosInstance } from 'axios';

interface KPIResponse {
  total_revenue: number;
  total_units: number;
  avg_price: number;
  profit_margin: number;
  // ... (see Data Models section)
}

interface SalesDataResponse {
  data: SalesRecord[];
  pagination: Pagination;
  summary: SalesSummary;
}

interface SummaryItem {
  dimension: string;
  total_revenue: number;
  total_units: number;
  average_price: number;
  transaction_count: number;
}

class TaskifAIAnalytics {
  private client: AxiosInstance;

  constructor(baseURL: string, jwtToken: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        Authorization: `Bearer ${jwtToken}`
      }
    });
  }

  async getKPIs(params?: {
    startDate?: string;
    endDate?: string;
    channel?: string;
  }): Promise<KPIResponse> {
    const { data } = await this.client.get('/api/analytics/kpis', {
      params: {
        start_date: params?.startDate,
        end_date: params?.endDate,
        channel: params?.channel
      }
    });
    return data;
  }

  async getSales(params?: {
    channel?: string;
    startDate?: string;
    endDate?: string;
    reseller?: string;
    product?: string;
    country?: string;
    page?: number;
    pageSize?: number;
  }): Promise<SalesDataResponse> {
    const { data } = await this.client.get('/api/analytics/sales', {
      params: {
        channel: params?.channel || 'all',
        start_date: params?.startDate,
        end_date: params?.endDate,
        reseller: params?.reseller,
        product: params?.product,
        country: params?.country,
        page: params?.page || 1,
        page_size: params?.pageSize || 50
      }
    });
    return data;
  }

  async getSummary(params?: {
    groupBy?: string;
    channel?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<SummaryItem[]> {
    const { data } = await this.client.get('/api/analytics/sales/summary', {
      params: {
        group_by: params?.groupBy || 'month',
        channel: params?.channel || 'all',
        start_date: params?.startDate,
        end_date: params?.endDate
      }
    });
    return data;
  }

  async exportReport(params: {
    format?: string;
    channel?: string;
    startDate?: string;
    endDate?: string;
    reseller?: string;
    product?: string;
  }): Promise<string> {
    const { data } = await this.client.post('/api/analytics/export', {
      format: params.format || 'pdf',
      channel: params.channel || 'all',
      start_date: params.startDate,
      end_date: params.endDate,
      reseller: params.reseller,
      product: params.product
    });
    return data.task_id;
  }

  async downloadReport(
    format: string,
    params?: {
      channel?: string;
      startDate?: string;
      endDate?: string;
      reseller?: string;
      product?: string;
    }
  ): Promise<Blob> {
    const { data } = await this.client.get(`/api/analytics/export/${format}`, {
      params: {
        channel: params?.channel || 'all',
        start_date: params?.startDate,
        end_date: params?.endDate,
        reseller: params?.reseller,
        product: params?.product
      },
      responseType: 'blob'
    });
    return data;
  }
}

// Usage example
async function main() {
  const client = new TaskifAIAnalytics(
    'https://api.taskifai.com',
    'your_jwt_token_here'
  );

  // Get KPIs for last 30 days
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    .toISOString().split('T')[0];

  const kpis = await client.getKPIs({ startDate, endDate });
  console.log(`Total Revenue: €${kpis.total_revenue.toLocaleString()}`);
  console.log(`Profit Margin: ${kpis.profit_margin.toFixed(2)}%`);

  // Get top products
  const summary = await client.getSummary({
    groupBy: 'product',
    channel: 'online'
  });
  console.log('\nTop 5 Products:');
  summary.slice(0, 5).forEach((product, index) => {
    console.log(`${index + 1}. ${product.dimension}: €${product.total_revenue.toFixed(2)}`);
  });

  // Download report
  const reportBlob = await client.downloadReport('excel', { startDate, endDate });
  console.log(`\nReport downloaded: ${reportBlob.size} bytes`);
}
```

---

## Best Practices

### Performance Optimization

**Use Appropriate Page Sizes:**
- Small dashboards: `page_size=20-50`
- Data exports: `page_size=100` (maximum)
- Avoid fetching all data at once for large datasets

**Cache KPI Results:**
- KPIs are expensive to calculate
- Cache results for 5-15 minutes on client side
- Use ETags or Last-Modified headers if available

**Limit Date Ranges:**
- Shorter date ranges = faster queries
- Consider pagination for large date ranges
- Use summary endpoint for historical trends instead of fetching all records

### Error Handling

**Common Errors:**

**400 Bad Request:**
- Invalid date format
- Invalid `group_by` or `channel` parameter
- Invalid `format` for exports

**401 Unauthorized:**
- Missing or expired JWT token
- Solution: Refresh token and retry

**500 Internal Server Error:**
- Database connection issues
- Query timeout (large datasets)
- Solution: Reduce date range, add filters, contact support

**Example Error Response:**
```json
{
  "detail": "Invalid group_by parameter. Must be one of: month, product, reseller, country"
}
```

### Data Consistency

**Multi-Table Queries:**
- Online and offline data may have different update frequencies
- Online data is real-time
- Offline data may be uploaded in batches

**Currency:**
- All amounts in EUR
- Exchange rate conversions happen before data upload
- Historical rates not stored

**Time Zones:**
- All dates stored in UTC
- Convert to local time zone on client side
- Be consistent with date range boundaries

### Security Considerations

**Data Access:**
- All endpoints enforce `user_id` filtering automatically
- Users can only see their own sales data
- JWT token must be valid and not expired

**Rate Limiting:**
- Consider implementing client-side rate limiting
- Large exports may take longer during high load
- Use async export endpoint for large datasets

**Data Privacy:**
- Do not log or cache sensitive sales data
- Clear report files after download
- Use HTTPS for all API calls

---

## Related Documentation

- [Authentication API](./authentication.md) - JWT token generation and management
- [Upload API](./uploads.md) - Data upload and processing
- [AI Chat API](./chat.md) - Natural language analytics queries
- [Database Schema](../reference/database-schema.md) - Table structures and relationships
- [RLS Policies](../reference/rls-policies.md) - Security and data isolation

---

## Support

For questions or issues with the Analytics API:

- **Documentation:** [docs.taskifai.com](https://docs.taskifai.com)
- **Support Email:** support@taskifai.com
- **GitHub Issues:** [github.com/taskifai/platform/issues](https://github.com/taskifai/platform/issues)

---

**Last Updated:** 2025-10-18
**API Version:** 2.0
**Status:** Production
