# External Dashboard Integration API

## Overview

The External Dashboard Integration API enables users to embed external Business Intelligence (BI) dashboards from platforms like Looker, Tableau, Power BI, Metabase, and custom solutions directly into the TaskifAI platform. This system provides secure credential management with encryption, URL validation, and iframe-safe embedding configurations.

**Key Features:**
- Support for multiple BI platforms (Looker, Tableau, Power BI, Metabase, Custom)
- Secure credential encryption using pgcrypto
- URL validation with security checks
- Primary dashboard management (one active dashboard per user)
- Iframe-safe embed URL generation
- Authentication method configuration (Bearer Token, API Key, OAuth, None)

**Base URL:** `/api/dashboards`

**Authentication:** Required (JWT Bearer Token)

---

## Dashboard Types

The system supports these dashboard platforms:

| Type | Description | Common Providers |
|------|-------------|------------------|
| `looker` | Looker dashboards with embed support | Looker Cloud, Looker (Google Cloud core) |
| `tableau` | Tableau Server or Tableau Online | Tableau Server, Tableau Cloud |
| `powerbi` | Microsoft Power BI embedded reports | Power BI Embedded, Power BI Cloud |
| `metabase` | Metabase open-source BI | Self-hosted Metabase, Metabase Cloud |
| `custom` | Custom dashboard solutions | Any HTML/JavaScript dashboard |

---

## Authentication Methods

Dashboards can use various authentication methods:

| Method | Description | Use Case |
|--------|-------------|----------|
| `none` | No authentication required | Public dashboards |
| `bearer_token` | JWT Bearer token authentication | API-based dashboards |
| `api_key` | API key header authentication | SaaS BI platforms |
| `oauth` | OAuth 2.0 authentication flow | Enterprise dashboards |

**Security Note:** All authentication credentials are encrypted at rest using PostgreSQL's `pgcrypto` extension.

---

## Endpoints

### 1. Create Dashboard

Create a new external dashboard configuration with encrypted credentials.

**Endpoint:** `POST /api/dashboards`

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dashboard_name` | string | Yes | Display name for dashboard (1-255 chars) |
| `dashboard_type` | string | Yes | Dashboard platform type (looker, tableau, powerbi, metabase, custom) |
| `dashboard_url` | string | Yes | Full URL to embed (must be HTTPS in production) |
| `authentication_method` | string | No | Auth method (none, bearer_token, api_key, oauth) - default: none |
| `authentication_config` | object | No | Auth credentials (will be encrypted) |
| `permissions` | string[] | No | User permissions for this dashboard |
| `is_active` | boolean | No | Set as primary dashboard - default: false |

**Authentication Config Structure:**

**Bearer Token:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "header_name": "Authorization"
}
```

**API Key:**
```json
{
  "api_key": "sk_live_abc123...",
  "header_name": "X-API-Key"
}
```

**OAuth:**
```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "token_url": "https://provider.com/oauth/token",
  "refresh_token": "refresh_token_value"
}
```

**URL Validation Rules:**

1. Must be valid HTTPS URL (HTTP allowed in development only)
2. Cannot use localhost/127.0.0.1 in production
3. No malicious patterns (javascript:, data:, <script>, etc.)
4. Optional domain whitelist enforcement
5. Provider-specific validation (e.g., Looker URLs must contain "looker")

#### Example Requests

**cURL:**

```bash
curl -X POST "https://api.taskifai.com/api/dashboards" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "Sales Analytics",
    "dashboard_type": "looker",
    "dashboard_url": "https://company.looker.com/dashboards/123",
    "authentication_method": "bearer_token",
    "authentication_config": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "header_name": "Authorization"
    },
    "is_active": true
  }'
```

**Python:**

```python
import requests

url = "https://api.taskifai.com/api/dashboards"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "dashboard_name": "Sales Analytics",
    "dashboard_type": "looker",
    "dashboard_url": "https://company.looker.com/dashboards/123",
    "authentication_method": "bearer_token",
    "authentication_config": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "header_name": "Authorization"
    },
    "is_active": True
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 201:
    dashboard = response.json()
    print(f"Created dashboard: {dashboard['config_id']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const createDashboard = async () => {
  const response = await fetch('https://api.taskifai.com/api/dashboards', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      dashboard_name: 'Sales Analytics',
      dashboard_type: 'looker',
      dashboard_url: 'https://company.looker.com/dashboards/123',
      authentication_method: 'bearer_token',
      authentication_config: {
        token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        header_name: 'Authorization'
      },
      is_active: true
    })
  });

  if (response.ok) {
    const dashboard = await response.json();
    console.log('Created dashboard:', dashboard.config_id);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `201 Created`

```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "dashboard_name": "Sales Analytics",
  "dashboard_type": "looker",
  "dashboard_url": "https://company.looker.com/dashboards/123",
  "authentication_method": "bearer_token",
  "authentication_config": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "header_name": "Authorization"
  },
  "permissions": [],
  "is_active": true,
  "is_primary": true,
  "created_at": "2025-10-18T10:30:00Z",
  "updated_at": "2025-10-18T10:30:00Z"
}
```

#### Error Responses

**400 Bad Request - Invalid URL:**

```json
{
  "detail": "Invalid dashboard URL: URL must start with https://"
}
```

**400 Bad Request - Localhost in Production:**

```json
{
  "detail": "Invalid dashboard URL: Localhost URLs are not allowed in production"
}
```

**400 Bad Request - Malicious Pattern:**

```json
{
  "detail": "Invalid dashboard URL: Malicious pattern detected: javascript:"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to create dashboard: Database connection error"
}
```

---

### 2. List Dashboards

Retrieve all dashboard configurations for the authenticated user, with primary dashboard first.

**Endpoint:** `GET /api/dashboards`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Pagination offset |
| `limit` | integer | 50 | Number of dashboards to return (max 100) |

#### Example Requests

**cURL:**

```bash
curl -X GET "https://api.taskifai.com/api/dashboards?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

