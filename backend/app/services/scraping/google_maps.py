import asyncio
import httpx
from typing import Optional, Dict
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import re


class GoogleMapsScraper:
    """
    Scrape Google Maps for business contact information.
    
    Note: This uses HTML scraping and may be unreliable due to Google's
    anti-scraping measures. Use as a best-effort fallback.
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    
    async def search_business(self, business_name: str) -> Optional[Dict[str, any]]:
        """
        Search for a business on Google Maps and extract contact info.
        
        Returns:
            Dict with 'phone', 'website', 'address' or None
        """
        try:
            # Search Google Maps
            query = f"{business_name}"
            search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
            
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(search_url, headers=self.headers)
                
                if response.status_code != 200:
                    return None
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'lxml')
                
                result = {
                    'phone': None,
                    'website': None,
                    'address': None
                }
                
                # Try to extract phone number
                # Google Maps often has phone in specific data attributes or text
                phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
                phone_matches = re.findall(phone_pattern, response.text)
                if phone_matches:
                    result['phone'] = phone_matches[0]
                
                # Try to extract website
                # Look for website links
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'http' in href and 'google.com' not in href and 'maps' not in href:
                        # Potential website
                        result['website'] = href
                        break
                
                return result if (result['phone'] or result['website']) else None
        
        except Exception as e:
            print(f"Google Maps search failed for '{business_name}': {e}")
            return None
    
    async def get_place_details(self, place_url: str) -> Optional[Dict[str, any]]:
        """
        Get details from a specific Google Maps place URL.
        
        Args:
            place_url: Direct Google Maps place URL
        
        Returns:
            Dict with contact information
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(place_url, headers=self.headers)
                
                if response.status_code != 200:
                    return None
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                result = {
                    'phone': None,
                    'website': None,
                    'address': None
                }
                
                # Extract phone
                phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
                phone_matches = re.findall(phone_pattern, response.text)
                if phone_matches:
                    result['phone'] = phone_matches[0]
                
                # Extract website
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if 'http' in href and 'google.com' not in href:
                        result['website'] = href
                        break
                
                return result if (result['phone'] or result['website']) else None
        
        except Exception as e:
            print(f"Failed to get place details: {e}")
            return None


# Note: Google Maps scraping is very fragile and may not work reliably.
# This is a best-effort implementation for educational purposes.
# In production, consider using the official Google Places API (paid).
