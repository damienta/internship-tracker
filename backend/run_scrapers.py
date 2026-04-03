"""
Orchestrates all scrapers and saves results to the database.

Usage
-----
Run once manually:
    python run_scrapers.py

Run on a schedule (recommended every 12 hours - keeps running, Ctrl+C to stop):
    python run_scrapers.py --schedule

The `schedule` library (already in requirements.txt) handles the timing.
"""

import argparse
import logging
import time
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

import requests
import schedule

from app import create_app
from models import db, Internship
from scraper.company_scraper import CompanyScraper
from scraper.greenhouse_scraper import GreenhouseScraper
from scraper.lever_scraper import LeverScraper
from scraper.ashby_scraper import AshbyScraper
from scraper.db_writer import save_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

INACTIVE_MARKERS = [
    "job not found",
    "the job you requested was not found",
    "this job is no longer available",
    "this role is no longer available",
    "position is filled",
    "position has been filled",
    "this position has been closed",
    "no longer accepting applications",
    "return to job search",
    "view all open positions",
    "view all positions",
]

SEARCH_INDEX_PATH_MARKERS = [
    "/jobs/search",
    "/job-search",
    "/jobs",
    "/careers",
    "/careers/jobs",
]

# Companies supported by the HTML scraper (Taleo / Avature)
HTML_COMPANIES = ["BT Group", "HSBC", "SAP"]


def _normalize_source(value: str) -> str:
    return (value or "").strip().lower()


def _collect_urls_by_source(jobs):
    """Build {source_website -> set(url)} from latest scraper output."""
    result = defaultdict(set)
    for job in jobs or []:
        source = _normalize_source(job.get("source_website", ""))
        url = (job.get("url") or "").strip()
        if source and url:
            result[source].add(url)
    return result


def _looks_like_search_or_index(url: str) -> bool:
    parsed = urlparse(url)
    path = (parsed.path or "").lower()
    query = (parsed.query or "").lower()
    if any(marker in path for marker in SEARCH_INDEX_PATH_MARKERS):
        return True
    if any(k in query for k in ["search=", "keywords=", "location="]):
        return True
    return False


def _is_inactive_listing(job: Internship) -> bool:
    """Generic check for listings that resolve to inactive pages."""
    original_url = (job.url or "").strip().lower()

    try:
        resp = requests.get(
            job.url,
            timeout=15,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; InternshipTrackerBot/1.0)"},
        )
    except requests.RequestException:
        return False

    if resp.status_code in {404, 410}:
        return True

    final_url = (resp.url or job.url).strip().lower()
    body = (resp.text or "").lower()

    if any(marker in body for marker in INACTIVE_MARKERS):
        return True

    if final_url != original_url and _looks_like_search_or_index(final_url):
        return True

    return False


