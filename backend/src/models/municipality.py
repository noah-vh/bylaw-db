"""
Municipality model definitions.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class MunicipalityBase(BaseModel):
    """Base municipality model."""
    name: str = Field(..., description="Municipality name")
    province: str = Field(..., description="Province or state")
    website_url: Optional[str] = Field(None, description="Official website URL")
    scraping_enabled: bool = Field(True, description="Whether scraping is enabled")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MunicipalityCreate(MunicipalityBase):
    """Municipality creation model."""
    pass


class MunicipalityUpdate(BaseModel):
    """Municipality update model."""
    name: Optional[str] = Field(None, description="Municipality name")
    province: Optional[str] = Field(None, description="Province or state")
    website_url: Optional[str] = Field(None, description="Official website URL")
    scraping_enabled: Optional[bool] = Field(None, description="Whether scraping is enabled")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class Municipality(MunicipalityBase):
    """Full municipality model."""
    id: UUID = Field(..., description="Municipality ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class MunicipalityWithStats(Municipality):
    """Municipality with statistics."""
    bylaw_count: int = Field(0, description="Number of bylaws")
    active_bylaw_count: int = Field(0, description="Number of active bylaws")
    last_scraped_at: Optional[datetime] = Field(None, description="Last scraping timestamp")
    source_document_count: int = Field(0, description="Number of source documents")


class MunicipalitySearch(BaseModel):
    """Municipality search parameters."""
    name: Optional[str] = Field(None, description="Search by name (partial match)")
    province: Optional[str] = Field(None, description="Filter by province")
    scraping_enabled: Optional[bool] = Field(None, description="Filter by scraping status")
    has_bylaws: Optional[bool] = Field(None, description="Filter by presence of bylaws")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    
    # Sorting
    sort_by: str = Field("name", description="Sort field")
    sort_order: str = Field("asc", regex="^(asc|desc)$", description="Sort order")
    
    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = ["name", "province", "created_at", "updated_at", "bylaw_count"]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {allowed_fields}")
        return v


class MunicipalityList(BaseModel):
    """Paginated municipality list."""
    municipalities: List[MunicipalityWithStats] = Field(..., description="List of municipalities")
    total: int = Field(..., description="Total number of municipalities")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    
    @validator("total_pages", pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        if "total" in values and "page_size" in values:
            import math
            return math.ceil(values["total"] / values["page_size"])
        return v


class MunicipalityStats(BaseModel):
    """Municipality statistics."""
    id: UUID = Field(..., description="Municipality ID")
    name: str = Field(..., description="Municipality name")
    province: str = Field(..., description="Province")
    
    # Bylaw statistics
    total_bylaws: int = Field(0, description="Total number of bylaws")
    active_bylaws: int = Field(0, description="Number of active bylaws")
    repealed_bylaws: int = Field(0, description="Number of repealed bylaws")
    
    # Category breakdown
    bylaw_categories: Dict[str, int] = Field(default_factory=dict, description="Bylaws by category")
    
    # Scraping statistics
    total_source_documents: int = Field(0, description="Total source documents")
    last_scraped_at: Optional[datetime] = Field(None, description="Last scraping timestamp")
    scraping_enabled: bool = Field(True, description="Whether scraping is enabled")
    
    # Data quality
    bylaws_with_full_text: int = Field(0, description="Bylaws with full text")
    bylaws_with_requirements: int = Field(0, description="Bylaws with extracted requirements")
    data_completeness_score: float = Field(0.0, description="Data completeness score (0-1)")
    
    @validator("data_completeness_score", pre=True, always=True)
    def calculate_completeness(cls, v, values):
        if "total_bylaws" in values and values["total_bylaws"] > 0:
            total = values["total_bylaws"]
            with_text = values.get("bylaws_with_full_text", 0)
            with_requirements = values.get("bylaws_with_requirements", 0)
            
            # Simple completeness calculation
            text_score = with_text / total * 0.6
            requirements_score = with_requirements / total * 0.4
            return min(1.0, text_score + requirements_score)
        return 0.0