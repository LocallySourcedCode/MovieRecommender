from typing import List, Dict, Optional, Set

# Demo catalog for offline development. In production, swap to TMDb via a feature flag.
# Each item includes: title, year, description, poster_url, providers (list[str]), rotten_tomatoes (0-100)
_DEMO_CATALOG: List[Dict] = [
    {
        "title": "Inception",
        "year": 2010,
        "description": "A thief who steals corporate secrets through dream-sharing technology is given an inverse task.",
        "poster_url": "https://image.tmdb.org/t/p/w342/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg",
        "providers": ["netflix", "amazon"],
        "rotten_tomatoes": 87,
    },
    {
        "title": "The Social Network",
        "year": 2010,
        "description": "The founding of Facebook and the resulting lawsuits.",
        "poster_url": "https://image.tmdb.org/t/p/w342/n0ybibhJtQ5icDqTp8eRytcIHJx.jpg",
        "providers": ["netflix", "hulu"],
        "rotten_tomatoes": 96,
    },
    {
        "title": "Mad Max: Fury Road",
        "year": 2015,
        "description": "In a post-apocalyptic wasteland, Max teams up with Furiosa to flee a cult leader.",
        "poster_url": "https://image.tmdb.org/t/p/w342/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg",
        "providers": ["hbo", "amazon"],
        "rotten_tomatoes": 97,
    },
    {
        "title": "Parasite",
        "year": 2019,
        "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "poster_url": "https://image.tmdb.org/t/p/w342/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "providers": ["hulu"],
        "rotten_tomatoes": 99,
    },
    {
        "title": "Knives Out",
        "year": 2019,
        "description": "A modern whodunit where a detective investigates the death of a patriarch of an eccentric, combative family.",
        "poster_url": "https://image.tmdb.org/t/p/w342/pThyQovXQrw2m0s9x82twj48Jq4.jpg",
        "providers": ["amazon", "netflix"],
        "rotten_tomatoes": 97,
    },
    {
        "title": "Spider-Man: Into the Spider-Verse",
        "year": 2018,
        "description": "Teen Miles Morales becomes Spider-Man and joins other Spider-People from other dimensions.",
        "poster_url": "https://image.tmdb.org/t/p/w342/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
        "providers": ["netflix"],
        "rotten_tomatoes": 97,
    },
]


def _matches_shared_providers(item: Dict, shared_providers: Optional[Set[str]]) -> bool:
    if not shared_providers:
        return True
    providers = set(map(str.lower, item.get("providers", [])))
    return len(providers.intersection(shared_providers)) > 0


def get_next_demo_candidate(
    used_titles: Set[str],
    shared_providers: Optional[Set[str]] = None,
) -> Optional[Dict]:
    """Return the next candidate dict not in used_titles and compatible with shared providers.

    Returns None if the demo catalog is exhausted under the constraints.
    """
    for item in _DEMO_CATALOG:
        if item["title"] in used_titles:
            continue
        if _matches_shared_providers(item, shared_providers):
            return item
    return None

# The functions in this module provide movie recommendations for the app.
# By default we use a small in-process demo catalog that requires no external APIs (used by tests).
# Optionally, if TMDB_READ_TOKEN (v4) or TMDB_API_KEY (v3) is set in the environment, we will fetch
# candidates from TMDb and map them into the same structure. On any error, we fall back to the demo data.

from typing import List, Dict, Optional, Set
import os
import httpx

