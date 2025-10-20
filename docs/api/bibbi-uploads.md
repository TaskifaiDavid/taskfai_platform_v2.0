# BIBBI Reseller Upload API

## Overview

The BIBBI Reseller Upload API provides a specialized multi-reseller sales data upload system exclusively for the BIBBI tenant. This system handles Excel file uploads from multiple resellers (distributors), processes reseller-specific data formats, validates and stages data, and provides product mapping workflows.

**Tenant Isolation:** All endpoints in this API are restricted to `tenant_id='bibbi'` only.

**Key Features:**
- Multi-reseller Excel upload (8+ supported resellers)
- Automatic file validation and duplicate detection
- 3-stage processing pipeline: Upload → Staging → Validation → Approval → Final
- Product mapping workflow for unmapped SKUs
- Store matching and validation
- Concurrent multi-file uploads (up to 24 simultaneous)
- Comprehensive error reporting and retry mechanisms

**Base URL:** `/api/bibbi`

**Authentication:** Required (JWT Bearer Token)

**Supported Resellers:**
- Aromateque (Ukraine)
- Boxnox (Spain)
- Creme de la Creme / CDLC (Balticum)
- Galilu (Poland)
- Liberty (England)
- Selfridges (England)
- Skins NL (Netherlands)
- Skins SA (South Africa)

---

## Upload Workflow

### Complete Upload Pipeline

```
1. Upload File → API validates format, size, calculates hash
      ↓
2. Create Upload Batch → Record created in upload_batches table
      ↓
3. Enqueue Celery Task → Async processing begins
      ↓
4. File Processing → Parse Excel, detect reseller, extract sales data
      ↓
5. Staging → Insert to bibbi_staging_sales (with validation errors)
      ↓
6. Product Mapping → Match product codes to EAN using product_reseller_mappings
      ↓
7. Store Matching → Match store codes/names to stores table
      ↓
8. Validation → Check required fields, data types, ranges
      ↓
9. Error Reporting → Generate detailed error report for failed records
      ↓
10. Approval → User reviews staging data and approves
      ↓
11. Final Insert → Move approved records to bibbi_final_sales
      ↓
12. Complete → Update upload_batch status to 'completed'
```

### Data Flow Diagram

```
Excel File (Reseller Format)
      ↓
[Upload API] → File validation
      ↓
[upload_batches] → Track upload metadata
      ↓
[Celery Worker] → Async processing
      ↓
[Reseller Parser] → Extract sales rows
      ↓
[bibbi_staging_sales] → Temporary staging with errors
      ↓
[Product Mapping Service] → product_code → EAN
      ↓
[Store Matching Service] → store_code → store_id
      ↓
[Validation Service] → Business rules
      ↓
[bibbi_final_sales] → Production data (after approval)
```

---

## Configuration

### Environment Variables

**Backend `.env`:**

```env
# BIBBI Upload Configuration
BIBBI_UPLOAD_DIR=/var/uploads/bibbi
BIBBI_MAX_FILE_SIZE=52428800  # 50MB in bytes
BIBBI_ALLOWED_EXTENSIONS=[".xlsx", ".xls"]

# Tenant Override (for DigitalOcean deployments)
TENANT_ID_OVERRIDE=bibbi
```

**Important:** Set `TENANT_ID_OVERRIDE=bibbi` when deploying to DigitalOcean or other non-subdomain URLs to ensure proper tenant isolation.

### Celery Configuration

The BIBBI upload system uses Celery for async file processing:

```python
# backend/app/workers/celery_app.py
worker_prefetch_multiplier = 4  # Enables 24 concurrent uploads
task_time_limit = 1800  # 30-minute timeout per file
```

---

## Endpoints

### 1. Upload Reseller File

Upload an Excel file from a reseller for processing.

**Endpoint:** `POST /api/bibbi/uploads`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | Excel file (.xlsx or .xls) |
| `reseller_id` | string (UUID) | Yes | Reseller UUID from resellers table |

**File Validation Rules:**
- Maximum size: 50MB (configurable via `BIBBI_MAX_FILE_SIZE`)
- Allowed extensions: `.xlsx`, `.xls`
- Automatic duplicate detection via SHA256 hash
- Reseller must exist in `resellers` table

**Processing Pipeline:**
1. Validate file extension and size
2. Calculate SHA256 hash for duplicate detection
3. Check for duplicate uploads (same file hash)
4. Save file to disk with unique timestamped name
5. Create upload batch record in database
6. Enqueue Celery task for async processing
7. Return upload_id and batch_id

#### Example Requests

**cURL:**

```bash
curl -X POST "https://bibbi.taskifai.com/api/bibbi/uploads" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@galilu_sales_october.xlsx" \
  -F "reseller_id=550e8400-e29b-41d4-a716-446655440000"
```

**Python:**

