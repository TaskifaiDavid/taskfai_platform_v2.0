# 8. Dashboard Management System

This document describes the external dashboard embedding and management capabilities that allow users to integrate third-party analytics dashboards into the platform.

## 8.1. Core Purpose

The dashboard management system enables users to connect and view external analytics dashboards (e.g., Looker, Tableau, Power BI, Metabase) directly within the application interface, creating a unified analytics experience.

**Key Business Value:**
- Centralized access to all analytics in one place
- Eliminates context switching between tools
- Secure iframe embedding with authentication passthrough
- Multi-dashboard support for different views (sales, marketing, operations)
- User-specific dashboard configurations

## 8.2. System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend Dashboard UI                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Dashboard Tabs (Sales | Marketing | Operations)       │  │
│  │  ├─ Tab Controls                                       │  │
│  │  ├─ Fullscreen Toggle                                  │  │
│  │  ├─ External Link Button                               │  │
│  │  └─ Dashboard Management (Add/Delete)                  │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Dashboard Viewport (iframe container)                 │  │
│  │  └─ Active Dashboard Display                           │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │ HTTPS/JSON
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Backend API (Dashboard Management)              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  • Authentication & Authorization                      │  │
│  │  • Dashboard CRUD Operations                           │  │
│  │  • User-specific Configuration Storage                 │  │
│  │  • Dashboard URL Validation                            │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  dashboard_configs Table                               │  │
│  │  ├─ id, user_id, dashboard_name                        │  │
│  │  ├─ dashboard_url, dashboard_type                      │  │
│  │  ├─ authentication_config, permissions                 │  │
│  │  └─ is_active, created_at, updated_at                  │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              External Dashboard Services                     │
│  (Looker Studio, Tableau, Power BI, Metabase, etc.)        │
└─────────────────────────────────────────────────────────────┘
```

## 8.3. Dashboard Configuration Model

### Configuration Entity

Each dashboard configuration stores:

```
DashboardConfig:
- id: Unique identifier
- user_id: Owner of the dashboard configuration
- dashboard_name: Display name (e.g., "Sales Performance Q1")
- dashboard_type: Type of dashboard platform (looker, tableau, powerbi, metabase, custom)
- dashboard_url: Embeddable URL for the dashboard
- authentication_method: How to authenticate with the dashboard (none, bearer_token, api_key, oauth)
- authentication_config: Credentials or tokens (encrypted)
- permissions: Which users can view this dashboard (array of user IDs or roles)
- is_active: Whether this is the primary/default dashboard
- created_at: When the configuration was created
- updated_at: When last modified
```

### Dashboard Types Supported

| Type | Platform | Embedding Method | Authentication |
|------|----------|------------------|----------------|
| `looker` | Looker Studio | Iframe | Public or OAuth |
| `tableau` | Tableau Public/Online | Iframe | Public or SSO |
| `powerbi` | Microsoft Power BI | Iframe | Embed token |
| `metabase` | Metabase | Iframe + JWT | Signed URL |
| `custom` | Any web dashboard | Iframe | Configurable |

## 8.4. Core Features

### 8.4.1. Dashboard Connection

Users can connect new external dashboards through a modal interface:

**Required Information:**
1. Dashboard Name (user-friendly label)
2. Dashboard URL (embeddable URL from external platform)
3. Primary Dashboard Flag (set as default view)

**Optional Information:**
- Authentication credentials (for private dashboards)
- User permissions (who can view this dashboard)
- Dashboard type/platform (for platform-specific handling)

**Connection Flow:**
```
1. User clicks "Connect Dashboard" button
2. Modal form appears
3. User enters dashboard name and URL
4. User optionally sets as primary dashboard
5. System validates URL format
6. Configuration saved to database
7. Dashboard appears in tabs
8. Iframe loads dashboard content
```

### 8.4.2. Multi-Dashboard Support

**Tab-Based Interface:**
- Each connected dashboard appears as a tab
- Click tab to switch between dashboards
- Active dashboard highlighted visually
- Primary dashboard marked with indicator
- Empty state when no dashboards connected

**Dashboard Switching:**
```
User Action: Click "Marketing Dashboard" tab
System Process:
1. Deactivate current dashboard view
2. Update iframe src to marketing dashboard URL
3. Update active tab styling
4. Load new dashboard content
5. Update browser history (optional)
```

### 8.4.3. Fullscreen Mode

**Toggle Fullscreen:**
- Button to enter/exit fullscreen mode
- Dashboard expands to fill entire viewport
- Clean presentation mode for data review
- ESC key exits fullscreen
- Maintains iframe interactivity

**Use Cases:**
- Presentation mode for meetings
- Detailed data exploration
- Screenshot capture
- Focus mode without distractions

### 8.4.4. External Link

**Open in New Tab:**
- Button to open dashboard in separate browser tab
- Useful for multi-monitor setups
- Access platform-specific features
- Direct dashboard manipulation
- Compare multiple dashboards side-by-side

### 8.4.5. Dashboard Management

**Add Dashboard:**
- Floating action button always visible
- Quick access to connection modal
- No limit on number of dashboards
- Immediate availability after creation

**Delete Dashboard:**
- Three-dot menu on active dashboard
- Confirmation dialog before deletion
- Removes from tabs immediately
- Database record permanently deleted
- Falls back to first available dashboard

**Edit Dashboard (Future):**
- Modify dashboard name
- Update URL
- Change permissions
- Toggle primary status

## 8.5. Security Considerations

### 8.5.1. Iframe Sandboxing

All embedded dashboards use iframe sandbox attributes:

```html
<iframe
  src="[dashboard_url]"
  sandbox="allow-scripts allow-same-origin allow-forms"
  title="[dashboard_name]"
