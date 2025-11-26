from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class JobStatus(str, enum.Enum):
    """Job status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExtractionStatus(str, enum.Enum):
    """Extraction status for individual companies."""
    FOUND_ON_WEBSITE = "found_on_website"
    FOUND_ON_MAPS = "found_on_maps"
    FOUND_ON_LINKEDIN = "found_on_linkedin"
    FOUND_ON_DIRECTORY = "found_on_directory"
    NOT_FOUND = "not_found"
    FAILED = "failed"
    CAPTCHA_BLOCKED = "captcha_blocked"


class InputType(str, enum.Enum):
    """Input type enum."""
    URL = "url"
    NAME = "name"


class Job(Base):
    """Job model to track scraping jobs."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    
    # Input data
    total_companies = Column(Integer, default=0)
    processed_companies = Column(Integer, default=0)
    
    # Settings used for this job
    settings = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Summary statistics
    total_phones_found = Column(Integer, default=0)
    total_emails_found = Column(Integer, default=0)
    companies_with_no_contact = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Celery task ID
    celery_task_id = Column(String(255), nullable=True)
    
    # Relationships
    results = relationship("CompanyResult", back_populates="job", cascade="all, delete-orphan")


class CompanyResult(Base):
    """Company result model to store extracted data."""
    __tablename__ = "company_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Input
    original_input = Column(Text, nullable=False)
    detected_input_type = Column(SQLEnum(InputType), nullable=False)
    
    # Resolved data
    resolved_company_name = Column(String(500), nullable=True)
    resolved_website_url = Column(Text, nullable=True)
    
    # Contact counts
    number_of_unique_phone_numbers_found = Column(Integer, default=0)
    number_of_unique_emails_found = Column(Integer, default=0)
    
    # Contact lists (stored as JSON arrays)
    list_of_phone_numbers = Column(JSON, default=list)
    list_of_emails = Column(JSON, default=list)
    
    # Social links (stored as JSON object)
    other_contact_links = Column(JSON, default=dict)  # {"linkedin": "...", "facebook": "..."}
    
    # Metadata
    data_sources = Column(JSON, default=list)  # ["website", "google_maps", "linkedin"]
    extraction_status = Column(SQLEnum(ExtractionStatus), nullable=False)
    
    # Quality metrics
    confidence_score = Column(Float, default=0.0)  # 0-100
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Notes and errors
    notes = Column(Text, nullable=True)
    
    # Raw data storage (optional, for debugging)
    raw_html_pages = Column(JSON, nullable=True)  # List of URLs and HTML snippets
    
    # Relationship
    job = relationship("Job", back_populates="results")
