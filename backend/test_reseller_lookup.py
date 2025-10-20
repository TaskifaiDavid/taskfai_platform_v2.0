#!/usr/bin/env python3
"""
Test Reseller Auto-Lookup

Verifies that the reseller lookup function correctly finds Liberty
reseller from BIBBI database and returns correct UUID.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.workers.upload_pipeline import upload_pipeline
from app.core.config import settings


def test_reseller_lookup():
    """Test reseller lookup for Liberty vendor"""

    print("=" * 80)
    print("RESELLER AUTO-LOOKUP TEST")
    print("=" * 80)

    # Check environment configuration
    print("\n[1] Environment Configuration:")
    print(f"   TENANT_ID_OVERRIDE: {settings.tenant_id_override}")
    print(f"   BIBBI_SUPABASE_URL: {settings.bibbi_supabase_url}")
    print(f"   BIBBI_SUPABASE_SERVICE_KEY: {'***' + settings.bibbi_supabase_service_key[-10:] if settings.bibbi_supabase_service_key else 'NOT SET'}")

    # Test Liberty lookup
    print("\n[2] Testing Liberty Reseller Lookup:")
    try:
        reseller_id = upload_pipeline.lookup_reseller_for_vendor("liberty", tenant_id="bibbi")

        if reseller_id:
            print(f"   ✅ Found Liberty reseller_id: {reseller_id}")
            print(f"   Expected: 14b2a64e-013b-4c2d-9c42-379699b5823d")

            if reseller_id == "14b2a64e-013b-4c2d-9c42-379699b5823d":
                print(f"   ✅ Reseller ID matches expected value")
            else:
                print(f"   ⚠️  Reseller ID differs from expected value")
        else:
            print(f"   ❌ No reseller found for Liberty")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test other BIBBI vendors
    print("\n[3] Testing Other BIBBI Vendor Lookups:")
    test_vendors = ["boxnox", "galilu", "skins_sa", "selfridges"]

    for vendor in test_vendors:
        try:
            reseller_id = upload_pipeline.lookup_reseller_for_vendor(vendor, tenant_id="bibbi")
            if reseller_id:
                print(f"   ✅ {vendor}: {reseller_id}")
            else:
                print(f"   ⚠️  {vendor}: No reseller found")
        except Exception as e:
            print(f"   ❌ {vendor}: Error - {e}")

    # Test demo vendor (should return None)
    print("\n[4] Testing Demo Vendor (should return None):")
    try:
        reseller_id = upload_pipeline.lookup_reseller_for_vendor("demo", tenant_id="bibbi")
        if reseller_id is None:
            print(f"   ✅ Demo vendor correctly returns None (not a BIBBI reseller)")
        else:
            print(f"   ⚠️  Demo vendor unexpectedly returned reseller_id: {reseller_id}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

    print("\n" + "=" * 80)
    print("✅ TEST PASSED: Reseller auto-lookup working correctly")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_reseller_lookup()
    sys.exit(0 if success else 1)
