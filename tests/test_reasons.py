import pytest
from sqlmodel import select

from app.models import Group, GenreFinalized


def _create_guest_group(client):
    r = client.post("/groups", json={"display_name": "tester"})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["group"]["code"], data["access_token"]


def _finalize(db_session, code: str, genres: list[str]):
    group = db_session.exec(select(Group).where(Group.code == code)).first()
    assert group is not None
    # clear old finals
    for old in db_session.exec(select(GenreFinalized).where(GenreFinalized.group_id == group.id)).all():
        db_session.delete(old)
    for g in genres:
        db_session.add(GenreFinalized(group_id=group.id, genre=g))
    group.phase = "movie_selection"
    db_session.add(group)
    db_session.commit()


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_tmdb_is_used_first_and_returns_candidate(test_client, db_session, monkeypatch):
    # Ensure TMDb path is active
    from app import main as app_main
    monkeypatch.setenv("TMDB_READ_TOKEN", "test-token")
    monkeypatch.setattr(app_main, "get_candidate_queue", lambda **kwargs: [
        {"title": "T1", "source": "tmdb", "year": 2001, "description": "d1", "poster_url": None, "providers": [], "reason": "tmdb:queue:tier=primary"}
    ])

    code, token = _create_guest_group(test_client)
    _finalize(db_session, code, ["Comedy"])  # any single genre

    r = test_client.get(f"/groups/{code}/movies/current", headers=auth(token))
    assert r.status_code == 200, r.text
    cand = r.json()["candidate"]
    assert cand.get("source") == "tmdb"


def test_reason_indicates_genre_match_when_available(test_client, db_session, monkeypatch):
    from app import main as app_main
    monkeypatch.setenv("TMDB_READ_TOKEN", "test-token")
    monkeypatch.setattr(app_main, "get_candidate_queue", lambda **kwargs: [
        {"title": "T2", "source": "tmdb", "year": 2002, "description": "d2", "poster_url": None, "providers": [], "reason": "tmdb:queue:tier=primary"}
    ])

    code, token = _create_guest_group(test_client)
    _finalize(db_session, code, ["Drama"])  # TMDb-backed candidate

    r = test_client.get(f"/groups/{code}/movies/current", headers=auth(token))
    assert r.status_code == 200, r.text
    cand = r.json()["candidate"]
    assert cand.get("source") == "tmdb"