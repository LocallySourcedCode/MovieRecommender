import os
import pytest

from app.services import recommendations as rec


def test_tmdb_top2_genre_filter_single_genre(monkeypatch):
    # Pretend TMDb is configured
    monkeypatch.setenv("TMDB_API_KEY", "dummy")

    # Popular page returns items with genre_ids
    # - Wide Mix: Fantasy appears 3rd -> should be rejected for strict top-2 filtering
    # - FantasyTop: Fantasy is in top-2 -> should be accepted
    items_page1 = [
        {"id": 101, "title": "Wide Mix", "genre_ids": [28, 35, 14]},  # Action, Comedy, Fantasy (Fantasy 3rd)
        {"id": 102, "title": "FantasyTop", "genre_ids": [14, 12]},    # Fantasy, Adventure (both in top-2)
    ]
    monkeypatch.setattr(rec, "_fetch_popular_page", lambda page: items_page1 if page == 1 else [])
    # No provider restriction for this test
    monkeypatch.setattr(rec, "_fetch_movie_providers", lambda movie_id, region: [])

    out = rec.get_next_candidate(used_titles=set(), shared_providers=None, genres={"Fantasy"})
    assert out is not None
    assert out["title"] == "FantasyTop"


def test_tmdb_top2_genre_filter_two_genres(monkeypatch):
    # Pretend TMDb is configured
    monkeypatch.setenv("TMDB_API_KEY", "dummy")

    # Items where Adventure is 3rd in one candidate and top-2 in another
    items_page1 = [
        {"id": 201, "title": "AdventureThird", "genre_ids": [28, 53, 12]},  # Adventure 3rd -> reject
        {"id": 202, "title": "AdventureTop", "genre_ids": [12, 28]},       # Adventure top-2 -> accept
    ]
    monkeypatch.setattr(rec, "_fetch_popular_page", lambda page: items_page1 if page == 1 else [])
    monkeypatch.setattr(rec, "_fetch_movie_providers", lambda movie_id, region: [])

    out = rec.get_next_candidate(used_titles=set(), shared_providers=None, genres={"Fantasy", "Adventure"})
    assert out is not None
    assert out["title"] == "AdventureTop"
