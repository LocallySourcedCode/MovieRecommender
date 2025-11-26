from sqlmodel import select
from app.models import GenreFinalized


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


def test_progress_flags_and_phase_transitions(test_client, db_session):
    code, t1, t2 = make_group_with_two_guests(test_client)

    # Initially: no nominations or votes
    p0 = test_client.get(f"/groups/{code}/progress", headers=auth_header(t1))
    assert p0.status_code == 200
    d0 = p0.json()
    assert d0["nominated_count"] == 0 and d0["voted_count"] == 0
    assert d0["phase"] == "lobby"

    # Start nomination phase
    test_client.post(f"/groups/{code}/start", headers=auth_header(t1))

    # Each nominates one -> phase should advance to genre_voting
    test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t1), json={"genres": ["Action"]})
    test_client.post(f"/groups/{code}/genres/nominate", headers=auth_header(t2), json={"genres": ["Comedy"]})

    p1 = test_client.get(f"/groups/{code}/progress", headers=auth_header(t1))
    d1 = p1.json()
    assert d1["all_nominated"] is True
    assert d1["phase"] == "genre_voting"

    # Each casts a vote -> finalize top2 and move to movie_selection
    test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t1), json={"genre": "Action"})
    test_client.post(f"/groups/{code}/genres/vote", headers=auth_header(t2), json={"genre": "Comedy"})

    p2 = test_client.get(f"/groups/{code}/progress", headers=auth_header(t1))
    d2 = p2.json()
    assert d2["all_voted"] is True
    assert d2["phase"] == "movie_selection"
    finals = d2.get("finalized_genres")
    assert set(finals) == {"Action", "Comedy"}

    # Database has finalized rows
    finals_db = db_session.exec(select(GenreFinalized)).all()
    assert any(f.genre in ("Action", "Comedy") for f in finals_db)


def test_progress_returns_is_host(test_client):
    # 1. Host creates group (User flow)
    import time
    email = f"h_{time.time()}@ex.com"
    password = "password123"
    r = test_client.post("/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, f"Register failed: {r.text}"
    
    r = test_client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    
    r = test_client.post("/groups", headers=auth_header(token))
    code = r.json()["group"]["code"]
    
    # Check Host Progress
    p1 = test_client.get(f"/groups/{code}/progress", headers=auth_header(token))
    assert p1.status_code == 200
    assert p1.json()["is_host"] is True

    # 2. Guest joins
    j = test_client.post(f"/groups/{code}/join", json={"display_name": "Guest"})
    g_token = j.json()["access_token"]
    
    # Check Guest Progress
    p2 = test_client.get(f"/groups/{code}/progress", headers=auth_header(g_token))
    assert p2.status_code == 200
    assert p2.json()["is_host"] is False
