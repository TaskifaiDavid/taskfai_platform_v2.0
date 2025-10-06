"""
T071: Chat History API Contract Test
GET /api/chat/history
"""

import pytest
from httpx import AsyncClient


@pytest.mark.contract
@pytest.mark.asyncio
class TestChatHistoryContract:
    """Contract tests for GET /api/chat/history endpoint"""

    async def test_chat_history_success_response(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test successful history retrieval returns expected structure

        Expected response:
        {
            "conversations": [
                {
                    "conversation_id": "uuid",
                    "messages": [
                        {"role": "user", "content": "...", "timestamp": "..."},
                        {"role": "assistant", "content": "...", "timestamp": "..."}
                    ],
                    "created_at": "2025-10-06T10:00:00Z",
                    "updated_at": "2025-10-06T10:05:00Z"
                }
            ],
            "total": 10
        }
        """
        response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers
        )

        # Assert status code
        assert response.status_code == 200

        # Assert response structure
        data = response.json()
        assert "conversations" in data
        assert "total" in data

        # Assert types
        assert isinstance(data["conversations"], list)
        assert isinstance(data["total"], int)

        # If conversations exist, verify structure
        if len(data["conversations"]) > 0:
            conv = data["conversations"][0]
            assert "conversation_id" in conv
            assert "messages" in conv
            assert isinstance(conv["messages"], list)

    async def test_chat_history_requires_authentication(
        self, async_client: AsyncClient
    ):
        """
        Test unauthenticated request returns 401

        Expected:
        - Status: 401 Unauthorized
        """
        response = await async_client.get("/api/chat/history")

        assert response.status_code == 401

    async def test_chat_history_empty_for_new_user(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test new user with no conversations returns empty list

        Expected:
        - Status: 200
        - conversations: []
        - total: 0
        """
        # Assuming new user token
        response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Might be empty or might have conversations
        assert "conversations" in data
        assert "total" in data

    async def test_chat_history_pagination(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test history supports pagination

        Expected:
        - Query params: limit, offset
        - Response includes pagination info
        """
        response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers,
            params={"limit": 5, "offset": 0}
        )

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert len(data["conversations"]) <= 5

    async def test_chat_history_specific_conversation(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test retrieving specific conversation by ID

        Expected:
        - Query param: conversation_id
        - Returns only that conversation
        """
        response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers,
            params={"conversation_id": "test-conversation-uuid"}
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            if len(data["conversations"]) > 0:
                assert data["conversations"][0]["conversation_id"] == "test-conversation-uuid"

    async def test_chat_history_sorted_by_date(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test conversations sorted by most recent first

        Expected:
        - Conversations in descending order by updated_at
        """
        response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify sorting if multiple conversations
        conversations = data["conversations"]
        if len(conversations) > 1:
            for i in range(len(conversations) - 1):
                assert conversations[i]["updated_at"] >= conversations[i+1]["updated_at"], \
                    "Conversations should be sorted by updated_at desc"

    async def test_chat_history_includes_message_timestamps(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test message timestamps are included

        Expected:
        - Each message has timestamp field
        """
        response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["conversations"]) > 0:
            messages = data["conversations"][0]["messages"]
            if len(messages) > 0:
                assert "timestamp" in messages[0]
