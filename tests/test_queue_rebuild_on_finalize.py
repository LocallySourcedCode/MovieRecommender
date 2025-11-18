from sqlmodel import select
from app.models import Group, Participant, MovieCandidate, GenreFinalized


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_rebuild_queue_after_finalize_clears_demo_then_builds_queue(test_client, db_session, monkeypatch):
    # Create group as guest and fetch a movie before finalization to create a demo candidate
    r = test_client.post("/groups", json={"display_name": "Host"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    code = r.json()["group"]["code"]

    # Stub a pre-finalization candidate so the first fetch succeeds offline
    from app import main as app_main
    monkeypatch.setattr(app_main, "get_next_candidate", lambda used_titles, shared_providers=None, genres=None: {
        "title": "PreDemo", "source": "tmdb", "year": 1999, "description": "pre", "poster_url": None, "providers": [], "reason": "tmdb:unrestricted"
    }, raising=False)

    # First call creates a candidate via on-demand path (demo in tests)
    r0 = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
    assert r0.status_code == 200
    first_title = r0.json()["candidate"]["title"]
    # Persisted
    with db_session as s:
        group = s.exec(select(Group).where(Group.code == code)).first()
        assert group is not None
        cands = s.exec(select(MovieCandidate).where(MovieCandidate.group_id == group.id)).all()
        assert len(cands) >= 1

    # Simulate finalized genres (Comedy + Thriller) and phase movement
    with db_session as s:
        group = s.exec(select(Group).where(Group.code == code)).first()
        s.add(GenreFinalized(group_id=group.id, genre="Comedy"))
        s.add(GenreFinalized(group_id=group.id, genre="Thriller"))
        group.phase = "movie_selection"
        s.add(group)
        s.commit()

    # Monkeypatch queue builder to return a specific item so we can assert rebuild happened
    from app import main as app_main

    # Ensure server considers TMDb configured so purge+queue path runs
    monkeypatch.setenv("TMDB_READ_TOKEN", "test-token")

    def fake_queue(**kwargs):
        return [{
            "title": "Scary Movie",
            "source": "tmdb",
            "year": 2000,
            "description": "Parody",
            "poster_url": None,
            "providers": [],
            "reason": "tmdb:queue:tier=both",
        }]

    monkeypatch.setattr(app_main, "get_candidate_queue", fake_queue)

    # Now call current again; server should purge old candidates and build the queue
    r1 = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(token))
    assert r1.status_code == 200
    body = r1.json()
    assert body["status"] == "current"
    cand = body["candidate"]
    assert cand["title"] == "Scary Movie"

    # Ensure previous candidate list was cleared
    with db_session as s:
        group = s.exec(select(Group).where(Group.code == code)).first()
        cands = s.exec(select(MovieCandidate).where(MovieCandidate.group_id == group.id)).all()
        assert any(c.title == "Scary Movie" for c in cands)
        # Original first title should have been cleared
        assert not any(c.title == first_title and c.metadata_json for c in cands)
