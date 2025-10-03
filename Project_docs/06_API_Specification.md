# 6. API Specification

This document defines the key endpoints for the Backend API server. It serves as a contract between the frontend and the backend.

**Base URL:** `/api/v1`

--- 

### Authentication

**Endpoint:** `POST /auth/login`
-   **Description:** Authenticates a user and returns a session token (e.g., JWT).
-   **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "user_password"
    }
    ```
-   **Response (200 OK):**
    ```json
    {
      "access_token": "...",
      "token_type": "bearer"
    }
    ```

**Endpoint:** `POST /auth/logout`
-   **Description:** Invalidates the user's session token.
-   **Requires Auth:** Yes.

--- 

### Data Upload

**Endpoint:** `POST /uploads`
-   **Description:** Uploads a new sales data file for processing.
-   **Requires Auth:** Yes.
-   **Request Body:** `multipart/form-data` containing the file.
-   **Response (202 Accepted):**
    ```json
    {
      "upload_batch_id": "...",
      "status": "pending"
    }
    ```

**Endpoint:** `GET /uploads/{upload_batch_id}/status`
-   **Description:** Checks the processing status of a specific upload batch.
-   **Requires Auth:** Yes.
-   **Response (200 OK):**
    ```json
    {
      "upload_batch_id": "...",
      "status": "processing",
      "progress": 45.5
    }
    ```

--- 

### Dashboards & Analytics

**Endpoint:** `GET /dashboard/summary`
-   **Description:** Retrieves aggregated summary data for the main dashboard.
-   **Requires Auth:** Yes.
-   **Query Parameters:** `start_date`, `end_date`, `reseller_id` (optional).
-   **Response (200 OK):**
    ```json
    {
      "total_revenue": 123456.78,
      "total_units_sold": 9876,
      "top_selling_product": {
        "product_name": "...",
        "units_sold": 500
      }
    }
    ```

--- 

### Reporting

**Endpoint:** `GET /reports/sales`
-   **Description:** Retrieves a paginated list of individual sales records.
-   **Requires Auth:** Yes.
-   **Query Parameters:** `start_date`, `end_date`, `reseller_id`, `product_id`, `page`, `per_page`.
-   **Response (200 OK):** A paginated list of `Sale` objects.

**Endpoint:** `GET /reports/errors/{upload_batch_id}`
-   **Description:** Retrieves a list of processing errors for a specific upload batch.
-   **Requires Auth:** Yes.
-   **Response (200 OK):** A list of `ErrorReport` objects.

---

### AI Chat

**Endpoint:** `POST /chat`
-   **Description:** Submit a natural language question about sales data.
-   **Requires Auth:** Yes.
-   **Request Body:**
    ```json
    {
      "message": "What were total sales in May 2024?",
      "session_id": "optional-session-id"
    }
    ```
-   **Response (200 OK):**
    ```json
    {
      "answer": "In May 2024, your total sales were €45,320.50...",
      "session_id": "default"
    }
    ```

**Endpoint:** `GET /chat/history`
-   **Description:** Retrieve conversation history for the authenticated user.
-   **Requires Auth:** Yes.
-   **Query Parameters:** `session_id` (optional), `limit` (default 50).
-   **Response (200 OK):**
    ```json
    {
      "conversations": [
        {
          "session_id": "default",
          "user_message": "What were sales in May?",
          "ai_response": "In May 2024...",
          "timestamp": "2024-05-20T14:30:00Z"
        }
      ],
      "total_messages": 10
    }
    ```

**Endpoint:** `POST /chat/clear`
-   **Description:** Clear conversation history.
-   **Requires Auth:** Yes.
-   **Request Body:**
    ```json
    {
      "session_id": "optional-session-to-clear"
    }
    ```
-   **Response (200 OK):**
    ```json
    {
      "message": "Conversation cleared successfully",
      "session_id": "default"
    }
    ```

---

### Dashboard Management

**Endpoint:** `GET /dashboards/configs`
-   **Description:** Retrieve all dashboard configurations for the authenticated user.
-   **Requires Auth:** Yes.
-   **Response (200 OK):**
    ```json
    {
      "configs": [
        {
          "id": "dash_123",
          "dashboardName": "Sales Performance",
          "dashboardType": "looker",
          "dashboardUrl": "https://lookerstudio.google.com/...",
          "authenticationMethod": "none",
          "isActive": true,
          "createdAt": "2024-05-20T10:00:00Z"
        }
      ],
      "total": 1
    }
    ```

**Endpoint:** `POST /dashboards/configs`
-   **Description:** Create a new dashboard configuration.
-   **Requires Auth:** Yes.
-   **Request Body:**
    ```json
    {
      "dashboardName": "Marketing Analytics",
      "dashboardType": "tableau",
      "dashboardUrl": "https://public.tableau.com/...",
      "authenticationMethod": "none",
      "isActive": false
    }
    ```
-   **Response (201 Created):**
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

**Endpoint:** `GET /dashboards/configs/{config_id}`
-   **Description:** Get a specific dashboard configuration.
-   **Requires Auth:** Yes.
-   **Response (200 OK):** Dashboard configuration object.

**Endpoint:** `PUT /dashboards/configs/{config_id}`
-   **Description:** Update an existing dashboard configuration.
-   **Requires Auth:** Yes.
-   **Request Body:** Same as POST with updated fields.
-   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Dashboard configuration updated successfully"
    }
    ```

