from sqlmodel import select
from app.models import Group


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

def test_veto_requires_enabled(test_client, monkeypatch):
    # Stub single-pick so current candidate exists pre-finalization
    seq = {"i": 0}
    def fake_next(used_titles, shared_providers=None, genres=None):
        seq["i"] += 1
        t = f"V{seq['i']}"
        if t in (used_titles or set()):
            return None
        return {"title": t, "year": 2000 + seq["i"], "description": t, "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"}
    monkeypatch.setattr(app_main, "get_next_candidate", fake_next, raising=False)

    code, t1, _ = make_group_with_two_guests(test_client)
    # Create a current candidate
    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(t1))
    assert cur.status_code == 200

    # Veto not enabled -> 409
    v = test_client.post(f"/groups/{code}/veto/use", headers=auth_header(t1))
    assert v.status_code == 409


def test_veto_disqualifies_and_advances_once(test_client, db_session, monkeypatch):
    seq = {"i": 0}
    def fake_next(used_titles, shared_providers=None, genres=None):
        seq["i"] += 1
        t = f"W{seq['i']}"
        if t in (used_titles or set()):
            return None
        return {"title": t, "year": 1990 + seq["i"], "description": t, "poster_url": None, "providers": [], "reason": "tmdb:unrestricted", "source": "tmdb"}
    monkeypatch.setattr(app_main, "get_next_candidate", fake_next, raising=False)

    code, t1, t2 = make_group_with_two_guests(test_client)

    # Enable veto mode directly in DB for this test
    group = db_session.exec(select(Group).where(Group.code == code)).first()
    group.veto_enabled = True
    db_session.add(group)
    db_session.commit()

    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(t1))
    assert cur.status_code == 200
    cand1 = cur.json()["candidate"]

    # Use veto -> should advance to next
    v = test_client.post(f"/groups/{code}/veto/use", headers=auth_header(t1))
    assert v.status_code == 200
    body = v.json()
    assert body["status"] == "current"
    cand2 = body["candidate"]
    assert cand2["title"] != cand1["title"]

    # Same participant cannot veto again
    v2 = test_client.post(f"/groups/{code}/veto/use", headers=auth_header(t1))
    assert v2.status_code == 409