def run_all_scrapers():
    """Run every scraper and save results to the database."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Scrape run started at {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    total_saved = total_skipped = total_errors = 0
    scraped_urls_by_source = defaultdict(set)
    successful_sources = set()

    # 1. HTML scrapers (BT, HSBC, SAP)
    for company in HTML_COMPANIES:
        logger.info(f"[HTML] Scraping {company} ...")
        try:
            scraper = CompanyScraper(company)
            jobs = scraper.scrape()
            logger.info(f"[HTML] {company}: {len(jobs)} roles found")
            stats = save_jobs(jobs)
            total_saved   += stats["saved"]
            total_skipped += stats["skipped"]
            total_errors  += stats["errors"]

            source_urls = _collect_urls_by_source(jobs)
            for source, urls in source_urls.items():
                scraped_urls_by_source[source].update(urls)
                successful_sources.add(source)
        except Exception as e:
            logger.error(f"[HTML] {company} scraper failed: {e}")

    # Greenhouse scraper (70+ companies via JSON API)
    logger.info("[Greenhouse] Scraping all companies ...")
    try:
        greenhouse = GreenhouseScraper()
        jobs = greenhouse.scrape()
        logger.info(f"[Greenhouse] {len(jobs)} roles found")
        stats = save_jobs(jobs)
        total_saved   += stats["saved"]
        total_skipped += stats["skipped"]
        total_errors  += stats["errors"]

        source_urls = _collect_urls_by_source(jobs)
        for source, urls in source_urls.items():
            scraped_urls_by_source[source].update(urls)
            successful_sources.add(source)
    except Exception as e:
        logger.error(f"[Greenhouse] scraper failed: {e}")

    # Lever scraper (verified companies via JSON API)
    logger.info("[Lever] Scraping all companies ...")
    try:
        lever = LeverScraper()
        jobs = lever.scrape()
        logger.info(f"[Lever] {len(jobs)} roles found")
        stats = save_jobs(jobs)
        total_saved   += stats["saved"]
        total_skipped += stats["skipped"]
        total_errors  += stats["errors"]

        source_urls = _collect_urls_by_source(jobs)
        for source, urls in source_urls.items():
            scraped_urls_by_source[source].update(urls)
            successful_sources.add(source)
    except Exception as e:
        logger.error(f"[Lever] scraper failed: {e}")

    # Ashby scraper (embedded JSON in window.__appData)
    logger.info("[Ashby] Scraping all companies ...")
    try:
        ashby = AshbyScraper()
        jobs = ashby.scrape()
        logger.info(f"[Ashby] {len(jobs)} roles found")
        stats = save_jobs(jobs)
        total_saved   += stats["saved"]
        total_skipped += stats["skipped"]
        total_errors  += stats["errors"]

        source_urls = _collect_urls_by_source(jobs)
        for source, urls in source_urls.items():
            scraped_urls_by_source[source].update(urls)
            successful_sources.add(source)
    except Exception as e:
        logger.error(f"[Ashby] scraper failed: {e}")

    # Mark jobs inactive if they no longer appear in successful source scrapes
    check_job_expiry(scraped_urls_by_source, successful_sources)

    # Summary
    elapsed = (datetime.now() - start).seconds
    logger.info("=" * 60)
    logger.info(
        f"Run complete in {elapsed}s - "
        f"saved={total_saved}, skipped={total_skipped}, errors={total_errors}"
    )
    logger.info("=" * 60)


def check_job_expiry(scraped_urls_by_source, successful_sources):
    """
    Mark active jobs as inactive if they are absent from the latest successful source scrape.

    Safety rules:
    - Only process sources that completed successfully in this run.
    - Skip sources that returned zero URLs (prevents mass inactivation on scraper regressions).
    """
    if not successful_sources:
        logger.warning("[Expiry] No successful sources in this run; skipping expiry check")
        return

    valid_sources = [
        source for source in sorted(successful_sources)
        if scraped_urls_by_source.get(source)
    ]
    skipped_zero = sorted(set(successful_sources) - set(valid_sources))
    if skipped_zero:
        logger.warning(
            f"[Expiry] Skipping zero-result sources to avoid false inactivation: {', '.join(skipped_zero)}"
        )

    if not valid_sources:
        logger.warning("[Expiry] All successful sources returned zero URLs; skipping expiry check")
        return

    logger.info(f"[Expiry] Checking active jobs against fresh scrape output for sources: {', '.join(valid_sources)}")

    # Pass 1: safe source-snapshot deactivation (only where we have fresh source data)
    source_jobs = Internship.query.filter(
        Internship.is_active.is_(True),
        Internship.source_website.in_(valid_sources),
    ).all()

    expired = 0
    expired_by_source = 0
    checked_by_page = 0
    expired_by_page = 0
    for job in source_jobs:
        source = _normalize_source(job.source_website)
        fresh_urls = scraped_urls_by_source.get(source, set())
        if fresh_urls and job.url not in fresh_urls:
            job.is_active = False
            expired += 1
            expired_by_source += 1
            logger.debug(f"[Expiry] Marked inactive (missing from latest scrape): {job.company} - {job.title}")

    # Pass 2: generic inactive-page check for all remaining active jobs
    remaining_jobs = Internship.query.filter(Internship.is_active.is_(True)).all()
    for job in remaining_jobs:
        checked_by_page += 1
        if _is_inactive_listing(job):
            job.is_active = False
            expired += 1
            expired_by_page += 1
            logger.debug(f"[Expiry] Marked inactive (inactive page): {job.company} - {job.title}")

    db.session.commit()
    logger.info(
        f"[Expiry] Marked {expired} active jobs as inactive "
        f"(source-missing={expired_by_source}, inactive-page={expired_by_page})"
    )
    if checked_by_page:
        logger.info(f"[Expiry] Inactive-page check: {expired_by_page}/{checked_by_page} marked inactive")


def main():
    parser = argparse.ArgumentParser(description="Internship scraper runner")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Keep running and scrape every 12 hours instead of running once",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=12,
        help="Hours between scrape runs when --schedule is used (default: 12)",
    )
    args = parser.parse_args()

    # All database operations must happen inside the Flask app context
    app = create_app()

    with app.app_context():
        if args.schedule:
            logger.info(
                f"Scheduler mode: scraping every {args.interval} hour(s). "
                "Press Ctrl+C to stop."
            )
            # Run immediately on startup, then on schedule
            run_all_scrapers()

            schedule.every(args.interval).hours.do(run_all_scrapers)

            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        else:
            # Single run
            run_all_scrapers()


if __name__ == "__main__":
    main()
