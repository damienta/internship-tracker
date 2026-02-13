"""
Company-specific scraper that uses custom configurations.

This scraper:
1. Checks if company has custom config in company_configs.py
2. If yes: Uses those specific selectors (guaranteed to work)
3. If no: Falls back to BaseScraper's 30+ generic patterns

This hybrid approach ensures reliability across different websites.

Example usage:
    scraper = CompanyScraper(
        company_name="Man Group",
        user_agent="Mozilla/5.0..."
    )
    jobs = scraper.scrape()  # Uses Man Group's custom selectors
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper
from scraper.company_configs import get_company_config

logger = logging.getLogger(__name__)


class CompanyScraper(BaseScraper):
    """
    Scraper for individual company career pages.
    Uses custom configurations when available, falls back to generic patterns.
    """
    
    def __init__(self, company_name: str, 
                 user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                 careers_url: Optional[str] = None,
                 delay: float = 2.0):
        """
        Initialize scraper for a specific company.
        
        Args:
            company_name: Name of company (e.g., "Google", "Man Group")
            user_agent: Browser identity string
            careers_url: Optional URL override (uses config if not provided)
            delay: Seconds to wait between requests
            
        Example:
            # Uses Man Group's custom config automatically:
            scraper = CompanyScraper("Man Group")
            
            # Custom URL override:
            scraper = CompanyScraper(
                "Google", 
                careers_url="https://careers.google.com/jobs/results/"
            )
        """
        # Load company-specific configuration
        self.config = get_company_config(company_name)
        
        # Determine careers URL
        if careers_url:
            final_url = careers_url
        elif self.config and 'careers_url' in self.config:
            final_url = self.config['careers_url']
            logger.info(f"✅ Using custom config for {company_name}")
        else:
            raise ValueError(
                f"No careers URL provided and {company_name} not in configs. "
                f"Either provide careers_url parameter or add to company_configs.py"
            )
        
        # Initialize parent class
        super().__init__(
            company_name=company_name,
            careers_url=final_url,
            user_agent=user_agent,
            delay=delay
        )
    
    
    def extract_job_cards(self, soup: BeautifulSoup) -> List:
        """
        Override to prioritize company-specific selectors.
        
        Workflow:
        1. If company has custom config → use that selector (most reliable)
        2. Otherwise → fall back to BaseScraper's 30+ generic patterns
        
        Args:
            soup: BeautifulSoup object of careers page
            
        Returns:
            List of job card elements
        """
        # Try custom selector first (if configured)
        if self.config and 'job_card_selector' in self.config:
            custom_selector = self.config['job_card_selector']
            job_cards = soup.select(custom_selector)
            
            if job_cards:
                logger.info(f"✅ Found {len(job_cards)} jobs using custom selector: {custom_selector}")
                return job_cards
            else:
                logger.warning(f"⚠️  Custom selector '{custom_selector}' found no results")
                logger.info("Falling back to generic patterns...")
        
        # Fall back to generic patterns (BaseScraper's 30+ selectors)
        return super().extract_job_cards(soup)
    
    
    def extract_job_data(self, job_card) -> Optional[Dict]:
        """
        Override to use company-specific selectors when available.
        
        Args:
            job_card: BeautifulSoup element for one job
            
        Returns:
            Dictionary with job data (title, location, url, etc.)
        """
        job_data = {
            'title': None,
            'company': self.company_name,
            'location': None,
            'url': None,
            'description': None,
            'date_posted': None,
            'deadline': None,
            'scraped_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Extract title (use custom selector if available)
            if self.config and 'title_selector' in self.config:
                title_elem = job_card.select_one(self.config['title_selector'])
                job_data['title'] = title_elem.get_text(strip=True) if title_elem else None
            
            # Fall back to generic title extraction
            if not job_data['title']:
                title = (
                    self.extract_text(job_card, 'h2') or
                    self.extract_text(job_card, 'h3') or
                    self.extract_text(job_card, 'h4') or
                    self.extract_text(job_card, '.job-title') or
                    self.extract_text(job_card, 'p.body--medium') or
                    self.extract_text(job_card, 'a')
                )
                job_data['title'] = title
            
            # Extract location (use custom selector if available)
            if self.config and 'location_selector' in self.config:
                location_elem = job_card.select_one(self.config['location_selector'])
                job_data['location'] = location_elem.get_text(strip=True) if location_elem else None
            
            # Fall back to generic location extraction
            if not job_data['location']:
                location = (
                    self.extract_text(job_card, '.location') or
                    self.extract_text(job_card, '.job-location') or
                    self.extract_text(job_card, 'p.body__secondary') or
                    self.extract_text(job_card, 'span[class*="location"]')
                )
                job_data['location'] = location
            
            # Extract URL (use custom selector if available)
            if self.config and 'link_selector' in self.config:
                link_elem = job_card.select_one(self.config['link_selector'])
            else:
                link_elem = job_card.find('a', href=True)
            
            if link_elem and link_elem.get('href'):
                href = link_elem['href']
                # Convert relative URLs to absolute
                from urllib.parse import urljoin
                job_data['url'] = urljoin(self.careers_url, href)
            
            # Extract description (use custom selector if available)
            if self.config and 'description_selector' in self.config:
                desc_elem = job_card.select_one(self.config['description_selector'])
                job_data['description'] = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract date (use custom selector if available)
            if self.config and 'date_selector' in self.config:
                date_elem = job_card.select_one(self.config['date_selector'])
                job_data['date_posted'] = date_elem.get_text(strip=True) if date_elem else None
            
            # Extract deadline (use custom selector if available)
            if self.config and 'deadline_selector' in self.config:
                deadline_elem = job_card.select_one(self.config['deadline_selector'])
                job_data['deadline'] = deadline_elem.get_text(strip=True) if deadline_elem else None
        
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
        
        return job_data
    
    
    def test_selectors(self, soup: BeautifulSoup) -> Dict:
        """
        Test which selectors work for this company's HTML.
        Useful for debugging and adding new companies.
        
        Args:
            soup: BeautifulSoup object of careers page
            
        Returns:
            Dictionary showing which selectors found results
            
        Example:
            scraper = CompanyScraper("NewCompany", careers_url="...")
            page = scraper.fetch_page(scraper.careers_url)
            results = scraper.test_selectors(page)
            print(results)  # Shows which selectors work
        """
        results = {
            'job_cards': {},
            'config_status': 'custom' if self.config else 'generic',
            'company': self.company_name
        }
        
        # Test all generic selectors from BaseScraper
        common_selectors = [
            'tr.job-post', 'tr.job-listing', 'tr.job-row',
            'div.job-card', 'div.job-listing', 'div.job-item',
            'article.job', 'li.job', 'a.job-link'
        ]
        
        for selector in common_selectors:
            cards = soup.select(selector)
            if cards:
                results['job_cards'][selector] = len(cards)
        
        # If company has custom config, test those too
        if self.config and 'job_card_selector' in self.config:
            custom = self.config['job_card_selector']
            cards = soup.select(custom)
            results['job_cards'][f"{custom} (custom)"] = len(cards) if cards else 0
        
        return results