url = "https://api.taskifai.com/api/dashboards"
headers = {"Authorization": f"Bearer {jwt_token}"}
params = {"skip": 0, "limit": 10}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['total']} dashboards")
    for dashboard in data['dashboards']:
        print(f"- {dashboard['dashboard_name']} ({'Primary' if dashboard['is_primary'] else 'Secondary'})")
else:
    print(f"Error: {response.status_code}")
```

**JavaScript:**

```javascript
const listDashboards = async (skip = 0, limit = 10) => {
  const url = new URL('https://api.taskifai.com/api/dashboards');
  url.searchParams.append('skip', skip);
  url.searchParams.append('limit', limit);

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    }
  });

  if (response.ok) {
    const data = await response.json();
    console.log(`Found ${data.total} dashboards`);
    data.dashboards.forEach(dashboard => {
      console.log(`- ${dashboard.dashboard_name} (${dashboard.is_primary ? 'Primary' : 'Secondary'})`);
    });
  } else {
    console.error('Error:', response.status);
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "dashboards": [
    {
      "config_id": "550e8400-e29b-41d4-a716-446655440000",
      "dashboard_name": "Sales Analytics",
      "dashboard_type": "looker",
      "dashboard_url": "https://company.looker.com/dashboards/123",
      "authentication_method": "bearer_token",
      "authentication_config": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "header_name": "Authorization"
      },
      "permissions": ["view", "export"],
      "is_active": true,
      "is_primary": true,
      "created_at": "2025-10-18T10:30:00Z",
      "updated_at": "2025-10-18T10:30:00Z"
    },
    {
      "config_id": "660e8400-e29b-41d4-a716-446655440001",
      "dashboard_name": "Marketing Metrics",
      "dashboard_type": "tableau",
      "dashboard_url": "https://tableau.company.com/views/marketing",
      "authentication_method": "api_key",
      "authentication_config": {
        "api_key": "sk_live_abc123...",
        "header_name": "X-API-Key"
      },
      "permissions": ["view"],
      "is_active": false,
      "is_primary": false,
      "created_at": "2025-10-17T14:20:00Z",
      "updated_at": "2025-10-17T14:20:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 50,
  "primary_dashboard": {
    "config_id": "550e8400-e29b-41d4-a716-446655440000",
    "dashboard_name": "Sales Analytics",
    "dashboard_type": "looker",
    "dashboard_url": "https://company.looker.com/dashboards/123",
    "authentication_method": "bearer_token",
    "authentication_config": {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "header_name": "Authorization"
    },
    "permissions": ["view", "export"],
    "is_active": true,
    "is_primary": true,
    "created_at": "2025-10-18T10:30:00Z",
    "updated_at": "2025-10-18T10:30:00Z"
  }
}
```

#### Error Responses

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to list dashboards: Database connection error"
}
```

---

### 3. Get Dashboard by ID

Retrieve detailed information for a specific dashboard configuration.

**Endpoint:** `GET /api/dashboards/{dashboard_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

#### Example Requests

**cURL:**

```bash
curl -X GET "https://api.taskifai.com/api/dashboards/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

dashboard_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"https://api.taskifai.com/api/dashboards/{dashboard_id}"
headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    dashboard = response.json()
    print(f"Dashboard: {dashboard['dashboard_name']}")
    print(f"Type: {dashboard['dashboard_type']}")
    print(f"Primary: {dashboard['is_primary']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const getDashboard = async (dashboardId) => {
  const response = await fetch(
    `https://api.taskifai.com/api/dashboards/${dashboardId}`,
    {
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.ok) {
    const dashboard = await response.json();
    console.log('Dashboard:', dashboard.dashboard_name);
    console.log('Type:', dashboard.dashboard_type);
    console.log('Primary:', dashboard.is_primary);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "dashboard_name": "Sales Analytics",
  "dashboard_type": "looker",
  "dashboard_url": "https://company.looker.com/dashboards/123",
  "authentication_method": "bearer_token",
  "authentication_config": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "header_name": "Authorization"
  },
  "permissions": ["view", "export"],
  "is_active": true,
  "is_primary": true,
  "created_at": "2025-10-18T10:30:00Z",
  "updated_at": "2025-10-18T10:30:00Z"
}
```

#### Error Responses

**404 Not Found:**

```json
{
  "detail": "Dashboard not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to get dashboard: Database error"
}
```

---

### 4. Update Dashboard

Update an existing dashboard configuration. Only provided fields will be updated.

**Endpoint:** `PUT /api/dashboards/{dashboard_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

**Request Body:**

All fields are optional. Only include fields you want to update.

| Field | Type | Description |
|-------|------|-------------|
| `dashboard_name` | string | Updated display name |
| `dashboard_type` | string | Updated dashboard type |
| `dashboard_url` | string | Updated embed URL (will be validated) |
| `authentication_method` | string | Updated auth method |
| `authentication_config` | object | Updated auth credentials (will be encrypted) |
| `permissions` | string[] | Updated permissions |
| `is_active` | boolean | Enable/disable dashboard |

#### Example Requests

**cURL:**

```bash
curl -X PUT "https://api.taskifai.com/api/dashboards/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "Updated Sales Dashboard",
    "is_active": false
  }'
```

**Python:**

```python
import requests

dashboard_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"https://api.taskifai.com/api/dashboards/{dashboard_id}"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "dashboard_name": "Updated Sales Dashboard",
    "is_active": False
}

response = requests.put(url, json=payload, headers=headers)

if response.status_code == 200:
    dashboard = response.json()
    print(f"Updated dashboard: {dashboard['dashboard_name']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const updateDashboard = async (dashboardId, updates) => {
  const response = await fetch(
    `https://api.taskifai.com/api/dashboards/${dashboardId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${jwtToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );

  if (response.ok) {
    const dashboard = await response.json();
    console.log('Updated dashboard:', dashboard.dashboard_name);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};

// Example usage
updateDashboard('550e8400-e29b-41d4-a716-446655440000', {
  dashboard_name: 'Updated Sales Dashboard',
  is_active: false
});
```

#### Success Response

**Status:** `200 OK`

```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "dashboard_name": "Updated Sales Dashboard",
  "dashboard_type": "looker",
  "dashboard_url": "https://company.looker.com/dashboards/123",
  "authentication_method": "bearer_token",
  "authentication_config": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "header_name": "Authorization"
  },
  "permissions": ["view", "export"],
  "is_active": false,
  "is_primary": false,
  "created_at": "2025-10-18T10:30:00Z",
  "updated_at": "2025-10-18T11:45:00Z"
}
```

#### Error Responses

**400 Bad Request - Invalid URL:**

```json
{
  "detail": "Invalid dashboard URL: URL must start with https://"
}
```

**404 Not Found:**

```json
{
  "detail": "Dashboard not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to update dashboard: Database error"
}
```

---

### 5. Delete Dashboard

Permanently delete a dashboard configuration.

**Endpoint:** `DELETE /api/dashboards/{dashboard_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

#### Example Requests

**cURL:**

```bash
curl -X DELETE "https://api.taskifai.com/api/dashboards/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

dashboard_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"https://api.taskifai.com/api/dashboards/{dashboard_id}"
headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.delete(url, headers=headers)

if response.status_code == 204:
    print("Dashboard deleted successfully")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const deleteDashboard = async (dashboardId) => {
  const response = await fetch(
    `https://api.taskifai.com/api/dashboards/${dashboardId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.status === 204) {
    console.log('Dashboard deleted successfully');
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `204 No Content`

No response body.

#### Error Responses

**404 Not Found:**

```json
{
  "detail": "Dashboard not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to delete dashboard: Database error"
}
```

---

### 6. Set Primary Dashboard

Set a dashboard as the primary (active) dashboard. Only one dashboard can be primary at a time.

**Endpoint:** `PATCH /api/dashboards/{dashboard_id}/primary`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

**Behavior:**
- Sets `is_active=true` for the specified dashboard
- Automatically sets `is_active=false` for all other user dashboards
- Returns the updated dashboard configuration

#### Example Requests

**cURL:**

```bash
curl -X PATCH "https://api.taskifai.com/api/dashboards/550e8400-e29b-41d4-a716-446655440000/primary" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

dashboard_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"https://api.taskifai.com/api/dashboards/{dashboard_id}/primary"
headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.patch(url, headers=headers)

if response.status_code == 200:
    dashboard = response.json()
    print(f"Set {dashboard['dashboard_name']} as primary")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const setPrimaryDashboard = async (dashboardId) => {
  const response = await fetch(
    `https://api.taskifai.com/api/dashboards/${dashboardId}/primary`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.ok) {
    const dashboard = await response.json();
    console.log(`Set ${dashboard.dashboard_name} as primary`);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "dashboard_name": "Sales Analytics",
  "dashboard_type": "looker",
  "dashboard_url": "https://company.looker.com/dashboards/123",
  "authentication_method": "bearer_token",
  "authentication_config": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "header_name": "Authorization"
  },
  "permissions": ["view", "export"],
  "is_active": true,
  "is_primary": true,
  "created_at": "2025-10-18T10:30:00Z",
  "updated_at": "2025-10-18T12:00:00Z"
}
```

#### Error Responses

**404 Not Found:**

```json
{
  "detail": "Dashboard not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to set primary dashboard: Database error"
}
```

---

### 7. Get Embed URL

Generate a secure embed URL with authentication for iframe display.

**Endpoint:** `POST /api/dashboards/embed`

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

**Response includes:**
- Embed-ready URL with authentication
- Dashboard metadata
- Recommended iframe sandbox attributes

#### Example Requests

**cURL:**

```bash
curl -X POST "https://api.taskifai.com/api/dashboards/embed" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Python:**

