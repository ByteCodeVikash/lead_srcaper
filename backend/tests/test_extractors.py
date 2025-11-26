import pytest
from app.services.scraping.extractors import PhoneExtractor, EmailExtractor


class TestPhoneExtractor:
    """Test phone number extraction and normalization."""
    
    def test_extract_us_phone(self):
        text = "Call us at (555) 123-4567 or 555-987-6543"
        phones = PhoneExtractor.extract_from_text(text)
        assert len(phones) >= 2
    
    def test_normalize_phone(self):
        phone = "(555) 123-4567"
        normalized = PhoneExtractor.normalize_phone(phone, "US")
        assert normalized.startswith('+')
    
    def test_deduplicate_phones(self):
        phones = ["(555) 123-4567", "555-123-4567", "+15551234567"]
        result = PhoneExtractor.deduplicate_and_normalize(phones, "US")
        # Should deduplicate to one number
        assert len(result) == 1


class TestEmailExtractor:
    """Test email extraction and normalization."""
    
    def test_extract_email(self):
        text = "Contact us at info@example.com or support@example.org"
        emails = EmailExtractor.extract_from_text(text)
        assert len(emails) == 2
        assert "info@example.com" in emails
    
    def test_deobfuscate_email(self):
        text = "Email: john [at] example [dot] com"
        deobfuscated = EmailExtractor.deobfuscate_text(text)
        assert "@" in deobfuscated
        assert "example.com" in deobfuscated
    
    def test_normalize_email(self):
        email = "INFO@EXAMPLE.COM"
        normalized = EmailExtractor.normalize_email(email)
        assert normalized == "info@example.com"
    
    def test_deduplicate_emails(self):
        emails = ["info@example.com", "INFO@EXAMPLE.COM", "contact@example.com"]
        result = EmailExtractor.deduplicate_and_normalize(emails)
        assert len(result) == 2  # info and contact


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
