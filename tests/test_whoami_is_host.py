def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_whoami_includes_is_host_flag_for_creator(test_client):
    # Create a group as guest
    r = test_client.post("/groups", json={"display_name": "Creator"})
    assert r.status_code == 200
    tok = r.json()["access_token"]

    who = test_client.get("/whoami", headers=auth_header(tok))
    assert who.status_code == 200
    data = who.json()
    assert data.get("kind") == "participant"
    assert data.get("is_host") is True
