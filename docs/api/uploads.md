# File Upload API

## Overview

The unified upload API handles both D2C (direct-to-consumer) and B2B (reseller) sales data uploads with automatic vendor detection and processing.

**Base Path**: `/api/uploads`

## Features

- Automatic vendor format detection (9+ formats supported)
- Async processing with Celery workers
- Upload tracking and status monitoring
- Error reporting with row-level details
- Support for append and replace modes
- Duplicate detection
- Multi-file concurrent uploads (24 simultaneous)

---

## Endpoints

### Upload Sales Data File

Upload an Excel or CSV file containing sales data. The system automatically detects the vendor format and processes the data asynchronously.

**Endpoint**: `POST /uploads`

**Authentication**: Required (Bearer token)

**Content-Type**: `multipart/form-data`

**Form Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | file | Yes | Excel (.xlsx, .xls) or CSV file |
| mode | string | Yes | Upload mode: `append` or `replace` |
| reseller_id | string | No | BIBBI reseller UUID (triggers B2B processing) |
| tenant_id | string | No | Tenant context override (usually auto-detected) |

**Supported File Formats**:
- Excel: `.xlsx`, `.xls`
- CSV: `.csv`
- Maximum size: 100MB
- Maximum concurrent uploads: 24

**Supported Vendors**:
- Boxnox (Spain, Europe)
- Galilu (Poland)
- Skins SA (South Africa)
- Skins NL (Netherlands)
- CDLC (Creme de la Creme, Balticum)
- Selfridges (UK)
- Liberty (UK)
- Aromateque (Ukraine)
- Continuity Suppliers (UK)

**Success Response** (200 OK):
```json
{
  "success": true,
  "batch_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
  "filename": "sales_october_2024.xlsx",
  "file_size": 524288,
  "mode": "append",
  "status": "pending",
  "message": "File uploaded successfully. Processing will begin shortly."
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| batch_id | string | Unique upload batch identifier (use for status tracking) |
| filename | string | Original filename |
| file_size | integer | File size in bytes |
| mode | string | Upload mode used |
| status | string | Initial status (always `pending`) |

**Error Responses**:

`400 Bad Request` - Invalid mode:
```json
{
  "detail": "Mode must be 'append' or 'replace'"
}
```

`400 Bad Request` - Invalid file:
```json
{
  "detail": "Invalid file type. Allowed extensions: .xlsx, .xls, .csv"
}
```

`500 Internal Server Error` - Upload failed:
```json
{
  "detail": "Failed to save file: [error details]"
}
```

**Processing Pipeline**:
1. File validation (extension, size)
2. Batch record creation in database
3. File saved to temporary storage
4. Celery worker task enqueued
5. Vendor auto-detection
6. Data parsing and normalization
7. Database insertion with user_id filtering
8. Status update (completed or failed)

**Example (cURL)**:
```bash
curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sales_data.xlsx" \
  -F "mode=append"
```

**Example (Python)**:
```python
import requests

with open('sales_data.xlsx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/uploads',
        headers={'Authorization': f'Bearer {token}'},
        files={'file': f},
        data={'mode': 'append'}
    )

batch_id = response.json()['batch_id']
print(f"Upload started: {batch_id}")
```

**Example (JavaScript)**:
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('mode', 'append');

const response = await fetch('/api/uploads', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const { batch_id } = await response.json();
console.log(`Upload batch: ${batch_id}`);
```

---

### List Upload Batches

Retrieve list of user's upload batches with pagination and filtering.

**Endpoint**: `GET /uploads/batches`

**Authentication**: Required (Bearer token)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results (max 100) |
| offset | integer | 0 | Pagination offset |
| status | string | null | Filter by status: `pending`, `processing`, `completed`, `failed` |

**Success Response** (200 OK):
```json
{
  "success": true,
  "batches": [
    {
      "upload_batch_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "original_filename": "sales_october_2024.xlsx",
      "file_size_bytes": 524288,
      "vendor_name": "Galilu",
      "upload_mode": "append",
      "processing_status": "completed",
      "rows_total": 1500,
      "rows_processed": 1495,
      "rows_failed": 5,
      "total_sales_eur": 125430.50,
      "upload_timestamp": "2024-10-18T14:30:00.000Z",
      "processing_started_at": "2024-10-18T14:30:05.000Z",
      "processing_completed_at": "2024-10-18T14:31:22.000Z",
      "error_summary": null
    }
  ],
  "count": 1
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| upload_batch_id | string | Unique batch identifier |
| original_filename | string | Uploaded filename |
| file_size_bytes | integer | File size in bytes |
| vendor_name | string | Auto-detected vendor |
| upload_mode | string | `append` or `replace` |
| processing_status | string | `pending`, `processing`, `completed`, `failed` |
| rows_total | integer | Total rows parsed from file |
| rows_processed | integer | Successfully inserted rows |
| rows_failed | integer | Failed rows (see error reports) |
| total_sales_eur | decimal | Sum of sales revenue (EUR) |
| upload_timestamp | string | Upload initiation time (ISO 8601) |
| processing_started_at | string | Processing start time |
| processing_completed_at | string | Processing completion time |
| error_summary | string | Brief error description (if failed) |

**Example**:
```bash
# Get all completed uploads
curl -X GET "http://localhost:8000/api/uploads/batches?status=completed&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Upload Batch Details

