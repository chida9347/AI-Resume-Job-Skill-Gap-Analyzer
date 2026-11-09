"""Authentication, session rotation and account lifecycle."""

from __future__ import annotations


class TestRegistrationAndLogin:
    def test_register_returns_token_pair_and_public_user(self, client):
        response = client.post(
            "/auth/register",
            json={"email": "avery@example.com", "password": "StrongPass1!", "full_name": "Avery Chen"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["user"]["email"] == "avery@example.com"
        assert body["user"]["full_name"] == "Avery Chen"
        assert "password" not in body["user"]

    def test_email_is_normalised_and_duplicates_rejected(self, client):
        payload = {"email": "  Avery@Example.COM ", "password": "StrongPass1!"}
        assert client.post("/auth/register", json=payload).status_code == 201
        duplicate = client.post("/auth/register", json=payload)
        assert duplicate.status_code == 409
        assert "already exists" in duplicate.json()["detail"]

    def test_invalid_email_and_weak_password_are_validation_errors(self, client):
        response = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "password"},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["detail"]
        assert body["error"]["code"] == "validation_error"

    def test_login_and_me(self, client, register):
        headers, body = register()
        me = client.get("/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["id"] == body["user"]["id"]

        login = client.post(
            "/auth/login",
            json={"email": "avery@example.com", "password": "StrongPass1!"},
        )
        assert login.status_code == 200
        assert login.json()["access_token"]

    def test_wrong_password_is_rejected(self, client, register):
        register()
        response = client.post(
            "/auth/login",
            json={"email": "avery@example.com", "password": "WrongPass1!"},
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_unauthenticated_me_is_401(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert response.json()["detail"]


class TestTokenRotation:
    def test_refresh_rotates_and_rejects_replay(self, client, register):
        _, body = register()
        first = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]})
        assert first.status_code == 200
        new_tokens = first.json()
        assert new_tokens["refresh_token"] != body["refresh_token"]

        replay = client.post("/auth/refresh", json={"refresh_token": body["refresh_token"]})
        assert replay.status_code == 401
        assert "invalid or expired" in replay.json()["detail"]

    def test_logout_revokes_refresh_token(self, client, register):
        headers, body = register()
        logout = client.post(
            "/auth/logout",
            headers=headers,
            json={"refresh_token": body["refresh_token"]},
        )
        assert logout.status_code == 200
        assert logout.json()["status"] == "signed_out"
        assert client.post(
            "/auth/refresh", json={"refresh_token": body["refresh_token"]}
        ).status_code == 401


class TestProfileAndPassword:
    def test_profile_can_be_updated(self, client, register):
        headers, _ = register()
        response = client.patch(
            "/auth/me",
            headers=headers,
            json={"full_name": "Avery C.", "headline": "Backend engineer"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Avery C."
        assert response.json()["headline"] == "Backend engineer"

    def test_change_password_revokes_sessions(self, client, register):
        headers, body = register()
        changed = client.post(
            "/auth/change-password",
            headers=headers,
            json={"current_password": "StrongPass1!", "new_password": "NewStrongPass2!"},
        )
        assert changed.status_code == 200
        assert changed.json()["status"] == "password_changed"
        assert client.post(
            "/auth/refresh", json={"refresh_token": body["refresh_token"]}
        ).status_code == 401
        assert client.post(
            "/auth/login",
            json={"email": "avery@example.com", "password": "StrongPass1!"},
        ).status_code == 401
        assert client.post(
            "/auth/login",
            json={"email": "avery@example.com", "password": "NewStrongPass2!"},
        ).status_code == 200

    def test_change_password_requires_current_password(self, client, register):
        headers, _ = register()
        response = client.post(
            "/auth/change-password",
            headers=headers,
            json={"current_password": "wrong", "new_password": "NewStrongPass2!"},
        )
        assert response.status_code == 400


class TestAccountDeletion:
    def test_delete_requires_password_and_removes_access(self, client, register):
        headers, _ = register()
        wrong = client.request("DELETE", "/auth/me", headers=headers, json={"password": "wrong"})
        assert wrong.status_code == 400

        deleted = client.request(
            "DELETE", "/auth/me", headers=headers, json={"password": "StrongPass1!"}
        )
        assert deleted.status_code == 200
        assert deleted.json()["status"] == "account_deleted"
        assert client.get("/auth/me", headers=headers).status_code == 401
        assert client.post(
            "/auth/login",
            json={"email": "avery@example.com", "password": "StrongPass1!"},
        ).status_code == 401
