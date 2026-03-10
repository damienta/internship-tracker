"""
lever_scraper - scrapes internship/graduate roles from companies using the Lever ATS.

Uses the public Lever JSON API - no authentication required.

API endpoint:
    GET https://api.lever.co/v0/postings/{slug}?mode=json
    Returns a JSON array of all live job postings for that company.

Adding a company:
    Verify the slug exists at https://api.lever.co/v0/postings/{slug}?mode=json
    then add ("Display Name", "slug") to LEVER_COMPANIES.

Usage:
    scraper = LeverScraper()
    jobs = scraper.scrape()
    jobs = scraper.scrape_company("palantir")
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Company list - (display_name, lever_slug)
# To add a company: find their slug from https://api.lever.co/v0/postings/{slug}?mode=json
# ---------------------------------------------------------------------------
LEVER_COMPANIES = [
    ("Monzo", "monzo"),
    ("Revolut", "revolut"),
    ("Starling Bank", "starlingbank"),
    ("GoCardless", "gocardless"),
    ("Freetrade", "freetrade"),
    ("Curve", "curve"),
    ("Cleo", "cleo"),
    ("Tide", "tide"),
    ("Zopa", "zopa"),
    ("OakNorth", "oaknorth"),
    ("Azimo", "azimo"),
    ("Soldo", "soldo"),
    ("Deliveroo", "deliveroo"),
    ("Skyscanner", "skyscanner"),
    ("Babylon Health", "babylonhealth"),
    ("Bulb", "bulb"),
    ("Gousto", "gousto"),
    ("Onto", "onto"),
    ("Unmind", "unmind"),
    ("Onfido", "onfido"),
    ("Trussle", "trussle"),
    ("Habito", "habito"),
    ("Bought By Many", "boughtbymany"),
    ("Lyst", "lyst"),
    ("Cazoo", "cazoo"),
    ("Elvie", "elvie"),
    ("Cuvva", "cuvva"),
    ("Beamery", "beamery"),
    ("Perkbox", "perkbox"),
    ("Reward Gateway", "rewardgateway"),
    ("Goodlord", "goodlord"),
    ("Nested", "nested"),
    ("Farewill", "farewill"),
    ("Kano", "kano"),
    ("Bulb Energy", "bulbenergy"),
    ("Octopus Energy", "octopusenergy"),
    ("OVO Energy", "ovoenergy"),
    ("Quantexa", "quantexa"),
    ("Thought Machine", "thought-machine"),
    ("Faculty", "faculty"),
    ("Improbable", "improbable"),
    ("Robin AI", "robin-ai"),
    ("Multiverse", "multiverse"),
    ("Eigen Technologies", "eigen-technologies"),
    ("PolyAI", "polyai"),
    ("Kainos", "kainos"),
    ("AND Digital", "and-digital"),
    ("Softwire", "softwire"),
    ("Mimecast", "mimecast"),
    ("Snyk", "snyk"),
    ("Palantir", "palantir"),
    ("Stripe", "stripe"),
    ("Twilio", "twilio"),
    ("Confluent", "confluent"),
    ("HashiCorp", "hashicorp"),
    ("MongoDB", "mongodb"),
    ("Okta", "okta"),
    ("Zendesk", "zendesk"),
    ("Datadog", "datadog"),
    ("Cloudflare", "cloudflare"),
    ("Figma", "figma"),
    ("Notion", "notion"),
    ("Airtable", "airtable"),
    ("Brex", "brex"),
    ("Rippling", "rippling"),
    ("Coinbase", "coinbase"),
    ("Robinhood", "robinhood"),
    ("Affirm", "affirm"),
    ("Chime", "chime"),
    ("Cohere", "cohere"),
    ("Scale AI", "scaleai"),
    ("Waymo", "waymo"),
    ("Recursion", "recursion"),
    ("Tractable", "tractable"),
    ("Graphcore", "graphcore"),
    ("Wayve", "wayve"),
    ("FiveAI", "fiveai"),
    ("Hadean", "hadean"),
    ("Papercup", "papercup"),
    ("Corti", "corti"),
    ("Imbue", "imbue"),
    ("Weights & Biases", "wandb"),
    ("Hugging Face", "huggingface"),
    ("Perplexity", "perplexityai"),
    ("Mistral", "mistral"),
    ("Anthropic", "anthropic"),
    ("Citadel", "citadel"),
    ("Optiver", "optiver"),
    ("IMC Trading", "imc-trading"),
    ("Two Sigma", "twosigma"),
    ("Hudson River Trading", "hudson-river-trading"),
    ("Jane Street", "janestreet"),
    ("Sourcegraph", "sourcegraph"),
    ("Supabase", "supabase"),
    ("dbt Labs", "dbt-labs"),
    ("Airbyte", "airbyte"),
    ("Prefect", "prefect"),
    ("Observable", "observablehq"),
    ("Retool", "retool"),
    ("Contentful", "contentful"),
    ("Loom", "loom"),
    ("Intercom", "intercom"),
    ("Asana", "asana"),
    ("PagerDuty", "pagerduty"),
    ("Amplitude", "amplitude"),
    ("Mixpanel", "mixpanel"),
    ("Samsara", "samsara"),
    ("Lattice", "lattice"),
    ("Carta", "carta"),
    ("Ramp", "ramp"),
    ("Benchling", "benchling"),
    ("Gem", "gem"),
    ("Plaid", "plaid"),
    ("Wise", "wise"),
    ("Checkout.com", "checkout"),
    ("iwoca", "iwoca"),
    ("Wagestream", "wagestream"),
    ("Funding Circle", "fundingcircle"),
    ("TrueLayer", "truelayer"),
    ("Yapily", "yapily"),
    ("Tink", "tink"),
    ("ClearScore", "clearscore"),
    ("Darktrace", "darktrace"),
    ("Ro", "ro"),
    ("Arm", "arm"),
    ("Accurx", "accurx"),
    ("Griffin", "griffin-bank"),
    ("Allica Bank", "allica"),
    ("Flagstone", "flagstone"),
    ("Moneyhub", "moneyhub"),
    ("Grafana Labs", "grafana"),
    ("Linear", "linear"),
    ("Netlify", "netlify"),
    ("Vercel", "vercel"),
    ("Segment", "segment"),
    ("Replit", "replit"),
    ("Zapier", "zapier"),
    ("Modal", "modal"),
    ("Together AI", "together"),
    ("Hex", "hex"),
]

# Role keywords - checked against job title (case-insensitive)
ROLE_KEYWORDS = ["intern", "internship", "graduate", "grad", "placement", "apprentice"]

# UK location keywords - checked against location field
UK_LOCATION_KEYWORDS = ["london", "united kingdom", "england", "uk", "remote", "manchester", "edinburgh", "bristol"]


class LeverScraper:
    """
    Scrapes multiple companies via the public Lever jobs API.
    Returns job dicts in the same format as GreenhouseScraper and BaseScraper.
    """

    BASE_URL = "https://api.lever.co/v0/postings/{slug}"

    def __init__(
        self,
        companies: Optional[List[tuple]] = None,
        uk_only: bool = True,
        delay: float = 0.0,
        timeout: int = 10,
        workers: int = 10,
    ):
        self.companies = companies or LEVER_COMPANIES
        self.uk_only = uk_only
        self.delay = delay
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

    def _is_relevant_title(self, title: str) -> bool:
        # Use word boundaries to avoid substring false-positives e.g "intern" must not match "international"
        t = title.lower()
        return any(re.search(r'\b' + re.escape(kw) + r'\b', t) for kw in ROLE_KEYWORDS)

    def _is_uk_location(self, location: str) -> bool:
        loc = location.lower()
        return any(kw in loc for kw in UK_LOCATION_KEYWORDS)

    def scrape_company(self, slug: str, company_name: str) -> List[Dict]:
        """Fetch and filter all jobs for a single Lever company."""
        url = self.BASE_URL.format(slug=slug)
        logger.debug(f"Fetching {company_name} ({slug})...")

        try:
            r = self.session.get(url, params={"mode": "json"}, timeout=self.timeout)
            if r.status_code == 404:
                logger.debug(f"  {company_name} ({slug}): not on Lever (404)")
                return []
            r.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"  {company_name} ({slug}): request failed - {e}")
            return []

        all_jobs = r.json()
        if not isinstance(all_jobs, list):
            logger.warning(f"  {company_name}: unexpected response format")
            return []

        logger.info(f"  {company_name}: {len(all_jobs)} total postings")

        results = []
        for job in all_jobs:
            title = job.get("text", "")
            cats = job.get("categories", {})
            location = cats.get("location") or cats.get("allLocations", [""])[0] if cats.get("allLocations") else ""
            location = location or ""

            if not self._is_relevant_title(title):
                continue

            if self.uk_only and not self._is_uk_location(location):
                logger.debug(f"  Skipping non-UK: {title} ({location})")
                continue

            description = job.get("descriptionPlain") or "" # plaintext ver of job description
            if not description:
                import html as html_module
                from bs4 import BeautifulSoup
                raw = job.get("description") or job.get("descriptionBody") or ""
                description = BeautifulSoup(html_module.unescape(raw), "html.parser").get_text(" ", strip=True) # strip=True removes all whitespace
            # Append structured list sections (e.g. "Technologies We Use", "Requirements")
            # These are stored separately in the Lever API response
            for lst in job.get("lists", []): # List of extra fields
                heading = lst.get("text", "") # Grabs header of field (e.g. "Technologies We Use")
                items = lst.get("content", "") # Grabs content of that field
                if heading or items:
                    from bs4 import BeautifulSoup as _BS
                    items_text = _BS(items, "html.parser").get_text(" ", strip=True) if items else ""
                    description += f" {heading}: {items_text}"

            created_at = job.get("createdAt") # When job posting was created (recorded in ms since epoch)

            results.append({
                "title":          title,
                "company":        company_name,
                "location":       location or "Location not specified",
                "description":    description,
                "url":            job.get("hostedUrl", ""),
                "source_website": "lever",
                "date_posted":    created_at,
                "deadline":       None, 
                "salary_range":   None,
                "scraped_at":     datetime.now().isoformat(),
            })

        logger.info(f"  {company_name}: {len(results)} relevant UK roles found")
        return results

    def scrape(self) -> List[Dict]:
        """Scrape all companies concurrently and return combined results."""
        logger.info(f"[Lever] Scraping {len(self.companies)} companies ({self.workers} workers, timeout={self.timeout}s)...")

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
            f"[Lever] Done: {len(all_results)} relevant roles "
            f"across {len(self.companies)} companies"
        )
        return all_results
