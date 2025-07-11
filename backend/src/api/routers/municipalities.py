"""
Municipality management API endpoints.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from postgrest import APIError

from ...models.municipality import (
    Municipality,
    MunicipalityCreate,
    MunicipalityUpdate,
    MunicipalityWithStats,
    MunicipalitySearch,
    MunicipalityList,
    MunicipalityStats
)
from ...utils.supabase_client import get_supabase_client, get_admin_client
from ...config import settings

router = APIRouter(prefix="/municipalities", tags=["municipalities"])


@router.get("/", response_model=MunicipalityList)
async def get_municipalities(
    search: MunicipalitySearch = Depends()
):
    """Get list of municipalities with optional filtering and pagination."""
    client = get_supabase_client()
    
    try:
        # Build query
        query = client.table("municipalities").select(
            "*, bylaw_count:bylaws(count), "
            "active_bylaw_count:bylaws(count).eq(status,active), "
            "source_document_count:source_documents(count)"
        )
        
        # Apply filters
        if search.name:
            query = query.ilike("name", f"%{search.name}%")
        if search.province:
            query = query.eq("province", search.province)
        if search.scraping_enabled is not None:
            query = query.eq("scraping_enabled", search.scraping_enabled)
        
        # Apply sorting
        sort_column = search.sort_by
        if search.sort_order == "desc":
            sort_column = f"{sort_column}.desc()"
        query = query.order(sort_column)
        
        # Get total count
        count_query = client.table("municipalities").select("*", count="exact")
        if search.name:
            count_query = count_query.ilike("name", f"%{search.name}%")
        if search.province:
            count_query = count_query.eq("province", search.province)
        if search.scraping_enabled is not None:
            count_query = count_query.eq("scraping_enabled", search.scraping_enabled)
        
        count_result = count_query.execute()
        total = count_result.count
        
        # Apply pagination
        offset = (search.page - 1) * search.page_size
        query = query.range(offset, offset + search.page_size - 1)
        
        # Execute query
        result = query.execute()
        
        # Transform results
        municipalities = []
        for row in result.data:
            municipality = MunicipalityWithStats(
                **row,
                bylaw_count=row.get("bylaw_count", [{"count": 0}])[0]["count"],
                active_bylaw_count=row.get("active_bylaw_count", [{"count": 0}])[0]["count"],
                source_document_count=row.get("source_document_count", [{"count": 0}])[0]["count"]
            )
            municipalities.append(municipality)
        
        return MunicipalityList(
            municipalities=municipalities,
            total=total,
            page=search.page,
            page_size=search.page_size,
            total_pages=(total + search.page_size - 1) // search.page_size
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/", response_model=Municipality)
async def create_municipality(municipality: MunicipalityCreate):
    """Create a new municipality."""
    client = get_admin_client()
    
    try:
        result = client.table("municipalities").insert(municipality.model_dump()).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create municipality")
        
        return Municipality(**result.data[0])
        
    except APIError as e:
        if "duplicate key value" in str(e):
            raise HTTPException(status_code=409, detail="Municipality already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{municipality_id}", response_model=MunicipalityWithStats)
async def get_municipality(municipality_id: UUID):
    """Get municipality by ID."""
    client = get_supabase_client()
    
    try:
        result = client.table("municipalities").select(
            "*, bylaw_count:bylaws(count), "
            "active_bylaw_count:bylaws(count).eq(status,active), "
            "source_document_count:source_documents(count), "
            "last_scraped_at:source_documents(scraped_at).order(scraped_at.desc).limit(1)"
        ).eq("id", str(municipality_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        row = result.data[0]
        last_scraped = row.get("last_scraped_at")
        last_scraped_at = last_scraped[0]["scraped_at"] if last_scraped and last_scraped[0] else None
        
        return MunicipalityWithStats(
            **row,
            bylaw_count=row.get("bylaw_count", [{"count": 0}])[0]["count"],
            active_bylaw_count=row.get("active_bylaw_count", [{"count": 0}])[0]["count"],
            source_document_count=row.get("source_document_count", [{"count": 0}])[0]["count"],
            last_scraped_at=last_scraped_at
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/{municipality_id}", response_model=Municipality)
async def update_municipality(municipality_id: UUID, municipality: MunicipalityUpdate):
    """Update municipality by ID."""
    client = get_admin_client()
    
    try:
        # Remove None values
        update_data = {k: v for k, v in municipality.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = client.table("municipalities").update(update_data).eq("id", str(municipality_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        return Municipality(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{municipality_id}")
async def delete_municipality(municipality_id: UUID):
    """Delete municipality by ID."""
    client = get_admin_client()
    
    try:
        result = client.table("municipalities").delete().eq("id", str(municipality_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        return {"message": "Municipality deleted successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{municipality_id}/stats", response_model=MunicipalityStats)
async def get_municipality_stats(municipality_id: UUID):
    """Get detailed statistics for a municipality."""
    client = get_supabase_client()
    
    try:
        # Get municipality info
        muni_result = client.table("municipalities").select("*").eq("id", str(municipality_id)).execute()
        
        if not muni_result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        municipality = muni_result.data[0]
        
        # Get bylaw statistics
        bylaw_stats = client.table("bylaws").select(
            "status, category"
        ).eq("municipality_id", str(municipality_id)).execute()
        
        # Get source document statistics
        doc_stats = client.table("source_documents").select(
            "scraped_at"
        ).eq("municipality_id", str(municipality_id)).order("scraped_at.desc").limit(1).execute()
        
        # Process bylaw statistics
        total_bylaws = len(bylaw_stats.data)
        active_bylaws = sum(1 for b in bylaw_stats.data if b["status"] == "active")
        repealed_bylaws = sum(1 for b in bylaw_stats.data if b["status"] == "repealed")
        
        # Category breakdown
        category_counts = {}
        for bylaw in bylaw_stats.data:
            category = bylaw.get("category", "other")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get requirements and full text counts
        version_stats = client.table("bylaw_versions").select(
            "content, extracted_requirements"
        ).in_("bylaw_id", [b["id"] for b in bylaw_stats.data if "id" in b]).execute()
        
        bylaws_with_full_text = sum(1 for v in version_stats.data if v.get("content"))
        bylaws_with_requirements = sum(1 for v in version_stats.data if v.get("extracted_requirements"))
        
        last_scraped_at = None
        if doc_stats.data:
            last_scraped_at = doc_stats.data[0]["scraped_at"]
        
        return MunicipalityStats(
            id=municipality["id"],
            name=municipality["name"],
            province=municipality["province"],
            total_bylaws=total_bylaws,
            active_bylaws=active_bylaws,
            repealed_bylaws=repealed_bylaws,
            bylaw_categories=category_counts,
            total_source_documents=len(doc_stats.data),
            last_scraped_at=last_scraped_at,
            scraping_enabled=municipality.get("scraping_enabled", True),
            bylaws_with_full_text=bylaws_with_full_text,
            bylaws_with_requirements=bylaws_with_requirements
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{municipality_id}/bylaws")
async def get_municipality_bylaws(
    municipality_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get bylaws for a specific municipality."""
    client = get_supabase_client()
    
    try:
        # Build query
        query = client.table("bylaws").select("*").eq("municipality_id", str(municipality_id))
        
        # Apply filters
        if category:
            query = query.eq("category", category)
        if status:
            query = query.eq("status", status)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.range(offset, offset + page_size - 1)
        
        # Execute query
        result = query.execute()
        
        return {
            "bylaws": result.data,
            "total": len(result.data),
            "page": page,
            "page_size": page_size
        }
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{municipality_id}/enable-scraping")
async def enable_scraping(municipality_id: UUID):
    """Enable scraping for a municipality."""
    client = get_admin_client()
    
    try:
        result = client.table("municipalities").update(
            {"scraping_enabled": True}
        ).eq("id", str(municipality_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        return {"message": "Scraping enabled successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{municipality_id}/disable-scraping")
async def disable_scraping(municipality_id: UUID):
    """Disable scraping for a municipality."""
    client = get_admin_client()
    
    try:
        result = client.table("municipalities").update(
            {"scraping_enabled": False}
        ).eq("id", str(municipality_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        return {"message": "Scraping disabled successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")