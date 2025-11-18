from fastapi.testclient import TestClient
from sqlmodel import select
from app.models import Group


def create_guest_group(client: TestClient, display_name="Host"):
    r = client.post("/groups", json={"display_name": display_name})
    assert r.status_code == 200
    data = r.json()
    token = data["access_token"]
    code = data["group"]["code"]
    return token, code


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_refresh_returns_same_current_no_404(test_client: TestClient, monkeypatch):
    # Ensure TMDb path is used by providing a fake queue
    from app import main as app_main
    monkeypatch.setenv("TMDB_READ_TOKEN", "test-token")
    monkeypatch.setattr(app_main, "get_candidate_queue", lambda **kwargs: [
        {"title": "Q1", "source": "tmdb", "year": 2001, "description": "d1", "poster_url": None, "providers": [], "reason": "tmdb:queue:tier=both"}
    ])

    token, code = create_guest_group(test_client)
    # Single participant: nominate two genres to auto-finalize and enter movie_selection
    r = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_headers(token), json={"genres": ["Action", "Adventure"]})
    assert r.status_code == 200

    # First fetch current
    r1 = test_client.get(f"/groups/{code}/movies/current", headers=auth_headers(token))
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1.get("status") in ("current", "finalized")
    cand1 = data1.get("candidate") or data1.get("winner")
    assert cand1 and "id" in cand1

    # Refresh should return the same current (and not 404)
    r2 = test_client.get(f"/groups/{code}/movies/current", headers=auth_headers(token))
    assert r2.status_code == 200
    data2 = r2.json()
    cand2 = data2.get("candidate") or data2.get("winner")
    assert cand2 and "id" in cand2
    # If not finalized, current id should match
    if data1.get("status") == "current" and data2.get("status") == "current":
        assert cand1["id"] == cand2["id"]


def test_veto_returns_next_candidate_no_404(test_client: TestClient, db_session, monkeypatch):
    from app import main as app_main
    monkeypatch.setenv("TMDB_READ_TOKEN", "test-token")
    # Provide two queue items so veto advances to the next
    monkeypatch.setattr(app_main, "get_candidate_queue", lambda **kwargs: [
        {"title": "Q1", "source": "tmdb", "year": 2001, "description": "d1", "poster_url": None, "providers": [], "reason": "tmdb:queue:tier=both"},
        {"title": "Q2", "source": "tmdb", "year": 2002, "description": "d2", "poster_url": None, "providers": [], "reason": "tmdb:queue:tier=primary"},
    ])

    token, code = create_guest_group(test_client)
    # Enable veto for this group directly
    group = db_session.exec(select(Group).where(Group.code == code)).first()
    group.veto_enabled = True
    db_session.add(group)
    db_session.commit()

    # Enter movie_selection by nominating (single participant auto-finalizes)
    r = test_client.post(f"/groups/{code}/genres/nominate", headers=auth_headers(token), json={"genres": ["Drama", "Mystery"]})
    assert r.status_code == 200

    # Fetch current and keep its id
    r1 = test_client.get(f"/groups/{code}/movies/current", headers=auth_headers(token))
    assert r1.status_code == 200
    cand1 = (r1.json().get("candidate") or {})
    first_id = cand1.get("id")

    # Use veto -> should return a new current (or at least not 404)
    r2 = test_client.post(f"/groups/{code}/veto/use", headers=auth_headers(token))
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2.get("status") in ("current", "finalized")
    cand2 = data2.get("candidate") or data2.get("winner")
    assert cand2 and "id" in cand2
    if first_id is not None and data2.get("status") == "current":
        assert cand2["id"] != first_id
