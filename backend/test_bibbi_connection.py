#!/usr/bin/env python3
"""
Test BIBBI Database Connection

Verifies that worker_db.py correctly routes to BIBBI database
when TENANT_ID_OVERRIDE=bibbi is set.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.worker_db import get_worker_supabase_client
from app.core.config import settings


def test_bibbi_connection():
    """Test BIBBI database connection"""

    print("=" * 80)
    print("BIBBI DATABASE CONNECTION TEST")
    print("=" * 80)

    # Check environment configuration
    print("\n[1] Environment Configuration:")
    print(f"   TENANT_ID_OVERRIDE: {settings.tenant_id_override}")
    print(f"   BIBBI_SUPABASE_URL: {settings.bibbi_supabase_url}")
    print(f"   BIBBI_SUPABASE_SERVICE_KEY: {'***' + settings.bibbi_supabase_service_key[-10:] if settings.bibbi_supabase_service_key else 'NOT SET'}")

    # Test worker database client
    print("\n[2] Testing Worker Database Client:")
    try:
        # Get BIBBI client
        supabase = get_worker_supabase_client(tenant_id="bibbi")
        print("   ✅ Worker client created successfully")

        # Test connection by querying sales_unified table
        print("\n[3] Testing BIBBI Database Connection:")
        result = supabase.table("sales_unified").select("*").limit(5).execute()

        print(f"   ✅ Connected to BIBBI database")
        print(f"   - Retrieved {len(result.data)} sample records")

        if result.data:
            sample = result.data[0]
            print(f"\n[4] Sample Record from sales_unified:")
            print(f"   - functional_name: {sample.get('functional_name', 'N/A')}")
            print(f"   - store_identifier: {sample.get('store_identifier', 'N/A')}")
            print(f"   - quantity: {sample.get('quantity', 'N/A')}")
            print(f"   - sales_eur: {sample.get('sales_eur', 'N/A')}")
            print(f"   - sale_date: {sample.get('sale_date', 'N/A')}")

        # Check for Liberty reseller
        print("\n[5] Checking for Liberty Reseller:")
        resellers = supabase.table("resellers").select("*").execute()

        liberty_resellers = [r for r in resellers.data if 'liberty' in r.get('name', '').lower()]

        if liberty_resellers:
            for reseller in liberty_resellers:
                print(f"   ✅ Found Liberty reseller:")
                print(f"      - ID: {reseller.get('reseller_id')}")
                print(f"      - Name: {reseller.get('name')}")
                print(f"      - City: {reseller.get('city')}")
        else:
            print("   ⚠️  No Liberty reseller found in database")

        print("\n" + "=" * 80)
        print("✅ TEST PASSED: BIBBI database connection working correctly")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bibbi_connection()
    sys.exit(0 if success else 1)