```python
import requests

url = "https://bibbi.taskifai.com/api/bibbi/uploads"
headers = {"Authorization": f"Bearer {jwt_token}"}

files = {
    "file": ("galilu_sales_october.xlsx", open("galilu_sales_october.xlsx", "rb"))
}
data = {
    "reseller_id": "550e8400-e29b-41d4-a716-446655440000"
}

response = requests.post(url, headers=headers, files=files, data=data)

if response.status_code == 200:
    upload_data = response.json()
    print(f"Upload ID: {upload_data['upload_id']}")
    print(f"Batch ID: {upload_data['batch_id']}")
    print(f"Status: {upload_data['status']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

**JavaScript:**

```javascript
const uploadResellerFile = async (file, resellerId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('reseller_id', resellerId);

  const response = await fetch('https://bibbi.taskifai.com/api/bibbi/uploads', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    },
    body: formData
  });

  if (response.ok) {
    const uploadData = await response.json();
    console.log('Upload ID:', uploadData.upload_id);
    console.log('Batch ID:', uploadData.batch_id);
    console.log('Status:', uploadData.status);

    // Poll for status updates
    pollUploadStatus(uploadData.batch_id);
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
  }
};

// Example usage
const fileInput = document.querySelector('input[type="file"]');
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  const resellerId = '550e8400-e29b-41d4-a716-446655440000';
  uploadResellerFile(file, resellerId);
});
```

#### Success Response

**Status:** `200 OK`

```json
{
  "upload_id": "abc12345-6789-4def-0123-456789abcdef",
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "galilu_sales_october.xlsx",
  "file_size": 2458624,
  "file_hash": "d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2",
  "status": "pending",
  "message": "File uploaded successfully. Processing will begin shortly.",
  "created_at": "2025-10-18T14:30:00Z"
}
```

#### Error Responses

**400 Bad Request - Invalid File Type:**

```json
{
  "detail": "Invalid file type. Allowed extensions: .xlsx, .xls"
}
```

**400 Bad Request - File Too Large:**

```json
{
  "detail": "File too large. Maximum size: 50MB"
}
```

**400 Bad Request - Reseller Not Found:**

```json
{
  "detail": "Reseller not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

**409 Conflict - Duplicate Upload:**

```json
{
  "detail": {
    "message": "File already uploaded",
    "existing_upload_id": "def12345-6789-4abc-0123-456789abcdef",
    "uploaded_at": "2025-10-17T10:15:00Z",
    "status": "completed"
  }
}
```

**500 Internal Server Error - Upload Failed:**

```json
{
  "detail": "Failed to save file: Disk write error"
}
```

---

### 2. Get Upload Status

Check the processing status of an upload batch.

**Endpoint:** `GET /api/bibbi/uploads/{batch_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_id` | UUID | Yes | Upload batch ID from upload response |

**Upload Statuses:**

| Status | Description | Next Action |
|--------|-------------|-------------|
| `pending` | Queued for processing | Wait for worker |
| `processing` | Currently being processed | Monitor progress |
| `staging_complete` | Data in staging table | Review errors, approve |
| `approved` | Approved, moving to final | Wait for completion |
| `completed` | Successfully completed | View final data |
| `failed` | Processing failed | Review error, retry |
| `partial_success` | Some records failed | Review errors, reprocess failed |

#### Example Requests

**cURL:**

```bash
curl -X GET "https://bibbi.taskifai.com/api/bibbi/uploads/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests
import time

def poll_upload_status(batch_id, jwt_token, interval=5, max_attempts=60):
    """Poll upload status until completion or failure"""
    url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    for attempt in range(max_attempts):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            status_data = response.json()
            status = status_data['status']

            print(f"Attempt {attempt+1}: Status = {status}")

            if status == 'completed':
                print(f"Upload completed! Processed {status_data['processed_rows']} rows")
                return status_data
            elif status == 'failed':
                print(f"Upload failed: {status_data['error_message']}")
                return status_data
            elif status == 'staging_complete':
                print(f"Staging complete. Failed rows: {status_data['failed_rows']}")
                return status_data

        time.sleep(interval)

    print("Polling timeout reached")
    return None

# Usage
status = poll_upload_status('550e8400-e29b-41d4-a716-446655440000', jwt_token)
```

**JavaScript:**

```javascript
const pollUploadStatus = async (batchId, maxAttempts = 60, interval = 5000) => {
  const url = `https://bibbi.taskifai.com/api/bibbi/uploads/${batchId}`;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    });

    if (response.ok) {
      const statusData = await response.json();
      const { status, processed_rows, failed_rows, error_message } = statusData;

      console.log(`Attempt ${attempt + 1}: Status = ${status}`);

      if (status === 'completed') {
        console.log(`Upload completed! Processed ${processed_rows} rows`);
        return statusData;
      } else if (status === 'failed') {
        console.error(`Upload failed: ${error_message}`);
        return statusData;
      } else if (status === 'staging_complete') {
        console.log(`Staging complete. Failed rows: ${failed_rows}`);
        return statusData;
      }
    }

    await new Promise(resolve => setTimeout(resolve, interval));
  }

  console.warn('Polling timeout reached');
  return null;
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "upload_id": "abc12345-6789-4def-0123-456789abcdef",
  "status": "completed",
  "vendor_name": "Galilu",
  "total_rows": 1500,
  "processed_rows": 1485,
  "failed_rows": 15,
  "error_message": null,
  "created_at": "2025-10-18T14:30:00Z",
  "updated_at": "2025-10-18T14:35:22Z"
}
```

**Status: Failed Upload:**

```json
{
  "upload_id": "abc12345-6789-4def-0123-456789abcdef",
  "status": "failed",
  "vendor_name": null,
  "total_rows": null,
  "processed_rows": null,
  "failed_rows": null,
  "error_message": "Invalid Excel format: Missing required sheet 'Sales Data'",
  "created_at": "2025-10-18T14:30:00Z",
  "updated_at": "2025-10-18T14:30:45Z"
}
```

#### Error Responses

**404 Not Found:**

```json
{
  "detail": "Upload not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

---

### 3. List Upload Batches

List all upload batches with pagination and optional status filtering.

**Endpoint:** `GET /api/bibbi/uploads`

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum results per page |
| `offset` | integer | 0 | Number of results to skip |
| `status_filter` | string | null | Filter by status (optional) |

#### Example Requests

**cURL:**

```bash
curl -X GET "https://bibbi.taskifai.com/api/bibbi/uploads?limit=20&offset=0&status_filter=completed" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

url = "https://bibbi.taskifai.com/api/bibbi/uploads"
headers = {"Authorization": f"Bearer {jwt_token}"}
params = {
    "limit": 20,
    "offset": 0,
    "status_filter": "completed"
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Found {data['count']} uploads")
    for upload in data['uploads']:
        print(f"- {upload['original_filename']}: {upload['processing_status']}")
else:
    print(f"Error: {response.status_code}")
```

**JavaScript:**

```javascript
const listUploads = async (limit = 50, offset = 0, statusFilter = null) => {
  const url = new URL('https://bibbi.taskifai.com/api/bibbi/uploads');
  url.searchParams.append('limit', limit);
  url.searchParams.append('offset', offset);
  if (statusFilter) {
    url.searchParams.append('status_filter', statusFilter);
  }

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    }
  });

  if (response.ok) {
    const data = await response.json();
    console.log(`Found ${data.count} uploads`);
    data.uploads.forEach(upload => {
      console.log(`- ${upload.original_filename}: ${upload.processing_status}`);
    });
    return data;
  } else {
    console.error('Error:', response.status);
    return null;
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "uploads": [
    {
      "upload_batch_id": "550e8400-e29b-41d4-a716-446655440000",
      "uploader_user_id": "660e8400-e29b-41d4-a716-446655440001",
      "reseller_id": "770e8400-e29b-41d4-a716-446655440002",
      "original_filename": "galilu_sales_october.xlsx",
      "file_size_bytes": 2458624,
      "upload_mode": "append",
      "processing_status": "completed",
      "total_records": 1500,
      "success_count": 1485,
      "error_count": 15,
      "upload_timestamp": "2025-10-18T14:30:00Z",
      "processing_started_at": "2025-10-18T14:30:05Z",
      "processing_completed_at": "2025-10-18T14:35:22Z"
    },
    {
      "upload_batch_id": "880e8400-e29b-41d4-a716-446655440003",
      "uploader_user_id": "660e8400-e29b-41d4-a716-446655440001",
      "reseller_id": "990e8400-e29b-41d4-a716-446655440004",
      "original_filename": "boxnox_september.xlsx",
      "file_size_bytes": 1856432,
      "upload_mode": "append",
      "processing_status": "failed",
      "total_records": null,
      "success_count": null,
      "error_count": null,
      "upload_timestamp": "2025-10-17T10:15:00Z",
      "processing_started_at": "2025-10-17T10:15:10Z",
      "processing_completed_at": "2025-10-17T10:15:45Z"
    }
  ],
  "count": 2,
  "limit": 50,
  "offset": 0
}
```

---

### 4. Get Error Report

Retrieve detailed error report for failed records in an upload batch.

**Endpoint:** `GET /api/bibbi/uploads/{batch_id}/errors`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_id` | UUID | Yes | Upload batch ID |

**Error Types:**

| Error Code | Description | Solution |
|------------|-------------|----------|
| `PRODUCT_NOT_MAPPED` | Product code has no EAN mapping | Create product mapping |
| `STORE_NOT_FOUND` | Store code not in stores table | Add store or correct code |
| `INVALID_DATE_FORMAT` | Date field incorrect format | Check Excel date formatting |
| `MISSING_REQUIRED_FIELD` | Required column empty | Fix source data |
| `INVALID_QUANTITY` | Quantity not numeric or negative | Correct quantity values |
| `INVALID_PRICE` | Price not numeric or negative | Correct price values |
| `DUPLICATE_TRANSACTION` | Transaction already exists | Remove duplicate rows |

#### Example Requests

**cURL:**

```bash
curl -X GET "https://bibbi.taskifai.com/api/bibbi/uploads/550e8400-e29b-41d4-a716-446655440000/errors" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests
import pandas as pd

def get_error_report(batch_id, jwt_token):
    """Download error report and display summary"""
    url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}/errors"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        errors = response.json()

        # Convert to DataFrame for analysis
        df = pd.DataFrame(errors['errors'])

        print(f"Total Errors: {errors['total_errors']}")
        print(f"Error Breakdown:")
        print(df['error_type'].value_counts())

        # Show first 5 errors
        print("\nFirst 5 Errors:")
        print(df[['row_number', 'error_type', 'error_message']].head())

        # Export to CSV
        df.to_csv(f"errors_{batch_id}.csv", index=False)
        print(f"\nFull error report saved to: errors_{batch_id}.csv")

        return df
    else:
        print(f"Error: {response.status_code} - {response.json()}")
        return None

