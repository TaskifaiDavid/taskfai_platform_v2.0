#!/usr/bin/env python3
"""
Tenant Provisioning Script

Reads tenant details from tenants_to_add.md and generates SQL statements
for inserting tenants into the tenant registry database.

Usage:
    python backend/scripts/add_tenant.py

Output:
    Generates backend/scripts/add_tenants.sql
"""

import re
import json
import uuid
from pathlib import Path
from datetime import datetime


def parse_yaml_block(yaml_text: str) -> dict:
    """Parse simple YAML block into dictionary"""
    data = {}
    lines = yaml_text.strip().split('\n')

    current_key = None
    metadata_lines = []
    in_metadata = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if ':' in line and not in_metadata:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key == 'metadata':
                in_metadata = True
                metadata_lines = []
                continue

            # Convert boolean strings
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False

            data[key] = value
        elif in_metadata:
            # Collect metadata lines
            if line and ':' in line:
                metadata_lines.append(line)

    # Parse metadata if present
    if metadata_lines:
        metadata = {}
        for line in metadata_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                metadata[key] = value
        data['metadata'] = metadata

    return data


def validate_subdomain(subdomain: str) -> bool:
    """Validate subdomain format"""
    pattern = r'^[a-z0-9]([a-z0-9-]{0,48}[a-z0-9])?$'
    return bool(re.match(pattern, subdomain))


def generate_tenant_sql(tenant_data: dict, encryption_key: str = "PLACEHOLDER_KEY") -> str:
    """Generate SQL INSERT statement for tenant"""

    # Validate required fields
    required = ['company_name', 'subdomain', 'database_url', 'service_key', 'anon_key']
    missing = [f for f in required if f not in tenant_data]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    # Validate subdomain
    if not validate_subdomain(tenant_data['subdomain']):
        raise ValueError(f"Invalid subdomain format: {tenant_data['subdomain']}")

    # Generate UUID
    tenant_id = str(uuid.uuid4())

    # Prepare credentials JSON
    credentials = {
        "service_key": tenant_data['service_key'],
        "anon_key": tenant_data['anon_key']
    }
    credentials_json = json.dumps(credentials)

    # Prepare metadata
    metadata = tenant_data.get('metadata', {})
    metadata_json = json.dumps(metadata)

    # Generate SQL
    sql = f"""
-- Tenant: {tenant_data['company_name']} ({tenant_data['subdomain']})
INSERT INTO tenants (
    tenant_id,
    company_name,
    subdomain,
    database_url,
    encrypted_credentials,
    is_active,
    metadata
) VALUES (
    '{tenant_id}',
    '{tenant_data['company_name']}',
    '{tenant_data['subdomain']}',
    '{tenant_data['database_url']}',
    '{credentials_json}',  -- IMPORTANT: Encrypt this in production using encrypt_data() function
    {str(tenant_data.get('is_active', True)).upper()},
    '{metadata_json}'::jsonb
) ON CONFLICT (subdomain) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    database_url = EXCLUDED.database_url,
    encrypted_credentials = EXCLUDED.encrypted_credentials,
    is_active = EXCLUDED.is_active,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- Add tenant config
INSERT INTO tenant_configs (
    tenant_id,
    max_file_size_mb,
    features_enabled
) VALUES (
    '{tenant_id}',
    100,
    '{{
        "ai_chat": true,
        "dashboards": true,
        "email_reports": true,
        "api_access": false
    }}'::jsonb
) ON CONFLICT (tenant_id) DO NOTHING;
"""

    return sql


def main():
    """Main execution"""
    script_dir = Path(__file__).parent
    input_file = script_dir / "tenants_to_add.md"
    output_file = script_dir / "add_tenants.sql"

    # Read input file
    if not input_file.exists():
        print(f"❌ Error: {input_file} not found")
        print(f"   Create it by copying tenants_to_add.md template")
        return 1

    content = input_file.read_text()

    # Extract YAML blocks
    yaml_blocks = re.findall(r'```yaml\s*(.*?)\s*```', content, re.DOTALL)

    if not yaml_blocks:
        print(f"❌ Error: No YAML blocks found in {input_file}")
        print(f"   Make sure your tenant data is wrapped in ```yaml blocks")
        return 1

    # Generate SQL for each tenant
    sql_statements = []
    sql_statements.append(f"""-- ============================================
-- TaskifAI Tenant Provisioning SQL
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ============================================

-- IMPORTANT: This SQL contains unencrypted credentials!
-- For production:
-- 1. Use encrypt_data() function: encrypt_data('credentials_json', 'encryption_key')
-- 2. Store encryption key securely (NOT in code/SQL)
-- 3. Run this SQL in Supabase SQL Editor or via secure connection

""")

    tenant_count = 0
    for yaml_text in yaml_blocks:
        try:
            tenant_data = parse_yaml_block(yaml_text)

            # Skip empty blocks
            if not tenant_data or 'subdomain' not in tenant_data:
                continue

            sql = generate_tenant_sql(tenant_data)
            sql_statements.append(sql)
            tenant_count += 1

            print(f"✅ Generated SQL for tenant: {tenant_data['subdomain']} ({tenant_data['company_name']})")

        except Exception as e:
            print(f"❌ Error processing tenant: {e}")
            continue

    if tenant_count == 0:
        print(f"❌ No valid tenant data found")
        return 1

    # Write output
    sql_statements.append("""
-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check newly added tenants
SELECT
    company_name,
    subdomain,
    database_url,
    is_active,
    created_at
FROM tenants
ORDER BY created_at DESC
LIMIT 10;

-- Check tenant configs
SELECT
    t.company_name,
    t.subdomain,
    tc.max_file_size_mb,
    tc.features_enabled
FROM tenants t
JOIN tenant_configs tc ON t.tenant_id = tc.tenant_id
ORDER BY t.created_at DESC
LIMIT 10;
""")

    output_file.write_text('\n'.join(sql_statements))

    print(f"\n✅ Generated SQL file: {output_file}")
    print(f"   Tenants processed: {tenant_count}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review {output_file}")
    print(f"   2. Execute in Supabase SQL Editor (tenant registry database)")
    print(f"   3. Verify tenants: SELECT * FROM tenants ORDER BY created_at DESC;")
    print(f"\n⚠️  SECURITY WARNING:")
    print(f"   - Generated SQL contains unencrypted credentials")
    print(f"   - For production: Use encrypt_data() function")
    print(f"   - Delete {output_file} after execution")

    return 0


if __name__ == "__main__":
    exit(main())
