import asyncio
import httpx
from typing import Optional, List, Set, Dict
from urllib.parse import urlparse, urljoin, urlencode
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import time
from app.config import get_settings
from app.services.scraping.extractors import ContactPageDetector

settings = get_settings()


class RateLimiter:
    """Simple rate limiter for  polite crawling."""
    
    def __init__(self, rate_limit: float = 2.0):
        """
        Args:
            rate_limit: Minimum seconds between requests
        """
        self.rate_limit = rate_limit
        self.last_request_time: Dict[str, float] = {}
    
    async def wait_if_needed(self, domain: str):
        """Wait if necessary to respect rate limit for a domain."""
        current_time = time.time()
        
        if domain in self.last_request_time:
            elapsed = current_time - self.last_request_time[domain]
            if elapsed < self.rate_limit:
                wait_time = self.rate_limit - elapsed
                await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()


class RobotsTxtChecker:
    """Check robots.txt compliance."""
    
    def __init__(self):
        self.parsers: Dict[str, RobotFileParser] = {}
    
    async def can_fetch(self, url: str, user_agent: str) -> bool:
        """Check if crawling is allowed by robots.txt."""
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            if base_url not in self.parsers:
                robots_url = urljoin(base_url, '/robots.txt')
                
                # Fetch robots.txt
                async with httpx.AsyncClient(timeout=10) as client:
                    try:
                        response = await client.get(robots_url)
                        if response.status_code == 200:
                            parser = RobotFileParser()
                            parser.parse(response.text.splitlines())
                            self.parsers[base_url] = parser
                        else:
                            # No robots.txt, assume allowed
                            return True
                    except Exception:
                        # Error fetching robots.txt, assume allowed
                        return True
            
            parser = self.parsers.get(base_url)
            if parser:
                return parser.can_fetch(user_agent, url)
            
            return True
        
        except Exception:
            # On any error, assume allowed
            return True


class WebCrawler:
    """Async web crawler for fetching and parsing web pages."""
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        robots_checker: Optional[RobotsTxtChecker] = None,
        respect_robots_txt: bool = True,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.rate_limiter = rate_limiter or RateLimiter(settings.scraping_rate_limit)
        self.robots_checker = robots_checker or RobotsTxtChecker()
        self.respect_robots_txt = respect_robots_txt
        self.max_retries = max_retries
        self.timeout = timeout
        
        # HTTP client settings
        self.headers = {
            'User-Agent': settings.scraping_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
        }
        
        # Proxy settings
        self.proxies = None
        if settings.http_proxy or settings.https_proxy:
            self.proxies = {
                'http://': settings.http_proxy,
                'https://': settings.https_proxy,
            }
    
    async def fetch_page(self, url: str) -> Optional[Dict[str, any]]:
        """
        Fetch a web page with retries and rate limiting.
        
        Returns:
            Dict with 'url', 'html', 'status_code' or None if failed
        """
        domain = urlparse(url).netloc
        
        # Check robots.txt
        if self.respect_robots_txt:
            allowed = await self.robots_checker.can_fetch(url, self.headers['User-Agent'])
            if not allowed:
                print(f"Blocked by robots.txt: {url}")
                return None
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed(domain)
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    proxies=self.proxies
                ) as client:
                    response = await client.get(url, headers=self.headers)
                    
                    if response.status_code == 200:
                        return {
                            'url': str(response.url),
                            'html': response.text,
                            'status_code': response.status_code
                        }
                    elif response.status_code == 403 or response.status_code == 429:
                        # Rate limited or forbidden
                        print(f"HTTP {response.status_code} for {url}")
                        return None
                    else:
                        # Retry on other errors
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
            
            except httpx.TimeoutException:
                print(f"Timeout fetching {url}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
            
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
        
        return None
    
    async def crawl_domain(
        self,
        base_url: str,
        max_pages: int = 10,
        target_keywords: Optional[List[str]] = None
    ) -> List[Dict[str, any]]:
        """
        Crawl a domain starting from base_url.
        
        Prioritizes:
        - Homepage
        - Contact pages
        - About pages
        - Other pages with target keywords
        
        Returns:
            List of page dicts with 'url', 'html', 'status_code'
        """
        visited_urls: Set[str] = set()
        pages_fetched: List[Dict[str, any]] = []
        
        # Normalize base URL
        parsed = urlparse(base_url)
        if not parsed.scheme:
            base_url = 'https://' + base_url
        
        # Define priority URLs to crawl
        priority_paths = ['/', '/contact', '/contact-us', '/about', '/about-us', '/team', '/people']
        urls_to_crawl = [urljoin(base_url, path) for path in priority_paths]
        
        # Fetch homepage first
        homepage = await self.fetch_page(base_url)
        if homepage:
            pages_fetched.append(homepage)
            visited_urls.add(homepage['url'])
            
            # Find additional contact links
            contact_links = ContactPageDetector.find_contact_links(homepage['html'], base_url)
            urls_to_crawl.extend(contact_links)
        
        # Crawl priority URLs
        for url in urls_to_crawl:
            if len(pages_fetched) >= max_pages:
                break
            
            # Normalize URL
            normalized_url = self._normalize_url(url)
            
            if normalized_url in visited_urls:
                continue
            
            # Ensure same domain
            if urlparse(normalized_url).netloc != urlparse(base_url).netloc:
                continue
            
            page = await self.fetch_page(normalized_url)
            if page:
                pages_fetched.append(page)
                visited_urls.add(normalized_url)
        
        return pages_fetched
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        parsed = urlparse(url)
        # Remove fragment and query params for deduplication
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        # Remove trailing slash
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]
        return normalized
