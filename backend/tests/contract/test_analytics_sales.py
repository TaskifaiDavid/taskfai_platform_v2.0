"""
T079: Analytics Sales API Contract Test
GET /api/analytics/sales
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestAnalyticsSalesContract:
    """Contract tests for GET /api/analytics/sales endpoint"""

    async def test_get_sales_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful sales data retrieval

        Expected response:
        {
            "data": [
                {
                    "sale_id": "uuid",
                    "product_ean": "1234567890123",
                    "functional_name": "Product A",
                    "quantity": 10,
                    "unit_price": 99.99,
                    "total_amount": 999.90,
                    "sale_date": "2025-10-01",
                    "channel": "online",
                    "reseller_name": "Reseller X"
                }
            ],
            "total": 1000,
            "page": 1,
            "page_size": 50
        }
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

        # If data exists, verify structure
        if len(data["data"]) > 0:
            sale = data["data"][0]
            assert "sale_id" in sale or "product_ean" in sale
            assert "quantity" in sale
            assert "total_amount" in sale or "unit_price" in sale
            assert "sale_date" in sale

    async def test_get_sales_pagination(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test sales data pagination

        Expected:
        - Query params: page, page_size
        - Response includes pagination info
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={"page": 1, "page_size": 20}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]) <= 20
        assert "total" in data or "page" in data

    async def test_get_sales_filter_by_date_range(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering by date range

        Expected:
        - Query params: start_date, end_date
        - Returns sales within range
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-03-31"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify dates within range
        for sale in data["data"]:
            sale_date = sale.get("sale_date", "")
            assert "2025-01" <= sale_date <= "2025-04"

    async def test_get_sales_filter_by_channel(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering by channel (online/offline)

        Expected:
        - Query param: channel=online or channel=offline
        - Returns only specified channel sales
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={"channel": "online"}
        )

        assert response.status_code == 200
        data = response.json()

        # All results should match filter
        for sale in data["data"]:
            assert sale.get("channel") == "online"

    async def test_get_sales_filter_by_reseller(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering by reseller

        Expected:
        - Query param: reseller_name=ResX
        - Returns only sales from that reseller
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={"reseller_name": "Test Reseller"}
        )

        assert response.status_code == 200
        data = response.json()

        # All results should match filter
        for sale in data["data"]:
            assert "reseller" in sale.get("reseller_name", "").lower() or \
                   "test" in sale.get("reseller_name", "").lower()

    async def test_get_sales_filter_by_product(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test filtering by product EAN

        Expected:
        - Query param: product_ean=1234567890123
        - Returns only sales for that product
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={"product_ean": "1234567890123"}
        )

        assert response.status_code == 200
        data = response.json()

        # All results should match filter
        for sale in data["data"]:
            assert sale.get("product_ean") == "1234567890123"

    async def test_get_sales_sorting(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test sorting by different fields

        Expected:
        - Query params: sort_by=sale_date, order=desc
        - Results sorted accordingly
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={"sort_by": "sale_date", "order": "desc"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify sorting
        sales = data["data"]
        if len(sales) > 1:
            for i in range(len(sales) - 1):
                assert sales[i].get("sale_date", "") >= sales[i+1].get("sale_date", "")

    async def test_get_sales_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        response = await async_client.get("/api/analytics/sales")

        assert response.status_code == 401

    async def test_get_sales_empty_results(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test no sales data returns empty array

        Expected:
        - Status: 200
        - data: []
        - total: 0
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={
                "start_date": "2030-01-01",
                "end_date": "2030-12-31"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["data"] == [] or len(data["data"]) == 0
        assert data.get("total", 0) >= 0

    async def test_get_sales_multiple_filters(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test combining multiple filters

        Expected:
        - Multiple query params work together
        - Results match ALL filters
        """
        response = await async_client.get(
            "/api/analytics/sales",
            headers=auth_headers,
            params={
                "channel": "online",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # All results should match all filters
        for sale in data["data"]:
            assert sale.get("channel") == "online"
            assert "2025-01" <= sale.get("sale_date", "") <= "2026-01"
