from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./scraper.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Scraping Configuration
    scraping_rate_limit: float = 2.0  # seconds between requests
    scraping_concurrency: int = 5
    scraping_max_retries: int = 3
    scraping_timeout: int = 30
    scraping_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Proxy Configuration
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    socks_proxy: Optional[str] = None
    
    # Feature Flags
    respect_robots_txt: bool = True
    enable_ocr: bool = False
    enable_playwright: bool = True
    enable_google_maps: bool = True
    enable_linkedin: bool = True
    enable_directories: bool = True
    
    # Crawling Limits
    max_pages_per_domain: int = 10
    max_depth: int = 2
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Application
    env: str = "development"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Export
    export_dir: str = "./exports"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
