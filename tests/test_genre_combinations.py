import itertools
import json
from typing import Iterable

import pytest
from sqlmodel import select

from app.main import ALLOWED_GENRES
from app.models import Group, GenreFinalized


def _create_guest_group(client) -> tuple[str, str]:
    r = client.post("/groups", json={"display_name": "tester"})
    assert r.status_code == 200, r.text
    data = r.json()
    code = data["group"]["code"]
    token = data.get("access_token")
    assert token, "expected access_token for guest group creation"
    return code, token


def _finalize_genres(db_session, code: str, genres: Iterable[str]):
    group = db_session.exec(select(Group).where(Group.code == code)).first()
    assert group is not None
    # Clear any existing finalized
    for old in db_session.exec(select(GenreFinalized).where(GenreFinalized.group_id == group.id)).all():
        db_session.delete(old)
    for g in genres:
        db_session.add(GenreFinalized(group_id=group.id, genre=g))
    group.phase = "movie_selection"
    db_session.add(group)
    db_session.commit()


@pytest.mark.parametrize("combo", [
    (g,) for g in ALLOWED_GENRES
] + list(itertools.combinations(ALLOWED_GENRES, 2)))
def test_all_genre_combinations_yield_candidate(test_client, db_session, combo, monkeypatch):
    # Stub queue builder to avoid live TMDb and ensure a candidate for any combo
    from app import main as app_main
    monkeypatch.setattr(app_main, "get_candidate_queue", lambda **kwargs: [
        {"title": "ComboPick", "source": "tmdb", "year": 2000, "description": "", "poster_url": None, "providers": [], "reason": "tmdb:queue:tier=primary"}
    ])

    code, token = _create_guest_group(test_client)
    _finalize_genres(db_session, code, combo)
    r = test_client.get(f"/groups/{code}/movies/current", headers={"Authorization": f"Bearer {token}"})
    # Endpoint should never 404 due to rare/no-match combinations
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "current"
    cand = data.get("candidate")
    assert isinstance(cand, dict)
    assert cand.get("title")
