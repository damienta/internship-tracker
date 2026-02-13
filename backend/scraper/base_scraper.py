import requests
import time
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

# Set up logging to track scraper activity
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper:
    """
    Base scraper for job listings.
    Provides common functionality for scraping with robots.txt compliance.
    Child classes (LinkedInJobsScraper, IndeedScraper) inherit from this.
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
        
        # Session for persistent connections (faster)
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
            'graduate', 'grad role', 'new grad', 'graduate scheme',
            'grad scheme', 'early career', 'entry level', 'grad'
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
            logger.warning("Proceeding with caution - will scrape slowly")
    
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
            
            # Be polite - wait before next request
            time.sleep(self.delay)
            
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
        element = soup.select_one(selector)
        
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
        
        text = (title + " " + description).lower()
        
        return any(keyword in text for keyword in self.target_keywords)
    
    def extract_job_cards(self, soup) -> List:
        """
        Find all job listing cards on the page.
        
        This method tries multiple common HTML patterns that companies use:
        - <div class="job-card">
        - <article class="job-listing">
        - <li class="position">
        - <tr class="job-row">
        
        Args:
            soup: BeautifulSoup object of the careers page
            
        Returns:
            List of job card elements
        """
        # Try common job card selectors (different companies use different HTML)
        common_selectors = [
            # Table-based patterns
            'tr.job-post',
            'tr.job-posts',
            'tr.job-listing',
            'tr.job-row',
            'tr[class*="job"]',
            'tr[data-job]',
            
            # Div-based patterns (most common)
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
            
            # Article/Section patterns
            'article.job',
            'article[class*="job"]',
            'section.job',
            
            # List-based patterns
            'li.job',
            'li.job-listing',
            'li[class*="job"]',
            
            # Link-based patterns (some sites wrap everything in <a>)
            'a.job-link',
            'a[class*="job-card"]'
        ]
        
        for selector in common_selectors:
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
            # Extract title (try multiple selectors)
            title = (
                # Heading tags
                self.extract_text(job_card, 'h2') or
                self.extract_text(job_card, 'h3') or
                self.extract_text(job_card, 'h4') or

                # Common class patterns
                self.extract_text(job_card, '.job-title') or
                self.extract_text(job_card, '.title') or
                self.extract_text(job_card, '.position-title') or

                # Generic patterns (first <p> or <a> as fallback)
                self.extract_text(job_card, 'a') or
                self.extract_text(job_card, 'p')
            )
            
            if not title:
                return None
            
            # Extract location
            location = (
                # Common class patterns
                self.extract_text(job_card, '.location') or
                self.extract_text(job_card, '.job-location') or
                self.extract_text(job_card, '[class*="location"]') or

                # Generic patterns
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
                # Get paragraphs that aren't title or location
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
            
            # Get all text content to search for dates
            page_text = soup.get_text().lower()
            
            # Extract date posted (if available on detail page)
            date_posted = (
                self.extract_text(soup, '.date') or
                self.extract_text(soup, '.posted-date') or
                self.extract_text(soup, 'time') or
                None
            )
            
            # Look in text for posted date
            if not date_posted:
                date_match = re.search(r'(?:posted|published|date posted):?\s*:?\s*([\w\s,]+\d{4})', page_text, re.IGNORECASE)
                if date_match:
                    date_posted = date_match.group(1).strip()
            
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
                # Match patterns like "Apply by date: 22nd February 2026"
                deadline_match = re.search(r'(?:deadline|closing date|apply by date|apply by|close date):?\s*:?\s*([\w\s,]+\d{4})', page_text, re.IGNORECASE)
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
                    description = elem.get_text(strip=True)[:500]  # First 500 chars
                    break
            
            return {
                'date_posted': date_posted,
                'deadline': deadline,
                'description': description
            }
            
        except Exception as e:
            logger.warning(f"Error fetching job details from {job_url}: {e}")
            return None
    
    def scrape(self) -> List[Dict]:
        """
        Main scraping method for company careers page.
        
        Process:
        1. Fetch the careers page
        2. Find all job cards
        3. Extract data from each card
        4. Filter for internships/graduate roles
        5. Return list of relevant jobs
        
        Returns:
            List of dictionaries, each containing job data
        """
        logger.info(f"Scraping {self.company_name} careers page: {self.careers_url}")
        
        # Fetch the page
        soup = self.fetch_page(self.careers_url)
        if not soup:
            logger.error(f"Failed to fetch page for {self.company_name}")
            return []
        
        # Find all job cards
        job_cards = self.extract_job_cards(soup)
        if not job_cards:
            return []
        
        # Extract data and filter for relevant roles
        relevant_jobs = []
        
        for card in job_cards:
            job_data = self.extract_job_data(card)
            
            if job_data and self.is_relevant_role(job_data['title'], job_data['description']):
                # This is a relevant intern/graduate role - fetch full details
                job_url = job_data.get('url')
                if job_url and (not job_data['date_posted'] or not job_data['deadline'] or not job_data['description']):
                    logger.info(f"Fetching details for: {job_data['title']}")
                    detail_data = self.fetch_job_details(job_url)
                    if detail_data:
                        # Update with detail page information
                        if not job_data['date_posted'] and detail_data.get('date_posted'):
                            job_data['date_posted'] = detail_data['date_posted']
                        if not job_data['deadline'] and detail_data.get('deadline'):
                            job_data['deadline'] = detail_data['deadline']
                        # Get fuller description if available
                        if not job_data['description'] and detail_data.get('description'):
                            job_data['description'] = detail_data['description']
                
                relevant_jobs.append(job_data)
                logger.info(f"Found relevant role: {job_data['title']}")
        
        logger.info(f"Found {len(relevant_jobs)} internship/graduate roles at {self.company_name}")
        return relevant_jobs


# List of companies to scrape
COMPANY_TARGETS = [
    {
        'name': 'Google',
        'url': 'https://www.google.com/about/careers/applications/jobs/results/'
    },
    {
        'name': 'Microsoft',
        'url': 'https://careers.microsoft.com/professionals/us/en/search-results'
    },
    {
        'name': 'Meta',
        'url': 'https://www.metacareers.com/jobs/'
    },
    {
        'name': 'Amazon',
        'url': 'https://www.amazon.jobs/en/search'
    },
]
