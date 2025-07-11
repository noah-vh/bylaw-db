"""
Source document retrieval API endpoints.
"""
from typing import List, Optional
from uuid import UUID
import mimetypes
import os

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from postgrest import APIError
import httpx

from ...models.source_document import (
    SourceDocument,
    SourceDocumentCreate,
    SourceDocumentUpdate,
    SourceDocumentWithContent,
    SourceDocumentSearch,
    SourceDocumentList,
    SourceDocumentStats,
    SourceDocumentContent,
    SourceDocumentFile
)
from ...utils.supabase_client import get_supabase_client, get_admin_client
from ...config import settings

router = APIRouter(prefix="/source-documents", tags=["source-documents"])


@router.get("/", response_model=SourceDocumentList)
async def get_source_documents(search: SourceDocumentSearch = Depends()):
    """Get list of source documents with optional filtering and pagination."""
    client = get_supabase_client()
    
    try:
        # Build query
        query = client.table("source_documents").select(
            "*, municipality:municipalities(name, province), "
            "bylaw_count:bylaws(count)"
        )
        
        # Apply filters
        if search.municipality_id:
            query = query.eq("municipality_id", str(search.municipality_id))
        
        if search.document_type:
            query = query.eq("document_type", search.document_type)
        
        if search.preservation_status:
            query = query.eq("preservation_status", search.preservation_status)
        
        if search.scraped_from:
            query = query.gte("scraped_at", search.scraped_from.isoformat())
        
        if search.scraped_to:
            query = query.lte("scraped_at", search.scraped_to.isoformat())
        
        if search.url_contains:
            query = query.ilike("document_url", f"%{search.url_contains}%")
        
        if search.has_content is not None:
            if search.has_content:
                query = query.or_(
                    "raw_html_path.not.is.null,pdf_path.not.is.null,screenshot_path.not.is.null"
                )
            else:
                query = query.is_("raw_html_path", "null").is_("pdf_path", "null").is_("screenshot_path", "null")
        
        # Apply sorting
        sort_column = search.sort_by
        if search.sort_order == "desc":
            sort_column = f"{sort_column}.desc()"
        query = query.order(sort_column)
        
        # Get total count
        count_query = client.table("source_documents").select("*", count="exact")
        if search.municipality_id:
            count_query = count_query.eq("municipality_id", str(search.municipality_id))
        if search.document_type:
            count_query = count_query.eq("document_type", search.document_type)
        if search.preservation_status:
            count_query = count_query.eq("preservation_status", search.preservation_status)
        
        count_result = count_query.execute()
        total = count_result.count
        
        # Apply pagination
        offset = (search.page - 1) * search.page_size
        query = query.range(offset, offset + search.page_size - 1)
        
        # Execute query
        result = query.execute()
        
        # Transform results
        documents = []
        for row in result.data:
            document = SourceDocumentWithContent(
                **row,
                bylaw_count=row.get("bylaw_count", [{"count": 0}])[0]["count"],
                has_raw_html=row.get("raw_html_path") is not None,
                has_pdf=row.get("pdf_path") is not None,
                has_screenshot=row.get("screenshot_path") is not None
            )
            documents.append(document)
        
        return SourceDocumentList(
            documents=documents,
            total=total,
            page=search.page,
            page_size=search.page_size,
            total_pages=(total + search.page_size - 1) // search.page_size
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/", response_model=SourceDocument)
async def create_source_document(document: SourceDocumentCreate):
    """Create a new source document record."""
    client = get_admin_client()
    
    try:
        result = client.table("source_documents").insert(document.dict()).execute()
        
        if not result.data:
            raise HTTPException(status_code=400, detail="Failed to create source document")
        
        return SourceDocument(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}", response_model=SourceDocumentWithContent)
async def get_source_document(document_id: UUID):
    """Get source document by ID."""
    client = get_supabase_client()
    
    try:
        result = client.table("source_documents").select(
            "*, municipality:municipalities(name, province), "
            "bylaw_count:bylaws(count)"
        ).eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        row = result.data[0]
        
        return SourceDocumentWithContent(
            **row,
            bylaw_count=row.get("bylaw_count", [{"count": 0}])[0]["count"],
            has_raw_html=row.get("raw_html_path") is not None,
            has_pdf=row.get("pdf_path") is not None,
            has_screenshot=row.get("screenshot_path") is not None
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/{document_id}", response_model=SourceDocument)
async def update_source_document(document_id: UUID, document: SourceDocumentUpdate):
    """Update source document by ID."""
    client = get_admin_client()
    
    try:
        # Remove None values
        update_data = {k: v for k, v in document.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        result = client.table("source_documents").update(update_data).eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        return SourceDocument(**result.data[0])
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{document_id}")
async def delete_source_document(document_id: UUID):
    """Delete source document by ID."""
    client = get_admin_client()
    
    try:
        result = client.table("source_documents").delete().eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        return {"message": "Source document deleted successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}/content", response_model=SourceDocumentContent)
async def get_source_document_content(document_id: UUID):
    """Get the content of a source document."""
    client = get_supabase_client()
    
    try:
        # Get document metadata
        result = client.table("source_documents").select("*").eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        document = result.data[0]
        
        # For now, return metadata only
        # In a full implementation, you would fetch content from storage
        return SourceDocumentContent(
            id=document["id"],
            document_url=document["document_url"],
            document_type=document["document_type"],
            content_hash=document.get("content_hash"),
            file_size_bytes=document.get("file_size_bytes"),
            scraped_at=document["scraped_at"],
            raw_html=None,  # Would fetch from storage
            pdf_content=None,  # Would fetch from storage
            screenshot_content=None  # Would fetch from storage
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}/raw-html")
async def get_source_document_raw_html(document_id: UUID):
    """Get the raw HTML content of a source document."""
    client = get_supabase_client()
    
    try:
        # Get document metadata
        result = client.table("source_documents").select("raw_html_path").eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        document = result.data[0]
        
        if not document.get("raw_html_path"):
            raise HTTPException(status_code=404, detail="Raw HTML not available")
        
        # In a full implementation, fetch from storage
        # For now, return a placeholder
        return Response(
            content="<html><body>HTML content would be loaded from storage</body></html>",
            media_type="text/html"
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}/pdf")
async def get_source_document_pdf(document_id: UUID):
    """Get the PDF content of a source document."""
    client = get_supabase_client()
    
    try:
        # Get document metadata
        result = client.table("source_documents").select("pdf_path").eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        document = result.data[0]
        
        if not document.get("pdf_path"):
            raise HTTPException(status_code=404, detail="PDF not available")
        
        # In a full implementation, fetch from storage
        # For now, return a placeholder response
        raise HTTPException(status_code=501, detail="PDF retrieval not implemented")
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}/screenshot")
async def get_source_document_screenshot(document_id: UUID):
    """Get the screenshot of a source document."""
    client = get_supabase_client()
    
    try:
        # Get document metadata
        result = client.table("source_documents").select("screenshot_path").eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        document = result.data[0]
        
        if not document.get("screenshot_path"):
            raise HTTPException(status_code=404, detail="Screenshot not available")
        
        # In a full implementation, fetch from storage
        # For now, return a placeholder response
        raise HTTPException(status_code=501, detail="Screenshot retrieval not implemented")
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}/files", response_model=List[SourceDocumentFile])
async def get_source_document_files(document_id: UUID):
    """Get list of files associated with a source document."""
    client = get_supabase_client()
    
    try:
        # Get document metadata
        result = client.table("source_documents").select("*").eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        document = result.data[0]
        files = []
        
        # Add available files
        if document.get("raw_html_path"):
            files.append(SourceDocumentFile(
                filename="raw.html",
                content_type="text/html",
                file_size=document.get("file_size_bytes", 0),
                file_path=document["raw_html_path"],
                created_at=document["scraped_at"],
                is_accessible=True
            ))
        
        if document.get("pdf_path"):
            files.append(SourceDocumentFile(
                filename="document.pdf",
                content_type="application/pdf",
                file_size=document.get("file_size_bytes", 0),
                file_path=document["pdf_path"],
                created_at=document["scraped_at"],
                is_accessible=True
            ))
        
        if document.get("screenshot_path"):
            files.append(SourceDocumentFile(
                filename="screenshot.png",
                content_type="image/png",
                file_size=0,  # Would get from storage
                file_path=document["screenshot_path"],
                created_at=document["scraped_at"],
                is_accessible=True
            ))
        
        return files
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats", response_model=SourceDocumentStats)
async def get_source_document_stats():
    """Get statistics about source documents."""
    client = get_supabase_client()
    
    try:
        # Get basic counts
        all_docs = client.table("source_documents").select("*").execute()
        
        total_documents = len(all_docs.data)
        
        # Count by type
        documents_by_type = {}
        documents_by_status = {}
        total_storage = 0
        
        for doc in all_docs.data:
            doc_type = doc.get("document_type", "unknown")
            documents_by_type[doc_type] = documents_by_type.get(doc_type, 0) + 1
            
            status = doc.get("preservation_status", "unknown")
            documents_by_status[status] = documents_by_status.get(status, 0) + 1
            
            if doc.get("file_size_bytes"):
                total_storage += doc["file_size_bytes"]
        
        # Count documents with content
        documents_with_content = sum(1 for doc in all_docs.data 
                                   if doc.get("raw_html_path") or doc.get("pdf_path") or doc.get("screenshot_path"))
        
        # Count documents with bylaws
        documents_with_bylaws = len(set(doc.get("id") for doc in all_docs.data 
                                      if any(bylaw.get("source_document_id") == doc.get("id") 
                                           for bylaw in client.table("bylaws").select("source_document_id").execute().data)))
        
        return SourceDocumentStats(
            total_documents=total_documents,
            documents_by_type=documents_by_type,
            documents_by_status=documents_by_status,
            total_storage_bytes=total_storage,
            documents_with_content=documents_with_content,
            documents_with_bylaws=documents_with_bylaws
        )
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{document_id}/reprocess")
async def reprocess_source_document(document_id: UUID):
    """Trigger reprocessing of a source document."""
    client = get_admin_client()
    
    try:
        # Verify document exists
        result = client.table("source_documents").select("id").eq("id", str(document_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        # In a full implementation, trigger reprocessing job
        # For now, just return success
        return {"message": "Reprocessing triggered successfully"}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{document_id}/bylaws")
async def get_source_document_bylaws(document_id: UUID):
    """Get bylaws extracted from a source document."""
    client = get_supabase_client()
    
    try:
        # Get bylaws from this source document
        result = client.table("bylaws").select("*").eq("source_document_id", str(document_id)).execute()
        
        return {"bylaws": result.data}
        
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")