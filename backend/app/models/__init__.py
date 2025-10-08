"""Pydantic models for request/response validation"""

from .user import UserCreate, UserLogin, UserResponse, Token, TokenData
from .tenant import TenantBase, TenantCreate, TenantUpdate, TenantResponse, TenantInDB
from .vendor_config import VendorConfigData, VendorConfigCreate, VendorConfigUpdate, VendorConfig, VendorConfigList
from .sales import (
    OfflineSaleBase, OfflineSaleCreate, OfflineSaleResponse, OfflineSaleInDB,
    OnlineSaleBase, OnlineSaleCreate, OnlineSaleResponse, OnlineSaleInDB,
    SalesFilter, SalesSummary
)
from .product import ProductBase, ProductCreate, ProductUpdate, ProductResponse, ProductList, ProductSearch
from .reseller import ResellerBase, ResellerCreate, ResellerUpdate, ResellerResponse, ResellerList, ResellerWithStats
from .upload import (
    UploadBatchBase, UploadBatchCreate, UploadBatchUpdate, UploadBatchResponse, UploadBatchList,
    ErrorReportBase, ErrorReportCreate, ErrorReportResponse, ErrorReportList
)
from .conversation import (
    ConversationBase, ConversationCreate, ConversationResponse, ConversationList,
    ChatMessage, ChatSession, ChatQueryRequest, ChatQueryResponse, QueryIntent
)
from .dashboard import (
    DashboardBase, DashboardCreate, DashboardUpdate, DashboardResponse, DashboardList,
    DashboardEmbedRequest, DashboardEmbedResponse
)
from .email import (
    EmailLogBase, EmailLogCreate, EmailLogUpdate, EmailLogResponse, EmailLogList,
    EmailSendRequest, EmailSendResponse, EmailTemplate, EmailStats
)

__all__ = [
    # User models
    "UserCreate", "UserLogin", "UserResponse", "Token", "TokenData",
    # Tenant models
    "TenantBase", "TenantCreate", "TenantUpdate", "TenantResponse", "TenantInDB",
    # Vendor config models
    "VendorConfigData", "VendorConfigCreate", "VendorConfigUpdate", "VendorConfig", "VendorConfigList",
    # Sales models
    "OfflineSaleBase", "OfflineSaleCreate", "OfflineSaleResponse", "OfflineSaleInDB",
    "OnlineSaleBase", "OnlineSaleCreate", "OnlineSaleResponse", "OnlineSaleInDB",
    "SalesFilter", "SalesSummary",
    # Product models
    "ProductBase", "ProductCreate", "ProductUpdate", "ProductResponse", "ProductList", "ProductSearch",
    # Reseller models
    "ResellerBase", "ResellerCreate", "ResellerUpdate", "ResellerResponse", "ResellerList", "ResellerWithStats",
    # Upload models
    "UploadBatchBase", "UploadBatchCreate", "UploadBatchUpdate", "UploadBatchResponse", "UploadBatchList",
    "ErrorReportBase", "ErrorReportCreate", "ErrorReportResponse", "ErrorReportList",
    # Conversation models
    "ConversationBase", "ConversationCreate", "ConversationResponse", "ConversationList",
    "ChatMessage", "ChatSession", "ChatQueryRequest", "ChatQueryResponse", "QueryIntent",
    # Dashboard models
    "DashboardBase", "DashboardCreate", "DashboardUpdate", "DashboardResponse", "DashboardList",
    "DashboardEmbedRequest", "DashboardEmbedResponse",
    # Email models
    "EmailLogBase", "EmailLogCreate", "EmailLogUpdate", "EmailLogResponse", "EmailLogList",
    "EmailSendRequest", "EmailSendResponse", "EmailTemplate", "EmailStats",
]