Retrieve detailed information about a specific upload batch.

**Endpoint**: `GET /uploads/batches/{batch_id}`

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| batch_id | string | Upload batch UUID |

**Success Response** (200 OK):
```json
{
  "success": true,
  "batch": {
    "upload_batch_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
    "uploader_user_id": "123e4567-e89b-12d3-a456-426614174000",
    "original_filename": "sales_october_2024.xlsx",
    "file_size_bytes": 524288,
    "vendor_name": "Galilu",
    "upload_mode": "append",
    "processing_status": "completed",
    "rows_total": 1500,
    "rows_processed": 1495,
    "rows_failed": 5,
    "total_sales_eur": 125430.50,
    "upload_timestamp": "2024-10-18T14:30:00.000Z",
    "processing_started_at": "2024-10-18T14:30:05.000Z",
    "processing_completed_at": "2024-10-18T14:31:22.000Z",
    "error_summary": "5 rows failed validation"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Batch not found"
}
```

**Example**:
```bash
curl -X GET "http://localhost:8000/api/uploads/batches/d290f1ee-6c54-4b01-90e6-d701748f0851" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Get Upload Error Reports

Retrieve row-level error details for failed uploads.

**Endpoint**: `GET /uploads/{batch_id}/errors`

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| batch_id | string | Upload batch UUID |

**Success Response** (200 OK):
```json
{
  "success": true,
  "errors": [
    {
      "error_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "upload_batch_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "row_number_in_file": 42,
      "error_type": "VALIDATION_ERROR",
      "error_message": "Invalid product EAN: must be 13 digits",
      "raw_data": {
        "product_ean": "12345",
        "functional_name": "Product XYZ",
        "sales_eur": "150.00",
        "quantity": "5"
      },
      "created_at": "2024-10-18T14:31:15.000Z"
    },
    {
      "error_id": "b2c3d4e5-f6a7-5b6c-9d0e-1f2a3b4c5d6e",
      "upload_batch_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
      "row_number_in_file": 87,
      "error_type": "MISSING_REQUIRED_FIELD",
      "error_message": "Missing required field: functional_name",
      "raw_data": {
        "product_ean": "1234567890123",
        "sales_eur": "200.00",
        "quantity": "10"
      },
      "created_at": "2024-10-18T14:31:18.000Z"
    }
  ],
  "count": 2
}
```

**Common Error Types**:
| Error Type | Description |
|------------|-------------|
| VALIDATION_ERROR | Data validation failed (invalid format, out of range) |
| MISSING_REQUIRED_FIELD | Required field is null or empty |
| INVALID_DATE | Date parsing failed or invalid date value |
| INVALID_NUMBER | Numeric field contains non-numeric value |
| DUPLICATE_ENTRY | Row conflicts with existing data (replace mode) |
| VENDOR_DETECTION_FAILED | Could not identify vendor format |
| PARSING_ERROR | Excel/CSV parsing failed |

**Example**:
```bash
curl -X GET "http://localhost:8000/api/uploads/d290f1ee-6c54-4b01-90e6-d701748f0851/errors" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Delete Upload Batch

Delete an upload batch and associated data.

**Endpoint**: `DELETE /uploads/batches/{batch_id}`

**Authentication**: Required (Bearer token)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| batch_id | string | Upload batch UUID |

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Batch deleted successfully"
}
```

**Error Responses**:

`404 Not Found`:
```json
{
  "detail": "Batch not found"
}
```

**Note**: This operation:
- Deletes the upload batch record
- Deletes associated error reports
- Does NOT delete processed sales data (use `mode=replace` for that)
- Cleans up temporary files

**Example**:
```bash
curl -X DELETE "http://localhost:8000/api/uploads/batches/d290f1ee-6c54-4b01-90e6-d701748f0851" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Cleanup Stuck Uploads

Automatically clean up uploads stuck in `pending` status for more than 10 minutes.

**Endpoint**: `POST /uploads/cleanup-stuck`

**Authentication**: Required (Bearer token)

**Success Response** (200 OK):
```json
{
  "success": true,
  "cleaned_count": 3,
  "message": "Cleaned up 3 stuck upload(s)"
}
```

**What it does**:
1. Finds uploads with `processing_status=pending`
2. Filters uploads older than 10 minutes
3. Updates status to `failed`
4. Sets error_summary: "Processing timeout - marked as failed during cleanup"

**When to use**:
- Worker crashes during processing
- Network issues preventing task completion
- Manual cleanup after Celery restarts

