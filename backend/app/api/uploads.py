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
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Upload data file for processing

    Args:
        file: Uploaded file (Excel or CSV)
        mode: Upload mode - "append" or "replace"
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

    # Create upload batch record
    try:
        batch_data = {
            "upload_batch_id": batch_id,
            "uploader_user_id": user_id,
            "original_filename": file.filename,
            "file_size_bytes": file_size,
            "upload_mode": mode,
            "processing_status": "pending",
            "upload_timestamp": datetime.utcnow().isoformat()
        }

        result = supabase.table("upload_batches").insert(batch_data).execute()

        if not result.data:
            raise Exception("Failed to create upload batch record")

    except Exception as e:
        # Cleanup file if database insert fails
        file_storage.cleanup_batch(user_id, batch_id)
        raise HTTPException(status_code=500, detail=f"Failed to create batch record: {str(e)}")

    # Trigger Celery background processing task
    from app.workers.tasks import process_upload
    process_upload.delay(batch_id, user_id)

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

    try:
        query = supabase.table("upload_batches").select("*").eq("uploader_user_id", user_id)

        if status:
            query = query.eq("processing_status", status)

        query = query.order("upload_timestamp", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        # Transform field names to match frontend expectations
        transformed_batches = []
        for batch in result.data:
            transformed = batch.copy()
            # Map backend field names to frontend field names
            if 'rows_total' in batch:
                transformed['total_rows_parsed'] = batch['rows_total']
            if 'rows_processed' in batch:
                transformed['successful_inserts'] = batch['rows_processed']
            if 'rows_failed' in batch:
                transformed['failed_inserts'] = batch['rows_failed']
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

    try:
        result = supabase.table("upload_batches").select("*").eq("upload_batch_id", batch_id).eq("uploader_user_id", user_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Batch not found")

        # Transform field names to match frontend expectations
        batch = result.data[0].copy()
        if 'rows_total' in batch:
            batch['total_rows_parsed'] = batch['rows_total']
        if 'rows_processed' in batch:
            batch['successful_inserts'] = batch['rows_processed']
        if 'rows_failed' in batch:
            batch['failed_inserts'] = batch['rows_failed']

        return {
            "success": True,
            "batch": batch
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
