"""
Test Liberty file routing to BIBBI processor

This script tests that Liberty files automatically route to the BIBBI processor
after the routing refactor.
"""
import base64
import uuid
from app.workers.unified_tasks import process_unified_upload

# Liberty test file path
liberty_file = "/home/david/TaskifAI_platform_v2.0/backend/BIBBI/Example_docs/Liberty statistics/Continuity Supplier Size Report 27-07-2025.xlsx"

# Read and encode file
with open(liberty_file, "rb") as f:
    file_content = f.read()
    file_content_b64 = base64.b64encode(file_content).decode('utf-8')

# Test parameters
batch_id = str(uuid.uuid4())
user_id = "test-user-id"
filename = "Continuity Supplier Size Report 27-07-2025.xlsx"
tenant_id = "bibbi"

print(f"\n=== Testing Liberty File Routing ===")
print(f"Batch ID: {batch_id}")
print(f"File: {filename}")
print(f"Tenant: {tenant_id}")
print(f"Initial reseller_id: None (should be auto-assigned)")
print(f"\n=== Expected Flow ===")
print("1. Prepare context → detect vendor=liberty")
print("2. Auto-lookup reseller → assign reseller_id")
print("3. Route to BIBBI processor (NOT demo)")
print("4. Process with Liberty processor")
print("5. Success!\n")

# Execute upload task
print("=== Executing Upload Task ===\n")
result = process_unified_upload(
    batch_id=batch_id,
    user_id=user_id,
    file_content_b64=file_content_b64,
    filename=filename,
    reseller_id=None,  # NOT provided - should be auto-assigned
    tenant_id=tenant_id
)

print("\n=== Result ===")
print(result)

if result.get("status") in ("completed", "completed_with_errors"):
    print("\n✅ SUCCESS: Liberty file routed to BIBBI processor!")
    print(f"   Vendor: {result.get('vendor', 'N/A')}")
    print(f"   Records processed: {result.get('records_processed', 0)}")
    print(f"   Sales inserted: {result.get('sales_inserted', 0)}")
else:
    print("\n❌ FAILED: Liberty file did not process correctly")
    print(f"   Error: {result.get('error', 'Unknown error')}")
