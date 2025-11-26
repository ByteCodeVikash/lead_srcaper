import asyncio
import httpx
from typing import Optional, List, Dict
from urllib.parse import urlparse, urljoin, quote_plus
from bs4 import BeautifulSoup
import re


class WebSearcher:
    """Search for company websites using DuckDuckGo HTML results."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
        }
    
    async def search_company(self, company_name: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search for a company and return top results.
        
        Returns:
            List of dicts with 'title', 'url', 'snippet'
        """
        try:
            # Try DuckDuckGo first
            results = await self._search_duckduckgo(company_name, max_results)
            if results:
                return results
            
            # Fallback to basic Bing search if DDG fails
            return await self._search_bing(company_name, max_results)
        
        except Exception as e:
            print(f"Search failed for '{company_name}': {e}")
            return []
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Search using DuckDuckGo HTML."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'lxml')
                results = []
                
                # Find result divs
                for result_div in soup.find_all('div', class_='result')[:max_results]:
                    try:
                        # Extract title and link
                        title_tag = result_div.find('a', class_='result__a')
                        snippet_tag = result_div.find('a', class_='result__snippet')
                        
                        if title_tag:
                            title = title_tag.get_text().strip()
                            # DDG uses a redirect, extract actual URL
                            redirect_url = title_tag.get('href', '')
                            
                            # Parse actual URL from DDG redirect
                            actual_url = self._extract_url_from_ddg_redirect(redirect_url)
                            
                            snippet = snippet_tag.get_text().strip() if snippet_tag else ""
                            
                            if actual_url:
                                results.append({
                                    'title': title,
                                    'url': actual_url,
                                    'snippet': snippet
                                })
                    except Exception:
                        continue
                
                return results
        
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            return []
    
    def _extract_url_from_ddg_redirect(self, redirect_url: str) -> str:
        """Extract actual URL from DuckDuckGo redirect link."""
        try:
            # DDG format: //duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com
            if 'uddg=' in redirect_url:
                from urllib.parse import unquote
                parts = redirect_url.split('uddg=')
                if len(parts) > 1:
                    return unquote(parts[1].split('&')[0])
            return redirect_url
        except Exception:
            return redirect_url
    
    async def _search_bing(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Fallback: Search using Bing HTML."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                url = f"https://www.bing.com/search?q={quote_plus(query)}"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'lxml')
                results = []
                
                # Find result items
                for result_div in soup.find_all('li', class_='b_algo')[:max_results]:
                    try:
                        title_tag = result_div.find('h2')
                        link_tag = title_tag.find('a') if title_tag else None
                        snippet_tag = result_div.find('p')
                        
                        if link_tag:
                            title = link_tag.get_text().strip()
                            url = link_tag.get('href', '')
                            snippet = snippet_tag.get_text().strip() if snippet_tag else ""
                            
                            if url.startswith('http'):
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'snippet': snippet
                                })
                    except Exception:
                        continue
                
                return results
        
        except Exception as e:
            print(f"Bing search failed: {e}")
            return []
    
    def find_official_domain(self, company_name: str, search_results: List[Dict[str, str]]) -> Optional[str]:
        """
        Use heuristics to find the most likely official company domain.
        
        Heuristics:
        1. Domain contains company name
        2. Domain is not a directory (yellowpages, yelp, linkedin, facebook, etc.)
        3. Prefer shorter domains
        4. Check if domain has /about or /contact pages
        """
        if not search_results:
            return None
        
        # Normalize company name for comparison
        company_normalized = re.sub(r'[^a-z0-9]', '', company_name.lower())
        
        # Directory domains to avoid
        directory_domains = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'yellowpages.com', 'yelp.com', 'bbb.org', 'manta.com',
            'wikipedia.org', 'bloomberg.com', 'crunchbase.com'
        ]
        
        scored_results = []
        
        for result in search_results:
            url = result['url']
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            
            # Skip directory sites
            if any(dir_domain in domain for dir_domain in directory_domains):
                continue
            
            score = 0
            
            # Score 1: Company name in domain
            domain_normalized = re.sub(r'[^a-z0-9]', '', domain.split('.')[0])
            if company_normalized in domain_normalized or domain_normalized in company_normalized:
                score += 10
            
            # Score 2: Company name in title
            if company_name.lower() in result['title'].lower():
                score += 5
            
            # Score 3: Shorter domains are better (likely official)
            score += max(0, 5 - len(domain.split('.')))
            
            # Score 4: Root domain preferred
            if parsed.path in ['', '/']:
                score += 3
            
            scored_results.append((score, url))
        
        # Sort by score descending
        scored_results.sort(reverse=True, key=lambda x: x[0])
        
        # Return highest scoring URL
        if scored_results and scored_results[0][0] > 0:
            return scored_results[0][1]
        
        # Fallback: return first non-directory result
        for result in search_results:
            domain = urlparse(result['url']).netloc.lower()
            if not any(dir_domain in domain for dir_domain in directory_domains):
                return result['url']
        
        return None
