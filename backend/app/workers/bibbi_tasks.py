"""
BIBBI Celery Background Tasks

Async processing for BIBBI reseller Excel uploads with full pipeline integration.

Pipeline Flow:
1. Staging - Extract file metadata
2. Detection - Identify vendor/reseller
3. Routing - Route to appropriate processor
4. Processing - Extract and transform rows
5. Store Creation - Auto-create stores
6. Validation - 4-layer validation
7. Insertion - Batch insert into sales_unified
8. Status Update - Update upload record

Task: process_bibbi_upload
"""

import os
import traceback
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from app.workers.celery_app import celery_app
from app.core.bibbi import get_bibbi_db, BIBBI_TENANT_ID
from app.services.bibbi import (
    get_staging_service,
    detect_bibbi_vendor,
    route_bibbi_vendor,
    get_validation_service,
    get_error_report_service,
    get_store_service,
    get_sales_insertion_service,
)


@celery_app.task(bind=True, name="app.workers.bibbi_tasks.process_bibbi_upload")
def process_bibbi_upload(self, upload_id: str, file_path: str) -> Dict[str, Any]:
    """
    Process BIBBI reseller upload through complete pipeline

    Args:
        upload_id: Upload UUID from uploads table
        file_path: Absolute path to uploaded Excel file

    Returns:
        Processing result dictionary

    Pipeline:
        Upload → Staging → Detection → Routing → Processing →
        Store Creation → Validation → Insertion → Complete
    """
    bibbi_db = get_bibbi_db()
    staging_id = None
    batch_id = None

    try:
        print(f"[BIBBI Task] Starting processing for upload: {upload_id}")

        # Update upload status to processing
        bibbi_db.table("uploads")\
            .update({
                "upload_status": "processing",
                "processing_started_at": datetime.utcnow().isoformat()
            })\
            .eq("upload_id", upload_id)\
            .execute()

        # ============================================
        # PHASE 1: STAGING
        # ============================================
        print(f"[BIBBI Task] Phase 1: Staging file metadata extraction...")

        staging_service = get_staging_service(bibbi_db)
        staging_id = staging_service.stage_upload(
            upload_id=upload_id,
            file_path=file_path
        )

        print(f"[BIBBI Task] Staging complete: {staging_id}")

        # Link staging to upload
        staging_service.link_staging_to_upload(staging_id, upload_id)

        # ============================================
        # PHASE 2: VENDOR DETECTION
        # ============================================
        print(f"[BIBBI Task] Phase 2: Vendor detection...")

        vendor_name, confidence, metadata = detect_bibbi_vendor(file_path)

        if not vendor_name:
            raise Exception(f"Unable to detect vendor. Confidence: {confidence}")

        if confidence < 0.5:
            raise Exception(f"Low vendor confidence: {confidence:.2f} for {vendor_name}")

        print(f"[BIBBI Task] Vendor detected: {vendor_name} (confidence: {confidence:.2f})")

        # Update staging with vendor info
        staging_service.update_staging_status(
            staging_id,
            "vendor_detected",
            {"vendor_name": vendor_name, "confidence": confidence, **metadata}
        )

        # ============================================
        # PHASE 3: ROUTING & PROCESSING
        # ============================================
        print(f"[BIBBI Task] Phase 3: Routing to processor...")

        # Get reseller_id from uploads table
        upload_result = bibbi_db.table("uploads")\
            .select("reseller_id")\
            .eq("upload_id", upload_id)\
            .execute()

        if not upload_result.data:
            raise Exception(f"Upload not found: {upload_id}")

        reseller_id = upload_result.data[0]["reseller_id"]

        # Route to appropriate processor
        processor = route_bibbi_vendor(vendor_name, reseller_id, bibbi_db)

        print(f"[BIBBI Task] Processing file with {vendor_name} processor...")

        # Generate unique batch_id for this upload
        import uuid
        batch_id = str(uuid.uuid4())

        # Process file
        processing_result = processor.process(file_path, batch_id)

        print(f"[BIBBI Task] Processing complete:")
        print(f"  - Total rows: {processing_result.total_rows}")
        print(f"  - Successful: {processing_result.successful_rows}")
        print(f"  - Failed: {processing_result.failed_rows}")

        # Update staging with processing results
        staging_service.update_staging_status(
            staging_id,
            "processed",
            {
                "total_rows": processing_result.total_rows,
                "successful_rows": processing_result.successful_rows,
                "failed_rows": processing_result.failed_rows,
                "processing_errors": processing_result.errors
            }
        )

        # ============================================
        # PHASE 4: STORE CREATION
        # ============================================
        print(f"[BIBBI Task] Phase 4: Auto-creating stores...")

        store_service = get_store_service(bibbi_db)

        # Bulk create stores from processing result
        if processing_result.stores:
            store_mapping = store_service.bulk_get_or_create_stores(
                reseller_id=reseller_id,
                stores_data=processing_result.stores
            )
            print(f"[BIBBI Task] Created/found {len(store_mapping)} stores")
        else:
            print(f"[BIBBI Task] No stores to create")

        # ============================================
        # PHASE 5: VALIDATION
        # ============================================
        print(f"[BIBBI Task] Phase 5: Validating transformed data...")

        validation_service = get_validation_service(bibbi_db)

        # Validate transformed data
        validation_result = validation_service.validate_transformed_data(
            processing_result.transformed_data
        )

        print(f"[BIBBI Task] Validation complete:")
        print(f"  - Valid rows: {validation_result.valid_rows}")
        print(f"  - Invalid rows: {validation_result.invalid_rows}")
        print(f"  - Success rate: {validation_result.validation_success_rate:.1f}%")

        # Update staging with validation results
        staging_service.update_validation_results(staging_id, validation_result)

        # Generate error report if validation errors exist
        if validation_result.errors:
            print(f"[BIBBI Task] Generating validation error report...")
            error_report_service = get_error_report_service()

            report_path = error_report_service.generate_report_from_staging(
                staging_id,
                bibbi_db
            )

            print(f"[BIBBI Task] Error report generated: {report_path}")

        # If validation failed completely, stop here
        if validation_result.valid_rows == 0:
            raise Exception(f"Validation failed: 0 valid rows out of {validation_result.total_rows}")

        # ============================================
        # PHASE 6: FOREIGN KEY VALIDATION
        # ============================================
        print(f"[BIBBI Task] Phase 6: Validating foreign keys...")

        fk_validation_result = validation_service.validate_foreign_keys(
            validation_result.valid_data
        )

        if fk_validation_result.valid_rows < validation_result.valid_rows:
            print(f"[BIBBI Task] Foreign key validation removed {validation_result.valid_rows - fk_validation_result.valid_rows} rows")
            validation_result = fk_validation_result

        # ============================================
        # PHASE 7: SALES INSERTION
        # ============================================
        print(f"[BIBBI Task] Phase 7: Inserting validated sales...")

        insertion_service = get_sales_insertion_service(bibbi_db)

        # Insert validated data
        insertion_result = insertion_service.insert_validated_sales(
            validated_data=validation_result.valid_data,
            batch_size=1000  # Use default batch size
        )

        print(f"[BIBBI Task] Insertion complete:")
        print(f"  - Inserted: {insertion_result.inserted_rows}")
        print(f"  - Duplicates: {insertion_result.duplicate_rows}")
        print(f"  - Failed: {insertion_result.failed_rows}")
        print(f"  - Success rate: {insertion_result.to_dict()['insertion_success_rate']:.1f}%")

        # ============================================
        # PHASE 8: UPDATE UPLOAD STATUS
        # ============================================
        print(f"[BIBBI Task] Phase 8: Updating upload status...")

        # Update upload with final results
        insertion_service.update_upload_status(
            upload_id=upload_id,
            insertion_result=insertion_result
        )

        # Update staging status
        staging_service.update_staging_status(
            staging_id,
            "completed",
            {
                "inserted_rows": insertion_result.inserted_rows,
                "duplicate_rows": insertion_result.duplicate_rows,
                "insertion_errors": insertion_result.errors
            }
        )

        # ============================================
        # CLEANUP
        # ============================================
        print(f"[BIBBI Task] Cleanup: Removing temporary file...")

        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[BIBBI Task] File removed: {file_path}")

        # ============================================
        # SUCCESS RESULT
        # ============================================
        print(f"[BIBBI Task] Processing complete for upload: {upload_id}")

        return {
            "success": True,
            "upload_id": upload_id,
            "staging_id": staging_id,
            "batch_id": batch_id,
            "vendor": vendor_name,
            "confidence": confidence,
            "processing": {
                "total_rows": processing_result.total_rows,
                "successful_rows": processing_result.successful_rows,
                "failed_rows": processing_result.failed_rows,
            },
            "validation": {
                "valid_rows": validation_result.valid_rows,
                "invalid_rows": validation_result.invalid_rows,
                "success_rate": validation_result.validation_success_rate,
            },
            "insertion": insertion_result.to_dict(),
        }

    except Exception as e:
        error_message = str(e)
        error_trace = traceback.format_exc()

        print(f"[BIBBI Task] ERROR: {error_message}")
        print(f"[BIBBI Task] Trace:\n{error_trace}")

        # ============================================
        # ERROR CLEANUP
        # ============================================

        # Cleanup temporary file
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"[BIBBI Task] Cleaned up file: {file_path}")
        except Exception:
            pass  # Ignore cleanup errors

        # Update upload status to failed
        try:
            bibbi_db.table("uploads")\
                .update({
                    "upload_status": "failed",
                    "processing_completed_at": datetime.utcnow().isoformat(),
                    "processing_errors": {
                        "error_message": error_message,
                        "error_trace": error_trace[:1000]  # Truncate trace
                    }
                })\
                .eq("upload_id", upload_id)\
                .execute()
        except Exception as update_error:
            print(f"[BIBBI Task] Failed to update upload status: {update_error}")

        # Update staging status to failed if staging was created
        if staging_id:
            try:
                staging_service = get_staging_service(bibbi_db)
                staging_service.update_staging_status(
                    staging_id,
                    "failed",
                    {"error": error_message}
                )
            except Exception:
                pass  # Ignore staging update errors

        # ============================================
        # ERROR RESULT
        # ============================================
        return {
            "success": False,
            "upload_id": upload_id,
            "staging_id": staging_id,
            "batch_id": batch_id,
            "error": error_message,
            "trace": error_trace[:1000]  # Truncate for response
        }
