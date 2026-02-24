"""
Test the GreenhouseScraper across all configured companies.
Run: python -m scraper.tests.test_greenhouse
"""
import sys
import time
import logging

sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

from scraper.greenhouse_scraper import GreenhouseScraper, GREENHOUSE_COMPANIES

print("=" * 60)
print("TESTING GREENHOUSE SCRAPER")
print(f"Companies: {[name for name, _ in GREENHOUSE_COMPANIES]}")
print("UK only:   True")
print("=" * 60)

start = time.time()
scraper = GreenhouseScraper(uk_only=True)
jobs = scraper.scrape()
elapsed = time.time() - start

print(f"\nTotal relevant UK roles found: {len(jobs)}")
print(f"Time taken: {elapsed:.1f}s")
print("=" * 60)

for i, job in enumerate(jobs, 1):
    print(f"\n[{i}] {job['title']}")
    print(f"Company: {job['company']}")
    print(f"Location: {job['location']}")
    print(f"Posted: {job['date_posted']}")
    print(f"URL: {job['url']}")
    if job["description"]:
        print(f"Desc: {job['description'][:120]}...")
