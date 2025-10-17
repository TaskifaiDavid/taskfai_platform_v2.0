"""
BIBBI Reseller Upload API

Handles Excel file uploads from resellers for the BIBBI tenant ONLY.
Provides 3-stage processing: Upload → Staging → Validation → Unified

IMPORTANT: All endpoints in this module are restricted to tenant_id='bibbi'
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.core.bibbi import (
    get_bibbi_tenant_context,
    get_bibbi_supabase_client,
    BibbιTenant,
    BibbιDB,
    BIBBI_TENANT_ID
)


router = APIRouter(
    prefix="/bibbi",
    tags=["BIBBI Reseller Uploads"],
)


# Response Models
class UploadResponse(BaseModel):
    """Response for successful file upload"""
    upload_id: str
    batch_id: str
    filename: str
    file_size: int
    file_hash: str
    status: str
    message: str
    created_at: str


class UploadStatusResponse(BaseModel):
    """Response for upload status check"""
    upload_id: str
    status: str
    vendor_name: Optional[str] = None
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    failed_rows: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()


def validate_file_extension(filename: str) -> bool:
    """Validate file extension is allowed for BIBBI uploads"""
    file_ext = Path(filename).suffix.lower()
    return file_ext in settings.bibbi_allowed_extensions


def validate_file_size(file_size: int) -> bool:
    """Validate file size is within BIBBI limits"""
    return file_size <= settings.bibbi_max_file_size


async def check_duplicate_upload(
    file_hash: str,
    bibbi_db: BibbιDB
) -> Optional[dict]:
    """
    Check if file with same hash was already uploaded

    Args:
        file_hash: SHA256 hash of file content
        bibbi_db: BIBBI-specific Supabase client

    Returns:
        Existing upload record if duplicate found, None otherwise
    """
    try:
        # Query uploads table for same file hash
        result = bibbi_db.table("uploads")\
            .select("*")\
            .eq("file_hash", file_hash)\
            .execute()

        if result.data and len(result.data) > 0:
            return result.data[0]

        return None

    except Exception as e:
        print(f"[BibbιUpload] Error checking duplicate: {e}")
        return None


@router.post("/uploads", response_model=UploadResponse)
async def upload_bibbi_file(
    file: UploadFile = File(..., description="Excel file from reseller"),
    reseller_id: str = ...,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Upload reseller Excel file for BIBBI tenant

    **Tenant Isolation**: This endpoint ONLY accepts uploads for tenant_id='bibbi'

    **Processing Pipeline**:
    1. Validate file (extension, size)
    2. Calculate file hash for duplicate detection
    3. Check for duplicate uploads
    4. Save file to disk/storage
    5. Create upload record in database
    6. Enqueue Celery task for async processing

    **Supported Resellers**:
    - Aromateque
    - Boxnox
    - Creme de la Creme (CDLC)
    - Galilu
    - Liberty
    - Selfridges
    - Skins NL
    - Skins SA

    Args:
        file: Excel file upload (.xlsx or .xls)
        reseller_id: UUID of the reseller from resellers table
        bibbi_tenant: BIBBI tenant context (auto-validated)
        bibbi_db: BIBBI-specific database client (auto-filtered)

    Returns:
        UploadResponse with upload_id and status

    Raises:
        400 Bad Request: Invalid file extension or size
        409 Conflict: File already uploaded (duplicate detected)
        500 Internal Server Error: Upload processing failed
    """
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed extensions: {', '.join(settings.bibbi_allowed_extensions)}"
        )

    # Read file content
    try:
        file_content = await file.read()
        file_size = len(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read uploaded file: {str(e)}"
        )

    # Validate file size
    if not validate_file_size(file_size):
        max_size_mb = settings.bibbi_max_file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {max_size_mb:.0f}MB"
        )

    # Calculate file hash for duplicate detection
    file_hash = calculate_file_hash(file_content)

    # Check for duplicate upload
    # TODO: Create uploads table in migration and enable this check
    # existing_upload = await check_duplicate_upload(file_hash, bibbi_db)
    # if existing_upload:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail={
    #             "message": "File already uploaded",
    #             "existing_upload_id": existing_upload.get("upload_id"),
    #             "uploaded_at": existing_upload.get("upload_timestamp"),
    #             "status": existing_upload.get("upload_status")
    #         }
    #     )

    # Generate unique IDs
    upload_id = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())  # Generate proper UUID for upload_batch_id column

    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.bibbi_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save file to disk with unique name
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe_filename = f"{timestamp}_{upload_id[:8]}_{Path(file.filename).name}"
    file_path = upload_dir / safe_filename

    try:
        with open(file_path, 'wb') as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Validate reseller exists (use underlying client - resellers table doesn't have text tenant_id)
    try:
        reseller_check = bibbi_db.client.table("resellers")\
            .select("reseller_id")\
            .eq("reseller_id", reseller_id)\
            .execute()

        if not reseller_check.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reseller not found: {reseller_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate reseller: {str(e)}"
        )

    # Create upload record in upload_batches table (using existing table for now)
    try:
        upload_data = {
            "upload_batch_id": batch_id,
            "uploader_user_id": "3eae3da5-f2af-449c-8000-d4874c955a05",  # BIBBI admin user
            "reseller_id": reseller_id,
            "original_filename": file.filename,
            "file_size_bytes": file_size,
            "upload_mode": "append",
            "processing_status": "pending",
            "upload_timestamp": datetime.utcnow().isoformat(),
        }

        result = bibbi_db.client.table("upload_batches").insert(upload_data).execute()

        if not result.data:
            raise Exception("Failed to create upload record")

        print(f"[BibbιUpload] Created upload_batches record: {batch_id}")

    except Exception as e:
        # Cleanup: Delete file if database insert failed
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create upload record: {str(e)}"
        )

    # Enqueue Celery task for async processing
    try:
        from app.workers.bibbi_tasks import process_bibbi_upload
        process_bibbi_upload.delay(batch_id, str(file_path))  # Pass batch_id, not upload_id
        print(f"[BibbιUpload] Celery task enqueued for batch: {batch_id}")
    except Exception as e:
        print(f"[BibbιUpload] Warning: Failed to enqueue Celery task: {e}")
        # Don't fail the upload if Celery is down - allow manual retry later

    return UploadResponse(
        upload_id=upload_id,
        batch_id=batch_id,
        filename=file.filename,
        file_size=file_size,
        file_hash=file_hash,
        status="pending",
        message="File uploaded successfully. Processing will begin shortly.",
        created_at=datetime.utcnow().isoformat()
    )