```python
import requests

url = "https://api.taskifai.com/api/dashboards/embed"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "dashboard_id": "550e8400-e29b-41d4-a716-446655440000"
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    embed_data = response.json()
    print(f"Embed URL: {embed_data['embed_url']}")
    print(f"Requires auth: {embed_data['requires_auth']}")
    print(f"Sandbox attributes: {', '.join(embed_data['sandbox_attributes'])}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const getEmbedUrl = async (dashboardId) => {
  const response = await fetch('https://api.taskifai.com/api/dashboards/embed', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      dashboard_id: dashboardId
    })
  });

  if (response.ok) {
    const embedData = await response.json();
    console.log('Embed URL:', embedData.embed_url);
    console.log('Requires auth:', embedData.requires_auth);

    // Create iframe
    const iframe = document.createElement('iframe');
    iframe.src = embedData.embed_url;
    iframe.sandbox = embedData.sandbox_attributes.join(' ');
    iframe.width = '100%';
    iframe.height = '600px';

    document.getElementById('dashboard-container').appendChild(iframe);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "embed_url": "https://company.looker.com/embed/dashboards/123?embed_domain=taskifai.com&auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "dashboard_name": "Sales Analytics",
  "dashboard_type": "looker",
  "requires_auth": true,
  "sandbox_attributes": [
    "allow-scripts",
    "allow-same-origin",
    "allow-forms",
    "allow-popups",
    "allow-downloads"
  ]
}
```

