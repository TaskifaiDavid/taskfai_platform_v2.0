#!/usr/bin/env python3
"""
Tenant Registry Initialization Script

Creates the tenants table in the master Supabase database.
This table stores the master registry of all tenant organizations.

Run this script ONCE to initialize the tenant registry:
    python backend/db/init_tenant_registry.py
"""

import os
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from supabase import create_client
from app.core.config import settings


def init_tenant_registry():
    """Initialize tenant registry table in master database"""

    print("🔧 Initializing Tenant Registry...")
    print(f"📡 Connecting to: {settings.supabase_url}")

    # Connect to master database
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_key
    )

    # SQL to create tenants table
    create_table_sql = """
    -- Drop existing table if exists (for development only!)
    DROP TABLE IF EXISTS tenants CASCADE;

    -- Create tenants table
    CREATE TABLE tenants (
        tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        company_name VARCHAR(255) NOT NULL,
        subdomain VARCHAR(50) NOT NULL UNIQUE,
        database_url TEXT NOT NULL,  -- Encrypted PostgreSQL connection string
        database_credentials TEXT NOT NULL,  -- Encrypted JSON: {anon_key, service_key}
        is_active BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ,
        suspended_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}'::jsonb,

        -- Constraints
        CONSTRAINT valid_subdomain CHECK (subdomain ~ '^[a-z0-9-]+$'),
        CONSTRAINT no_hyphen_edges CHECK (
            subdomain !~ '^-' AND subdomain !~ '-$'
        )
    );

    -- Create indexes
    CREATE INDEX idx_tenants_subdomain ON tenants(subdomain);
    CREATE INDEX idx_tenants_active ON tenants(is_active) WHERE is_active = true;
    CREATE INDEX idx_tenants_created ON tenants(created_at DESC);

    -- Enable Row Level Security (RLS)
    ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

    -- RLS Policies
    -- Only service role can access tenant registry
    CREATE POLICY "Service role full access"
        ON tenants
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);

    -- Authenticated users can only view their own tenant
    CREATE POLICY "Users can view own tenant"
        ON tenants
        FOR SELECT
        TO authenticated
        USING (tenant_id = (current_setting('request.jwt.claims', true)::json->>'tenant_id')::uuid);

    COMMENT ON TABLE tenants IS 'Master registry of all tenant organizations';
    COMMENT ON COLUMN tenants.database_url IS 'Encrypted Supabase project URL';
    COMMENT ON COLUMN tenants.database_credentials IS 'Encrypted JSON with anon_key and service_key';
    COMMENT ON COLUMN tenants.is_active IS 'Tenant activation status (false = suspended)';
    """

    try:
        # Execute SQL via Supabase RPC or direct PostgreSQL connection
        # Note: Supabase client doesn't support raw DDL, so we use RPC

        print("📝 Creating tenants table...")

        # For now, print the SQL for manual execution
        # In production, use psycopg2 or asyncpg for direct execution
        print("\n" + "="*60)
        print("EXECUTE THIS SQL IN SUPABASE SQL EDITOR:")
        print("="*60)
        print(create_table_sql)
        print("="*60 + "\n")

        print("✅ Tenant registry schema ready!")
        print("⚠️  Please execute the SQL above in Supabase SQL Editor")
        print("    Dashboard → SQL Editor → New Query → Paste & Run")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    init_tenant_registry()
