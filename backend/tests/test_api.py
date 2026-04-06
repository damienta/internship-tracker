"""
tests/test_api.py - API endpoint tests using SQLite.
Run: pytest tests/test_api.py -v
"""
import pytest
from datetime import datetime, timezone
from app import create_app
from models import db, Internship

# Fixtures
@pytest.fixture(scope="module")
def client():
    app = create_app(db_url="sqlite:///:memory:")
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        db.session.add_all([
            Internship(title="Software Engineering Intern",
                       company="Alpha Corp",
                       location="London, UK",
                       url="https://example.com/1",
                       source_website="greenhouse",
                       is_active=True,
                       scraped_at=datetime.now(timezone.utc)),
            Internship(title="Graduate Software Engineer",
                       company="Beta Ltd",
                       location="London, UK",
                       url="https://example.com/2",
                       source_website="lever",
                       is_active=True,
                       scraped_at=datetime.now(timezone.utc)),
            Internship(title="Industrial Placement Engineer",
                       company="Charlie Inc",
                       location="Manchester, UK",
                       url="https://example.com/3",
                       source_website="lever",
                       is_active=True,
                       scraped_at=datetime.now(timezone.utc)),
            Internship(title="Technology Graduate Scheme",
                       company="Delta Co",
                       location="Birmingham, UK",
                       url="https://example.com/4",
                       source_website="bt",
                       is_active=True,
                       scraped_at=datetime.now(timezone.utc)),
            Internship(title="Expired Intern Role",
                       company="Echo Ltd",
                       location="London, UK",
                       url="https://example.com/5",
                       source_website="bt",
                       is_active=False,
                       scraped_at=datetime.now(timezone.utc)),
        ])
        db.session.commit()

    yield app.test_client()


# /api/stats

def test_stats_returns_200(client):
    assert client.get("/api/stats").status_code == 200

def test_stats_has_required_keys(client):
    data = client.get("/api/stats").get_json()
    assert {"total", "active", "companies", "by_source", "by_role_type"} <= data.keys()

def test_stats_active_less_than_total(client):
    data = client.get("/api/stats").get_json()
    assert data["active"] < data["total"]

# /api/companies

def test_companies_returns_list(client):
    data = client.get("/api/companies").get_json()
    assert isinstance(data, list)

def test_companies_sorted(client):
    data = client.get("/api/companies").get_json()
    assert data == sorted(data)

def test_companies_no_duplicates(client):
    data = client.get("/api/companies").get_json()
    assert len(data) == len(set(data))

# /api/jobs

def test_jobs_returns_200(client):
    assert client.get("/api/jobs").status_code == 200

def test_jobs_response_shape(client):
    data = client.get("/api/jobs").get_json()
    assert {"page", "per_page", "total", "pages", "results"} <= data.keys()

def test_jobs_active_only(client):
    data = client.get("/api/jobs").get_json()
    assert all(j["is_active"] for j in data["results"])

def test_jobs_pagination(client):
    data = client.get("/api/jobs?per_page=2&page=1").get_json()
    assert len(data["results"]) == 2

def test_jobs_per_page_capped(client):
    data = client.get("/api/jobs?per_page=999").get_json()
    assert data["per_page"] == 100

def test_jobs_empty_page(client):
    data = client.get("/api/jobs?page=999").get_json()
    assert data["results"] == []

# /api/jobs - filters

def test_filter_company(client):
    data = client.get("/api/jobs?company=Alpha").get_json()
    assert all("Alpha" in j["company"] for j in data["results"])

def test_filter_source_json_scraper(client):
    data = client.get("/api/jobs?source=greenhouse").get_json()
    assert all(j["source_website"] == "greenhouse" for j in data["results"])

def test_filter_source_html_scraper(client):
    data = client.get("/api/jobs?source=bt").get_json()
    assert data["total"] >= 1
    assert all(j["source_website"] == "bt" for j in data["results"])

def test_filter_location_london(client):
    data = client.get("/api/jobs?location=London").get_json()
    assert data["total"] >= 1
    assert all("London" in j["location"] for j in data["results"])

def test_filter_keyword(client):
    data = client.get("/api/jobs?keyword=intern").get_json()
    assert all("intern" in j["title"].lower() for j in data["results"])

def test_filter_role_type_intern(client):
    data = client.get("/api/jobs?role_type=intern").get_json()
    assert data["total"] >= 1

def test_filter_role_type_graduate(client):
    data = client.get("/api/jobs?role_type=graduate").get_json()
    assert data["total"] >= 1

def test_filter_source_lever_single_filter(client):
    data = client.get("/api/jobs?source=lever").get_json()
    assert data["total"] >= 1
    assert all(j["source_website"] == "lever" for j in data["results"])

def test_filter_no_match_returns_empty(client):
    data = client.get("/api/jobs?company=zzznonexistent").get_json()
    assert data["total"] == 0 and data["results"] == []

def test_multi_filter_source_and_location(client):
    data = client.get("/api/jobs?source=lever&location=London").get_json()
    assert data["total"] >= 1
    assert all(j["source_website"] == "lever" and "London" in (j.get("location") or "") for j in data["results"])

def test_multi_filter_company_and_keyword(client):
    data = client.get("/api/jobs?company=Alpha&keyword=Software").get_json()
    assert data["total"] == 1
    assert all("Alpha" in j["company"] and "software" in j["title"].lower() for j in data["results"])

def test_multi_filter_role_type_and_location(client):
    data = client.get("/api/jobs?role_type=graduate&location=London").get_json()
    assert data["total"] >= 1
    assert all("graduate" in j["title"].lower() and "London" in (j.get("location") or "") for j in data["results"])


# /api/jobs/<id>

def test_job_by_id_returns_200(client):
    job_id = client.get("/api/jobs").get_json()["results"][0]["id"]
    assert client.get(f"/api/jobs/{job_id}").status_code == 200

def test_job_by_invalid_id_returns_404(client):
    assert client.get("/api/jobs/999999").status_code == 404
