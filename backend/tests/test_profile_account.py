import time


def _unique_username(prefix="profile"):
    return f"{prefix}_{int(time.time() * 1000000)}"


def _register_user(client, prefix="profile", password="password123"):
    username = _unique_username(prefix)
    email = f"{username}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201
    data = response.get_json()
    return {**data["user"], "auth": {"Authorization": f"Bearer {data['token']}"}}, password


def test_get_profile_returns_default_shape(client):
    user, _ = _register_user(client, "profile_get")
    response = client.get(f"/api/profile/{user['id']}", headers=user["auth"])
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == user["username"]
    assert "profile" in data and isinstance(data["profile"], dict)


def test_update_profile_saves_fields(client):
    user, _ = _register_user(client, "profile_put")
    payload = {
        "full_name": "Test User",
        "university": "Test University",
        "degree": "Computer Science",
        "skills": ["Python", "python", "SQL", ""],
    }
    response = client.put(f"/api/profile/{user['id']}", json=payload, headers=user["auth"])
    assert response.status_code == 200
    profile = response.get_json()["profile"]
    assert profile["full_name"] == "Test User"
    assert profile["university"] == "Test University"
    assert profile["degree"] == "Computer Science"
    assert profile["skills"] == ["Python", "SQL"]


def test_update_account_identity_requires_correct_password(client):
    user, _ = _register_user(client, "identity_bad")
    response = client.patch(
        "/api/account/id",
        headers=user["auth"],
        json={
            "username": f"{user['username']}_new",
            "email": user["email"],
            "current_password": "wrong-password",
        },
    )
    assert response.status_code == 401


def test_update_account_identity_success(client):
    user, password = _register_user(client, "identity_ok")
    new_username = f"{user['username']}_updated"
    new_email = f"{new_username}@example.com"

    response = client.patch(
        "/api/account/id",
        headers=user["auth"],
        json={
            "username": new_username,
            "email": new_email,
            "current_password": password,
        },
    )
    assert response.status_code == 200
    updated = response.get_json()["user"]
    assert updated["username"] == new_username
    assert updated["email"] == new_email


def test_update_account_identity_duplicate_username_returns_400(client):
    owner, owner_password = _register_user(client, "identity_dup_owner")
    other, _ = _register_user(client, "identity_dup_other")

    response = client.patch(
        "/api/account/id",
        headers=owner["auth"],
        json={
            "username": other["username"],
            "email": owner["email"],
            "current_password": owner_password,
        },
    )
    assert response.status_code == 400


def test_update_account_identity_invalid_email_returns_400(client):
    user, password = _register_user(client, "identity_bad_email")
    response = client.patch(
        "/api/account/id",
        headers=user["auth"],
        json={
            "username": user["username"],
            "email": "not-an-email",
            "current_password": password,
        },
    )
    assert response.status_code == 400


def test_change_password_success_then_login_with_new_password(client):
    user, old_password = _register_user(client, "change_pw")
    new_password = "newpassword456"

    response = client.post(
        "/api/account/change-password",
        headers=user["auth"], json={"current_password": old_password, "new_password": new_password},
    )
    assert response.status_code == 200

    login_old = client.post(
        "/api/auth/login",
        json={"username": user["username"], "password": old_password},
    )
    assert login_old.status_code == 401

    login_new = client.post(
        "/api/auth/login",
        json={"username": user["username"], "password": new_password},
    )
    assert login_new.status_code == 200


def test_change_password_short_new_password_returns_400(client):
    user, password = _register_user(client, "change_pw_short")
    response = client.post(
        "/api/account/change-password",
        headers=user["auth"], json={"current_password": password, "new_password": "short"},
    )
    assert response.status_code == 400


def test_delete_account_requires_password(client):
    user, _ = _register_user(client, "delete_req")
    response = client.delete(f"/api/account/{user['id']}", json={}, headers=user["auth"])
    assert response.status_code == 400


def test_delete_account_success(client):
    user, password = _register_user(client, "delete_ok")

    response = client.delete(f"/api/account/{user['id']}", json={"password": password}, headers=user["auth"])
    assert response.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={"username": user["username"], "password": password},
    )
    assert login.status_code == 401


def test_delete_account_wrong_password_returns_401(client):
    user, _ = _register_user(client, "delete_wrong_pw")
    response = client.delete(f"/api/account/{user['id']}", json={"password": "wrong-password"}, headers=user["auth"])
    assert response.status_code == 401


def test_profile_requires_token(client):
    user, _ = _register_user(client, "profile_no_token")
    response = client.get(f"/api/profile/{user['id']}")
    assert response.status_code == 401


def test_profile_of_another_user_is_forbidden(client):
    owner, _ = _register_user(client, "profile_owner")
    other, _ = _register_user(client, "profile_other")

    read = client.get(f"/api/profile/{owner['id']}", headers=other["auth"])
    assert read.status_code == 403

    write = client.put(f"/api/profile/{owner['id']}", json={"full_name": "Hijack"}, headers=other["auth"])
    assert write.status_code == 403


def test_change_password_ignores_user_id_from_client(client):
    owner, owner_password = _register_user(client, "pw_owner")
    other, other_password = _register_user(client, "pw_other")

    # A user_id in the body is ignored, so this changes the caller's own password
    response = client.post(
        "/api/account/change-password",
        headers=other["auth"],
        json={"user_id": owner["id"], "current_password": other_password, "new_password": "takenover123"},
    )
    assert response.status_code == 200

    owner_login = client.post("/api/auth/login", json={"username": owner["username"], "password": owner_password})
    assert owner_login.status_code == 200


def test_delete_another_users_account_is_forbidden(client):
    owner, owner_password = _register_user(client, "delete_owner")
    other, _ = _register_user(client, "delete_other")

    response = client.delete(f"/api/account/{owner['id']}", json={"password": owner_password}, headers=other["auth"])
    assert response.status_code == 403
