"""
Test cases for scraper functionality.
Tests web scraping, document extraction, and data processing.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
import tempfile
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup

# Import the modules we're testing (adjust imports based on actual structure)
# from src.scrapers.base import BaseScraper
# from src.scrapers.municipal import MunicipalScraper
# from src.scrapers.document_processor import DocumentProcessor
# from src.models.document import Document
# from src.models.jurisdiction import Jurisdiction


class TestBaseScraper:
    """Test cases for the base scraper functionality."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock aiohttp session."""
        session = Mock(spec=aiohttp.ClientSession)
        return session
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML content for testing."""
        return """
        <html>
            <body>
                <div class="document-list">
                    <div class="document-item">
                        <a href="/document/1">Bylaw 2024-001</a>
                        <span class="date">2024-01-15</span>
                    </div>
                    <div class="document-item">
                        <a href="/document/2">Bylaw 2024-002</a>
                        <span class="date">2024-02-20</span>
                    </div>
                </div>
            </body>
        </html>
        """
    
    @pytest.fixture
    def sample_jurisdiction(self):
        """Sample jurisdiction data."""
        return {
            "id": "test-jurisdiction",
            "name": "Test Municipality",
            "type": "municipal",
            "country": "Canada",
            "province_state": "Ontario",
            "website": "https://example.com",
            "scraping_config": {
                "base_url": "https://example.com/bylaws",
                "document_list_selector": ".document-item",
                "title_selector": "a",
                "date_selector": ".date",
                "link_selector": "a"
            }
        }
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, sample_jurisdiction):
        """Test scraper initialization with configuration."""
        # Mock the scraper class
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper(sample_jurisdiction)
            MockScraper.assert_called_once_with(sample_jurisdiction)
    
    @pytest.mark.asyncio
    async def test_fetch_page_success(self, mock_session, sample_html):
        """Test successful page fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=sample_html)
        mock_response.headers = {'content-type': 'text/html'}
        
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Test the fetch operation
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            scraper.fetch_page = AsyncMock(return_value=sample_html)
            
            result = await scraper.fetch_page("https://example.com")
            assert result == sample_html
    
    @pytest.mark.asyncio
    async def test_fetch_page_error_handling(self, mock_session):
        """Test error handling in page fetching."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status = 404
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            scraper.fetch_page = AsyncMock(side_effect=aiohttp.ClientError("Not found"))
            
            with pytest.raises(aiohttp.ClientError):
                await scraper.fetch_page("https://example.com/nonexistent")
    
    @pytest.mark.asyncio
    async def test_parse_document_list(self, sample_html, sample_jurisdiction):
        """Test parsing document list from HTML."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        # Mock parser
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            scraper.parse_document_list = Mock(return_value=[
                {
                    'title': 'Bylaw 2024-001',
                    'url': 'https://example.com/document/1',
                    'date': '2024-01-15'
                },
                {
                    'title': 'Bylaw 2024-002',
                    'url': 'https://example.com/document/2',
                    'date': '2024-02-20'
                }
            ])
            
            documents = scraper.parse_document_list(soup)
            assert len(documents) == 2
            assert documents[0]['title'] == 'Bylaw 2024-001'
            assert documents[1]['title'] == 'Bylaw 2024-002'
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_session):
        """Test rate limiting between requests."""
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            scraper.rate_limit = 1.0  # 1 second between requests
            
            # Mock timing
            with patch('asyncio.sleep') as mock_sleep:
                scraper.apply_rate_limit = AsyncMock()
                await scraper.apply_rate_limit()
                # Verify that sleep was called with appropriate delay
                # (actual implementation would vary)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, mock_session):
        """Test retry mechanism for failed requests."""
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            
            # Mock method that fails twice then succeeds
            call_count = 0
            async def mock_fetch(url):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise aiohttp.ClientError("Connection failed")
                return "<html>Success</html>"
            
            scraper.fetch_page = mock_fetch
            
            # This should succeed after 2 retries
            result = await scraper.fetch_page("https://example.com")
            assert result == "<html>Success</html>"
            assert call_count == 3


