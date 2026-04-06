import time


def _unique_username(prefix="tracker"):
    return f"{prefix}_{int(time.time() * 1000000)}"


def _register_user(client, prefix="tracker"):
    username = _unique_username(prefix)
    email = f"{username}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.get_json()["user"]


def _sample_tracker_payload(user_id):
    return {
        "user_id": user_id,
        "status": "Applied",
        "company": "Acme Ltd",
        "role": "Software Intern",
        "opening_date": "2026-04-01",
        "closing_date": "2026-04-30",
        "link": "https://example.com/apply",
        "notes": "Initial application submitted.",
    }


def test_tracker_crud_flow(client):
    user = _register_user(client, "crud")
    payload = _sample_tracker_payload(user["id"])

    create_response = client.post("/api/tracker", json=payload)
    assert create_response.status_code == 201
    created = create_response.get_json()
    assert created["company"] == payload["company"]

    list_response = client.get("/api/tracker", query_string={"user_id": user["id"]})
    assert list_response.status_code == 200
    entries = list_response.get_json()
    assert any(entry["id"] == created["id"] for entry in entries)

    patch_response = client.patch(
        f"/api/tracker/{created['id']}",
        json={"user_id": user["id"], "status": "Offer"},
    )
    assert patch_response.status_code == 200
    assert patch_response.get_json()["status"] == "Offer"

    delete_response = client.delete(
        f"/api/tracker/{created['id']}",
        query_string={"user_id": user["id"]},
    )
    assert delete_response.status_code == 200

    after_delete = client.get("/api/tracker", query_string={"user_id": user["id"]}).get_json()
    assert all(entry["id"] != created["id"] for entry in after_delete)


def test_tracker_validation_missing_required_fields(client):
    user = _register_user(client, "validate_missing")
    response = client.post(
        "/api/tracker",
        json={"user_id": user["id"], "status": "Applied", "company": "", "role": "", "link": ""},
    )
    assert response.status_code == 400


def test_tracker_get_without_user_id_returns_400(client):
    response = client.get("/api/tracker")
    assert response.status_code == 400


def test_tracker_validation_invalid_link(client):
    user = _register_user(client, "validate_link")
    payload = _sample_tracker_payload(user["id"])
    payload["link"] = "example.com/no-scheme"
    response = client.post("/api/tracker", json=payload)
    assert response.status_code == 400


def test_tracker_validation_invalid_date_format(client):
    user = _register_user(client, "validate_date")
    payload = _sample_tracker_payload(user["id"])
    payload["opening_date"] = "04/01/2026"
    response = client.post("/api/tracker", json=payload)
    assert response.status_code == 400


def test_tracker_validation_closing_before_opening(client):
    user = _register_user(client, "validate_order")
    payload = _sample_tracker_payload(user["id"])
    payload["opening_date"] = "2026-05-01"
    payload["closing_date"] = "2026-04-01"
    response = client.post("/api/tracker", json=payload)
    assert response.status_code == 400


def test_tracker_validation_invalid_status_on_create(client):
    user = _register_user(client, "validate_status")
    payload = _sample_tracker_payload(user["id"])
    payload["status"] = "Unknown Status"
    response = client.post("/api/tracker", json=payload)
    assert response.status_code == 400


def test_tracker_validation_invalid_internship_id(client):
    user = _register_user(client, "validate_internship")
    payload = _sample_tracker_payload(user["id"])
    payload["internship_id"] = 999999
    response = client.post("/api/tracker", json=payload)
    assert response.status_code == 404


def test_tracker_validation_non_integer_internship_id(client):
    user = _register_user(client, "validate_internship_type")
    payload = _sample_tracker_payload(user["id"])
    payload["internship_id"] = "abc"
    response = client.post("/api/tracker", json=payload)
    assert response.status_code == 400


def test_tracker_update_forbidden_for_non_owner(client):
    owner = _register_user(client, "forbid_owner")
    other = _register_user(client, "forbid_other")
    payload = _sample_tracker_payload(owner["id"])
    created = client.post("/api/tracker", json=payload)
    assert created.status_code == 201
    entry_id = created.get_json()["id"]

    response = client.patch(
        f"/api/tracker/{entry_id}",
        json={"user_id": other["id"], "status": "Offer"},
    )
    assert response.status_code == 403


def test_tracker_delete_forbidden_for_non_owner(client):
    owner = _register_user(client, "forbid_del_owner")
    other = _register_user(client, "forbid_del_other")
    payload = _sample_tracker_payload(owner["id"])
    created = client.post("/api/tracker", json=payload)
    assert created.status_code == 201
    entry_id = created.get_json()["id"]

    response = client.delete(
        f"/api/tracker/{entry_id}",
        query_string={"user_id": other["id"]},
    )
    assert response.status_code == 403


def test_tracker_update_invalid_status_returns_400(client):
    user = _register_user(client, "update_status")
    payload = _sample_tracker_payload(user["id"])
    created = client.post("/api/tracker", json=payload)
    assert created.status_code == 201
    entry_id = created.get_json()["id"]

    response = client.patch(
        f"/api/tracker/{entry_id}",
        json={"user_id": user["id"], "status": "Invalid"},
    )
    assert response.status_code == 400


def test_tracker_update_invalid_date_format_returns_400(client):
    user = _register_user(client, "update_date")
    payload = _sample_tracker_payload(user["id"])
    created = client.post("/api/tracker", json=payload)
    assert created.status_code == 201
    entry_id = created.get_json()["id"]

    response = client.patch(
        f"/api/tracker/{entry_id}",
        json={"user_id": user["id"], "opening_date": "01/04/2026"},
    )
    assert response.status_code == 400


def test_tracker_from_opportunity_prevents_duplicate_for_same_user(client):
    user = _register_user(client, "dup_same")
    jobs = client.get("/api/jobs").get_json()["results"]
    internship_id = jobs[0]["id"]

    first = client.post(
        "/api/tracker/from-opportunity",
        json={"user_id": user["id"], "internship_id": internship_id},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/tracker/from-opportunity",
        json={"user_id": user["id"], "internship_id": internship_id},
    )
    assert second.status_code == 409


def test_tracker_from_opportunity_allows_different_users(client):
    user_a = _register_user(client, "dup_diff_a")
    user_b = _register_user(client, "dup_diff_b")
    jobs = client.get("/api/jobs").get_json()["results"]
    internship_id = jobs[1]["id"]

    first = client.post(
        "/api/tracker/from-opportunity",
        json={"user_id": user_a["id"], "internship_id": internship_id},
    )
    second = client.post(
        "/api/tracker/from-opportunity",
        json={"user_id": user_b["id"], "internship_id": internship_id},
    )

    assert first.status_code == 201
    assert second.status_code == 201
