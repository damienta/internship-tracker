"""
Saves a list of job dicts (returned by any scraper) to the database.

All scrapers return dicts with these keys:
    title, company, location, description, url,
    source_website, date_posted, deadline, scraped_at

The url column is UNIQUE — duplicate listings are skipped automatically.
"""

import logging
from datetime import datetime, date
from typing import List, Dict

from models import db, Internship

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ", # 2024-09-01T12:00:00.000Z  (Greenhouse/Lever ISO)
    "%Y-%m-%dT%H:%M:%SZ",    # 2024-09-01T12:00:00Z
    "%Y-%m-%dT%H:%M:%S",     # 2024-09-01T12:00:00
    "%Y-%m-%d",              # 2024-09-01
    "%d/%m/%Y",              # 01/09/2024  (UK format)
    "%d %B %Y",              # 01 September 2024
    "%B %d, %Y",             # September 01, 2024
]


def _parse_date(value) -> date | None:
    """
    Convert a date string or timestamp (ms) to a Python date object.
    Returns None if the value is missing or unrecognisable.
    """
    if value is None:
        return None

    # Greenhouse returns first_published as milliseconds since epoch (int)
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value / 1000).date()
        except (OSError, ValueError, OverflowError):
            return None

    if isinstance(value, date):
        return value if isinstance(value, date) else value.date()

    value = str(value).strip()
    if not value:
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    logger.debug(f"Could not parse date: {value!r}")
    return None


def _parse_datetime(value) -> datetime | None:
    """Convert a datetime string / timestamp to a Python datetime."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value / 1000)
        except (OSError, ValueError, OverflowError):
            return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


# ---------------------------------------------------------------------------
# Main save function
# ---------------------------------------------------------------------------

def save_jobs(jobs: List[Dict]) -> Dict[str, int]:
    """
    Persist a list of job dicts to the database.

    Each dict must contain at minimum: title, company, url.
    Duplicate URLs are skipped (url column is UNIQUE in the model).

    Args:
        jobs: List of job dicts from any scraper.

    Returns:
        {"saved": N, "skipped": N, "errors": N}
    """
    saved = skipped = errors = 0

    for job in jobs:
        url = job.get("url", "").strip()
        if not url:
            logger.warning(f"Skipping job with no URL: {job.get('title')}")
            errors += 1
            continue

        try:
            existing = Internship.query.filter_by(url=url).first() # Checks if URL already in database
            if existing:
                logger.debug(f"Duplicate, skipping: {url}")
                skipped += 1
                continue

            internship = Internship(
                title          = (job.get("title") or "")[:500],
                company        = (job.get("company") or "")[:200],
                location       = (job.get("location") or "")[:200],
                description    = job.get("description") or None,
                url            = url[:1000],
                source_website = (job.get("source_website") or "")[:200],
                date_posted    = _parse_date(job.get("date_posted")),
                deadline       = _parse_date(job.get("deadline")),
                scraped_at     = _parse_datetime(job.get("scraped_at")) or datetime.utcnow(),
                salary_range   = (job.get('salary_range') or "")[:100] or None,
                # Requirements populated later by NLP pipeline
                requirements   = None,
                extracted_skills = None,
                is_active      = True,
            )

            db.session.add(internship)
            db.session.commit()
            saved += 1
            logger.debug(f"Saved: {internship.company} — {internship.title}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving job '{job.get('title')}': {e}")
            errors += 1

    logger.info(f"db_writer: saved={saved}, skipped={skipped}, errors={errors}")
    return {"saved": saved, "skipped": skipped, "errors": errors}