# Demo catalog for offline development. In production, swap to TMDb via a feature flag.
# Each item includes: title, year, description, poster_url, providers (list[str]), rotten_tomatoes (0-100)
_DEMO_CATALOG: List[Dict] = [
    {
        "title": "Inception",
        "year": 2010,
        "description": "A thief who steals corporate secrets through dream-sharing technology is given an inverse task.",
        "poster_url": "https://image.tmdb.org/t/p/w342/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg",
        "providers": ["netflix", "amazon"],
        "rotten_tomatoes": 87,
    },
    {
        "title": "The Social Network",
        "year": 2010,
        "description": "The founding of Facebook and the resulting lawsuits.",
        "poster_url": "https://image.tmdb.org/t/p/w342/n0ybibhJtQ5icDqTp8eRytcIHJx.jpg",
        "providers": ["netflix", "hulu"],
        "rotten_tomatoes": 96,
    },
    {
        "title": "Mad Max: Fury Road",
        "year": 2015,
        "description": "In a post-apocalyptic wasteland, Max teams up with Furiosa to flee a cult leader.",
        "poster_url": "https://image.tmdb.org/t/p/w342/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg",
        "providers": ["hbo", "amazon"],
        "rotten_tomatoes": 97,
    },
    {
        "title": "Parasite",
        "year": 2019,
        "description": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
        "poster_url": "https://image.tmdb.org/t/p/w342/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg",
        "providers": ["hulu"],
        "rotten_tomatoes": 99,
    },
    {
        "title": "Knives Out",
        "year": 2019,
        "description": "A modern whodunit where a detective investigates the death of a patriarch of an eccentric, combative family.",
        "poster_url": "https://image.tmdb.org/t/p/w342/pThyQovXQrw2m0s9x82twj48Jq4.jpg",
        "providers": ["amazon", "netflix"],
        "rotten_tomatoes": 97,
    },
    {
        "title": "Spider-Man: Into the Spider-Verse",
        "year": 2018,
        "description": "Teen Miles Morales becomes Spider-Man and joins other Spider-People from other dimensions.",
        "poster_url": "https://image.tmdb.org/t/p/w342/iiZZdoQBEYBv6id8su7ImL0oCbD.jpg",
        "providers": ["netflix"],
        "rotten_tomatoes": 97,
    },
]


def _matches_shared_providers(item: Dict, shared_providers: Optional[Set[str]]) -> bool:
    if not shared_providers:
        return True
    providers = set(map(str.lower, item.get("providers", [])))
    return len(providers.intersection(shared_providers)) > 0


def get_next_demo_candidate(
    used_titles: Set[str],
    shared_providers: Optional[Set[str]] = None,
) -> Optional[Dict]:
    """Return the next candidate dict not in used_titles and compatible with shared providers.

    Returns None if the demo catalog is exhausted under the constraints.
    """
    for item in _DEMO_CATALOG:
        if item["title"] in used_titles:
            continue
        if _matches_shared_providers(item, shared_providers):
            return item
    return None


# ---------------------
# TMDb integration
# ---------------------
_TMDb_BASE = "https://api.themoviedb.org/3"
_TMDb_IMAGE = "https://image.tmdb.org/t/p/w342"
_TMDb_REGION = os.getenv("TMDB_REGION", "US")

# Very small name normalization for a few common providers used in this app
_PROVIDER_NORMALIZATION = {
    "netflix": "netflix",
    "hulu": "hulu",
    "amazon prime video": "amazon",
    "amazon video": "amazon",
    "prime video": "amazon",
    "hbo max": "hbo",
    "max": "hbo",
}

# Tiny in-process caches to cut down on duplicate requests
_PAGE_CACHE: dict[int, list[dict]] = {}
_PROVIDER_CACHE: dict[tuple[int, str], list[str]] = {}


def _tmdb_is_configured() -> bool:
    return bool(os.getenv("TMDB_READ_TOKEN") or os.getenv("TMDB_API_KEY"))


def _tmdb_headers() -> dict:
    token = os.getenv("TMDB_READ_TOKEN")
    if token:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
    return {"Accept": "application/json"}


def _tmdb_params() -> dict:
    api_key = os.getenv("TMDB_API_KEY")
    return {"api_key": api_key} if api_key else {}


def _normalize_provider_names(raw_names: list[str]) -> list[str]:
    out = []
    for name in raw_names:
        key = _PROVIDER_NORMALIZATION.get(name.strip().lower())
        if key and key not in out:
            out.append(key)
    return out


