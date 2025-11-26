# RankRiseUSA Web Scraper & Lead Extractor

A production-ready web application that automatically extracts contact information (phone numbers, emails, social media links) from company websites and public sources.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2+-blue.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ⚠️ Legal & Ethical Notice

**IMPORTANT**: This tool is for educational and research purposes only. When using this scraper:

- ✅ Always respect robots.txt files
- ✅ Respect website terms of service
- ✅ Use reasonable rate limiting
- ✅ Do not use for spam or unauthorized data collection
- ✅ Comply with applicable laws (GDPR, CCPA, etc.)

**Scraping Google Maps, LinkedIn, and other sites may violate their Terms of Service.** The scrapers for these sources are best-effort and may not work reliably due to anti-scraping measures. Use at your own risk.

## 🚀 Features

### Multi-Source Data Extraction
- **Primary**: Scrapes company websites with intelligent page crawling
- **Fallback sources**: Google Maps, LinkedIn, YellowPages, Yelp
- **Smart detection**: Automatically determines if input is a URL or company name

### Intelligent Extraction
- 📞 **Phone numbers**: Regex-based extraction with E.164 normalization
- 📧 **Emails**: De-obfuscation support for masked emails
- 🔗 **Social media**: LinkedIn, Facebook, Twitter, Instagram links
- 🎯 **Contact page detection**: Automatically finds /contact, /about pages

### Data Quality
- ✨ Deduplication and normalization
- 📊 Confidence scoring (0-100) based on source reliability
- 📝 Detailed notes and data source tracking
- 🔍 Extraction status per company

### Export & Reporting
- 📑 CSV export
- 📊 Excel export with summary sheet
- 📦 ZIP archive with raw HTML and JSON
- 📈 Aggregated statistics

### Modern UI
- 🎨 Beautiful dark-mode interface with Tailwind CSS
- 📤 Drag-and-drop file upload
- ⚡ Real-time progress updates via WebSocket
- 📱 Responsive design

## 🏗️ Technology Stack

### Backend
- **Framework**: Python 3.11+ with FastAPI
- **Async HTTP**: httpx for concurrent requests
- **HTML Parsing**: BeautifulSoup4, lxml
- **Browser Automation**: Playwright (headless, for JS-heavy sites)
- **Phone Normalization**: phonenumbers library
- **Job Queue**: Celery with Redis
- **Database**: SQLAlchemy 2.0 (SQLite/PostgreSQL)
- **Export**: pandas, openpyxl

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: Tailwind CSS
- **HTTP**: axios
- **Tables**: TanStack Table
- **File Upload**: react-dropzone
- **Icons**: Lucide React

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Message Broker**: Redis
- **Web Server**: Nginx (in production)

## 📦 Installation & Setup

### Prerequisites
- Docker and Docker Compose (recommended)
- OR Python 3.11+ and Node.js 18+ (for local development)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd RankRiseUSAWebScraper

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment variables
cp .env.example .env

# Start Redis (required for Celery)
# On macOS: brew services start redis
# On Linux: sudo service redis-server start
# On Windows: Download Redis from https://github.com/microsoftarchive/redis/releases

# Run database migrations (creates tables)
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"

# Start backend server
uvicorn app.main:app --reload --port 8000

# In a new terminal, start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:5173
```

## 🎯 Usage

### Web UI

1. **Open the application** at `http://localhost:3000` (or `localhost:5173` for local dev)

2. **Input companies** using one of two methods:
   - **Text input**: Enter company names or URLs (comma or newline separated)
   - **File upload**: Upload a CSV or Excel file with company names in the first column

3. **Monitor progress**: Watch real-time progress as companies are processed

4. **View results**: See extracted contact information in a detailed table

5. **Export data**: Download results in CSV, Excel, or ZIP format

### API Usage

#### Create Job

```bash
# With company names/URLs
curl -X POST http://localhost:8000/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "companies": ["Google Inc", "https://microsoft.com", "Apple"]
  }'

# With file upload
curl -X POST http://localhost:8000/api/jobs/ \
  -F "file=@companies.csv"
```

#### Get Job Status

```bash
curl http://localhost:8000/api/jobs/1/status
```

#### Download Exports

```bash
# CSV
curl -o results.csv http://localhost:8000/api/jobs/1/export/csv

# Excel
curl -o results.xlsx http://localhost:8000/api/jobs/1/export/xlsx

# ZIP Archive
curl -o results.zip http://localhost:8000/api/jobs/1/export/zip
```

## ⚙️ Configuration

Edit `backend/.env` to configure:

```env
# Scraping Settings
SCRAPING_RATE_LIMIT=2.0          # Seconds between requests per domain
SCRAPING_CONCURRENCY=5           # Max concurrent scrapers
SCRAPING_MAX_RETRIES=3          # Retry count for failed requests
SCRAPING_TIMEOUT=30             # Request timeout in seconds

# Feature Flags
RESPECT_ROBOTS_TXT=true         # Respect robots.txt
ENABLE_PLAYWRIGHT=true          # Enable JS-heavy site support
ENABLE_GOOGLE_MAPS=true         # Enable Google Maps fallback
ENABLE_LINKEDIN=true            # Enable LinkedIn fallback
ENABLE_DIRECTORIES=true         # Enable directory fallbacks

# Crawling Limits
MAX_PAGES_PER_DOMAIN=10        # Max pages to crawl per company
MAX_DEPTH=2                     # Max crawl depth

# Proxy (optional)
# HTTP_PROXY=http://proxy:8080
# HTTPS_PROXY=http://proxy:8080
```

## 📊 Output Format

### CSV/Excel Columns

- `Original Input`: User-provided company name or URL
- `Input Type`: `url` or `name`
- `Company Name`: Resolved company name
- `Website URL`: Found website URL
- `Phone Count`: Number of unique phones found
- `Email Count`: Number of unique emails found
- `Phone Numbers`: Comma-separated list
- `Emails`: Comma-separated list
- `LinkedIn/Facebook/Twitter/Instagram`: Social media links
- `Data Sources`: Where data was found (website, google_maps, linkedin, etc.)
- `Extraction Status`: found_on_website, found_on_maps, not_found, etc.
- `Confidence Score`: 0-100 quality score
- `Timestamp`: When processed
- `Notes`: Any issues or notes

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# With coverage
pytest --cov=app tests/
```

## 🐛 Troubleshooting

### No contact info found
- Some websites may block scrapers or use CAPTCHAs
- Try adjusting `SCRAPING_RATE_LIMIT` to be more polite
- Check if robots.txt is blocking access

### Playwright errors
- Ensure Playwright browsers are installed: `playwright install chromium`
- In Docker, this is handled automatically

### Celery worker not processing
- Ensure Redis is running: `redis-cli ping`
- Check Celery logs for errors
- Verify `CELERY_BROKER_URL` in `.env`

### Import errors
- Make sure you're in the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛣️ Roadmap

- [ ] OCR support for contact info in images
- [ ] More directory sources (Manta, BBB, etc.)
- [ ] Proxy rotation support
- [ ] CAPTCHA detection and handling
- [ ] Advanced filtering and search in UI
- [ ] Job scheduling and automation
- [ ] Multi-language support

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 💡 Acknowledgments

- Built with FastAPI, React, Tailwind CSS
- Uses open-source libraries: BeautifulSoup, Playwright, phonenumbers
- Inspired by the need for ethical, transparent web scraping tools

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review API docs at `/docs` endpoint

---

**Remember**: Always use this tool responsibly and ethically. Respect website owners and their terms of service.
# lead_srcaper