**Example**:
```bash
curl -X POST "http://localhost:8000/api/uploads/cleanup-stuck" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Upload Modes

### Append Mode

**Behavior**: Add new sales data without deleting existing records.

**Use Cases**:
- Monthly data uploads
- Incremental updates
- Adding new products/resellers

**Example**:
```bash
curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@october_sales.xlsx" \
  -F "mode=append"
```

### Replace Mode

**Behavior**: Delete all existing user data before importing new data.

**Use Cases**:
- Full data refresh
- Correcting previous upload mistakes
- Annual data replacement

**Warning**: This permanently deletes all existing sales data for the user!

**Example**:
```bash
curl -X POST http://localhost:8000/api/uploads \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@full_sales_2024.xlsx" \
  -F "mode=replace"
```

---

## Vendor Auto-Detection

The system automatically identifies vendor format by analyzing:

1. **Column Headers**: Unique column naming patterns
2. **File Structure**: Sheet names, header positions
3. **Data Patterns**: Date formats, currency symbols

**Detection Confidence Levels**:
- High: Exact match on 5+ unique patterns
- Medium: Match on 3-4 patterns
- Low: Match on 1-2 patterns (may require manual verification)

**If Detection Fails**:
- Upload will fail with `vendor_detection_failed` error
- Check error reports for details
- Verify file format matches supported vendors
- Contact support to add new vendor format

---

## Processing Status Workflow

```
pending → processing → completed
              ↓
           failed
```

**Status Descriptions**:
| Status | Description | Next Action |
|--------|-------------|-------------|
| pending | Upload received, waiting for worker | Wait for processing |
| processing | Worker is processing the file | Monitor progress |
| completed | Successfully processed | View data in analytics |
| failed | Processing failed | Check error reports |

**Typical Processing Times**:
- Small files (<100 rows): 5-10 seconds
- Medium files (100-1000 rows): 10-30 seconds
- Large files (1000-10000 rows): 30-120 seconds
- Very large files (>10000 rows): 2-5 minutes

---

## Concurrent Uploads

The system supports up to **24 simultaneous uploads** per user.

**Configuration**:
```python
# backend/app/workers/celery_app.py
worker_prefetch_multiplier = 4
worker_concurrency = 6
# Total: 4 × 6 = 24 concurrent tasks
```

**Best Practices**:
- Upload multiple files in parallel for faster processing
- Monitor system resources during bulk uploads
- Use append mode for concurrent uploads to avoid data conflicts

---

## Error Handling

### Common Upload Errors

**File Too Large**:
```json
{
  "detail": "File size exceeds maximum limit (100MB)"
}
```
**Solution**: Split file into smaller chunks or compress data.

**Invalid File Format**:
```json
{
  "detail": "Invalid file type. Allowed extensions: .xlsx, .xls, .csv"
}
```
**Solution**: Convert file to Excel or CSV format.

**Vendor Not Detected**:
```json
{
  "detail": "Could not detect vendor format"
}
```
**Solution**: Verify file structure matches supported vendors or contact support.

**Worker Not Available**:
```json
{
  "detail": "Processing queue is full. Try again later."
}
```
**Solution**: Wait a few minutes and retry. Check Celery worker status.

---

## Code Examples

### Monitor Upload Progress (Python)

```python
import requests
import time

def upload_and_wait(file_path, token, mode='append'):
    # Upload file
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/uploads',
            headers={'Authorization': f'Bearer {token}'},
            files={'file': f},
            data={'mode': mode}
        )

    batch_id = response.json()['batch_id']
    print(f"Upload started: {batch_id}")

    # Poll for completion
    while True:
        status_response = requests.get(
            f'http://localhost:8000/api/uploads/batches/{batch_id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        batch = status_response.json()['batch']
        status = batch['processing_status']

        print(f"Status: {status}")

        if status == 'completed':
            print(f"Processed {batch['rows_processed']} rows")
            print(f"Total sales: €{batch['total_sales_eur']}")
            break
        elif status == 'failed':
            print(f"Upload failed: {batch['error_summary']}")
            break

        time.sleep(2)  # Poll every 2 seconds

# Usage
upload_and_wait('sales_data.xlsx', 'YOUR_TOKEN')
```

### Batch Upload Multiple Files (JavaScript)

```javascript
async function uploadMultipleFiles(files, token) {
  const uploadPromises = files.map(async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', 'append');

    const response = await fetch('/api/uploads', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    return response.json();
  });

  const results = await Promise.all(uploadPromises);
  console.log(`Uploaded ${results.length} files`);
  return results.map(r => r.batch_id);
}

// Usage
const fileInput = document.querySelector('#fileInput');
const batchIds = await uploadMultipleFiles(fileInput.files, token);
```

---

## Related Documentation

- [API Overview](./README.md)
- [BIBBI Reseller Uploads](./bibbi-uploads.md)
- [Data Processing Pipeline](../architecture/data-processing-pipeline.md)
- [Vendor Formats Reference](../reference/vendor-formats.md)
- [Troubleshooting Upload Errors](../reference/troubleshooting/common-errors.md)
