"""
Core module for Advanced Scraper.
Production-grade architecture for resilient, stealth, and intelligent web scraping.
Features: Async execution with httpx, anti-detection, retry logic, rate limiting, proxy rotation, 
and structured data extraction with BeautifulSoup.
"""
import asyncio
import random
import time
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, HttpUrl
from loguru import logger
import json

# Configure logger for production use
logger.remove()
logger.add(
    "logs/scraper_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)
logger.add(
    lambda msg: print(msg, end=""),
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> - <cyan>{message}</cyan>",
)


# --- Enums & Constants ---
class ScrapingStatus(Enum):
    """Status enumeration for scraping tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    BLOCKED = "blocked"


class UserAgentType(Enum):
    """Common user agent types for rotation."""
    CHROME_WINDOWS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    CHROME_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    FIREFOX_WINDOWS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    FIREFOX_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
    SAFARI_MAC = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
    EDGE_WINDOWS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"


USER_AGENTS = [ua.value for ua in UserAgentType]


# --- Data Models ---
class ScrapedItem(BaseModel):
    """Pydantic model for structured data extraction with validation."""
    url: HttpUrl
    title: str = Field(..., min_length=1, max_length=500)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "success"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


@dataclass
class ScraperConfig:
    """Configuration dataclass for scraper initialization."""
    base_url: str
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    rate_limit_delay: float = 0.5
    enable_proxy_rotation: bool = False
    proxy_list: List[str] = field(default_factory=list)
    enable_stealth: bool = True
    max_concurrent_requests: int = 5
    save_to_file: bool = True
    output_dir: str = "output"
    debug_mode: bool = False


@dataclass
class RequestResult:
    """Result container for HTTP requests."""
    success: bool
    status_code: int
    content: str
    headers: Dict[str, str]
    error_message: Optional[str] = None
    response_time: float = 0.0


# --- Advanced Utilities ---
class StealthUtils:
    """Utility class for anti-detection and stealth mechanisms."""
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Return a random user agent from the pool."""
        return random.choice(USER_AGENTS)
    
    @staticmethod
    def generate_request_headers(custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Generate realistic browser-like headers."""
        headers = {
            "User-Agent": StealthUtils.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
        if custom_headers:
            headers.update(custom_headers)
        return headers
    
    @staticmethod
    async def simulate_human_behavior():
        """Simulate human-like delays between actions."""
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)
    
    @staticmethod
    def generate_fingerprint() -> str:
        """Generate a unique session fingerprint."""
        timestamp = str(time.time())
        random_seed = str(random.random())
        return hashlib.sha256((timestamp + random_seed).encode()).hexdigest()[:16]


class RateLimiter:
    """Token bucket rate limiter for controlling request frequency."""
    
    def __init__(self, rate: float = 1.0, burst: int = 5):
        self.rate = rate  # tokens per second
        self.burst = burst  # maximum tokens
        self.tokens = burst
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class ProxyRotator:
    """Manages proxy rotation for distributed scraping."""
    
    def __init__(self, proxy_list: List[str]):
        self.proxies = proxy_list
        self.current_index = 0
        self.failed_proxies: set = set()
        self._lock = asyncio.Lock()
    
    async def get_next_proxy(self) -> Optional[str]:
        """Get the next available proxy."""
        async with self._lock:
            available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
            if not available_proxies:
                logger.warning("No available proxies remaining")
                return None
            
            proxy = available_proxies[self.current_index % len(available_proxies)]
            self.current_index += 1
            return proxy
    
    async def mark_failed(self, proxy: str):
        """Mark a proxy as failed."""
        async with self._lock:
            self.failed_proxies.add(proxy)
            logger.warning(f"Proxy marked as failed: {proxy}")
    
    async def reset_failed(self):
        """Reset all failed proxies after cooldown."""
        async with self._lock:
            self.failed_proxies.clear()
            logger.info("All failed proxies reset")


# --- Base Scraper Class ---
class BaseScraper:
    """
    Advanced base scraper class with production-grade features:
    - Async HTTP fetching with httpx
    - HTML parsing with BeautifulSoup
    - Anti-bot & stealth mechanisms
    - Intelligent retry with exponential backoff
    - Rate limiting and proxy rotation
    - Structured data extraction and validation
    - Comprehensive logging and error handling
    """
    
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.base_url = config.base_url
        self.max_retries = config.max_retries
        self.retry_delay = config.retry_delay
        self.timeout = config.timeout
        self.rate_limiter = RateLimiter(rate=1.0/config.rate_limit_delay)
        self.proxy_rotator = ProxyRotator(config.proxy_list) if config.enable_proxy_rotation else None
        self.session_fingerprint = StealthUtils.generate_fingerprint()
        self.scraped_items: List[ScrapedItem] = []
        self.failed_urls: List[str] = []
        self._http_client = None
        
        logger.info(f"Initialized advanced scraper for {self.base_url}")
        logger.info(f"Session fingerprint: {self.session_fingerprint}")
        logger.info(f"Max retries: {self.max_retries}, Timeout: {self.timeout}s")
        
        # Create output directory if needed
        if config.save_to_file:
            Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def _get_http_client(self, proxy: Optional[str] = None) -> "httpx.AsyncClient":
        """Initialize or return existing HTTP client with stealth configuration."""
        import httpx
        
        headers = StealthUtils.generate_request_headers()
        
        client = httpx.AsyncClient(
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
            http2=True,
        )
        logger.debug("HTTP client initialized with stealth headers")
        
        return client
    
    async def fetch_page_http(self, url: str) -> RequestResult:
        """Fetch page using httpx with retry logic and stealth."""
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                await self.rate_limiter.acquire()
                
                client = await self._get_http_client()
                
                # Rotate proxy if enabled
                if self.proxy_rotator:
                    proxy = await self.proxy_rotator.get_next_proxy()
                    if proxy:
                        client = httpx.AsyncClient(
                            proxy=proxy,
                            headers=StealthUtils.generate_request_headers(),
                            timeout=self.timeout,
                        )
                
                # Simulate human behavior before request
                await StealthUtils.simulate_human_behavior()
                
                response = await client.get(url)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    logger.success(f"Successfully fetched {url} (attempt {attempt + 1})")
                    return RequestResult(
                        success=True,
                        status_code=response.status_code,
                        content=response.text,
                        headers=dict(response.headers),
                        response_time=response_time,
                    )
                elif response.status_code in [403, 429, 503]:
                    logger.warning(f"Blocked/rate-limited: {url} - Status {response.status_code}")
                    if self.proxy_rotator and attempt < self.max_retries - 1:
                        await self.proxy_rotator.mark_failed(await self.proxy_rotator.get_next_proxy())
                    raise Exception(f"HTTP {response.status_code}")
                else:
                    logger.error(f"Failed to fetch {url} - Status {response.status_code}")
                    return RequestResult(
                        success=False,
                        status_code=response.status_code,
                        content="",
                        headers={},
                        error_message=f"HTTP {response.status_code}",
                        response_time=response_time,
                    )
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    backoff = self.retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Retrying in {backoff:.2f}s...")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"All attempts failed for {url}")
                    self.failed_urls.append(url)
                    return RequestResult(
                        success=False,
                        status_code=0,
                        content="",
                        headers={},
                        error_message=str(e),
                        response_time=time.time() - start_time,
                    )
        
        return RequestResult(
            success=False,
            status_code=0,
            content="",
            headers={},
            error_message="Max retries exceeded",
            response_time=time.time() - start_time,
        )
    
    def parse_page(self, html: str, url: str) -> ScrapedItem:
        """Parse HTML into structured Pydantic models using BeautifulSoup."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        
        # Extract metadata
        metadata = {}
        meta_tags = soup.find_all("meta")
        for meta in meta_tags:
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[name] = content
        
        # Extract main content (customizable per site)
        data = {
            "headings": {
                "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
                "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
                "h3": [h.get_text(strip=True) for h in soup.find_all("h3")],
            },
            "links": [a.get("href") for a in soup.find_all("a", href=True)],
            "images": [img.get("src") for img in soup.find_all("img", src=True)],
            "paragraphs": [p.get_text(strip=True)[:200] for p in soup.find_all("p")[:10]],
        }
        
        item = ScrapedItem(
            url=url,
            title=title,
            data=data,
            metadata=metadata,
            status="success",
        )
        
        logger.info(f"Parsed {url}: {title}")
        return item
    
    async def scrape_url(self, url: str) -> Optional[ScrapedItem]:
        """Scrape a single URL using httpx and BeautifulSoup."""
        logger.info(f"Scraping: {url}")
        
        result = await self.fetch_page_http(url)
        
        if result.success:
            item = self.parse_page(result.content, url)
            item.metadata["response_time"] = result.response_time
            item.metadata["status_code"] = result.status_code
            self.scraped_items.append(item)
            return item
        else:
            logger.error(f"Failed to scrape {url}: {result.error_message}")
            return None
    
    async def run(self, urls: Optional[List[str]] = None) -> List[ScrapedItem]:
        """
        Main execution loop with concurrent scraping support.
        
        Args:
            urls: Optional list of URLs to scrape. If None, uses base_url.
        
        Returns:
            List of successfully scraped items.
        """
        logger.info("=" * 60)
        logger.info("Starting advanced scraping process...")
        logger.info("=" * 60)
        
        if urls is None:
            urls = [self.base_url]
        
        # Create semaphore for concurrent request limiting
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def scrape_with_semaphore(url: str):
            async with semaphore:
                return await self.scrape_url(url)
        
        # Execute concurrent scraping
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = [r for r in results if isinstance(r, ScrapedItem)]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        logger.info("=" * 60)
        logger.info(f"Scraping completed!")
        logger.info(f"Successful: {len(successful)}/{len(urls)}")
        logger.info(f"Failed: {len(self.failed_urls)}")
        logger.info(f"Exceptions: {len(exceptions)}")
        logger.info("=" * 60)
        
        # Save results if configured
        if self.config.save_to_file and successful:
            await self.save_results(successful)
        
        return successful
    
    async def save_results(self, items: List[ScrapedItem], filename: Optional[str] = None):
        """Save scraped results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data_{timestamp}.json"
        
        filepath = Path(self.config.output_dir) / filename
        
        data = [item.model_dump(mode='json') for item in items]
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.success(f"Results saved to {filepath}")
    
    async def close(self):
        """Cleanup resources."""
        logger.debug("Scraper closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# --- Entry Point ---
async def main():
    """Main entry point demonstrating scraper usage."""
    # Example configuration
    config = ScraperConfig(
        base_url="https://example.com",
        max_retries=3,
        retry_delay=1.0,
        timeout=30,
        rate_limit_delay=0.5,
        enable_proxy_rotation=False,
        enable_stealth=True,
        max_concurrent_requests=3,
        save_to_file=True,
        output_dir="output",
        debug_mode=False,
    )
    
    # Example URLs to scrape
    urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/headers",
    ]
    
    async with BaseScraper(config) as scraper:
        results = await scraper.run(urls)
        
        if results:
            logger.info(f"\nScraped {len(results)} pages successfully:")
            for item in results:
                logger.info(f"  - {item.url}: {item.title}")


if __name__ == "__main__":
    asyncio.run(main())