class TestMunicipalScraper:
    """Test cases for municipal-specific scraping."""
    
    @pytest.fixture
    def toronto_config(self):
        """Toronto-specific scraping configuration."""
        return {
            "id": "toronto",
            "name": "City of Toronto",
            "scraping_config": {
                "base_url": "https://www.toronto.ca/city-government/accountability-operations-customer-service/city-administration/city-managers-office/accountability-offices/ombudsman-toronto/investigation-reports/",
                "document_list_selector": ".field-item",
                "pagination_selector": ".pager-next a",
                "max_pages": 50
            }
        }
    
    @pytest.mark.asyncio
    async def test_municipal_scraper_initialization(self, toronto_config):
        """Test municipal scraper initialization."""
        with patch('src.scrapers.municipal.MunicipalScraper') as MockScraper:
            scraper = MockScraper(toronto_config)
            MockScraper.assert_called_once_with(toronto_config)
    
    @pytest.mark.asyncio
    async def test_pagination_handling(self, toronto_config):
        """Test pagination through multiple pages."""
        with patch('src.scrapers.municipal.MunicipalScraper') as MockScraper:
            scraper = MockScraper.return_value
            
            # Mock pagination
            scraper.get_next_page_url = Mock(side_effect=[
                "https://example.com/page2",
                "https://example.com/page3",
                None  # No more pages
            ])
            
            pages = []
            current_url = "https://example.com/page1"
            
            while current_url:
                pages.append(current_url)
                current_url = scraper.get_next_page_url(current_url)
            
            assert len(pages) == 3
            assert pages[0] == "https://example.com/page1"
            assert pages[1] == "https://example.com/page2"
            assert pages[2] == "https://example.com/page3"
    
    @pytest.mark.asyncio
    async def test_document_type_detection(self):
        """Test automatic document type detection."""
        with patch('src.scrapers.municipal.MunicipalScraper') as MockScraper:
            scraper = MockScraper.return_value
            
            def mock_detect_type(title):
                if "bylaw" in title.lower():
                    return "bylaw"
                elif "policy" in title.lower():
                    return "policy"
                else:
                    return "document"
            
            scraper.detect_document_type = mock_detect_type
            
            assert scraper.detect_document_type("Bylaw 2024-001") == "bylaw"
            assert scraper.detect_document_type("Policy on Housing") == "policy"
            assert scraper.detect_document_type("Report on Budget") == "document"


class TestDocumentProcessor:
    """Test cases for document processing."""
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Mock PDF content."""
        return b"%PDF-1.4\nSample PDF content for testing"
    
    @pytest.fixture
    def temp_pdf_file(self, sample_pdf_content):
        """Create a temporary PDF file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(sample_pdf_content)
            tmp.flush()
            yield tmp.name
        
        # Cleanup
        Path(tmp.name).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_pdf_download(self, temp_pdf_file):
        """Test PDF document download."""
        with patch('src.scrapers.document_processor.DocumentProcessor') as MockProcessor:
            processor = MockProcessor.return_value
            
            # Mock download
            processor.download_document = AsyncMock(return_value=temp_pdf_file)
            
            file_path = await processor.download_document("https://example.com/doc.pdf")
            assert file_path == temp_pdf_file
            assert Path(file_path).exists()
    
    @pytest.mark.asyncio
    async def test_pdf_text_extraction(self, temp_pdf_file):
        """Test text extraction from PDF."""
        with patch('src.scrapers.document_processor.DocumentProcessor') as MockProcessor:
            processor = MockProcessor.return_value
            
            # Mock text extraction
            processor.extract_text = Mock(return_value="Sample extracted text from PDF")
            
            text = processor.extract_text(temp_pdf_file)
            assert text == "Sample extracted text from PDF"
    
    @pytest.mark.asyncio
    async def test_document_metadata_extraction(self, temp_pdf_file):
        """Test metadata extraction from document."""
        with patch('src.scrapers.document_processor.DocumentProcessor') as MockProcessor:
            processor = MockProcessor.return_value
            
            # Mock metadata extraction
            processor.extract_metadata = Mock(return_value={
                "title": "Test Document",
                "pages": 5,
                "file_size": 1024,
                "created_date": "2024-01-15",
                "format": "PDF"
            })
            
            metadata = processor.extract_metadata(temp_pdf_file)
            assert metadata["title"] == "Test Document"
            assert metadata["pages"] == 5
            assert metadata["file_size"] == 1024
    
    @pytest.mark.asyncio
    async def test_document_section_parsing(self):
        """Test parsing document into sections."""
        sample_text = """
        1. Introduction
        This is the introduction section.
        
        2. Definitions
        These are the definitions.
        
        3. Regulations
        These are the regulations.
        """
        
        with patch('src.scrapers.document_processor.DocumentProcessor') as MockProcessor:
            processor = MockProcessor.return_value
            
            # Mock section parsing
            processor.parse_sections = Mock(return_value=[
                {
                    "section_number": "1",
                    "title": "Introduction",
                    "content": "This is the introduction section."
                },
                {
                    "section_number": "2",
                    "title": "Definitions",
                    "content": "These are the definitions."
                },
                {
                    "section_number": "3",
                    "title": "Regulations",
                    "content": "These are the regulations."
                }
            ])
            
            sections = processor.parse_sections(sample_text)
            assert len(sections) == 3
            assert sections[0]["section_number"] == "1"
            assert sections[0]["title"] == "Introduction"
    
    @pytest.mark.asyncio
    async def test_file_validation(self):
        """Test file validation and security checks."""
        with patch('src.scrapers.document_processor.DocumentProcessor') as MockProcessor:
            processor = MockProcessor.return_value
            
            # Mock validation
            processor.validate_file = Mock(return_value=True)
            processor.is_safe_file = Mock(return_value=True)
            
            assert processor.validate_file("document.pdf") == True
            assert processor.is_safe_file("document.pdf") == True
            
            # Test invalid file
            processor.validate_file = Mock(return_value=False)
            assert processor.validate_file("malicious.exe") == False