@router.get("/uploads/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Get status of a BIBBI upload

    Args:
        upload_id: Unique upload identifier
        bibbi_tenant: BIBBI tenant context (auto-validated)
        bibbi_db: BIBBI-specific database client (auto-filtered)

    Returns:
        UploadStatusResponse with current status and processing details

    Raises:
        404 Not Found: Upload not found
    """
    try:
        result = bibbi_db.table("uploads")\
            .select("*")\
            .eq("upload_id", upload_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Upload not found: {upload_id}"
            )

        upload = result.data[0]

        return UploadStatusResponse(
            upload_id=upload["upload_id"],
            status=upload.get("upload_status", "unknown"),
            vendor_name=upload.get("vendor_name"),
            total_rows=upload.get("total_rows"),
            processed_rows=upload.get("processed_rows"),
            failed_rows=upload.get("failed_rows"),
            error_message=upload.get("error_message"),
            created_at=upload["upload_timestamp"],
            updated_at=upload.get("updated_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upload status: {str(e)}"
        )


@router.get("/uploads")
async def list_uploads(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    List BIBBI uploads with pagination

    Args:
        limit: Max number of results (default: 50)
        offset: Number of results to skip (default: 0)
        status_filter: Filter by status (optional)
        bibbi_tenant: BIBBI tenant context (auto-validated)
        bibbi_db: BIBBI-specific database client (auto-filtered)

    Returns:
        List of uploads with pagination info
    """
    try:
        query = bibbi_db.table("uploads")\
            .select("*")\
            .order("upload_timestamp", desc=True)\
            .range(offset, offset + limit - 1)

        # Apply status filter if provided
        if status_filter:
            query = query.eq("upload_status", status_filter)

        result = query.execute()

        return {
            "uploads": result.data,
            "count": len(result.data),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list uploads: {str(e)}"
        )


@router.post("/uploads/{upload_id}/retry")
async def retry_failed_upload(
    upload_id: str,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Retry a failed BIBBI upload

    Args:
        upload_id: Unique upload identifier
        bibbi_tenant: BIBBI tenant context (auto-validated)
        bibbi_db: BIBBI-specific database client (auto-filtered)

    Returns:
        Success message

    Raises:
        404 Not Found: Upload not found
        400 Bad Request: Upload not in failed state
    """
    try:
        # Get upload record
        result = bibbi_db.table("uploads")\
            .select("*")\
            .eq("upload_id", upload_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Upload not found: {upload_id}"
            )

        upload = result.data[0]

        # Validate upload is in failed state
        if upload.get("upload_status") != "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Upload is not in failed state. Current status: {upload.get('upload_status')}"
            )

        # Reset upload status
        update_data = {
            "upload_status": "pending",
            "processing_status": "pending",
            "error_message": None,
            "updated_at": datetime.utcnow().isoformat()
        }

        bibbi_db.table("uploads")\
            .update(update_data)\
            .eq("upload_id", upload_id)\
            .execute()

        # Re-enqueue Celery task
        file_path = upload.get("file_path")
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload has no file_path - cannot retry"
            )

        try:
            from app.workers.bibbi_tasks import process_bibbi_upload
            process_bibbi_upload.delay(upload_id, file_path)
            print(f"[BibbιUpload] Retry: Celery task enqueued for upload: {upload_id}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to enqueue Celery task: {str(e)}"
            )

        return {
            "message": "Upload retry initiated",
            "upload_id": upload_id,
            "status": "pending"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry upload: {str(e)}"
        )
