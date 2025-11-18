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


from app import main as app_main


def test_current_candidate_and_finalize_accept(test_client, monkeypatch):
    # Stub single-pick recommender so /movies/current works pre-finalization in offline tests
    seq = {"i": 0}
    def fake_next(used_titles, shared_providers=None, genres=None):
        seq["i"] += 1
        t = f"S{seq['i']}"
        if t in (used_titles or set()):
            return None
        return {"title": t, "year": 2000 + seq["i"], "description": t, "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"}
    monkeypatch.setattr(app_main, "get_next_candidate", fake_next, raising=False)

    code, t1, t2 = make_group_with_two_guests(test_client)

    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(t1))
    assert cur.status_code == 200
    cand = cur.json()["candidate"]
    assert cand["title"]

    # First accept should be pending (2 participants -> need 2 yes)
    v1 = test_client.post(f"/groups/{code}/movies/vote", headers=auth_header(t1), json={"accept": True})
    assert v1.status_code == 200
    assert v1.json()["status"] == "pending"

    # Second accept finalizes
    v2 = test_client.post(f"/groups/{code}/movies/vote", headers=auth_header(t2), json={"accept": True})
    assert v2.status_code == 200
    body = v2.json()
    assert body["status"] == "finalized"
    assert body["winner"]["title"] == cand["title"]


def test_reject_moves_to_next_candidate(test_client, monkeypatch):
    seq = {"i": 0}
    def fake_next(used_titles, shared_providers=None, genres=None):
        seq["i"] += 1
        t = f"R{seq['i']}"
        if t in (used_titles or set()):
            return None
        return {"title": t, "year": 1990 + seq["i"], "description": t, "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"}
    monkeypatch.setattr(app_main, "get_next_candidate", fake_next, raising=False)

    code, t1, t2 = make_group_with_two_guests(test_client)
    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(t1))
    assert cur.status_code == 200
    cand1 = cur.json()["candidate"]

    # Both reject -> should move to next candidate and return new current
    v1 = test_client.post(f"/groups/{code}/movies/vote", headers=auth_header(t1), json={"accept": False})
    assert v1.status_code == 200
    v2 = test_client.post(f"/groups/{code}/movies/vote", headers=auth_header(t2), json={"accept": False})
    assert v2.status_code == 200
    body = v2.json()
    assert body["status"] == "current"
    cand2 = body["candidate"]
    assert cand2["title"] != cand1["title"]