**Embed URL Transformation Examples:**

**Looker:**
- Original: `https://company.looker.com/dashboards/123`
- Embed: `https://company.looker.com/embed/dashboards/123`

**Tableau:**
- Original: `https://tableau.company.com/views/dashboard`
- Embed: `https://tableau.company.com/views/dashboard?:embed=y&:showVizHome=no`

**Power BI:**
- Original: `https://app.powerbi.com/view?r=abc123`
- Embed: Same (no transformation needed)

#### Error Responses

**404 Not Found:**

```json
{
  "detail": "Dashboard not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to get embed URL: Configuration error"
}
```

---

## Dynamic Dashboard Configuration API

The Dynamic Dashboard Configuration API allows users to customize their dashboard layout, KPIs, widgets, and filters. This is separate from the External Dashboard Integration and manages the internal TaskifAI dashboard experience.

**Base URL:** `/api/dashboard-configs`

**Authentication:** Required (JWT Bearer Token)

---

### Dashboard Configuration Concepts

#### Widget Types

| Widget Type | Description | Use Case |
|------------|-------------|----------|
| `kpi_grid` | Grid of KPI metrics | Overview statistics |
| `recent_uploads` | Recent file uploads | Upload history |
| `top_products` | Best-selling products | Product performance |
| `reseller_performance` | Reseller metrics | B2B analytics |
| `category_revenue` | Revenue by category | Category analysis |
| `revenue_chart` | Revenue over time | Trend analysis |
| `sales_trend` | Sales trend line chart | Sales forecasting |

#### KPI Types

| KPI Type | Description | Data Source |
|----------|-------------|-------------|
| `total_revenue` | Total sales revenue | ecommerce_orders |
| `total_units` | Total units sold | ecommerce_orders |
| `avg_price` | Average selling price | ecommerce_orders |
| `total_uploads` | Total file uploads | upload_batches |
| `gross_profit` | Total gross profit | ecommerce_orders |
| `profit_margin` | Profit margin % | ecommerce_orders |
| `unique_countries` | Countries with sales | ecommerce_orders |
| `order_count` | Total order count | ecommerce_orders |
| `reseller_count` | Active resellers | BIBBI resellers |
| `category_mix` | Category distribution | ecommerce_orders |
| `yoy_growth` | Year-over-year growth | ecommerce_orders |
| `top_products` | Top 10 products | ecommerce_orders |

#### Dashboard Filters

Dashboards support these default filters:

**Date Ranges:**
- `last_7_days`, `last_14_days`, `last_30_days`
- `last_60_days`, `last_90_days`, `last_180_days`, `last_365_days`
- `this_month`, `last_month`
- `this_quarter`, `last_quarter`
- `this_year`, `last_year`
- `all_time`

**Other Filters:**
- `vendor`: Filter by vendor (default: "all")
- `category`: Filter by product category (optional)
- `reseller`: Filter by reseller (BIBBI only, optional)

---

### 8. Get Default Dashboard Config

Retrieve the default dashboard configuration for the current user.

**Endpoint:** `GET /api/dashboard-configs/default`

**Authentication:** Required

**Priority Order:**
1. User's personal default (`is_default=true`, `user_id=current_user`)
2. Tenant-wide default (`is_default=true`, `user_id=NULL`)

#### Example Requests

**cURL:**

```bash
curl -X GET "https://api.taskifai.com/api/dashboard-configs/default" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

url = "https://api.taskifai.com/api/dashboard-configs/default"
headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    config = response.json()
    print(f"Dashboard: {config['dashboard_name']}")
    print(f"Widgets: {len(config['layout'])}")
    print(f"KPIs: {', '.join(config['kpis'])}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const getDefaultDashboard = async () => {
  const response = await fetch(
    'https://api.taskifai.com/api/dashboard-configs/default',
    {
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.ok) {
    const config = await response.json();
    console.log('Dashboard:', config.dashboard_name);
    console.log('Widgets:', config.layout.length);
    console.log('KPIs:', config.kpis.join(', '));
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": null,
  "dashboard_name": "Overview Dashboard",
  "description": "Real-time overview of sales performance",
  "layout": [
    {
      "id": "kpi-grid",
      "type": "kpi_grid",
      "position": {
        "row": 0,
        "col": 0,
        "width": 12,
        "height": 2
      },
      "props": {
        "title": "Key Metrics",
        "kpis": ["total_revenue", "total_units", "avg_price", "profit_margin"]
      }
    },
    {
      "id": "revenue-chart",
      "type": "revenue_chart",
      "position": {
        "row": 2,
        "col": 0,
        "width": 8,
        "height": 4
      },
      "props": {
        "title": "Revenue Trend",
        "chart_type": "area"
      }
    },
    {
      "id": "top-products",
      "type": "top_products",
      "position": {
        "row": 2,
        "col": 8,
        "width": 4,
        "height": 4
      },
      "props": {
        "title": "Top Products",
        "limit": 10
      }
    }
  ],
  "kpis": ["total_revenue", "total_units", "avg_price", "profit_margin"],
  "filters": {
    "date_range": "last_30_days",
    "vendor": "all",
    "category": null,
    "reseller": null
  },
  "is_default": true,
  "is_active": true,
  "display_order": 0,
  "created_at": "2025-10-10T10:00:00Z",
  "updated_at": "2025-10-10T10:00:00Z"
}
```

#### Error Responses

**404 Not Found:**

```json
{
  "detail": "No default dashboard configuration found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to fetch default dashboard config: Database error"
}
```

---

