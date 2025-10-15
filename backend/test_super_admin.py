#!/usr/bin/env python
"""
Test script for super admin authentication
"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

def test_tenant_registry_connection():
    """Test connection to tenant registry database"""
    print("=" * 60)
    print("Testing Tenant Registry Connection")
    print("=" * 60)

    registry_url = os.getenv('TENANT_REGISTRY_URL')
    registry_service_key = os.getenv('TENANT_REGISTRY_SERVICE_KEY')

    print(f"Registry URL: {registry_url}")

    if not registry_service_key or registry_service_key == 'YOUR_SERVICE_KEY_HERE':
        print("\n❌ TENANT_REGISTRY_SERVICE_KEY not configured")
        print("\nPlease:")
        print("1. Go to https://supabase.com/dashboard/project/jzyvvmzkhprmqrqmxzdv/settings/api")
        print("2. Copy the 'service_role' key")
        print("3. Update TENANT_REGISTRY_SERVICE_KEY in backend/.env")
        print("4. Restart backend server")
        return False

    print(f"Service Key: {registry_service_key[:20]}... (configured: Yes)")

    try:
        client = create_client(registry_url, registry_service_key)

        # Test connection by querying super_admins table
        response = client.table('super_admins').select('email, created_at').execute()

        print(f"\n✅ Connection: SUCCESS")
        print(f"✅ super_admins table accessible")
        print(f"\nSuper admins in database:")
        for admin in response.data:
            print(f"  - {admin['email']} (added: {admin['created_at'][:10]})")

        # Check if david@taskifai.com exists
        david_response = client.table('super_admins').select('email').eq('email', 'david@taskifai.com').execute()

        if david_response.data:
            print(f"\n✅ david@taskifai.com is registered as super admin")
            return True
        else:
            print(f"\n❌ david@taskifai.com NOT found in super_admins table")
            return False

    except Exception as e:
        print(f"\n❌ Connection: FAILED")
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    success = test_tenant_registry_connection()
    exit(0 if success else 1)
