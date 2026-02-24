"""
Test the BT Group careers scraper.
Run: python -m scraper.tests.test_bt
"""
import sys
import time
import logging

sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from scraper.company_scraper import CompanyScraper

print("=" * 60)
print("TESTING BT GROUP SCRAPER")
print("=" * 60)

start = time.time()
scraper = CompanyScraper("BT Group")
jobs = scraper.scrape()
elapsed = time.time() - start

print(f"\nTotal relevant UK roles found: {len(jobs)}")
print(f"Time taken: {elapsed:.1f}s")
print("=" * 60)

for i, job in enumerate(jobs, 1):
    print(f"\n[{i}] {job['title']}")
    print(f"  Location:  {job['location']}")
    print(f"  Posted:    {job.get('date_posted', 'N/A')}")
    print(f"  Deadline:  {job.get('deadline', 'N/A')}")
    print(f"  URL:       {job['url']}")
    if job.get('description'):
        print(f"  Desc:      {job['description'][:120]}...")
