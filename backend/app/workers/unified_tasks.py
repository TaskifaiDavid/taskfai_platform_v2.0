"""
Unified Upload Processing Tasks

Single worker for processing both D2C (demo) and B2B (BIBBI reseller) uploads.
Uses shared upload_pipeline utilities to eliminate code duplication.

Refactored from 3 separate worker files (tasks.py, bibbi_tasks.py, unified_tasks.py)
to reduce code duplication and improve maintainability.
"""

from typing import Dict, Any, Optional

from app.workers.celery_app import celery_app
from app.workers.upload_pipeline import upload_pipeline, UploadContext


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
    # Create upload context
    context = UploadContext(
        batch_id=batch_id,
        user_id=user_id,
        filename=filename,
        tenant_id=tenant_id,
        reseller_id=reseller_id
    )

    print(f"[Unified] Processing batch={batch_id}, file={filename}, reseller_id={reseller_id}, tenant={tenant_id}")

    # Route to appropriate processor based on context
    if reseller_id:
        # BIBBI reseller upload - B2B processing
        print(f"[Unified] Routing to BIBBI processor for reseller: {reseller_id}")

        def processor_fn(ctx):
            return _process_bibbi(ctx)
    else:
        # Demo D2C upload - standard ecommerce processing
        print(f"[Unified] Routing to demo processor for tenant: {tenant_id}")

        def processor_fn(ctx):
            return _process_demo(ctx)

    # Execute pipeline
    return upload_pipeline.process_upload(
        context=context,
        file_content_b64=file_content_b64,
        processor_fn=processor_fn
    )


def _process_demo(context: UploadContext) -> Dict[str, Any]:
    """
    Process demo D2C upload (online sales data)

    Uses demo-specific processors for standard ecommerce data.
    Inserts directly into ecommerce_orders table.

    Args:
        context: Upload context with file path and vendor

    Returns:
        Processing result dictionary
    """
    # LAZY IMPORT: Load only when executing demo path
    from app.core.worker_db import get_worker_supabase_client

    print(f"[Demo] Processing vendor={context.detected_vendor}")

    # Get processor instance
    processor = upload_pipeline.get_demo_processor(context.detected_vendor)

    # Process file - FIXED: Add missing batch_id parameter
    print(f"[Demo] Processing file with {context.detected_vendor} processor")
    processed_records = processor.process(context.file_path, context.user_id, context.batch_id)
    print(f"[Demo] Processed {len(processed_records)} records")

    # Insert into ecommerce_orders table
    supabase = get_worker_supabase_client(context.tenant_id)

    if processed_records:
        result = supabase.table("ecommerce_orders").insert(processed_records).execute()
        inserted_count = len(result.data) if result.data else 0
        print(f"[Demo] Inserted {inserted_count} orders")
    else:
        inserted_count = 0

    # Update batch status
    upload_pipeline.update_batch_status(
        batch_id=context.batch_id,
        status="completed",
        tenant_id=context.tenant_id,
        records_processed=len(processed_records),
        vendor_name=context.detected_vendor
    )

    print("[Demo] Processing complete")

    return {
        "status": "completed",
        "records_processed": len(processed_records),
        "records_inserted": inserted_count,
        "vendor": context.detected_vendor
    }


def _process_bibbi(context: UploadContext) -> Dict[str, Any]:
    """
    Process BIBBI reseller upload (B2B data)

    Uses BIBBI-specific services for validation, staging, and insertion.
    Full 8-phase pipeline: staging → detection → routing → processing →
    store creation → validation → insertion → status update

    Args:
        context: Upload context with file path and vendor

    Returns:
        Processing result dictionary
    """
    # LAZY IMPORT: Load BIBBI services only when executing BIBBI path
    from app.services.bibbi import (
        get_staging_service,
        get_validation_service,
        get_error_report_service,
        get_store_service,
        get_sales_insertion_service,
    )

    print(f"[BIBBI] Processing vendor={context.detected_vendor}, reseller={context.reseller_id}")

    # Get processor instance
    processor = upload_pipeline.get_bibbi_processor(context.detected_vendor)

    # Process file with vendor processor
    print(f"[BIBBI] Parsing file with {context.detected_vendor} processor")
    parsed_records = processor.process(context.file_path, context.reseller_id, context.tenant_id)
    print(f"[BIBBI] Parsed {len(parsed_records)} records")

    # Stage records
    staging_service = get_staging_service()
    staging_service.clear_staging(context.batch_id)
    staging_service.stage_records(context.batch_id, parsed_records)
    print(f"[BIBBI] Staged {len(parsed_records)} records")

    # Validate records
    validation_service = get_validation_service()
    validation_results = validation_service.validate_batch(context.batch_id)
    print(f"[BIBBI] Validation: {validation_results['valid_count']} valid, {validation_results['error_count']} errors")

    # Generate error report if needed
    if validation_results['error_count'] > 0:
        error_report_service = get_error_report_service()
        error_report = error_report_service.generate_report(context.batch_id)
        print(f"[BIBBI] Generated error report with {len(error_report)} issues")

    # Store valid records in permanent tables
    store_service = get_store_service()
    stored_count = store_service.store_valid_records(context.batch_id)
    print(f"[BIBBI] Stored {stored_count} valid records")

    # Insert sales data
    sales_service = get_sales_insertion_service()
    sales_count = sales_service.insert_sales_from_batch(context.batch_id)
    print(f"[BIBBI] Inserted {sales_count} sales records")

    # Determine final status
    final_status = "completed" if validation_results['error_count'] == 0 else "completed_with_errors"

    # Update batch status
    upload_pipeline.update_batch_status(
        batch_id=context.batch_id,
        status=final_status,
        tenant_id=context.tenant_id,
        records_processed=len(parsed_records),
        records_valid=validation_results['valid_count'],
        records_invalid=validation_results['error_count']
    )

    print(f"[BIBBI] Processing complete: {final_status}")

    return {
        "status": final_status,
        "records_processed": len(parsed_records),
        "records_valid": validation_results['valid_count'],
        "records_invalid": validation_results['error_count'],
        "sales_inserted": sales_count
    }
