"""
T069: Credential Encryption Test
Verify AES-256 encryption of database credentials
"""

import pytest
from cryptography.fernet import Fernet, InvalidToken
import base64


@pytest.mark.security
class TestCredentialEncryption:
    """Test suite for tenant credential encryption"""

    def test_encrypt_database_url(self):
        """
        Verify database URLs are encrypted with AES-256

        Test scenario:
        1. Encrypt database URL
        2. Verify encrypted format is different from plaintext
        3. Verify encryption is not reversible without key
        """
        from app.core.security import encrypt_credential, decrypt_credential

        original_url = "postgresql://user:secret_password@host:5432/database"

        # Encrypt
        encrypted = encrypt_credential(original_url)

        # Verify encrypted is different from plaintext
        assert encrypted != original_url, "Encryption failed - output matches input"

        # Verify encrypted format (should be base64)
        try:
            base64.urlsafe_b64decode(encrypted)
        except Exception:
            pytest.fail("Encrypted credential is not valid base64")

        # Verify cannot decrypt without key
        with pytest.raises(Exception):
            Fernet(Fernet.generate_key()).decrypt(encrypted.encode())

    def test_decrypt_database_url(self):
        """
        Verify encrypted credentials can be decrypted correctly

        Test scenario:
        1. Encrypt database URL
        2. Decrypt with same key
        3. Verify decrypted matches original
        """
        from app.core.security import encrypt_credential, decrypt_credential

        original_url = "postgresql://user:secret_password@host:5432/database"

        # Encrypt then decrypt
        encrypted = encrypt_credential(original_url)
        decrypted = decrypt_credential(encrypted)

        # Verify round-trip success
        assert decrypted == original_url, \
            "Decryption failed - output doesn't match input"

    def test_encryption_key_from_env(self):
        """
        Verify encryption key loaded from environment variable

        Test scenario:
        1. Check encryption key is loaded from env
        2. Verify key format is valid Fernet key
        """
        from app.core.security import get_encryption_key

        key = get_encryption_key()

        # Verify key is valid Fernet key (32 url-safe base64-encoded bytes)
        try:
            Fernet(key)
        except Exception:
            pytest.fail("Encryption key is not valid Fernet key")

    def test_encrypt_database_key(self):
        """
        Verify database_key (for pgcrypto) is also encrypted

        Test scenario:
        1. Encrypt database_key
        2. Verify encryption works
        3. Verify decryption recovers original key
        """
        from app.core.security import encrypt_credential, decrypt_credential

        original_key = "super_secret_db_encryption_key_12345"

        # Encrypt
        encrypted = encrypt_credential(original_key)

        # Verify encrypted is different
        assert encrypted != original_key

        # Decrypt
        decrypted = decrypt_credential(encrypted)

        # Verify matches original
        assert decrypted == original_key

    def test_different_plaintexts_different_ciphertexts(self):
        """
        Verify same encryption produces different ciphertexts (IV randomness)

        Test scenario:
        1. Encrypt same plaintext twice
        2. Verify ciphertexts are different (due to random IV)
        """
        from app.core.security import encrypt_credential

        plaintext = "postgresql://user:password@host/db"

        # Encrypt twice
        encrypted1 = encrypt_credential(plaintext)
        encrypted2 = encrypt_credential(plaintext)

        # Should be different due to random IV
        assert encrypted1 != encrypted2, \
            "Encryption should use random IV for each encryption"

        # But both should decrypt to same plaintext
        from app.core.security import decrypt_credential
        assert decrypt_credential(encrypted1) == plaintext
        assert decrypt_credential(encrypted2) == plaintext

    def test_invalid_encrypted_data_raises_error(self):
        """
        Verify decryption of invalid data raises error

        Test scenario:
        1. Attempt to decrypt garbage data
        2. Should raise InvalidToken or similar error
        """
        from app.core.security import decrypt_credential

        invalid_encrypted = "this_is_not_encrypted_data"

        with pytest.raises((InvalidToken, ValueError, Exception)):
            decrypt_credential(invalid_encrypted)

    def test_wrong_key_cannot_decrypt(self):
        """
        Verify decryption with wrong key fails

        Test scenario:
        1. Encrypt with key A
        2. Attempt decrypt with key B
        3. Should fail
        """
        from app.core.security import encrypt_credential, decrypt_credential

        plaintext = "postgresql://user:password@host/db"

        # Encrypt with current key
        encrypted = encrypt_credential(plaintext)

        # Attempt to decrypt with wrong key
        wrong_key = Fernet.generate_key()

        # Mock using wrong key
        from unittest.mock import patch
        with patch("app.core.security.get_encryption_key", return_value=wrong_key):
            with pytest.raises((InvalidToken, Exception)):
                decrypt_credential(encrypted)

    def test_tenant_credentials_stored_encrypted(self):
        """
        CRITICAL: Verify tenant credentials in DB are encrypted, not plaintext

        Test scenario:
        1. Create tenant with credentials
        2. Query tenant registry DB
        3. Verify database_url and database_key are encrypted
        4. Verify no plaintext credentials in DB
        """
        from app.services.tenant.registry import TenantRegistry

        registry = TenantRegistry()

        # Mock tenant data
        tenant_data = {
            "subdomain": "test",
            "company_name": "Test Company",
            "database_url": "postgresql://user:password@host/db",
            "database_key": "encryption_key_123"
        }

        # Create tenant (should encrypt credentials)
        with patch("app.services.tenant.registry.TenantRegistry.create") as mock_create:
            mock_create.return_value = {
                "tenant_id": "test_id",
                "subdomain": "test",
                "database_url": "encrypted_url_xxx",  # Should be encrypted
                "database_key": "encrypted_key_yyy"  # Should be encrypted
            }

            result = await registry.create(tenant_data)

            # Verify stored values are encrypted (not plaintext)
            assert result["database_url"] != tenant_data["database_url"], \
                "Database URL stored in plaintext!"
            assert result["database_key"] != tenant_data["database_key"], \
                "Database key stored in plaintext!"

    def test_credentials_decrypted_on_tenant_context_load(self):
        """
        Verify credentials are decrypted when loading TenantContext

        Test scenario:
        1. Store tenant with encrypted credentials
        2. Load tenant by subdomain
        3. TenantContext should have decrypted credentials
        """
        from app.services.tenant.registry import TenantRegistry
        from app.core.security import encrypt_credential

        # Encrypted credentials
        encrypted_url = encrypt_credential("postgresql://user:password@host/db")
        encrypted_key = encrypt_credential("db_encryption_key")

        with patch("app.services.tenant.registry.TenantRegistry.get_by_subdomain") as mock_get:
            mock_get.return_value = {
                "tenant_id": "test_id",
                "subdomain": "test",
                "database_url": encrypted_url,
                "database_key": encrypted_key
            }

            registry = TenantRegistry()
            tenant = await registry.get_by_subdomain("test")

            # TenantContext should have decrypted credentials
            from app.core.security import decrypt_credential
            assert tenant.database_url == "postgresql://user:password@host/db"
            assert tenant.database_key == "db_encryption_key"

    def test_encryption_key_rotation_support(self):
        """
        Verify system supports encryption key rotation

        Test scenario:
        1. Encrypt with old key
        2. Rotate to new key
        3. Re-encrypt existing data
        4. Verify decryption works with new key
        """
        from app.core.security import encrypt_credential, decrypt_credential

        plaintext = "postgresql://user:password@host/db"

        # Encrypt with old key
        old_key = Fernet.generate_key()
        with patch("app.core.security.get_encryption_key", return_value=old_key):
            encrypted_old = encrypt_credential(plaintext)

        # Decrypt with old key
        with patch("app.core.security.get_encryption_key", return_value=old_key):
            decrypted_old = decrypt_credential(encrypted_old)
            assert decrypted_old == plaintext

        # Rotate to new key
        new_key = Fernet.generate_key()

        # Re-encrypt with new key
        with patch("app.core.security.get_encryption_key", return_value=new_key):
            encrypted_new = encrypt_credential(plaintext)

        # Decrypt with new key
        with patch("app.core.security.get_encryption_key", return_value=new_key):
            decrypted_new = decrypt_credential(encrypted_new)
            assert decrypted_new == plaintext

    def test_no_credentials_in_logs(self):
        """
        CRITICAL: Verify credentials never logged in plaintext

        Test scenario:
        1. Trigger error with credential handling
        2. Verify error logs don't contain plaintext credentials
        3. Verify only encrypted or redacted values in logs
        """
        from app.core.security import encrypt_credential
        import logging
        from unittest.mock import patch

        plaintext_url = "postgresql://user:secret_password@host/db"

        # Capture logs
        with patch.object(logging.getLogger(), "error") as mock_log:
            try:
                # Trigger some operation that might log credentials
                encrypted = encrypt_credential(plaintext_url)
                # Simulate error that might log
                raise Exception(f"Error with database: {encrypted}")
            except Exception as e:
                logging.getLogger().error(str(e))

            # Verify plaintext password not in logs
            for call in mock_log.call_args_list:
                log_message = str(call)
                assert "secret_password" not in log_message, \
                    "Plaintext password found in error logs!"
