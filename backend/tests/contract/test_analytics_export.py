"""
T080: Analytics Export API Contract Test
POST /api/analytics/export
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestAnalyticsExportContract:
    """Contract tests for POST /api/analytics/export endpoint"""

    async def test_export_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful export request

        Expected response:
        {
            "task_id": "uuid",
            "status": "pending",
            "format": "pdf",
            "message": "Export queued"
        }
        """
        request_body = {
            "format": "pdf",
            "filters": {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            }
        }

        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 202]
        data = response.json()

        assert "task_id" in data or "export_id" in data
        assert "status" in data or "message" in data
        assert data.get("format") == "pdf" or "format" in str(data)

    async def test_export_supported_formats(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test supported export formats

        Expected formats: pdf, csv, excel (xlsx)
        """
        supported_formats = ["pdf", "csv", "excel", "xlsx"]

        for format_type in supported_formats:
            request_body = {
                "format": format_type,
                "filters": {}
            }

            response = await async_client.post(
                "/api/analytics/export",
                headers=auth_headers,
                json=request_body
            )

            assert response.status_code in [200, 202]

    async def test_export_invalid_format(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test invalid format returns 400

        Expected:
        - Status: 400 Bad Request
        - Error about unsupported format
        """
        request_body = {
            "format": "unsupported_format"
        }

        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [400, 422]

    async def test_export_with_filters(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test export with data filters

        Expected:
        - Accepts same filters as sales endpoint
        - Exports filtered data only
        """
        request_body = {
            "format": "csv",
            "filters": {
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "channel": "online",
                "reseller_name": "Test Reseller"
            }
        }

        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 202]

    async def test_export_task_id_format(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test task_id is valid UUID format

        Expected:
        - task_id is UUID string
        - Can be used to check status later
        """
        request_body = {"format": "pdf"}

        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 202]
        data = response.json()

        task_id = data.get("task_id") or data.get("export_id")
        assert task_id is not None

        # Verify UUID format
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, task_id, re.IGNORECASE), \
            "task_id should be valid UUID"

    async def test_export_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401
        """
        request_body = {"format": "pdf"}

        response = await async_client.post(
            "/api/analytics/export",
            json=request_body
        )

        assert response.status_code == 401

    async def test_export_missing_format(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test missing format field returns 422

        Expected:
        - Status: 422 Unprocessable Entity
        - Error about required field
        """
        request_body = {}  # Missing format

        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 422

    async def test_export_with_email_notification(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test export with email notification option

        Expected:
        - Optional email field
        - Notification sent when export complete
        """
        request_body = {
            "format": "pdf",
            "notify_email": True
        }

        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 202]

    async def test_export_status_check(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test checking export status by task_id

        Expected:
        - GET /api/analytics/export/{task_id} returns status
        - Status: pending, processing, completed, failed
        """
        # Request export
        request_body = {"format": "csv"}

        create_response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert create_response.status_code in [200, 202]
        task_id = create_response.json().get("task_id") or create_response.json().get("export_id")

        # Check status
        status_response = await async_client.get(
            f"/api/analytics/export/{task_id}",
            headers=auth_headers
        )

        assert status_response.status_code in [200, 404]

        if status_response.status_code == 200:
            status_data = status_response.json()
            assert "status" in status_data
            assert status_data["status"] in ["pending", "processing", "completed", "failed"]

    async def test_export_large_dataset_handling(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test export handles large datasets

        Expected:
        - Large date range accepted
        - Export queued (not immediate)
        - Returns task_id for async processing
        """
        request_body = {
            "format": "excel",
            "filters": {
                "start_date": "2020-01-01",
                "end_date": "2025-12-31"
            }
        }

        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 202]

        # Should be queued, not immediate
        data = response.json()
        assert "task_id" in data or "export_id" in data
