from scraper.greenhouse_scraper import GreenhouseScraper


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_greenhouse_scraper_filters_and_returns_expected_items(monkeypatch):
    payload = {
        "jobs": [
            {
                "title": "Machine Learning Intern",
                "location": {"name": "London, UK"},
                "content": "<p>Build models</p>",
                "absolute_url": "https://boards.example.com/jobs/1",
                "first_published": "2024-10-01",
            },
            {
                "title": "Staff Engineer",
                "location": {"name": "London, UK"},
                "content": "<p>Senior role</p>",
                "absolute_url": "https://boards.example.com/jobs/2",
                "first_published": "2024-10-02",
            },
            {
                "title": "Graduate Engineer",
                "location": {"name": "San Francisco, US"},
                "content": "<p>US role</p>",
                "absolute_url": "https://boards.example.com/jobs/3",
                "first_published": "2024-10-03",
            },
        ]
    }

    scraper = GreenhouseScraper(companies=[("Example", "example")], uk_only=True)

    def _fake_get(_url, params=None, timeout=None):
        return _FakeResponse(payload)

    monkeypatch.setattr(scraper.session, "get", _fake_get)

    jobs = scraper.scrape_company("example", "Example")

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Machine Learning Intern"
    assert jobs[0]["company"] == "Example"
    assert jobs[0]["location"] == "London, UK"
    assert jobs[0]["description"] == "Build models"
    assert jobs[0]["url"] == "https://boards.example.com/jobs/1"
    assert jobs[0]["source_website"] == "greenhouse"
