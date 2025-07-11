"""
Source document model definitions.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SourceDocumentBase(BaseModel):
    """Base source document model."""
    document_url: str = Field(..., description="URL of the source document")
    document_type: str = Field(..., description="Type of document")
    scraped_at: datetime = Field(..., description="When the document was scraped")
    scraper_version: str = Field(..., description="Version of the scraper used")
    scraper_ip_address: Optional[str] = Field(None, description="IP address of the scraper")
    
    # Storage paths
    raw_html_path: Optional[str] = Field(None, description="Path to raw HTML file")
    pdf_path: Optional[str] = Field(None, description="Path to PDF file")
    screenshot_path: Optional[str] = Field(None, description="Path to screenshot file")
    
    # Metadata
    http_headers: Optional[Dict[str, Any]] = Field(None, description="HTTP headers from response")
    response_code: Optional[int] = Field(None, description="HTTP response code")
    content_hash: Optional[str] = Field(None, description="SHA256 hash of content")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    
    # Preservation metadata
    preservation_status: str = Field("pending", description="Preservation status")
    preservation_error: Optional[str] = Field(None, description="Preservation error message")
    
    @validator("document_type")
    def validate_document_type(cls, v):
        allowed_types = ["webpage", "pdf", "doc", "docx", "html", "xml", "json", "other"]
        if v not in allowed_types:
            raise ValueError(f"document_type must be one of: {allowed_types}")
        return v
    
    @validator("preservation_status")
    def validate_preservation_status(cls, v):
        allowed_statuses = ["pending", "preserved", "failed", "partial"]
        if v not in allowed_statuses:
            raise ValueError(f"preservation_status must be one of: {allowed_statuses}")
        return v


class SourceDocumentCreate(SourceDocumentBase):
    """Source document creation model."""
    municipality_id: UUID = Field(..., description="Municipality ID")


class SourceDocumentUpdate(BaseModel):
    """Source document update model."""
    document_url: Optional[str] = Field(None, description="URL of the source document")
    document_type: Optional[str] = Field(None, description="Type of document")
    
    # Storage paths
    raw_html_path: Optional[str] = Field(None, description="Path to raw HTML file")
    pdf_path: Optional[str] = Field(None, description="Path to PDF file")
    screenshot_path: Optional[str] = Field(None, description="Path to screenshot file")
    
    # Metadata
    http_headers: Optional[Dict[str, Any]] = Field(None, description="HTTP headers from response")
    response_code: Optional[int] = Field(None, description="HTTP response code")
    content_hash: Optional[str] = Field(None, description="SHA256 hash of content")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    
    # Preservation metadata
    preservation_status: Optional[str] = Field(None, description="Preservation status")
    preservation_error: Optional[str] = Field(None, description="Preservation error message")


class SourceDocument(SourceDocumentBase):
    """Full source document model."""
    id: UUID = Field(..., description="Source document ID")
    municipality_id: UUID = Field(..., description="Municipality ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class SourceDocumentWithContent(SourceDocument):
    """Source document with content information."""
    content_preview: Optional[str] = Field(None, description="Preview of document content")
    has_raw_html: bool = Field(False, description="Whether raw HTML is available")
    has_pdf: bool = Field(False, description="Whether PDF is available")
    has_screenshot: bool = Field(False, description="Whether screenshot is available")
    
    # Related bylaws
    bylaw_count: int = Field(0, description="Number of bylaws extracted from this document")
    
    @validator("has_raw_html", pre=True, always=True)
    def check_raw_html(cls, v, values):
        return values.get("raw_html_path") is not None
    
    @validator("has_pdf", pre=True, always=True)
    def check_pdf(cls, v, values):
        return values.get("pdf_path") is not None
    
    @validator("has_screenshot", pre=True, always=True)
    def check_screenshot(cls, v, values):
        return values.get("screenshot_path") is not None


class SourceDocumentSearch(BaseModel):
    """Source document search parameters."""
    # Filters
    municipality_id: Optional[UUID] = Field(None, description="Filter by municipality")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    preservation_status: Optional[str] = Field(None, description="Filter by preservation status")
    
    # Date filters
    scraped_from: Optional[datetime] = Field(None, description="Scraped from date")
    scraped_to: Optional[datetime] = Field(None, description="Scraped to date")
    
    # Content filters
    has_content: Optional[bool] = Field(None, description="Has any content stored")
    has_bylaws: Optional[bool] = Field(None, description="Has extracted bylaws")
    
    # URL search
    url_contains: Optional[str] = Field(None, description="URL contains text")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    
    # Sorting
    sort_by: str = Field("scraped_at", description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = [
            "scraped_at", "created_at", "document_type", "preservation_status",
            "file_size_bytes", "response_code"
        ]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {allowed_fields}")
        return v


class SourceDocumentList(BaseModel):
    """Paginated source document list."""
    documents: List[SourceDocumentWithContent] = Field(..., description="List of source documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    
    @validator("total_pages", pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        if "total" in values and "page_size" in values:
            import math
            return math.ceil(values["total"] / values["page_size"])
        return v


class SourceDocumentStats(BaseModel):
    """Source document statistics."""
    total_documents: int = Field(0, description="Total number of documents")
    documents_by_type: Dict[str, int] = Field(default_factory=dict, description="Documents by type")
    documents_by_status: Dict[str, int] = Field(default_factory=dict, description="Documents by preservation status")
    
    # Storage statistics
    total_storage_bytes: int = Field(0, description="Total storage used in bytes")
    storage_by_type: Dict[str, int] = Field(default_factory=dict, description="Storage by content type")
    
    # Preservation statistics
    preservation_success_rate: float = Field(0.0, description="Preservation success rate")
    documents_with_content: int = Field(0, description="Documents with any content")
    documents_with_bylaws: int = Field(0, description="Documents with extracted bylaws")
    
    # Time-based statistics
    documents_last_24h: int = Field(0, description="Documents scraped in last 24 hours")
    documents_last_week: int = Field(0, description="Documents scraped in last week")
    documents_last_month: int = Field(0, description="Documents scraped in last month")
    
    @validator("preservation_success_rate", pre=True, always=True)
    def calculate_success_rate(cls, v, values):
        if "total_documents" in values and values["total_documents"] > 0:
            status_counts = values.get("documents_by_status", {})
            preserved = status_counts.get("preserved", 0)
            return preserved / values["total_documents"]
        return 0.0


class SourceDocumentContent(BaseModel):
    """Source document content for retrieval."""
    id: UUID = Field(..., description="Document ID")
    document_url: str = Field(..., description="Document URL")
    document_type: str = Field(..., description="Document type")
    
    # Content
    raw_html: Optional[str] = Field(None, description="Raw HTML content")
    pdf_content: Optional[bytes] = Field(None, description="PDF content")
    screenshot_content: Optional[bytes] = Field(None, description="Screenshot content")
    
    # Metadata
    content_hash: Optional[str] = Field(None, description="Content hash")
    file_size_bytes: Optional[int] = Field(None, description="File size")
    scraped_at: datetime = Field(..., description="Scraped timestamp")
    
    class Config:
        # Allow bytes fields
        arbitrary_types_allowed = True


class SourceDocumentFile(BaseModel):
    """Source document file information."""
    filename: str = Field(..., description="File name")
    content_type: str = Field(..., description="MIME content type")
    file_size: int = Field(..., description="File size in bytes")
    file_path: str = Field(..., description="Storage path")
    
    # File metadata
    created_at: datetime = Field(..., description="File creation timestamp")
    last_modified: Optional[datetime] = Field(None, description="Last modification timestamp")
    checksum: Optional[str] = Field(None, description="File checksum")
    
    # Access information
    is_accessible: bool = Field(True, description="Whether file is accessible")
    access_url: Optional[str] = Field(None, description="URL for file access")
    expires_at: Optional[datetime] = Field(None, description="Access URL expiration")