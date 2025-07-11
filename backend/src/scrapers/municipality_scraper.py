"""
Sample municipality scraper implementation.
Demonstrates how to inherit from BaseScraper and implement municipality-specific logic.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class MunicipalityScraper(BaseScraper):
    """
    Sample municipality scraper that demonstrates bylaw extraction patterns.
    This can be customized for specific municipality websites.
    """
    
    def __init__(self, municipality_id: str, config: Dict[str, Any]):
        super().__init__(municipality_id, config)
        
        # Municipality-specific configuration
        self.base_url = config.get('base_url', '')
        self.bylaw_patterns = config.get('bylaw_patterns', {})
        self.selectors = config.get('selectors', {})
        
        # Default selectors for common patterns
        self.default_selectors = {
            'bylaw_links': 'a[href*="bylaw"], a[href*="ordinance"]',
            'bylaw_title': 'h1, h2, .title, .bylaw-title',
            'bylaw_number': '.bylaw-number, .number',
            'bylaw_content': '.content, .bylaw-content, article, main',
            'pdf_links': 'a[href$=".pdf"]',
            'pagination': '.pagination a, .pager a, a[href*="page"]'
        }
    
    def get_target_urls(self) -> List[str]:
        """
        Get list of URLs to scrape based on configuration.
        
        Returns:
            List of URLs to scrape
        """
        urls = []
        
        # Primary URLs from configuration
        if target_urls := self.config.get('target_urls'):
            urls.extend(target_urls)
        
        # Discovery URLs (for finding additional pages)
        if discovery_urls := self.config.get('discovery_urls'):
            urls.extend(self._discover_urls(discovery_urls))
        
        return urls
    
    def _discover_urls(self, discovery_urls: List[str]) -> List[str]:
        """
        Discover additional URLs from discovery pages.
        
        Args:
            discovery_urls: List of URLs to check for additional links
            
        Returns:
            List of discovered URLs
        """
        discovered = []
        
        for url in discovery_urls:
            try:
                content, metadata = self.fetch_page(url)
                soup = BeautifulSoup(content, 'html5lib')
                
                # Find bylaw links
                bylaw_links = soup.select(self.selectors.get('bylaw_links', self.default_selectors['bylaw_links']))
                
                for link in bylaw_links:
                    if href := link.get('href'):
                        absolute_url = urljoin(url, href)
                        if self._is_valid_bylaw_url(absolute_url):
                            discovered.append(absolute_url)
                
                # Find pagination links
                pagination_links = soup.select(self.selectors.get('pagination', self.default_selectors['pagination']))
                
                for link in pagination_links:
                    if href := link.get('href'):
                        absolute_url = urljoin(url, href)
                        if absolute_url not in discovery_urls and absolute_url not in discovered:
                            discovered.append(absolute_url)
                
            except Exception as e:
                logger.warning(f"Error discovering URLs from {url}: {e}")
        
        return discovered
    
    def _is_valid_bylaw_url(self, url: str) -> bool:
        """
        Check if URL is likely to contain bylaw content.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be a bylaw page
        """
        # Check URL patterns
        bylaw_keywords = ['bylaw', 'ordinance', 'regulation', 'code', 'zoning']
        url_lower = url.lower()
        
        return any(keyword in url_lower for keyword in bylaw_keywords)
    
    def parse_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse document content and extract bylaw information.
        
        Args:
            content: HTML content
            metadata: Document metadata
            
        Returns:
            List of extracted bylaw information
        """
        soup = BeautifulSoup(content, 'html5lib')
        extracted_items = []
        
        # Determine document type
        doc_type = self._determine_document_type(soup, metadata['url'])
        
        if doc_type == 'bylaw_page':
            # Extract individual bylaw
            bylaw_info = self._extract_bylaw_info(soup, metadata['url'])
            if bylaw_info:
                extracted_items.append(bylaw_info)
        
        elif doc_type == 'bylaw_list':
            # Extract list of bylaws
            bylaw_links = self._extract_bylaw_links(soup, metadata['url'])
            extracted_items.extend(bylaw_links)
        
        elif doc_type == 'pdf_document':
            # Handle PDF documents
            pdf_info = self._extract_pdf_info(soup, metadata['url'])
            if pdf_info:
                extracted_items.append(pdf_info)
        
        return extracted_items
    
    def _determine_document_type(self, soup: BeautifulSoup, url: str) -> str:
        """
        Determine the type of document based on content and URL.
        
        Args:
            soup: BeautifulSoup object
            url: Document URL
            
        Returns:
            Document type ('bylaw_page', 'bylaw_list', 'pdf_document')
        """
        # Check for PDF
        if url.lower().endswith('.pdf'):
            return 'pdf_document'
        
        # Check for bylaw content indicators
        bylaw_indicators = soup.select(self.selectors.get('bylaw_content', self.default_selectors['bylaw_content']))
        
        if bylaw_indicators:
            # Check if it's a single bylaw or list
            bylaw_links = soup.select(self.selectors.get('bylaw_links', self.default_selectors['bylaw_links']))
            
            if len(bylaw_links) > 5:  # Arbitrary threshold
                return 'bylaw_list'
            else:
                return 'bylaw_page'
        
        return 'unknown'
    
    def _extract_bylaw_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract bylaw information from a bylaw page.
        
        Args:
            soup: BeautifulSoup object
            url: Page URL
            
        Returns:
            Dictionary with bylaw information
        """
        bylaw_info = {
            'type': 'bylaw',
            'source_url': url,
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        # Extract title
        title_element = soup.select_one(self.selectors.get('bylaw_title', self.default_selectors['bylaw_title']))
        if title_element:
            bylaw_info['title'] = title_element.get_text(strip=True)
        
        # Extract bylaw number
        number_element = soup.select_one(self.selectors.get('bylaw_number', self.default_selectors['bylaw_number']))
        if number_element:
            bylaw_info['bylaw_number'] = number_element.get_text(strip=True)
        else:
            # Try to extract from title or URL
            bylaw_info['bylaw_number'] = self._extract_bylaw_number_from_text(
                bylaw_info.get('title', '') + ' ' + url
            )
        
        # Extract content
        content_element = soup.select_one(self.selectors.get('bylaw_content', self.default_selectors['bylaw_content']))
        if content_element:
            bylaw_info['full_text'] = content_element.get_text(strip=True)
        
        # Extract metadata
        bylaw_info['metadata'] = self._extract_bylaw_metadata(soup)
        
        # Determine category
        bylaw_info['category'] = self._categorize_bylaw(bylaw_info)
        
        # Extract effective date
        bylaw_info['effective_date'] = self._extract_effective_date(soup)
        
        return bylaw_info if bylaw_info.get('title') else None
    
    def _extract_bylaw_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extract bylaw links from a listing page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of bylaw link information
        """
        bylaw_links = []
        
        links = soup.select(self.selectors.get('bylaw_links', self.default_selectors['bylaw_links']))
        
        for link in links:
            if href := link.get('href'):
                absolute_url = urljoin(base_url, href)
                
                link_info = {
                    'type': 'bylaw_link',
                    'url': absolute_url,
                    'title': link.get_text(strip=True),
                    'found_at': base_url,
                    'extracted_at': datetime.utcnow().isoformat()
                }
                
                # Extract bylaw number from link text
                link_info['bylaw_number'] = self._extract_bylaw_number_from_text(link_info['title'])
                
                bylaw_links.append(link_info)
        
        return bylaw_links
    
    def _extract_pdf_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract information about PDF documents.
        
        Args:
            soup: BeautifulSoup object
            url: PDF URL
            
        Returns:
            Dictionary with PDF information
        """
        return {
            'type': 'pdf_document',
            'source_url': url,
            'document_type': 'pdf',
            'extracted_at': datetime.utcnow().isoformat(),
            'requires_processing': True
        }
    
    def _extract_bylaw_number_from_text(self, text: str) -> Optional[str]:
        """
        Extract bylaw number from text using regex patterns.
        
        Args:
            text: Text to search
            
        Returns:
            Extracted bylaw number or None
        """
        # Common bylaw number patterns
        patterns = [
            r'(?:bylaw|ordinance|regulation)\s*(?:no\.?|#|number)?\s*(\d+(?:-\d+)*)',
            r'(?:bl|ord|reg)\.?\s*(\d+(?:-\d+)*)',
            r'(\d{4}-\d+)',  # Year-number format
            r'(\d+/\d+)',    # Number/year format
            r'#(\d+)',       # Simple number with hash
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_bylaw_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract metadata from bylaw page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Look for common metadata patterns
        meta_patterns = {
            'effective_date': ['effective', 'date', 'enacted'],
            'amended_date': ['amended', 'modified', 'updated'],
            'status': ['status', 'active', 'repealed'],
            'department': ['department', 'division', 'office']
        }
        
        for key, keywords in meta_patterns.items():
            for keyword in keywords:
                # Look for elements containing the keyword
                elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
                for element in elements:
                    parent = element.parent
                    if parent and parent.name in ['dt', 'th', 'label']:
                        # Look for corresponding value
                        value_element = parent.find_next_sibling(['dd', 'td']) or parent.parent.find_next_sibling()
                        if value_element:
                            metadata[key] = value_element.get_text(strip=True)
                            break
        
        return metadata
    
    def _categorize_bylaw(self, bylaw_info: Dict[str, Any]) -> str:
        """
        Categorize bylaw based on title and content.
        
        Args:
            bylaw_info: Bylaw information
            
        Returns:
            Bylaw category
        """
        title = bylaw_info.get('title', '').lower()
        content = bylaw_info.get('full_text', '').lower()
        
        # Category keywords
        categories = {
            'zoning': ['zoning', 'land use', 'development', 'subdivision'],
            'adu': ['accessory dwelling', 'secondary suite', 'adu', 'in-law'],
            'building': ['building code', 'construction', 'permit'],
            'parking': ['parking', 'vehicle'],
            'noise': ['noise', 'sound'],
            'business': ['business', 'commercial', 'license']
        }
        
        text_to_check = f"{title} {content}"
        
        for category, keywords in categories.items():
            if any(keyword in text_to_check for keyword in keywords):
                return category
        
        return 'general'
    
    def _extract_effective_date(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract effective date from bylaw page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Effective date string or None
        """
        # Look for date patterns
        date_patterns = [
            r'effective\s+(?:date\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'enacted\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'passed\s+(?:on\s+)?(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'
        ]
        
        text = soup.get_text()
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def handle_pagination(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Handle pagination to find additional pages.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of additional page URLs
        """
        pagination_urls = []
        
        # Find pagination links
        pagination_links = soup.select(self.selectors.get('pagination', self.default_selectors['pagination']))
        
        for link in pagination_links:
            if href := link.get('href'):
                absolute_url = urljoin(base_url, href)
                
                # Filter out unwanted pagination links
                link_text = link.get_text(strip=True).lower()
                if link_text not in ['previous', 'prev', 'first', 'last']:
                    pagination_urls.append(absolute_url)
        
        return pagination_urls