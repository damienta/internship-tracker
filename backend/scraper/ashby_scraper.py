"""ashby_scraper - scrapes roles from Ashby-hosted boards.

Unlike Lever/Greenhouse, Ashby data is embedded in `window.__appData` JSON
inside each jobs page HTML (e.g. https://jobs.ashbyhq.com/{slug}).

This scraper builds a company list from existing Greenhouse + Lever companies
plus a curated set of common Ashby-hosted companies.
"""

import json
import html as html_module
import logging
import re
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from scraper.greenhouse_scraper import GREENHOUSE_COMPANIES
from scraper.lever_scraper import LEVER_COMPANIES

logger = logging.getLogger(__name__)

ROLE_KEYWORDS = ["intern", "internship", "graduate", "grad", "placement", "apprentice", "junior"]
UK_LOCATION_KEYWORDS = [
    "united kingdom",
    "uk",
    "england",
    "scotland",
    "wales",
    "northern ireland",
    "great britain",
    "gb",
    "london",
    "manchester",
    "edinburgh",
    "bristol",
    "birmingham",
    "glasgow",
    "leeds",
    "cambridge",
    "reading",
]

# ---------------------------------------------------------------------------
# Company list: (display_name, [ashby_slug_candidates])
# To add a company: add name to COMMON_ASHBY_COMPANIES and verify slug at
# https://jobs.ashbyhq.com/{slug}
# ---------------------------------------------------------------------------
COMMON_ASHBY_COMPANIES = [
    "Notion",
    "Monzo",
    "OpenAI",
    "Anthropic",
    "Figma",
    "Scale AI",
    "Vercel",
    "Rippling",
    "Deel",
    "Replit",
    "Retool",
    "Plaid",
    "Mercury",
    "Anduril",
    "Airtable",
    "Ramp",
    "Snyk",
    "Canva",
    "Miro",
    "Webflow",
    "ClickUp",
    "Linear",
    "Datadog",
    "Brex",
    "Gusto",
    "Synthesia",
    "Perplexity",
    "Hugging Face",
    "Character AI",
    "ElevenLabs",
]

def _slugify_company_name(name: str) -> str:
    """Normalises company names into slug text by lowercasing, replacing non-alphanumeric characters with hyphens."""
    value = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return value


def _build_slug_candidates(company_name: str, known_slugs: Optional[List[str]] = None) -> List[str]:
    """Builds multiple slug guesses for one company"""
    known_slugs = known_slugs or []
    generated = _slugify_company_name(company_name)
    generated_no_hyphen = generated.replace("-", "")

    pieces = [p for p in generated.split("-") if p]
    first_word = pieces[0] if pieces else ""
    first_two_words = "-".join(pieces[:2]) if len(pieces) >= 2 else first_word

    candidates: List[str] = []
    for candidate in [generated, generated_no_hyphen, first_word, first_two_words, *known_slugs]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    return candidates


def _build_ashby_companies() -> List[Tuple[str, List[str]]]:
    """Combines Greenhouse + Lever company seeds with common Ashby company seeds and attaches slug candidates."""
    merged: "OrderedDict[str, List[str]]" = OrderedDict()

    for company_name, slug in GREENHOUSE_COMPANIES + LEVER_COMPANIES:
        if company_name not in merged:
            merged[company_name] = []
        if slug and slug not in merged[company_name]:
            merged[company_name].append(slug)

    for company_name in COMMON_ASHBY_COMPANIES:
        if company_name not in merged:
            merged[company_name] = []

    result: List[Tuple[str, List[str]]] = []
    for company_name, known_slugs in merged.items():
        result.append((company_name, _build_slug_candidates(company_name, known_slugs)))

    return result

ASHBY_COMPANIES = _build_ashby_companies()


