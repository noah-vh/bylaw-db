# Bylaw Database Scraping Infrastructure

This document describes the comprehensive web scraping infrastructure built for the bylaw-db project, with a strong focus on source document preservation for liability protection.

## Architecture Overview

The scraping infrastructure consists of five main components:

1. **Base Scraper Class** (`src/scrapers/base_scraper.py`)
2. **Document Preservation Module** (`src/storage/document_preserver.py`)
3. **Municipality Scraper** (`src/scrapers/municipality_scraper.py`)
4. **Job Manager** (`src/scrapers/job_manager.py`)
5. **ADU Extractor** (`src/scrapers/extractors/adu_extractor.py`)

## Key Features

### Source Document Preservation
- **Complete HTML preservation** with all assets
- **Full-page screenshots** using Selenium
- **PDF downloads** with metadata
- **Content integrity verification** using SHA256 hashing
- **Metadata capture** including HTTP headers, timestamps, and IP addresses
- **Supabase Storage integration** for reliable document archival

### Liability Protection
- Every piece of extracted data is **traceable back to its source**
- Complete audit trail with timestamps and user attribution
- Immutable document versions with change tracking
- Confidence scoring for all extracted information
- Source text attribution for each extracted fact

### Reliability & Error Handling
- **Retry mechanisms** with exponential backoff
- **Comprehensive error logging** with stack traces
- **Job status tracking** and progress monitoring
- **Failure recovery** with configurable retry limits
- **Rate limiting** to respect target websites

## Component Details

### 1. Base Scraper Class

The `BaseScraper` class provides core functionality for all scrapers:

```python
from backend.src.scrapers.base_scraper import BaseScraper

class CustomScraper(BaseScraper):
    def get_target_urls(self):
        return ['https://example.com/bylaws']
    
    def parse_document(self, content, metadata):
        # Custom parsing logic
        return extracted_items
```

**Key Features:**
- Selenium WebDriver integration for JavaScript-heavy sites
- Full-page screenshot capture
- Asset preservation (images, CSS, JS)
- Content hashing for integrity verification
- Metadata extraction from HTML pages

### 2. Document Preservation Module

The `DocumentPreserver` class handles comprehensive document archival:

```python
from backend.src.storage.document_preserver import DocumentPreserver

preserver = DocumentPreserver(supabase_client, db_pool)

result = await preserver.preserve_document(
    municipality_id=municipality_id,
    url=url,
    document_type='webpage',
    scraper_version='1.0.0',
    content=html_content,
    metadata=metadata,
    screenshot_path=screenshot_path,
    assets=assets
)
```

**Storage Structure:**
```
source-documents/
├── {municipality_id}/
│   ├── {domain}/
│   │   ├── {timestamp}/
│   │   │   ├── page.html
│   │   │   ├── screenshot.png
│   │   │   ├── document.pdf
│   │   │   ├── metadata.json
│   │   │   └── assets/
│   │   │       ├── image1.jpg
│   │   │       ├── style.css
│   │   │       └── script.js
```

### 3. Municipality Scraper

The `MunicipalityScraper` demonstrates how to implement municipality-specific scrapers:

```python
from backend.src.scrapers.municipality_scraper import MunicipalityScraper

config = {
    'target_urls': ['https://city.example.com/bylaws'],
    'requires_javascript': False,
    'selectors': {
        'bylaw_links': 'a[href*="bylaw"]',
        'bylaw_title': 'h1.title',
        'bylaw_content': '.content'
    }
}

scraper = MunicipalityScraper(municipality_id, config)
results = scraper.scrape()
```

**Features:**
- Automatic link discovery and pagination handling
- Bylaw categorization and metadata extraction
- PDF document handling
- Configurable CSS selectors for different website structures

### 4. Job Manager

The `ScrapingJobManager` orchestrates scraping operations using Celery:

```python
from backend.src.scrapers.job_manager import schedule_municipality_scraping

# Schedule scraping for a municipality
result = schedule_municipality_scraping.delay(municipality_id, 'user_123')
```

**Celery Tasks:**
- `scrape_municipality`: Main scraping task
- `schedule_municipality_scraping`: Schedule scraping based on configuration
- `batch_scrape_municipalities`: Batch processing for multiple municipalities
- `cleanup_old_jobs`: Maintenance task for cleaning old job records

### 5. ADU Extractor

The `ADUExtractor` specializes in extracting ADU requirements with confidence scoring:

```python
from backend.src.scrapers.extractors.adu_extractor import ADUExtractor

extractor = ADUExtractor()
requirements = extractor.extract_adu_requirements(bylaw_text, metadata)

if requirements['is_adu_related']:
    print(f"Confidence: {requirements['overall_confidence']}")
    print(f"Max height: {requirements['requirements']['max_height_m']}m")
    print(f"Max floor area: {requirements['requirements']['max_floor_area_sqm']}sqm")
```

**Extracted Requirements:**
- Maximum height (converted to meters)
- Maximum floor area (converted to square meters)
- Minimum lot size requirements
- Setback requirements (front, rear, side)
- Maximum number of units
- Parking space requirements
- Owner occupancy requirements
- Other specific requirements

