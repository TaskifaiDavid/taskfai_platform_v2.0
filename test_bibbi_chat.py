#!/usr/bin/env python3
"""
Test script to verify BIBBI chat SQL generation after fixing schema issues.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai_chat.agent import SQLDatabaseAgent


def test_bibbi_sql_generation():
    """Test that BIBBI chat configuration is correct"""

    print("="*80)
    print("BIBBI Chat Configuration Test")
    print("="*80)

    # Initialize agent for BIBBI tenant
    agent = SQLDatabaseAgent(
        project_id="dummy-project-id",
        tenant_subdomain="bibbi",
        openai_api_key="sk-dummy-key-for-testing"  # Won't actually call API
    )

    print(f"\n✓ Agent initialized successfully")
    print(f"  Tenant: {agent.tenant_subdomain}")
    print(f"  Primary Table: {agent.primary_table}")
    print(f"  Filter Column: {agent.filter_column}")
    print(f"  Filter Value: {agent.filter_value}")

    # Validate configuration
    print("\n" + "="*80)
    print("Configuration Validation")
    print("="*80)

    issues = []

    # Check table name
    if agent.primary_table != "sales_unified":
        issues.append("❌ Wrong primary table (should be 'sales_unified')")
    else:
        print("✅ Primary table: sales_unified")

    # Check filter configuration
    if agent.filter_column is not None:
        issues.append(f"❌ Filter column should be None for BIBBI, got: {agent.filter_column}")
    else:
        print("✅ Filter column: None (correct for single-tenant database)")

    if agent.filter_value is not None:
        issues.append(f"❌ Filter value should be None for BIBBI, got: {agent.filter_value}")
    else:
        print("✅ Filter value: None (correct for single-tenant database)")

    # Check available columns
    required_columns = [
        "functional_name",
        "product_ean",
        "sales_eur",
        "country",
        "sales_channel",
        "is_refund",
        "cost_of_goods",
        "utm_source"
    ]

    missing_columns = []
    for col in required_columns:
        if col not in agent.available_columns:
            missing_columns.append(col)

    if missing_columns:
        issues.append(f"❌ Missing columns in config: {', '.join(missing_columns)}")
    else:
        print(f"✅ All required columns present ({len(required_columns)} checked)")

    # Check that tenant_id is NOT in available columns
    if "tenant_id" in agent.available_columns:
        issues.append("❌ tenant_id should NOT be in available columns for BIBBI")
    else:
        print("✅ tenant_id correctly excluded from available columns")

    # Print summary
    print("\n" + "="*80)
    if issues:
        print("TEST FAILED ❌")
        print("="*80)
        print("\nIssues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("TEST PASSED ✅")
        print("="*80)
        print("\nBIBBI chat configuration is correct!")
        print("The agent will now generate SQL queries without tenant_id filters")
        print("and with access to all columns from the actual database schema.")
        return True


if __name__ == "__main__":
    test_bibbi_sql_generation()