### 9. List Dashboard Configs

List all dashboard configurations for the current user.

**Endpoint:** `GET /api/dashboard-configs`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_tenant_defaults` | boolean | true | Include tenant-wide defaults in results |

#### Example Requests

**cURL:**

```bash
curl -X GET "https://api.taskifai.com/api/dashboard-configs?include_tenant_defaults=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

url = "https://api.taskifai.com/api/dashboard-configs"
headers = {"Authorization": f"Bearer {jwt_token}"}
params = {"include_tenant_defaults": True}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Total dashboards: {data['total']}")
    print(f"Has default: {data['has_default']}")
    for dashboard in data['dashboards']:
        print(f"- {dashboard['dashboard_name']} ({dashboard['widget_count']} widgets)")
else:
    print(f"Error: {response.status_code}")
```

**JavaScript:**

```javascript
const listDashboardConfigs = async (includeTenantDefaults = true) => {
  const url = new URL('https://api.taskifai.com/api/dashboard-configs');
  url.searchParams.append('include_tenant_defaults', includeTenantDefaults);

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    }
  });

  if (response.ok) {
    const data = await response.json();
    console.log(`Total dashboards: ${data.total}`);
    console.log(`Has default: ${data.has_default}`);
    data.dashboards.forEach(dashboard => {
      console.log(`- ${dashboard.dashboard_name} (${dashboard.widget_count} widgets)`);
    });
  } else {
    console.error('Error:', response.status);
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "dashboards": [
    {
      "dashboard_id": "550e8400-e29b-41d4-a716-446655440000",
      "dashboard_name": "Overview Dashboard",
      "description": "Real-time overview of sales performance",
      "is_default": true,
      "is_active": true,
      "display_order": 0,
      "widget_count": 3,
      "kpi_count": 4,
      "updated_at": "2025-10-10T10:00:00Z"
    },
    {
      "dashboard_id": "660e8400-e29b-41d4-a716-446655440001",
      "dashboard_name": "Marketing Dashboard",
      "description": "Marketing campaign performance",
      "is_default": false,
      "is_active": true,
      "display_order": 1,
      "widget_count": 5,
      "kpi_count": 6,
      "updated_at": "2025-10-15T14:30:00Z"
    }
  ],
  "total": 2,
  "has_default": true
}
```

#### Error Responses

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to list dashboard configs: Database error"
}
```

---

### 10. Get Dashboard Config by ID

Retrieve a specific dashboard configuration by ID.

**Endpoint:** `GET /api/dashboard-configs/{dashboard_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

**Authorization:**
- User can access their own configs
- User can access tenant-wide defaults (`user_id=NULL`)

#### Example Requests

**cURL:**

```bash
curl -X GET "https://api.taskifai.com/api/dashboard-configs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

dashboard_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"https://api.taskifai.com/api/dashboard-configs/{dashboard_id}"
headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    config = response.json()
    print(f"Dashboard: {config['dashboard_name']}")
    print(f"Widgets: {len(config['layout'])}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const getDashboardConfig = async (dashboardId) => {
  const response = await fetch(
    `https://api.taskifai.com/api/dashboard-configs/${dashboardId}`,
    {
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.ok) {
    const config = await response.json();
    console.log('Dashboard:', config.dashboard_name);
    console.log('Widgets:', config.layout.length);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `200 OK`

(Same structure as Get Default Dashboard Config response)

#### Error Responses

**403 Forbidden:**

```json
{
  "detail": "You don't have permission to access this dashboard configuration"
}
```

**404 Not Found:**

```json
{
  "detail": "Dashboard configuration not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to fetch dashboard config: Database error"
}
```

---

### 11. Create Dashboard Config

Create a new dashboard configuration for the current user.

**Endpoint:** `POST /api/dashboard-configs`

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dashboard_name` | string | Yes | Display name (1-255 chars) |
| `description` | string | No | Dashboard description (max 1000 chars) |
| `layout` | WidgetConfig[] | Yes | Array of widget configurations (min 1) |
| `kpis` | KPIType[] | No | Array of KPI types (default: []) |
| `filters` | DashboardFilters | No | Default filter settings |
| `is_default` | boolean | No | Set as default dashboard (default: false) |
| `is_active` | boolean | No | Active status (default: true) |
| `display_order` | integer | No | Display order (default: 0) |

**Widget Config Structure:**

```json
{
  "id": "unique-widget-id",
  "type": "kpi_grid",
  "position": {
    "row": 0,
    "col": 0,
    "width": 12,
    "height": 2
  },
  "props": {
    "title": "Key Metrics",
    "kpis": ["total_revenue", "total_units"]
  }
}
```

**Position Rules:**
- 12-column grid system
- `col`: 0-11 (column position)
- `width`: 1-12 (column span)
- `row`: 0+ (row position)
- `height`: 1-12 (row span)

#### Example Requests

**cURL:**

```bash
curl -X POST "https://api.taskifai.com/api/dashboard-configs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "My Custom Dashboard",
    "description": "Custom analytics dashboard",
    "layout": [
      {
        "id": "kpi-grid",
        "type": "kpi_grid",
        "position": {"row": 0, "col": 0, "width": 12, "height": 2},
        "props": {"title": "Key Metrics", "kpis": ["total_revenue", "total_units"]}
      }
    ],
    "kpis": ["total_revenue", "total_units", "avg_price"],
    "filters": {
      "date_range": "last_30_days",
      "vendor": "all"
    },
    "is_default": true
  }'
```

**Python:**

```python
import requests

url = "https://api.taskifai.com/api/dashboard-configs"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "dashboard_name": "My Custom Dashboard",
    "description": "Custom analytics dashboard",
    "layout": [
        {
            "id": "kpi-grid",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {"title": "Key Metrics", "kpis": ["total_revenue", "total_units"]}
        },
        {
            "id": "revenue-chart",
            "type": "revenue_chart",
            "position": {"row": 2, "col": 0, "width": 8, "height": 4},
            "props": {"title": "Revenue Trend", "chart_type": "line"}
        }
    ],
    "kpis": ["total_revenue", "total_units", "avg_price"],
    "filters": {
        "date_range": "last_30_days",
        "vendor": "all"
    },
    "is_default": True
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 201:
    config = response.json()
    print(f"Created dashboard: {config['dashboard_id']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const createDashboardConfig = async () => {
  const response = await fetch('https://api.taskifai.com/api/dashboard-configs', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      dashboard_name: 'My Custom Dashboard',
      description: 'Custom analytics dashboard',
      layout: [
        {
          id: 'kpi-grid',
          type: 'kpi_grid',
          position: { row: 0, col: 0, width: 12, height: 2 },
          props: { title: 'Key Metrics', kpis: ['total_revenue', 'total_units'] }
        },
        {
          id: 'revenue-chart',
          type: 'revenue_chart',
          position: { row: 2, col: 0, width: 8, height: 4 },
          props: { title: 'Revenue Trend', chart_type: 'line' }
        }
      ],
      kpis: ['total_revenue', 'total_units', 'avg_price'],
      filters: {
        date_range: 'last_30_days',
        vendor: 'all'
      },
      is_default: true
    })
  });

  if (response.ok) {
    const config = await response.json();
    console.log('Created dashboard:', config.dashboard_id);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `201 Created`

(Same structure as Get Default Dashboard Config response)

#### Error Responses

**400 Bad Request - Duplicate Widget IDs:**

```json
{
  "detail": "All widget IDs must be unique within a dashboard"
}
```

**400 Bad Request - Invalid Date Range:**

```json
{
  "detail": "Invalid date_range. Must be one of: last_7_days, last_14_days, last_30_days..."
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to create dashboard config: Database error"
}
```

---

### 12. Update Dashboard Config

Update an existing dashboard configuration.

**Endpoint:** `PUT /api/dashboard-configs/{dashboard_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

**Request Body:**

All fields are optional. Only provided fields will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `dashboard_name` | string | Updated display name |
| `description` | string | Updated description |
| `layout` | WidgetConfig[] | Updated widget layout |
| `kpis` | KPIType[] | Updated KPI list |
| `filters` | DashboardFilters | Updated default filters |
| `is_default` | boolean | Set as default |
| `is_active` | boolean | Active status |
| `display_order` | integer | Display order |

**Authorization:**
- User can only update their own configurations

#### Example Requests

**cURL:**

```bash
curl -X PUT "https://api.taskifai.com/api/dashboard-configs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard_name": "Updated Dashboard Name",
    "is_default": true
  }'
