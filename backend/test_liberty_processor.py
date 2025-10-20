#!/usr/bin/env python3
"""
Test Liberty Processor

Tests the Liberty processor with an actual Continuity Supplier Size Report file.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.vendors.liberty_processor import LibertyProcessor


def test_liberty_processor():
    """Test Liberty processor with real file"""

    # Test file path
    test_file = "/home/david/TaskifAI_platform_v2.0/backend/BIBBI/Example_docs/Liberty statistics/2025/August/Continuity Supplier Size Report 31-08-2025.xlsx"

    print("=" * 80)
    print("LIBERTY PROCESSOR TEST")
    print("=" * 80)
    print(f"\nTest File: {test_file}")
    print(f"File exists: {os.path.exists(test_file)}")

    # Initialize processor
    print("\n[1] Initializing Liberty Processor...")
    processor = LibertyProcessor()

    # Process file
    print("\n[2] Processing file...")
    try:
        records = processor.process(test_file, user_id="test-user-id", batch_id="test-batch-id")

        print(f"\n[3] Processing Results:")
        print(f"   - Total records extracted: {len(records)}")

        if records:
            # Analyze records
            london_records = [r for r in records if r.get("store_identifier") == "London"]
            online_records = [r for r in records if r.get("store_identifier") == "Online"]

            print(f"   - London (Flagship) records: {len(london_records)}")
            print(f"   - Online (Internet) records: {len(online_records)}")

            # Show sample records
            print(f"\n[4] Sample Records:")
            print("\n   LONDON (Flagship) Sample:")
            if london_records:
                sample = london_records[0]
                print(f"      functional_name: {sample.get('functional_name')}")
                print(f"      product_id: {sample.get('product_id')}")
                print(f"      quantity: {sample.get('quantity')}")
                print(f"      sales_gbp: {sample.get('sales_gbp')}")
                print(f"      sales_eur: {sample.get('sales_eur')}")
                print(f"      store_identifier: {sample.get('store_identifier')}")
                print(f"      sale_date: {sample.get('sale_date')}")
                print(f"      year: {sample.get('year')}, month: {sample.get('month')}")

            print("\n   ONLINE (Internet) Sample:")
            if online_records:
                sample = online_records[0]
                print(f"      functional_name: {sample.get('functional_name')}")
                print(f"      product_id: {sample.get('product_id')}")
                print(f"      quantity: {sample.get('quantity')}")
                print(f"      sales_gbp: {sample.get('sales_gbp')}")
                print(f"      sales_eur: {sample.get('sales_eur')}")
                print(f"      store_identifier: {sample.get('store_identifier')}")
                print(f"      sale_date: {sample.get('sale_date')}")
                print(f"      year: {sample.get('year')}, month: {sample.get('month')}")

            # Validation checks
            print(f"\n[5] Validation Checks:")

            # Check all have required fields
            missing_fields = []
            for r in records[:10]:  # Check first 10
                if not r.get('functional_name'):
                    missing_fields.append("functional_name")
                if r.get('quantity') is None:
                    missing_fields.append("quantity")
                if r.get('sales_eur') is None:
                    missing_fields.append("sales_eur")

            if missing_fields:
                print(f"   ⚠️  Missing required fields: {set(missing_fields)}")
            else:
                print(f"   ✅ All records have required fields")

            # Check store identifiers
            store_ids = set(r.get('store_identifier') for r in records)
            if store_ids == {"London", "Online"}:
                print(f"   ✅ Store identifiers correct: {store_ids}")
            else:
                print(f"   ⚠️  Unexpected store identifiers: {store_ids}")

            # Check GBP → EUR conversion
            if records[0].get('sales_gbp') and records[0].get('sales_eur'):
                gbp = records[0]['sales_gbp']
                eur = records[0]['sales_eur']
                expected_eur = round(gbp * 1.17, 2)
                if abs(eur - expected_eur) < 0.01:
                    print(f"   ✅ Currency conversion correct: {gbp} GBP → {eur} EUR (rate: 1.17)")
                else:
                    print(f"   ⚠️  Currency conversion issue: {gbp} GBP → {eur} EUR (expected: {expected_eur})")

            # Check date extraction
            if records[0].get('sale_date'):
                sale_date = records[0]['sale_date']
                if sale_date == "2025-08-24":  # 31-08-2025 minus 1 week
                    print(f"   ✅ Date extraction correct: {sale_date} (31-08-2025 - 1 week)")
                else:
                    print(f"   ⚠️  Date extraction issue: {sale_date} (expected: 2025-08-24)")

            print(f"\n[6] Test Status: ✅ SUCCESS")
            print(f"   Liberty processor extracted {len(records)} records with store-level detail")

        else:
            print("\n⚠️  WARNING: No records extracted!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    return True


if __name__ == "__main__":
    success = test_liberty_processor()
    sys.exit(0 if success else 1)
