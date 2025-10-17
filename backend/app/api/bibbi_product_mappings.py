"""
BIBBI Product Mapping API

Admin interface for managing product code → EAN mappings.

Endpoints:
- POST /api/bibbi/product-mappings - Create mapping
- GET /api/bibbi/product-mappings/{mapping_id} - Get mapping
- GET /api/bibbi/product-mappings - List mappings by reseller
- PUT /api/bibbi/product-mappings/{mapping_id} - Update mapping
- DELETE /api/bibbi/product-mappings/{mapping_id} - Delete mapping
- POST /api/bibbi/product-mappings/bulk - Bulk create mappings
- GET /api/bibbi/product-mappings/unmapped - Find unmapped products
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.bibbi import (
    get_bibbi_tenant_context,
    get_bibbi_supabase_client,
    BibbιTenant,
    BibbιDB
)
from app.services.bibbi import BibbιProductMappingService, get_product_mapping_service


router = APIRouter(prefix="/bibbi/product-mappings", tags=["BIBBI Product Mappings"])


# ========================================
# Request/Response Models
# ========================================

class ProductMappingCreate(BaseModel):
    """Request model for creating product mapping"""
    reseller_id: str = Field(..., description="Reseller UUID")
    product_code: str = Field(..., description="Reseller's product code or name")
    ean: str = Field(..., min_length=13, max_length=13, description="EAN code (13 digits)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata (product_name, category, etc.)")


class ProductMappingBulkCreate(BaseModel):
    """Request model for bulk creating product mappings"""
    reseller_id: str = Field(..., description="Reseller UUID")
    mappings: List[Dict[str, Any]] = Field(..., description="List of mappings (product_code, ean, metadata)")


class ProductMappingUpdate(BaseModel):
    """Request model for updating product mapping"""
    product_code: Optional[str] = Field(None, description="New product code")
    ean: Optional[str] = Field(None, min_length=13, max_length=13, description="New EAN code")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata")
    is_active: Optional[bool] = Field(None, description="Active status")


class ProductMappingResponse(BaseModel):
    """Response model for product mapping"""
    mapping_id: str
    reseller_id: str
    product_code: str
    ean: str
    metadata: Dict[str, Any]
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None


class ProductMappingListResponse(BaseModel):
    """Response model for list of mappings"""
    mappings: List[ProductMappingResponse]
    total_count: int


class UnmappedProductsRequest(BaseModel):
    """Request model for finding unmapped products"""
    reseller_id: str = Field(..., description="Reseller UUID")
    product_codes: List[str] = Field(..., description="List of product codes to check")


class UnmappedProductsResponse(BaseModel):
    """Response model for unmapped products"""
    reseller_id: str
    unmapped_products: List[str]
    unmapped_count: int


# ========================================
# API Endpoints
# ========================================

@router.post("", response_model=ProductMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_product_mapping(
    mapping_data: ProductMappingCreate,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Create new product mapping

    Creates a mapping between reseller product code and EAN.

    **Requirements**:
    - Valid EAN format (13 digits)
    - Unique product_code per reseller
    - Tenant must be 'bibbi'
    """
    try:
        mapping_service = get_product_mapping_service(bibbi_db)

        mapping_id = mapping_service.create_mapping(
            reseller_id=mapping_data.reseller_id,
            product_code=mapping_data.product_code,
            ean=mapping_data.ean,
            metadata=mapping_data.metadata
        )

        # Fetch created mapping
        mappings = mapping_service.get_reseller_mappings(mapping_data.reseller_id, active_only=False)
        created_mapping = next((m for m in mappings if m["mapping_id"] == mapping_id), None)

        if not created_mapping:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Mapping created but could not be retrieved"
            )

        return ProductMappingResponse(
            mapping_id=created_mapping["mapping_id"],
            reseller_id=created_mapping["reseller_id"],
            product_code=created_mapping["reseller_product_code"],
            ean=created_mapping["product_id"],
            metadata=created_mapping.get("mapping_metadata", {}),
            is_active=created_mapping["is_active"],
            created_at=created_mapping["created_at"],
            updated_at=created_mapping.get("updated_at")
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create mapping: {str(e)}"
        )


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_create_product_mappings(
    bulk_data: ProductMappingBulkCreate,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Bulk create product mappings

    Creates multiple mappings in one request.

    **Returns**:
    - success_count: Number of successfully created mappings
    - created_mapping_ids: List of mapping_ids
    - errors: List of errors for failed mappings
    """
    try:
        mapping_service = get_product_mapping_service(bibbi_db)

        results = mapping_service.bulk_create_mappings(
            reseller_id=bulk_data.reseller_id,
            mappings=bulk_data.mappings
        )

        success_count = len(results)
        total_count = len(bulk_data.mappings)

        return {
            "success": True,
            "success_count": success_count,
            "total_count": total_count,
            "created_mapping_ids": list(results.values())
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create mappings: {str(e)}"
        )


@router.get("", response_model=ProductMappingListResponse)
async def list_product_mappings(
    reseller_id: str,
    active_only: bool = True,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    List product mappings for a reseller

    **Query Parameters**:
    - reseller_id: Reseller UUID (required)
    - active_only: Only return active mappings (default: true)
    """
    try:
        mapping_service = get_product_mapping_service(bibbi_db)

        mappings = mapping_service.get_reseller_mappings(
            reseller_id=reseller_id,
            active_only=active_only
        )

        mapping_responses = [
            ProductMappingResponse(
                mapping_id=m["mapping_id"],
                reseller_id=m["reseller_id"],
                product_code=m["reseller_product_code"],
                ean=m["product_id"],
                metadata=m.get("mapping_metadata", {}),
                is_active=m["is_active"],
                created_at=m["created_at"],
                updated_at=m.get("updated_at")
            )
            for m in mappings
        ]

        return ProductMappingListResponse(
            mappings=mapping_responses,
            total_count=len(mapping_responses)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list mappings: {str(e)}"
        )


@router.get("/{mapping_id}", response_model=ProductMappingResponse)
async def get_product_mapping(
    mapping_id: str,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Get product mapping by ID
    """
    try:
        result = bibbi_db.table("product_reseller_mappings")\
            .select("*")\
            .eq("mapping_id", mapping_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping not found: {mapping_id}"
            )

        mapping = result.data[0]

        return ProductMappingResponse(
            mapping_id=mapping["mapping_id"],
            reseller_id=mapping["reseller_id"],
            product_code=mapping["reseller_product_code"],
            ean=mapping["product_id"],
            metadata=mapping.get("mapping_metadata", {}),
            is_active=mapping["is_active"],
            created_at=mapping["created_at"],
            updated_at=mapping.get("updated_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mapping: {str(e)}"
        )


@router.put("/{mapping_id}", response_model=ProductMappingResponse)
async def update_product_mapping(
    mapping_id: str,
    update_data: ProductMappingUpdate,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Update product mapping

    **Updatable Fields**:
    - product_code
    - ean
    - metadata
    - is_active
    """
    try:
        mapping_service = get_product_mapping_service(bibbi_db)

        # Build update dict
        updates = {}
        if update_data.product_code is not None:
            updates["reseller_product_code"] = update_data.product_code
        if update_data.ean is not None:
            updates["product_id"] = update_data.ean
        if update_data.metadata is not None:
            updates["mapping_metadata"] = update_data.metadata
        if update_data.is_active is not None:
            updates["is_active"] = update_data.is_active

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        mapping_service.update_mapping(mapping_id, updates)

        # Fetch updated mapping
        result = bibbi_db.table("product_reseller_mappings")\
            .select("*")\
            .eq("mapping_id", mapping_id)\
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mapping not found: {mapping_id}"
            )

        mapping = result.data[0]

        return ProductMappingResponse(
            mapping_id=mapping["mapping_id"],
            reseller_id=mapping["reseller_id"],
            product_code=mapping["reseller_product_code"],
            ean=mapping["product_id"],
            metadata=mapping.get("mapping_metadata", {}),
            is_active=mapping["is_active"],
            created_at=mapping["created_at"],
            updated_at=mapping.get("updated_at")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update mapping: {str(e)}"
        )


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_mapping(
    mapping_id: str,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Delete product mapping

    Permanently removes the mapping.
    """
    try:
        mapping_service = get_product_mapping_service(bibbi_db)
        mapping_service.delete_mapping(mapping_id)

        return None

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete mapping: {str(e)}"
        )


@router.post("/unmapped", response_model=UnmappedProductsResponse)
async def find_unmapped_products(
    request_data: UnmappedProductsRequest,
    bibbi_tenant: BibbιTenant = Depends(get_bibbi_tenant_context),
    bibbi_db: BibbιDB = Depends(get_bibbi_supabase_client)
):
    """
    Find unmapped products

    Identifies product codes that don't have mappings yet.

    Useful for:
    - Identifying missing mappings before upload
    - Validating Galilu data files
    """
    try:
        mapping_service = get_product_mapping_service(bibbi_db)

        unmapped = mapping_service.get_unmapped_products(
            reseller_id=request_data.reseller_id,
            product_codes=request_data.product_codes
        )

        return UnmappedProductsResponse(
            reseller_id=request_data.reseller_id,
            unmapped_products=unmapped,
            unmapped_count=len(unmapped)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find unmapped products: {str(e)}"
        )
