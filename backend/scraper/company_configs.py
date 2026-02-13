"""
Company-specific scraper configurations.

This file stores custom CSS selectors for companies that don't match
the standard patterns in BaseScraper.

When adding a new company:
1. Run BaseScraper first - it might work automatically
2. If it fails, inspect the HTML and add custom selectors here
3. Use CompanyScraper class which checks here first

Example:
    # If Google's careers page doesn't work with default selectors:
    COMPANY_CONFIGS = {
        'Google': {
            'careers_url': 'https://careers.google.com/jobs/results/',
            'job_card_selector': 'li.lLd3Je',  # Custom Google selector
            'title_selector': 'h3.QJPWVe',
            'location_selector': 'span.r0wTof',
        }
    }
"""

from typing import Dict, Optional


# Company-specific configurations
# Add custom selectors here when default patterns don't work
COMPANY_CONFIGS = {
    'BT Group': {
        'careers_url': 'https://jobs.bt.com/search/?createNewAlert=false&q=&locationsearch=&optionsFacetsDD_brand=&optionsFacetsDD_customfield3=',
        'job_card_selector': 'tr.data-row',
        'title_selector': 'a.jobTitle-link',
        'location_selector': 'span.jobLocation',
        'link_selector': 'a.jobTitle-link',
        'notes': 'UK telecoms company - table-based job listings'
    },
    
    'Arm': {
        'careers_url': 'https://careers.arm.com/search-jobs',
        'job_card_selector': 'li.job-card',
        'title_selector': 'a.job-card__title',
        'location_selector': 'span.job-card__location',
        'link_selector': 'a.job-card__title',
        'notes': 'UK tech company - list-based layout'
    },
    
    'Man Group': {
        'careers_url': 'https://www.man.com/careers',
        'job_card_selector': 'tr.job-post',
        'title_selector': 'p.body--medium',
        'location_selector': 'p.body__secondary',
        'link_selector': 'a',
        'notes': 'Table-based layout - may be blocked by robots.txt'
    },
    
    'Goldman Sachs': {
        'careers_url': 'https://www.goldmansachs.com/careers/students/programs/',
        'job_card_selector': 'div.job-result',
        'title_selector': 'h3.job-title',
        'location_selector': 'span.location',
        'notes': 'Standard div-based with custom classes'
    },
    
    # Template for adding more companies:
    # 'Company Name': {
    #     'careers_url': 'https://company.com/careers',
    #     'job_card_selector': 'div.job-card',  # CSS selector for job container
    #     'title_selector': 'h2.title',         # CSS selector for job title
    #     'location_selector': 'span.location', # CSS selector for location
    #     'link_selector': 'a.apply-link',      # Optional: specific link selector
    #     'description_selector': 'div.desc',   # Optional: description selector
    #     'date_selector': 'time.posted',       # Optional: date posted selector
    #     'notes': 'Any special notes about this company'
    # },
}


def get_company_config(company_name: str) -> Optional[Dict]:
    """
    Get custom configuration for a specific company.
    
    Args:
        company_name: Name of the company (e.g., "Google", "Microsoft")
        
    Returns:
        Dictionary with custom selectors, or None if not configured
        
    Example:
        config = get_company_config("Man Group")
        if config:
            job_cards = soup.select(config['job_card_selector'])
    """
    return COMPANY_CONFIGS.get(company_name)


def add_company_config(company_name: str, config: Dict) -> None:
    """
    Add or update company configuration.
    
    Args:
        company_name: Name of the company
        config: Dictionary with selectors and settings
        
    Example:
        add_company_config("Barclays", {
            'careers_url': 'https://barclays.com/careers',
            'job_card_selector': 'div.job-item',
            'title_selector': 'h3',
        })
    """
    COMPANY_CONFIGS[company_name] = config


def list_configured_companies() -> list:
    """
    Get list of companies with custom configurations.
    
    Returns:
        List of company names that have custom configs
    """
    return list(COMPANY_CONFIGS.keys())
