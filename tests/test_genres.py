def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_group_with_two_guests(client):
    r = client.post("/groups", json={"display_name": "Host"})
    assert r.status_code == 200
    code = r.json()["group"]["code"]
    token1 = r.json()["access_token"]
    j = client.post(f"/groups/{code}/join", json={"display_name": "Guest2"})
    assert j.status_code == 200
    token2 = j.json().get("access_token")
    return code, token1, token2


def test_nominate_limits_and_listing(test_client):
    code, t1, _ = make_group_with_two_guests(test_client)

    # Nominate two genres
    n1 = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t1), json={"genres": ["Action", "Comedy"]})
    assert n1.status_code == 200
    body = n1.json()
    assert body["ok"] is True
    tally = {row["genre"]: row["count"] for row in body["nominations"]}
    assert tally.get("Action") == 1
    assert tally.get("Comedy") == 1

    # Third nomination should fail due to per-participant limit (2)
    n2 = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t1), json={"genres": ["Drama"]})
    assert n2.status_code == 409

    # Listing shows allowed and current nominations
    lst = test_client.get(f"/groups/{code}/genres/nominations", headers=auth_header(t1))
    assert lst.status_code == 200
    data = lst.json()
    assert "allowed" in data and isinstance(data["allowed"], list)
    tally2 = {row["genre"]: row["count"] for row in data["nominations"]}
    assert tally2.get("Action") == 1 and tally2.get("Comedy") == 1


def test_vote_limits_and_validation(test_client):
    code, t1, t2 = make_group_with_two_guests(test_client)

    # Create some nominations from both participants
    r1 = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t1), json={"genres": ["Action", "Comedy"]})
    assert r1.status_code == 200
    r2 = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t2), json={"genres": ["Drama", "Horror"]})
    assert r2.status_code == 200

    # Invalid genre should 400
    bad = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "NotAGenre"})
    assert bad.status_code == 400

    # Non-nominated valid genre should 400 (e.g., Sci-Fi not nominated yet)
    non_nom = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Sci-Fi"})
    assert non_nom.status_code == 400

    # Vote up to 3 times across nominated genres
    v1 = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Action"})
    assert v1.status_code == 200
    v2 = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Comedy"})
    assert v2.status_code == 200
    v3 = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Drama"})
    assert v3.status_code == 200

    # 4th vote should hit limit
    v4 = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Horror"})
    assert v4.status_code == 409

    # Duplicate vote for same genre should be idempotent (still 200)
    vdup = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Action"})
    assert vdup.status_code == 200
