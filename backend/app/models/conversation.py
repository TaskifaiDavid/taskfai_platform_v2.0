"""Conversation models for AI chat system"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ConversationBase(BaseModel):
    """Base conversation model"""
    user_message: str = Field(min_length=1)
    ai_response: str = Field(min_length=1)
    query_intent: Optional[str] = Field(None, max_length=100)
    session_id: Optional[str] = Field(None, max_length=255)

    @validator('user_message', 'ai_response')
    def validate_messages(cls, v):
        """Validate messages are not empty"""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ConversationCreate(ConversationBase):
    """Model for creating conversation"""
    user_id: str


class ConversationInDB(ConversationBase):
    """Conversation as stored in database"""
    conversation_id: str
    user_id: str
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(ConversationBase):
    """Conversation response"""
    conversation_id: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ConversationList(BaseModel):
    """List of conversations with pagination"""
    conversations: list[ConversationResponse]
    total: int
    page: int = 1
    page_size: int = 50


class ConversationFilter(BaseModel):
    """Filter options for conversations"""
    session_id: Optional[str] = None
    query_intent: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search_term: Optional[str] = None  # Search in messages


class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1)
    timestamp: Optional[datetime] = None


class ChatSession(BaseModel):
    """Chat session with messages"""
    session_id: str
    user_id: str
    messages: list[ChatMessage]
    created_at: datetime
    last_updated: datetime


class QueryIntent(BaseModel):
    """Detected query intent"""
    intent_type: str = Field(
        pattern="^(ONLINE_SALES|OFFLINE_SALES|COMPARISON|TIME_ANALYSIS|PRODUCT_ANALYSIS|RESELLER_ANALYSIS|GENERAL)$"
    )
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict = Field(default_factory=dict)
    suggested_filters: Optional[dict] = None


class ChatQueryRequest(BaseModel):
    """Request for chat query"""
    query: str = Field(min_length=1, max_length=5000)
    session_id: Optional[str] = None

    @validator('query')
    def validate_query(cls, v):
        """Validate query is not empty"""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class ChatQueryResponse(BaseModel):
    """Response for chat query"""
    response: str
    query_intent: Optional[QueryIntent] = None
    conversation_id: str
    session_id: Optional[str] = None
    timestamp: datetime
