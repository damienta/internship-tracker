# Scraper

This package handles all job data collection for the internship tracker. It pulls listings from three different sources - company HTML career pages, the Greenhouse ATS API, and the Lever ATS API - and feeds the results into the PostgreSQL database via `db_writer.py`.

Everything is orchestrated by `run_scrapers.py` in the backend root.

---

## Overview

The scraper runs in three stages:

1. **HTML scrapers** - fetch career pages directly from BT, HSBC, and SAP using BeautifulSoup.
2. **Greenhouse** - queries the public Greenhouse JSON API for ~120 companies concurrently.
3. **Lever** - queries the public Lever JSON API for ~124 companies concurrently.

Each stage returns a list of job dicts in a consistent format that `DbWriter` writes to PostgreSQL.

---

## Requirements

- Python 3.11+
- PostgreSQL running on `localhost:5432`
- Dependencies installed: `pip install -r requirements.txt`
- `.env` file in `backend/` with `DATABASE_URL` set

---

## Running the Scrapers

From the `backend/` directory:

```bash
python run_scrapers.py
```

This runs all three scraper stages in sequence and writes results to the database.

---

## Key Classes

### `BaseScraper` - `base_scraper.py`
The foundation for the HTML scrapers. It handles making HTTP requests, parsing HTML with BeautifulSoup, and filtering job titles against a set of entry-level keywords (`intern`, `graduate`, `placement`, etc.). Companies that publish their own career pages (BT, HSBC, SAP) use scrapers that inherit from this class.

### `CompanyScraper` - `company_scraper.py`
A generic HTML scraper that tries to work on any career page without prior knowledge of its structure. It attempts a range of common CSS patterns to find job listings. Used as a fallback when a company does not have a dedicated scraper.

### `company_configs.py`
A dictionary of known company career page configurations - the URL to scrape and the CSS selectors needed to find job titles and locations. Any company listed here will be scraped reliably without guesswork.

### `GreenhouseScraper` - `greenhouse_scraper.py`
Calls the public Greenhouse jobs API (`boards-api.greenhouse.io`) for a list of companies. Greenhouse is an ATS used by many tech companies, and its API returns structured JSON, making this much more reliable than HTML scraping. Runs concurrently across all companies using `ThreadPoolExecutor`.

### `LeverScraper` - `lever_scraper.py`
Same idea as `GreenhouseScraper` but for the Lever ATS (`api.lever.co`). Also runs concurrently. Both Greenhouse and Lever scrapers filter results to UK locations only and discard anything that is not an internship or graduate role.

### `DbWriter` - `db_writer.py`
Takes the list of job dicts returned by any scraper and writes them to the `internships` table in PostgreSQL. Handles deduplication so re-running the scrapers does not create duplicate entries.

---

## Adding a Company

- **Greenhouse**: add `("Display Name", "slug")` to `GREENHOUSE_COMPANIES` in `greenhouse_scraper.py`. Verify the slug at `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs`.
- **Lever**: add `("Display Name", "slug")` to `LEVER_COMPANIES` in `lever_scraper.py`. Verify at `https://api.lever.co/v0/postings/{slug}?mode=json`.
- **Custom HTML**: add a config entry to `company_configs.py` with the careers URL and CSS selectors.

---

## Database

The scrapers write to the `internships` table in PostgreSQL. The schema is defined in `models.py`.

**To view current data:**
```sql
SELECT title, company, location, source_website FROM internships ORDER BY scraped_at DESC LIMIT 20;
```

**To clear all scraped data and start fresh:**
```sql
TRUNCATE TABLE internships;
```

**To check how many roles are stored per source:**
```sql
SELECT source_website, COUNT(*) FROM internships GROUP BY source_website;
```

Re-running `run_scrapers.py` will not create duplicates — `DbWriter` checks for existing entries by URL before inserting.

---

## Tests

_Tests to be added._

---

## Known Limitations

- Some Lever/Greenhouse slugs become stale if a company stops using that ATS — these will silently return no results or a 404.
- HTML scrapers (BT, HSBC, SAP) are fragile to page structure changes and may need updating if the company redesigns their careers page.
- Location filtering for Lever and Greenhouse uses keyword matching (`london`, `uk`, etc.) so roles listed with unusual location strings may be missed.
