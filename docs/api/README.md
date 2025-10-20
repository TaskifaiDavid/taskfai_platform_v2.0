# TaskifAI REST API Documentation

**Version**: 2.0.0
**Base URL**: `https://your-domain.com/api` (Production) or `http://localhost:8000/api` (Development)
**Authentication**: Bearer JWT Token

## Overview

The TaskifAI REST API provides programmatic access to all platform features including:

- User authentication and registration
- File uploads (D2C and B2B reseller data)
- Analytics and KPI queries
- AI-powered natural language chat
- Dashboard management
- Admin operations

## Quick Start

### 1. Authentication

All API requests (except login/register) require a JWT bearer token:

```bash
# Login to get token
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "your_password"}'

# Response
{
  "user": {...},
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. Making Authenticated Requests

Include the token in the `Authorization` header:

```bash
curl -X GET https://your-domain.com/api/analytics/kpis \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Multi-Tenant Context

The API automatically extracts tenant context from:
- Subdomain: `bibbi.taskifai.com` → `tenant_id="bibbi"`
- URL parameter: `?tenant_id=demo`
- Header: `X-Tenant-ID: demo`

## API Endpoints

### Authentication
- `POST /auth/register` - Create new user account
- `POST /auth/login` - Authenticate and get JWT token
- `POST /auth/logout` - Logout (client-side token removal)
- `POST /auth/mfa/enroll` - Enable two-factor authentication
- `POST /auth/mfa/verify-enrollment` - Verify TOTP code for MFA
- `POST /auth/mfa/disable` - Disable two-factor authentication
- `GET /auth/mfa/status` - Check MFA enrollment status
- `POST /auth/login/mfa-verify` - Complete MFA login

[Full Authentication Documentation →](./authentication.md)

### File Uploads
- `POST /uploads` - Upload sales data file (unified D2C/B2B)
- `GET /uploads/batches` - List upload batches
- `GET /uploads/batches/{batch_id}` - Get batch details
- `GET /uploads/{batch_id}/errors` - Get upload error reports
- `DELETE /uploads/batches/{batch_id}` - Delete upload batch
- `POST /uploads/cleanup-stuck` - Clean up stuck/pending uploads

[Full Upload Documentation →](./uploads.md)

### BIBBI Reseller Uploads
- `POST /bibbi/uploads` - Upload reseller file (BIBBI tenant only)
- `GET /bibbi/uploads/{upload_id}` - Get upload status
- `GET /bibbi/uploads` - List BIBBI uploads
- `POST /bibbi/uploads/{upload_id}/retry` - Retry failed upload
- `GET /bibbi/resellers` - List active resellers

[Full BIBBI Documentation →](./bibbi-uploads.md)

### Analytics
- `GET /analytics/kpis` - Get key performance indicators
- `GET /analytics/sales` - Get detailed sales data with filters
- `GET /analytics/sales/summary` - Get aggregated sales summary
- `POST /analytics/export` - Export report (PDF, CSV, Excel)
- `GET /analytics/export/{format}` - Download report immediately

[Full Analytics Documentation →](./analytics.md)

### AI Chat
- `POST /chat/query` - Send natural language query
- `GET /chat/history` - Get conversation history
- `DELETE /chat/history` - Clear conversation history
- `GET /chat/sessions` - List chat sessions

[Full Chat Documentation →](./chat.md)

### Dashboard Management
- `POST /dashboards` - Create dashboard configuration
- `GET /dashboards` - List user dashboards
- `GET /dashboards/{dashboard_id}` - Get dashboard details
- `PUT /dashboards/{dashboard_id}` - Update dashboard
- `DELETE /dashboards/{dashboard_id}` - Delete dashboard
- `PATCH /dashboards/{dashboard_id}/primary` - Set primary dashboard
- `POST /dashboards/embed` - Get secure embed URL

[Full Dashboard Documentation →](./dashboards.md)

### Admin (Coming Soon)
- Tenant management
- User administration
- System configuration

## Response Format

All API responses follow a consistent JSON structure:

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for async processing |
| 204 | No Content | Success with no response body |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

[Full Error Code Reference →](./error-codes.md)

## Rate Limiting

**Current Implementation**: No rate limiting enforced.

**Future Plans**:
- 100 requests/minute per user for standard endpoints
- 10 requests/minute for AI chat endpoints
- 5 uploads/minute for file upload endpoints

## Pagination

List endpoints support pagination via query parameters:

```bash
GET /uploads/batches?limit=20&offset=40
```

- `limit` - Number of results per page (default: 20, max: 100)
- `offset` - Number of results to skip (default: 0)

Response includes pagination metadata:
```json
{
  "success": true,
  "data": [...],
  "count": 20,
  "total": 150,
  "limit": 20,
  "offset": 40
}
```

## Filtering

Many endpoints support filtering via query parameters:

```bash
GET /analytics/sales?channel=online&start_date=2024-01-01&end_date=2024-12-31
```

Common filter parameters:
- `start_date` - Filter by start date (ISO 8601: YYYY-MM-DD)
- `end_date` - Filter by end date (ISO 8601: YYYY-MM-DD)
- `channel` - Filter by channel (`online`, `offline`, `all`)
- `status` - Filter by status (varies by endpoint)
- `reseller` - Filter by reseller name (fuzzy search)
- `product` - Filter by product name (fuzzy search)
- `country` - Filter by country

## Date Formats

All dates use ISO 8601 format:

- **Dates**: `YYYY-MM-DD` (e.g., `2024-10-18`)
- **Timestamps**: `YYYY-MM-DDTHH:MM:SS.sssZ` (e.g., `2024-10-18T14:30:00.000Z`)

Timestamps are always in UTC timezone.

## File Upload Format

File uploads use `multipart/form-data` encoding:

```bash
curl -X POST https://your-domain.com/api/uploads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sales_data.xlsx" \
  -F "mode=append"
```

Supported file formats:
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`

Maximum file size: 100MB

## Interactive API Documentation

When the backend is running, access interactive API docs:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

These provide:
- Interactive request/response testing
- Complete schema definitions
- Authentication configuration
- Example requests and responses

## Code Examples

### Python

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'your_password'
})
token = response.json()['access_token']

# Get KPIs
headers = {'Authorization': f'Bearer {token}'}
kpis = requests.get('http://localhost:8000/api/analytics/kpis', headers=headers)
print(kpis.json())
```

### JavaScript (Fetch)

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'your_password' })
});
const { access_token } = await loginResponse.json();

// Get KPIs
const kpisResponse = await fetch('http://localhost:8000/api/analytics/kpis', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const kpis = await kpisResponse.json();
console.log(kpis);
```

### cURL

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"your_password"}' \
  | jq -r '.access_token')

# Get KPIs
curl -X GET http://localhost:8000/api/analytics/kpis \
  -H "Authorization: Bearer $TOKEN"
```

## Webhooks

**Status**: Not implemented yet.

**Planned**:
- Upload completion notifications
- Processing error notifications
- Daily analytics summaries

## Versioning

**Current Version**: 2.0.0

The API version is included in the response headers:
```
X-API-Version: 2.0.0
```

**Breaking Changes**: Will be announced via changelog and email notifications.

## Support

- **Documentation**: [Full documentation →](../README.md)
- **Issues**: GitHub Issues
- **Email**: support@taskifai.com

## Next Steps

- [Authentication Guide →](./authentication.md)
- [Upload File Data →](./uploads.md)
- [Query Analytics →](./analytics.md)
- [AI Chat Integration →](./chat.md)
- [Error Handling →](./error-codes.md)
