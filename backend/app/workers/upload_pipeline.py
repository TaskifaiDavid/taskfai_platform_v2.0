"""
Upload Pipeline Utilities

Shared utilities for processing uploads across demo and BIBBI workflows.
Extracts common patterns to reduce code duplication and improve maintainability.
"""

import base64
import hashlib
import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, Callable

from app.core.worker_db import get_worker_supabase_client


@dataclass
class UploadContext:
    """
    Context object for upload processing

    Contains all necessary information for processing an upload through the pipeline.
    """
    batch_id: str
    user_id: str
    filename: str
    tenant_id: str = "demo"
    reseller_id: Optional[str] = None
    file_path: Optional[str] = None
    detected_vendor: Optional[str] = None
    confidence: Optional[float] = None


class UploadPipeline:
    """
    Upload processing pipeline with shared utilities

    Provides common functionality for both demo and BIBBI upload workflows:
    - File handling (decode, save, cleanup)
    - Vendor detection
    - Batch status management
    - Error handling
    """

    TEMP_DIR = "/tmp/taskifai_uploads"

    def __init__(self):
        """Initialize pipeline and ensure temp directory exists"""
        os.makedirs(self.TEMP_DIR, exist_ok=True)

    # ============================================
    # FILE HANDLING
    # ============================================

    def decode_and_save_file(
        self,
        file_content_b64: str,
        filename: str
    ) -> str:
        """
        Decode base64 file content and save to temporary file

        Args:
            file_content_b64: Base64-encoded file content
            filename: Original filename

        Returns:
            Absolute path to saved temporary file

        Raises:
            ValueError: If file content cannot be decoded
        """
        try:
            # Decode base64 content
            file_content = base64.b64decode(file_content_b64)

            # Generate unique filename using content hash
            file_hash = hashlib.md5(file_content).hexdigest()
            file_path = os.path.join(self.TEMP_DIR, f"{file_hash}_{filename}")

            # Write to temporary file
            with open(file_path, 'wb') as f:
                f.write(file_content)

            return file_path

        except Exception as e:
            raise ValueError(f"Failed to decode and save file: {e}")

    def cleanup_file(self, file_path: str) -> bool:
        """
        Remove temporary file

        Args:
            file_path: Path to file to remove

        Returns:
            True if file was removed, False if error occurred
        """
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    # ============================================
    # VENDOR DETECTION
    # ============================================

    def detect_vendor(self, file_path: str, filename: str) -> Tuple[Optional[str], float]:
        """
        Detect vendor format from file

        Args:
            file_path: Path to file
            filename: Original filename

        Returns:
            Tuple of (vendor_name, confidence) or (None, 0.0) if detection failed
        """
        # LAZY IMPORT: Load detector only when needed
        from app.services.vendors.detector import vendor_detector

        detected_vendor, confidence = vendor_detector.detect_vendor(file_path, filename)
        return detected_vendor, confidence

    def lookup_reseller_for_vendor(self, vendor_name: str, tenant_id: str = "bibbi") -> Optional[str]:
        """
        Auto-lookup reseller ID for BIBBI vendors

        For Liberty and other BIBBI resellers, automatically lookup the reseller_id
        from the BIBBI database to ensure correct routing to BIBBI processor path.

        Args:
            vendor_name: Detected vendor name (e.g., "liberty", "boxnox")
            tenant_id: Tenant context for database lookup (default: "bibbi")

        Returns:
            Reseller UUID if found, None otherwise
        """
        # LAZY IMPORT: Load database client only when needed
        from app.core.worker_db import get_worker_supabase_client

        # Map vendor names to reseller names in database
        vendor_to_reseller_map = {
            "liberty": "Liberty",
            "boxnox": "BOXNOX",
            "galilu": "Galilu",
            "skins_sa": "Skins SA",
            "skins_nl": "Skins NL",
            "cdlc": "Creme de la creme",
            "selfridges": "Selfridges",
            "ukraine": "Aromateque",
            "online": "woocommerce"
        }

        reseller_name = vendor_to_reseller_map.get(vendor_name.lower())
        if not reseller_name:
            print(f"[Pipeline] No reseller mapping for vendor: {vendor_name}")
            return None

        try:
            # Query BIBBI database for reseller
            supabase = get_worker_supabase_client(tenant_id)
            result = supabase.table("resellers")\
                .select("id")\
                .ilike("reseller", reseller_name)\
                .execute()

            if result.data and len(result.data) > 0:
                reseller_id = result.data[0]["id"]
                print(f"[Pipeline] Found reseller_id={reseller_id} for vendor={vendor_name}")
                return reseller_id
            else:
                print(f"[Pipeline] No reseller found for vendor={vendor_name} (reseller_name={reseller_name})")
                return None

        except Exception as e:
            print(f"[Pipeline] Error looking up reseller for {vendor_name}: {e}")
            return None

    # ============================================
    # BATCH STATUS MANAGEMENT
    # ============================================

    def update_batch_status(
        self,
        batch_id: str,
        status: str,
        tenant_id: str = "demo",
        **additional_fields
    ) -> None:
        """
        Update upload batch status

        Args:
            batch_id: Batch identifier
            status: New status (processing, completed, failed, etc.)
            tenant_id: Tenant context for database connection
            **additional_fields: Additional fields to update
        """
        try:
            supabase = get_worker_supabase_client(tenant_id)

            update_data = {
                "processing_status": status,
                **additional_fields
            }

            # Add timestamp based on status
            if status == "processing":
                update_data["processing_started_at"] = datetime.utcnow().isoformat()
            elif status in ("completed", "completed_with_errors", "failed"):
                update_data["processed_at"] = datetime.utcnow().isoformat()

            supabase.table("upload_batches").update(update_data).eq(
                "upload_batch_id", batch_id
            ).execute()

        except Exception as e:
            print(f"[Pipeline] Failed to update batch status: {e}")

    # ============================================
    # ERROR HANDLING
    # ============================================

    def handle_upload_error(
        self,
        context: UploadContext,
        error: Exception
    ) -> Dict[str, Any]:
        """
        Handle upload processing error

        Updates batch status, cleans up files, and returns error response.

        Args:
            context: Upload context with batch info
            error: Exception that occurred

        Returns:
            Error response dictionary
        """
        error_msg = str(error)
        error_trace = traceback.format_exc()

        print(f"[Pipeline] ERROR in batch {context.batch_id}: {error_msg}")

        # Cleanup temporary file
        if context.file_path:
            self.cleanup_file(context.file_path)

        # Update batch status to failed
        self.update_batch_status(
            batch_id=context.batch_id,
            status="failed",
            tenant_id=context.tenant_id,
            error_message=error_msg
        )

        return {
            "success": False,
            "batch_id": context.batch_id,
            "error": error_msg,
            "trace": error_trace[:1000]  # Truncate trace
        }

    # ============================================
    # PROCESSOR ROUTING
    # ============================================

    def get_demo_processor(self, vendor_name: str):
        """
        Get demo processor instance for vendor

        Args:
            vendor_name: Vendor identifier

        Returns:
            Processor instance

        Raises:
            ValueError: If no processor available for vendor
        """
        # LAZY IMPORT: Load processors only when needed
        from app.services.vendors.demo_processor import DemoProcessor
        from app.services.vendors.online_processor import OnlineProcessor

        processors = {
            "demo": DemoProcessor,
            "online": OnlineProcessor
        }

        processor_class = processors.get(vendor_name)
        if not processor_class:
            raise ValueError(f"No demo processor available for vendor: {vendor_name}. Use BIBBI path for reseller vendors.")

        return processor_class()

    def get_bibbi_processor(self, vendor_name: str):
        """
        Get BIBBI processor instance for vendor

        Args:
            vendor_name: Vendor identifier

        Returns:
            Processor instance

        Raises:
            ValueError: If no processor available for vendor
        """
        # LAZY IMPORT: Load BIBBI routing only when needed
        from app.services.bibbi import route_bibbi_vendor

        processor = route_bibbi_vendor(vendor_name)
        if not processor:
            raise ValueError(f"No BIBBI processor available for vendor: {vendor_name}")

        return processor

    # ============================================
    # PIPELINE EXECUTION
    # ============================================

    def process_upload(
        self,
        context: UploadContext,
        file_content_b64: str,
        processor_fn: Callable[[UploadContext], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main pipeline execution

        Handles common workflow:
        1. Decode and save file
        2. Detect vendor
        3. Auto-lookup reseller for BIBBI vendors (Liberty, Boxnox, etc.)
        4. Update batch status to processing
        5. Execute processor function
        6. Cleanup

        Args:
            context: Upload context
            file_content_b64: Base64-encoded file content
            processor_fn: Function to process the upload (demo or BIBBI)

        Returns:
            Processing result dictionary
        """
        try:
            # Decode and save file
            context.file_path = self.decode_and_save_file(file_content_b64, context.filename)
            print(f"[Pipeline] Saved temp file: {context.file_path}")

            # Detect vendor
            context.detected_vendor, context.confidence = self.detect_vendor(
                context.file_path,
                context.filename
            )
            print(f"[Pipeline] Detected vendor: {context.detected_vendor} (confidence: {context.confidence})")

            if not context.detected_vendor:
                raise Exception(f"Unable to detect vendor from file. Confidence: {context.confidence}")

            # Auto-lookup reseller for BIBBI vendors (if not already set)
            # This ensures Liberty and other reseller vendors route to BIBBI path
            if not context.reseller_id:
                reseller_id = self.lookup_reseller_for_vendor(context.detected_vendor, context.tenant_id)
                if reseller_id:
                    context.reseller_id = reseller_id
                    print(f"[Pipeline] Auto-assigned reseller_id={reseller_id} for vendor={context.detected_vendor}")

            # Update batch status to processing
            self.update_batch_status(
                batch_id=context.batch_id,
                status="processing",
                tenant_id=context.tenant_id,
                vendor_name=context.detected_vendor
            )

            # Execute processor function
            result = processor_fn(context)

            # Cleanup file
            self.cleanup_file(context.file_path)

            return result

        except Exception as e:
            return self.handle_upload_error(context, e)


# Global pipeline instance
upload_pipeline = UploadPipeline()
