import asyncio
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse
from app.models.job import InputType, ExtractionStatus
from app.services.scraping.web_search import WebSearcher
from app.services.scraping.crawler import WebCrawler
from app.services.scraping.extractors import (
    PhoneExtractor,
    EmailExtractor,
    SocialLinkExtractor
)
from app.services.scraping.google_maps import GoogleMapsScraper
from app.services.scraping.linkedin import LinkedInScraper
from app.services.scraping.directories import DirectoryScraper
from app.config import get_settings

settings = get_settings()


class JobProcessor:
    """Main job processor that orchestrates scraping workflow."""
    
    def __init__(self):
        self.web_searcher = WebSearcher()
        self.web_crawler = WebCrawler()
        self.google_maps = GoogleMapsScraper() if settings.enable_google_maps else None
        self.linkedin = LinkedInScraper() if settings.enable_linkedin else None
        self.directories = DirectoryScraper() if settings.enable_directories else None
    
    async def process_company(self, input_text: str) -> Dict[str, any]:
        """
        Process a single company input and extract contact information.
        
        Args:
            input_text: Company name or URL
        
        Returns:
            Dict with all extracted information
        """
        # Initialize result
        result = {
            'original_input': input_text.strip(),
            'detected_input_type': None,
            'resolved_company_name': None,
            'resolved_website_url': None,
            'number_of_unique_phone_numbers_found': 0,
            'number_of_unique_emails_found': 0,
            'list_of_phone_numbers': [],
            'list_of_emails': [],
            'other_contact_links': {},
            'data_sources': [],
            'extraction_status': ExtractionStatus.NOT_FOUND,
            'confidence_score': 0.0,
            'notes': '',
            'raw_html_pages': []
        }
        
        try:
            # Step 1: Determine if input is URL or company name
            input_type, normalized_input = self._detect_input_type(input_text)
            result['detected_input_type'] = input_type
            
            # Step 2: Get website URL
            website_url = None
            
            if input_type == InputType.URL:
                website_url = normalized_input
                result['resolved_website_url'] = website_url
                # Try to extract company name from domain
                domain = urlparse(website_url).netloc.replace('www.', '')
                result['resolved_company_name'] = domain.split('.')[0].title()
            
            else:  # input_type == InputType.NAME
                result['resolved_company_name'] = normalized_input
                
                # Search for company website
                search_results = await self.web_searcher.search_company(normalized_input)
                
                if search_results:
                    website_url = self.web_searcher.find_official_domain(normalized_input, search_results)
                    result['resolved_website_url'] = website_url
                    result['notes'] += f"Found via web search. "
            
            # Step 3: Scrape website if found
            if website_url:
                website_data = await self._scrape_website(website_url)
                
                if website_data:
                    result['list_of_phone_numbers'].extend(website_data.get('phones', []))
                    result['list_of_emails'].extend(website_data.get('emails', []))
                    result['other_contact_links'].update(website_data.get('social_links', {}))
                    result['data_sources'].append('website')
                    result['raw_html_pages'] = website_data.get('pages', [])
            
            # Step 4: Try alternative sources if no contact info found
            if not result['list_of_phone_numbers'] and not result['list_of_emails']:
                
                # Try Google Maps
                if self.google_maps and result['resolved_company_name']:
                    maps_data = await self.google_maps.search_business(result['resolved_company_name'])
                    if maps_data:
                        if maps_data.get('phone'):
                            result['list_of_phone_numbers'].append(maps_data['phone'])
                        if maps_data.get('website') and not result['resolved_website_url']:
                            result['resolved_website_url'] = maps_data['website']
                        result['data_sources'].append('google_maps')
                        result['notes'] += "Found on Google Maps. "
                
                # Try LinkedIn
                if self.linkedin and result['resolved_company_name']:
                    linkedin_data = await self.linkedin.search_company(result['resolved_company_name'])
                    if linkedin_data:
                        if linkedin_data.get('website') and not result['resolved_website_url']:
                            result['resolved_website_url'] = linkedin_data['website']
                        if linkedin_data.get('linkedin_url'):
                            result['other_contact_links']['linkedin'] = linkedin_data['linkedin_url']
                        result['data_sources'].append('linkedin')
                        result['notes'] += "Found on LinkedIn. "
                
                # Try directories
                if self.directories and result['resolved_company_name']:
                    directory_data = await self.directories.search_all_directories(result['resolved_company_name'])
                    if directory_data:
                        if directory_data.get('phone'):
                            result['list_of_phone_numbers'].append(directory_data['phone'])
                        if directory_data.get('website') and not result['resolved_website_url']:
                            result['resolved_website_url'] = directory_data['website']
                        result['data_sources'].extend(directory_data.get('sources', []))
                        result['notes'] += f"Found in directories: {', '.join(directory_data.get('sources', []))}. "
            
            # Step 5: Normalize and deduplicate
            result['list_of_phone_numbers'] = PhoneExtractor.deduplicate_and_normalize(
                result['list_of_phone_numbers']
            )
            result['list_of_emails'] = EmailExtractor.deduplicate_and_normalize(
                result['list_of_emails']
            )
            
            result['number_of_unique_phone_numbers_found'] = len(result['list_of_phone_numbers'])
            result['number_of_unique_emails_found'] = len(result['list_of_emails'])
            
            # Step 6: Determine extraction status and confidence
            result['extraction_status'], result['confidence_score'] = self._calculate_status_and_confidence(result)
        
        except Exception as e:
            result['extraction_status'] = ExtractionStatus.FAILED
            result['notes'] += f"Error: {str(e)}"
        
        return result
    
    def _detect_input_type(self, input_text: str) -> tuple[InputType, str]:
        """
        Detect if input is a URL or company name.
        
        Returns:
            (InputType, normalized_value)
        """
        input_text = input_text.strip()
        
        # Check if it looks like a URL
        url_patterns = [
            r'^https?://',
            r'^www\.',
            r'\.(com|org|net|io|co|biz|info|edu|gov)',
        ]
        
        is_url = any(re.search(pattern, input_text, re.IGNORECASE) for pattern in url_patterns)
        
        if is_url:
            # Normalize URL
            if not input_text.startswith('http'):
                input_text = 'https://' + input_text.replace('www.', '')
            return InputType.URL, input_text
        else:
            # It's a company name
            return InputType.NAME, input_text
    
    async def _scrape_website(self, url: str) -> Optional[Dict[str, any]]:
        """Scrape a website and extract contact information."""
        try:
            # Crawl website pages
            pages = await self.web_crawler.crawl_domain(
                url,
                max_pages=settings.max_pages_per_domain
            )
            
            if not pages:
                return None
            
            # Extract contact info from all pages
            all_phones = []
            all_emails = []
            social_links = {}
            
            for page in pages:
                html = page.get('html', '')
                page_url = page.get('url', '')
                
                # Extract phones
                phones = PhoneExtractor.extract_from_html(html)
                all_phones.extend(phones)
                
                # Extract emails
                emails = EmailExtractor.extract_from_html(html)
                all_emails.extend(emails)
                
                # Extract social links
                page_social = SocialLinkExtractor.extract_from_html(html, page_url)
                social_links.update(page_social)
            
            return {
                'phones': all_phones,
                'emails': all_emails,
                'social_links': social_links,
                'pages': [{'url': p['url'], 'status': p['status_code']} for p in pages]
            }
        
        except Exception as e:
            print(f"Error scraping website {url}: {e}")
            return None
    
    def _calculate_status_and_confidence(self, result: Dict) -> tuple[ExtractionStatus, float]:
        """
        Calculate extraction status and confidence score.
        
        Confidence based on:
        - Source reliability (website > maps > linkedin > directories)
        - Amount of data found
        - Data quality indicators
        """
        score = 0.0
        
        # No contact info found
        if not result['list_of_phone_numbers'] and not result['list_of_emails']:
            return ExtractionStatus.NOT_FOUND, 0.0
        
        # Determine primary source
        data_sources = result.get('data_sources', [])
        
        if 'website' in data_sources:
            status = ExtractionStatus.FOUND_ON_WEBSITE
            score = 80.0  # High confidence
        elif 'google_maps' in data_sources:
            status = ExtractionStatus.FOUND_ON_MAPS
            score = 60.0  # Medium confidence
        elif 'linkedin' in data_sources:
            status = ExtractionStatus.FOUND_ON_LINKEDIN
            score = 50.0  # Medium-low confidence
        elif any(src in data_sources for src in ['yellowpages', 'yelp']):
            status = ExtractionStatus.FOUND_ON_DIRECTORY
            score = 40.0  # Lower confidence
        else:
            status = ExtractionStatus.NOT_FOUND
            return status, 0.0
        
        # Boost score based on data completeness
        if result['list_of_phone_numbers']:
            score += 10.0
        if result['list_of_emails']:
            score += 10.0
        if result['other_contact_links']:
            score += 5.0
        
        # Cap at 100
        score = min(score, 100.0)
        
        return status, score
