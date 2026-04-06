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


def test_jobs_invalid_pagination_defaults(client):
    data = client.get("/api/jobs?page=abc&per_page=def").get_json()
    assert data["page"] == 1
    assert data["per_page"] == 20


def test_jobs_negative_or_zero_pagination_is_clamped(client):
    data = client.get("/api/jobs?page=-5&per_page=0").get_json()
    assert data["page"] == 1
    assert data["per_page"] == 1


def test_jobs_empty_page(client):
    data = client.get("/api/jobs?page=999").get_json()
    assert data["results"] == []


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


def test_upcoming_jobs_returns_results_key(client):
    data = client.get("/api/jobs/upcoming").get_json()
    assert "results" in data


def test_sort_match_without_user_id_returns_400(client):
    response = client.get("/api/jobs?sort=match")
    assert response.status_code == 400


def test_sort_match_with_missing_user_returns_404(client):
    response = client.get("/api/jobs?sort=match&user_id=999999")
    assert response.status_code == 404


def test_job_by_id_returns_200(client):
    job_id = client.get("/api/jobs").get_json()["results"][0]["id"]
    assert client.get(f"/api/jobs/{job_id}").status_code == 200


def test_job_by_invalid_id_returns_404(client):
    assert client.get("/api/jobs/999999").status_code == 404