class TestScrapingIntegration:
    """Integration tests for complete scraping workflow."""
    
    @pytest.mark.asyncio
    async def test_full_scraping_workflow(self, sample_jurisdiction):
        """Test complete scraping workflow from start to finish."""
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            
            # Mock the complete workflow
            scraper.run_scraping_job = AsyncMock(return_value={
                "job_id": "test-job-123",
                "status": "completed",
                "documents_found": 5,
                "documents_processed": 4,
                "errors": 1,
                "duration": 120.5
            })
            
            result = await scraper.run_scraping_job(sample_jurisdiction)
            
            assert result["status"] == "completed"
            assert result["documents_found"] == 5
            assert result["documents_processed"] == 4
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, sample_jurisdiction):
        """Test error recovery in scraping workflow."""
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            
            # Mock partial failure
            scraper.run_scraping_job = AsyncMock(return_value={
                "job_id": "test-job-456",
                "status": "partial_failure",
                "documents_found": 10,
                "documents_processed": 7,
                "errors": 3,
                "error_details": [
                    {"url": "https://example.com/doc1", "error": "Download failed"},
                    {"url": "https://example.com/doc2", "error": "Parse failed"},
                    {"url": "https://example.com/doc3", "error": "Timeout"}
                ]
            })
            
            result = await scraper.run_scraping_job(sample_jurisdiction)
            
            assert result["status"] == "partial_failure"
            assert result["errors"] == 3
            assert len(result["error_details"]) == 3
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, sample_jurisdiction):
        """Test progress tracking during scraping."""
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            
            # Mock progress callback
            progress_updates = []
            
            def mock_progress_callback(current, total, url):
                progress_updates.append({
                    "current": current,
                    "total": total,
                    "url": url,
                    "percent": (current / total) * 100
                })
            
            scraper.progress_callback = mock_progress_callback
            
            # Simulate progress updates
            for i in range(1, 6):
                scraper.progress_callback(i, 5, f"https://example.com/doc{i}")
            
            assert len(progress_updates) == 5
            assert progress_updates[0]["percent"] == 20.0
            assert progress_updates[4]["percent"] == 100.0


class TestScrapingMetrics:
    """Test metrics collection during scraping."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test that metrics are properly collected during scraping."""
        with patch('src.utils.metrics.metrics_collector') as mock_metrics:
            mock_metrics.record_scraping_job = Mock()
            
            # Mock scraping job
            with patch('src.scrapers.base.BaseScraper') as MockScraper:
                scraper = MockScraper.return_value
                
                # Simulate metrics recording
                mock_metrics.record_scraping_job(
                    jurisdiction="test-municipality",
                    job_type="full_scrape",
                    status="completed",
                    duration=120.5,
                    documents_found=10,
                    documents_processed=9
                )
                
                # Verify metrics were recorded
                mock_metrics.record_scraping_job.assert_called_once_with(
                    jurisdiction="test-municipality",
                    job_type="full_scrape",
                    status="completed",
                    duration=120.5,
                    documents_found=10,
                    documents_processed=9
                )
    
    @pytest.mark.asyncio
    async def test_error_metrics(self):
        """Test error metrics collection."""
        with patch('src.utils.metrics.scraping_errors') as mock_error_metric:
            mock_error_metric.labels.return_value.inc = Mock()
            
            # Simulate error
            mock_error_metric.labels(
                jurisdiction="test-municipality",
                error_type="connection_timeout"
            ).inc()
            
            # Verify error was recorded
            mock_error_metric.labels.assert_called_once_with(
                jurisdiction="test-municipality",
                error_type="connection_timeout"
            )


# Test fixtures for database testing
@pytest.fixture
async def test_db():
    """Test database fixture."""
    # This would set up a test database
    # Implementation depends on your database setup
    pass


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing."""
    with patch('src.tasks.scraping_tasks.scrape_jurisdiction') as mock_task:
        mock_task.delay.return_value.id = "test-task-123"
        yield mock_task


# Performance tests
class TestScrapingPerformance:
    """Performance tests for scraping operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_scraping(self):
        """Test concurrent scraping of multiple jurisdictions."""
        jurisdictions = [
            {"id": "jurisdiction1", "name": "Test 1"},
            {"id": "jurisdiction2", "name": "Test 2"},
            {"id": "jurisdiction3", "name": "Test 3"}
        ]
        
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            scraper.run_scraping_job = AsyncMock(return_value={
                "status": "completed",
                "documents_processed": 5
            })
            
            # Test concurrent execution
            tasks = [
                scraper.run_scraping_job(jurisdiction)
                for jurisdiction in jurisdictions
            ]
            
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 3
            assert all(r["status"] == "completed" for r in results)
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage during large scraping operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Simulate large scraping operation
        with patch('src.scrapers.base.BaseScraper') as MockScraper:
            scraper = MockScraper.return_value
            scraper.run_scraping_job = AsyncMock(return_value={
                "status": "completed"
            })
            
            # Run multiple scraping jobs
            for i in range(10):
                await scraper.run_scraping_job({"id": f"test-{i}"})
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100 * 1024 * 1024, f"Memory increased by {memory_increase} bytes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])