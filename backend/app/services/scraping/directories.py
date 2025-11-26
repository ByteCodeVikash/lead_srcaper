import asyncio
import httpx
from typing import Optional, Dict, List
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import re


class DirectoryScraper:
    """Scrape business directories for contact information."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def search_all_directories(self, business_name: str) -> Optional[Dict[str, any]]:
        """
        Search multiple directories and combine results.
        
        Returns:
            Combined contact information from all sources
        """
        results = []
        
        # Try each directory
        tasks = [
            self.search_yellowpages(business_name),
            self.search_yelp(business_name),
        ]
        
        directory_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine non-None results
        combined = {
            'phone': None,
            'website': None,
            'address': None,
            'sources': []
        }
        
        for result in directory_results:
            if result and not isinstance(result, Exception):
                if result.get('phone') and not combined['phone']:
                    combined['phone'] = result['phone']
                if result.get('website') and not combined['website']:
                    combined['website'] = result['website']
                if result.get('address') and not combined['address']:
                    combined['address'] = result['address']
                if result.get('source'):
                    combined['sources'].append(result['source'])
        
        return combined if combined['phone'] or combined['website'] else None
    
    async def search_yellowpages(self, business_name: str) -> Optional[Dict[str, any]]:
        """
        Search YellowPages for business contact information.
        
        Returns:
            Dict with contact info or None
        """
        try:
            search_url = f"https://www.yellowpages.com/search?search_terms={quote_plus(business_name)}&geo_location_terms=USA"
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(search_url, headers=self.headers)
                
                if response.status_code != 200:
                    return None
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # YellowPages typically shows results in divs with class 'result'
                result_div = soup.find('div', class_='result')
                if not result_div:
                    return None
                
                result = {
                    'phone': None,
                    'website': None,
                    'address': None,
                    'source': 'yellowpages'
                }
                
                # Extract phone
                phone_elem = result_div.find('div', class_='phones')
                if phone_elem:
                    result['phone'] = phone_elem.get_text().strip()
                
                # Extract website
                website_link = result_div.find('a', class_='track-visit-website')
                if website_link:
                    result['website'] = website_link.get('href')
                
                # Extract address
                address_elem = result_div.find('div', class_='street-address')
                if address_elem:
                    result['address'] = address_elem.get_text().strip()
                
                return result if result['phone'] or result['website'] else None
        
        except Exception as e:
            print(f"YellowPages search failed: {e}")
            return None
    
    async def search_yelp(self, business_name: str) -> Optional[Dict[str, any]]:
        """
        Search Yelp for business contact information.
        
        Returns:
            Dict with contact info or None
        """
        try:
            search_url = f"https://www.yelp.com/search?find_desc={quote_plus(business_name)}"
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(search_url, headers=self.headers)
                
                if response.status_code != 200:
                    return None
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                result = {
                    'phone': None,
                    'website': None,
                    'address': None,
                    'source': 'yelp'
                }
                
                # Yelp's structure changes frequently, so this is best-effort
                # Look for phone numbers in the HTML
                phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
                phone_matches = re.findall(phone_pattern, response.text)
                if phone_matches:
                    result['phone'] = phone_matches[0]
                
                # Look for website links
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if '/biz_redir?' in href:
                        # Yelp business website redirect
                        result['website'] = href
                        break
                
                return result if result['phone'] or result['website'] else None
        
        except Exception as e:
            print(f"Yelp search failed: {e}")
            return None


# Note: Business directory websites frequently change their HTML structure
# and may block scrapers. These implementations are best-effort and for
# educational purposes only.
