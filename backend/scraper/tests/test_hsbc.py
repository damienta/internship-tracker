"""
Test scraper for HSBC careers - HTML-only (Avature ATS)
robots.txt: mycareer.hsbc.com explicitly Allow: /external
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from scraper.company_scraper import CompanyScraper

def main():
    scraper = CompanyScraper(
        company_name="HSBC",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        delay=2.0
    )

    print("Scraping HSBC careers... (pipelineOffset pagination, 10 jobs/page)")
    print("=" * 60)

    jobs = scraper.scrape()

    print(f"\nTotal relevant jobs found: {len(jobs)}")
    print("=" * 60)

    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}] {job.get('title', 'N/A')}")
        print(f"Location: {job.get('location', 'N/A')}")
        if job.get('description'):
            print(f"Description: {job['description'][:150]}...")
            print(f"Posted: {job.get('date_posted', 'Not specified')}")
            print(f"Deadline: {job.get('deadline', 'Not specified')}")
            print(f"Start Date: {job.get('start_date', 'Not specified')}")
            print(f"URL: {job.get('url', 'N/A')}")

if __name__ == '__main__':
    main()
