-- ============================================
-- Tenant Registry RPC Functions
-- Used by TenantRegistryService for encrypted operations
-- ============================================

-- Create tenant with encrypted credentials
CREATE OR REPLACE FUNCTION create_tenant_with_encryption(
    p_subdomain TEXT,
    p_company_name TEXT,
    p_database_url TEXT,
    p_credentials_json TEXT,
    p_encryption_key TEXT
) RETURNS TABLE(
    tenant_id UUID,
    subdomain TEXT,
    company_name TEXT,
    database_url TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ
)
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO tenants (subdomain, company_name, database_url, encrypted_credentials, is_active)
    VALUES (
        p_subdomain,
        p_company_name,
        p_database_url,
        encode(pgp_sym_encrypt(p_credentials_json, p_encryption_key), 'base64'),
        TRUE
    )
    RETURNING tenants.tenant_id, tenants.subdomain, tenants.company_name, tenants.database_url, tenants.is_active, tenants.created_at;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get tenant with decrypted credentials
CREATE OR REPLACE FUNCTION get_tenant_with_credentials(
    p_subdomain TEXT,
    p_encryption_key TEXT
) RETURNS TABLE(
    tenant_id UUID,
    subdomain TEXT,
    company_name TEXT,
    database_url TEXT,
    decrypted_credentials TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tenants.tenant_id,
        tenants.subdomain,
        tenants.company_name,
        tenants.database_url,
        pgp_sym_decrypt(decode(tenants.encrypted_credentials, 'base64'), p_encryption_key) AS decrypted_credentials,
        tenants.is_active,
        tenants.created_at,
        tenants.updated_at
    FROM tenants
    WHERE tenants.subdomain = p_subdomain;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update tenant credentials with encryption
CREATE OR REPLACE FUNCTION update_tenant_credentials(
    p_tenant_id UUID,
    p_credentials_json TEXT,
    p_encryption_key TEXT
) RETURNS BOOLEAN
AS $$
BEGIN
    UPDATE tenants
    SET
        encrypted_credentials = encode(pgp_sym_encrypt(p_credentials_json, p_encryption_key), 'base64'),
        updated_at = NOW()
    WHERE tenant_id = p_tenant_id;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comments for documentation
COMMENT ON FUNCTION create_tenant_with_encryption IS 'Creates a new tenant with pgp_sym_encrypt for credentials encryption';
COMMENT ON FUNCTION get_tenant_with_credentials IS 'Retrieves tenant with decrypted credentials using pgp_sym_decrypt';
COMMENT ON FUNCTION update_tenant_credentials IS 'Updates tenant credentials with re-encryption';
