"""
Conversation memory service for persistent chat history
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from supabase import Client


class ConversationMemory:
    """
    Database-backed conversation memory for chat persistence

    Stores conversation history in database for:
    - Session continuity across requests
    - Conversation history retrieval
    - Analytics and debugging
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize conversation memory

        Args:
            supabase_client: Tenant-routed Supabase client
        """
        self.supabase = supabase_client

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

        self.supabase.table('conversation_history').insert({
            'conversation_id': conversation_id,
            'user_id': user_id,
            'session_id': session_id,
            'user_message': user_message,
            'ai_response': ai_response,
            'query_intent': query_intent,
            'timestamp': datetime.utcnow().isoformat()
        }).execute()

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
        query = self.supabase.table('conversation_history').select(
            'conversation_id, session_id, user_message, ai_response, query_intent, timestamp'
        ).eq('user_id', user_id)

        if session_id:
            query = query.eq('session_id', session_id)

        result = query.order('timestamp', desc=True).limit(limit).offset(offset).execute()

        return result.data if result.data else []

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
        query = self.supabase.table('conversation_history').delete().eq('user_id', user_id)

        if session_id:
            query = query.eq('session_id', session_id)

        result = query.execute()

        # Return count of deleted records
        return len(result.data) if result.data else 0

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

        Note: Simplified version - returns basic session list without aggregations
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        result = self.supabase.table('conversation_history').select(
            'session_id, timestamp'
        ).eq('user_id', user_id).gte('timestamp', cutoff_date).order('timestamp', desc=True).execute()

        # Group by session_id manually
        sessions = {}
        for row in (result.data or []):
            sid = row['session_id']
            if sid not in sessions:
                sessions[sid] = {
                    'session_id': sid,
                    'message_count': 0,
                    'last_message_at': row['timestamp']
                }
            sessions[sid]['message_count'] += 1

        return list(sessions.values())

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
        result = self.supabase.table('conversation_history').select(
            'conversation_id, user_id, session_id, user_message, ai_response, query_intent, timestamp'
        ).eq('conversation_id', conversation_id).eq('user_id', user_id).limit(1).execute()

        return result.data[0] if result.data else None

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

        Note: Simplified version - uses basic ILIKE matching without full-text search ranking
        """
        result = self.supabase.table('conversation_history').select(
            'conversation_id, session_id, user_message, ai_response, query_intent, timestamp'
        ).eq('user_id', user_id).or_(
            f"user_message.ilike.%{search_term}%,ai_response.ilike.%{search_term}%"
        ).order('timestamp', desc=True).limit(limit).execute()

        return result.data if result.data else []

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

        Note: Simplified version - computes basic stats from retrieved data
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

        result = self.supabase.table('conversation_history').select(
            'session_id, timestamp'
        ).eq('user_id', user_id).gte('timestamp', cutoff_date).execute()

        data = result.data if result.data else []

        # Compute stats manually
        total_conversations = len(data)
        unique_sessions = len(set(row['session_id'] for row in data))

        stats = {
            "total_conversations": total_conversations,
            "total_sessions": unique_sessions,
            "period_days": days_back,
            "avg_conversations_per_session": (
                total_conversations / max(unique_sessions, 1) if unique_sessions else 0
            )
        }

        return stats


# Alias for backwards compatibility
ConversationMemoryService = ConversationMemory
