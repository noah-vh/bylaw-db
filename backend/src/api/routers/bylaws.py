"""
Bylaws API endpoints with version tracking.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from postgrest import APIError

from ...models.bylaw import (
    Bylaw,
    BylawCreate,
    BylawUpdate,
    BylawWithVersions,
    BylawVersion,
    BylawVersionCreate,
    BylawVersionUpdate,
    BylawSearch,
    BylawList,
    ADURequirements,
    ADURequirementsCreate
)
from ...utils.supabase_client import get_supabase_client, get_admin_client
from ...config import settings

router = APIRouter(prefix="/bylaws", tags=["bylaws"])


@router.get("/", response_model=BylawList)
async def get_bylaws(search: BylawSearch = Depends()):
    """Get list of bylaws with optional filtering and pagination."""
    client = get_supabase_client()
    
    try:
        # Build query
        query = client.table("bylaws").select("*, municipality:municipalities(name, province)")
        
        # Apply filters
        if search.query:
            query = query.or_(
                f"title.ilike.%{search.query}%,"
                f"bylaw_number.ilike.%{search.query}%,"
                f"full_text.ilike.%{search.query}%"
            )
        
        if search.municipality_id:
            query = query.eq("municipality_id", str(search.municipality_id))
        
        if search.category:
            query = query.eq("category", search.category)
        
        if search.status:
            query = query.eq("status", search.status)
        
        if search.effective_date_from:
            query = query.gte("effective_date", search.effective_date_from.isoformat())
        
        if search.effective_date_to:
            query = query.lte("effective_date", search.effective_date_to.isoformat())
        
        if search.has_full_text is not None:
            if search.has_full_text:
                query = query.not_.is_("full_text", "null")
            else:
                query = query.is_("full_text", "null")
        
        # Apply sorting
        sort_column = search.sort_by
        if search.sort_order == "desc":
            sort_column = f"{sort_column}.desc()"
        query = query.order(sort_column)
        
        # Get total count
        count_query = client.table("bylaws").select("*", count="exact")
        if search.municipality_id:
            count_query = count_query.eq("municipality_id", str(search.municipality_id))
        if search.category:
            count_query = count_query.eq("category", search.category)
        if search.status:
            count_query = count_query.eq("status", search.status)
        
        count_result = count_query.execute()
        total = count_result.count
        
        # Apply pagination
        offset = (search.page - 1) * search.page_size
        query = query.range(offset, offset + search.page_size - 1)
        
        # Execute query
        result = query.execute()
        
        # Transform results
        bylaws = [Bylaw(**row) for row in result.data]
        
        return BylawList(
            bylaws=bylaws,
            total=total,
            page=search.page,
            page_size=search.page_size,
            total_pages=(total + search.page_size - 1) // search.page_size
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/", response_model=Bylaw)
async def create_bylaw(bylaw: BylawCreate):
    """Create a new bylaw."""
    client = get_admin_client()
    
    try:
        result = client.table("bylaws").insert(bylaw.dict()).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create bylaw")
        
        return Bylaw(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{bylaw_id}", response_model=BylawWithVersions)
async def get_bylaw(bylaw_id: UUID):
    """Get bylaw by ID with version information."""
    client = get_supabase_client()
    
    try:
        # Get bylaw
        bylaw_result = client.table("bylaws").select(
            "*, municipality:municipalities(name, province)"
        ).eq("id", str(bylaw_id)).execute()
        
        if not bylaw_result.data:
            raise HTTPException(status_code=404, detail="Bylaw not found")
        
        bylaw_data = bylaw_result.data[0]
        
        # Get versions
        versions_result = client.table("bylaw_versions").select("*").eq(
            "bylaw_id", str(bylaw_id)
        ).order("version_number.desc").execute()
        
        # Find current version
        current_version = None
        for version in versions_result.data:
            if version.get("is_current"):
                current_version = BylawVersion(**version)
                break
        
        return BylawWithVersions(
            **bylaw_data,
            versions=[BylawVersion(**v) for v in versions_result.data],
            current_version=current_version,
            version_count=len(versions_result.data)
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/{bylaw_id}", response_model=Bylaw)
async def update_bylaw(bylaw_id: UUID, bylaw: BylawUpdate):
    """Update bylaw by ID."""
    client = get_admin_client()
    
    try:
        # Remove None values
        update_data = {k: v for k, v in bylaw.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = client.table("bylaws").update(update_data).eq("id", str(bylaw_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Bylaw not found")
        
        return Bylaw(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{bylaw_id}")
async def delete_bylaw(bylaw_id: UUID):
    """Delete bylaw by ID."""
    client = get_admin_client()
    
    try:
        result = client.table("bylaws").delete().eq("id", str(bylaw_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Bylaw not found")
        
        return {"message": "Bylaw deleted successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Bylaw Versions endpoints
@router.get("/{bylaw_id}/versions", response_model=List[BylawVersion])
async def get_bylaw_versions(bylaw_id: UUID):
    """Get all versions of a bylaw."""
    client = get_supabase_client()
    
    try:
        result = client.table("bylaw_versions").select("*").eq(
            "bylaw_id", str(bylaw_id)
        ).order("version_number.desc").execute()
        
        return [BylawVersion(**v) for v in result.data]
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{bylaw_id}/versions", response_model=BylawVersion)
async def create_bylaw_version(bylaw_id: UUID, version: BylawVersionCreate):
    """Create a new version of a bylaw."""
    client = get_admin_client()
    
    try:
        # Verify bylaw exists
        bylaw_result = client.table("bylaws").select("id").eq("id", str(bylaw_id)).execute()
        if not bylaw_result.data:
            raise HTTPException(status_code=404, detail="Bylaw not found")
        
        # Get next version number
        versions_result = client.table("bylaw_versions").select("version_number").eq(
            "bylaw_id", str(bylaw_id)
        ).order("version_number.desc").limit(1).execute()
        
        next_version = 1
        if versions_result.data:
            next_version = versions_result.data[0]["version_number"] + 1
        
        # Create version data
        version_data = version.dict()
        version_data["bylaw_id"] = str(bylaw_id)
        version_data["version_number"] = next_version
        
        # If this is marked as current, unmark other versions
        if version_data.get("is_current"):
            client.table("bylaw_versions").update({"is_current": False}).eq(
                "bylaw_id", str(bylaw_id)
            ).execute()
        
        result = client.table("bylaw_versions").insert(version_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create version")
        
        return BylawVersion(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{bylaw_id}/versions/{version_id}", response_model=BylawVersion)
async def get_bylaw_version(bylaw_id: UUID, version_id: UUID):
    """Get a specific version of a bylaw."""
    client = get_supabase_client()
    
    try:
        result = client.table("bylaw_versions").select("*").eq(
            "id", str(version_id)
        ).eq("bylaw_id", str(bylaw_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return BylawVersion(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/{bylaw_id}/versions/{version_id}", response_model=BylawVersion)
async def update_bylaw_version(bylaw_id: UUID, version_id: UUID, version: BylawVersionUpdate):
    """Update a specific version of a bylaw."""
    client = get_admin_client()
    
    try:
        # Remove None values
        update_data = {k: v for k, v in version.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = client.table("bylaw_versions").update(update_data).eq(
            "id", str(version_id)
        ).eq("bylaw_id", str(bylaw_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return BylawVersion(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{bylaw_id}/versions/{version_id}/set-current")
async def set_current_version(bylaw_id: UUID, version_id: UUID):
    """Set a specific version as the current version."""
    client = get_admin_client()
    
    try:
        # Verify version exists
        version_result = client.table("bylaw_versions").select("id").eq(
            "id", str(version_id)
        ).eq("bylaw_id", str(bylaw_id)).execute()
        
        if not version_result.data:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Unmark all other versions as current
        client.table("bylaw_versions").update({"is_current": False}).eq(
            "bylaw_id", str(bylaw_id)
        ).execute()
        
        # Mark this version as current
        result = client.table("bylaw_versions").update({"is_current": True}).eq(
            "id", str(version_id)
        ).execute()
        
        return {"message": "Current version updated successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ADU Requirements endpoints
@router.get("/{bylaw_id}/adu-requirements", response_model=List[ADURequirements])
async def get_adu_requirements(bylaw_id: UUID):
    """Get ADU requirements for a bylaw."""
    client = get_supabase_client()
    
    try:
        # Get current version
        version_result = client.table("bylaw_versions").select("id").eq(
            "bylaw_id", str(bylaw_id)
        ).eq("is_current", True).execute()
        
        if not version_result.data:
            return []
        
        version_id = version_result.data[0]["id"]
        
        # Get ADU requirements
        result = client.table("adu_requirements").select("*").eq(
            "bylaw_version_id", version_id
        ).execute()
        
        return [ADURequirements(**req) for req in result.data]
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{bylaw_id}/adu-requirements", response_model=ADURequirements)
async def create_adu_requirements(bylaw_id: UUID, requirements: ADURequirementsCreate):
    """Create ADU requirements for a bylaw version."""
    client = get_admin_client()
    
    try:
        # Verify bylaw version exists
        version_result = client.table("bylaw_versions").select("id").eq(
            "id", str(requirements.bylaw_version_id)
        ).eq("bylaw_id", str(bylaw_id)).execute()
        
        if not version_result.data:
            raise HTTPException(status_code=404, detail="Bylaw version not found")
        
        result = client.table("adu_requirements").insert(requirements.dict()).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create ADU requirements")
        
        return ADURequirements(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/search", response_model=BylawList)
async def search_bylaws(
    q: str = Query(..., description="Search query"),
    municipality_id: Optional[UUID] = Query(None, description="Municipality filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size")
):
    """Search bylaws by text query."""
    search_params = BylawSearch(
        query=q,
        municipality_id=municipality_id,
        category=category,
        page=page,
        page_size=page_size
    )
    
    return await get_bylaws(search_params)