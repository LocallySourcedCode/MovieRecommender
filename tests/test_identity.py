from app.security import parse_subject


def register(client, email="alice@example.com", password="supersecret"):
    return client.post("/auth/register", json={"email": email, "password": password})


def login(client, email="alice@example.com", password="supersecret"):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_whoami_user(test_client):
    r = register(test_client)
    assert r.status_code == 201
    r = login(test_client)
    assert r.status_code == 200
    token = r.json()["access_token"]

    who = test_client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert who.status_code == 200
    data = who.json()
    assert data["kind"] == "user"
    assert data["email"] == "alice@example.com"


def test_whoami_participant_guest_group(test_client):
    # Create a group as a guest
    r = test_client.post("/groups", json={"display_name": "HostGuest", "streaming_services": ["netflix"]})
    assert r.status_code == 200
    body = r.json()
    token = body["access_token"]

    who = test_client.get("/whoami", headers={"Authorization": f"Bearer {token}"})
    assert who.status_code == 200
    data = who.json()
    assert data["kind"] == "participant"
    assert data["display_name"] == "HostGuest"
    assert isinstance(data["group_id"], int)


def test_parse_subject_helper():
    assert parse_subject("5") == ("user", 5)
    assert parse_subject("participant:12") == ("participant", 12)
    kind, pid = parse_subject("weird:token")
    assert kind == "unknown" and pid is None
