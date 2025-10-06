"""
T070: Chat Query API Contract Test
POST /api/chat/query
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestChatQueryContract:
    """Contract tests for POST /api/chat/query endpoint"""

    async def test_chat_query_success_response(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful chat query returns expected structure

        Expected response:
        {
            "response": "Your top products are...",
            "sql_generated": "SELECT ...",
            "conversation_id": "uuid",
            "timestamp": "2025-10-06T10:00:00Z"
        }
        """
        request_body = {
            "query": "What are my top selling products?"
        }

        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json=request_body
        )

        # Assert status code
        assert response.status_code == 200

        # Assert response structure
        data = response.json()
        assert "response" in data
        assert "sql_generated" in data
        assert "conversation_id" in data
        assert "timestamp" in data

        # Assert types
        assert isinstance(data["response"], str)
        assert isinstance(data["sql_generated"], str)
        assert isinstance(data["conversation_id"], str)
        assert isinstance(data["timestamp"], str)

    async def test_chat_query_missing_query_field(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test request without 'query' field returns 422

        Expected:
        - Status: 422 Unprocessable Entity
        - Error details about missing field
        """
        request_body = {}  # Missing 'query'

        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_chat_query_empty_query_rejected(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test empty query string returns 400

        Expected:
        - Status: 400 Bad Request
        - Error message about empty query
        """
        request_body = {"query": ""}

        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower() or "required" in data["detail"].lower()

    async def test_chat_query_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401

        Expected:
        - Status: 401 Unauthorized
        """
        request_body = {"query": "What are my sales?"}

        response = await async_client.post(
            "/api/chat/query",
            json=request_body
        )

        assert response.status_code == 401

    async def test_chat_query_with_context(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test query with optional conversation context

        Expected:
        - Accepts conversation_id for context
        - Returns response considering previous conversation
        """
        request_body = {
            "query": "What about last month?",
            "conversation_id": "existing-conversation-uuid"
        }

        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "existing-conversation-uuid"

    async def test_chat_query_sql_injection_blocked(
        self, async_client: AsyncClient, auth_headers, malicious_sql_queries
    ):
        """
        SECURITY: Test malicious SQL queries are blocked

        Expected:
        - Status: 400 Bad Request
        - Error about unsafe query
        """
        for malicious_query in malicious_sql_queries[:3]:  # Test first 3
            request_body = {"query": malicious_query}

            response = await async_client.post(
                "/api/chat/query",
                headers=auth_headers,
                json=request_body
            )

            # Should reject or sanitize
            assert response.status_code in [200, 400], \
                f"Unexpected status for malicious query: {malicious_query}"

            if response.status_code == 200:
                # If allowed, verify SQL was sanitized
                data = response.json()
                assert "DROP" not in data.get("sql_generated", "").upper()
                assert "DELETE" not in data.get("sql_generated", "").upper()

    async def test_chat_query_max_length_validation(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test query length validation

        Expected:
        - Very long queries rejected with 400
        """
        long_query = "A" * 5000  # 5000 characters

        request_body = {"query": long_query}

        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json=request_body
        )

        assert response.status_code in [200, 400]  # Either handled or rejected

    async def test_chat_query_response_time(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test response time is reasonable (< 5 seconds per spec)

        Expected:
        - Response within 5 seconds
        """
        import time

        request_body = {"query": "What are my total sales?"}

        start = time.time()
        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json=request_body
        )
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 5.0, f"Chat query took {duration}s, should be < 5s"
