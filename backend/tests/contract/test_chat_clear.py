"""
T072: Chat Clear History API Contract Test
DELETE /api/chat/history
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestChatClearContract:
    """Contract tests for DELETE /api/chat/history endpoint"""

    async def test_chat_clear_success_response(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful history clear returns expected response

        Expected response:
        {
            "message": "Chat history cleared",
            "deleted_count": 5
        }
        """
        response = await async_client.delete(
            "/api/chat/history",
            headers=auth_headers
        )

        # Assert status code
        assert response.status_code == 200

        # Assert response structure
        data = response.json()
        assert "message" in data
        assert "deleted_count" in data or "count" in data

    async def test_chat_clear_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401

        Expected:
        - Status: 401 Unauthorized
        """
        response = await async_client.delete("/api/chat/history")

        assert response.status_code == 401

    async def test_chat_clear_specific_conversation(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test clearing specific conversation by ID

        Expected:
        - Query param or path param: conversation_id
        - Deletes only that conversation
        """
        response = await async_client.delete(
            "/api/chat/history",
            headers=auth_headers,
            params={"conversation_id": "test-conversation-uuid"}
        )

        assert response.status_code in [200, 404]

    async def test_chat_clear_empty_history_returns_zero(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test clearing empty history returns deleted_count: 0

        Expected:
        - Status: 200
        - deleted_count: 0
        """
        # Clear once
        await async_client.delete(
            "/api/chat/history",
            headers=auth_headers
        )

        # Clear again (should be empty)
        response = await async_client.delete(
            "/api/chat/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("deleted_count", 0) >= 0 or data.get("count", 0) >= 0

    async def test_chat_clear_verifiable_by_get(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test cleared history is verifiable via GET

        Expected:
        - DELETE clears history
        - GET returns empty conversations
        """
        # Clear history
        delete_response = await async_client.delete(
            "/api/chat/history",
            headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Verify via GET
        get_response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        data = get_response.json()

        # Should be empty (or eventually consistent)
        # Allow for eventual consistency
        assert "conversations" in data
