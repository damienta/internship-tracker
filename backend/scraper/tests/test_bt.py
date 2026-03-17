"""Quick test for BT Group careers scraper"""

from scraper.company_scraper import CompanyScraper

print("\n" + "="*60)
print("TESTING BT GROUP SCRAPER")
print("="*60 + "\n")

# Create scraper
scraper = CompanyScraper("BT Group")

print(f"Scraping: {scraper.careers_url}\n")

# Run scraper
jobs = scraper.scrape()

# Display results
print("\n" + "-"*60)
print("RESULTS")
print("-"*60 + "\n")

if jobs:
    print(f"Found {len(jobs)} relevant internship/graduate roles:\n")
    
    for i, job in enumerate(jobs[:10], 1):
        print(f"{i}. {job['title']}")
        print(f"Location: {job['location']}")
        if job.get('description'):
            desc = job['description'][:150] + "..." if len(job.get('description', '')) > 150 else job.get('description', 'N/A')
            print(f"Description: {desc}")
        if job.get('date_posted'):
            print(f"Posted: {job['date_posted']}")
        else:
            print(f"Posted: Not specified")
        if job.get('deadline'):
            print(f"Deadline: {job['deadline']}")
        else:
            print(f"Deadline: Not specified")
        if job.get('start_date'):
            print(f"Start Date: {job['start_date']}")
        else:
            print(f"Start Date: Not specified")
        print(f"URL: {job['url']}")
        print()
    
    if len(jobs) > 10:
        print(f"... and {len(jobs) - 10} more roles")
else:
    print("No relevant internship/graduate jobs found")
    print("\nThis could mean:")
    print("1. No current openings matching keywords (intern, graduate)")
    print("2. Selectors need updating")

print("\n" + "="*60)