# Usage
errors_df = get_error_report('550e8400-e29b-41d4-a716-446655440000', jwt_token)
```

**JavaScript:**

```javascript
const getErrorReport = async (batchId) => {
  const response = await fetch(
    `https://bibbi.taskifai.com/api/bibbi/uploads/${batchId}/errors`,
    {
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.ok) {
    const errorData = await response.json();

    console.log(`Total Errors: ${errorData.total_errors}`);

    // Group by error type
    const errorsByType = errorData.errors.reduce((acc, error) => {
      acc[error.error_type] = (acc[error.error_type] || 0) + 1;
      return acc;
    }, {});

    console.log('Error Breakdown:', errorsByType);

    // Display errors in table
    displayErrorsTable(errorData.errors);

    return errorData;
  } else {
    console.error('Error:', response.status);
    return null;
  }
};

const displayErrorsTable = (errors) => {
  const table = document.createElement('table');
  table.innerHTML = `
    <thead>
      <tr>
        <th>Row</th>
        <th>Error Type</th>
        <th>Message</th>
        <th>Field</th>
      </tr>
    </thead>
    <tbody>
      ${errors.map(error => `
        <tr>
          <td>${error.row_number}</td>
          <td>${error.error_type}</td>
          <td>${error.error_message}</td>
          <td>${error.field_name || '-'}</td>
        </tr>
      `).join('')}
    </tbody>
  `;
  document.getElementById('errors-container').appendChild(table);
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_errors": 15,
  "errors": [
    {
      "row_number": 45,
      "error_type": "PRODUCT_NOT_MAPPED",
      "error_message": "Product code 'SKU-12345' not found in mappings",
      "field_name": "product_code",
      "field_value": "SKU-12345",
      "reseller_name": "Galilu"
    },
    {
      "row_number": 127,
      "error_type": "STORE_NOT_FOUND",
      "error_message": "Store code 'WS-001' not found",
      "field_name": "store_code",
      "field_value": "WS-001",
      "reseller_name": "Galilu"
    },
    {
      "row_number": 238,
      "error_type": "INVALID_QUANTITY",
      "error_message": "Quantity must be numeric and positive",
      "field_name": "quantity",
      "field_value": "-5",
      "reseller_name": "Galilu"
    },
    {
      "row_number": 412,
      "error_type": "MISSING_REQUIRED_FIELD",
      "error_message": "Required field 'sale_date' is empty",
      "field_name": "sale_date",
      "field_value": null,
      "reseller_name": "Galilu"
    },
    {
      "row_number": 567,
      "error_type": "INVALID_DATE_FORMAT",
      "error_message": "Date format must be YYYY-MM-DD or Excel date number",
      "field_name": "sale_date",
      "field_value": "32/13/2025",
      "reseller_name": "Galilu"
    }
  ]
}
```

#### Error Responses

**404 Not Found:**

```json
{
  "detail": "Upload not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

**404 Not Found - No Errors:**

```json
{
  "detail": "No errors found for this upload batch"
}
```

---

### 5. Approve Staged Data

Approve staging data and move to final production table.

**Endpoint:** `POST /api/bibbi/uploads/{batch_id}/approve`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_id` | UUID | Yes | Upload batch ID |

**Behavior:**
1. Validates batch is in `staging_complete` status
2. Moves successful records from `bibbi_staging_sales` to `bibbi_final_sales`
3. Failed records remain in staging for review/correction
4. Updates batch status to `approved` then `completed`

**Auto-Approval:**
If upload has zero errors (`failed_rows=0`), batch is auto-approved during processing.

#### Example Requests

**cURL:**

```bash
curl -X POST "https://bibbi.taskifai.com/api/bibbi/uploads/550e8400-e29b-41d4-a716-446655440000/approve" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

def approve_upload(batch_id, jwt_token):
    """Approve staging data and move to final"""
    url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}/approve"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"Approved! Moved {result['records_moved']} records to final table")
        print(f"Failed records: {result['failed_records']}")
        return result
    else:
        error = response.json()
        print(f"Error: {error['detail']}")
        return None

# Usage
result = approve_upload('550e8400-e29b-41d4-a716-446655440000', jwt_token)
```

**JavaScript:**

```javascript
const approveUpload = async (batchId) => {
  const response = await fetch(
    `https://bibbi.taskifai.com/api/bibbi/uploads/${batchId}/approve`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.ok) {
    const result = await response.json();
    console.log(`Approved! Moved ${result.records_moved} records to final table`);
    console.log(`Failed records: ${result.failed_records}`);
    return result;
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
    return null;
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "records_moved": 1485,
  "failed_records": 15,
  "message": "Successfully moved 1485 records to final sales table"
}
```

#### Error Responses

**400 Bad Request - Not Ready for Approval:**

```json
{
  "detail": "Upload batch not in staging_complete status. Current status: processing"
}
```

**404 Not Found:**

```json
{
  "detail": "Upload not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 6. Retry Failed Upload

Retry processing a failed upload batch.

**Endpoint:** `POST /api/bibbi/uploads/{batch_id}/retry`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_id` | UUID | Yes | Upload batch ID |

**Behavior:**
1. Validates batch is in `failed` status
2. Resets batch status to `pending`
3. Re-enqueues Celery task for processing
4. Uses original uploaded file

#### Example Requests

**cURL:**

```bash
curl -X POST "https://bibbi.taskifai.com/api/bibbi/uploads/550e8400-e29b-41d4-a716-446655440000/retry" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

def retry_upload(batch_id, jwt_token):
    """Retry a failed upload"""
    url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}/retry"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"Retry initiated for batch: {result['upload_id']}")
        print(f"Status: {result['status']}")
        return result
    else:
        error = response.json()
        print(f"Error: {error['detail']}")
        return None

# Usage
result = retry_upload('550e8400-e29b-41d4-a716-446655440000', jwt_token)
```

**JavaScript:**

```javascript
const retryUpload = async (batchId) => {
  const response = await fetch(
    `https://bibbi.taskifai.com/api/bibbi/uploads/${batchId}/retry`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.ok) {
    const result = await response.json();
    console.log(`Retry initiated for batch: ${result.upload_id}`);
    console.log(`Status: ${result.status}`);
    return result;
  } else {
    const error = await response.json();
    console.error('Error:', error.detail);
    return null;
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
{
  "message": "Upload retry initiated",
  "upload_id": "abc12345-6789-4def-0123-456789abcdef",
  "status": "pending"
}
```

#### Error Responses

**400 Bad Request - Not in Failed State:**

```json
{
  "detail": "Upload is not in failed state. Current status: completed"
}
```

**400 Bad Request - No File Path:**

```json
{
  "detail": "Upload has no file_path - cannot retry"
}
```

---

### 7. Delete Upload Batch

Permanently delete an upload batch and associated staging data.

**Endpoint:** `DELETE /api/bibbi/uploads/{batch_id}`

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_id` | UUID | Yes | Upload batch ID |

**Warning:** This permanently deletes:
- Upload batch record
- Staging data (`bibbi_staging_sales`)
- Upload file from disk

Final data (`bibbi_final_sales`) is NOT deleted.

#### Example Requests

**cURL:**

```bash
curl -X DELETE "https://bibbi.taskifai.com/api/bibbi/uploads/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

def delete_upload(batch_id, jwt_token):
    """Delete upload batch and staging data"""
    url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # Confirm deletion
    confirm = input(f"Delete batch {batch_id}? This cannot be undone. (yes/no): ")
    if confirm.lower() != 'yes':
        print("Deletion cancelled")
        return

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print(f"Upload batch {batch_id} deleted successfully")
    else:
        error = response.json()
        print(f"Error: {error['detail']}")

# Usage
delete_upload('550e8400-e29b-41d4-a716-446655440000', jwt_token)
```

**JavaScript:**

```javascript
const deleteUpload = async (batchId) => {
  // Confirm deletion
  if (!confirm(`Delete batch ${batchId}? This cannot be undone.`)) {
    console.log('Deletion cancelled');
    return;
  }

  const response = await fetch(
    `https://bibbi.taskifai.com/api/bibbi/uploads/${batchId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  if (response.status === 204) {
    console.log(`Upload batch ${batchId} deleted successfully`);
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
  "detail": "Upload not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 8. List Resellers

Get list of all supported BIBBI resellers.

**Endpoint:** `GET /api/bibbi/resellers`

**Authentication:** Required

**Returns:** All active resellers with their IDs, names, and countries.

#### Example Requests

**cURL:**

```bash
curl -X GET "https://bibbi.taskifai.com/api/bibbi/resellers" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python:**

```python
import requests

def list_resellers(jwt_token):
    """Get list of all BIBBI resellers"""
    url = "https://bibbi.taskifai.com/api/bibbi/resellers"
    headers = {"Authorization": f"Bearer {jwt_token}"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        resellers = response.json()
        print(f"Found {len(resellers)} resellers:")
        for reseller in resellers:
            print(f"- {reseller['reseller_name']} ({reseller['country']}): {reseller['reseller_id']}")
        return resellers
    else:
        print(f"Error: {response.status_code}")
        return []

# Usage
resellers = list_resellers(jwt_token)
```

**JavaScript:**

```javascript
const listResellers = async () => {
  const response = await fetch('https://bibbi.taskifai.com/api/bibbi/resellers', {
    headers: {
      'Authorization': `Bearer ${jwtToken}`
    }
  });

  if (response.ok) {
    const resellers = await response.json();
    console.log(`Found ${resellers.length} resellers:`);
    resellers.forEach(reseller => {
      console.log(`- ${reseller.reseller_name} (${reseller.country}): ${reseller.reseller_id}`);
    });
    return resellers;
  } else {
    console.error('Error:', response.status);
    return [];
  }
};
```

#### Success Response

**Status:** `200 OK`

```json
[
  {
    "reseller_id": "550e8400-e29b-41d4-a716-446655440000",
    "reseller_name": "Galilu",
    "country": "Poland",
    "currency": null,
    "is_active": true,
    "created_at": "2025-01-15T08:00:00Z"
  },
  {
    "reseller_id": "660e8400-e29b-41d4-a716-446655440001",
    "reseller_name": "Boxnox",
    "country": "Spain",
    "currency": null,
    "is_active": true,
    "created_at": "2025-01-15T08:00:00Z"
  },
  {
    "reseller_id": "770e8400-e29b-41d4-a716-446655440002",
    "reseller_name": "Skins SA",
    "country": "South Africa",
    "currency": null,
    "is_active": true,
    "created_at": "2025-01-15T08:00:00Z"
  },
  {
    "reseller_id": "880e8400-e29b-41d4-a716-446655440003",
    "reseller_name": "Aromateque",
    "country": "Ukraine",
    "currency": null,
    "is_active": true,
    "created_at": "2025-01-15T08:00:00Z"
  },
  {
    "reseller_id": "990e8400-e29b-41d4-a716-446655440004",
    "reseller_name": "Liberty",
    "country": "England",
    "currency": null,
    "is_active": true,
    "created_at": "2025-01-15T08:00:00Z"
  }
]
```

---

## Common Scenarios

### Scenario 1: Complete Upload Workflow

```python
import requests
import time

def complete_upload_workflow(file_path, reseller_id, jwt_token):
    """Complete BIBBI upload workflow from file to approval"""

    # Step 1: Upload file
    print("Step 1: Uploading file...")
    upload_url = "https://bibbi.taskifai.com/api/bibbi/uploads"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    files = {"file": (file_path, open(file_path, "rb"))}
    data = {"reseller_id": reseller_id}

    upload_response = requests.post(upload_url, headers=headers, files=files, data=data)

    if upload_response.status_code != 200:
        print(f"Upload failed: {upload_response.json()}")
        return

    upload_data = upload_response.json()
    batch_id = upload_data['batch_id']
    print(f"Upload successful! Batch ID: {batch_id}")

    # Step 2: Poll for processing completion
    print("\nStep 2: Waiting for processing...")
    status_url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}"

    max_attempts = 60
    for attempt in range(max_attempts):
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()
        status = status_data['status']

        print(f"  Attempt {attempt+1}: Status = {status}")

        if status == 'staging_complete':
            print(f"\n  Processing complete!")
            print(f"  Total rows: {status_data['total_rows']}")
            print(f"  Successful: {status_data['processed_rows']}")
            print(f"  Failed: {status_data['failed_rows']}")
            break
        elif status == 'failed':
            print(f"\n  Processing failed: {status_data['error_message']}")
            return

        time.sleep(5)

    # Step 3: Check for errors
    if status_data['failed_rows'] > 0:
        print(f"\nStep 3: Retrieving error report...")
        errors_url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}/errors"
        errors_response = requests.get(errors_url, headers=headers)
        errors_data = errors_response.json()

        print(f"  Found {errors_data['total_errors']} errors:")
        for error in errors_data['errors'][:5]:  # Show first 5
            print(f"    Row {error['row_number']}: {error['error_type']} - {error['error_message']}")

        # Ask user to proceed
        proceed = input("\n  Errors found. Approve successful records? (yes/no): ")
        if proceed.lower() != 'yes':
            print("  Approval cancelled")
            return

    # Step 4: Approve staged data
    print("\nStep 4: Approving staged data...")
    approve_url = f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}/approve"
    approve_response = requests.post(approve_url, headers=headers)

    if approve_response.status_code == 200:
        approve_data = approve_response.json()
        print(f"  Approval successful!")
        print(f"  Records moved to final: {approve_data['records_moved']}")
        print(f"  Failed records: {approve_data['failed_records']}")
    else:
        print(f"  Approval failed: {approve_response.json()}")

# Usage
complete_upload_workflow(
    'galilu_sales_october.xlsx',
    '550e8400-e29b-41d4-a716-446655440000',
    jwt_token
)
```

### Scenario 2: Batch Multiple File Uploads

```python
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def upload_file(file_path, reseller_id, jwt_token):
    """Upload single file"""
    url = "https://bibbi.taskifai.com/api/bibbi/uploads"
    headers = {"Authorization": f"Bearer {jwt_token}"}
    files = {"file": (file_path, open(file_path, "rb"))}
    data = {"reseller_id": reseller_id}

    response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.json(), "file": file_path}

def batch_upload_files(file_reseller_pairs, jwt_token, max_workers=5):
    """Upload multiple files concurrently"""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all uploads
        future_to_file = {
            executor.submit(upload_file, file_path, reseller_id, jwt_token): file_path
            for file_path, reseller_id in file_reseller_pairs
        }

        # Collect results as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                if 'error' in result:
                    print(f"❌ {file_path}: {result['error']}")
                else:
                    print(f"✅ {file_path}: Batch {result['batch_id']}")
                results.append(result)
            except Exception as e:
                print(f"❌ {file_path}: Exception - {e}")
                results.append({"error": str(e), "file": file_path})

    return results

# Usage
files_to_upload = [
    ('galilu_october.xlsx', '550e8400-e29b-41d4-a716-446655440000'),
    ('galilu_november.xlsx', '550e8400-e29b-41d4-a716-446655440000'),
    ('boxnox_october.xlsx', '660e8400-e29b-41d4-a716-446655440001'),
    ('skins_sa_october.xlsx', '770e8400-e29b-41d4-a716-446655440002'),
]

results = batch_upload_files(files_to_upload, jwt_token, max_workers=4)
print(f"\nUploaded {len([r for r in results if 'batch_id' in r])} files successfully")
```

### Scenario 3: Monitor Upload Progress with Real-Time UI

```javascript
// React Component for Upload Progress
import React, { useState, useEffect } from 'react';

function UploadMonitor({ batchId, jwtToken }) {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const pollStatus = async () => {
      const response = await fetch(
        `https://bibbi.taskifai.com/api/bibbi/uploads/${batchId}`,
        {
          headers: { 'Authorization': `Bearer ${jwtToken}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStatus(data);

        // Calculate progress
        if (data.total_rows) {
          const processed = data.processed_rows || 0;
          const total = data.total_rows;
          setProgress((processed / total) * 100);
        }

        // Stop polling when complete or failed
        if (['completed', 'failed', 'staging_complete'].includes(data.status)) {
          clearInterval(intervalId);
        }
      }
    };

    const intervalId = setInterval(pollStatus, 3000);
    pollStatus(); // Initial call

    return () => clearInterval(intervalId);
  }, [batchId, jwtToken]);

  if (!status) return <div>Loading...</div>;

  return (
    <div className="upload-monitor">
      <h3>Upload Status: {status.status}</h3>

      {status.total_rows && (
        <div className="progress-bar">
          <div className="progress" style={{ width: `${progress}%` }}></div>
          <span>{Math.round(progress)}%</span>
        </div>
      )}

      <div className="stats">
        <div>Total Rows: {status.total_rows || 'N/A'}</div>
        <div>Processed: {status.processed_rows || 0}</div>
        <div>Failed: {status.failed_rows || 0}</div>
      </div>

      {status.status === 'failed' && (
        <div className="error-message">
          Error: {status.error_message}
        </div>
      )}

      {status.status === 'staging_complete' && status.failed_rows > 0 && (
        <button onClick={() => viewErrors(batchId)}>
          View {status.failed_rows} Errors
        </button>
      )}
    </div>
  );
}
```

---

## Best Practices

### 1. File Preparation

**Excel File Requirements:**
- Use `.xlsx` format (preferred) or `.xls`
- Maximum file size: 50MB
- Include all required columns
- Use consistent date formats (YYYY-MM-DD or Excel dates)
- Avoid merged cells and complex formatting
- Remove empty rows and columns

**Data Quality Checklist:**
- ✅ Product codes match mappings table
- ✅ Store codes match stores table
- ✅ Dates are valid and within reasonable range
- ✅ Quantities are positive integers
- ✅ Prices are positive numbers
- ✅ No duplicate transaction IDs

### 2. Error Handling

**Retry Strategy:**
```python
import requests
import time

def upload_with_retry(file_path, reseller_id, jwt_token, max_retries=3):
    """Upload with exponential backoff retry"""

    for attempt in range(max_retries):
        try:
            url = "https://bibbi.taskifai.com/api/bibbi/uploads"
            headers = {"Authorization": f"Bearer {jwt_token}"}
            files = {"file": (file_path, open(file_path, "rb"))}
            data = {"reseller_id": reseller_id}

            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 409:  # Duplicate
                print("File already uploaded")
                return response.json()
            elif response.status_code >= 500:  # Server error - retry
                raise Exception(f"Server error: {response.status_code}")
            else:  # Client error - don't retry
                print(f"Upload failed: {response.json()}")
                return None

        except Exception as e:
            wait_time = (2 ** attempt) * 5  # Exponential backoff
            print(f"Attempt {attempt+1} failed: {e}")

            if attempt < max_retries - 1:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached")
                return None

    return None
```

### 3. Large File Handling

**Chunked Upload (for very large files):**
```python
def split_excel_file(file_path, chunk_size=1000):
    """Split large Excel file into smaller chunks"""
    import pandas as pd

    df = pd.read_excel(file_path)
    total_rows = len(df)

    chunks = []
    for i in range(0, total_rows, chunk_size):
        chunk_df = df[i:i+chunk_size]
        chunk_filename = f"chunk_{i//chunk_size + 1}.xlsx"
        chunk_df.to_excel(chunk_filename, index=False)
        chunks.append(chunk_filename)

    return chunks

# Usage
chunks = split_excel_file('large_file.xlsx', chunk_size=1000)
for chunk in chunks:
    upload_file(chunk, reseller_id, jwt_token)
```

### 4. Performance Optimization

**Concurrent Uploads:**
- Use ThreadPoolExecutor for parallel uploads
- Limit concurrent uploads to 10-15 (backend supports 24)
- Monitor system resources (CPU, memory, network)

**Polling Best Practices:**
- Use exponential backoff for status polling
- Start with 3-5 second intervals
- Increase interval after several attempts
- Set reasonable timeout (10-30 minutes for large files)

---

## Troubleshooting

### Issue: "Reseller not found: {reseller_id}"

**Cause:** Invalid reseller UUID or reseller not in database.

**Solution:**
```python
# Get list of valid resellers
resellers = requests.get(
    "https://bibbi.taskifai.com/api/bibbi/resellers",
    headers={"Authorization": f"Bearer {jwt_token}"}
).json()

# Find correct reseller ID
for reseller in resellers:
    if reseller['reseller_name'] == 'Galilu':
        print(f"Galilu ID: {reseller['reseller_id']}")
```

### Issue: Upload stuck in "processing" status

**Possible Causes:**
1. Celery worker not running
2. File processing taking longer than expected
3. Worker crashed during processing

**Solutions:**
```bash
# Check Celery worker logs
docker-compose logs -f worker

# Restart Celery worker
docker-compose restart worker

# Retry the upload
curl -X POST "https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}/retry" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Issue: "Product code not found in mappings"

**Cause:** Product code from Excel doesn't exist in `product_reseller_mappings` table.

**Solution:**
1. Get error report to identify unmapped products
2. Create product mappings (see Product Mappings API)
3. Retry upload or manually correct staging data

```python
# Get unmapped products
errors_response = requests.get(
    f"https://bibbi.taskifai.com/api/bibbi/uploads/{batch_id}/errors",
    headers={"Authorization": f"Bearer {jwt_token}"}
)

unmapped_products = [
    error['field_value']
    for error in errors_response.json()['errors']
    if error['error_type'] == 'PRODUCT_NOT_MAPPED'
]

print(f"Unmapped products: {set(unmapped_products)}")

# Create mappings via Product Mappings API (see bibbi-product-mappings.md)
```

### Issue: High error rate (>10% failed rows)

**Investigation Steps:**
1. Download error report
2. Analyze error patterns
3. Check source data quality
4. Verify reseller file format hasn't changed

```python
import pandas as pd

# Analyze error patterns
errors_df = pd.DataFrame(errors_response.json()['errors'])
error_summary = errors_df.groupby('error_type').size()

print("Error Distribution:")
print(error_summary)

# Check if specific columns are problematic
field_errors = errors_df.groupby('field_name').size()
print("\nErrors by Field:")
print(field_errors)
```

---

## See Also

- [BIBBI Product Mappings API](/docs/api/bibbi-product-mappings.md) - Manage product code mappings
- [Error Codes Reference](/docs/api/error-codes.md) - Complete error reference
- [Authentication API](/docs/api/authentication.md) - JWT token management
- [BIBBI Database Design](/claudedocs/BIBBI_Final_Database_Design.md) - Database schema
- [Data Processing Pipeline](/Project_docs/05_Data_Processing_Pipeline.md) - Processing architecture
