from scraper.lever_scraper import LeverScraper


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_lever_scraper_filters_and_returns_expected_items(monkeypatch):
    payload = [
        {
            "text": "Software Engineer Intern",
            "categories": {"location": "London, UK"},
            "descriptionPlain": "Python and SQL",
            "hostedUrl": "https://jobs.example.com/1",
            "createdAt": 1700000000000,
            "lists": [],
        },
        {
            "text": "Senior Engineer",
            "categories": {"location": "London, UK"},
            "descriptionPlain": "Senior role",
            "hostedUrl": "https://jobs.example.com/2",
            "createdAt": 1700000000001,
            "lists": [],
        },
        {
            "text": "Graduate Engineer",
            "categories": {"location": "New York, US"},
            "descriptionPlain": "US role",
            "hostedUrl": "https://jobs.example.com/3",
            "createdAt": 1700000000002,
            "lists": [],
        },
    ]

    scraper = LeverScraper(companies=[("Example", "example")], uk_only=True)

    def _fake_get(_url, params=None, timeout=None):
        return _FakeResponse(payload)

    monkeypatch.setattr(scraper.session, "get", _fake_get)

    jobs = scraper.scrape_company("example", "Example")

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Software Engineer Intern"
    assert jobs[0]["company"] == "Example"
    assert jobs[0]["location"] == "London, UK"
    assert jobs[0]["url"] == "https://jobs.example.com/1"
    assert jobs[0]["source_website"] == "lever"
