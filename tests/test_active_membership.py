from sqlmodel import select
from app.models import Group, Participant


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_guest_cannot_create_second_group_without_leaving(test_client):
    # Create a group as guest to get participant token
    r1 = test_client.post("/groups", json={"display_name": "Host1"})
    assert r1.status_code == 200
    tok = r1.json()["access_token"]

    # Attempt to create another group while still having participant token -> 409
    r2 = test_client.post("/groups", headers=auth_header(tok), json={"display_name": "NewHost"})
    assert r2.status_code == 409
    detail = r2.json().get("detail")
    # detail may be string or dict; handle both
    if isinstance(detail, dict):
        assert detail.get("error") == "participant_in_active_group"
        assert detail.get("group_code") == r1.json()["group"]["code"]

    # Leave current group
    rleave = test_client.post("/groups/leave", headers=auth_header(tok))
    assert rleave.status_code == 200

    # Now create another group as guest (no auth header)
    r3 = test_client.post("/groups", json={"display_name": "Host2"})
    assert r3.status_code == 200
    assert r3.json()["group"]["code"] != r1.json()["group"]["code"]


def test_user_join_enforces_single_active_membership(test_client):
    # Make group A as guest for a code
    g1 = test_client.post("/groups", json={"display_name": "G1"}).json()["group"]["code"]

    # Register/login user
    reg = test_client.post("/auth/register", json={"email": "u@example.com", "password": "supersecret"})
    assert reg.status_code == 201
    token = test_client.post("/auth/login", data={"username": "u@example.com", "password": "supersecret"}).json()["access_token"]

    # Join group A as user
    j1 = test_client.post(f"/groups/{g1}/join", headers=auth_header(token))
    assert j1.status_code == 200

    # Make another group B
    g2 = test_client.post("/groups", json={"display_name": "G2"}).json()["group"]["code"]

    # Try to join B as same user -> 409
    j2 = test_client.post(f"/groups/{g2}/join", headers=auth_header(token))
    assert j2.status_code == 409

    # Leave current (group A)
    rleave = test_client.post("/groups/leave", headers=auth_header(token))
    assert rleave.status_code == 200

    # Now joining group B should work
    j3 = test_client.post(f"/groups/{g2}/join", headers=auth_header(token))
    assert j3.status_code == 200


def test_host_leave_disbands_group(test_client, db_session):
    # Create group as guest host and add another guest
    r = test_client.post("/groups", json={"display_name": "Host"})
    assert r.status_code == 200
    body = r.json()
    code = body["group"]["code"]
    host_tok = body["access_token"]
    j = test_client.post(f"/groups/{code}/join", json={"display_name": "G2"})
    assert j.status_code == 200

    # Disband as host
    rleave = test_client.post("/groups/leave", headers=auth_header(host_tok))
    assert rleave.status_code == 200
    assert rleave.json().get("action") == "disbanded"

    # Group should no longer exist in DB
    grp = db_session.exec(select(Group).where(Group.code == code)).first()
    assert grp is None

    # Joining by old code should return 404
    j2 = test_client.post(f"/groups/{code}/join", json={"display_name": "Late"})
    assert j2.status_code == 404
