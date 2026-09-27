import time


def _unique_username(prefix="community"):
    return f"{prefix}_{int(time.time() * 1000000)}"


def _register_user(client, prefix="community"):
    username = _unique_username(prefix)
    email = f"{username}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    assert response.status_code == 201
    data = response.get_json()
    return {**data["user"], "auth": {"Authorization": f"Bearer {data['token']}"}}


def test_community_thread_crud_flow_owner(client):
    user = _register_user(client, "thread_owner")

    create_response = client.post(
        "/api/community/threads",
        headers=user["auth"],
        json={
            "category": "discussion",
            "title": "Interview tips",
            "content": "Share your best interview prep approach.",
        },
    )
    assert create_response.status_code == 201
    thread = create_response.get_json()

    list_response = client.get("/api/community/threads", query_string={"category": "discussion"})
    assert list_response.status_code == 200
    threads = list_response.get_json()
    assert any(item["id"] == thread["id"] for item in threads)

    update_response = client.patch(
        f"/api/community/threads/{thread['id']}",
        headers=user["auth"], json={"title": "Interview tips updated", "content": "Updated content."},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["title"] == "Interview tips updated"

    delete_response = client.delete(
        f"/api/community/threads/{thread['id']}",
        headers=user["auth"],
    )
    assert delete_response.status_code == 200


def test_community_thread_update_forbidden_for_non_owner(client):
    owner = _register_user(client, "thread_forbid_owner")
    other = _register_user(client, "thread_forbid_other")

    create_response = client.post(
        "/api/community/threads",
        headers=owner["auth"],
        json={
            "category": "discussion",
            "title": "Owner thread",
            "content": "Only owner can edit.",
        },
    )
    assert create_response.status_code == 201
    thread_id = create_response.get_json()["id"]

    forbidden = client.patch(
        f"/api/community/threads/{thread_id}",
        headers=other["auth"], json={"title": "Hijack", "content": "Nope"},
    )
    assert forbidden.status_code == 403


def test_community_thread_delete_forbidden_for_non_owner(client):
    owner = _register_user(client, "thread_delete_owner")
    other = _register_user(client, "thread_delete_other")

    create_response = client.post(
        "/api/community/threads",
        headers=owner["auth"],
        json={
            "category": "discussion",
            "title": "Owner thread delete",
            "content": "Only owner can delete.",
        },
    )
    assert create_response.status_code == 201
    thread_id = create_response.get_json()["id"]

    forbidden = client.delete(
        f"/api/community/threads/{thread_id}",
        headers=other["auth"],
    )
    assert forbidden.status_code == 403


def test_community_invalid_category_returns_400(client):
    user = _register_user(client, "invalid_category")
    response = client.post(
        "/api/community/threads",
        headers=user["auth"],
        json={
            "category": "not-a-category",
            "title": "Bad category",
            "content": "Should fail",
        },
    )
    assert response.status_code == 400


def test_community_company_ratings_invalid_rating_returns_400(client):
    user = _register_user(client, "invalid_rating")
    response = client.post(
        "/api/community/threads",
        headers=user["auth"],
        json={
            "category": "company-ratings",
            "title": "Rate this company",
            "content": "Rating missing/invalid",
            "rating": 6,
        },
    )
    assert response.status_code == 400


def test_community_empty_thread_content_returns_400(client):
    user = _register_user(client, "empty_content")
    response = client.post(
        "/api/community/threads",
        headers=user["auth"],
        json={
            "category": "discussion",
            "title": "",
            "content": "",
        },
    )
    assert response.status_code == 400


def test_community_reply_crud_flow_owner(client):
    user = _register_user(client, "reply_owner")

    thread_resp = client.post(
        "/api/community/threads",
        headers=user["auth"],
        json={
            "category": "discussion",
            "title": "Reply test",
            "content": "Thread for reply tests.",
        },
    )
    assert thread_resp.status_code == 201
    thread_id = thread_resp.get_json()["id"]

    reply_create = client.post(
        f"/api/community/threads/{thread_id}/replies",
        headers=user["auth"], json={"content": "First reply"},
    )
    assert reply_create.status_code == 201
    reply = reply_create.get_json()

    replies = client.get(f"/api/community/threads/{thread_id}/replies")
    assert replies.status_code == 200
    assert any(item["id"] == reply["id"] for item in replies.get_json())

    reply_update = client.patch(
        f"/api/community/replies/{reply['id']}",
        headers=user["auth"], json={"content": "Edited reply"},
    )
    assert reply_update.status_code == 200
    assert reply_update.get_json()["content"] == "Edited reply"

    reply_delete = client.delete(
        f"/api/community/replies/{reply['id']}",
        headers=user["auth"],
    )
    assert reply_delete.status_code == 200


def test_community_reply_update_forbidden_for_non_owner(client):
    owner = _register_user(client, "reply_forbid_owner")
    other = _register_user(client, "reply_forbid_other")

    thread_resp = client.post(
        "/api/community/threads",
        headers=owner["auth"],
        json={
            "category": "discussion",
            "title": "Reply forbidden",
            "content": "Thread",
        },
    )
    assert thread_resp.status_code == 201
    thread_id = thread_resp.get_json()["id"]

    reply_resp = client.post(
        f"/api/community/threads/{thread_id}/replies",
        headers=owner["auth"], json={"content": "Owner reply"},
    )
    assert reply_resp.status_code == 201
    reply_id = reply_resp.get_json()["id"]

    forbidden = client.patch(
        f"/api/community/replies/{reply_id}",
        headers=other["auth"], json={"content": "Hijack"},
    )
    assert forbidden.status_code == 403


def test_community_create_thread_requires_token(client):
    response = client.post(
        "/api/community/threads",
        json={"category": "discussion", "title": "No token", "content": "Should fail"},
    )
    assert response.status_code == 401


def test_community_thread_author_comes_from_token(client):
    owner = _register_user(client, "thread_impersonated")
    other = _register_user(client, "thread_impersonator")

    response = client.post(
        "/api/community/threads",
        headers=other["auth"],
        json={"user_id": owner["id"], "category": "discussion", "title": "Spoof", "content": "Posting as someone else"},
    )
    assert response.status_code == 201
    assert response.get_json()["user_id"] == other["id"]
