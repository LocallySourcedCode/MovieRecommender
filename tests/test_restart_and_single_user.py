from sqlmodel import select
from app.models import Group, GenreFinalized, MovieCandidate, MovieVote, GenreNomination


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_single_user_auto_finalize(test_client, db_session):
    # Create single-participant group as guest
    r = test_client.post("/groups", json={"display_name": "Solo"})
    assert r.status_code == 200
    body = r.json()
    code = body["group"]["code"]
    tok = body["access_token"]

    # Nominate two genres
    n = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(tok), json={"genres": ["Action", "Comedy"]})
    assert n.status_code == 200

    # After nomination, backend should auto-finalize and move to movie_selection
    prog = test_client.get(f"/groups/{code}/progress", headers=auth_header(tok))
    assert prog.status_code == 200
    p = prog.json()
    assert p["phase"] == "movie_selection"
    final = p.get("finalized_genres")
    assert set(final) == {"Action", "Comedy"}


from app import main as app_main

def test_reset_genres_resets_all(test_client, db_session, monkeypatch):
    # Create group with two guests
    r = test_client.post("/groups", json={"display_name": "Host"})
    assert r.status_code == 200
    code = r.json()["group"]["code"]
    host_tok = r.json()["access_token"]
    j = test_client.post(f"/groups/{code}/join", json={"display_name": "G2"})
    assert j.status_code == 200
    g2_tok = j.json().get("access_token")

    # Nominate and vote to progress to movie_selection
    test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(host_tok), json={"genres": ["Action", "Comedy"]})
    test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(g2_tok), json={"genres": ["Drama", "Horror"]})
    test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(host_tok), json={"genre": "Action"})
    test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(g2_tok), json={"genre": "Action"})

    # Force a current movie candidate (stub single-pick in case queue is empty offline)
    monkeypatch.setattr(app_main, "get_next_candidate", lambda used_titles, shared_providers=None, genres=None: {
        "title": "RST1", "year": 2001, "description": "d", "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"
    }, raising=False)
    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(host_tok))
    assert cur.status_code == 200

    # Call reset as host
    rreset = test_client.post(f"/groups/{code}/genres/reset", headers=auth_header(host_tok))
    assert rreset.status_code == 200
    assert rreset.json().get("phase") == "genre_nomination"

    # DB should have no finalized genres, no nominations, no movie votes/candidates
    group = db_session.exec(select(Group).where(Group.code == code)).first()
    assert group.phase == "genre_nomination"
    assert group.current_movie_id is None and group.winner_movie_id is None

    finals = db_session.exec(select(GenreFinalized).where(GenreFinalized.group_id == group.id)).all()
    assert finals == []
    noms = db_session.exec(select(GenreNomination).where(GenreNomination.group_id == group.id)).all()
    assert noms == []
    mvs = db_session.exec(select(MovieVote).where(MovieVote.group_id == group.id)).all()
    assert mvs == []
    mcs = db_session.exec(select(MovieCandidate).where(MovieCandidate.group_id == group.id)).all()
    assert mcs == []
