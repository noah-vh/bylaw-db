"""
Base scraper class with comprehensive source document preservation capabilities.
Ensures all scraped content is traceable back to its source for liability protection.
"""

import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for all municipality scrapers with built-in source preservation.
    """
    
    def __init__(self, municipality_id: str, config: Dict[str, Any]):
        self.municipality_id = municipality_id
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; BylawDB/1.0; +https://bylawdb.com/bot)'
        })
        
        # Selenium driver (initialized on demand)
        self._driver = None
        self.scraper_version = "1.0.0"
        
        # Configure custom headers if provided
        if custom_headers := config.get('custom_headers'):
            self.session.headers.update(custom_headers)
    
    def get_driver(self) -> webdriver.Chrome:
        """Initialize and return Selenium WebDriver (lazy loading)."""
        if self._driver is None:
            options = ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            # Enable full page screenshot capability
            options.add_argument('--force-device-scale-factor=1')
            
            self._driver = webdriver.Chrome(options=options)
            self._driver.set_page_load_timeout(30)
            
        return self._driver
    
    def cleanup(self):
        """Clean up resources."""
        if self._driver:
            self._driver.quit()
            self._driver = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def fetch_page(self, url: str, use_javascript: bool = False) -> Tuple[str, Dict[str, Any]]:
        """
        Fetch a webpage with full metadata capture.
        
        Args:
            url: URL to fetch
            use_javascript: Whether to use Selenium for JavaScript rendering
            
        Returns:
            Tuple of (content, metadata)
        """
        metadata = {
            'url': url,
            'fetched_at': datetime.utcnow().isoformat(),
            'scraper_version': self.scraper_version,
            'method': 'selenium' if use_javascript else 'requests'
        }
        
        if use_javascript:
            return self._fetch_with_selenium(url, metadata)
        else:
            return self._fetch_with_requests(url, metadata)
    
    def _fetch_with_requests(self, url: str, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Fetch page using requests library."""
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        metadata.update({
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'response_time_ms': int(response.elapsed.total_seconds() * 1000),
            'encoding': response.encoding,
            'content_length': len(response.content)
        })
        
        return response.text, metadata
    
    def _fetch_with_selenium(self, url: str, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Fetch page using Selenium for JavaScript rendering."""
        driver = self.get_driver()
        start_time = time.time()
        
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for dynamic content
        time.sleep(2)
        
        # Get page source
        content = driver.page_source
        
        # Capture performance metrics
        performance_data = driver.execute_script(
            "return window.performance.timing.toJSON()"
        )
        
        metadata.update({
            'status_code': 200,  # Selenium doesn't provide status codes
            'response_time_ms': int((time.time() - start_time) * 1000),
            'performance_metrics': performance_data,
            'page_title': driver.title,
            'final_url': driver.current_url,
            'content_length': len(content)
        })
        
        return content, metadata
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content for integrity verification."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def capture_screenshot(self, url: str, output_path: Path) -> Dict[str, Any]:
        """
        Capture full-page screenshot of the URL.
        
        Args:
            url: URL to capture
            output_path: Path to save screenshot
            
        Returns:
            Screenshot metadata
        """
        driver = self.get_driver()
        driver.get(url)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        
        # Get full page dimensions
        total_height = driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)"
        )
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Set window size to capture full page
        driver.set_window_size(1920, total_height)
        time.sleep(1)
        
        # Capture screenshot
        driver.save_screenshot(str(output_path))
        
        # Reset window size
        driver.set_window_size(1920, viewport_height)
        
        return {
            'path': str(output_path),
            'captured_at': datetime.utcnow().isoformat(),
            'dimensions': {
                'width': 1920,
                'height': total_height
            },
            'file_size': output_path.stat().st_size
        }
    
    def download_pdf(self, url: str, output_path: Path) -> Dict[str, Any]:
        """
        Download PDF with metadata.
        
        Args:
            url: PDF URL
            output_path: Path to save PDF
            
        Returns:
            Download metadata
        """
        response = self.session.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Save PDF
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Calculate hash
        with open(output_path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()
        
        return {
            'path': str(output_path),
            'downloaded_at': datetime.utcnow().isoformat(),
            'content_type': response.headers.get('Content-Type', 'application/pdf'),
            'content_length': int(response.headers.get('Content-Length', 0)),
            'content_hash': content_hash,
            'headers': dict(response.headers)
        }
    
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML page."""
        metadata = {}
        
        # Title
        if title := soup.find('title'):
            metadata['title'] = title.text.strip()
        
        # Meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            if name := meta.get('name'):
                meta_tags[name] = meta.get('content', '')
            elif prop := meta.get('property'):
                meta_tags[prop] = meta.get('content', '')
        
        metadata['meta_tags'] = meta_tags
        
        # Last modified date (if available)
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'last-modified' or meta.get('http-equiv') == 'last-modified':
                metadata['last_modified'] = meta.get('content')
                break
        
        return metadata
    
    def preserve_assets(self, soup: BeautifulSoup, base_url: str, output_dir: Path) -> List[Dict[str, Any]]:
        """
        Download and preserve all page assets (images, CSS, JS).
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative URLs
            output_dir: Directory to save assets
            
        Returns:
            List of asset metadata
        """
        assets = []
        asset_types = {
            'img': 'src',
            'link': 'href',
            'script': 'src'
        }
        
        for tag, attr in asset_types.items():
            for element in soup.find_all(tag):
                if url := element.get(attr):
                    # Skip data URLs and external resources
                    if url.startswith('data:') or url.startswith('//'):
                        continue
                    
                    # Resolve relative URLs
                    absolute_url = urljoin(base_url, url)
                    
                    try:
                        # Download asset
                        response = self.session.get(absolute_url, timeout=10)
                        response.raise_for_status()
                        
                        # Generate filename
                        parsed = urlparse(absolute_url)
                        filename = Path(parsed.path).name or f"{tag}_{len(assets)}"
                        asset_path = output_dir / filename
                        
                        # Save asset
                        with open(asset_path, 'wb') as f:
                            f.write(response.content)
                        
                        assets.append({
                            'type': tag,
                            'original_url': url,
                            'absolute_url': absolute_url,
                            'local_path': str(asset_path),
                            'content_type': response.headers.get('Content-Type', ''),
                            'size': len(response.content)
                        })
                        
                    except Exception as e:
                        logger.warning(f"Failed to download asset {absolute_url}: {e}")
        
        return assets
    
    @abstractmethod
    def get_target_urls(self) -> List[str]:
        """Return list of URLs to scrape. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def parse_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse document content and extract relevant information.
        Must be implemented by subclasses.
        
        Args:
            content: HTML content
            metadata: Document metadata
            
        Returns:
            List of extracted items (bylaws, documents, etc.)
        """
        pass
    
    def scrape(self) -> Dict[str, Any]:
        """
        Main scraping method that orchestrates the entire process.
        
        Returns:
            Scraping results including documents found, processed, and any errors
        """
        results = {
            'municipality_id': self.municipality_id,
            'started_at': datetime.utcnow().isoformat(),
            'documents': [],
            'errors': []
        }
        
        try:
            urls = self.get_target_urls()
            
            for url in urls:
                try:
                    # Determine if JavaScript is needed
                    use_js = self.config.get('requires_javascript', False)
                    
                    # Fetch page
                    content, metadata = self.fetch_page(url, use_javascript=use_js)
                    
                    # Calculate content hash
                    content_hash = self.calculate_content_hash(content)
                    
                    # Parse content
                    soup = BeautifulSoup(content, 'html5lib')
                    extracted_items = self.parse_document(content, metadata)
                    
                    # Add document info
                    doc_info = {
                        'url': url,
                        'content_hash': content_hash,
                        'metadata': metadata,
                        'extracted_items': extracted_items,
                        'scraped_at': datetime.utcnow().isoformat()
                    }
                    
                    results['documents'].append(doc_info)
                    
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
                    results['errors'].append({
                        'url': url,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
        finally:
            self.cleanup()
            results['completed_at'] = datetime.utcnow().isoformat()
        
        return results