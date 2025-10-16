import os
import types
from app.services import recommendations as rec


def make_movie(id, title, genre_ids, vote_average, vote_count=1000, popularity=100.0, poster_path="/x.jpg", overview="desc"):
    return {
        "id": id,
        "title": title,
        "genre_ids": genre_ids,
        "vote_average": vote_average,
        "vote_count": vote_count,
        "popularity": popularity,
        "poster_path": poster_path,
        "overview": overview,
    }


def test_tmdb_tiered_both_then_primary_then_secondary(monkeypatch):
    # Force TMDb path
    monkeypatch.setenv("TMDB_READ_TOKEN", "dummy")
    monkeypatch.setattr(rec, "_tmdb_is_configured", lambda: True)

    movies = [
        # Secondary-only (Adventure as secondary)
        make_movie(1, "OnlySecondaryHigh", [28, 12], 8.7, 900, 300),  # Adventure=12 in top-2 but not Fantasy=14
        # Primary-only but higher rated than both-tier candidate
        make_movie(2, "PrimaryHigher", [14, 18], 9.1, 1000, 500),  # Fantasy=14 in top-2
        # Both present anywhere (Fantasy+Adventure), one in top-2
        make_movie(3, "BothCandidate", [14, 12, 35], 8.9, 2000, 800),
    ]

    def fake_popular(page: int):
        return movies if page == 1 else []

    monkeypatch.setattr(rec, "_fetch_popular_page", fake_popular)
    monkeypatch.setattr(rec, "_fetch_movie_providers", lambda movie_id, region: [])

    # Order Fantasy (primary) then Adventure (secondary)
    item = rec.get_next_candidate(used_titles=set(), shared_providers=None, genres=["Fantasy", "Adventure"])
    assert item is not None
    # Despite PrimaryHigher having a higher rating, BothCandidate should win by tier priority
    assert item["title"] == "BothCandidate"

    # If we mark BothCandidate as used, primary tier should win next (PrimaryHigher)
    item2 = rec.get_next_candidate(used_titles={"BothCandidate"}, shared_providers=None, genres=["Fantasy", "Adventure"])
    assert item2 is not None
    assert item2["title"] == "PrimaryHigher"

    # If we also mark primary as used, secondary tier should be chosen (OnlySecondaryHigh)
    item3 = rec.get_next_candidate(used_titles={"BothCandidate", "PrimaryHigher"}, shared_providers=None, genres=["Fantasy", "Adventure"])
    assert item3 is not None
    assert item3["title"] == "OnlySecondaryHigh"


def test_tmdb_rating_sort_within_bucket(monkeypatch):
    monkeypatch.setenv("TMDB_READ_TOKEN", "dummy")
    monkeypatch.setattr(rec, "_tmdb_is_configured", lambda: True)

    movies = [
        make_movie(10, "P1", [14, 18], 7.5, 800, 200),  # Fantasy in top-2
        make_movie(11, "P2", [14, 28], 8.2, 500, 100),  # Fantasy in top-2, higher rating
        make_movie(12, "P3", [14, 35], 8.2, 1200, 50),  # tie on rating, higher vote_count
    ]

    def fake_popular(page: int):
        return movies if page == 1 else []

    monkeypatch.setattr(rec, "_fetch_popular_page", fake_popular)
    monkeypatch.setattr(rec, "_fetch_movie_providers", lambda movie_id, region: [])

    item = rec.get_next_candidate(used_titles=set(), shared_providers=None, genres=["Fantasy"])  # primary bucket
    assert item is not None
    # Should pick P3 because same vote_average as P2 but higher vote_count
    assert item["title"] == "P3"
