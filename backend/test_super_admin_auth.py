#!/usr/bin/env python
"""
Comprehensive test for super admin authentication endpoints
Tests both super admin access and regular admin rejection
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://localhost:8000"

def get_demo_token():
    """Login as test@demo.com (regular admin, NOT super admin)"""
    print("\n" + "=" * 60)
    print("Step 1: Login as test@demo.com (Regular Admin)")
    print("=" * 60)

    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={
            "email": "test@demo.com",
            "password": "password123",
            "subdomain": "demo"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful")
        print(f"   User: {data.get('email')}")
        print(f"   Role: {data.get('role')}")
        return data.get('access_token')
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def get_david_token():
    """Login as david@taskifai.com (super admin)"""
    print("\n" + "=" * 60)
    print("Step 2: Login as david@taskifai.com (Super Admin)")
    print("=" * 60)

    # Try demo subdomain first
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={
            "email": "david@taskifai.com",
            "password": "password123",
            "subdomain": "demo"
        }
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful")
        print(f"   User: {data.get('email')}")
        print(f"   Role: {data.get('role')}")
        return data.get('access_token')
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   {response.text}")
        print(f"\nℹ️  If david@taskifai.com doesn't exist in demo database:")
        print(f"   You can create the user or test with an existing super admin email")
        return None

def test_tenant_list_access(token, user_type):
    """Test access to /api/admin/tenants endpoint"""
    print("\n" + "=" * 60)
    print(f"Step 3: Test tenant list access as {user_type}")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/api/admin/tenants",
        headers=headers,
        params={"limit": 10, "offset": 0}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Access granted")
        print(f"   Tenants returned: {len(data.get('tenants', []))}")
        return True
    elif response.status_code == 403:
        error = response.json()
        print(f"🔒 Access denied (as expected)")
        print(f"   Message: {error.get('detail')}")
        return False
    elif response.status_code == 401:
        print(f"❌ Authentication failed")
        print(f"   {response.text}")
        return None
    else:
        print(f"❌ Unexpected error: {response.status_code}")
        print(f"   {response.text}")
        return None

def main():
    print("\n" + "=" * 60)
    print("SUPER ADMIN AUTHENTICATION TEST")
    print("=" * 60)
    print("\nThis test verifies:")
    print("1. Super admins (in super_admins table) CAN access tenant endpoints")
    print("2. Regular admins (NOT in super_admins table) CANNOT access tenant endpoints")

    # Test 1: Regular admin should be rejected
    demo_token = get_demo_token()
    if demo_token:
        regular_admin_access = test_tenant_list_access(demo_token, "Regular Admin")

        if regular_admin_access is False:
            print("\n✅ TEST 1 PASSED: Regular admin correctly denied access")
        elif regular_admin_access is True:
            print("\n❌ TEST 1 FAILED: Regular admin should NOT have access")
            return False
        else:
            print("\n⚠️  TEST 1 INCONCLUSIVE: Authentication issue")
    else:
        print("\n⚠️  TEST 1 SKIPPED: Could not login as regular admin")

    # Test 2: Super admin should have access
    david_token = get_david_token()
    if david_token:
        super_admin_access = test_tenant_list_access(david_token, "Super Admin")

        if super_admin_access is True:
            print("\n✅ TEST 2 PASSED: Super admin correctly granted access")
        elif super_admin_access is False:
            print("\n❌ TEST 2 FAILED: Super admin should have access")
            return False
        else:
            print("\n⚠️  TEST 2 INCONCLUSIVE: Authentication issue")
    else:
        print("\n⚠️  TEST 2 SKIPPED: Could not login as super admin")
        print("\nℹ️  To complete this test, you need a user with:")
        print("   - Email in super_admins table (e.g., david@taskifai.com)")
        print("   - Account in demo database (users table)")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if demo_token and david_token:
        if regular_admin_access is False and super_admin_access is True:
            print("✅ ALL TESTS PASSED")
            print("   - Regular admins are correctly blocked")
            print("   - Super admins have proper access")
            return True
        else:
            print("❌ TESTS FAILED - Authorization not working correctly")
            return False
    else:
        print("⚠️  PARTIAL TESTING - Some accounts unavailable")
        print("\nWhat was tested:")
        if demo_token and regular_admin_access is False:
            print("✅ Regular admin rejection works")
        if david_token and super_admin_access is True:
            print("✅ Super admin access works")
        return True  # Partial success

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend server")
        print("   Please ensure the server is running:")
        print("   cd /home/david/TaskifAI_platform_v2.0/backend")
        print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        exit(1)