```

**Python:**

```python
import requests

dashboard_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"https://api.taskifai.com/api/dashboard-configs/{dashboard_id}"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "dashboard_name": "Updated Dashboard Name",
    "is_default": True
}

response = requests.put(url, json=payload, headers=headers)

if response.status_code == 200:
    config = response.json()
    print(f"Updated dashboard: {config['dashboard_name']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const updateDashboardConfig = async (dashboardId, updates) => {
  const response = await fetch(
    `https://api.taskifai.com/api/dashboard-configs/${dashboardId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${jwtToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );

  if (response.ok) {
    const config = await response.json();
    console.log('Updated dashboard:', config.dashboard_name);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `200 OK`

(Same structure as Get Default Dashboard Config response)

#### Error Responses

**403 Forbidden:**

```json
{
  "detail": "You don't have permission to update this dashboard configuration"
}
```

**404 Not Found:**

```json
{
  "detail": "Dashboard configuration not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to update dashboard config: Database error"
}
```

---

### 13. Delete Dashboard Config

Delete a dashboard configuration.

**Endpoint:** `DELETE /api/dashboard-configs/{dashboard_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dashboard_id` | UUID | Yes | Dashboard configuration ID |

**Authorization:**
- User can only delete their own configurations
- Cannot delete tenant-wide defaults (`user_id=NULL`)

#### Example Requests

**cURL:**

```bash
curl -X DELETE "https://api.taskifai.com/api/dashboard-configs/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

dashboard_id = "550e8400-e29b-41d4-a716-446655440000"
url = f"https://api.taskifai.com/api/dashboard-configs/{dashboard_id}"
headers = {"Authorization": f"Bearer {jwt_token}"}

response = requests.delete(url, headers=headers)

if response.status_code == 204:
    print("Dashboard config deleted successfully")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const deleteDashboardConfig = async (dashboardId) => {
  const response = await fetch(
    `https://api.taskifai.com/api/dashboard-configs/${dashboardId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.status === 204) {
    console.log('Dashboard config deleted successfully');
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};
```

#### Success Response

**Status:** `204 No Content`

No response body.

#### Error Responses

**403 Forbidden - Cannot Delete Tenant Default:**

```json
{
  "detail": "Cannot delete tenant-wide default dashboard"
}
```

**403 Forbidden - Permission Denied:**

```json
{
  "detail": "You don't have permission to delete this dashboard configuration"
}
```

**404 Not Found:**

```json
{
  "detail": "Dashboard configuration not found"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error:**

```json
{
  "detail": "Failed to delete dashboard config: Database error"
}
```

---

## Common Scenarios

### Scenario 1: Set Up Looker Dashboard

```python
import requests

# 1. Create dashboard configuration
url = "https://api.taskifai.com/api/dashboards"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
payload = {
    "dashboard_name": "Sales Analytics",
    "dashboard_type": "looker",
    "dashboard_url": "https://company.looker.com/dashboards/sales",
    "authentication_method": "bearer_token",
    "authentication_config": {
        "token": "looker_embed_token",
        "header_name": "Authorization"
    },
    "is_active": True
}

response = requests.post(url, json=payload, headers=headers)
dashboard = response.json()
print(f"Created dashboard: {dashboard['config_id']}")

# 2. Get embed URL
embed_url = "https://api.taskifai.com/api/dashboards/embed"
embed_payload = {"dashboard_id": dashboard['config_id']}

embed_response = requests.post(embed_url, json=embed_payload, headers=headers)
embed_data = embed_response.json()

print(f"Embed URL: {embed_data['embed_url']}")
print(f"Sandbox: {', '.join(embed_data['sandbox_attributes'])}")

# 3. Create iframe in frontend
iframe_html = f'''
<iframe
  src="{embed_data['embed_url']}"
  sandbox="{' '.join(embed_data['sandbox_attributes'])}"
  width="100%"
  height="600px"
  frameborder="0">
</iframe>
'''
```

### Scenario 2: Create Custom Dashboard Layout

```python
import requests

url = "https://api.taskifai.com/api/dashboard-configs"
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

# Create 3-section dashboard: KPIs, Chart, Products
payload = {
    "dashboard_name": "Executive Dashboard",
    "description": "High-level sales overview",
    "layout": [
        # Top: KPI Grid (full width)
        {
            "id": "kpi-section",
            "type": "kpi_grid",
            "position": {"row": 0, "col": 0, "width": 12, "height": 2},
            "props": {
                "title": "Key Performance Indicators",
                "kpis": ["total_revenue", "total_units", "avg_price", "profit_margin"]
            }
        },
        # Middle Left: Revenue Chart (2/3 width)
        {
            "id": "revenue-section",
            "type": "revenue_chart",
            "position": {"row": 2, "col": 0, "width": 8, "height": 4},
            "props": {
                "title": "Revenue Trend (30 Days)",
                "chart_type": "area"
            }
        },
        # Middle Right: Top Products (1/3 width)
        {
            "id": "products-section",
            "type": "top_products",
            "position": {"row": 2, "col": 8, "width": 4, "height": 4},
            "props": {
                "title": "Top 10 Products",
                "limit": 10
            }
        },
        # Bottom: Recent Uploads (full width)
        {
            "id": "uploads-section",
            "type": "recent_uploads",
            "position": {"row": 6, "col": 0, "width": 12, "height": 3},
            "props": {
                "title": "Recent File Uploads",
                "limit": 5
            }
        }
    ],
    "kpis": [
        "total_revenue",
        "total_units",
        "avg_price",
        "profit_margin",
        "order_count"
    ],
    "filters": {
        "date_range": "last_30_days",
        "vendor": "all"
    },
    "is_default": True
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 201:
    config = response.json()
    print(f"Created dashboard with {len(config['layout'])} widgets")
else:
    print(f"Error: {response.json()}")
```

### Scenario 3: Switch Primary Dashboard

```python
import requests

headers = {"Authorization": f"Bearer {jwt_token}"}

# 1. List all dashboards
list_url = "https://api.taskifai.com/api/dashboards"
response = requests.get(list_url, headers=headers)
dashboards = response.json()['dashboards']

print("Available dashboards:")
for i, dashboard in enumerate(dashboards):
    status = "PRIMARY" if dashboard['is_primary'] else ""
    print(f"{i+1}. {dashboard['dashboard_name']} {status}")

# 2. Set new primary dashboard
new_primary_id = dashboards[1]['config_id']  # Choose second dashboard
primary_url = f"https://api.taskifai.com/api/dashboards/{new_primary_id}/primary"

response = requests.patch(primary_url, headers=headers)

if response.status_code == 200:
    dashboard = response.json()
    print(f"Set {dashboard['dashboard_name']} as primary")
```

### Scenario 4: Manage Multiple BI Platforms

```python
import requests

headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}

# Add Looker dashboard
looker_payload = {
    "dashboard_name": "Looker Sales",
    "dashboard_type": "looker",
    "dashboard_url": "https://company.looker.com/dashboards/sales",
    "authentication_method": "bearer_token",
    "authentication_config": {
        "token": "looker_token",
        "header_name": "Authorization"
    },
    "permissions": ["view", "export"]
}

# Add Tableau dashboard
tableau_payload = {
    "dashboard_name": "Tableau Marketing",
    "dashboard_type": "tableau",
    "dashboard_url": "https://tableau.company.com/views/marketing",
    "authentication_method": "none",
    "permissions": ["view"]
}

# Add Power BI dashboard
powerbi_payload = {
    "dashboard_name": "Power BI Finance",
    "dashboard_type": "powerbi",
    "dashboard_url": "https://app.powerbi.com/view?r=abc123",
    "authentication_method": "api_key",
    "authentication_config": {
        "api_key": "powerbi_key",
        "header_name": "X-API-Key"
    },
    "permissions": ["view"]
}

url = "https://api.taskifai.com/api/dashboards"

# Create all dashboards
for payload in [looker_payload, tableau_payload, powerbi_payload]:
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        dashboard = response.json()
        print(f"Created {dashboard['dashboard_type']}: {dashboard['dashboard_name']}")
```

---

## Best Practices

### 1. Security Best Practices

**Credential Management:**
- Never log or expose `authentication_config` in plain text
- Credentials are encrypted at rest using PostgreSQL pgcrypto
- Rotate dashboard credentials regularly
- Use read-only credentials when possible

**URL Validation:**
- Always use HTTPS in production
- Validate dashboard URLs before saving
- Implement Content Security Policy (CSP) headers
- Use iframe sandbox attributes

**Example CSP Header:**
```
Content-Security-Policy: frame-src 'self' https://company.looker.com https://tableau.company.com;
```

### 2. Iframe Embedding Best Practices

**Sandbox Attributes:**
```html
<iframe
  src="dashboard_embed_url"
  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
  width="100%"
  height="600px"
  frameborder="0"
  loading="lazy">
</iframe>
```

**Responsive Design:**
```javascript
// Adjust iframe height based on content
const iframe = document.querySelector('iframe');
iframe.onload = () => {
  const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
  iframe.style.height = iframeDoc.body.scrollHeight + 'px';
};
```

### 3. Error Handling

**Python Example:**
```python
import requests
from requests.exceptions import Timeout, ConnectionError

def create_dashboard_safely(dashboard_data, jwt_token):
    url = "https://api.taskifai.com/api/dashboards"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            json=dashboard_data,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    except Timeout:
        print("Request timed out after 30 seconds")
        return None
    except ConnectionError:
        print("Failed to connect to API")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            error = response.json()
            print(f"Validation error: {error['detail']}")
        elif response.status_code == 401:
            print("Authentication failed - check JWT token")
        elif response.status_code == 500:
            print("Server error - try again later")
        return None
```

### 4. Dashboard Layout Design

**Grid System Rules:**
- Use 12-column grid for responsive design
- Full-width widgets: `width=12`
- Half-width widgets: `width=6`
- One-third widgets: `width=4`
- Two-thirds widgets: `width=8`

**Recommended Layouts:**

**Executive Dashboard (3 sections):**
```
[     KPI Grid (12 cols, 2 rows)      ]
[  Chart (8 cols)  ] [ List (4 cols)  ]
[     Table (12 cols, 3 rows)         ]
```

**Analytics Dashboard (4 sections):**
```
[ KPI 1 (3) ] [ KPI 2 (3) ] [ KPI 3 (3) ] [ KPI 4 (3) ]
[        Chart 1 (6)       ] [       Chart 2 (6)      ]
[            Data Table (12 cols)                      ]
```

### 5. Performance Optimization

**Lazy Loading:**
```javascript
// Load dashboard iframe only when visible
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const iframe = entry.target;
      iframe.src = iframe.dataset.src;
      observer.unobserve(iframe);
    }
  });
});

