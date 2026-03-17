"""
company_configs - Company-specific scraper configurations.

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
    # BT
    # Taleo ATS, table-based listings, pagination with &p=1, &p=2 etc.
    'BT Group': {
        'careers_url': 'https://jobs.bt.com/search/?createNewAlert=false&q=&locationsearch=&optionsFacetsDD_brand=&optionsFacetsDD_customfield3=',
        'job_card_selector': 'tr.data-row',
        'title_selector': 'a.jobTitle-link',
        'location_selector': 'span.jobLocation',
        'link_selector': 'a.jobTitle-link',
        'notes': 'UK telecoms company - table-based job listings'
    },

    # HSBC
    # HTML-rendered via Avature ATS pipelineOffset pagination
    # URL filters for UK intern/grad roles
    'HSBC': {
        'careers_url': 'https://mycareer.hsbc.com/en_GB/external/SearchJobs/?keyword=intern+graduate+junior+placement&pipelineRecordsPerPage=10&pipelineOffset=0',
        'job_card_selector': 'article.article--result',
        'title_selector': 'h3.article__header__text__title a',
        'location_selector': 'span.location',
        'link_selector': 'h3.article__header__text__title a',
        'notes': 'UK/global bank - Avature ATS, 10 jobs/page, pipelineOffset pagination'
    },

    # SAP UK
    # Pagination: startrow=25, startrow=50 etc.
    'SAP': {
        'careers_url': 'https://jobs.sap.com/search/?q=intern+graduate+junior&locationsearch=UK+United+Kingdom&location=GBR',
        'job_card_selector': 'tr.data-row',
        'title_selector': 'a.jobTitle-link',
        'location_selector': 'span.jobLocation',
        'link_selector': 'a.jobTitle-link',
        'notes': 'Enterprise software - Taleo ATS, same structure as BT Group, startrow pagination, UK-filtered'
    },

    # Template for adding more companies:
    # 'Company Name': {
    #     'careers_url': 'https://company.com/careers',
    #     'job_card_selector': 'div.job-card',
    #     'title_selector': 'h2.title',
    #     'location_selector': 'span.location',
    #     'link_selector': 'a.apply-link',
    #     'description_selector': 'div.desc',
    #     'date_selector': 'time.posted',
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
