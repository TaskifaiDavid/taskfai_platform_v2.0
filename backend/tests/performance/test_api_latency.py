"""
Performance tests for API latency
Target: <200ms for all API endpoints
"""

import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


# Target latency in milliseconds
TARGET_LATENCY_MS = 200
ACCEPTABLE_LATENCY_MS = 300  # With tolerance


class TestAPILatencyPerformance:
    """Test API response time performance"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {
            "Authorization": "Bearer mock_token_for_testing"
        }

    # ============================================
    # AUTHENTICATION ENDPOINTS
    # ============================================

    @pytest.mark.performance
    def test_login_latency(self, client):
        """Test /api/auth/login latency"""
        start = time.perf_counter()

        response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword123"
        })

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\n/api/auth/login latency: {latency_ms:.2f}ms")
        assert latency_ms < ACCEPTABLE_LATENCY_MS, f"Login too slow: {latency_ms:.2f}ms"

    @pytest.mark.performance
    def test_register_latency(self, client):
        """Test /api/auth/register latency"""
        start = time.perf_counter()

        response = client.post("/api/auth/register", json={
            "email": f"test{time.time()}@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        })

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\n/api/auth/register latency: {latency_ms:.2f}ms")
        assert latency_ms < ACCEPTABLE_LATENCY_MS, f"Register too slow: {latency_ms:.2f}ms"

    @pytest.mark.performance
    def test_get_current_user_latency(self, client, auth_headers):
        """Test /api/auth/me latency"""
        start = time.perf_counter()

        response = client.get("/api/auth/me", headers=auth_headers)

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\n/api/auth/me latency: {latency_ms:.2f}ms")
        assert latency_ms < TARGET_LATENCY_MS, f"Get user too slow: {latency_ms:.2f}ms"

    # ============================================
    # UPLOAD ENDPOINTS
    # ============================================

    @pytest.mark.performance
    def test_list_uploads_latency(self, client, auth_headers):
        """Test GET /api/uploads latency"""
        start = time.perf_counter()

        response = client.get("/api/uploads", headers=auth_headers)

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\nGET /api/uploads latency: {latency_ms:.2f}ms")
        assert latency_ms < TARGET_LATENCY_MS, f"List uploads too slow: {latency_ms:.2f}ms"

    @pytest.mark.performance
    def test_get_upload_details_latency(self, client, auth_headers):
        """Test GET /api/uploads/{id} latency"""
        upload_id = "test-upload-id"

        start = time.perf_counter()

        response = client.get(f"/api/uploads/{upload_id}", headers=auth_headers)

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\nGET /api/uploads/{{id}} latency: {latency_ms:.2f}ms")
        assert latency_ms < TARGET_LATENCY_MS, f"Get upload details too slow: {latency_ms:.2f}ms"

    # ============================================
    # ANALYTICS ENDPOINTS
    # ============================================

    @pytest.mark.performance
    def test_get_kpis_latency(self, client, auth_headers):
        """Test GET /api/analytics/kpis latency"""
        start = time.perf_counter()

        response = client.get(
            "/api/analytics/kpis",
            headers=auth_headers,
            params={"start_date": "2024-01-01", "end_date": "2024-12-31"}
        )

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\nGET /api/analytics/kpis latency: {latency_ms:.2f}ms")
        assert latency_ms < ACCEPTABLE_LATENCY_MS, f"Get KPIs too slow: {latency_ms:.2f}ms"

    @pytest.mark.performance
    def test_get_sales_data_latency(self, client, auth_headers):
        """Test GET /api/analytics/sales latency"""
        start = time.perf_counter()

        response = client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={"limit": 100, "offset": 0}
        )

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\nGET /api/analytics/sales latency: {latency_ms:.2f}ms")
        assert latency_ms < ACCEPTABLE_LATENCY_MS, f"Get sales data too slow: {latency_ms:.2f}ms"

    # ============================================
    # CHAT ENDPOINTS
    # ============================================

    @pytest.mark.performance
    def test_get_chat_history_latency(self, client, auth_headers):
        """Test GET /api/chat/history latency"""
        start = time.perf_counter()

        response = client.get("/api/chat/history", headers=auth_headers)

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\nGET /api/chat/history latency: {latency_ms:.2f}ms")
        assert latency_ms < TARGET_LATENCY_MS, f"Get chat history too slow: {latency_ms:.2f}ms"

    # ============================================
    # DASHBOARD ENDPOINTS
    # ============================================

    @pytest.mark.performance
    def test_list_dashboards_latency(self, client, auth_headers):
        """Test GET /api/dashboards latency"""
        start = time.perf_counter()

        response = client.get("/api/dashboards", headers=auth_headers)

        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\nGET /api/dashboards latency: {latency_ms:.2f}ms")
        assert latency_ms < TARGET_LATENCY_MS, f"List dashboards too slow: {latency_ms:.2f}ms"

    # ============================================
    # CONCURRENT REQUEST TESTS
    # ============================================

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client, auth_headers):
        """Test API latency under concurrent load"""
        concurrent_requests = 10

        async def make_request():
            start = time.perf_counter()
            response = client.get("/api/auth/me", headers=auth_headers)
            latency = (time.perf_counter() - start) * 1000
            return latency

        # Execute concurrent requests
        start_total = time.perf_counter()
        latencies = await asyncio.gather(*[make_request() for _ in range(concurrent_requests)])
        total_time = (time.perf_counter() - start_total) * 1000

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        print(f"\nConcurrent requests: {concurrent_requests}")
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"Max latency: {max_latency:.2f}ms")
        print(f"Min latency: {min_latency:.2f}ms")
        print(f"Total time: {total_time:.2f}ms")

        # Under concurrent load, allow slightly higher latency
        assert avg_latency < ACCEPTABLE_LATENCY_MS * 1.5, f"Average latency too high: {avg_latency:.2f}ms"
        assert max_latency < ACCEPTABLE_LATENCY_MS * 2, f"Max latency too high: {max_latency:.2f}ms"

    # ============================================
    # DATABASE QUERY OPTIMIZATION TESTS
    # ============================================

    @pytest.mark.performance
    def test_paginated_query_latency(self, client, auth_headers):
        """Test paginated query performance"""
        page_sizes = [10, 50, 100]

        for page_size in page_sizes:
            start = time.perf_counter()

            response = client.get(
                "/api/analytics/sales",
                headers=auth_headers,
                params={"limit": page_size, "offset": 0}
            )

            latency_ms = (time.perf_counter() - start) * 1000

            print(f"\nPagination (limit={page_size}) latency: {latency_ms:.2f}ms")

            # Larger page sizes allowed slightly more time
            acceptable_latency = TARGET_LATENCY_MS + (page_size / 100 * 100)
            assert latency_ms < acceptable_latency, f"Pagination too slow for limit={page_size}: {latency_ms:.2f}ms"

    # ============================================
    # COLD START vs WARM CACHE TESTS
    # ============================================

    @pytest.mark.performance
    def test_cache_warm_vs_cold_latency(self, client, auth_headers):
        """Test latency difference between cold and warm cache"""
        endpoint = "/api/analytics/kpis"
        params = {"start_date": "2024-01-01", "end_date": "2024-12-31"}

        # Cold start (first request)
        start_cold = time.perf_counter()
        response_cold = client.get(endpoint, headers=auth_headers, params=params)
        cold_latency = (time.perf_counter() - start_cold) * 1000

        # Warm cache (second request)
        start_warm = time.perf_counter()
        response_warm = client.get(endpoint, headers=auth_headers, params=params)
        warm_latency = (time.perf_counter() - start_warm) * 1000

        print(f"\nCold start latency: {cold_latency:.2f}ms")
        print(f"\nWarm cache latency: {warm_latency:.2f}ms")
        print(f"Improvement: {((cold_latency - warm_latency) / cold_latency * 100):.1f}%")

        # Warm cache should be faster or same
        assert warm_latency <= cold_latency * 1.2, "Warm cache not performing better"

    # ============================================
    # ENDPOINT STRESS TEST
    # ============================================

    @pytest.mark.performance
    @pytest.mark.slow
    def test_sustained_load_latency(self, client, auth_headers):
        """Test latency under sustained load"""
        num_requests = 100
        latencies = []

        start_total = time.perf_counter()

        for i in range(num_requests):
            start = time.perf_counter()
            response = client.get("/api/auth/me", headers=auth_headers)
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        total_time = (time.perf_counter() - start_total) * 1000

        avg_latency = sum(latencies) / len(latencies)
        p50 = sorted(latencies)[len(latencies) // 2]
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]

        print(f"\nSustained load test ({num_requests} requests):")
        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"P50 latency: {p50:.2f}ms")
        print(f"P95 latency: {p95:.2f}ms")
        print(f"P99 latency: {p99:.2f}ms")
        print(f"Total time: {total_time:.2f}ms")
        print(f"Requests/second: {(num_requests / (total_time / 1000)):.2f}")

        # Performance thresholds
        assert avg_latency < ACCEPTABLE_LATENCY_MS, f"Average latency too high: {avg_latency:.2f}ms"
        assert p95 < ACCEPTABLE_LATENCY_MS * 1.5, f"P95 latency too high: {p95:.2f}ms"
        assert p99 < ACCEPTABLE_LATENCY_MS * 2, f"P99 latency too high: {p99:.2f}ms"


# ============================================
# LATENCY BREAKDOWN TESTS
# ============================================

class TestLatencyBreakdown:
    """Test latency breakdown by component"""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    @pytest.mark.performance
    def test_middleware_overhead(self, client):
        """Measure middleware processing time"""
        # This would require instrumentation in the actual middleware
        # For now, test overall request latency
        start = time.perf_counter()
        response = client.get("/api/health")  # Minimal endpoint
        latency_ms = (time.perf_counter() - start) * 1000

        print(f"\nMinimal endpoint latency (middleware overhead): {latency_ms:.2f}ms")

        # Middleware should add minimal overhead
        assert latency_ms < 50, f"Middleware overhead too high: {latency_ms:.2f}ms"

    @pytest.mark.performance
    def test_database_query_time(self, client, mocker):
        """Test database query time impact on latency"""
        # This test requires database mocking or profiling
        # Placeholder for database performance testing
        pass


# ============================================
# PERFORMANCE REGRESSION TESTS
# ============================================

class TestPerformanceRegression:
    """Test for performance regressions"""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    @pytest.mark.performance
    def test_baseline_performance_metrics(self, client):
        """Establish baseline performance metrics"""
        endpoints = [
            "/api/health",
            "/api/auth/me",
            "/api/uploads",
            "/api/dashboards",
        ]

        auth_headers = {"Authorization": "Bearer mock_token"}
        metrics = {}

        for endpoint in endpoints:
            start = time.perf_counter()
            try:
                response = client.get(endpoint, headers=auth_headers)
            except Exception:
                pass
            latency = (time.perf_counter() - start) * 1000
            metrics[endpoint] = latency

        print("\nBaseline Performance Metrics:")
        for endpoint, latency in metrics.items():
            print(f"{endpoint}: {latency:.2f}ms")

        # Store these as baseline for future regression testing
        # In CI/CD, compare against stored baseline values
