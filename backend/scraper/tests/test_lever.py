"""
Test the LeverScraper across all configured companies.
Run: python -m scraper.tests.test_lever
"""
import sys
import time
import logging

sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from scraper.lever_scraper import LeverScraper, LEVER_COMPANIES

print("=" * 60)
print("TESTING LEVER SCRAPER")
print(f"Companies: {len(LEVER_COMPANIES)}")
print("UK only:   True")
print("=" * 60)

start = time.time()
scraper = LeverScraper(uk_only=True)
jobs = scraper.scrape()
elapsed = time.time() - start

print(f"\nTotal relevant UK roles found: {len(jobs)}")
print(f"Time taken: {elapsed:.1f}s")
print("=" * 60)

for i, job in enumerate(jobs, 1):
    print(f"\n[{i}] {job['title']}")
    print(f"  Company:   {job['company']}")
    print(f"  Location:  {job['location']}")
    print(f"  Posted:    {job['date_posted']}")
    print(f"  URL:       {job['url']}")
    if job["description"]:
        print(f"  Desc:      {job['description'][:120]}...")
