"""
Pytest Configuration and Shared Fixtures
"""

import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import asyncpg

from app.main import app
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.core.tenant import TenantContext


# ============================================================================
# Application Fixtures
# ============================================================================

@pytest.fixture
def test_app():
    """FastAPI application instance for testing"""
    return app


@pytest.fixture
def client(test_app) -> Generator[TestClient, None, None]:
    """Synchronous test client for FastAPI"""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Async test client for FastAPI"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Tenant Fixtures
# ============================================================================

@pytest.fixture
def tenant_demo() -> TenantContext:
    """Demo tenant context for testing"""
    return TenantContext(
        tenant_id="550e8400-e29b-41d4-a716-446655440000",
        subdomain="demo",
        database_url="postgresql://user:pass@localhost:5432/demo_db",
        database_key="test_key_demo"
    )


@pytest.fixture
def tenant_acme() -> TenantContext:
    """Acme tenant context for testing isolation"""
    return TenantContext(
        tenant_id="660e8400-e29b-41d4-a716-446655440111",
        subdomain="acme",
        database_url="postgresql://user:pass@localhost:5432/acme_db",
        database_key="test_key_acme"
    )


@pytest.fixture
def tenant_beta() -> TenantContext:
    """Beta tenant context for testing isolation"""
    return TenantContext(
        tenant_id="770e8400-e29b-41d4-a716-446655440222",
        subdomain="beta",
        database_url="postgresql://user:pass@localhost:5432/beta_db",
        database_key="test_key_beta"
    )


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "email": "test@example.com",
        "role": "user",
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "subdomain": "demo"
    }


@pytest.fixture
def test_admin_data():
    """Test admin user data"""
    return {
        "user_id": "223e4567-e89b-12d3-a456-426614174001",
        "email": "admin@example.com",
        "role": "admin",
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "subdomain": "demo"
    }


@pytest.fixture
def test_user_token(test_user_data) -> str:
    """Generate JWT token for test user"""
    return create_access_token(data=test_user_data)


@pytest.fixture
def test_admin_token(test_admin_data) -> str:
    """Generate JWT token for test admin"""
    return create_access_token(data=test_admin_data)


@pytest.fixture
def auth_headers(test_user_token) -> dict:
    """Authorization headers with test user token"""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_headers(test_admin_token) -> dict:
    """Authorization headers with test admin token"""
    return {"Authorization": f"Bearer {test_admin_token}"}


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def test_password_hash() -> str:
    """Hashed password for testing"""
    return get_password_hash("test_password_123")


@pytest.fixture
async def db_pool():
    """Database connection pool for testing"""
    pool = await asyncpg.create_pool(
        dsn=settings.database_url or "postgresql://postgres:postgres@localhost:5432/test_db",
        min_size=1,
        max_size=5
    )
    yield pool
    await pool.close()


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def mock_upload_data():
    """Mock upload data for testing"""
    return {
        "batch_id": "batch_123",
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
        "file_name": "test_sales.xlsx",
        "file_size": 1024,
        "vendor_name": "boxnox",
        "status": "processing",
        "rows_processed": 0,
        "rows_failed": 0,
        "uploaded_at": "2025-10-06T10:00:00Z"
    }


@pytest.fixture
def mock_sales_data():
    """Mock sales data for testing"""
    return [
        {
            "sale_id": "sale_001",
            "product_ean": "1234567890123",
            "quantity": 10,
            "unit_price": 99.99,
            "total_amount": 999.90,
            "sale_date": "2025-10-01",
            "channel": "online",
            "reseller_name": "Test Reseller"
        },
        {
            "sale_id": "sale_002",
            "product_ean": "9876543210987",
            "quantity": 5,
            "unit_price": 49.99,
            "total_amount": 249.95,
            "sale_date": "2025-10-02",
            "channel": "offline",
            "reseller_name": "Another Reseller"
        }
    ]


# ============================================================================
# Security Test Fixtures
# ============================================================================

@pytest.fixture
def malicious_sql_queries() -> list[str]:
    """Common SQL injection attack patterns for testing"""
    return [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--",
        "'; DELETE FROM sales WHERE '1'='1",
        "1'; UPDATE users SET role='admin' WHERE '1'='1",
        "1' AND 1=1 UNION ALL SELECT 1,2,3,4,5,6,7,8,9,10--",
        "' OR 1=1--",
        "admin' OR '1'='1'/*",
    ]


@pytest.fixture
def malicious_subdomain_patterns() -> list[str]:
    """Subdomain spoofing attack patterns for testing"""
    return [
        "../../../etc/passwd",
        "demo.evil.com",
        "demo'; DROP TABLE--",
        "<script>alert('xss')</script>",
        "demo\x00evil",
        "demo%00evil",
        "../../admin",
        "localhost",
        "127.0.0.1",
        "demo.example.com.attacker.com"
    ]


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )
    config.addinivalue_line(
        "markers", "contract: mark test as API contract test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )
