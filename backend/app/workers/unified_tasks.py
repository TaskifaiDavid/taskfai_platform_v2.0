"""
Unified Upload Processing Tasks

Consolidates demo and BIBBI upload processing into a single intelligent system.
Supports both D2C (demo) and B2B (BIBBI reseller) workflows.
"""

import base64
import hashlib
import os
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="app.workers.unified_tasks.process_unified_upload")
def process_unified_upload(
    self,
    batch_id: str,
    user_id: str,
    file_content_b64: str,
    filename: str,
    reseller_id: Optional[str] = None,
    tenant_id: str = "demo"
) -> Dict[str, Any]:
    """
    Unified upload processor with intelligent routing

    Routes to appropriate processor based on context:
    - BIBBI processor if reseller_id provided (B2B reseller data)
    - Demo processor if tenant_id='demo' and no reseller_id (D2C data)
    - Intelligent detection + routing for ambiguous cases

    Args:
        batch_id: Upload batch identifier
        user_id: User who uploaded the file
        file_content_b64: Base64-encoded file content
        filename: Original filename
        reseller_id: Optional BIBBI reseller identifier (triggers BIBBI processing)
        tenant_id: Tenant context (default: "demo")

    Returns:
        Dict containing processing results and status
    """
    # LAZY IMPORTS: Load heavy dependencies only when task executes
    from app.core.dependencies import get_supabase_client
    from app.services.vendors.detector import vendor_detector

    print(f"[UnifiedUpload] Processing batch_id={batch_id}, filename={filename}, reseller_id={reseller_id}, tenant_id={tenant_id}")

    try:
        # Decode file content
        file_content = base64.b64decode(file_content_b64)

        # Save temporary file for processing
        temp_dir = "/tmp/taskifai_uploads"
        os.makedirs(temp_dir, exist_ok=True)

        file_hash = hashlib.md5(file_content).hexdigest()
        file_path = os.path.join(temp_dir, f"{file_hash}_{filename}")

        with open(file_path, 'wb') as f:
            f.write(file_content)

        print(f"[UnifiedUpload] Saved temp file: {file_path}")

        # Detect vendor format
        detected_vendor, confidence = vendor_detector.detect_vendor(file_path, filename)
        print(f"[UnifiedUpload] Detected vendor: {detected_vendor} (confidence: {confidence})")

        if not detected_vendor:
            raise Exception(f"Unable to detect vendor from file. Confidence: {confidence}")

        # Route to appropriate processor based on context
        if reseller_id:
            # BIBBI reseller upload - route to BIBBI processor
            print(f"[UnifiedUpload] Routing to BIBBI processor for reseller: {reseller_id}")
            return _process_bibbi_upload(
                batch_id=batch_id,
                file_path=file_path,
                detected_vendor=detected_vendor,
                reseller_id=reseller_id,
                tenant_id=tenant_id
            )
        else:
            # Demo D2C upload - route to demo processor
            print(f"[UnifiedUpload] Routing to demo processor for tenant: {tenant_id}")
            return _process_demo_upload(
                batch_id=batch_id,
                user_id=user_id,
                file_path=file_path,
                filename=filename,
                detected_vendor=detected_vendor
            )

    except Exception as e:
        error_msg = f"Upload processing failed: {str(e)}"
        print(f"[UnifiedUpload] ERROR: {error_msg}")
        traceback.print_exc()

        # Update batch status to failed
        try:
            supabase = get_supabase_client()
            supabase.table("upload_batches").update({
                "processing_status": "failed",
                "error_message": error_msg,
                "processed_at": datetime.utcnow().isoformat()
            }).eq("upload_batch_id", batch_id).execute()
        except Exception as update_error:
            print(f"[UnifiedUpload] Failed to update batch status: {update_error}")

        raise


