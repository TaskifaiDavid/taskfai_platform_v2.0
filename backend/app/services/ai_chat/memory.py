"""
Conversation memory service for persistent chat history
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncpg
from uuid import UUID, uuid4


class ConversationMemory:
    """
    Database-backed conversation memory for chat persistence

    Stores conversation history in database for:
    - Session continuity across requests
    - Conversation history retrieval
    - Analytics and debugging
    """

    def __init__(self, db_connection_pool: asyncpg.Pool):
        """
        Initialize conversation memory

        Args:
            db_connection_pool: AsyncPG connection pool
        """
        self.pool = db_connection_pool

    async def save_conversation(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        ai_response: str,
        query_intent: Optional[str] = None,
        sql_query: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save conversation exchange to database

        Args:
            user_id: User identifier
            session_id: Session identifier
            user_message: User's message
            ai_response: AI's response
            query_intent: Detected query intent
            sql_query: Generated SQL query (if any)
            metadata: Additional metadata

        Returns:
            Conversation ID
        """
        conversation_id = str(uuid4())

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO conversation_history (
                    conversation_id,
                    user_id,
                    session_id,
                    user_message,
                    ai_response,
                    query_intent,
                    timestamp
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                UUID(conversation_id),
                UUID(user_id),
                session_id,
                user_message,
                ai_response,
                query_intent,
                datetime.utcnow()
            )

        return conversation_id

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history

        Args:
            user_id: User identifier
            session_id: Optional session filter
            limit: Maximum number of conversations
            offset: Pagination offset

        Returns:
            List of conversation dictionaries
        """
        async with self.pool.acquire() as conn:
            if session_id:
                rows = await conn.fetch(
                    """
                    SELECT
                        conversation_id,
                        user_message,
                        ai_response,
                        query_intent,
                        timestamp
                    FROM conversation_history
                    WHERE user_id = $1 AND session_id = $2
                    ORDER BY timestamp DESC
                    LIMIT $3 OFFSET $4
                    """,
                    UUID(user_id),
                    session_id,
                    limit,
                    offset
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT
                        conversation_id,
                        session_id,
                        user_message,
                        ai_response,
                        query_intent,
                        timestamp
                    FROM conversation_history
                    WHERE user_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2 OFFSET $3
                    """,
                    UUID(user_id),
                    limit,
                    offset
                )

        return [dict(row) for row in rows]

    async def get_recent_context(
        self,
        user_id: str,
        session_id: str,
        limit: int = 5
    ) -> str:
        """
        Get recent conversation context for LLM

        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Number of recent exchanges

        Returns:
            Formatted conversation context
        """
        history = await self.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )

        if not history:
            return ""

        # Format as conversation context
        context_parts = []
        for conv in reversed(history):  # Oldest first
            context_parts.append(f"User: {conv['user_message']}")
            context_parts.append(f"Assistant: {conv['ai_response']}")

        return "\n".join(context_parts)

    async def clear_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> int:
        """
        Clear conversation history

        Args:
            user_id: User identifier
            session_id: Optional session filter (if None, clears all)

        Returns:
            Number of conversations deleted
        """
        async with self.pool.acquire() as conn:
            if session_id:
                result = await conn.execute(
                    """
                    DELETE FROM conversation_history
                    WHERE user_id = $1 AND session_id = $2
                    """,
                    UUID(user_id),
                    session_id
                )
            else:
                result = await conn.execute(
                    """
                    DELETE FROM conversation_history
                    WHERE user_id = $1
                    """,
                    UUID(user_id)
                )

        # Extract count from result
        count = int(result.split()[-1])
        return count

    async def get_session_list(
        self,
        user_id: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get list of conversation sessions

        Args:
            user_id: User identifier
            days_back: Number of days to look back

        Returns:
            List of sessions with metadata
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    session_id,
                    COUNT(*) as message_count,
                    MIN(timestamp) as started_at,
                    MAX(timestamp) as last_message_at,
                    array_agg(DISTINCT query_intent) as intents
                FROM conversation_history
                WHERE user_id = $1 AND timestamp >= $2
                GROUP BY session_id
                ORDER BY last_message_at DESC
                """,
                UUID(user_id),
                cutoff_date
            )

        return [dict(row) for row in rows]

    async def get_conversation_by_id(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific conversation by ID

        Args:
            conversation_id: Conversation identifier
            user_id: User identifier (for security)

        Returns:
            Conversation dict or None
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    conversation_id,
                    user_id,
                    session_id,
                    user_message,
                    ai_response,
                    query_intent,
                    timestamp
                FROM conversation_history
                WHERE conversation_id = $1 AND user_id = $2
                """,
                UUID(conversation_id),
                UUID(user_id)
            )

        return dict(row) if row else None

    async def search_conversations(
        self,
        user_id: str,
        search_term: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search conversations by content

        Args:
            user_id: User identifier
            search_term: Search term
            limit: Maximum results

        Returns:
            List of matching conversations
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    conversation_id,
                    session_id,
                    user_message,
                    ai_response,
                    query_intent,
                    timestamp,
                    ts_rank(
                        to_tsvector('english', user_message || ' ' || ai_response),
                        plainto_tsquery('english', $2)
                    ) as relevance
                FROM conversation_history
                WHERE user_id = $1
                AND (
                    user_message ILIKE $3
                    OR ai_response ILIKE $3
                )
                ORDER BY relevance DESC, timestamp DESC
                LIMIT $4
                """,
                UUID(user_id),
                search_term,
                f"%{search_term}%",
                limit
            )

        return [dict(row) for row in rows]

    async def get_conversation_stats(
        self,
        user_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get conversation statistics

        Args:
            user_id: User identifier
            days_back: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_conversations,
                    COUNT(DISTINCT session_id) as total_sessions,
                    COUNT(DISTINCT DATE(timestamp)) as active_days,
                    array_agg(DISTINCT query_intent) as intent_types
                FROM conversation_history
                WHERE user_id = $1 AND timestamp >= $2
                """,
                UUID(user_id),
                cutoff_date
            )

        stats = dict(row) if row else {}
        stats["period_days"] = days_back
        stats["avg_conversations_per_session"] = (
            stats["total_conversations"] / max(stats["total_sessions"], 1)
            if stats.get("total_sessions") else 0
        )

        return stats


# Alias for backwards compatibility
ConversationMemoryService = ConversationMemory
