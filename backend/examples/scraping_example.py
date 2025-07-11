"""
Example of how to use the scraping infrastructure.
"""

import asyncio
import asyncpg
from supabase import create_client

from backend.src.scrapers.municipality_scraper import MunicipalityScraper
from backend.src.storage.document_preserver import DocumentPreserver
from backend.src.scrapers.extractors.adu_extractor import ADUExtractor
from backend.src.utils.config import get_settings


async def example_scraping_workflow():
    """Example workflow showing how to use the scraping infrastructure."""
    settings = get_settings()
    
    # Initialize database connection
    db_pool = await asyncpg.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    
    # Initialize Supabase client
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Initialize document preserver
    document_preserver = DocumentPreserver(supabase, db_pool)
    
    # Initialize ADU extractor
    adu_extractor = ADUExtractor()
    
    # Example municipality configuration
    municipality_id = "123e4567-e89b-12d3-a456-426614174000"
    scraper_config = {
        'target_urls': [
            'https://example-municipality.ca/bylaws',
            'https://example-municipality.ca/zoning'
        ],
        'requires_javascript': False,
        'selectors': {
            'bylaw_links': 'a[href*="bylaw"]',
            'bylaw_title': 'h1.title',
            'bylaw_content': '.content'
        }
    }
    
    # Create scraper instance
    scraper = MunicipalityScraper(municipality_id, scraper_config)
    
    try:
        # Perform scraping
        print("Starting scraping process...")
        scraping_results = scraper.scrape()
        
        print(f"Found {len(scraping_results['documents'])} documents")
        
        # Process each document
        for doc in scraping_results['documents']:
            print(f"\nProcessing document: {doc['url']}")
            
            # Preserve the document
            preservation_result = await document_preserver.preserve_document(
                municipality_id=municipality_id,
                url=doc['url'],
                document_type='webpage',
                scraper_version='1.0.0',
                content=doc.get('content', ''),
                metadata=doc.get('metadata', {}),
                screenshot_path=doc.get('screenshot_path'),
                assets=doc.get('assets', [])
            )
            
            if preservation_result['success']:
                print(f"Document preserved successfully: {preservation_result['document_id']}")
                
                # Extract ADU requirements if applicable
                for item in doc.get('extracted_items', []):
                    if item.get('type') == 'bylaw':
                        adu_requirements = adu_extractor.extract_adu_requirements(
                            item.get('full_text', ''),
                            {'url': doc['url']}
                        )
                        
                        if adu_requirements.get('is_adu_related'):
                            print(f"Found ADU requirements with confidence: {adu_requirements['overall_confidence']}")
                            
                            # Validate the extracted data
                            validation = adu_extractor.validate_extracted_data(adu_requirements)
                            if validation['warnings']:
                                print(f"Validation warnings: {validation['warnings']}")
                            
                            # Here you would save the ADU requirements to the database
                            # await save_adu_requirements(adu_requirements, preservation_result['document_id'])
                            
            else:
                print(f"Document preservation failed: {preservation_result['errors']}")
        
        print("\nScraping process completed!")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        
    finally:
        # Clean up
        scraper.cleanup()
        await db_pool.close()


async def example_job_scheduling():
    """Example of how to schedule scraping jobs."""
    from backend.src.scrapers.job_manager import schedule_municipality_scraping
    
    # Schedule scraping for a municipality
    municipality_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # This would typically be called from a web API or scheduled task
    result = schedule_municipality_scraping.delay(municipality_id, 'api_user_123')
    
    print(f"Scheduled scraping job: {result.id}")


if __name__ == "__main__":
    # Run the example workflow
    asyncio.run(example_scraping_workflow())
    
    # Example of job scheduling (commented out as it requires Celery worker)
    # asyncio.run(example_job_scheduling())