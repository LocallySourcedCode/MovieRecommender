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

def test_movie_vote_upsert_and_pending_then_reject(test_client, db_session, monkeypatch):
    # Stub single-pick to work pre-finalization
    seq = {"i": 0}
    def fake_next(used_titles, shared_providers=None, genres=None):
        seq["i"] += 1
        t = f"U{seq['i']}"
        if t in (used_titles or set()):
            return None
        return {"title": t, "year": 2005 + seq["i"], "description": t, "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"}
    monkeypatch.setattr(app_main, "get_next_candidate", fake_next, raising=False)

    code, t1, t2 = make_group_with_two_guests(test_client)

    # Get current candidate
    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(t1))
    assert cur.status_code == 200
    cand = cur.json()["candidate"]

    # Same participant votes Yes then changes to No (upsert semantics) -> still pending until majority
    v1 = test_client.post(f"/groups/{code}/movies/vote", headers=auth_header(t1), json={"accept": True})
    assert v1.status_code == 200 and v1.json()["status"] == "pending"
    v1b = test_client.post(f"/groups/{code}/movies/vote", headers=auth_header(t1), json={"accept": False})
    assert v1b.status_code == 200 and v1b.json()["status"] == "pending"

    # Ensure only a single vote row exists for this participant (upsert) before the second participant votes
    from sqlmodel import select
    from app.models import MovieVote, Group

    group = db_session.exec(select(Group).where(Group.code == code)).first()
    votes = db_session.exec(select(MovieVote).where(MovieVote.group_id == group.id)).all()
    assert len(votes) == 1
    assert votes[0].movie_id is not None and votes[0].value == 0

    # Second participant votes No -> strict majority reject -> advances to a new current
    v2 = test_client.post(f"/groups/{code}/movies/vote", headers=auth_header(t2), json={"accept": False})
    assert v2.status_code == 200
    body = v2.json()
    assert body["status"] == "current"
    new_cand = body["candidate"]
    assert new_cand["title"] != cand["title"]
