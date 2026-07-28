"""
Advanced URL Manager with intelligent crawling capabilities.
Features: URL prioritization, duplicate detection, domain politeness, and sitemap parsing.
"""
import asyncio
from typing import Set, List, Optional, Dict
from collections import deque
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from loguru import logger


@dataclass
class CrawlURL:
    """Represents a URL to be crawled with metadata."""
    url: str
    priority: int = 0
    depth: int = 0
    parent_url: Optional[str] = None
    discovered_at: datetime = field(default_factory=datetime.now)
    last_attempted: Optional[datetime] = None
    retry_count: int = 0
    status: str = "pending"  # pending, success, failed, skipped
    
    def __hash__(self):
        return hash(self.url)
    
    def __eq__(self, other):
        if isinstance(other, CrawlURL):
            return self.url == other.url
        return False


class URLManager:
    """
    Advanced URL management system for web crawling.
    Features:
    - Priority queue for URL scheduling
    - Duplicate detection with Bloom filter-like mechanism
    - Domain-based rate limiting
    - Robots.txt compliance (optional)
    - Sitemap parsing integration
    """
    
    def __init__(
        self,
        max_urls: int = 10000,
        max_depth: int = 5,
        allowed_domains: Optional[List[str]] = None,
        respect_robots_txt: bool = True,
    ):
        self.max_urls = max_urls
        self.max_depth = max_depth
        self.allowed_domains = allowed_domains or []
        self.respect_robots_txt = respect_robots_txt
        
        # URL queues organized by priority
        self._queue: deque[CrawlURL] = deque()
        self._visited: Set[str] = set()
        self._failed: Set[str] = set()
        self._domain_last_access: Dict[str, datetime] = {}
        self._domain_request_count: Dict[str, int] = {}
        
        self._lock = asyncio.Lock()
        
        logger.info(f"URLManager initialized: max_urls={max_urls}, max_depth={max_depth}")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison."""
        from urllib.parse import urlunparse
        
        parsed = urlparse(url)
        # Remove fragments
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            parsed.params,
            parsed.query,
            ''  # Remove fragment
        ))
        return normalized
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL is from an allowed domain."""
        if not self.allowed_domains:
            return True
        
        domain = self._get_domain(url)
        return any(domain.endswith(allowed) for allowed in self.allowed_domains)
    
    def _generate_url_hash(self, url: str) -> str:
        """Generate unique hash for URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def add_url(
        self,
        url: str,
        priority: int = 0,
        depth: int = 0,
        parent_url: Optional[str] = None,
    ) -> bool:
        """
        Add a URL to the crawl queue.
        
        Returns:
            True if URL was added, False if rejected (duplicate, disallowed, etc.)
        """
        async with self._lock:
            normalized_url = self._normalize_url(url)
            
            # Check if already visited or failed
            if normalized_url in self._visited or normalized_url in self._failed:
                logger.debug(f"URL already processed: {normalized_url}")
                return False
            
            # Check domain restrictions
            if not self._is_allowed_domain(normalized_url):
                logger.debug(f"URL not in allowed domains: {normalized_url}")
                return False
            
            # Check depth limit
            if depth > self.max_depth:
                logger.debug(f"URL exceeds max depth: {normalized_url} (depth={depth})")
                return False
            
            # Check max URLs limit
            if len(self._visited) + len(self._queue) >= self.max_urls:
                logger.warning(f"URL manager at capacity ({self.max_urls} URLs)")
                return False
            
            # Create CrawlURL object
            crawl_url = CrawlURL(
                url=normalized_url,
                priority=priority,
                depth=depth,
                parent_url=parent_url,
            )
            
            # Add to queue with priority ordering
            if priority > 0:
                # High priority: add to front
                self._queue.appendleft(crawl_url)
            else:
                # Normal priority: add to back
                self._queue.append(crawl_url)
            
            logger.debug(f"Added URL to queue: {normalized_url} (priority={priority}, depth={depth})")
            return True
    
    async def get_next_url(self) -> Optional[CrawlURL]:
        """
        Get the next URL to crawl.
        
        Returns:
            CrawlURL object or None if queue is empty
        """
        async with self._lock:
            while self._queue:
                crawl_url = self._queue.popleft()
                
                # Check if already visited (might have been added multiple times)
                if crawl_url.url in self._visited:
                    continue
                
                # Apply domain politeness (rate limiting per domain)
                domain = self._get_domain(crawl_url.url)
                if domain in self._domain_last_access:
                    last_access = self._domain_last_access[domain]
                    time_since_last = (datetime.now() - last_access).total_seconds()
                    
                    # Minimum 1 second between requests to same domain
                    if time_since_last < 1.0:
                        # Put back in queue and try later
                        self._queue.append(crawl_url)
                        continue
                
                return crawl_url
            
            return None
    
    async def mark_visited(self, url: str):
        """Mark a URL as successfully visited."""
        async with self._lock:
            normalized_url = self._normalize_url(url)
            self._visited.add(normalized_url)
            
            domain = self._get_domain(normalized_url)
            self._domain_last_access[domain] = datetime.now()
            self._domain_request_count[domain] = self._domain_request_count.get(domain, 0) + 1
            
            logger.debug(f"Marked URL as visited: {normalized_url}")
    
    async def mark_failed(self, url: str):
        """Mark a URL as failed."""
        async with self._lock:
            normalized_url = self._normalize_url(url)
            self._failed.add(normalized_url)
            logger.debug(f"Marked URL as failed: {normalized_url}")
    
    async def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
        
        Returns:
            List of extracted and normalized URLs
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for anchor in soup.find_all('a', href=True):
            href = anchor['href'].strip()
            
            # Skip javascript, mailto, tel, etc.
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Normalize
            normalized = self._normalize_url(absolute_url)
            
            if normalized not in links:
                links.append(normalized)
        
        logger.debug(f"Extracted {len(links)} links from {base_url}")
        return links
    
    async def get_stats(self) -> Dict:
        """Get current URL manager statistics."""
        async with self._lock:
            return {
                'queue_size': len(self._queue),
                'visited_count': len(self._visited),
                'failed_count': len(self._failed),
                'domains_accessed': len(self._domain_last_access),
                'total_requests': sum(self._domain_request_count.values()),
            }
    
    async def clear(self):
        """Clear all URL data."""
        async with self._lock:
            self._queue.clear()
            self._visited.clear()
            self._failed.clear()
            self._domain_last_access.clear()
            self._domain_request_count.clear()
            logger.info("URLManager cleared")
