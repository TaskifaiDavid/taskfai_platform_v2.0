"""
AI Chat endpoints for natural language querying
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user, get_tenant_db_pool
from app.models.user import UserResponse
from app.models.conversation import (
    ChatQueryRequest,
    ChatQueryResponse,
    ConversationResponse,
    ConversationList
)
from app.services.ai_chat.agent import SQLAgent
from app.services.ai_chat.intent import IntentDetector
from app.services.ai_chat.security import SQLSecurityValidator
from app.services.ai_chat.memory import ConversationMemoryService
import asyncpg


router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.post("/query", response_model=ChatQueryResponse, status_code=status.HTTP_200_OK)
async def query_chat(
    request: ChatQueryRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db_pool: Annotated[asyncpg.Pool, Depends(get_tenant_db_pool)]
):
    """
    Send natural language query to AI chat agent

    - **message**: Natural language query about sales data
    - **session_id**: Optional session ID for conversation continuity

    The agent will:
    1. Detect query intent
    2. Generate secure SQL query
    3. Execute query with RLS filtering
    4. Return results in natural language
    5. Save conversation history
    """
    try:
        # Initialize services
        agent = SQLAgent(db_pool)
        intent_detector = IntentDetector()
        memory_service = ConversationMemoryService(db_pool)

        # Detect intent
        intent = intent_detector.detect_intent(request.message)

        # Generate and execute query via agent
        result = await agent.process_query(
            query=request.message,
            user_id=UUID(current_user.user_id),
            session_id=request.session_id,
            intent=intent
        )

        # Save conversation
        conversation = await memory_service.save_conversation(
            user_id=UUID(current_user.user_id),
            session_id=request.session_id or result.get('session_id'),
            user_message=request.message,
            ai_response=result['response'],
            sql_generated=result.get('sql'),
            intent=intent.dict()
        )

        return ChatQueryResponse(
            response=result['response'],
            sql_query=result.get('sql'),
            data=result.get('data'),
            intent=intent,
            session_id=result.get('session_id'),
            conversation_id=str(conversation.conversation_id)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )


@router.get("/history", response_model=ConversationList, status_code=status.HTTP_200_OK)
async def get_chat_history(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db_pool: Annotated[asyncpg.Pool, Depends(get_tenant_db_pool)],
    session_id: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get conversation history for current user

    - **session_id**: Optional filter by session ID
    - **limit**: Number of conversations to return (max 100)
    - **offset**: Pagination offset

    Returns list of conversations with messages
    """
    try:
        memory_service = ConversationMemoryService(db_pool)

        conversations = await memory_service.get_conversation_history(
            user_id=UUID(current_user.user_id),
            session_id=session_id,
            limit=min(limit, 100),
            offset=offset
        )

        return ConversationList(
            conversations=conversations,
            total=len(conversations),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat_history(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db_pool: Annotated[asyncpg.Pool, Depends(get_tenant_db_pool)],
    session_id: str = None
):
    """
    Clear conversation history

    - **session_id**: Optional - clear specific session. If not provided, clears all user conversations

    This will permanently delete conversation history.
    """
    try:
        memory_service = ConversationMemoryService(db_pool)

        await memory_service.clear_history(
            user_id=UUID(current_user.user_id),
            session_id=session_id
        )

        return None

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear history: {str(e)}"
        )


@router.get("/sessions", response_model=list[dict], status_code=status.HTTP_200_OK)
async def list_chat_sessions(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db_pool: Annotated[asyncpg.Pool, Depends(get_tenant_db_pool)]
):
    """
    List all chat sessions for current user

    Returns list of unique session IDs with metadata (message count, last activity)
    """
    try:
        memory_service = ConversationMemoryService(db_pool)

        sessions = await memory_service.list_sessions(
            user_id=UUID(current_user.user_id)
        )

        return sessions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )
