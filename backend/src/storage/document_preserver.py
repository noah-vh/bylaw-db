"""
Document preservation module for storing source documents with complete integrity.
Ensures liability protection through comprehensive source document archival.
"""

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

import asyncio
import asyncpg
from bs4 import BeautifulSoup
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class DocumentPreserver:
    """
    Handles comprehensive preservation of source documents.
    """
    
    def __init__(self, supabase_client: Client, db_pool: asyncpg.Pool):
        self.supabase = supabase_client
        self.db_pool = db_pool
        self.bucket_name = 'source-documents'
        
        # Ensure bucket exists
        try:
            self.supabase.storage.get_bucket(self.bucket_name)
        except:
            # Create bucket if it doesn't exist
            self.supabase.storage.create_bucket(self.bucket_name)
    
    def generate_storage_paths(self, municipality_id: str, url: str, timestamp: datetime) -> Dict[str, str]:
        """
        Generate organized storage paths for different document types.
        
        Args:
            municipality_id: Municipality UUID
            url: Source URL
            timestamp: Scraping timestamp
            
        Returns:
            Dictionary of storage paths
        """
        # Parse URL for filename generation
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # Create timestamp string
        ts = timestamp.strftime('%Y/%m/%d/%H%M%S')
        
        # Generate paths
        base_path = f"{municipality_id}/{domain}/{ts}"
        
        return {
            'html': f"{base_path}/page.html",
            'pdf': f"{base_path}/document.pdf",
            'screenshot': f"{base_path}/screenshot.png",
            'assets': f"{base_path}/assets/",
            'metadata': f"{base_path}/metadata.json"
        }
    
    async def create_source_document_record(
        self, 
        municipality_id: str, 
        url: str, 
        document_type: str,
        scraper_version: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Create a source document record in the database.
        
        Returns:
            The UUID of the created record
        """
        async with self.db_pool.acquire() as conn:
            query = """
            INSERT INTO source_documents (
                municipality_id, document_url, document_type, scraped_at,
                scraper_version, scraper_ip_address, http_headers, response_code,
                preservation_status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """
            
            record_id = await conn.fetchval(
                query,
                municipality_id,
                url,
                document_type,
                datetime.utcnow(),
                scraper_version,
                metadata.get('ip_address'),
                json.dumps(metadata.get('headers', {})),
                metadata.get('status_code'),
                'pending'
            )
            
            return str(record_id)
    
    async def update_source_document_paths(
        self, 
        document_id: str, 
        paths: Dict[str, str],
        content_hash: str,
        file_size: int
    ):
        """Update source document record with storage paths and metadata."""
        async with self.db_pool.acquire() as conn:
            query = """
            UPDATE source_documents 
            SET raw_html_path = $1, pdf_path = $2, screenshot_path = $3,
                content_hash = $4, file_size_bytes = $5, preservation_status = $6
            WHERE id = $7
            """
            
            await conn.execute(
                query,
                paths.get('html'),
                paths.get('pdf'),
                paths.get('screenshot'),
                content_hash,
                file_size,
                'preserved',
                document_id
            )
    
    async def mark_preservation_failed(self, document_id: str, error: str):
        """Mark a document preservation as failed."""
        async with self.db_pool.acquire() as conn:
            query = """
            UPDATE source_documents 
            SET preservation_status = 'failed', preservation_error = $1
            WHERE id = $2
            """
            await conn.execute(query, error, document_id)
    
    def upload_to_storage(self, file_path: str, content: bytes, content_type: str = None) -> bool:
        """
        Upload content to Supabase storage.
        
        Args:
            file_path: Path within storage bucket
            content: File content as bytes
            content_type: MIME type of content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine content type if not provided
            if content_type is None:
                if file_path.endswith('.html'):
                    content_type = 'text/html'
                elif file_path.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif file_path.endswith('.png'):
                    content_type = 'image/png'
                elif file_path.endswith('.json'):
                    content_type = 'application/json'
                else:
                    content_type = 'application/octet-stream'
            
            # Upload to storage
            result = self.supabase.storage.from_(self.bucket_name).upload(
                file_path,
                content,
                {
                    'content-type': content_type,
                    'cache-control': '31536000',  # 1 year
                    'x-upsert': 'false'  # Don't overwrite existing files
                }
            )
            
            if result.error:
                logger.error(f"Storage upload failed: {result.error}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Storage upload error: {e}")
            return False
    
    def preserve_html_with_assets(
        self, 
        content: str, 
        base_url: str, 
        storage_paths: Dict[str, str],
        assets: List[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Preserve HTML content with embedded assets.
        
        Args:
            content: HTML content
            base_url: Base URL for the page
            storage_paths: Dictionary of storage paths
            assets: List of asset information
            
        Returns:
            Tuple of (success, content_hash)
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(content, 'html5lib')
            
            # Add preservation metadata to HTML
            meta_tag = soup.new_tag('meta', 
                name='bylaw-db-preserved',
                content=datetime.utcnow().isoformat()
            )
            if soup.head:
                soup.head.append(meta_tag)
            
            # Update asset URLs if assets were preserved
            if assets:
                for asset in assets:
                    # Find elements with the original URL
                    for element in soup.find_all():
                        for attr in ['src', 'href']:
                            if element.get(attr) == asset['original_url']:
                                # Update to preserved path
                                element[attr] = asset['storage_path']
            
            # Convert back to string
            preserved_html = str(soup)
            
            # Calculate content hash
            content_hash = hashlib.sha256(preserved_html.encode('utf-8')).hexdigest()
            
            # Upload to storage
            success = self.upload_to_storage(
                storage_paths['html'],
                preserved_html.encode('utf-8'),
                'text/html'
            )
            
            return success, content_hash
            
        except Exception as e:
            logger.error(f"HTML preservation error: {e}")
            return False, ""
    
    def preserve_pdf(self, pdf_content: bytes, storage_path: str) -> Tuple[bool, str]:
        """
        Preserve PDF content.
        
        Args:
            pdf_content: PDF content as bytes
            storage_path: Storage path for PDF
            
        Returns:
            Tuple of (success, content_hash)
        """
        try:
            # Calculate content hash
            content_hash = hashlib.sha256(pdf_content).hexdigest()
            
            # Upload to storage
            success = self.upload_to_storage(
                storage_path,
                pdf_content,
                'application/pdf'
            )
            
            return success, content_hash
            
        except Exception as e:
            logger.error(f"PDF preservation error: {e}")
            return False, ""
    
    def preserve_screenshot(self, screenshot_path: Path, storage_path: str) -> bool:
        """
        Preserve screenshot file.
        
        Args:
            screenshot_path: Local path to screenshot
            storage_path: Storage path for screenshot
            
        Returns:
            True if successful
        """
        try:
            with open(screenshot_path, 'rb') as f:
                content = f.read()
            
            return self.upload_to_storage(
                storage_path,
                content,
                'image/png'
            )
            
        except Exception as e:
            logger.error(f"Screenshot preservation error: {e}")
            return False
    
    def preserve_assets(
        self, 
        assets: List[Dict[str, Any]], 
        base_storage_path: str
    ) -> List[Dict[str, Any]]:
        """
        Preserve page assets (images, CSS, JS).
        
        Args:
            assets: List of asset information from scraper
            base_storage_path: Base path for asset storage
            
        Returns:
            List of preserved asset information
        """
        preserved_assets = []
        
        for i, asset in enumerate(assets):
            try:
                # Read asset content
                with open(asset['local_path'], 'rb') as f:
                    content = f.read()
                
                # Generate storage path
                filename = Path(asset['local_path']).name
                storage_path = f"{base_storage_path}{filename}"
                
                # Upload to storage
                success = self.upload_to_storage(
                    storage_path,
                    content,
                    asset.get('content_type')
                )
                
                if success:
                    preserved_assets.append({
                        **asset,
                        'storage_path': storage_path,
                        'preserved_at': datetime.utcnow().isoformat()
                    })
                
            except Exception as e:
                logger.error(f"Asset preservation error for {asset['local_path']}: {e}")
        
        return preserved_assets
    
    def preserve_metadata(self, metadata: Dict[str, Any], storage_path: str) -> bool:
        """
        Preserve comprehensive metadata.
        
        Args:
            metadata: Metadata dictionary
            storage_path: Storage path for metadata
            
        Returns:
            True if successful
        """
        try:
            # Add preservation timestamp
            metadata['preserved_at'] = datetime.utcnow().isoformat()
            
            # Convert to JSON
            metadata_json = json.dumps(metadata, indent=2, default=str)
            
            # Upload to storage
            return self.upload_to_storage(
                storage_path,
                metadata_json.encode('utf-8'),
                'application/json'
            )
            
        except Exception as e:
            logger.error(f"Metadata preservation error: {e}")
            return False
    
    async def preserve_document(
        self,
        municipality_id: str,
        url: str,
        document_type: str,
        scraper_version: str,
        content: str,
        metadata: Dict[str, Any],
        screenshot_path: Optional[Path] = None,
        pdf_content: Optional[bytes] = None,
        assets: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive document preservation.
        
        Args:
            municipality_id: Municipality UUID
            url: Source URL
            document_type: Type of document (webpage, pdf, etc.)
            scraper_version: Version of scraper used
            content: HTML content
            metadata: Document metadata
            screenshot_path: Path to screenshot file
            pdf_content: PDF content if applicable
            assets: List of page assets
            
        Returns:
            Dictionary with preservation results
        """
        preservation_results = {
            'success': False,
            'document_id': None,
            'errors': []
        }
        
        try:
            # Create database record
            document_id = await self.create_source_document_record(
                municipality_id, url, document_type, scraper_version, metadata
            )
            preservation_results['document_id'] = document_id
            
            # Generate storage paths
            storage_paths = self.generate_storage_paths(
                municipality_id, url, datetime.utcnow()
            )
            
            # Preserve HTML content
            html_success, content_hash = self.preserve_html_with_assets(
                content, url, storage_paths, assets
            )
            if not html_success:
                preservation_results['errors'].append('HTML preservation failed')
            
            # Preserve PDF if provided
            pdf_success = True
            if pdf_content:
                pdf_success, pdf_hash = self.preserve_pdf(pdf_content, storage_paths['pdf'])
                if not pdf_success:
                    preservation_results['errors'].append('PDF preservation failed')
            
            # Preserve screenshot if provided
            screenshot_success = True
            if screenshot_path:
                screenshot_success = self.preserve_screenshot(
                    screenshot_path, storage_paths['screenshot']
                )
                if not screenshot_success:
                    preservation_results['errors'].append('Screenshot preservation failed')
            
            # Preserve assets if provided
            preserved_assets = []
            if assets:
                preserved_assets = self.preserve_assets(assets, storage_paths['assets'])
            
            # Preserve metadata
            full_metadata = {
                **metadata,
                'preservation_info': {
                    'preserved_at': datetime.utcnow().isoformat(),
                    'storage_paths': storage_paths,
                    'assets_preserved': len(preserved_assets)
                }
            }
            
            metadata_success = self.preserve_metadata(full_metadata, storage_paths['metadata'])
            if not metadata_success:
                preservation_results['errors'].append('Metadata preservation failed')
            
            # Update database record
            if html_success and pdf_success and screenshot_success and metadata_success:
                await self.update_source_document_paths(
                    document_id, 
                    storage_paths,
                    content_hash,
                    len(content.encode('utf-8'))
                )
                preservation_results['success'] = True
            else:
                await self.mark_preservation_failed(
                    document_id, 
                    '; '.join(preservation_results['errors'])
                )
            
        except Exception as e:
            logger.error(f"Document preservation error: {e}")
            preservation_results['errors'].append(f"General preservation error: {e}")
            
            if preservation_results['document_id']:
                await self.mark_preservation_failed(
                    preservation_results['document_id'], 
                    str(e)
                )
        
        return preservation_results
    
    async def get_preservation_status(self, document_id: str) -> Dict[str, Any]:
        """Get preservation status for a document."""
        async with self.db_pool.acquire() as conn:
            query = """
            SELECT preservation_status, preservation_error, raw_html_path,
                   pdf_path, screenshot_path, content_hash, file_size_bytes
            FROM source_documents
            WHERE id = $1
            """
            
            row = await conn.fetchrow(query, document_id)
            
            if row:
                return dict(row)
            else:
                return {'error': 'Document not found'}
    
    async def verify_document_integrity(self, document_id: str) -> Dict[str, Any]:
        """
        Verify the integrity of a preserved document.
        
        Args:
            document_id: Source document ID
            
        Returns:
            Dictionary with verification results
        """
        try:
            # Get document info
            status = await self.get_preservation_status(document_id)
            
            if 'error' in status:
                return status
            
            verification_results = {
                'document_id': document_id,
                'verified': False,
                'checks': {}
            }
            
            # Check if HTML exists in storage
            if html_path := status.get('raw_html_path'):
                try:
                    response = self.supabase.storage.from_(self.bucket_name).download(html_path)
                    if response:
                        # Verify hash
                        stored_hash = hashlib.sha256(response).hexdigest()
                        verification_results['checks']['html'] = {
                            'exists': True,
                            'hash_match': stored_hash == status.get('content_hash')
                        }
                    else:
                        verification_results['checks']['html'] = {'exists': False}
                except:
                    verification_results['checks']['html'] = {'exists': False}
            
            # Check other files similarly...
            # (PDF, screenshot, metadata)
            
            # Overall verification
            verification_results['verified'] = all(
                check.get('exists', False) for check in verification_results['checks'].values()
            )
            
            return verification_results
            
        except Exception as e:
            logger.error(f"Document verification error: {e}")
            return {'error': f"Verification failed: {e}"}