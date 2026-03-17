"""
greenhouse_scraper - calls the public Greenhouse jobs API for a list of companies.

Scrapes UK internship/graduate roles from companies using the Lever ATS
via the public JSON API - no authentication required.

API endpoint:
    GET https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
    → {"jobs": [{"id", "title", "location": {"name"}, "content", "absolute_url", ...}]}

Adding a new company:
    Just add an entry to GREENHOUSE_COMPANIES below - no other code changes needed.

Usage:
    scraper = GreenhouseScraper()
    jobs = scraper.scrape() # all companies
    jobs = scraper.scrape_company("graphcore", "Graphcore")  # one company
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Company list: (display_name, greenhouse_slug)
# To add a company: find their slug from https://boards.greenhouse.io/{slug}
# ---------------------------------------------------------------------------
GREENHOUSE_COMPANIES: List[tuple] = [
    ("Graphcore", "graphcore"),
    ("DeepMind", "deepmind"),
    ("Wayve", "wayve"),
    ("PolyAI", "polyai"),
    ("Behavox", "behavox"),
    ("Peak AI", "peak"),
    ("Featurespace", "featurespace"),
    ("Quantexa", "quantexa"),
    ("Eigen Technologies", "eigen-technologies"),
    ("Tractable", "tractable"),
    ("Robin AI", "robin-ai"),
    ("Robin AI", "robinai"),
    ("Faculty", "faculty"),
    ("Faculty", "faculty-ai"),
    ("Faculty", "faculty-science"),
    ("Improbable", "improbable"),
    ("Improbable", "improbable-worlds"),
    ("Darktrace", "darktrace"),
    ("Tessian", "tessian"),
    ("Tessian", "tessian-ltd"),
    ("Synthesia", "synthesia"),
    ("Onfido", "onfido"),
    ("Monzo", "monzo"),
    ("Monzo", "monzo-bank"),
    ("Revolut", "revolut"),
    ("Revolut", "revolut-ltd"),
    ("Wise", "wise"),
    ("Cleo", "cleo"),
    ("Tide", "tide"),
    ("Zilch", "zilch"),
    ("SumUp", "sumup"),
    ("Starling Bank", "starling-bank"),
    ("Starling Bank", "starlingbank"),
    ("OakNorth", "oaknorth"),
    ("OakNorth", "oaknorth-bank"),
    ("Freetrade", "freetrade"),
    ("Freetrade", "freetrade-ltd"),
    ("Griffin Bank", "griffin-bank"),
    ("Griffin Bank", "griffin"),
    ("Curve", "curve"),
    ("Curve", "curve-fintech"),
    ("Monese", "monese"),
    ("Paysafe", "paysafe"),
    ("Checkout.com", "checkout"),
    ("Checkout.com", "checkoutcom"),
    ("GoCardless", "gocardless"),
    ("Klarna", "klarna"),
    ("N26", "n26"),
    ("Deliveroo", "deliveroo"),
    ("Snyk", "snyk"),
    ("Thought Machine", "thought-machine"),
    ("Thought Machine", "thoughtmachine"),
    ("Multiverse", "multiverse"),
    ("Multiverse", "multiverse-computing"),
    ("AND Digital", "and-digital"),
    ("AND Digital", "anddigital"),
    ("Kainos", "kainos"),
    ("Kainos", "kainos-group"),
    ("Softwire", "softwire"),
    ("Softwire", "softwire-technology"),
    ("Cazoo", "cazoo"),
    ("Cazoo", "cazoo-ltd"),
    ("Elvie", "elvie"),
    ("Elvie", "elvie-ltd"),
    ("Citymapper", "citymapper"),
    ("Bulb", "bulb"),
    ("Octopus Energy", "octopusenergy"),
    ("Octopus Energy", "octopus-energy"),
    ("Arm", "arm"),
    ("Dyson", "dyson"),
    ("Dyson", "dyson-ltd"),
    ("BAE Systems", "bae-systems"),
    ("BAE Systems", "baesystems"),
    ("Airbnb", "airbnb"),
    ("Airbnb", "airbnb-inc"),
    ("Shopify", "shopify"),
    ("Databricks", "databricks"),
    ("Figma", "figma"),
    ("Notion", "notion"),
    ("Airtable", "airtable"),
    ("Rippling", "rippling"),
    ("Brex", "brex"),
    ("Brex", "brex-inc"),
    ("Stripe", "stripe"),
    ("Stripe", "stripe-inc"),
    ("Cohere", "cohere"),
    ("Anthropic", "anthropic"),
    ("Mistral", "mistral"),
    ("Mistral", "mistral-ai"),
    ("Stability AI", "stability"),
    ("Stability AI", "stability-ai"),
    ("Scale AI", "scaleai"),
    ("Scale AI", "scale-ai"),
    ("Waymo", "waymo"),
    ("CoreWeave", "coreweave"),
    ("Lambda Labs", "lambda"),
    ("Lambda Labs", "lambda-labs"),
    ("Recursion", "recursion"),
    ("Benchling", "benchling"),
    ("Palantir", "palantir"),
    ("Palantir", "palantir-technologies"),
    ("Citadel", "citadel"),
    ("Citadel", "citadel-securities"),
    ("Optiver", "optiver"),
    ("IMC Trading", "imc-trading"),
    ("IMC Trading", "imc"),
    ("Bloomberg", "bloomberg"),
    ("Bloomberg", "bloomberg-lp"),
    ("Two Sigma", "two-sigma"),
    ("Two Sigma", "twosigma"),
    ("Hudson River Trading", "hudson-river-trading"),
    ("Hudson River Trading", "hrt"),
    ("Jane Street", "janestreet"),
    ("Jane Street", "jane-street"),
]

# Keywords that identify relevant roles (checked against title, case-insensitive)
ROLE_KEYWORDS = ["intern", "internship", "graduate", "grad", "junior", "placement"]

# Location strings that confirm UK role (checked against location name)
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


class GreenhouseScraper:
    """Scrapes multiple companies via the public Greenhouse jobs board API retrieving JSON."""

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    def __init__(
        self,
        companies: Optional[List[tuple]] = None,
        uk_only: bool = True,
        timeout: int = 10,
        workers: int = 10,
    ):
        """
        Args:
            companies: list of (name, slug) tuples. Defaults to GREENHOUSE_COMPANIES.
            uk_only:   if True, only return roles with a UK/London location.
            timeout:   request timeout in seconds.
            workers:   number of concurrent threads.
        """
        self.companies = companies or GREENHOUSE_COMPANIES
        self.uk_only = uk_only
        self.timeout = timeout
        self.workers = workers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; InternshipTracker/1.0)",
            "Accept": "application/json",
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=workers, pool_maxsize=workers)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # Filtering helpers
    def _is_relevant_title(self, title: str) -> bool:
        """
        Return True if the job title indicates an intern/grad/placement role.
        Uses word boundaries so 'intern' does not match 'internal' or 'international'.
        """
        t = title.lower()
        return any(re.search(r'\b' + re.escape(kw) + r'\b', t) for kw in ROLE_KEYWORDS)

    def _is_uk_location(self, location_name: str) -> bool:
        """Return True if location string refers to a UK location."""
        loc = location_name.lower()
        return any(kw in loc for kw in UK_LOCATION_KEYWORDS)

    def _clean_description(self, html_content: str) -> str:
        """
        Strip HTML tags from the Greenhouse job description.

        Greenhouse returns the content field as HTML-escaped text
        (e.g converts &lt;div\&gt to <div>), unescape first, then strip the tags.
        Full text is kept so skills extraction can scan the whole description.
        """
        if not html_content:
            return ""
        import html as html_module
        unescaped = html_module.unescape(html_content)
        text = BeautifulSoup(unescaped, "html.parser").get_text(separator=" ", strip=True)
        return text

    # Per-company scrape
    def scrape_company(self, slug: str, company_name: str) -> List[Dict]:
        """
        Fetch and filter all jobs for a single Greenhouse company.

        Args:
            slug: Greenhouse board slug (e.g. "graphcore")
            company_name: Display name (e.g. "Graphcore")

        Returns:
            List of matching job dicts.
        """
        url = self.BASE_URL.format(slug=slug)
        logger.info(f"Fetching {company_name} from Greenhouse ({slug})...")

        try:
            response = self.session.get( # Retrieving JSON data from Greenhouse API endpoint
                url,
                params={"content": "true"},  # include job description HTML
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {company_name} ({slug}): {e}")
            return []

        data = response.json()
        all_jobs = data.get("jobs", [])
        logger.info(f"  {company_name}: {len(all_jobs)} total jobs")

        results = []
        for job in all_jobs:
            title = job.get("title", "")
            location_name = job.get("location", {}).get("name", "") or ""

            # Filter by role type
            if not self._is_relevant_title(title):
                continue

            # Filter by UK location (if enabled)
            if self.uk_only and not self._is_uk_location(location_name):
                logger.debug(f"  Skipping non-UK role: {title} ({location_name})")
                continue

            description = self._clean_description(job.get("content", ""))
            url = job.get("absolute_url", "")

            results.append({
                "title":        title,
                "company":      company_name,
                "location":     location_name or "Location not specified",
                "url":          url,
                "description":  description,
                "date_posted":  job.get("first_published", job.get("updated_at", None)),
                "deadline":     None,   # Greenhouse API doesn't expose closing date
                "start_date":   None,
                "scraped_at":   datetime.now().isoformat(),
                "source_website": "greenhouse",
            })

        logger.info(
            f"  {company_name}: {len(results)} relevant {'UK ' if self.uk_only else ''}roles found"
        )
        return results

    # Scrape all companies
    def scrape(self) -> List[Dict]:
        """
        Scrape all companies in self.companies concurrently and return combined results.

        Returns:
            List of job dicts from all companies combined.
        """
        logger.info(f"[Greenhouse] Scraping {len(self.companies)} companies ({self.workers} workers, timeout={self.timeout}s)...")

        all_results: List[Dict] = []

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {
                pool.submit(self.scrape_company, slug, company_name): company_name
                for company_name, slug in self.companies
            }
            for future in as_completed(futures):
                try:
                    jobs = future.result()
                    all_results.extend(jobs)
                except Exception as e:
                    company_name = futures[future]
                    logger.warning(f"  {company_name}: unexpected error - {e}")

        logger.info(
            f"[Greenhouse] Done: {len(all_results)} relevant roles "
            f"across {len(self.companies)} companies"
        )
        return all_results
