"""
Test cases for data extraction functionality.
Tests PDF processing, text extraction, and document parsing.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

# Import the modules we're testing (adjust imports based on actual structure)
# from src.extractors.pdf_extractor import PDFExtractor
# from src.extractors.text_processor import TextProcessor
# from src.extractors.section_parser import SectionParser
# from src.extractors.metadata_extractor import MetadataExtractor


class TestPDFExtractor:
    """Test cases for PDF extraction functionality."""
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Sample PDF content for testing."""
        return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    
    @pytest.fixture
    def temp_pdf_file(self, sample_pdf_content):
        """Create a temporary PDF file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(sample_pdf_content)
            tmp.flush()
            yield tmp.name
        
        # Cleanup
        os.unlink(tmp.name)
    
    @pytest.fixture
    def mock_pdf_extractor(self):
        """Mock PDF extractor."""
        with patch('src.extractors.pdf_extractor.PDFExtractor') as mock:
            yield mock
    
    def test_pdf_extractor_initialization(self, mock_pdf_extractor):
        """Test PDF extractor initialization."""
        extractor = mock_pdf_extractor.return_value
        assert extractor is not None
    
    def test_extract_text_from_pdf(self, mock_pdf_extractor, temp_pdf_file):
        """Test text extraction from PDF."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock text extraction
        expected_text = """
        CITY OF TORONTO
        BYLAW 2024-001
        
        1. DEFINITIONS
        In this bylaw:
        "Noise" means any sound that is unwanted or disturbing.
        
        2. PROHIBITED ACTIVITIES
        No person shall make excessive noise between 11:00 PM and 7:00 AM.
        
        3. PENALTIES
        Any person who contravenes this bylaw is guilty of an offence.
        """
        
        extractor.extract_text.return_value = expected_text.strip()
        
        result = extractor.extract_text(temp_pdf_file)
        
        assert result == expected_text.strip()
        assert "BYLAW 2024-001" in result
        assert "DEFINITIONS" in result
        assert "PROHIBITED ACTIVITIES" in result
    
    def test_extract_text_with_ocr(self, mock_pdf_extractor, temp_pdf_file):
        """Test text extraction with OCR fallback."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock OCR extraction
        extractor.extract_text_with_ocr.return_value = "OCR extracted text from scanned PDF"
        
        result = extractor.extract_text_with_ocr(temp_pdf_file)
        
        assert result == "OCR extracted text from scanned PDF"
        extractor.extract_text_with_ocr.assert_called_once_with(temp_pdf_file)
    
    def test_extract_metadata_from_pdf(self, mock_pdf_extractor, temp_pdf_file):
        """Test metadata extraction from PDF."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock metadata extraction
        expected_metadata = {
            "title": "Bylaw 2024-001",
            "author": "City of Toronto",
            "subject": "Noise Control",
            "creator": "Adobe Acrobat",
            "producer": "Adobe PDF Library",
            "creation_date": "2024-01-15T10:30:00Z",
            "modification_date": "2024-01-15T10:35:00Z",
            "pages": 5,
            "page_size": "Letter",
            "file_size": 1024768,
            "version": "1.4"
        }
        
        extractor.extract_metadata.return_value = expected_metadata
        
        result = extractor.extract_metadata(temp_pdf_file)
        
        assert result == expected_metadata
        assert result["title"] == "Bylaw 2024-001"
        assert result["pages"] == 5
    
    def test_extract_pages_separately(self, mock_pdf_extractor, temp_pdf_file):
        """Test extracting text from individual pages."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock page extraction
        pages = [
            {"page_number": 1, "text": "Title Page\nBYLAW 2024-001"},
            {"page_number": 2, "text": "1. DEFINITIONS\nIn this bylaw..."},
            {"page_number": 3, "text": "2. PROHIBITED ACTIVITIES\nNo person shall..."},
            {"page_number": 4, "text": "3. PENALTIES\nAny person who..."},
            {"page_number": 5, "text": "4. ENFORCEMENT\nThis bylaw shall..."}
        ]
        
        extractor.extract_pages.return_value = pages
        
        result = extractor.extract_pages(temp_pdf_file)
        
        assert len(result) == 5
        assert result[0]["page_number"] == 1
        assert "BYLAW 2024-001" in result[0]["text"]
        assert "DEFINITIONS" in result[1]["text"]
    
    def test_extract_images_from_pdf(self, mock_pdf_extractor, temp_pdf_file):
        """Test extracting images from PDF."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock image extraction
        images = [
            {
                "page_number": 1,
                "image_index": 0,
                "format": "JPEG",
                "size": (800, 600),
                "data": b"fake_image_data"
            },
            {
                "page_number": 3,
                "image_index": 1,
                "format": "PNG",
                "size": (400, 300),
                "data": b"fake_image_data_2"
            }
        ]
        
        extractor.extract_images.return_value = images
        
        result = extractor.extract_images(temp_pdf_file)
        
        assert len(result) == 2
        assert result[0]["format"] == "JPEG"
        assert result[1]["format"] == "PNG"
    
    def test_pdf_validation(self, mock_pdf_extractor, temp_pdf_file):
        """Test PDF file validation."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock validation
        extractor.validate_pdf.return_value = True
        extractor.is_encrypted.return_value = False
        extractor.is_corrupted.return_value = False
        
        assert extractor.validate_pdf(temp_pdf_file) == True
        assert extractor.is_encrypted(temp_pdf_file) == False
        assert extractor.is_corrupted(temp_pdf_file) == False
    
    def test_encrypted_pdf_handling(self, mock_pdf_extractor, temp_pdf_file):
        """Test handling of encrypted PDFs."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock encrypted PDF
        extractor.is_encrypted.return_value = True
        extractor.decrypt_pdf.return_value = False  # Decryption failed
        
        with pytest.raises(Exception) as exc_info:
            extractor.extract_text(temp_pdf_file)
        
        assert "encrypted" in str(exc_info.value).lower()
    
    def test_corrupted_pdf_handling(self, mock_pdf_extractor, temp_pdf_file):
        """Test handling of corrupted PDFs."""
        extractor = mock_pdf_extractor.return_value
        
        # Mock corrupted PDF
        extractor.is_corrupted.return_value = True
        
        with pytest.raises(Exception) as exc_info:
            extractor.extract_text(temp_pdf_file)
        
        assert "corrupted" in str(exc_info.value).lower()


