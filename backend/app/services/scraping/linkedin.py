import asyncio
import httpx
from typing import Optional, Dict
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import re


class LinkedInScraper:
    """
    Scrape LinkedIn public company pages for contact information.
    
    Note: This only accesses public company pages without login.
    LinkedIn actively blocks scrapers, so this may not work reliably.
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def search_company(self, company_name: str) -> Optional[Dict[str, any]]:
        """
        Search for a company on LinkedIn and extract public information.
        
        Returns:
            Dict with 'website', 'linkedin_url' or None
        """
        try:
            # Try to construct LinkedIn company URL
            # LinkedIn public company pages are at: linkedin.com/company/{company-name}
            normalized_name = self._normalize_company_name(company_name)
            company_url = f"https://www.linkedin.com/company/{normalized_name}"
            
            return await self.get_company_info(company_url)
        
        except Exception as e:
            print(f"LinkedIn search failed for '{company_name}': {e}")
            return None
    
    async def get_company_info(self, linkedin_url: str) -> Optional[Dict[str, any]]:
        """
        Get company information from LinkedIn company page URL.
        
        Args:
            linkedin_url: Direct LinkedIn company page URL
        
        Returns:
            Dict with website and other info
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(linkedin_url, headers=self.headers)
                
                # LinkedIn often returns 999 status for scrapers
                if response.status_code == 999:
                    print(f"LinkedIn blocked request: {linkedin_url}")
                    return None
                
                if response.status_code != 200:
                    return None
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                result = {
                    'website': None,
                    'linkedin_url': linkedin_url,
                    'phone': None
                }
                
                # Try to find website link
                # LinkedIn company pages usually have website in a specific section
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    # Look for external website links
                    if 'http' in href and 'linkedin.com' not in href:
                        # Clean LinkedIn tracking params
                        if '?trk=' in href:
                            href = href.split('?trk=')[0]
                        result['website'] = href
                        break
                
                # Try to extract from meta tags
                meta_tags = soup.find_all('meta', property=True)
                for meta in meta_tags:
                    if meta.get('property') == 'og:url':
                        content = meta.get('content', '')
                        if 'http' in content and 'linkedin.com' not in content:
                            result['website'] = content
                
                return result if result['website'] else None
        
        except Exception as e:
            print(f"Failed to get LinkedIn company info: {e}")
            return None
    
    def _normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for LinkedIn URL."""
        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^a-z0-9\s-]', '', company_name.lower())
        # Replace spaces with hyphens
        normalized = re.sub(r'\s+', '-', normalized.strip())
        # Remove common suffixes
        normalized = re.sub(r'-(inc|llc|ltd|corporation|corp)$', '', normalized)
        return normalized


# Note: LinkedIn actively blocks web scrapers.
# This implementation may not work reliably and is for educational purposes only.
# Consider using LinkedIn's official API (requires authentication) for production use.
