def test_member_only_endpoints_require_auth(test_client):
    # No Authorization header provided
    r1 = test_client.get(f"/groups/FAKE/progress")
    assert r1.status_code == 401

    r2 = test_client.get(f"/groups/FAKE/genres/nominations")
    assert r2.status_code == 401

    r3 = test_client.get(f"/groups/FAKE/genres/standings")
    assert r3.status_code == 401
