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


def test_genre_standings_and_leader(test_client):
    code, t1, t2 = make_group_with_two_guests(test_client)

    # Nominate 3 genres total across users
    n1 = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t1), json={"genres": ["Action", "Comedy"]})
    assert n1.status_code == 200
    n2 = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t2), json={"genres": ["Drama"]})
    assert n2.status_code == 200

    # Cast votes: Action gets 2, Comedy gets 1
    v1 = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Action"})
    assert v1.status_code == 200
    v2 = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t2), json={"genre": "Action"})
    assert v2.status_code == 200
    v3 = test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Comedy"})
    assert v3.status_code == 200

    st = test_client.get(f"/groups/{code}/genres/standings", headers=auth_header(t1))
    assert st.status_code == 200
    body = st.json()
    standings = {row["genre"]: row["votes"] for row in body["standings"]}
    assert standings.get("Action") == 2
    assert body["leader"] == "Action"
    assert any(r["genre"] == "Action" for r in body["nominations"])  # nominations included


def test_genres_reset_host_only(test_client):
    code, t1, t2 = make_group_with_two_guests(test_client)

    # Nominate and vote
    test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t1), json={"genres": ["Action", "Comedy"]})
    test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t2), json={"genre": "Action"})

    # Non-host cannot reset
    bad = test_client.post(f"/groups/{code}/genres/reset", headers=auth_header(t2))
    assert bad.status_code == 403

    # Host can reset
    ok = test_client.post(f"/groups/{code}/genres/reset", headers=auth_header(t1))
    assert ok.status_code == 200

    # After reset, standings and nominations should be empty
    st = test_client.get(f"/groups/{code}/genres/standings", headers=auth_header(t1))
    assert st.status_code == 200
    body = st.json()
    assert body["standings"] == []
    assert body["nominations"] == []
