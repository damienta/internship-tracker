from bs4 import BeautifulSoup

from scraper.company_scraper import CompanyScraper


def test_company_scraper_extracts_relevant_uk_roles_from_fake_html(monkeypatch):
    html = """
    <table>
      <tr class="data-row">
        <a class="jobTitle-link" href="/job/1">Software Engineering Intern</a>
        <span class="jobLocation">London, United Kingdom</span>
      </tr>
      <tr class="data-row">
        <a class="jobTitle-link" href="/job/2">Senior Product Manager</a>
        <span class="jobLocation">London, United Kingdom</span>
      </tr>
      <tr class="data-row">
        <a class="jobTitle-link" href="/job/3">Graduate Software Engineer</a>
        <span class="jobLocation">Berlin, Germany</span>
      </tr>
    </table>
    """
    soup = BeautifulSoup(html, "html.parser")

    scraper = CompanyScraper("BT Group")

    monkeypatch.setattr(scraper, "fetch_page", lambda _url: soup)
    monkeypatch.setattr(scraper, "find_next_page", lambda _soup, _url: None)
    monkeypatch.setattr(scraper, "fetch_job_details", lambda _url: None)

    jobs = scraper.scrape()

    assert len(jobs) == 1
    assert "intern" in jobs[0]["title"].lower()
    assert "london" in jobs[0]["location"].lower()
    assert jobs[0]["url"].endswith("/job/1")
    assert jobs[0]["source_website"] == "bt group"
