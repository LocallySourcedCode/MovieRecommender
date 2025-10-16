import json
import pytest
from sqlmodel import select

from app.models import Group, GenreFinalized, MovieCandidate


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_movie(id_base: int, title: str, genre_ids: list[int], vote_average: float = 7.0, vote_count: int = 500, popularity: float = 10.0):
    return {
        "id": id_base,
        "title": title,
        "genre_ids": genre_ids,
        "vote_average": vote_average,
        "vote_count": vote_count,
        "popularity": popularity,
        "release_date": "2010-01-01",
        "poster_path": "/x.jpg",
        "overview": f"Overview for {title}",
    }


@pytest.mark.parametrize("genres", [("Comedy","Thriller")])
def test_queue_builds_100_and_includes_scary_movie(test_client, db_session, monkeypatch, genres):
    # Monkeypatch TMDb configured and discover/search
    import app.services.recommendations as rec

    monkeypatch.setattr(rec, "_tmdb_is_configured", lambda: True)

    # Build synthetic discover pages
    COMEDY = 35
    THRILLER = 53

    def fake_discover(genres_ids, provider_ids, page, vote_count_gte=100, monetization="flatrate|ads|free", sort_by="vote_average.desc"):
        # both
        if genres_ids == (COMEDY, THRILLER) or genres_ids == (THRILLER, COMEDY):
            # 12 both-genre items across pages
            base = (page - 1) * 5
            return [
                make_movie(1000 + base + i, f"Both {base+i}", [COMEDY, THRILLER], 8.0 - i*0.01, 1000 - i, 100 - i)
                for i in range(5)
            ] if page <= 3 else []
        # primary-only (Comedy)
        if genres_ids == (COMEDY,):
            base = (page - 1) * 20
            return [
                make_movie(2000 + base + i, f"Comedy {base+i}", [COMEDY], 7.5 - (i%10)*0.01, 800 - i, 90 - i)
                for i in range(20)
            ] if page <= 3 else []
        # secondary-only (Thriller)
        if genres_ids == (THRILLER,):
            base = (page - 1) * 20
            return [
                make_movie(3000 + base + i, f"Thriller {base+i}", [THRILLER], 7.4 - (i%10)*0.01, 700 - i, 80 - i)
                for i in range(20)
            ] if page <= 3 else []
        # unrestricted
        if genres_ids is None:
            base = (page - 1) * 20
            return [
                make_movie(4000 + base + i, f"Any {base+i}", [COMEDY], 7.0, 500, 50)
                for i in range(20)
            ] if page <= 2 else []
        return []

    monkeypatch.setattr(rec, "_discover_page", fake_discover)

    # Stub httpx.Client only for search scary movie
    class _Resp:
        def __init__(self, payload):
            self._payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return self._payload

    class FakeClient:
        def __init__(self, timeout=7.0):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def get(self, url, headers=None, params=None):
            if "/search/movie" in url:
                payload = {
                    "results": [
                        make_movie(9001, "Scary Movie", [COMEDY], 6.2, 10000, 60),
                        make_movie(9002, "Scary Movie 2", [COMEDY], 5.3, 8000, 55),
                        make_movie(9003, "Scary Movie 3", [COMEDY], 5.5, 7000, 50),
                    ]
                }
                return _Resp(payload)
            # default empty
            return _Resp({"results": []})

    monkeypatch.setattr(rec, "httpx", type("HX", (), {"Client": FakeClient}))

    # Create group as guest
    r = test_client.post("/groups", json={"display_name": "Host"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    code = r.json()["group"]["code"]

    # Finalize genres manually and move to movie_selection
    g: Group = db_session.exec(select(Group).where(Group.code == code)).first()
    db_session.add(GenreFinalized(group_id=g.id, genre=genres[0]))
    db_session.add(GenreFinalized(group_id=g.id, genre=genres[1]))
    g.phase = "movie_selection"
    db_session.add(g)
    db_session.commit()

    # First current fetch should seed the queue and return first candidate
    r2 = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
    assert r2.status_code == 200
    body = r2.json()
    assert body["status"] == "current"

    # Ensure we stored 100 candidates
    all_cands = db_session.exec(select(MovieCandidate).where(MovieCandidate.group_id == g.id)).all()
    assert len(all_cands) == 100

    # Parse tiers from metadata
    tiers = {"both": 0, "primary": 0, "secondary": 0, "seed": 0}
    scary_present = False
    for mc in all_cands:
        meta = json.loads(mc.metadata_json or "{}")
        reason = str(meta.get("reason", ""))
        if "tier=both" in reason:
            tiers["both"] += 1
        if "tier=primary" in reason:
            tiers["primary"] += 1
        if "tier=secondary" in reason:
            tiers["secondary"] += 1
        if "seed=scary_movie" in reason:
            tiers["seed"] += 1
        if "seed=scary_movie" in reason or mc.title.startswith("Scary Movie"):
            scary_present = True
    # Both bucket capped at 50; remainder split between primary/secondary after any seeds
    assert tiers["both"] <= 50
    assert tiers["primary"] + tiers["secondary"] == 100 - tiers["both"] - tiers["seed"]
    assert scary_present, "Expected Scary Movie franchise titles to be included in the queue"
