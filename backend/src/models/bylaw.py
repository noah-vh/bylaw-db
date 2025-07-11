"""
Bylaw and BylawVersion model definitions.
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, validator


class BylawBase(BaseModel):
    """Base bylaw model."""
    bylaw_number: Optional[str] = Field(None, description="Bylaw number")
    title: str = Field(..., description="Bylaw title")
    category: Optional[str] = Field(None, description="Bylaw category")
    status: str = Field("active", description="Bylaw status")
    
    effective_date: Optional[date] = Field(None, description="Effective date")
    amendment_date: Optional[date] = Field(None, description="Amendment date")
    repeal_date: Optional[date] = Field(None, description="Repeal date")
    
    full_text: Optional[str] = Field(None, description="Full text of the bylaw")
    summary: Optional[str] = Field(None, description="Summary of the bylaw")
    
    @validator("status")
    def validate_status(cls, v):
        allowed_statuses = ["active", "repealed", "amended", "proposed", "draft"]
        if v not in allowed_statuses:
            raise ValueError(f"status must be one of: {allowed_statuses}")
        return v
    
    @validator("category")
    def validate_category(cls, v):
        if v is None:
            return v
        allowed_categories = [
            "zoning", "adu", "building_code", "parking", "noise", "animal_control",
            "business_licensing", "traffic", "development", "environmental", "other"
        ]
        if v not in allowed_categories:
            raise ValueError(f"category must be one of: {allowed_categories}")
        return v


class BylawCreate(BylawBase):
    """Bylaw creation model."""
    municipality_id: UUID = Field(..., description="Municipality ID")
    source_document_id: Optional[UUID] = Field(None, description="Source document ID")
    parent_bylaw_id: Optional[UUID] = Field(None, description="Parent bylaw ID for amendments")


class BylawUpdate(BaseModel):
    """Bylaw update model."""
    bylaw_number: Optional[str] = Field(None, description="Bylaw number")
    title: Optional[str] = Field(None, description="Bylaw title")
    category: Optional[str] = Field(None, description="Bylaw category")
    status: Optional[str] = Field(None, description="Bylaw status")
    
    effective_date: Optional[date] = Field(None, description="Effective date")
    amendment_date: Optional[date] = Field(None, description="Amendment date")
    repeal_date: Optional[date] = Field(None, description="Repeal date")
    
    full_text: Optional[str] = Field(None, description="Full text of the bylaw")
    summary: Optional[str] = Field(None, description="Summary of the bylaw")
    
    source_document_id: Optional[UUID] = Field(None, description="Source document ID")
    parent_bylaw_id: Optional[UUID] = Field(None, description="Parent bylaw ID for amendments")


class Bylaw(BylawBase):
    """Full bylaw model."""
    id: UUID = Field(..., description="Bylaw ID")
    municipality_id: UUID = Field(..., description="Municipality ID")
    source_document_id: Optional[UUID] = Field(None, description="Source document ID")
    parent_bylaw_id: Optional[UUID] = Field(None, description="Parent bylaw ID")
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class BylawVersionBase(BaseModel):
    """Base bylaw version model."""
    version_number: int = Field(..., description="Version number")
    content: Dict[str, Any] = Field(..., description="Version content")
    extracted_requirements: Optional[Dict[str, Any]] = Field(None, description="Extracted requirements")
    
    extracted_at: datetime = Field(..., description="Extraction timestamp")
    extraction_method: Optional[str] = Field(None, description="Extraction method")
    confidence_scores: Optional[Dict[str, float]] = Field(None, description="Confidence scores")
    
    source_location: Optional[Dict[str, Any]] = Field(None, description="Source location info")
    
    change_type: Optional[str] = Field(None, description="Type of change")
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    
    is_current: bool = Field(False, description="Whether this is the current version")
    
    @validator("extraction_method")
    def validate_extraction_method(cls, v):
        if v is None:
            return v
        allowed_methods = ["automated", "manual", "hybrid", "imported"]
        if v not in allowed_methods:
            raise ValueError(f"extraction_method must be one of: {allowed_methods}")
        return v
    
    @validator("change_type")
    def validate_change_type(cls, v):
        if v is None:
            return v
        allowed_types = ["amendment", "correction", "clarification", "initial", "repeal"]
        if v not in allowed_types:
            raise ValueError(f"change_type must be one of: {allowed_types}")
        return v


class BylawVersionCreate(BylawVersionBase):
    """Bylaw version creation model."""
    bylaw_id: UUID = Field(..., description="Bylaw ID")
    source_document_id: Optional[UUID] = Field(None, description="Source document ID")
    previous_version_id: Optional[UUID] = Field(None, description="Previous version ID")


class BylawVersionUpdate(BaseModel):
    """Bylaw version update model."""
    content: Optional[Dict[str, Any]] = Field(None, description="Version content")
    extracted_requirements: Optional[Dict[str, Any]] = Field(None, description="Extracted requirements")
    confidence_scores: Optional[Dict[str, float]] = Field(None, description="Confidence scores")
    
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")


class BylawVersion(BylawVersionBase):
    """Full bylaw version model."""
    id: UUID = Field(..., description="Version ID")
    bylaw_id: UUID = Field(..., description="Bylaw ID")
    source_document_id: Optional[UUID] = Field(None, description="Source document ID")
    previous_version_id: Optional[UUID] = Field(None, description="Previous version ID")
    
    created_by: Optional[UUID] = Field(None, description="Creator user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    approved_by: Optional[UUID] = Field(None, description="Approver user ID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    
    class Config:
        from_attributes = True


class BylawWithVersions(Bylaw):
    """Bylaw with version information."""
    versions: List[BylawVersion] = Field(default_factory=list, description="Bylaw versions")
    current_version: Optional[BylawVersion] = Field(None, description="Current version")
    version_count: int = Field(0, description="Total number of versions")


class ADURequirementsBase(BaseModel):
    """Base ADU requirements model."""
    # Physical requirements
    max_height_m: Optional[Decimal] = Field(None, description="Maximum height in meters")
    max_floor_area_sqm: Optional[Decimal] = Field(None, description="Maximum floor area in square meters")
    min_lot_size_sqm: Optional[Decimal] = Field(None, description="Minimum lot size in square meters")
    
    # Setbacks
    front_setback_m: Optional[Decimal] = Field(None, description="Front setback in meters")
    rear_setback_m: Optional[Decimal] = Field(None, description="Rear setback in meters")
    side_setback_m: Optional[Decimal] = Field(None, description="Side setback in meters")
    
    # Other requirements
    max_units: Optional[int] = Field(None, description="Maximum number of units")
    parking_spaces_required: Optional[int] = Field(None, description="Required parking spaces")
    owner_occupancy_required: Optional[bool] = Field(None, description="Owner occupancy required")
    
    # Additional requirements
    other_requirements: Optional[Dict[str, Any]] = Field(None, description="Other requirements")
    
    # Extraction metadata
    extraction_confidence: Optional[Decimal] = Field(None, description="Extraction confidence (0-1)")
    source_text: Optional[str] = Field(None, description="Source text for extraction")


class ADURequirementsCreate(ADURequirementsBase):
    """ADU requirements creation model."""
    bylaw_version_id: UUID = Field(..., description="Bylaw version ID")


class ADURequirements(ADURequirementsBase):
    """Full ADU requirements model."""
    id: UUID = Field(..., description="Requirements ID")
    bylaw_version_id: UUID = Field(..., description="Bylaw version ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class BylawSearch(BaseModel):
    """Bylaw search parameters."""
    # Text search
    query: Optional[str] = Field(None, description="Search query (title, text, number)")
    
    # Filters
    municipality_id: Optional[UUID] = Field(None, description="Filter by municipality")
    category: Optional[str] = Field(None, description="Filter by category")
    status: Optional[str] = Field(None, description="Filter by status")
    
    # Date filters
    effective_date_from: Optional[date] = Field(None, description="Effective date from")
    effective_date_to: Optional[date] = Field(None, description="Effective date to")
    
    # Content filters
    has_full_text: Optional[bool] = Field(None, description="Has full text")
    has_requirements: Optional[bool] = Field(None, description="Has extracted requirements")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    
    # Sorting
    sort_by: str = Field("updated_at", description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = [
            "title", "bylaw_number", "category", "status", "effective_date",
            "created_at", "updated_at"
        ]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {allowed_fields}")
        return v


class BylawList(BaseModel):
    """Paginated bylaw list."""
    bylaws: List[Bylaw] = Field(..., description="List of bylaws")
    total: int = Field(..., description="Total number of bylaws")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    
    @validator("total_pages", pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        if "total" in values and "page_size" in values:
            import math
            return math.ceil(values["total"] / values["page_size"])
        return v