const iframe = document.querySelector('iframe');
iframe.dataset.src = embedUrl;
observer.observe(iframe);
```

**Caching:**
```python
# Cache embed URLs for 15 minutes
from cachetools import TTLCache
import hashlib

embed_cache = TTLCache(maxsize=100, ttl=900)  # 15 minutes

def get_embed_url_cached(dashboard_id, jwt_token):
    cache_key = hashlib.md5(f"{dashboard_id}:{jwt_token}".encode()).hexdigest()

    if cache_key in embed_cache:
        return embed_cache[cache_key]

    # Fetch from API
    embed_data = get_embed_url(dashboard_id, jwt_token)
    embed_cache[cache_key] = embed_data

    return embed_data
```

---

## Troubleshooting

### Issue: "Invalid dashboard URL: Localhost URLs are not allowed in production"

**Cause:** Attempting to use localhost URL in production environment.

**Solution:**
- Use public HTTPS URL for production dashboards
- For development, set `ENVIRONMENT=development` in backend `.env`
- Use ngrok or similar for local development testing

### Issue: Dashboard iframe not loading

**Possible Causes:**
1. X-Frame-Options header blocking iframe
2. Content Security Policy (CSP) restrictions
3. Authentication failed
4. CORS issues

**Solutions:**
```javascript
// Check iframe loading errors
iframe.onerror = (e) => {
  console.error('Iframe failed to load:', e);
};

