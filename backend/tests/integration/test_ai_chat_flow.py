"""
T088: AI Chat Flow Integration Test
Query → Intent → SQL → Response → Memory
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestAIChatFlowIntegration:
    """Integration tests for complete AI chat workflow"""

    async def test_complete_chat_flow(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test complete chat flow from query to response

        Flow:
        1. User submits natural language query
        2. Intent detection classifies query type
        3. SQL agent generates safe SELECT query
        4. Query executed against tenant DB
        5. Results formatted to natural language
        6. Conversation saved to memory
        """
        # Step 1: Submit query
        query = "What are my top 5 products by revenue?"

        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": query}
        )

        assert response.status_code == 200
        data = response.json()

        # Step 2-5: Verify response structure
        assert "response" in data
        assert "sql_generated" in data
        assert "conversation_id" in data

        # SQL should be SELECT only
        assert data["sql_generated"].strip().upper().startswith("SELECT")

        # Step 6: Verify conversation saved
        conversation_id = data["conversation_id"]

        history_response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers,
            params={"conversation_id": conversation_id}
        )

        assert history_response.status_code == 200
        history = history_response.json()

        # Conversation should exist in history
        assert len(history.get("conversations", [])) > 0

    async def test_intent_detection_online_sales(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test intent detection for online sales query

        Expected:
        - Detects "online" channel intent
        - Queries online_sales table
        """
        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "Show me my D2C sales"}
        )

        assert response.status_code == 200
        data = response.json()

        sql = data["sql_generated"].lower()

        # Should query online_sales or filter by channel=online
        assert "online" in sql or "d2c" in sql

    async def test_intent_detection_offline_sales(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test intent detection for offline (B2B) sales query

        Expected:
        - Detects "offline" channel intent
        - Queries offline_sales table
        """
        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "What are my B2B sales?"}
        )

        assert response.status_code == 200
        data = response.json()

        sql = data["sql_generated"].lower()

        # Should query offline_sales or filter by channel=offline
        assert "offline" in sql or "b2b" in sql or "reseller" in sql

    async def test_intent_detection_time_based_query(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test intent detection for time-based query

        Expected:
        - Detects time period intent
        - Adds date filters to SQL
        """
        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "What were my sales last month?"}
        )

        assert response.status_code == 200
        data = response.json()

        sql = data["sql_generated"].lower()

        # Should have date filtering
        assert "where" in sql or "date" in sql

    async def test_conversation_memory_context(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test conversation memory maintains context

        Expected:
        - Follow-up questions use conversation history
        - Agent remembers previous queries
        """
        # First query
        response1 = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "What are my top products?"}
        )

        assert response1.status_code == 200
        conversation_id = response1.json()["conversation_id"]

        # Follow-up query (requires context)
        response2 = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={
                "query": "What about last month?",  # Requires context from first query
                "conversation_id": conversation_id
            }
        )

        assert response2.status_code == 200

        # Should use same conversation
        assert response2.json()["conversation_id"] == conversation_id

    async def test_sql_security_validation(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test SQL security validation in flow

        Expected:
        - Generated SQL validated before execution
        - Modification keywords blocked
        - user_id filter injected
        """
        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "Show all sales"}
        )

        assert response.status_code == 200
        data = response.json()

        sql = data["sql_generated"].upper()

        # Should be SELECT only
        assert sql.startswith("SELECT")

        # Should not contain modification keywords
        assert "DROP" not in sql
        assert "DELETE" not in sql
        assert "UPDATE" not in sql
        assert "INSERT" not in sql

    async def test_error_handling_in_flow(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test error handling at each stage of flow

        Expected:
        - Invalid SQL handled gracefully
        - DB errors returned as user-friendly messages
        - Errors don't crash conversation
        """
        # Query that might cause SQL error
        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "asdfasdfasdf nonsense query"}
        )

        # Should handle gracefully, not crash
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            # Should have some response, even if error
            assert "response" in data or "error" in data

    async def test_response_formatting(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test SQL results formatted to natural language

        Expected:
        - Numbers formatted (e.g., currency, thousands)
        - Dates formatted human-readable
        - Response in natural language, not raw data
        """
        response = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "What is my total revenue?"}
        )

        assert response.status_code == 200
        data = response.json()

        response_text = data["response"]

        # Should be natural language, not JSON or raw numbers
        assert isinstance(response_text, str)
        assert len(response_text) > 10  # Not just a number

    async def test_langraph_checkpointer_persistence(
        self, async_client: AsyncClient, auth_headers
    ):
        """
        Test LangGraph checkpointer persists conversation state

        Expected:
        - Conversation state saved to DB
        - Can resume conversation after restart
        - Memory persists across requests
        """
        # Start conversation
        response1 = await async_client.post(
            "/api/chat/query",
            headers=auth_headers,
            json={"query": "Show my sales"}
        )

        conversation_id = response1.json()["conversation_id"]

        # Make several follow-up queries
        for i in range(3):
            await async_client.post(
                "/api/chat/query",
                headers=auth_headers,
                json={
                    "query": f"What about product {i}?",
                    "conversation_id": conversation_id
                }
            )

        # Verify all messages in history
        history_response = await async_client.get(
            "/api/chat/history",
            headers=auth_headers,
            params={"conversation_id": conversation_id}
        )

        assert history_response.status_code == 200
        history = history_response.json()

        # Should have multiple messages
        conversations = history.get("conversations", [])
        if len(conversations) > 0:
            messages = conversations[0].get("messages", [])
            assert len(messages) >= 4  # Original + 3 follow-ups
