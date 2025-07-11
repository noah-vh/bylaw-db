"""
Audit log model definitions.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, validator


class AuditLogBase(BaseModel):
    """Base audit log model."""
    action: str = Field(..., description="Action performed")
    table_name: Optional[str] = Field(None, description="Table name")
    record_id: Optional[UUID] = Field(None, description="Record ID")
    
    # Change tracking
    old_values: Optional[Dict[str, Any]] = Field(None, description="Old values")
    new_values: Optional[Dict[str, Any]] = Field(None, description="New values")
    changed_fields: Optional[List[str]] = Field(None, description="Changed fields")
    
    # User information
    user_id: Optional[UUID] = Field(None, description="User ID")
    user_email: Optional[str] = Field(None, description="User email")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    # Additional context
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    @validator("action")
    def validate_action(cls, v):
        allowed_actions = [
            "INSERT", "UPDATE", "DELETE", "SCRAPE", "LOGIN", "LOGOUT",
            "EXPORT", "IMPORT", "APPROVE", "REJECT", "ARCHIVE", "RESTORE"
        ]
        if v not in allowed_actions:
            raise ValueError(f"action must be one of: {allowed_actions}")
        return v


class AuditLogCreate(AuditLogBase):
    """Audit log creation model."""
    pass


class AuditLog(AuditLogBase):
    """Full audit log model."""
    id: UUID = Field(..., description="Audit log ID")
    timestamp: datetime = Field(..., description="Timestamp")
    
    class Config:
        from_attributes = True


class AuditLogWithDetails(AuditLog):
    """Audit log with additional details."""
    # User details
    user_name: Optional[str] = Field(None, description="User display name")
    user_role: Optional[str] = Field(None, description="User role")
    
    # Record details
    record_title: Optional[str] = Field(None, description="Record title/name")
    municipality_name: Optional[str] = Field(None, description="Related municipality name")
    
    # Change summary
    change_summary: Optional[str] = Field(None, description="Summary of changes made")
    change_impact: Optional[str] = Field(None, description="Impact of changes")


class AuditLogSearch(BaseModel):
    """Audit log search parameters."""
    # Filters
    action: Optional[str] = Field(None, description="Filter by action")
    table_name: Optional[str] = Field(None, description="Filter by table")
    record_id: Optional[UUID] = Field(None, description="Filter by record ID")
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    user_email: Optional[str] = Field(None, description="Filter by user email")
    
    # Date filters
    timestamp_from: Optional[datetime] = Field(None, description="Timestamp from")
    timestamp_to: Optional[datetime] = Field(None, description="Timestamp to")
    
    # Content filters
    has_changes: Optional[bool] = Field(None, description="Has field changes")
    municipality_id: Optional[UUID] = Field(None, description="Filter by municipality")
    
    # Text search
    search_query: Optional[str] = Field(None, description="Search in context and values")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Page size")
    
    # Sorting
    sort_by: str = Field("timestamp", description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")
    
    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = ["timestamp", "action", "table_name", "user_email"]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {allowed_fields}")
        return v


class AuditLogList(BaseModel):
    """Paginated audit log list."""
    logs: List[AuditLogWithDetails] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total number of logs")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    
    @validator("total_pages", pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        if "total" in values and "page_size" in values:
            import math
            return math.ceil(values["total"] / values["page_size"])
        return v


class AuditLogStats(BaseModel):
    """Audit log statistics."""
    total_logs: int = Field(0, description="Total number of logs")
    logs_by_action: Dict[str, int] = Field(default_factory=dict, description="Logs by action")
    logs_by_table: Dict[str, int] = Field(default_factory=dict, description="Logs by table")
    logs_by_user: Dict[str, int] = Field(default_factory=dict, description="Logs by user")
    
    # Time-based statistics
    logs_last_24h: int = Field(0, description="Logs in last 24 hours")
    logs_last_week: int = Field(0, description="Logs in last week")
    logs_last_month: int = Field(0, description="Logs in last month")
    
    # Activity patterns
    most_active_users: List[Dict[str, Any]] = Field(default_factory=list, description="Most active users")
    most_modified_tables: List[Dict[str, Any]] = Field(default_factory=list, description="Most modified tables")
    activity_by_hour: Dict[int, int] = Field(default_factory=dict, description="Activity by hour of day")
    
    # Data quality
    logs_with_context: int = Field(0, description="Logs with context information")
    logs_with_changes: int = Field(0, description="Logs with field changes")


class AuditLogContext(BaseModel):
    """Context information for audit logs."""
    request_id: Optional[str] = Field(None, description="Request ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    # Application context
    app_version: Optional[str] = Field(None, description="Application version")
    feature_flag: Optional[str] = Field(None, description="Feature flag")
    
    # Business context
    municipality_id: Optional[UUID] = Field(None, description="Related municipality")
    bylaw_id: Optional[UUID] = Field(None, description="Related bylaw")
    scraping_job_id: Optional[UUID] = Field(None, description="Related scraping job")
    
    # Technical context
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    
    # Additional metadata
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AuditLogBatch(BaseModel):
    """Batch of audit log entries."""
    logs: List[AuditLogCreate] = Field(..., description="List of audit logs to create")
    batch_id: Optional[str] = Field(None, description="Batch identifier")
    batch_context: Optional[Dict[str, Any]] = Field(None, description="Batch context")
    
    @validator("logs")
    def validate_logs_not_empty(cls, v):
        if not v:
            raise ValueError("logs cannot be empty")
        return v


class AuditLogExport(BaseModel):
    """Audit log export configuration."""
    # Filters (same as search)
    action: Optional[str] = Field(None, description="Filter by action")
    table_name: Optional[str] = Field(None, description="Filter by table")
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    timestamp_from: Optional[datetime] = Field(None, description="Timestamp from")
    timestamp_to: Optional[datetime] = Field(None, description="Timestamp to")
    
    # Export settings
    format: str = Field("csv", description="Export format")
    include_details: bool = Field(True, description="Include detailed information")
    include_changes: bool = Field(True, description="Include change details")
    
    # Compression
    compress: bool = Field(False, description="Compress export file")
    
    @validator("format")
    def validate_format(cls, v):
        allowed_formats = ["csv", "json", "xlsx", "pdf"]
        if v not in allowed_formats:
            raise ValueError(f"format must be one of: {allowed_formats}")
        return v