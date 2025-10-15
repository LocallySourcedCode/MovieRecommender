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


def test_veto_requires_enabled(test_client):
    code, t1, _ = make_group_with_two_guests(test_client)
    # Create a current candidate
    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(t1))
    assert cur.status_code == 200

    # Veto not enabled -> 409
    v = test_client.post(f"/groups/{code}/veto/use", headers=auth_header(t1))
    assert v.status_code == 409


def test_veto_disqualifies_and_advances_once(test_client, db_session):
    code, t1, t2 = make_group_with_two_guests(test_client)

    # Enable veto mode directly in DB for this test
    group = db_session.exec(select(Group).where(Group.code == code)).first()
    group.veto_enabled = True
    db_session.add(group)
    db_session.commit()

    cur = test_client.get(f"/groups/{code}/movies/current", headers=auth_header(t1))
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
