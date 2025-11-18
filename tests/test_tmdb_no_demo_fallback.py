import types
from app.services import recommendations as rec


def test_get_next_candidate_avoids_demo_when_tmdb_configured(monkeypatch):
    # Force TMDb configured
    monkeypatch.setattr(rec, "_tmdb_is_configured", lambda: True)

    calls = {"n": 0}

    def fake_tmdb(used_titles, shared_providers=None, genres=None):
        calls["n"] += 1
        # 1st call (strict with genres) returns None
        # 2nd call (unrestricted with used/shared) returns an item
        # Subsequent calls shouldn't be needed
        if calls["n"] == 2:
            return {
                "title": "Some TMDb Pick",
                "year": 2001,
                "description": "",
                "poster_url": None,
                "providers": [],
                "reason": "tmdb:unrestricted",
            }
        return None

    monkeypatch.setattr(rec, "_get_next_tmdb_candidate", fake_tmdb)

    # Ensure demo path would have returned a known demo item if called
    # but our logic should return the TMDb pick instead
    used = set()
    item = rec.get_next_candidate(used_titles=used, shared_providers=None, genres={"Comedy", "Thriller"})
    assert item is not None
    assert item.get("title") == "Some TMDb Pick"
    assert item.get("reason", "").startswith("tmdb")
