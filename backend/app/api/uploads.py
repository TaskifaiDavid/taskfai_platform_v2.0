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

        return {
            "success": True,
            "batches": result.data,
            "count": len(result.data)
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

        return {
            "success": True,
            "batch": result.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch batch: {str(e)}")


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
