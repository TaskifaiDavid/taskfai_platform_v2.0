"""
File upload API endpoints
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from typing import Optional
import uuid
from datetime import datetime

from app.core.dependencies import get_current_user, get_supabase_client
from app.services.file_validator import validate_upload_file
from app.services.file_storage import file_storage

router = APIRouter(tags=["uploads"])


@router.post("/uploads")
async def upload_file(
    file: UploadFile = File(...),
    mode: str = Form(...),  # "append" or "replace"
    reseller_id: Optional[str] = Form(None),  # Optional BIBBI reseller ID
    tenant_id: Optional[str] = Form(None),  # Optional tenant override
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Unified upload endpoint for both D2C (demo) and B2B (BIBBI reseller) data

    Args:
        file: Uploaded file (Excel or CSV)
        mode: Upload mode - "append" or "replace"
        reseller_id: Optional BIBBI reseller identifier (triggers B2B processing)
        tenant_id: Optional tenant context override
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        Upload batch information including batch_id
    """
    # Validate mode
    if mode not in ["append", "replace"]:
        raise HTTPException(status_code=400, detail="Mode must be 'append' or 'replace'")

    # Get file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file
    is_valid, error_message = validate_upload_file(file.filename, file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # Generate batch ID
    batch_id = str(uuid.uuid4())
    user_id = current_user["user_id"]

    # Save file to temporary storage
    try:
        file_path = file_storage.save_file(
            user_id=user_id,
            batch_id=batch_id,
            filename=file.filename,
            file_content=file_content
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Determine tenant context for correct table/column mapping
    if not tenant_id:
        # Extract from current user's tenant context if available
        tenant_id = current_user.get("tenant_id", "demo")

    # Create upload record (table structure differs by tenant)
    try:
        if tenant_id == "bibbi":
            # BIBBI uses 'uploads' table with different column names
            batch_data = {
                "id": batch_id,  # BIBBI uses 'id' not 'upload_batch_id'
                "user_id": user_id,  # BIBBI uses 'user_id' not 'uploader_user_id'
                "filename": file.filename,  # BIBBI uses 'filename' not 'original_filename'
                "file_size": file_size,  # BIBBI uses 'file_size' not 'file_size_bytes'
                "status": "pending",  # BIBBI uses 'status' not 'processing_status'
                "uploaded_at": datetime.utcnow().isoformat()  # BIBBI uses 'uploaded_at' not 'upload_timestamp'
            }
            table_name = "uploads"
        else:
            # Demo/other tenants use 'upload_batches' table
            batch_data = {
                "upload_batch_id": batch_id,
                "uploader_user_id": user_id,
                "original_filename": file.filename,
                "file_size_bytes": file_size,
                "upload_mode": mode,
                "processing_status": "pending",
                "upload_timestamp": datetime.utcnow().isoformat()
            }
            table_name = "upload_batches"

        result = supabase.table(table_name).insert(batch_data).execute()

        if not result.data:
            raise Exception(f"Failed to create {table_name} record")

    except Exception as e:
        # Cleanup file if database insert fails
        file_storage.cleanup_batch(user_id, batch_id)
        raise HTTPException(status_code=500, detail=f"Failed to create batch record: {str(e)}")

    # Trigger unified Celery worker with intelligent routing
    # Pass file as base64 to worker (separate container, can't access /tmp/uploads)
    import base64
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')

    from app.workers.unified_tasks import process_unified_upload
    process_unified_upload.delay(
        batch_id=batch_id,
        user_id=user_id,
        file_content_b64=file_content_b64,
        filename=file.filename,
        reseller_id=reseller_id,
        tenant_id=tenant_id
    )

    return {
        "success": True,
        "batch_id": batch_id,
        "filename": file.filename,
        "file_size": file_size,
        "mode": mode,
        "status": "pending",
        "message": "File uploaded successfully. Processing will begin shortly."
    }


@router.get("/uploads/batches")
async def get_upload_batches(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Get user's upload batches

    Args:
        limit: Number of records to return
        offset: Pagination offset
        status: Filter by status (optional)
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        List of upload batches
    """
    user_id = current_user["user_id"]
    tenant_id = current_user.get("tenant_id", "demo")

    try:
        # Use correct table and column names per tenant
        if tenant_id == "bibbi":
            query = supabase.table("uploads").select("*").eq("user_id", user_id)
            status_col = "status"
            timestamp_col = "uploaded_at"
        else:
            query = supabase.table("upload_batches").select("*").eq("uploader_user_id", user_id)
            status_col = "processing_status"
            timestamp_col = "upload_timestamp"

        if status:
            query = query.eq(status_col, status)

        query = query.order(timestamp_col, desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        # Transform field names to match frontend expectations
        transformed_batches = []
        for batch in result.data:
            # Handle different table structures for BIBBI vs demo
            if tenant_id == "bibbi":
                # BIBBI uploads table structure
                transformed = {
                    'upload_batch_id': batch.get('id'),  # BIBBI uses 'id'
                    'uploader_user_id': batch.get('user_id'),  # BIBBI uses 'user_id'
                    'original_filename': batch.get('filename'),  # BIBBI uses 'filename'
                    'file_size_bytes': batch.get('file_size'),  # BIBBI uses 'file_size'
                    'vendor_name': batch.get('vendor_name'),  # Now available after migration
                    'upload_mode': 'append',  # BIBBI doesn't have upload_mode, default to append
                    'processing_status': batch.get('status'),  # BIBBI uses 'status'
                    'upload_timestamp': batch.get('uploaded_at'),  # BIBBI uses 'uploaded_at'
                    'processing_completed_at': batch.get('processing_completed_at'),
                    # BIBBI row count fields (same names)
                    'total_rows_parsed': batch.get('rows_total'),
                    'successful_inserts': batch.get('rows_inserted'),  # BIBBI uses 'rows_inserted'
                    'failed_inserts': batch.get('rows_invalid')  # BIBBI uses 'rows_invalid'
                }
            else:
                # Demo upload_batches table structure
                transformed = {
                    'upload_batch_id': batch.get('upload_batch_id'),
                    'uploader_user_id': batch.get('uploader_user_id'),
                    'original_filename': batch.get('original_filename'),
                    'file_size_bytes': batch.get('file_size_bytes'),
                    'vendor_name': batch.get('vendor_name'),
                    'upload_mode': batch.get('upload_mode'),
                    'processing_status': batch.get('processing_status'),
                    'upload_timestamp': batch.get('upload_timestamp'),
                    'processing_completed_at': batch.get('processing_completed_at'),
                    # Demo row count fields
                    'total_rows_parsed': batch.get('rows_total'),
                    'successful_inserts': batch.get('rows_processed'),
                    'failed_inserts': batch.get('rows_failed')
                }
            transformed_batches.append(transformed)

        return {
            "success": True,
            "batches": transformed_batches,
            "count": len(transformed_batches)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch batches: {str(e)}")


@router.get("/uploads/batches/{batch_id}")
async def get_upload_batch(
    batch_id: str,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Get specific upload batch details

    Args:
        batch_id: Batch identifier
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        Upload batch details
    """
    user_id = current_user["user_id"]
    tenant_id = current_user.get("tenant_id", "demo")

    try:
        # Use correct table and column names per tenant
        if tenant_id == "bibbi":
            result = supabase.table("uploads").select("*").eq("id", batch_id).eq("user_id", user_id).execute()
        else:
            result = supabase.table("upload_batches").select("*").eq("upload_batch_id", batch_id).eq("uploader_user_id", user_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")

        # Transform field names to match frontend expectations
        batch_data = result.data[0]

        # Handle different table structures for BIBBI vs demo
        if tenant_id == "bibbi":
            # BIBBI uploads table structure
            transformed_batch = {
                'upload_batch_id': batch_data.get('id'),
                'uploader_user_id': batch_data.get('user_id'),
                'original_filename': batch_data.get('filename'),
                'file_size_bytes': batch_data.get('file_size'),
                'vendor_name': batch_data.get('vendor_name'),
                'upload_mode': 'append',
                'processing_status': batch_data.get('status'),
                'upload_timestamp': batch_data.get('uploaded_at'),
                'processing_completed_at': batch_data.get('processing_completed_at'),
                'total_rows_parsed': batch_data.get('rows_total'),
                'successful_inserts': batch_data.get('rows_inserted'),
                'failed_inserts': batch_data.get('rows_invalid')
            }
        else:
            # Demo upload_batches table structure
            transformed_batch = {
                'upload_batch_id': batch_data.get('upload_batch_id'),
                'uploader_user_id': batch_data.get('uploader_user_id'),
                'original_filename': batch_data.get('original_filename'),
                'file_size_bytes': batch_data.get('file_size_bytes'),
                'vendor_name': batch_data.get('vendor_name'),
                'upload_mode': batch_data.get('upload_mode'),
                'processing_status': batch_data.get('processing_status'),
                'upload_timestamp': batch_data.get('upload_timestamp'),
                'processing_completed_at': batch_data.get('processing_completed_at'),
                'total_rows_parsed': batch_data.get('rows_total'),
                'successful_inserts': batch_data.get('rows_processed'),
                'failed_inserts': batch_data.get('rows_failed')
            }

        return {
            "success": True,
            "batch": transformed_batch
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch batch: {str(e)}")


@router.get("/uploads/{batch_id}/errors")
async def get_upload_errors(
    batch_id: str,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Get error reports for a specific upload batch

    Args:
        batch_id: Batch identifier
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        List of error reports
    """
    user_id = current_user["user_id"]

    try:
        # Verify batch belongs to user
        batch_result = supabase.table("upload_batches").select("upload_batch_id").eq("upload_batch_id", batch_id).eq("uploader_user_id", user_id).execute()

        if not batch_result.data:
            raise HTTPException(status_code=404, detail="Batch not found")

        # Get error reports
        errors_result = supabase.table("error_reports").select("*").eq("upload_batch_id", batch_id).order("row_number_in_file").execute()

        return {
            "success": True,
            "errors": errors_result.data or [],
            "count": len(errors_result.data) if errors_result.data else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch errors: {str(e)}")


@router.delete("/uploads/batches/{batch_id}")
async def delete_upload_batch(
    batch_id: str,
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Delete upload batch and associated files

    Args:
        batch_id: Batch identifier
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        Deletion confirmation
    """
    user_id = current_user["user_id"]

    try:
        # Delete from database
        result = supabase.table("upload_batches").delete().eq("upload_batch_id", batch_id).eq("uploader_user_id", user_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")

        # Cleanup files
        file_storage.cleanup_batch(user_id, batch_id)

        return {
            "success": True,
            "message": "Batch deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete batch: {str(e)}")


@router.post("/uploads/cleanup-stuck")
async def cleanup_stuck_uploads(
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Clean up stuck pending uploads (older than 10 minutes)

    Args:
        current_user: Authenticated user
        supabase: Supabase client

    Returns:
        Number of uploads cleaned up
    """
    user_id = current_user["user_id"]

    try:
        from datetime import datetime, timedelta

        # Calculate cutoff time (10 minutes ago)
        cutoff_time = datetime.now() - timedelta(minutes=10)

        # Get all pending uploads for this user
        result = supabase.table("upload_batches")\
            .select("*")\
            .eq("uploader_user_id", user_id)\
            .eq("processing_status", "pending")\
            .execute()

        if not result.data:
            return {
                "success": True,
                "cleaned_count": 0,
                "message": "No stuck uploads found"
            }

        # Filter for stuck uploads (older than cutoff)
        stuck_batches = []
        for batch in result.data:
            upload_time = datetime.fromisoformat(batch['upload_timestamp'].replace('Z', '+00:00'))
            if upload_time.replace(tzinfo=None) < cutoff_time:
                stuck_batches.append(batch['upload_batch_id'])

        # Update all stuck batches to failed status
        cleaned_count = 0
        for batch_id in stuck_batches:
            update_result = supabase.table("upload_batches").update({
                "processing_status": "failed",
                "error_summary": "Processing timeout - marked as failed during cleanup",
                "processing_completed_at": datetime.now().isoformat()
            }).eq("upload_batch_id", batch_id).execute()

            if update_result.data:
                cleaned_count += 1

        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"Cleaned up {cleaned_count} stuck upload(s)"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup uploads: {str(e)}")
