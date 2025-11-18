def register(client, email="host@example.com", password="supersecret"):
    return client.post("/auth/register", json={"email": email, "password": password})


def login(client, email="host@example.com", password="supersecret"):
    return client.post("/auth/login", data={"username": email, "password": password})


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_group_as_user_and_host_participant(test_client):
    assert register(test_client).status_code == 201
    r = login(test_client)
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = test_client.post("/groups", headers=auth_header(token))
    assert r.status_code == 200
    body = r.json()
    group = body["group"]
    assert group["code"] and isinstance(group["code"], str)
    # host participant should exist
    participants = group["participants"]
    assert len(participants) == 1
    host = participants[0]
    assert host["is_host"] is True
    assert host["display_name"] == "host"
    # user flow should not return a token in response
    assert body.get("access_token") in (None, "")


def test_create_group_as_guest_returns_token(test_client):
    r = test_client.post("/groups", json={"display_name": "GHost", "streaming_services": ["netflix", "hulu"]})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and body["access_token"]
    group = body["group"]
    assert group["participants"][0]["is_host"] is True
    assert group["participants"][0]["display_name"] == "GHost"


def test_join_group_as_guest_and_user_idempotent(test_client):
    # Create as guest to get code
    r = test_client.post("/groups", json={"display_name": "Host"})
    code = r.json()["group"]["code"]

    # Guest join
    j1 = test_client.post(f"/groups/{code}/join", json={"display_name": "Guest1"})
    assert j1.status_code == 200
    g1 = j1.json()["group"]
    assert len(g1["participants"]) == 2

    # Register a user and join
    register(test_client, email="u1@example.com")
    token = login(test_client, email="u1@example.com").json()["access_token"]
    j2 = test_client.post(f"/groups/{code}/join", headers=auth_header(token))
    assert j2.status_code == 200
    g2 = j2.json()["group"]
    assert len(g2["participants"]) == 3

    # Join again as same user should be idempotent
    j3 = test_client.post(f"/groups/{code}/join", headers=auth_header(token))
    assert j3.status_code == 200
    g3 = j3.json()["group"]
    assert len(g3["participants"]) == 3


def test_participant_token_cannot_join_other_group(test_client):
    # Make two groups, collect tokens
    r1 = test_client.post("/groups", json={"display_name": "Host1"})
    code1 = r1.json()["group"]["code"]
    token1 = r1.json()["access_token"]

    r2 = test_client.post("/groups", json={"display_name": "Host2"})
    code2 = r2.json()["group"]["code"]

    # Try to use participant token from group1 to join group2
    j = test_client.post(f"/groups/{code2}/join", headers=auth_header(token1))
    assert j.status_code == 403