def _fetch_popular_page(page: int) -> list[dict]:
    if page in _PAGE_CACHE:
        return _PAGE_CACHE[page]
    url = f"{_TMDb_BASE}/movie/popular"
    with httpx.Client(timeout=7.0) as client:
        r = client.get(url, headers=_tmdb_headers(), params={"language": "en-US", "page": page, **_tmdb_params()})
        r.raise_for_status()
        data = r.json()
    results = data.get("results", []) if isinstance(data, dict) else []
    _PAGE_CACHE[page] = results
    return results


def _fetch_movie_providers(movie_id: int, region: str) -> list[str]:
    cache_key = (movie_id, region)
    if cache_key in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[cache_key]
    url = f"{_TMDb_BASE}/movie/{movie_id}/watch/providers"
    with httpx.Client(timeout=7.0) as client:
        r = client.get(url, headers=_tmdb_headers(), params=_tmdb_params())
        r.raise_for_status()
        data = r.json()
    raw = []
    try:
        country = data.get("results", {}).get(region, {})
        # Combine flatrate/rent/buy/ads/free names if present
        for key in ("flatrate", "rent", "buy", "ads", "free"):
            for prov in country.get(key, []) or []:
                n = prov.get("provider_name")
                if n:
                    raw.append(n)
    except Exception:
        raw = []
    providers = _normalize_provider_names(raw)
    _PROVIDER_CACHE[cache_key] = providers
    return providers


def _tmdb_map_item(movie: dict, providers: Optional[list[str]] = None) -> dict:
    title = movie.get("title") or movie.get("name") or ""
    release_date = movie.get("release_date") or ""
    year = None
    if isinstance(release_date, str) and len(release_date) >= 4:
        try:
            year = int(release_date[:4])
        except Exception:
            year = None
    poster_path = movie.get("poster_path")
    poster_url = f"{_TMDb_IMAGE}{poster_path}" if poster_path else None
    overview = movie.get("overview")
    item = {
        "title": title,
        "year": year,
        "description": overview,
        "poster_url": poster_url,
        "providers": providers or [],
        "rotten_tomatoes": None,
    }
    return item


def _get_next_tmdb_candidate(used_titles: Set[str], shared_providers: Optional[Set[str]]) -> Optional[Dict]:
    # Try a few pages to find a suitable, unused candidate
    try:
        for page in range(1, 6):  # up to 5 pages
            for movie in _fetch_popular_page(page):
                title = (movie.get("title") or movie.get("name") or "").strip()
                if not title or title in used_titles:
                    continue
                providers: Optional[list[str]] = None
                if shared_providers:
                    # fetch providers for this movie and check intersection
                    provs = _fetch_movie_providers(int(movie.get("id")), _TMDb_REGION)
                    if not set(provs).intersection(shared_providers):
                        continue
                    providers = provs
                return _tmdb_map_item(movie, providers=providers)
        return None
    except Exception:
        # On any error, signal no candidate so callers can fall back
        return None


def get_next_candidate(
    used_titles: Set[str],
    shared_providers: Optional[Set[str]] = None,
) -> Optional[Dict]:
    """Primary candidate source.

    If TMDb credentials are available via env (TMDB_READ_TOKEN preferred, or TMDB_API_KEY),
    we attempt to fetch from TMDb. On any error or when not configured, we fall back to the
    built-in demo list.

    Env vars:
      - TMDB_READ_TOKEN: v4 Read Access Token (starts with eyJ...)
      - TMDB_API_KEY: v3 API key (32 hex chars)
      - TMDB_REGION: region for watch providers (default US)
    """
    if _tmdb_is_configured():
        item = _get_next_tmdb_candidate(used_titles=used_titles, shared_providers=shared_providers)
        if item:
            return item
    # Fallback
    return get_next_demo_candidate(used_titles=used_titles, shared_providers=shared_providers)
