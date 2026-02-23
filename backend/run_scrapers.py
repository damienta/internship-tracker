"""
Orchestrates all scrapers and saves results to the database.

Usage
-----
Run once manually:
    python run_scrapers.py

Run on a schedule (every 24 hours — keeps running, Ctrl+C to stop):
    python run_scrapers.py --schedule

The `schedule` library (already in requirements.txt) handles the timing.
"""

import argparse
import logging
import time
from datetime import datetime

import schedule

from app import create_app
from models import db
from scraper.company_scraper import CompanyScraper
from scraper.greenhouse_scraper import GreenhouseScraper
from scraper.db_writer import save_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Companies supported by the HTML scraper (Taleo / Avature)
HTML_COMPANIES = ["BT Group", "HSBC", "SAP"]


def run_all_scrapers():
    """Run every scraper and save results to the database."""
    start = datetime.now()
    logger.info("=" * 60)
    logger.info(f"Scrape run started at {start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    total_saved = total_skipped = total_errors = 0

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
    except Exception as e:
        logger.error(f"[Greenhouse] scraper failed: {e}")

    # Summary
    elapsed = (datetime.now() - start).seconds
    logger.info("=" * 60)
    logger.info(
        f"Run complete in {elapsed}s — "
        f"saved={total_saved}, skipped={total_skipped}, errors={total_errors}"
    )
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Internship scraper runner")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Keep running and scrape every 24 hours instead of running once",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="Hours between scrape runs when --schedule is used (default: 24)",
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
