import pytest


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_guest_group(client) -> tuple[str, str]:
    r = client.post("/groups", json={"display_name": "Host"})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["group"]["code"], data["access_token"]


from app import main as app_main

def test_many_rejections_never_404_or_stall(test_client, monkeypatch):
    # Stub single-pick recommender to return a long sequence of distinct titles
    seq = {"i": 0}
    def fake_next(used_titles, shared_providers=None, genres=None):
        for _ in range(100):
            seq["i"] += 1
            t = f"X{seq['i']}"
            if t not in (used_titles or set()):
                return {"title": t, "year": 2000 + seq["i"], "description": t, "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"}
        return None
    monkeypatch.setattr(app_main, "get_next_candidate", fake_next, raising=False)

    code, token = _create_guest_group(test_client)

    # Perform a series of rejections larger than a small catalog
    for i in range(15):
        cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
        assert cur.status_code == 200, cur.text
        # Reject the current movie
        v = test_client.post(
            f"/groups/{code}/movies/vote",
            headers=auth_header(token),
            json={"accept": False},
        )
        assert v.status_code == 200, v.text
        js = v.json()
        assert js.get("status") in {"current", "pending", "finalized"}

    # After many cycles, we should still be able to get a current candidate
    last = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
    assert last.status_code == 200, last.text
    data = last.json()
    assert data.get("status") == "current"
    assert isinstance(data.get("candidate"), dict)
