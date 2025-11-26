# RankRiseUSA Web Scraper - Quick Start Guide

## Fastest Way to Get Started

### Prerequisites
- Docker and Docker Compose installed
- Internet connection

### 3-Step Setup

```bash
# 1. Navigate to project directory
cd RankRiseUSAWebScraper

# 2. Start all services
docker-compose up -d

# 3. Wait ~30 seconds for services to start, then access:
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

That's it! The application is now running.

## First Time Usage

1. **Open your browser** to http://localhost:3000

2. **Enter company names** in the text area:
   ```
   Google Inc
   Microsoft Corporation
   https://apple.com
   ```

3. **Click "Start Scraping"**

4. **Watch real-time progress** as the scraper processes each company

5. **Download results** when complete (CSV, Excel, or ZIP)

## Viewing Logs

```bash
# All services
docker-compose logs -f

# Just backend
docker-compose logs -f backend

# Just worker
docker-compose logs -f worker
```

## Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove data
docker-compose down -v
```

## Troubleshooting

### Port conflicts
If ports 3000, 8000, or 6379 are in use, edit `docker-compose.yml` to change them.

### Services not starting
```bash
# Rebuild images
docker-compose build

# Start fresh
docker-compose down -v
docker-compose up -d
```

### No results found
- Some sites block scrapers or use CAPTCHAs
- Try simpler company names like "Google" instead of "Google LLC"
- Check logs for specific errors

## Configuration

Edit `backend/.env` to customize:
- `SCRAPING_RATE_LIMIT` - Seconds between requests (default: 2.0)
- `SCRAPING_CONCURRENCY` - Max concurrent scrapers (default: 5)
- `RESPECT_ROBOTS_TXT` - Honor robots.txt (default: true)

After changes, restart:
```bash
docker-compose restart backend worker
```

## What Gets Scraped

✅ Company websites (homepage, /contact, /about, /team)
✅ Phone numbers (normalized to E.164 format)
✅ Email addresses (de-obfuscated if needed)
✅ Social links (LinkedIn, Facebook, Twitter, Instagram)
✅ Google Maps business pages (fallback)
✅ LinkedIn company pages (fallback)
✅ Directory sites (YellowPages, Yelp)

## Legal Notice

⚠️ This tool is for educational purposes only. Always:
- Respect robots.txt
- Respect website terms of service
- Use reasonable rate limiting
- Do not use for spam

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [walkthrough.md](walkthrough.md) for technical details
- Visit http://localhost:8000/docs for API documentation
- Try the example CSV file in `examples/input_example.csv`

## Support

- GitHub Issues for bugs
- API docs at `/docs` endpoint
- Check logs with `docker-compose logs`

---

**Ready to scrape? Start with `docker-compose up -d` and visit http://localhost:3000!**