/>
```

**Allowed Capabilities:**
- `allow-scripts`: Execute JavaScript for dashboard interactivity
- `allow-same-origin`: Access to same-origin resources
- `allow-forms`: Submit forms within dashboard

**Blocked Capabilities:**
- `allow-top-navigation`: Prevent hijacking parent window
- `allow-popups`: Block unwanted popup windows
- `allow-pointer-lock`: Prevent locking user mouse
- `allow-modals`: Block modal dialogs from iframe

### 8.5.2. URL Validation

Before storing dashboard configurations:

```
Validation Rules:
1. Must be valid HTTPS URL
2. Must not be localhost/127.0.0.1 (production)
3. Must not contain suspicious parameters
4. Domain must be allowlisted (optional)
```

### 8.5.3. Authentication Handling

**Public Dashboards:**
- No authentication required
- URL embedded directly
- Works for publicly shared analytics

**Private Dashboards:**
- Bearer tokens stored encrypted
- JWT tokens signed on backend
- OAuth tokens refreshed automatically
- API keys stored in secure vault

**Authentication Flow (Metabase Example):**
```
1. User provides Metabase dashboard URL
2. System extracts dashboard ID
3. Backend generates signed JWT with user context
4. Signed URL constructed: https://metabase.com/embed/[id]#jwt=[token]
5. Iframe loads authenticated dashboard
```

### 8.5.4. User Data Isolation

Each user only sees their own dashboard configurations:

```sql
SELECT * FROM dashboard_configs
WHERE user_id = [authenticated_user_id]
ORDER BY created_at DESC
```

Prevents unauthorized access to other users' dashboard setups.

## 8.6. API Endpoints

### GET /api/dashboards/configs

Retrieve all dashboard configurations for the authenticated user.

**Response:**
```json
{
  "configs": [
    {
      "id": "dash_123",
      "dashboardName": "Sales Performance",
      "dashboardType": "looker",
      "dashboardUrl": "https://lookerstudio.google.com/embed/reporting/...",
      "authenticationMethod": "none",
      "authenticationConfig": {},
      "permissions": [],
      "isActive": true,
      "createdAt": "2024-05-20T10:00:00Z",
      "updatedAt": "2024-05-20T10:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /api/dashboards/configs

Create a new dashboard configuration.

**Request:**
```json
{
  "dashboardName": "Marketing Analytics",
  "dashboardType": "tableau",
  "dashboardUrl": "https://public.tableau.com/views/...",
  "authenticationMethod": "none",
  "authenticationConfig": {},
  "permissions": [],
  "isActive": false
}
```

**Response:**
```json
{
  "success": true,
  "config": {
    "id": "dash_456",
    "dashboardName": "Marketing Analytics",
    ...
  },
  "message": "Dashboard configuration created successfully"
}
```

### PUT /api/dashboards/configs/{config_id}

Update an existing dashboard configuration.

**Request:**
```json
{
  "dashboardName": "Updated Dashboard Name",
  "dashboardType": "looker",
  "dashboardUrl": "https://new-url.com/dashboard",
  "authenticationMethod": "bearer_token",
  "authenticationConfig": {
    "token": "encrypted_token_here"
  },
  "permissions": ["user_123", "user_456"],
  "isActive": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Dashboard configuration updated successfully",
  "updatedAt": "2024-05-21T14:30:00Z"
}
```

### DELETE /api/dashboards/configs/{config_id}

Delete a dashboard configuration.

**Response:**
```json
{
  "success": true,
  "message": "Dashboard configuration deleted successfully",
  "deleted_id": "dash_123"
}
```

### GET /api/dashboards/configs/{config_id}

Get a specific dashboard configuration.

**Response:**
```json
{
  "id": "dash_123",
  "dashboardName": "Sales Performance",
  "dashboardType": "looker",
  "dashboardUrl": "https://lookerstudio.google.com/...",
  ...
}
```

## 8.7. User Experience Flows

### First-Time Setup

```
User State: No dashboards connected

UI Display:
┌─────────────────────────────────────────┐
│  Empty State                            │
│  ┌───────────────────────────────────┐  │
│  │  [Chart Icon]                     │  │
│  │  "Connect Your First Dashboard"  │  │
│  │  "Start monitoring business..."  │  │
│  │  [Connect Dashboard Button]      │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

User Action: Click "Connect Dashboard"
→ Modal opens with connection form
→ User fills in name and URL
→ Click "Connect" button
→ Dashboard appears in viewport
→ Tab navigation now visible
```

### Multi-Dashboard Navigation

```
User State: 3 dashboards connected

UI Display:
┌─────────────────────────────────────────┐
│  [Sales*] [Marketing] [Operations]     │
│  ────────                               │
│  ┌───────────────────────────────────┐  │
│  │  [Dashboard iframe content]       │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│  [Fullscreen] [External] [•••] [+]     │
└─────────────────────────────────────────┘

* = Primary dashboard indicator

User Action: Click "Marketing" tab
→ Iframe source changes to marketing URL
→ Tab styling updates (Marketing now active)
→ Dashboard content loads
```

### Dashboard Deletion

```
User Action: Click three-dot menu on active dashboard
→ Floating menu appears with "Disconnect" option

User Action: Click "Disconnect"
→ Confirmation dialog: "Disconnect 'Sales Performance'?"
→ User confirms

System Process:
1. DELETE /api/dashboards/configs/{id} called
2. Dashboard removed from tabs
3. If deleted dashboard was active, switch to first remaining dashboard
4. Success notification shown
5. Tab bar updates to remove deleted dashboard
```

## 8.8. Platform-Specific Integration

### Looker Studio

**Embedding:**
- Use "Embed" option in Looker Studio
- Copy embed URL
- Paste into dashboard configuration
- Public dashboards work without authentication

**Limitations:**
- Must be shared publicly or with specific users
- Filters may not sync with parent application

### Tableau

**Embedding:**
- Tableau Public: Use share/embed link
- Tableau Online: Generate embed code with JavaScript API
- Supports parameter passing via URL

**Authentication:**
- Tableau Public: No auth required
- Tableau Online: Trusted ticket or OAuth

### Power BI

**Embedding:**
- Use Power BI Embed for customers
- Generate embed token via API
- Token expires after 1 hour (auto-refresh required)

**Authentication:**
- Service principal authentication
- Embed token stored and refreshed

### Metabase

**Embedding:**
- Enable embedding in Metabase settings
- Generate signed JWT for authentication
- Pass user context in JWT payload

**Authentication:**
```javascript
const jwt = generateJWT({
  resource: { dashboard: dashboardId },
  params: { user_id: userId },
  exp: Math.round(Date.now() / 1000) + (10 * 60) // 10 minute expiry
})
const embedUrl = `${metabaseUrl}/embed/dashboard/${token}#bordered=false&titled=false`
```

## 8.9. Performance Considerations

**Lazy Loading:**
- Only load active dashboard iframe
- Defer loading non-visible dashboards
- Preload next likely dashboard on hover

**Caching:**
- Cache dashboard configurations in frontend state
- Only fetch from API on page load or after modifications
- Use optimistic UI updates for deletions

**Error Handling:**
```
Scenario: Dashboard fails to load

Display:
┌─────────────────────────────────────────┐
│  [!] Dashboard Loading Error            │
│  Unable to load dashboard.              │
│  [Try Again] [Open External]            │
└─────────────────────────────────────────┘
```

## 8.10. Future Enhancements

1. **Dashboard Sharing:** Share configurations between team members
2. **Scheduled Snapshots:** Auto-capture dashboard state daily/weekly
3. **Dashboard Templates:** Pre-built configurations for common tools
4. **Embedded Filters:** Sync filters between platform and external dashboard
5. **Dashboard Collections:** Group related dashboards into folders
6. **Mobile Optimization:** Responsive dashboard viewing on tablets/phones
7. **Collaboration:** Comments and annotations on dashboard views
8. **Export Capabilities:** Save dashboard view as PDF or image