**Endpoint:** `DELETE /dashboards/configs/{config_id}`
-   **Description:** Delete a dashboard configuration.
-   **Requires Auth:** Yes.
-   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Dashboard configuration deleted successfully",
      "deleted_id": "dash_123"
    }
    ```

---

### Email & Reporting

**Endpoint:** `POST /reports/email`
-   **Description:** Generate and send a one-time email report.
-   **Requires Auth:** Yes.
-   **Request Body:**
    ```json
    {
      "reportType": "sales_summary",
      "dateRange": {
        "start": "2024-05-01",
        "end": "2024-05-31"
      },
      "format": "pdf",
      "recipients": ["user@example.com"]
    }
    ```
-   **Response (200 OK):**
    ```json
    {
      "success": true,
      "message": "Report sent successfully",
      "emailLog": {
        "log_id": "email_789",
        "sent_at": "2024-05-20T14:30:00Z"
      }
    }
    ```

**Endpoint:** `POST /reports/generate`
-   **Description:** Generate a report for download (without emailing).
-   **Requires Auth:** Yes.
-   **Request Body:**
    ```json
    {
      "reportType": "detailed_transactions",
      "format": "excel",
      "dateRange": {
        "start": "2024-05-01",
        "end": "2024-05-31"
      }
    }
    ```
-   **Response (200 OK):**
    ```json
    {
      "success": true,
      "download_url": "/downloads/report_abc123.xlsx",
      "expires_at": "2024-05-21T14:30:00Z",
      "file_size": 1234567
    }
    ```

**Endpoint:** `GET /email/logs`
-   **Description:** Retrieve email log history.
-   **Requires Auth:** Yes.
-   **Query Parameters:** `start_date`, `end_date`, `email_type`, `status`, `limit`.
-   **Response (200 OK):**
    ```json
    {
      "logs": [
        {
          "log_id": "email_789",
          "email_type": "scheduled_report",
          "recipient_email": "user@example.com",
          "subject": "Weekly Sales Report",
          "sent_at": "2024-05-20T09:00:00Z",
          "status": "sent"
        }
      ],
      "total": 125
    }
    ```

---

## API Response Patterns

### Success Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional success message"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": { ... }
  }
}
```

### Common HTTP Status Codes
- **200 OK:** Request successful
- **201 Created:** Resource created successfully
- **202 Accepted:** Request accepted for asynchronous processing
- **400 Bad Request:** Invalid request parameters
- **401 Unauthorized:** Missing or invalid authentication token
- **403 Forbidden:** User lacks permission for requested resource
- **404 Not Found:** Resource does not exist
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Server-side error

### Authentication Header
All authenticated endpoints require:
```
Authorization: Bearer <jwt_token>
```
