"""
Celery background tasks
"""

import traceback
from datetime import datetime
from typing import Dict, Any

from app.workers.celery_app import celery_app
from app.db import get_supabase
from app.services.file_storage import file_storage


@celery_app.task(bind=True, name="app.workers.tasks.process_upload")
def process_upload(self, batch_id: str, user_id: str) -> Dict[str, Any]:
    """
    Process uploaded file in the background

    Args:
        batch_id: Upload batch identifier
        user_id: User identifier

    Returns:
        Processing result dictionary
    """
    supabase = get_supabase()

    try:
        # Update status to processing
        supabase.table("upload_batches").update({
            "processing_status": "processing",
            "started_processing_at": datetime.utcnow().isoformat()
        }).eq("batch_id", batch_id).execute()

        # Get batch details
        batch_result = supabase.table("upload_batches").select("*").eq("batch_id", batch_id).execute()

        if not batch_result.data:
            raise Exception(f"Batch {batch_id} not found")

        batch = batch_result.data[0]
        file_path = batch["file_path"]
        filename = batch["filename"]

        # Vendor detection
        from app.services.vendors.detector import vendor_detector
        detected_vendor, confidence = vendor_detector.detect_vendor(file_path, filename)

        if not detected_vendor:
            raise Exception(f"Unable to detect vendor from file. Confidence: {confidence}")

        # Update batch with detected vendor
        supabase.table("upload_batches").update({
            "detected_vendor": detected_vendor
        }).eq("batch_id", batch_id).execute()

        # Process based on vendor
        if detected_vendor == "demo":
            from app.services.vendors.demo_processor import DemoProcessor
            from app.services.data_inserter import DataInserter

            processor = DemoProcessor()
            process_result = processor.process(file_path, user_id, batch_id)

            # Insert data
            inserter = DataInserter(supabase)

            # Check duplicates if in append mode
            transformed_data = process_result["transformed_data"]
            if batch["upload_mode"] == "append":
                transformed_data = inserter.check_duplicates(user_id, "online_sales", transformed_data)

            # Insert demo data into online_sales table
            successful, failed = inserter.insert_online_sales(transformed_data, batch["upload_mode"])

            result = {
                "total_rows": process_result["total_rows"],
                "successful_rows": successful,
                "failed_rows": failed + process_result["failed_rows"],
                "detected_vendor": detected_vendor,
                "errors": process_result["errors"]
            }
        elif detected_vendor == "boxnox":
            from app.services.vendors.boxnox_processor import BoxnoxProcessor
            from app.services.data_inserter import DataInserter

            processor = BoxnoxProcessor()
            process_result = processor.process(file_path, user_id, batch_id)

            # Insert data
            inserter = DataInserter(supabase)

            # Check duplicates if in append mode
            transformed_data = process_result["transformed_data"]
            if batch["upload_mode"] == "append":
                transformed_data = inserter.check_duplicates(user_id, "sellout_entries2", transformed_data)

            # Insert records
            successful, failed = inserter.insert_sellout_entries(transformed_data, batch["upload_mode"])

            result = {
                "total_rows": process_result["total_rows"],
                "successful_rows": successful,
                "failed_rows": failed + process_result["failed_rows"],
                "detected_vendor": detected_vendor,
                "errors": process_result["errors"]
            }
        else:
            raise Exception(f"Vendor '{detected_vendor}' processor not implemented yet")

        # Update batch with results
        supabase.table("upload_batches").update({
            "processing_status": "completed",
            "processed_at": datetime.utcnow().isoformat(),
            "total_rows": result["total_rows"],
            "successful_rows": result["successful_rows"],
            "failed_rows": result["failed_rows"],
            "detected_vendor": result["detected_vendor"]
        }).eq("batch_id", batch_id).execute()

        # Cleanup temporary files
        file_storage.cleanup_batch(user_id, batch_id)

        # Send success email notification
        send_email.delay(user_id, batch_id, "success")

        return {
            "success": True,
            "batch_id": batch_id,
            "result": result
        }

    except Exception as e:
        error_message = str(e)
        error_trace = traceback.format_exc()

        # Update batch with error
        supabase.table("upload_batches").update({
            "processing_status": "failed",
            "processed_at": datetime.utcnow().isoformat(),
            "error_message": error_message
        }).eq("batch_id", batch_id).execute()

        # Send failure email notification
        send_email.delay(user_id, batch_id, "failure")

        return {
            "success": False,
            "batch_id": batch_id,
            "error": error_message,
            "trace": error_trace
        }


@celery_app.task(name="app.workers.tasks.send_email")
def send_email(user_id: str, batch_id: str, status: str) -> Dict[str, Any]:
    """
    Send email notification

    Args:
        user_id: User identifier
        batch_id: Batch identifier
        status: Email type (success/failure)

    Returns:
        Email sending result
    """
    from app.services.email.notifier import email_notifier

    result = email_notifier.send_upload_notification(user_id, batch_id, status)

    return {
        "success": result.get("success", False),
        "user_id": user_id,
        "batch_id": batch_id,
        "status": status
    }


@celery_app.task(name="app.workers.tasks.cleanup_old_files")
def cleanup_old_files(days_old: int = 7) -> Dict[str, Any]:
    """
    Cleanup old temporary files

    Args:
        days_old: Remove files older than this many days

    Returns:
        Cleanup result
    """
    try:
        removed_count = file_storage.cleanup_old_files(days_old)

        return {
            "success": True,
            "removed_count": removed_count,
            "days_old": days_old
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
