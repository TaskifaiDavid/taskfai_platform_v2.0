#!/usr/bin/env python3
"""
Demo Tenant Seeder

Seeds the demo tenant into the master registry.
This allows local development and testing.

Prerequisites:
    1. Tenant registry table must exist (run init_tenant_registry.py first)
    2. Environment variables must be set (.env file)

Run this script to seed demo tenant:
    python backend/db/seed_demo_tenant.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.services.tenant.registry import tenant_registry
from app.models.tenant import TenantCreate


async def seed_demo_tenant():
    """Seed demo tenant into registry"""

    print("🌱 Seeding Demo Tenant...")

    # Demo tenant configuration
    demo_tenant = TenantCreate(
        company_name="TaskifAI Demo Organization",
        subdomain="demo",
        database_url=settings.supabase_url,  # Use main Supabase project for demo
        database_anon_key=settings.supabase_anon_key,
        database_service_key=settings.supabase_service_key,
        admin_email="admin@demo.taskifai.com",
        admin_name="Demo Admin",
        metadata={
            "environment": "development",
            "purpose": "Local development and testing",
            "created_by": "seed_script"
        }
    )

    try:
        # Check if demo tenant already exists
        print("🔍 Checking for existing demo tenant...")
        existing = await tenant_registry.get_by_subdomain("demo")

        if existing:
            print("⚠️  Demo tenant already exists!")
            print(f"   Tenant ID: {existing.tenant_id}")
            print(f"   Company: {existing.company_name}")
            print(f"   Subdomain: {existing.subdomain}")
            print(f"   Active: {existing.is_active}")
            print(f"   Created: {existing.created_at}")

            response = input("\n🤔 Delete and recreate? (yes/no): ")
            if response.lower() != "yes":
                print("❌ Aborted")
                return

            print("🗑️  Deleting existing demo tenant...")
            # Note: You'd need to add delete method to registry
            # For now, manually delete via SQL

        # Create demo tenant
        print("✨ Creating demo tenant...")
        tenant = await tenant_registry.create_tenant(demo_tenant)

        print("✅ Demo tenant created successfully!")
        print(f"   Tenant ID: {tenant.tenant_id}")
        print(f"   Company: {tenant.company_name}")
        print(f"   Subdomain: {tenant.subdomain}")
        print(f"   Access URL: {tenant.access_url}")
        print(f"   Active: {tenant.is_active}")

        print("\n🎉 Demo tenant is ready for development!")
        print("   Use subdomain 'demo' or 'localhost' for local testing")

    except ValueError as e:
        print(f"⚠️  Validation error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating demo tenant: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed_demo_tenant())
