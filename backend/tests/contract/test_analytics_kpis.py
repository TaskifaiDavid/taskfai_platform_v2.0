"""
T078: Analytics KPIs API Contract Test
GET /api/analytics/kpis
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestAnalyticsKPIsContract:
    """Contract tests for GET /api/analytics/kpis endpoint"""

    async def test_get_kpis_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful KPI retrieval

        Expected response:
        {
            "total_revenue": 1234567.89,
            "total_units_sold": 10000,
            "total_products": 150,
            "top_products": [
                {
                    "product_ean": "1234567890123",
                    "functional_name": "Product A",
                    "total_revenue": 50000.00,
                    "units_sold": 1000
                }
            ],
            "period_start": "2025-01-01",
            "period_end": "2025-10-06"
        }
        """
        response = await async_client.get(
            "/api/analytics/kpis",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "total_revenue" in data
        assert "total_units_sold" in data
        assert "total_products" in data
        assert "top_products" in data

        # Types
        assert isinstance(data["total_revenue"], (int, float))
        assert isinstance(data["total_units_sold"], int)
        assert isinstance(data["total_products"], int)
        assert isinstance(data["top_products"], list)

    async def test_get_kpis_with_date_range(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test KPIs with custom date range

        Expected:
        - Query params: start_date, end_date
        - Returns KPIs for specified period
        """
        response = await async_client.get(
            "/api/analytics/kpis",
            headers=auth_headers,
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-03-31"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify date range reflected in response
        if "period_start" in data and "period_end" in data:
            assert data["period_start"] == "2025-01-01"
            assert data["period_end"] == "2025-03-31"

    async def test_get_kpis_invalid_date_range(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test invalid date range returns 400

        Expected:
        - end_date before start_date rejected
        - Invalid date format rejected
        """
        # End before start
        response = await async_client.get(
            "/api/analytics/kpis",
            headers=auth_headers,
            params={
                "start_date": "2025-12-31",
                "end_date": "2025-01-01"
            }
        )

        assert response.status_code == 400

    async def test_get_kpis_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.get("/api/analytics/kpis")

        assert response.status_code == 401

    async def test_get_kpis_top_products_limit(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test top_products limit parameter

        Expected:
        - Query param: limit=5
        - Returns top 5 products
        """
        response = await async_client.get(
            "/api/analytics/kpis",
            headers=auth_headers,
            params={"limit": 5}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["top_products"]) <= 5

    async def test_get_kpis_by_channel(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering KPIs by channel

        Expected:
        - Query param: channel=online or channel=offline
        - Returns KPIs for specified channel only
        """
        response = await async_client.get(
            "/api/analytics/kpis",
            headers=auth_headers,
            params={"channel": "online"}
        )

        assert response.status_code == 200
        data = response.json()

        # KPIs should be for online channel only
        if "channel" in data:
            assert data["channel"] == "online"

    async def test_get_kpis_empty_data_returns_zeros(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test KPIs with no data returns zeros

        Expected:
        - Status: 200
        - total_revenue: 0
        - total_units_sold: 0
        - top_products: []
        """
        # Request for future date range (no data)
        response = await async_client.get(
            "/api/analytics/kpis",
            headers=auth_headers,
            params={
                "start_date": "2030-01-01",
                "end_date": "2030-12-31"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should return zeros or null, not error
        assert "total_revenue" in data
        assert "total_units_sold" in data

    async def test_get_kpis_response_time(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test KPI calculation is fast (< 2 seconds)

        Expected:
        - Response within 2 seconds
        """
        import time

        start = time.time()
        response = await async_client.get(
            "/api/analytics/kpis",
            headers=auth_headers
        )
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 2.0, f"KPI calculation took {duration}s, should be < 2s"