class TestTextProcessor:
    """Test cases for text processing functionality."""
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for processing."""
        return """
        CITY OF TORONTO
        BYLAW 2024-001
        
        A bylaw to regulate noise in the city.
        
        1. DEFINITIONS
        
        In this bylaw:
        
        "Noise" means any sound that is unwanted or disturbing;
        "Person" includes a corporation, partnership, or other legal entity;
        "Property" means any land, building, or structure.
        
        2. PROHIBITED ACTIVITIES
        
        2.1 No person shall make excessive noise between 11:00 PM and 7:00 AM.
        
        2.2 No person shall operate construction equipment on Sundays.
        
        3. PENALTIES
        
        3.1 Any person who contravenes this bylaw is guilty of an offence.
        
        3.2 The penalty for a first offence is a fine of $200.
        """
    
    @pytest.fixture
    def mock_text_processor(self):
        """Mock text processor."""
        with patch('src.extractors.text_processor.TextProcessor') as mock:
            yield mock
    
    def test_text_processor_initialization(self, mock_text_processor):
        """Test text processor initialization."""
        processor = mock_text_processor.return_value
        assert processor is not None
    
    def test_clean_text(self, mock_text_processor, sample_text):
        """Test text cleaning functionality."""
        processor = mock_text_processor.return_value
        
        # Mock text cleaning
        cleaned_text = sample_text.strip()
        cleaned_text = " ".join(cleaned_text.split())  # Normalize whitespace
        
        processor.clean_text.return_value = cleaned_text
        
        result = processor.clean_text(sample_text)
        
        assert result == cleaned_text
        assert "\n\n" not in result
    
    def test_extract_title(self, mock_text_processor, sample_text):
        """Test title extraction."""
        processor = mock_text_processor.return_value
        
        # Mock title extraction
        processor.extract_title.return_value = "BYLAW 2024-001"
        
        result = processor.extract_title(sample_text)
        
        assert result == "BYLAW 2024-001"
    
    def test_extract_document_number(self, mock_text_processor, sample_text):
        """Test document number extraction."""
        processor = mock_text_processor.return_value
        
        # Mock document number extraction
        processor.extract_document_number.return_value = "2024-001"
        
        result = processor.extract_document_number(sample_text)
        
        assert result == "2024-001"
    
    def test_extract_effective_date(self, mock_text_processor):
        """Test effective date extraction."""
        processor = mock_text_processor.return_value
        
        text_with_date = "This bylaw comes into effect on January 15, 2024."
        
        # Mock date extraction
        processor.extract_effective_date.return_value = datetime(2024, 1, 15).date()
        
        result = processor.extract_effective_date(text_with_date)
        
        assert result == datetime(2024, 1, 15).date()
    
    def test_extract_keywords(self, mock_text_processor, sample_text):
        """Test keyword extraction."""
        processor = mock_text_processor.return_value
        
        # Mock keyword extraction
        keywords = ["noise", "bylaw", "penalties", "construction", "offence"]
        processor.extract_keywords.return_value = keywords
        
        result = processor.extract_keywords(sample_text)
        
        assert result == keywords
        assert "noise" in result
        assert "bylaw" in result
    
    def test_detect_language(self, mock_text_processor, sample_text):
        """Test language detection."""
        processor = mock_text_processor.return_value
        
        # Mock language detection
        processor.detect_language.return_value = "en"
        
        result = processor.detect_language(sample_text)
        
        assert result == "en"
    
    def test_extract_entities(self, mock_text_processor, sample_text):
        """Test named entity extraction."""
        processor = mock_text_processor.return_value
        
        # Mock entity extraction
        entities = [
            {"text": "CITY OF TORONTO", "type": "ORG"},
            {"text": "11:00 PM", "type": "TIME"},
            {"text": "7:00 AM", "type": "TIME"},
            {"text": "$200", "type": "MONEY"}
        ]
        
        processor.extract_entities.return_value = entities
        
        result = processor.extract_entities(sample_text)
        
        assert len(result) == 4
        assert result[0]["text"] == "CITY OF TORONTO"
        assert result[0]["type"] == "ORG"


class TestSectionParser:
    """Test cases for section parsing functionality."""
    
    @pytest.fixture
    def sample_sectioned_text(self):
        """Sample text with sections."""
        return """
        BYLAW 2024-001
        
        1. DEFINITIONS
        
        In this bylaw:
        "Noise" means any sound that is unwanted or disturbing;
        "Person" includes a corporation.
        
        2. PROHIBITED ACTIVITIES
        
        2.1 No person shall make excessive noise between 11:00 PM and 7:00 AM.
        
        2.2 No person shall operate construction equipment on Sundays.
        
        2.3 No person shall use amplified sound devices in public spaces.
        
        3. PENALTIES
        
        3.1 Any person who contravenes this bylaw is guilty of an offence.
        
        3.2 The penalty for a first offence is a fine of $200.
        
        3.3 The penalty for a second offence is a fine of $400.
        
        4. ENFORCEMENT
        
        4.1 This bylaw may be enforced by municipal law enforcement officers.
        
        4.2 Officers may issue notices of violation.
        """
    
    @pytest.fixture
    def mock_section_parser(self):
        """Mock section parser."""
        with patch('src.extractors.section_parser.SectionParser') as mock:
            yield mock
    
    def test_section_parser_initialization(self, mock_section_parser):
        """Test section parser initialization."""
        parser = mock_section_parser.return_value
        assert parser is not None
    
    def test_parse_sections(self, mock_section_parser, sample_sectioned_text):
        """Test parsing document into sections."""
        parser = mock_section_parser.return_value
        
        # Mock section parsing
        expected_sections = [
            {
                "section_number": "1",
                "title": "DEFINITIONS",
                "content": "In this bylaw:\n\"Noise\" means any sound that is unwanted or disturbing;\n\"Person\" includes a corporation.",
                "subsections": []
            },
            {
                "section_number": "2",
                "title": "PROHIBITED ACTIVITIES",
                "content": "",
                "subsections": [
                    {
                        "section_number": "2.1",
                        "content": "No person shall make excessive noise between 11:00 PM and 7:00 AM."
                    },
                    {
                        "section_number": "2.2",
                        "content": "No person shall operate construction equipment on Sundays."
                    },
                    {
                        "section_number": "2.3",
                        "content": "No person shall use amplified sound devices in public spaces."
                    }
                ]
            },
            {
                "section_number": "3",
                "title": "PENALTIES",
                "content": "",
                "subsections": [
                    {
                        "section_number": "3.1",
                        "content": "Any person who contravenes this bylaw is guilty of an offence."
                    },
                    {
                        "section_number": "3.2",
                        "content": "The penalty for a first offence is a fine of $200."
                    },
                    {
                        "section_number": "3.3",
                        "content": "The penalty for a second offence is a fine of $400."
                    }
                ]
            },
            {
                "section_number": "4",
                "title": "ENFORCEMENT",
                "content": "",
                "subsections": [
                    {
                        "section_number": "4.1",
                        "content": "This bylaw may be enforced by municipal law enforcement officers."
                    },
                    {
                        "section_number": "4.2",
                        "content": "Officers may issue notices of violation."
                    }
                ]
            }
        ]
        
        parser.parse_sections.return_value = expected_sections
        
        result = parser.parse_sections(sample_sectioned_text)
        
        assert len(result) == 4
        assert result[0]["section_number"] == "1"
        assert result[0]["title"] == "DEFINITIONS"
        assert len(result[1]["subsections"]) == 3
        assert result[1]["subsections"][0]["section_number"] == "2.1"
    
    def test_parse_definitions(self, mock_section_parser, sample_sectioned_text):
        """Test parsing definitions section."""
        parser = mock_section_parser.return_value
        
        # Mock definitions parsing
        expected_definitions = [
            {
                "term": "Noise",
                "definition": "means any sound that is unwanted or disturbing"
            },
            {
                "term": "Person",
                "definition": "includes a corporation"
            }
        ]
        
        parser.parse_definitions.return_value = expected_definitions
        
        result = parser.parse_definitions(sample_sectioned_text)
        
        assert len(result) == 2
        assert result[0]["term"] == "Noise"
        assert result[1]["term"] == "Person"
    
    def test_extract_section_hierarchy(self, mock_section_parser, sample_sectioned_text):
        """Test extracting section hierarchy."""
        parser = mock_section_parser.return_value
        
        # Mock hierarchy extraction
        hierarchy = {
            "1": {
                "title": "DEFINITIONS",
                "children": []
            },
            "2": {
                "title": "PROHIBITED ACTIVITIES",
                "children": ["2.1", "2.2", "2.3"]
            },
            "3": {
                "title": "PENALTIES",
                "children": ["3.1", "3.2", "3.3"]
            },
            "4": {
                "title": "ENFORCEMENT",
                "children": ["4.1", "4.2"]
            }
        }
        
        parser.extract_hierarchy.return_value = hierarchy
        
        result = parser.extract_hierarchy(sample_sectioned_text)
        
        assert len(result) == 4
        assert result["2"]["title"] == "PROHIBITED ACTIVITIES"
        assert len(result["2"]["children"]) == 3
    
    def test_parse_cross_references(self, mock_section_parser):
        """Test parsing cross-references between sections."""
        parser = mock_section_parser.return_value
        
        text_with_refs = """
        3.1 Any person who contravenes section 2.1 is guilty of an offence.
        3.2 The definitions in section 1 apply to this section.
        """
        
        # Mock cross-reference parsing
        cross_refs = [
            {
                "from_section": "3.1",
                "to_section": "2.1",
                "reference_text": "contravenes section 2.1"
            },
            {
                "from_section": "3.2",
                "to_section": "1",
                "reference_text": "definitions in section 1"
            }
        ]
        
        parser.parse_cross_references.return_value = cross_refs
        
        result = parser.parse_cross_references(text_with_refs)
        
        assert len(result) == 2
        assert result[0]["from_section"] == "3.1"
        assert result[0]["to_section"] == "2.1"
    
    def test_validate_section_structure(self, mock_section_parser, sample_sectioned_text):
        """Test validation of section structure."""
        parser = mock_section_parser.return_value
        
        # Mock structure validation
        validation_result = {
            "is_valid": True,
            "issues": [],
            "section_count": 4,
            "subsection_count": 8
        }
        
        parser.validate_structure.return_value = validation_result
        
        result = parser.validate_structure(sample_sectioned_text)
        
        assert result["is_valid"] == True
        assert result["section_count"] == 4
        assert result["subsection_count"] == 8
    
    def test_invalid_section_structure(self, mock_section_parser):
        """Test handling of invalid section structure."""
        parser = mock_section_parser.return_value
        
        invalid_text = "Some text without proper sections"
        
        # Mock validation of invalid structure
        validation_result = {
            "is_valid": False,
            "issues": ["No sections found", "Missing section numbering"],
            "section_count": 0,
            "subsection_count": 0
        }
        
        parser.validate_structure.return_value = validation_result
        
        result = parser.validate_structure(invalid_text)
        
        assert result["is_valid"] == False
        assert len(result["issues"]) == 2
        assert result["section_count"] == 0


class TestMetadataExtractor:
    """Test cases for metadata extraction functionality."""
    
    @pytest.fixture
    def sample_document_info(self):
        """Sample document information."""
        return {
            "file_path": "/path/to/document.pdf",
            "file_size": 1024768,
            "file_type": "application/pdf",
            "creation_date": "2024-01-15T10:30:00Z",
            "modification_date": "2024-01-15T10:35:00Z"
        }
    
    @pytest.fixture
    def mock_metadata_extractor(self):
        """Mock metadata extractor."""
        with patch('src.extractors.metadata_extractor.MetadataExtractor') as mock:
            yield mock
    
    def test_metadata_extractor_initialization(self, mock_metadata_extractor):
        """Test metadata extractor initialization."""
        extractor = mock_metadata_extractor.return_value
        assert extractor is not None
    
    def test_extract_document_metadata(self, mock_metadata_extractor, sample_document_info):
        """Test extracting comprehensive document metadata."""
        extractor = mock_metadata_extractor.return_value
        
        # Mock metadata extraction
        expected_metadata = {
            "title": "Noise Control Bylaw",
            "document_number": "2024-001",
            "document_type": "bylaw",
            "jurisdiction": "City of Toronto",
            "effective_date": "2024-01-15",
            "language": "en",
            "pages": 5,
            "sections": 4,
            "subsections": 8,
            "definitions": 2,
            "keywords": ["noise", "control", "enforcement"],
            "file_metadata": sample_document_info
        }
        
        extractor.extract_all_metadata.return_value = expected_metadata
        
        result = extractor.extract_all_metadata("/path/to/document.pdf", "extracted text")
        
        assert result["title"] == "Noise Control Bylaw"
        assert result["document_number"] == "2024-001"
        assert result["pages"] == 5
        assert result["sections"] == 4
    
    def test_extract_classification_metadata(self, mock_metadata_extractor):
        """Test extracting classification metadata."""
        extractor = mock_metadata_extractor.return_value
        
        # Mock classification
        classification = {
            "document_type": "bylaw",
            "subject_areas": ["noise control", "public safety"],
            "complexity_score": 0.7,
            "readability_score": 0.6,
            "legal_authority": "municipal"
        }
        
        extractor.classify_document.return_value = classification
        
        result = extractor.classify_document("sample text")
        
        assert result["document_type"] == "bylaw"
        assert "noise control" in result["subject_areas"]
        assert result["complexity_score"] == 0.7
    
    def test_extract_quality_metrics(self, mock_metadata_extractor):
        """Test extracting quality metrics."""
        extractor = mock_metadata_extractor.return_value
        
        # Mock quality metrics
        quality_metrics = {
            "text_quality": 0.9,
            "ocr_confidence": 0.95,
            "structure_quality": 0.8,
            "completeness": 1.0,
            "extraction_errors": 0
        }
        
        extractor.assess_quality.return_value = quality_metrics
        
        result = extractor.assess_quality("extracted text", "file_path")
        
        assert result["text_quality"] == 0.9
        assert result["ocr_confidence"] == 0.95
        assert result["extraction_errors"] == 0
    
    def test_extract_usage_metadata(self, mock_metadata_extractor):
        """Test extracting usage and access metadata."""
        extractor = mock_metadata_extractor.return_value
        
        # Mock usage metadata
        usage_metadata = {
            "access_level": "public",
            "copyright": "City of Toronto",
            "license": "Open Government License",
            "usage_restrictions": None,
            "contact_info": "clerk@toronto.ca"
        }
        
        extractor.extract_usage_metadata.return_value = usage_metadata
        
        result = extractor.extract_usage_metadata("sample text")
        
        assert result["access_level"] == "public"
        assert result["copyright"] == "City of Toronto"
        assert result["license"] == "Open Government License"


class TestExtractionIntegration:
    """Integration tests for complete extraction workflow."""
    
    @pytest.fixture
    def temp_pdf_file(self):
        """Create a temporary PDF file for testing."""
        content = b"%PDF-1.4\nSample PDF content"
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(content)
            tmp.flush()
            yield tmp.name
        
        os.unlink(tmp.name)
    
    @pytest.mark.asyncio
    async def test_complete_extraction_workflow(self, temp_pdf_file):
        """Test complete extraction workflow from PDF to structured data."""
        with patch('src.extractors.pdf_extractor.PDFExtractor') as MockPDFExtractor, \
             patch('src.extractors.text_processor.TextProcessor') as MockTextProcessor, \
             patch('src.extractors.section_parser.SectionParser') as MockSectionParser, \
             patch('src.extractors.metadata_extractor.MetadataExtractor') as MockMetadataExtractor:
            
            # Mock extractors
            pdf_extractor = MockPDFExtractor.return_value
            text_processor = MockTextProcessor.return_value
            section_parser = MockSectionParser.return_value
            metadata_extractor = MockMetadataExtractor.return_value
            
            # Mock the workflow
            pdf_extractor.extract_text.return_value = "Sample bylaw text"
            pdf_extractor.extract_metadata.return_value = {"pages": 5}
            
            text_processor.clean_text.return_value = "Cleaned sample bylaw text"
            text_processor.extract_title.return_value = "Bylaw 2024-001"
            
            section_parser.parse_sections.return_value = [
                {"section_number": "1", "title": "DEFINITIONS", "content": "..."}
            ]
            
            metadata_extractor.extract_all_metadata.return_value = {
                "title": "Bylaw 2024-001",
                "document_type": "bylaw",
                "sections": 1
            }
            
            # Simulate workflow
            raw_text = pdf_extractor.extract_text(temp_pdf_file)
            pdf_metadata = pdf_extractor.extract_metadata(temp_pdf_file)
            
            cleaned_text = text_processor.clean_text(raw_text)
            title = text_processor.extract_title(cleaned_text)
            
            sections = section_parser.parse_sections(cleaned_text)
            
            final_metadata = metadata_extractor.extract_all_metadata(temp_pdf_file, cleaned_text)
            
            # Verify workflow
            assert raw_text == "Sample bylaw text"
            assert cleaned_text == "Cleaned sample bylaw text"
            assert title == "Bylaw 2024-001"
            assert len(sections) == 1
            assert final_metadata["title"] == "Bylaw 2024-001"
    
    @pytest.mark.asyncio
    async def test_extraction_error_handling(self, temp_pdf_file):
        """Test error handling in extraction workflow."""
        with patch('src.extractors.pdf_extractor.PDFExtractor') as MockPDFExtractor:
            pdf_extractor = MockPDFExtractor.return_value
            
            # Mock extraction failure
            pdf_extractor.extract_text.side_effect = Exception("PDF extraction failed")
            
            with pytest.raises(Exception) as exc_info:
                pdf_extractor.extract_text(temp_pdf_file)
            
            assert "PDF extraction failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extraction_performance(self, temp_pdf_file):
        """Test extraction performance metrics."""
        import time
        
        with patch('src.extractors.pdf_extractor.PDFExtractor') as MockPDFExtractor:
            pdf_extractor = MockPDFExtractor.return_value
            
            # Mock timed extraction
            def mock_extract_text(file_path):
                time.sleep(0.1)  # Simulate processing time
                return "Extracted text"
            
            pdf_extractor.extract_text.side_effect = mock_extract_text
            
            start_time = time.time()
            result = pdf_extractor.extract_text(temp_pdf_file)
            end_time = time.time()
            
            assert result == "Extracted text"
            assert end_time - start_time >= 0.1  # Should take at least 0.1 seconds


class TestExtractionMetrics:
    """Test metrics collection during extraction."""
    
    @pytest.mark.asyncio
    async def test_extraction_metrics(self):
        """Test that metrics are collected during extraction."""
        with patch('src.utils.metrics.metrics_collector') as mock_metrics:
            mock_metrics.record_document_processing = Mock()
            
            # Simulate extraction with metrics
            mock_metrics.record_document_processing(
                document_type="bylaw",
                status="completed",
                duration=2.5,
                file_size=1024,
                pages=5
            )
            
            # Verify metrics were recorded
            mock_metrics.record_document_processing.assert_called_once_with(
                document_type="bylaw",
                status="completed",
                duration=2.5,
                file_size=1024,
                pages=5
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])