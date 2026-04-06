def test_stats_returns_200(client):
    assert client.get("/api/stats").status_code == 200


def test_stats_has_required_keys(client):
    data = client.get("/api/stats").get_json()
    assert {"total", "active", "companies", "by_source", "by_role_type"} <= data.keys()


def test_stats_active_less_than_total(client):
    data = client.get("/api/stats").get_json()
    assert data["active"] < data["total"]


def test_companies_returns_sorted_unique_list(client):
    data = client.get("/api/companies").get_json()
    assert isinstance(data, list)
    assert data == sorted(data)
    assert len(data) == len(set(data))


def test_skills_returns_sorted_unique_list(client):
    data = client.get("/api/skills").get_json()
    assert isinstance(data, list)
    assert data == sorted(data)
    assert len(data) == len(set(data))
