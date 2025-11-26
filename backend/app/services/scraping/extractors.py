import re
from typing import List, Set
from urllib.parse import urlparse, urljoin
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from bs4 import BeautifulSoup


class PhoneExtractor:
    """Extract and normalize phone numbers from text and HTML."""
    
    # Comprehensive phone number patterns
    PHONE_PATTERNS = [
        r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Simple format
        r'\d{10,}',  # 10+ digits
    ]
    
    @classmethod
    def extract_from_text(cls, text: str, default_region: str = "US") -> List[str]:
        """Extract phone numbers from plain text."""
        phones: Set[str] = set()
        
        for pattern in cls.PHONE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean up the match
                cleaned = re.sub(r'[^\d+]', '', match)
                if len(cleaned) >= 10:  # Minimum valid phone number length
                    phones.add(match)
        
        return list(phones)
    
    @classmethod
    def extract_from_html(cls, html: str, default_region: str = "US") -> List[str]:
        """Extract phone numbers from HTML, including tel: links."""
        phones: Set[str] = set()
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract from tel: links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('tel:'):
                phone = href.replace('tel:', '').strip()
                phones.add(phone)
        
        # Extract from text content
        text = soup.get_text()
        phones.update(cls.extract_from_text(text, default_region))
        
        return list(phones)
    
    @classmethod
    def normalize_phone(cls, phone: str, default_region: str = "US") -> str:
        """Normalize phone number to E.164 format."""
        try:
            # Remove common formatting characters
            cleaned = re.sub(r'[^\d+]', '', phone)
            
            # Parse phone number
            parsed = phonenumbers.parse(cleaned, default_region)
            
            # Check if valid
            if phonenumbers.is_valid_number(parsed):
                # Format to E.164
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            else:
                return phone  # Return original if not valid
        except Exception:
            return phone  # Return original if parsing fails
    
    @classmethod
    def deduplicate_and_normalize(cls, phones: List[str], default_region: str = "US") -> List[str]:
        """Deduplicate and normalize a list of phone numbers."""
        normalized_set: Set[str] = set()
        
        for phone in phones:
            normalized = cls.normalize_phone(phone, default_region)
            if normalized:
                normalized_set.add(normalized)
        
        return sorted(list(normalized_set))


class EmailExtractor:
    """Extract and normalize email addresses from text and HTML."""
    
    # Email pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Obfuscation patterns
    OBFUSCATION_PATTERNS = [
        (r'(\w+)\s*\[at\]\s*(\w+)\s*\[dot\]\s*(\w+)', r'\1@\2.\3'),
        (r'(\w+)\s*\(at\)\s*(\w+)\s*\(dot\)\s*(\w+)', r'\1@\2.\3'),
        (r'(\w+)\s*@\s*(\w+)\s*\.\s*(\w+)', r'\1@\2.\3'),
    ]
    
    @classmethod
    def extract_from_text(cls, text: str) -> List[str]:
        """Extract email addresses from plain text."""
        emails: Set[str] = set()
        
        # De-obfuscate text first
        deobfuscated = cls.deobfuscate_text(text)
        
        # Extract emails
        matches = re.findall(cls.EMAIL_PATTERN, deobfuscated, re.IGNORECASE)
        emails.update(matches)
        
        return list(emails)
    
    @classmethod
    def extract_from_html(cls, html: str) -> List[str]:
        """Extract email addresses from HTML, including mailto: links."""
        emails: Set[str] = set()
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract from mailto: links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('mailto:'):
                email = href.replace('mailto:', '').strip().split('?')[0]
                emails.add(email)
        
        # Extract from text content
        text = soup.get_text()
        emails.update(cls.extract_from_text(text))
        
        return list(emails)
    
    @classmethod
    def deobfuscate_text(cls, text: str) -> str:
        """De-obfuscate email addresses in text."""
        result = text
        for pattern, replacement in cls.OBFUSCATION_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    @classmethod
    def normalize_email(cls, email: str) -> str:
        """Normalize email address (lowercase and validate)."""
        try:
            # Validate and normalize
            validated = validate_email(email, check_deliverability=False)
            return validated.normalized.lower()
        except EmailNotValidError:
            # Return lowercase version if validation fails
            return email.lower().strip()
    
    @classmethod
    def deduplicate_and_normalize(cls, emails: List[str]) -> List[str]:
        """Deduplicate and normalize a list of emails."""
        normalized_set: Set[str] = set()
        
        for email in emails:
            normalized = cls.normalize_email(email)
            if normalized and '@' in normalized:
                normalized_set.add(normalized)
        
        return sorted(list(normalized_set))


class SocialLinkExtractor:
    """Extract social media links from HTML."""
    
    SOCIAL_PLATFORMS = {
        'linkedin': [r'linkedin\.com'],
        'facebook': [r'facebook\.com', r'fb\.com'],
        'twitter': [r'twitter\.com', r'x\.com'],
        'instagram': [r'instagram\.com'],
    }
    
    @classmethod
    def extract_from_html(cls, html: str, base_url: str = "") -> dict:
        """Extract social media links from HTML."""
        social_links = {}
        soup = BeautifulSoup(html, 'lxml')
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            
            # Make absolute URL if needed
            if base_url and not href.startswith('http'):
                href = urljoin(base_url, href)
            
            # Check each platform
            for platform, patterns in cls.SOCIAL_PLATFORMS.items():
                for pattern in patterns:
                    if re.search(pattern, href):
                        if platform not in social_links:
                            social_links[platform] = href
                        break
        
        return social_links


class ContactPageDetector:
    """Detect potential contact pages from links."""
    
    CONTACT_KEYWORDS = [
        'contact', 'about', 'team', 'staff', 'people',
        'connect', 'reach', 'get-in-touch', 'support',
        'help', 'office', 'location', 'address'
    ]
    
    @classmethod
    def is_contact_page(cls, url: str, text: str = "") -> bool:
        """Check if a URL or link text suggests a contact page."""
        check_text = (url + " " + text).lower()
        return any(keyword in check_text for keyword in cls.CONTACT_KEYWORDS)
    
    @classmethod
    def find_contact_links(cls, html: str, base_url: str) -> List[str]:
        """Find potential contact page links in HTML."""
        contact_links = []
        soup = BeautifulSoup(html, 'lxml')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Make absolute URL
            absolute_url = urljoin(base_url, href)
            
            # Check if it's a contact-related link
            if cls.is_contact_page(absolute_url, text):
                # Avoid duplicates and external links
                if urlparse(absolute_url).netloc == urlparse(base_url).netloc:
                    contact_links.append(absolute_url)
        
        return list(set(contact_links))