// Verify embed URL
console.log('Embed URL:', iframe.src);

// Check browser console for CSP errors
```

### Issue: "Dashboard not found" when accessing

**Cause:** Dashboard belongs to different user or has been deleted.

**Solution:**
```python
# Verify dashboard ownership
response = requests.get(
    f"https://api.taskifai.com/api/dashboards",
    headers={"Authorization": f"Bearer {jwt_token}"}
)
dashboards = response.json()['dashboards']

# Check if dashboard_id exists
dashboard_exists = any(d['config_id'] == dashboard_id for d in dashboards)
print(f"Dashboard exists: {dashboard_exists}")
```

### Issue: Authentication credentials not working

**Cause:** Credentials may be incorrectly formatted or expired.

**Solution:**
```python
# Update dashboard credentials
update_url = f"https://api.taskifai.com/api/dashboards/{dashboard_id}"
update_payload = {
    "authentication_config": {
        "token": "new_valid_token",
        "header_name": "Authorization"
    }
}

response = requests.put(
    update_url,
    json=update_payload,
    headers={"Authorization": f"Bearer {jwt_token}"}
)

if response.status_code == 200:
    print("Credentials updated successfully")
```

### Issue: Widget IDs must be unique

**Cause:** Duplicate widget IDs in dashboard layout.

**Solution:**
```python
import uuid

# Generate unique widget IDs
layout = [
    {
        "id": f"widget-{uuid.uuid4()}",  # Unique ID
        "type": "kpi_grid",
        "position": {"row": 0, "col": 0, "width": 12, "height": 2},
        "props": {}
    }
]
```

---

## See Also

- [Analytics API](/docs/api/analytics.md) - Data queries for dashboard widgets
- [Authentication API](/docs/api/authentication.md) - JWT token management
- [Error Codes Reference](/docs/api/error-codes.md) - Complete error reference
- [Architecture Documentation](/Project_docs/02_Architecture.md) - System architecture
