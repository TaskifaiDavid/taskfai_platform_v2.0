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

    Routes to appropriate processor based on vendor detection and reseller lookup:
    - BIBBI processor if reseller_id detected (B2B reseller data like Liberty)
    - Demo processor if no reseller_id (D2C data)

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

    try:
        # Phase 1: Prepare context (vendor detection + reseller lookup)
        # This auto-assigns reseller_id for Liberty and other BIBBI vendors
        context = upload_pipeline.prepare_context(context, file_content_b64)

        # Phase 2: Route to appropriate processor based on AUTO-DETECTED reseller_id
        # NOTE: reseller_id may have been auto-assigned during prepare_context()
        if context.reseller_id:
            # BIBBI reseller upload (B2B data)
            print(f"[Unified] ✓ Routing to BIBBI processor for reseller={context.reseller_id}, vendor={context.detected_vendor}")

            def processor_fn(ctx):
                return _process_bibbi(ctx)
        else:
            # Demo D2C upload - standard ecommerce processing
            print(f"[Unified] Routing to demo processor for tenant={tenant_id}, vendor={context.detected_vendor}")

            def processor_fn(ctx):
                return _process_demo(ctx)

        # Phase 3: Execute processor
        return upload_pipeline.execute_processor(context, processor_fn)

    except Exception as e:
        return upload_pipeline.handle_upload_error(context, e)


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
        records_processed=len(processed_records)
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

    Full BIBBI pipeline:
    1. Parse file with vendor processor
    2. Create/update store records
    3. Insert validated sales data into sales_unified
    4. Update batch status with statistics

    Args:
        context: Upload context with file path and vendor

    Returns:
        Processing result dictionary
    """
    # LAZY IMPORT: Load only when executing BIBBI path
    from app.core.worker_db import get_worker_supabase_client
    from app.services.bibbi.store_service import BibbιStoreService
    from app.services.bibbi.sales_insertion_service import BibbιSalesInsertionService

    print(f"[BIBBI] Processing vendor={context.detected_vendor}, reseller={context.reseller_id}")

    # Get BIBBI database client
    bibbi_db = get_worker_supabase_client(context.tenant_id)

    # Get processor instance
    processor = upload_pipeline.get_bibbi_processor(context.detected_vendor, context.reseller_id)

    # STEP 1: Parse file with vendor processor
    print(f"[BIBBI] Step 1: Parsing file with {context.detected_vendor} processor")
    processing_result = processor.process(context.file_path, context.batch_id)

    # Extract records from ProcessingResult
    parsed_records = processing_result.transformed_data
    print(f"[BIBBI] Parsed {len(parsed_records)} records ({processing_result.successful_rows} success, {processing_result.failed_rows} failed)")
    print(f"[BIBBI] Detected {len(processing_result.stores)} stores")

    # STEP 2: Create/update store records and build store_identifier → store_id mapping
    print(f"[BIBBI] Step 2: Creating/updating {len(processing_result.stores)} stores")
    store_service = BibbιStoreService(bibbi_db)

    # Use bulk operation to get store_identifier → store_id mapping
    store_mapping = store_service.bulk_get_or_create_stores(
        reseller_id=context.reseller_id,
        stores_data=processing_result.stores
    )

    created_stores = len(store_mapping)
    print(f"[BIBBI] Created/updated {created_stores} stores")
    print(f"[BIBBI] Store mapping: {store_mapping}")

    # STEP 3: Insert validated sales data into sales_unified
    print(f"[BIBBI] Step 3: Inserting {len(parsed_records)} records into sales_unified")
    insertion_service = BibbιSalesInsertionService(bibbi_db)

    try:
        insertion_result = insertion_service.insert_validated_sales(
            validated_data=parsed_records,
            store_mapping=store_mapping  # Pass mapping to convert store_identifier → store_id
        )

        rows_inserted = insertion_result.inserted_rows
        rows_duplicate = insertion_result.duplicate_rows
        rows_failed = insertion_result.failed_rows

        print(f"[BIBBI] Insertion complete: {rows_inserted} inserted, {rows_duplicate} duplicates, {rows_failed} failed")

        final_status = "completed" if rows_failed == 0 else "completed_with_errors"

    except Exception as e:
        print(f"[BIBBI] ERROR: Sales insertion failed: {e}")
        import traceback
        traceback.print_exc()

        rows_inserted = 0
        rows_duplicate = 0
        rows_failed = len(parsed_records)
        final_status = "failed"

    # STEP 4: Update batch status with statistics
    upload_pipeline.update_batch_status(
        batch_id=context.batch_id,
        status=final_status,
        tenant_id=context.tenant_id,
        rows_processed=processing_result.successful_rows,
        rows_total=processing_result.total_rows,
        rows_valid=rows_inserted,
        rows_invalid=processing_result.failed_rows,
        rows_inserted=rows_inserted,
        rows_duplicate=rows_duplicate,
        parser_class=f"{context.detected_vendor}_processor",
        parser_version="1.0"
    )

    print(f"[BIBBI] ✅ Pipeline complete: {final_status}")
    print(f"[BIBBI] Summary: {rows_inserted} records inserted into sales_unified")

    return {
        "status": final_status,
        "records_processed": processing_result.successful_rows,
        "records_total": processing_result.total_rows,
        "records_inserted": rows_inserted,
        "records_duplicate": rows_duplicate,
        "records_failed": rows_failed,
        "stores_created": created_stores,
        "vendor": context.detected_vendor
    }