def _process_bibbi_upload(
    batch_id: str,
    file_path: str,
    detected_vendor: str,
    reseller_id: str,
    tenant_id: str
) -> Dict[str, Any]:
    """
    Process BIBBI reseller upload (B2B data)

    Uses BIBBI-specific services for validation, staging, and insertion.
    """
    # LAZY IMPORT: Load BIBBI services only when needed
    from app.services.bibbi import (
        get_staging_service,
        route_bibbi_vendor,
        get_validation_service,
        get_error_report_service,
        get_store_service,
        get_sales_insertion_service,
    )

    print(f"[BIBBI] Processing vendor={detected_vendor}, reseller={reseller_id}")

    try:
        # 1. Route to vendor-specific processor
        processor = route_bibbi_vendor(detected_vendor)
        if not processor:
            raise Exception(f"No BIBBI processor available for vendor: {detected_vendor}")

        # 2. Parse file with vendor processor
        print(f"[BIBBI] Parsing file with {detected_vendor} processor")
        parsed_records = processor.process(file_path, reseller_id, tenant_id)
        print(f"[BIBBI] Parsed {len(parsed_records)} records")

        # 3. Stage records
        staging_service = get_staging_service()
        staging_service.clear_staging(batch_id)
        staging_service.stage_records(batch_id, parsed_records)
        print(f"[BIBBI] Staged {len(parsed_records)} records")

        # 4. Validate records
        validation_service = get_validation_service()
        validation_results = validation_service.validate_batch(batch_id)
        print(f"[BIBBI] Validation: {validation_results['valid_count']} valid, {validation_results['error_count']} errors")

        # 5. Generate error report if needed
        if validation_results['error_count'] > 0:
            error_report_service = get_error_report_service()
            error_report = error_report_service.generate_report(batch_id)
            print(f"[BIBBI] Generated error report with {len(error_report)} issues")

        # 6. Store valid records in permanent tables
        store_service = get_store_service()
        stored_count = store_service.store_valid_records(batch_id)
        print(f"[BIBBI] Stored {stored_count} valid records")

        # 7. Insert sales data
        sales_service = get_sales_insertion_service()
        sales_count = sales_service.insert_sales_from_batch(batch_id)
        print(f"[BIBBI] Inserted {sales_count} sales records")

        # 8. Update batch status
        from app.core.dependencies import get_supabase_client
        supabase = get_supabase_client()

        final_status = "completed" if validation_results['error_count'] == 0 else "completed_with_errors"

        supabase.table("upload_batches").update({
            "processing_status": final_status,
            "processed_at": datetime.utcnow().isoformat(),
            "records_processed": len(parsed_records),
            "records_valid": validation_results['valid_count'],
            "records_invalid": validation_results['error_count']
        }).eq("upload_batch_id", batch_id).execute()

        print(f"[BIBBI] Processing complete: {final_status}")

        return {
            "status": final_status,
            "records_processed": len(parsed_records),
            "records_valid": validation_results['valid_count'],
            "records_invalid": validation_results['error_count'],
            "sales_inserted": sales_count
        }

    except Exception as e:
        error_msg = f"BIBBI processing failed: {str(e)}"
        print(f"[BIBBI] ERROR: {error_msg}")
        traceback.print_exc()

        # Update batch status
        from app.core.dependencies import get_supabase_client
        supabase = get_supabase_client()
        supabase.table("upload_batches").update({
            "processing_status": "failed",
            "error_message": error_msg,
            "processed_at": datetime.utcnow().isoformat()
        }).eq("upload_batch_id", batch_id).execute()

        raise


def _process_demo_upload(
    batch_id: str,
    user_id: str,
    file_path: str,
    filename: str,
    detected_vendor: str
) -> Dict[str, Any]:
    """
    Process demo D2C upload (online sales data)

    Uses demo-specific processors for standard ecommerce data.
    """
    # LAZY IMPORT: Load demo services only when needed
    from app.core.dependencies import get_supabase_client
    from app.services.vendors.demo_processor import DemoProcessor
    from app.services.vendors.online_processor import OnlineProcessor
    from app.services.vendors.boxnox_processor import BoxnoxProcessor

    print(f"[Demo] Processing vendor={detected_vendor}")

    try:
        # Route to appropriate demo processor
        if detected_vendor == "demo":
            processor = DemoProcessor()
        elif detected_vendor == "online":
            processor = OnlineProcessor()
        elif detected_vendor == "boxnox":
            processor = BoxnoxProcessor()
        else:
            raise Exception(f"No demo processor available for vendor: {detected_vendor}")

        # Process file
        print(f"[Demo] Processing with {detected_vendor} processor")
        processed_records = processor.process(file_path, user_id)
        print(f"[Demo] Processed {len(processed_records)} records")

        # Insert into ecommerce_orders table
        supabase = get_supabase_client()

        if processed_records:
            result = supabase.table("ecommerce_orders").insert(processed_records).execute()
            inserted_count = len(result.data) if result.data else 0
            print(f"[Demo] Inserted {inserted_count} orders")
        else:
            inserted_count = 0

        # Update batch status
        supabase.table("upload_batches").update({
            "processing_status": "completed",
            "processed_at": datetime.utcnow().isoformat(),
            "records_processed": len(processed_records),
            "vendor_name": detected_vendor
        }).eq("upload_batch_id", batch_id).execute()

        print(f"[Demo] Processing complete")

        # Clean up temp file
        try:
            os.remove(file_path)
            print(f"[Demo] Cleaned up temp file: {file_path}")
        except Exception as cleanup_error:
            print(f"[Demo] Failed to clean up temp file: {cleanup_error}")

        return {
            "status": "completed",
            "records_processed": len(processed_records),
            "records_inserted": inserted_count,
            "vendor": detected_vendor
        }

    except Exception as e:
        error_msg = f"Demo processing failed: {str(e)}"
        print(f"[Demo] ERROR: {error_msg}")
        traceback.print_exc()

        # Update batch status
        supabase = get_supabase_client()
        supabase.table("upload_batches").update({
            "processing_status": "failed",
            "error_message": error_msg,
            "processed_at": datetime.utcnow().isoformat()
        }).eq("upload_batch_id", batch_id).execute()

        raise
