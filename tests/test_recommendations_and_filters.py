from app.services.recommendations import get_next_demo_candidate


def test_recommendations_respect_used_titles_and_shared_providers():
    # Should return a netflix-compatible title first
    item = get_next_demo_candidate(used_titles=set(), shared_providers={"netflix"})
    assert item is not None
    assert "netflix" in [p.lower() for p in item.get("providers", [])]

    # If we mark it used, next should still be netflix-compatible until exhausted
    next_item = get_next_demo_candidate(used_titles={item["title"]}, shared_providers={"netflix"})
    assert next_item is not None
    assert "netflix" in [p.lower() for p in next_item.get("providers", [])]

    # Unknown provider should yield None
    none_item = get_next_demo_candidate(used_titles=set(), shared_providers={"disneyplus"})
    assert none_item is None


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_streaming_intersection_filters_candidates(test_client):
    # Host on netflix+hulu; guest on netflix -> intersection is netflix
    r = test_client.post("/groups", json={"display_name": "Host", "streaming_services": ["netflix", "hulu"]})
    assert r.status_code == 200
    code = r.json()["group"]["code"]
    token = r.json()["access_token"]

    j = test_client.post(f"/groups/{code}/join", json={"display_name": "G2", "streaming_services": ["netflix"]})
    assert j.status_code == 200

    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
    assert cur.status_code == 200
    cand = cur.json()["candidate"]
    providers = [p.lower() for p in cand.get("providers", [])]
    assert "netflix" in providers


def test_streaming_no_intersection_falls_back(test_client):
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
