import time


def _unique_username(prefix="user"):
    return f"{prefix}_{int(time.time() * 1000000)}"


def _register(client, username=None, email=None, password="password123"):
    username = username or _unique_username("tester")
    email = email or f"{username}@example.com"
    payload = {"username": username, "email": email, "password": password}
    response = client.post("/api/auth/register", json=payload)
    return response, payload


def test_register_success_returns_user_and_token(client):
    response, payload = _register(client)
    assert response.status_code == 201
    data = response.get_json()
    assert data["user"]["username"] == payload["username"]
    assert data["user"]["email"] == payload["email"]
    assert isinstance(data.get("token"), str) and len(data["token"]) > 10


def test_register_missing_fields_returns_400(client):
    response = client.post("/api/auth/register", json={"username": "x"})
    assert response.status_code == 400


def test_register_without_json_body_returns_400(client):
    response = client.post("/api/auth/register")
    assert response.status_code == 400


def test_register_short_password_returns_400(client):
    response, payload = _register(client, password="short")
    assert payload["password"] == "short"
    assert response.status_code == 400


def test_register_normalizes_email_and_trims_username(client):
    raw_username = f"  {_unique_username('norm')}  "
    raw_email = f"  {raw_username.strip()}@EXAMPLE.COM  "
    response, _ = _register(client, username=raw_username, email=raw_email)
    assert response.status_code == 201
    user = response.get_json()["user"]
    assert user["username"] == raw_username.strip()
    assert user["email"] == raw_email.strip().lower()


def test_register_duplicate_username_returns_400(client):
    username = _unique_username("dupname")
    first, _ = _register(client, username=username, email=f"{username}1@example.com")
    assert first.status_code == 201

    second, _ = _register(client, username=username, email=f"{username}2@example.com")
    assert second.status_code == 400


def test_register_duplicate_email_returns_400(client):
    username = _unique_username("dupemail")
    email = f"{username}@example.com"
    first, _ = _register(client, username=f"{username}_a", email=email)
    assert first.status_code == 201

    second, _ = _register(client, username=f"{username}_b", email=email)
    assert second.status_code == 400


def test_login_success_returns_user_and_token(client):
    registration, payload = _register(client)
    assert registration.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["username"] == payload["username"]
    assert isinstance(data.get("token"), str) and len(data["token"]) > 10


def test_login_invalid_password_returns_401(client):
    registration, payload = _register(client)
    assert registration.status_code == 201

    response = client.post(
        "/api/auth/login",
        json={"username": payload["username"], "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_unknown_username_returns_401(client):
    response = client.post(
        "/api/auth/login",
        json={"username": f"unknown_{_unique_username('user')}", "password": "password123"},
    )
    assert response.status_code == 401


def test_login_without_json_body_returns_401(client):
    response = client.post("/api/auth/login")
    assert response.status_code == 401
