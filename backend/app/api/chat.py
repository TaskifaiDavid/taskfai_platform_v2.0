"""
AI Chat endpoints for natural language querying
"""

from typing import Annotated
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.dependencies import get_current_user, get_tenant_context, get_supabase_client, CurrentTenant
from app.core.config import settings
from app.models.user import UserResponse
from app.models.conversation import (
    ChatQueryRequest,
    ChatQueryResponse,
    ConversationResponse,
    ConversationList
)
from app.services.ai_chat.agent import SQLDatabaseAgent
from app.services.ai_chat.intent import IntentDetector
from app.services.ai_chat.security import SQLSecurityValidator
from app.services.ai_chat.memory import ConversationMemoryService


router = APIRouter(prefix="/chat", tags=["AI Chat"])


# Supabase project ID for MCP operations
SUPABASE_PROJECT_ID = "afualzsndhnbsuruwese"


async def execute_sql_via_mcp(project_id: str, query: str, supabase_client) -> list:
    """
    Execute SQL query via Supabase REST API (using exec_sql RPC function)

    Args:
        project_id: Supabase project ID (unused, kept for compatibility)
        query: SQL SELECT query to execute
        supabase_client: Tenant-routed Supabase client from dependencies

    Returns:
        Query results as list of dictionaries
    """
    try:
        # Execute query via the exec_sql RPC function using tenant-routed client
        result = supabase_client.rpc('exec_sql', {'query': query}).execute()

        # Return the data (already in list format from jsonb_agg)
        return result.data if result.data else []
    except Exception as e:
        raise ValueError(f"SQL execution failed: {str(e)}")


@router.post("/query", status_code=status.HTTP_200_OK)
async def query_chat(
    request: ChatQueryRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    tenant_context: CurrentTenant,
    supabase: Annotated[Client, Depends(get_supabase_client)]
):
    """
    Send natural language query to AI chat agent

    - **message**: Natural language query about sales data
    - **session_id**: Optional session ID for conversation continuity

    The agent will:
    1. Detect query intent
    2. Generate secure SQL query using OpenAI
    3. Execute query via tenant-routed Supabase client
    4. Return results in natural language
    """
    try:
        # Initialize hybrid SQL agent with tenant context
        agent = SQLDatabaseAgent(
            project_id=SUPABASE_PROJECT_ID,
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model,
            tenant_subdomain=tenant_context.subdomain
        )

        # Initialize conversation memory for context
        from app.services.ai_chat.memory import ConversationMemory
        memory = ConversationMemory(project_id=SUPABASE_PROJECT_ID)

        # Detect intent
        intent_detector = IntentDetector()
        intent = intent_detector.detect_intent(request.query)

        # Create closure to pass supabase client to execute function
        async def execute_sql_with_client(project_id: str, query: str) -> list:
            return await execute_sql_via_mcp(project_id, query, supabase)

        # Process query with agent (uses tenant-routed Supabase client + conversation context)
        result = await agent.process_query(
            query=request.query,
            user_id=str(current_user["user_id"]),
            mcp_execute_sql_fn=execute_sql_with_client,
            session_id=request.session_id,
            intent=intent,
            conversation_memory=memory
        )

        # Return response matching frontend expectations
        return {
            "response": result['response'],
            "sql_generated": result.get('sql'),
            "session_id": result.get('session_id')
        }

    except ValueError as e:
        # Configuration or validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # General errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/history")
async def get_chat_history(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session_id: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get conversation history for current user

    - **session_id**: Optional filter by session ID
    - **limit**: Number of conversations to return (max 100)
    - **offset**: Pagination offset

    Returns conversation with messages
    """
    # Conversation history intentionally disabled - not implemented in current architecture
    return {
        "conversation_id": session_id or "temp",
        "session_id": session_id or "temp",
        "messages": [],
        "created_at": datetime.utcnow().isoformat()
    }


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat_history(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    session_id: str = None
):
    """
    Clear conversation history

    - **session_id**: Optional - clear specific session. If not provided, clears all user conversations

    This will permanently delete conversation history.
    """
    # Conversation history intentionally disabled - not implemented in current architecture
    return None


@router.get("/sessions", response_model=list[dict], status_code=status.HTTP_200_OK)
async def list_chat_sessions(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    List all chat sessions for current user

    Returns list of unique session IDs with metadata (message count, last activity)
    """
    # Conversation history intentionally disabled - not implemented in current architecture
    return []