## Database Schema

The scraping infrastructure integrates with a comprehensive database schema:

### Source Documents Table
```sql
CREATE TABLE source_documents (
    id UUID PRIMARY KEY,
    municipality_id UUID REFERENCES municipalities(id),
    document_url TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,
    scraper_version VARCHAR(20) NOT NULL,
    raw_html_path TEXT,
    pdf_path TEXT,
    screenshot_path TEXT,
    content_hash VARCHAR(64),
    preservation_status VARCHAR(50) DEFAULT 'pending'
);
```

### Bylaw Versions Table
```sql
CREATE TABLE bylaw_versions (
    id UUID PRIMARY KEY,
    bylaw_id UUID REFERENCES bylaws(id),
    content JSONB NOT NULL,
    extracted_requirements JSONB,
    confidence_scores JSONB,
    source_document_id UUID REFERENCES source_documents(id),
    extraction_method VARCHAR(100),
    is_current BOOLEAN DEFAULT false
);
```

## Usage Examples

### Basic Scraping Workflow

```python
import asyncio
from backend.src.scrapers.municipality_scraper import MunicipalityScraper
from backend.src.storage.document_preserver import DocumentPreserver

async def scrape_municipality():
    # Initialize components
    scraper = MunicipalityScraper(municipality_id, config)
    preserver = DocumentPreserver(supabase_client, db_pool)
    
    # Perform scraping
    results = scraper.scrape()
    
    # Preserve documents
    for doc in results['documents']:
        await preserver.preserve_document(
            municipality_id=municipality_id,
            url=doc['url'],
            document_type='webpage',
            scraper_version='1.0.0',
            content=doc['content'],
            metadata=doc['metadata']
        )
```

### Job Scheduling

```python
from backend.src.scrapers.job_manager import schedule_municipality_scraping

# Schedule immediate scraping
result = schedule_municipality_scraping.delay(municipality_id, 'user_123')

# Check job status
job_status = result.get()
print(f"Job completed: {job_status}")
```

### ADU Requirement Extraction

```python
from backend.src.scrapers.extractors.adu_extractor import ADUExtractor

extractor = ADUExtractor()
requirements = extractor.extract_adu_requirements(bylaw_text, metadata)

# Validate extracted data
validation = extractor.validate_extracted_data(requirements)
if validation['warnings']:
    print(f"Validation warnings: {validation['warnings']}")
```

## Configuration

### Environment Variables
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bylaw_db
DB_USER=postgres
DB_PASSWORD=your_password

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Scraping
MAX_CONCURRENT_SCRAPERS=5
REQUEST_DELAY=1.0
```

### Scraping Configuration
```python
config = {
    'target_urls': [
        'https://municipality.ca/bylaws',
        'https://municipality.ca/zoning'
    ],
    'discovery_urls': [
        'https://municipality.ca/bylaws/list'
    ],
    'requires_javascript': False,
    'selectors': {
        'bylaw_links': 'a[href*="bylaw"]',
        'bylaw_title': 'h1, h2.title',
        'bylaw_content': '.content, article',
        'pagination': '.pagination a'
    },
    'custom_headers': {
        'User-Agent': 'BylawDB/1.0'
    }
}
```

## Running the Infrastructure

### Start Celery Worker
```bash
celery -A backend.src.scrapers.job_manager.celery_app worker --loglevel=info
```

### Start Celery Beat (for scheduled tasks)
```bash
celery -A backend.src.scrapers.job_manager.celery_app beat --loglevel=info
```

### Monitor Jobs
```bash
celery -A backend.src.scrapers.job_manager.celery_app flower
```

## Error Handling & Monitoring

### Job Status Tracking
All scraping jobs are tracked in the database with detailed status information:
- Job start/end times
- Documents found/processed/changed
- Error messages and details
- Celery task IDs for monitoring

### Failure Recovery
- Automatic retries with exponential backoff
- Configuration-based failure limits
- Detailed error logging with stack traces
- Graceful degradation when services are unavailable

### Monitoring & Alerting
- Prometheus metrics for job success/failure rates
- Structured logging with correlation IDs
- Database triggers for audit logging
- Storage quota monitoring

## Security Considerations

### Rate Limiting
- Configurable delays between requests
- Respect for robots.txt files
- User-Agent identification
- IP address tracking

### Data Protection
- Secure storage of scraped content
- Encryption of sensitive configuration
- Access control for preserved documents
- Regular cleanup of old data

## Future Enhancements

1. **Machine Learning Integration**: Use ML models to improve extraction accuracy
2. **Distributed Scraping**: Scale across multiple worker nodes
3. **Real-time Change Detection**: Monitor websites for changes
4. **API Integration**: Support for municipality APIs where available
5. **Advanced Validation**: Cross-reference extracted data with known standards

## Support

For questions about the scraping infrastructure, please refer to:
- Database schema documentation in `/database/schemas/`
- API documentation for integration endpoints
- Example usage in `/backend/examples/`
- Test cases in `/backend/tests/`