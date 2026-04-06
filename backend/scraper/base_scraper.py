"""
base_scraper - generic HTML scraper foundation used by all company scrapers.

Provides robots.txt compliance, persistent HTTP sessions, keyword-based
internship/graduate role detection, multi-page pagination, and Taleo ATS
field extraction (salary, posting date) for companies like BT Group and SAP.

Extended by CompanyScraper, which layers on company-specific CSS selectors
from company_configs.py before falling back to these generic patterns.

Usage:
    from scraper.company_scraper import CompanyScraper

    scraper = CompanyScraper("BT Group")
    jobs = scraper.scrape()  # list of job dicts
"""

import requests
import time
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper:
    """
    Base scraper for job listings.
    Provides common functionality for scraping with robots.txt compliance.
    """
    
    def __init__(self, company_name: str, careers_url: str, 
                 user_agent: str, delay: float = 2.0, timeout: int = 10):
        """
        Initialize scraper for a specific company.
        
        Args:
            company_name: Name of the company (e.g "Google", "Microsoft")
            careers_url: Full URL to their careers/jobs page
            user_agent: Browser identity
            delay: Seconds between requests
            timeout: Request timeout
            
        Example:
            scraper = BaseScraper(
                company_name="Google",
                careers_url="https://www.google.com/careers/jobs/results/",
                user_agent="Mozilla/5.0..."
            )
        """
        # Extract base_url from careers_url for robots.txt
        parsed = urlparse(careers_url) # Breaks URL into components e.g scheme, netloc, path
        base_url = f"{parsed.scheme}://{parsed.netloc}" # e.g https://uk.indeed.com from https://uk.indeed.com/jobs?q=python&l=london
        
        # Initialize scraper settings
        self.base_url = base_url
        self.user_agent = user_agent
        self.delay = delay
        self.timeout = timeout
        self.domain = urlparse(base_url).netloc
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        
        # robots.txt parser
        self.robot_parser = RobotFileParser()
        self._load_robots_txt()
        
        # Company-specific settings
        self.company_name = company_name
        self.careers_url = careers_url
        
        # Keywords to identify internships and graduate roles
        self.target_keywords = [
            'intern', 'internship', 'placement',
            'graduate', 'grad role', 'new grad', 'graduate scheme', 'junior',
            'grad scheme', 'early career', 'entry level', 'grad',
            'industrial placement', 'sandwich placement',
            'year in industry', 'sandwich year', 'industrial year',
        ]

        self.uk_location_keywords = [
            'london', 'united kingdom', 'england', 'uk', 'remote',
            'britain', 'manchester', 'birmingham', 'edinburgh',
            'glasgow', 'bristol', 'leeds', 'reading', 'cambridge',
        ]
        
        logger.info(f"Initialized scraper for {company_name}")
    
    def _load_robots_txt(self):
        """
        Load and parse robots.txt file from the website.
        This tells us which pages we're allowed to scrape.
        """
        robots_url = urljoin(self.base_url, '/robots.txt') # e.g https://uk.indeed.com/robots.txt
        
        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
            logger.info(f"Successfully loaded robots.txt from {robots_url}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt from {robots_url}: {e}")
    
    def is_scraping_permitted(self, url: str) -> bool:
        """
        Check if we're allowed to scrape this URL according to robots.txt.
        
        Args:
            url: The URL we want to scrape
            
        Returns:
            True if allowed, False if forbidden
        """
        is_allowed = self.robot_parser.can_fetch(self.user_agent, url) # Checks if our user agent is allowed to fetch this URL
        
        if not is_allowed:
            logger.warning(f"robots.txt disallows scraping: {url}")
        
        return is_allowed
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Download a web page and parse it into BeautifulSoup object.
        
        Args:
            url: The URL to download
            
        Returns:
            BeautifulSoup object if successful, None if failed
        """
        # Check if we're allowed to scrape this URL
        if not self.is_scraping_permitted(url):
            logger.error(f"Skipping {url} - forbidden by robots.txt")
            return None
        
        try:
            # Download the page
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status() # Check for HTTP errors
            
            # Parse HTML into BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser') # Takes HTML tags and creates a parse tree for easy data extraction
            
            time.sleep(self.delay) # Delay to avoid overwhelming the server
            
            return soup
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching {url}")
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_text(self, soup: BeautifulSoup, selector: str, default: str = "") -> str:
        """
        Extract text from HTML using CSS selector.
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector (e.g "h1.title", ".company-name")
            default: Return this if element not found
            
        Returns:
            <h1>Software Engineer Intern</h1> -> "Software Engineer Intern"
        """
        element = soup.select_one(selector) # Finds first element that matches CSS selector
        
        if element:
            return element.get_text(strip=True)
        
        return default
    
    def extract_attribute(self, soup: BeautifulSoup, selector: str, 
                         attribute: str, default: str = "") -> str:
        """
        Extract an attribute from HTML element (e.g href, src).
        
        Args:
            soup: BeautifulSoup object
            selector: CSS selector
            attribute: Attribute name (e.g "href", "src", "data-id")
            default: Return this if element/attribute not found
            
        Returns:
            <a href="https://google.com/apply">Click Here</a> -> "https://google.com/apply"
        """
        element = soup.select_one(selector) # Find first element that matches HTML element
        
        if element and element.has_attr(attribute):
            return element[attribute]
        
        return default
    
    def is_relevant_role(self, title: str, description: str = "") -> bool:
        """
        Check if job title/description matches keywords for internship or graduate role.
        
        Args:
            title: Job title
            description: Job description (optional)
            
        Returns:
            True if it's an internship/graduate role
            
        Example:
            is_relevant_role("Software Engineering Intern") -> True
            is_relevant_role("Senior Director of Marketing") -> False
        """
        # Handle None values
        title = title or ""
        description = description or ""
        
        # Split text into words to check for exact matches
        text = (title + " " + description).lower()
        words = text.split()
        
        # Check if any keyword appears as a complete word
        for keyword in self.target_keywords:
            if keyword in words:
                return True
        
        return False
    
    def extract_job_cards(self, soup) -> List:
        """
        Find all job listing cards on the page.
        
        This method tries multiple common HTML patterns that companies use:
        - <div class="job-card">
        - <article class="job-listing">
        - <li class="position">
        - <tr class="job-row">
        If one found, it returns results found with that selector. If none found, returns empty list.
        
        Args:
            soup: BeautifulSoup object of the careers page
            
        Returns:
            List of job card elements
        """
        # Try common job card selectors (different companies use different HTML)
        common_selectors = [
            'tr.job-post',
            'tr.job-posts',
            'tr.job-listing',
            'tr.job-row',
            'tr[class*="job"]',
            'tr[data-job]',
            'div.job-card',
            'div.job-listing',
            'div.job-item',
            'div.job-post',
            'div.job-posts',
            'div[class*="job-card"]',
            'div[class*="job-item"]',
            'div[data-job-id]',
            'div.position',
            'div.opening',
            'div.career-item',
            'article.job',
            'article[class*="job"]',
            'section.job',
            'li.job',
            'li.job-listing',
            'li[class*="job"]',
            'a.job-link',
            'a[class*="job-card"]'
        ]
        
        for selector in common_selectors: # For all selectors, how many results show up
            job_cards = soup.select(selector)
            if job_cards:
                logger.info(f"Found {len(job_cards)} job cards using selector: {selector}")
                return job_cards
        
        logger.warning(f"Could not find job cards on {self.careers_url}")
        logger.warning("You may need to customize the selector for this company")
        return []
    
    def extract_job_data(self, job_card) -> Optional[Dict]:
        """
        Extract job information from a single job card element.
        
        Tries to find:
        - Title
        - Location
        - Description/summary
        - URL/link
        - Date posted (if available)
        - Deadline (if available)
        
        Args:
            job_card: BeautifulSoup element representing one job
            
        Returns:
            Dictionary with job data, or None if extraction fails
        """
        try:
            # Extract title
            title = (
                self.extract_text(job_card, 'h2') or
                self.extract_text(job_card, 'h3') or
                self.extract_text(job_card, 'h4') or

                self.extract_text(job_card, '.job-title') or
                self.extract_text(job_card, '.title') or
                self.extract_text(job_card, '.position-title') or

                self.extract_text(job_card, 'a') or
                self.extract_text(job_card, 'p')
            )
            
            if not title:
                return None
            
            # Extract location
            location = (
                self.extract_text(job_card, '.location') or
                self.extract_text(job_card, '.job-location') or
                self.extract_text(job_card, '[class*="location"]') or

                self.extract_text(job_card, 'span.location') or
                self.extract_text(job_card, '[data-location]') or
                "Location not specified"
            )
            
            # Extract job URL
            job_url = (
                self.extract_attribute(job_card, 'a', 'href') or
                self.extract_attribute(job_card, '[href]', 'href')
            )
            
            # Make URL absolute if it's relative
            if job_url and not job_url.startswith('http'):
                from urllib.parse import urljoin
                job_url = urljoin(self.base_url, job_url)
            
            # Extract description/summary (if available on listing page)
            # Skip the title and location paragraphs
            description = ""
            all_p_tags = job_card.find_all('p')
            if len(all_p_tags) > 2:  # If more than title + location
                for p in all_p_tags:
                    text = p.get_text(strip=True)
                    if text and text != title and text != location:
                        description = text
                        break
            
            if not description:
                description = (
                    self.extract_text(job_card, '.description') or
                    self.extract_text(job_card, '.summary') or
                    self.extract_text(job_card, '.job-description') or
                    ""
                )
            
            # Extract date posted (if available)
            date_posted = (
                self.extract_text(job_card, '.date') or
                self.extract_text(job_card, '.posted-date') or
                self.extract_text(job_card, 'time') or
                None
            )
            
            # Extract deadline/closing date (if available)
            deadline = (
                self.extract_text(job_card, '.deadline') or
                self.extract_text(job_card, '.closing-date') or
                self.extract_text(job_card, '[class*="deadline"]') or
                self.extract_text(job_card, '[class*="closing"]') or
                self.extract_text(job_card, '[class*="apply-by"]') or
                None
            )
            
            return {
                'title': title,
                'company': self.company_name,
                'location': location,
                'description': description,
                'url': job_url or self.careers_url,
                'source_website': self.company_name,
                'date_posted': date_posted,
                'deadline': deadline,
                'salary_range': None,  # Filled in by fetch_job_details for Taleo sites
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return None
    
    def fetch_job_details(self, job_url: str) -> Optional[Dict]:
        """
        Fetch individual job posting page to extract detailed information.
        
        Args:
            job_url: URL of the specific job posting
            
        Returns:
            Dictionary with date_posted, deadline, and full description if found
        """
        try:
            logger.info(f"Fetching job details from: {job_url}")
            soup = self.fetch_page(job_url)
            if not soup:
                return None
            
            page_text = soup.get_text().lower() # Retrieve all text

            # Taleo ATS structured fields (BT Group, SAP)
            # Each field: <span class="joblayouttoken-label">Label:</span>
            # <span class="rtltextaligneligible">Value</span>
            taleo_fields = {}
            for label_span in soup.select('span.joblayouttoken-label'):
                key = label_span.get_text(strip=True).rstrip(':').lower()
                value_span = label_span.find_next_sibling('span')
                if value_span:
                    taleo_fields[key] = value_span.get_text(strip=True)

            salary_range = taleo_fields.get('salary') or None
            date_posted = taleo_fields.get('posting date') or None

            if not date_posted:
                date_posted = (
                    self.extract_text(soup, '.date') or
                    self.extract_text(soup, '.posted-date') or
                    self.extract_text(soup, 'time') or
                    None
                )

            # Look in text for posted date
            if not date_posted:
                # Match "Posting Date: \n 14 Feb 2026" or "Posted: 14 Feb 2026"
                # Delimiter (: or -) to prevent false matches
                date_match = re.search(r'(?:posting date|posted|published|date posted):?\s*:?\s*([\w\s,]+?\d{4})', page_text, re.IGNORECASE | re.DOTALL)
                if date_match:
                    date_posted = date_match.group(1).strip()
            
            # Extract start date (if available)
            start_date = None
            start_date_patterns = [
                '.start-date', '[class*="start-date"]',
                '[class*="starting-date"]', '.commencement-date', '.commence-date'
            ]
            for pattern in start_date_patterns:
                elem = soup.select_one(pattern)
                if elem:
                    start_date = elem.get_text(strip=True)
                    break
            
            # Look in text for start date
            if not start_date:
                # Match "Start Date: 7th September 2026" or "Start Date: 22nd June 26"
                # Handle both 2-digit (26) and 4-digit (2026) years (\d2 or \d4)
                start_match = re.search(r'(?:start date|commencement date|starting date|begins)\s*[:\-–—]\s*([\d\w\s,()]+?(?:\d{4}|\d{2}(?:\s|\(|$)))', page_text, re.IGNORECASE | re.DOTALL)
                if start_match:
                    start_date = start_match.group(1).strip()
            
            # Try to find deadline with various patterns
            deadline = None
            deadline_patterns = [
                '.deadline', '.closing-date', '[class*="deadline"]',
                '[class*="closing-date"]', '[class*="apply-by"]', '.application-deadline'
            ]
            for pattern in deadline_patterns:
                elem = soup.select_one(pattern)
                if elem:
                    deadline = elem.get_text(strip=True)
                    break
            
            # Look in text for common phrases
            if not deadline:
                deadline_match = re.search(r'(?:deadline|closing date|apply by date|apply by|close date):?\s*[:\-–—]?\s*([\w\s,]+?\d{4})', page_text, re.IGNORECASE | re.DOTALL)
                if deadline_match:
                    deadline = deadline_match.group(1).strip()
            
            # Extract full description
            description = None
            desc_selectors = [
                '.job-description', '.description', '[class*="job-description"]',
                '[class*="description"]', '.job-details', 'article', 'main'
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    description = elem.get_text(" ", strip=True)[:12000]
                    break

            # Fallback: use page text if no structured description element exists.
            if not description:
                description = soup.get_text(" ", strip=True)[:12000]
            
            return {
                'date_posted': date_posted,
                'deadline': deadline,
                'start_date': start_date,
                'description': description,
                'salary_range': salary_range,
            }
            
        except Exception as e:
            logger.warning(f"Error fetching job details from {job_url}: {e}")
            return None
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method for company careers page.
        
        Process:
        1. Fetch the careers page
        2. Find all job cards (with pagination)
        3. Filter job cards by title/description for relevant roles
        4. Extract data from each card - if not enough data in job card, visit individual job page to get more details
        5. Return list of relevant jobs
        
        Returns:
            List of dictionaries, each containing job data
        """
        logger.info(f"Scraping {self.company_name} careers page: {self.careers_url}")
        
        all_job_cards = []
        current_url = self.careers_url
        page_num = 1
        max_pages = 10  # Safety limit to avoid infinite loops
        
        # Fetch all pages and collect job cards
        while current_url and page_num <= max_pages:
            logger.info(f"Fetching page {page_num}: {current_url}")
            
            soup = self.fetch_page(current_url)
            if not soup:
                logger.error(f"Failed to fetch page {page_num}")
                break
            
            # Find job cards on this page
            job_cards = self.extract_job_cards(soup)
            if not job_cards:
                logger.info(f"No job cards found on page {page_num}")
                break
            
            all_job_cards.extend(job_cards) # Add those job_cards to all_job_cards list
            logger.info(f"Found {len(job_cards)} jobs on page {page_num} (total: {len(all_job_cards)})")
            
            # Look for next page link
            next_url = self.find_next_page(soup, current_url)
            if next_url:
                current_url = next_url
                page_num += 1
            else:
                logger.info("No more pages found")
                break
        
        logger.info(f"Total jobs found across {page_num} pages: {len(all_job_cards)}")
        
        # Extract data and filter for relevant roles
        relevant_jobs = []
        
        for card in all_job_cards:
            job_data = self.extract_job_data(card) # Extracts title, location, url etc. from the job card
            
            if job_data and self.is_relevant_role(job_data['title'], job_data['description']):
                # Skip non-UK roles when location is populated and clearly not UK
                location = (job_data.get('location') or '').lower()
                if location and not any(kw in location for kw in self.uk_location_keywords):
                    logger.debug(f"Skipping non-UK role: {job_data['title']} ({job_data['location']})")
                    continue
                # This is a relevant intern/graduate role - fetch full details
                job_url = job_data.get('url')
                # Checks if anything is missing
                if job_url and (
                    not job_data.get('date_posted')
                    or not job_data.get('deadline')
                    or not job_data.get('start_date')
                    or not job_data['description']
                    or len((job_data.get('description') or '').strip()) < 500
                ):
                    logger.info(f"Fetching details for: {job_data['title']}")
                    detail_data = self.fetch_job_details(job_url) # Visit the individual job page to get more info like date posted, deadline, full description
                    if detail_data:
                        # Update with detail page information
                        if not job_data.get('date_posted') and detail_data.get('date_posted'):
                            job_data['date_posted'] = detail_data['date_posted']
                        if not job_data.get('deadline') and detail_data.get('deadline'):
                            job_data['deadline'] = detail_data['deadline']
                        if not job_data.get('start_date') and detail_data.get('start_date'):
                            job_data['start_date'] = detail_data['start_date']
                        # Get fuller description if available
                        if not job_data['description'] and detail_data.get('description'):
                            job_data['description'] = detail_data['description']
                        # Salary - populated for Taleo sites (BT, SAP)
                        if not job_data.get('salary_range') and detail_data.get('salary_range'):
                            job_data['salary_range'] = detail_data['salary_range']
                
                relevant_jobs.append(job_data)
                logger.info(f"Found relevant role: {job_data['title']}")
        
        logger.info(f"Found {len(relevant_jobs)} internship/graduate roles at {self.company_name}")
        return relevant_jobs
    
    def find_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Find the next page link for pagination.
        Tries multiple common pagination patterns in order.
        
        Args:
            soup: BeautifulSoup object of current page
            current_url: Current page URL
            
        Returns:
            URL of next page, or None if no next page
        """
        from urllib.parse import urljoin, urlparse, parse_qs
        
        # Strategy 1: URL parameter with page number (?page=2, ?p=2 or path-style &p=2)
        for param in ['page', 'p', 'pg']:
            links = soup.select(f'a[href*="{param}="]')
            if links:
                parsed = urlparse(current_url) # Split URL into components
                params = parse_qs(parsed.query) # Query e.g page=2&location=London 
                # Also check for &param=N in the URL path (e.g. Barclays: /search-jobs&p=1)
                path_match = re.search(rf'[?&]{re.escape(param)}=(\d+)', current_url) # Safety net to find current page number
                if path_match:
                    current_page = int(path_match.group(1))
                elif param in params:
                    current_page = int(params[param][0])
                else:
                    current_page = 0
                next_page = current_page + 1
                
                for link in links:
                    href = link.get('href', '')
                    if f'{param}={next_page}' in href:
                        return urljoin(current_url, href)
        
        # Strategy 2: URL parameter with startrow/offset (?startrow=25, ?offset=25)
        # Also handles HSBC pipelineOffset (increment 10)
        for param, increment in [('startrow', 25), ('pipelineOffset', 10), ('offset', 25), ('start', 25)]:
            links = soup.select(f'a[href*="{param}="]')
            if links:
                parsed = urlparse(current_url)
                params = parse_qs(parsed.query)
                current_val = int(params.get(param, ['0'])[0]) if param in params else 0
                next_val = current_val + increment
                
                for link in links:
                    href = link.get('href', '')
                    if f'{param}={next_val}' in href:
                        return urljoin(current_url, href)
        
        # Strategy 3: Next button/link with common selectors
        next_selectors = [
            'a[aria-label*="next" i]',
            'a[title*="next" i]',
            'a.next',
            'a.pagination-next',
            'a[rel="next"]',
            'li.next a',
            'a:soup-contains("Next")',
            'button[aria-label*="next" i]'
        ]
        
        for selector in next_selectors:
            try:
                next_link = soup.select_one(selector)
                if next_link:
                    href = next_link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = urljoin(current_url, href)
                        return href
            except:
                continue
        
        return None