class AshbyScraper:
    """Scrapes Ashby jobs by discovering valid board slugs and parsing appData JSON."""

    BASE_URL = "https://jobs.ashbyhq.com/{slug}"

    def __init__(
        self,
        companies: Optional[List[Tuple[str, List[str]]]] = None,
        uk_only: bool = True,
        timeout: int = 12,
        workers: int = 8,
    ):
        self.companies = companies or ASHBY_COMPANIES
        self.uk_only = uk_only
        self.timeout = timeout
        self.workers = workers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; InternshipTracker/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        })

    def _is_relevant_title(self, title: str) -> bool:
        t = (title or "").lower()
        return any(re.search(r"\b" + re.escape(kw) + r"\b", t) for kw in ROLE_KEYWORDS)

    def _is_uk_location(self, location: str) -> bool:
        loc = (location or "").lower()
        return any(kw in loc for kw in UK_LOCATION_KEYWORDS)

    def _fetch_posting_description(self, slug: str, posting_id: str) -> str:
        """Fetches an individual posting page and extracts description text from posting.descriptionPlainText or posting.descriptionHtml"""
        url = f"https://jobs.ashbyhq.com/{slug}/{posting_id}"
        try:
            r = self.session.get(url, timeout=self.timeout)
            if r.status_code != 200:
                return ""
        except requests.RequestException:
            return ""

        app_data = self._extract_app_data(r.text)
        posting = (app_data or {}).get("posting") or {}
        if isinstance(posting, dict):
            plain = (posting.get("descriptionPlainText") or "").strip()
            if plain:
                return plain

            html_text = posting.get("descriptionHtml") or ""
            if html_text:
                return BeautifulSoup(html_module.unescape(html_text), "html.parser").get_text(" ", strip=True)

        return ""

    def _extract_app_data(self, html: str) -> Optional[dict]:
        """Finds and parses window.__appData JSON embedded in Ashby HTML"""
        marker = "window.__appData = "
        start = html.find(marker)
        if start == -1:
            return None

        i = html.find("{", start)
        if i == -1:
            return None

        depth = 0
        in_string = False
        escape = False
        end = None

        for idx in range(i, len(html)):
            ch = html[idx]

            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break

        if not end:
            return None

        try:
            return json.loads(html[i:end])
        except json.JSONDecodeError:
            return None

    def _fetch_board_data(self, slug: str) -> Optional[dict]:
        """Fetches one Ashby board page by slug and validates that jobBoard.jobPostings exists"""
        url = self.BASE_URL.format(slug=slug)
        try:
            r = self.session.get(url, timeout=self.timeout)
            if r.status_code != 200:
                return None
        except requests.RequestException:
            return None

        app_data = self._extract_app_data(r.text)
        if not app_data:
            return None

        job_board = app_data.get("jobBoard") or {}
        if not isinstance(job_board, dict):
            return None

        if not isinstance(job_board.get("jobPostings", []), list):
            return None

        return app_data

    def _resolve_slug(self, company_name: str, slug_candidates: List[str]) -> Optional[str]:
        """Tries candidate slugs and returns first one with valid data"""
        for slug in slug_candidates:
            if self._fetch_board_data(slug):
                return slug

        logger.debug(f"[Ashby] {company_name}: no valid Ashby board found")
        return None

    def scrape_company(self, slug: str, company_name: str) -> List[Dict]:
        """If resolved slug it loops through each posting, filters by title and UK location. Gets posting_id, desc and returns job dictionaries"""
        app_data = self._fetch_board_data(slug)
        if not app_data:
            return []

        job_board = app_data.get("jobBoard") or {}
        if not isinstance(job_board, dict):
            return []

        postings = job_board.get("jobPostings") or []
        results: List[Dict] = []

        for posting in postings:
            if not isinstance(posting, dict):
                continue

            title = posting.get("title", "")
            if not self._is_relevant_title(title):
                continue

            location_name = (posting.get("locationName") or "").strip()
            secondary_locations = posting.get("secondaryLocations") or []
            secondary_names = [
                loc.get("locationName", "")
                for loc in secondary_locations
                if isinstance(loc, dict)
            ]
            combined_location = ", ".join([location_name, *[name for name in secondary_names if name]]) or "Location not specified"

            if self.uk_only and not self._is_uk_location(combined_location):
                continue

            posting_id = posting.get("id")
            if not posting_id:
                continue

            description = self._fetch_posting_description(slug, posting_id)

            results.append({
                "title": title,
                "company": company_name,
                "location": combined_location,
                "description": description,
                "url": f"https://jobs.ashbyhq.com/{slug}/{posting_id}",
                "source_website": "ashby",
                "date_posted": posting.get("publishedDate") or posting.get("updatedAt"),
                "deadline": posting.get("applicationDeadline"),
                "salary_range": None,
                "scraped_at": datetime.now().isoformat(),
            })

        logger.info(f"[Ashby] {company_name}: {len(results)} relevant UK roles found")
        return results

    def scrape(self) -> List[Dict]:
        """Resolves slugs for all companies then scrapes them and merges results"""
        logger.info(f"[Ashby] Scraping {len(self.companies)} companies ({self.workers} workers)...")
        all_results: List[Dict] = []

        targets: List[Tuple[str, str]] = []
        for company_name, slug_candidates in self.companies:
            slug = self._resolve_slug(company_name, slug_candidates)
            if slug:
                targets.append((company_name, slug))

        logger.info(f"[Ashby] Resolved {len(targets)} active Ashby boards")

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {
                pool.submit(self.scrape_company, slug, company_name): company_name
                for company_name, slug in targets
            }
            for future in as_completed(futures):
                company_name = futures[future]
                try:
                    jobs = future.result()
                    all_results.extend(jobs)
                except Exception as e:
                    logger.warning(f"[Ashby] {company_name}: unexpected error - {e}")

        logger.info(f"[Ashby] Done: {len(all_results)} relevant roles")
        return all_results
