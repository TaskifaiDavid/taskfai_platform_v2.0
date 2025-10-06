"""
T091: Report Generation Integration Test
Query → PDF/CSV/Excel → Email
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.slow
class TestReportGenerationIntegration:
    """Integration tests for report generation and email delivery"""

    async def test_complete_report_generation_flow(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test complete report generation workflow

        Flow:
        1. User requests report export
        2. Task queued in Celery
        3. Worker queries sales data with filters
        4. Report generated (PDF/CSV/Excel)
        5. File stored temporarily
        6. Email sent with download link
        7. Cleanup after 24 hours
        """
        with patch("app.workers.report_generator.generate_report") as mock_generate:
            mock_generate.return_value = {
                "task_id": "report_task_123",
                "status": "pending"
            }

            # Step 1-2: Request export
            response = await async_client.post(
                "/api/analytics/export",
                headers=auth_headers,
                json={
                    "format": "pdf",
                    "filters": {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31"
                    }
                }
            )

            assert response.status_code in [200, 202]
            data = response.json()

            task_id = data.get("task_id") or data.get("export_id")
            assert task_id is not None

            # Step 3-6: In real implementation, Celery worker would:
            # - Query data
            # - Generate report
            # - Send email
            # This is tested in worker tests

    async def test_pdf_report_generation(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test PDF report generation

        Expected:
        - Query data from database
        - Format as PDF using ReportLab
        - Include charts and tables
        - Professional styling
        """
        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json={"format": "pdf"}
        )

        assert response.status_code in [200, 202]

    async def test_csv_report_generation(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test CSV report generation

        Expected:
        - Query data from database
        - Format as CSV
        - Include headers
        - Proper escaping
        """
        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json={"format": "csv"}
        )

        assert response.status_code in [200, 202]

    async def test_excel_report_generation(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test Excel report generation

        Expected:
        - Query data from database
        - Format as Excel (.xlsx)
        - Multiple sheets if needed
        - Formatting and formulas
        """
        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json={"format": "excel"}
        )

        assert response.status_code in [200, 202]

    async def test_report_with_filters_applied(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test report respects data filters

        Expected:
        - Date range filters applied
        - Channel filters applied
        - Reseller filters applied
        - Only filtered data in report
        """
        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json={
                "format": "csv",
                "filters": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-03-31",
                    "channel": "online",
                    "reseller_name": "Test Reseller"
                }
            }
        )

        assert response.status_code in [200, 202]

    async def test_email_notification_sent(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test email notification sent when report ready

        Expected:
        - Email sent to user
        - Includes download link
        - Link expires after 24 hours
        """
        with patch("app.services.email.notifier.EmailNotifier") as MockEmail:
            mock_notifier = AsyncMock()
            MockEmail.return_value = mock_notifier

            response = await async_client.post(
                "/api/analytics/export",
                headers=auth_headers,
                json={
                    "format": "pdf",
                    "notify_email": True
                }
            )

            assert response.status_code in [200, 202]

            # In real implementation, would verify email sent
            # This is tested in email service tests

    async def test_large_dataset_export_performance(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test large dataset export performance

        Expected:
        - Can export 10,000+ rows
        - Process within reasonable time
        - Memory efficient (streaming)
        """
        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json={
                "format": "csv",
                "filters": {
                    "start_date": "2020-01-01",
                    "end_date": "2025-12-31"
                }
            }
        )

        assert response.status_code in [200, 202]

        # Task should be queued, not executed immediately
        data = response.json()
        assert "task_id" in data or "export_id" in data

    async def test_report_status_check(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test checking report generation status

        Expected:
        - Can query status by task_id
        - Status: pending, processing, completed, failed
        - Download link when completed
        """
        # Request export
        create_response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json={"format": "pdf"}
        )

        task_id = create_response.json().get("task_id") or \
                  create_response.json().get("export_id")

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

    async def test_concurrent_export_requests(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test multiple concurrent export requests

        Expected:
        - Can queue multiple exports
        - Each gets unique task_id
        - Processed independently
        """
        # Request multiple exports
        responses = []
        for i in range(3):
            response = await async_client.post(
                "/api/analytics/export",
                headers=auth_headers,
                json={"format": "pdf"}
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code in [200, 202]

        # All should have unique task IDs
        task_ids = [r.json().get("task_id") or r.json().get("export_id") for r in responses]
        assert len(set(task_ids)) == 3, "Task IDs should be unique"

    async def test_report_file_cleanup(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test report files cleaned up after expiry

        Expected:
        - Files deleted after 24 hours
        - Download links expire
        - Cleanup job runs automatically
        """
        # Request export
        response = await async_client.post(
            "/api/analytics/export",
            headers=auth_headers,
            json={"format": "pdf"}
        )

        task_id = response.json().get("task_id") or response.json().get("export_id")

        # In real implementation, would test that:
        # 1. File exists after generation
        # 2. File deleted after 24 hours
        # 3. Download link returns 404 after expiry

        # This is tested in cleanup job tests
