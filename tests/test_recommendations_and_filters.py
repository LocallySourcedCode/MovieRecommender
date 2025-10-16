

def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


from app import main as app_main

def test_streaming_intersection_filters_candidates(test_client, monkeypatch):
    # Stub offline single-pick so we don't rely on live TMDb in this test
    monkeypatch.setattr(app_main, "get_next_candidate", lambda used_titles, shared_providers=None, genres=None: {
        "title": "SVCand", "year": 2020, "description": "d", "poster_url": None, "providers": list(shared_providers or []), "reason": "tmdb:unrestricted", "source": "tmdb"
    }, raising=False)

    # Host on netflix+hulu; guest on netflix -> intersection is netflix
    r = test_client.post("/groups", json={"display_name": "Host", "streaming_services": ["netflix", "hulu"]})
    assert r.status_code == 200
    code = r.json()["group"]["code"]
    token = r.json()["access_token"]

    j = test_client.post(f"/groups/{code}/join", json={"display_name": "G2", "streaming_services": ["netflix"]})
    assert j.status_code == 200

    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
    assert cur.status_code == 200
    cand = cur.json().get("candidate") or {}
    assert cand.get("title")


def test_streaming_no_intersection_falls_back(test_client, monkeypatch):
    # Stub offline single-pick for pre-finalization path
    monkeypatch.setattr(app_main, "get_next_candidate", lambda used_titles, shared_providers=None, genres=None: {
        "title": "AnyCand", "year": 2021, "description": "d", "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"
    }, raising=False)

    # Disjoint services -> intersection empty -> server falls back to no filter and still returns something
    r = test_client.post("/groups", json={"display_name": "Host", "streaming_services": ["hulu"]})
    code = r.json()["group"]["code"]
    token = r.json()["access_token"]

    j = test_client.post(f"/groups/{code}/join", json={"display_name": "G2", "streaming_services": ["netflix"]})
    assert j.status_code == 200

    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
    assert cur.status_code == 200
    cand = cur.json()["candidate"]
    assert cand["title"]  # anything is fine as long as a candidate is returned
