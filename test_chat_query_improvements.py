#!/usr/bin/env python3
"""
Test script to validate AI chat query improvements for BIBBI tenant.

Tests the following improvements:
1. Product identification (EAN vs SKU/functional_name)
2. Partial product matching with ILIKE
3. Reseller queries with JOIN
4. Conversation context support
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.ai_chat.agent import SQLDatabaseAgent


def test_product_query_strategy():
    """Test that product query strategy examples are present in agent.py source code"""

    print("=" * 80)
    print("Test 1: Product Query Strategy in System Prompt")
    print("=" * 80)

    # Read the agent.py source code directly
    agent_file = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services', 'ai_chat', 'agent.py')

    with open(agent_file, 'r') as f:
        source_code = f.read()

    checks = [
        ("Product identification section", "PRODUCT IDENTIFICATION STRATEGY"),
        ("EAN barcode guidance", "13-digit number"),
        ("Functional name guidance", "functional_name ILIKE"),
        ("ILIKE wildcard usage", "'%PRODUCTCODE%'"),
        ("Example: BBGOT100", "BBGOT100"),
    ]

    passed = 0
    failed = 0

    for check_name, search_text in checks:
        if search_text in source_code:
            print(f"✅ {check_name}: Found")
            passed += 1
        else:
            print(f"❌ {check_name}: Missing '{search_text}'")
            failed += 1

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0


def test_reseller_query_strategy():
    """Test that reseller JOIN examples are present in agent.py source code"""

    print("\n" + "=" * 80)
    print("Test 2: Reseller Query Strategy in System Prompt")
    print("=" * 80)

    # Read the agent.py source code directly
    agent_file = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services', 'ai_chat', 'agent.py')

    with open(agent_file, 'r') as f:
        source_code = f.read()

    checks = [
        ("Reseller strategy section", "RESELLER QUERY STRATEGY"),
        ("JOIN resellers table", "JOIN resellers"),
        ("Reseller name column", "r.name"),
        ("ILIKE for reseller matching", "r.name ILIKE"),
        ("Example: Liberty", "Liberty"),
    ]

    passed = 0
    failed = 0

    for check_name, search_text in checks:
        if search_text in source_code:
            print(f"✅ {check_name}: Found")
            passed += 1
        else:
            print(f"❌ {check_name}: Missing '{search_text}'")
            failed += 1

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0


def test_conversation_context_support():
    """Test that conversation context is properly integrated"""

    print("\n" + "=" * 80)
    print("Test 3: Conversation Context Support")
    print("=" * 80)

    # Read the agent.py source code directly
    agent_file = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services', 'ai_chat', 'agent.py')

    with open(agent_file, 'r') as f:
        source_code = f.read()

    # Test that _generate_sql accepts conversation_context parameter
    agent = SQLDatabaseAgent(
        project_id="dummy-project-id",
        tenant_subdomain="bibbi",
        openai_api_key="sk-dummy-key-for-testing"
    )

    import inspect
    sig = inspect.signature(agent._generate_sql)

    checks = [
        ("_generate_sql has conversation_context param", "conversation_context" in sig.parameters),
        ("conversation_context has default value", sig.parameters.get("conversation_context", None) and sig.parameters["conversation_context"].default == ""),
        ("Context section in source", "RECENT CONVERSATION CONTEXT:" in source_code),
        ("Follow-up examples in source", "follow-up questions" in source_code.lower()),
        ("process_query gets conversation_memory param", "conversation_memory" in source_code),
        ("process_query retrieves context", "get_recent_context" in source_code),
    ]

    passed = 0
    failed = 0

    for check_name, condition in checks:
        if condition:
            print(f"✅ {check_name}")
            passed += 1
        else:
            print(f"❌ {check_name}")
            failed += 1

    print(f"\nResult: {passed} passed, {failed} failed")
    return failed == 0


def test_hypothetical_queries():
    """Generate SQL patterns for hypothetical queries to validate logic"""

    print("\n" + "=" * 80)
    print("Test 4: Hypothetical Query Validation (SQL Pattern Analysis)")
    print("=" * 80)

    # Read the agent.py source code directly
    agent_file = os.path.join(os.path.dirname(__file__), 'backend', 'app', 'services', 'ai_chat', 'agent.py')

    with open(agent_file, 'r') as f:
        source_code = f.read()

    query_scenarios = [
        ("Product by SKU code", "How much did BBGOT100 sell?",
         ["functional_name ILIKE", "%BBGOT100%"]),
        ("Product by partial SKU", "Show GOT100 sales",
         ["functional_name ILIKE", "%GOT100%"]),
        ("Product by EAN barcode", "Sales for 7350154320022",
         ["product_ean", "7350154320022"]),
        ("Reseller query", "How much did Liberty sell?",
         ["JOIN resellers", "r.name ILIKE", "%Liberty%"]),
        ("Reseller with product", "What did Galilu sell of BBGOT100?",
         ["JOIN resellers", "functional_name ILIKE", "%BBGOT100%"]),
    ]

    print("\nValidating system prompt contains guidance for each scenario:\n")

    passed = 0
    failed = 0

    for scenario_name, query, expected_patterns in query_scenarios:
        print(f"Scenario: {scenario_name}")
        print(f"  Query: '{query}'")

        scenario_passed = True
        for pattern in expected_patterns:
            if pattern in source_code:
                print(f"  ✅ Guidance for '{pattern}' present")
            else:
                print(f"  ❌ Missing guidance for '{pattern}'")
                scenario_passed = False

        if scenario_passed:
            passed += 1
        else:
            failed += 1
        print()

    print(f"Result: {passed}/{len(query_scenarios)} scenarios have complete guidance")
    return failed == 0


def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("BIBBI AI Chat Query Improvements - Validation Tests")
    print("=" * 80)
    print("\nThese tests validate the system prompt contains proper guidance")
    print("for handling product queries, reseller queries, and conversation context.")
    print("\nNote: This does NOT test actual SQL generation (requires OpenAI API)")

    results = []

    try:
        results.append(("Product Query Strategy", test_product_query_strategy()))
        results.append(("Reseller Query Strategy", test_reseller_query_strategy()))
        results.append(("Conversation Context", test_conversation_context_support()))
        results.append(("Hypothetical Queries", test_hypothetical_queries()))
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nThe system prompt contains proper guidance for:")
        print("  • Product identification (EAN vs SKU/functional_name)")
        print("  • Partial product matching with ILIKE wildcards")
        print("  • Reseller queries with JOIN")
        print("  • Conversation context for follow-up questions")
        print("\nReady to commit changes!")
        return True
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease review the system prompt configuration in agent.py")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
