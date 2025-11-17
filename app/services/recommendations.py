import httpx
import os
from typing import List, Dict, Optional, Set, Union

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


# Optional simple title->genres mapping to support genre filtering without changing demo items
_TITLE_GENRES: dict[str, list[str]] = {
    "Inception": ["Sci-Fi", "Action", "Thriller"],
    "The Social Network": ["Drama"],
    "Mad Max: Fury Road": ["Action", "Adventure"],
    "Parasite": ["Thriller", "Drama"],
    "Knives Out": ["Mystery", "Crime"],
    "Spider-Man: Into the Spider-Verse": ["Animation", "Action"],
}


def _matches_genres(title: str, allowed: Optional[Set[str]]) -> bool:
    if not allowed:
        return True
    gs = set(_TITLE_GENRES.get(title, []))
    return bool(gs.intersection(allowed))


def get_next_demo_candidate(
    used_titles: Set[str],
    shared_providers: Optional[Set[str]] = None,
    genres: Optional[Set[str]] = None,
) -> Optional[Dict]:
    """Return the next candidate dict not in used_titles and compatible with filters.

    Returns None if the demo catalog is exhausted under the constraints.
    """
    for base in _DEMO_CATALOG:
        if base["title"] in used_titles:
            continue
        if not _matches_shared_providers(base, shared_providers):
            continue
        if not _matches_genres(base["title"], genres):
            continue
        # Do not mutate the catalog; copy and annotate reason
        item = dict(base)
        item["reason"] = "demo:genres_match" if genres else "demo:unrestricted"
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
# Discover cache keyed by (genres_key, providers_key, page, region, monetization, sort_by, vote_count_gte)
_DISCOVER_CACHE: dict[tuple[str, str, int,
                            str, str, str, int], list[dict]] = {}


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


# Map our normalized provider keys to TMDb provider IDs
# References (subject to change by TMDb): Netflix=8, Hulu=15, Amazon Prime Video=119, HBO Max/Max=1899 (older HBO Max=384)
_PROVIDER_ID_MAP: dict[str, list[int]] = {
    "netflix": [8],
    "hulu": [15],
    "amazon": [119],
    "hbo": [1899, 384],
}


def _provider_ids_for(shared_providers: Optional[Set[str]]) -> Optional[list[int]]:
    if not shared_providers:
        return None
    ids: list[int] = []
    for p in shared_providers:
        for pid in _PROVIDER_ID_MAP.get(p, []):
            if pid not in ids:
                ids.append(pid)
    return ids or None


def _fetch_popular_page(page: int) -> list[dict]:
    if page in _PAGE_CACHE:
        return _PAGE_CACHE[page]
    url = f"{_TMDb_BASE}/movie/popular"
    with httpx.Client(timeout=7.0) as client:
        r = client.get(url, headers=_tmdb_headers(), params={
                       "language": "en-US", "page": page, **_tmdb_params()})
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


def _discover_page(genres_ids: Optional[tuple[int, ...]], provider_ids: Optional[tuple[int, ...]], page: int,
                   vote_count_gte: int = 500, monetization: str = "flatrate|ads|free",
                   sort_by: str = "vote_average.desc") -> list[dict]:
    """Call TMDb Discover API and return results for a page. Cached in-process.

    - genres_ids: None for unrestricted or tuple of TMDb genre IDs (comma = AND per TMDb docs)
    - provider_ids: None or tuple of TMDb watch provider IDs
    """
    genres_key = ",".join(str(i) for i in genres_ids) if genres_ids else "-"
    prov_key = ",".join(str(i) for i in provider_ids) if provider_ids else "-"
    cache_key = (genres_key, prov_key, page, _TMDb_REGION,
                 monetization, sort_by, vote_count_gte)
    if cache_key in _DISCOVER_CACHE:
        return _DISCOVER_CACHE[cache_key]
    params: dict = {
        "language": "en-US",
        "page": page,
        "include_adult": False,
        "sort_by": sort_by,
        "vote_count.gte": vote_count_gte,
        **_tmdb_params(),
    }
    if genres_ids:
        params["with_genres"] = ",".join(str(i) for i in genres_ids)
    if provider_ids:
        params["with_watch_providers"] = ",".join(str(i) for i in provider_ids)
        params["watch_region"] = _TMDb_REGION
        params["with_watch_monetization_types"] = monetization
    url = f"{_TMDb_BASE}/discover/movie"
    with httpx.Client(timeout=8.0) as client:
        r = client.get(url, headers=_tmdb_headers(), params=params)
        r.raise_for_status()
        data = r.json()
    results = data.get("results", []) if isinstance(data, dict) else []
    _DISCOVER_CACHE[cache_key] = results
    return results


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


def _get_next_tmdb_candidate(used_titles: Set[str], shared_providers: Optional[Set[str]], genres: Optional[Union[list[str], Set[str]]] = None) -> Optional[Dict]:
    """Return next TMDb candidate with tiered genre priority and rating sort.

    Priority when finalized genres are provided (ordered: most-voted first):
      1) Highly rated movies matching BOTH selected genres (both present anywhere; at least one in top-2)
      2) Highly rated movies where the PRIMARY (most-voted) genre is in top-2
      3) Highly rated movies where the SECOND genre is in top-2
    If no genres provided, fall back to provider-filtered popular picks.

    Higher "rating" = vote_average desc, then vote_count desc, then popularity desc.
    Provider intersection is applied if provided.
    """
    # Local mapping from our canonical genre names to TMDb IDs
    TMDB_GENRE_IDS = {
        "Action": 28,
        "Comedy": 35,
        "Drama": 18,
        "Thriller": 53,
        "Horror": 27,
        "Sci-Fi": 878,
        "Romance": 10749,
        "Animation": 16,
        "Family": 10751,
        "Adventure": 12,
        "Documentary": 99,
        "Fantasy": 14,
        "Mystery": 9648,
        "Crime": 80,
    }

    # Normalize genres into an ordered list (as finalized order encodes vote priority)
    genres_ordered: list[str] = []
    if genres:
        try:
            if isinstance(genres, set):
                # sets do not preserve order; keep arbitrary but stable order
                genres_ordered = sorted(
                    [g for g in genres if isinstance(g, str)])
            else:
                genres_ordered = [g for g in list(
                    genres) if isinstance(g, str)]
        except Exception:
            genres_ordered = []

    sel_ids: list[int] = []
    for g in genres_ordered:
        gid = TMDB_GENRE_IDS.get(g)
        if gid is not None:
            sel_ids.append(gid)
    # Limit to at most two finalized genres
    sel_ids = sel_ids[:2]

    # Buckets
    both: list[dict] = []
    primary: list[dict] = []
    secondary: list[dict] = []
    unrestricted: list[dict] = []  # when no genres specified

    # First attempt: TMDb Discover API (broader than Popular) with paging and optional provider prefilter
    try:
        prov_ids = _provider_ids_for(shared_providers)

        def _score(movie: dict) -> tuple[float, int, float]:
            return (
                float(movie.get("vote_average") or 0.0),
                int(movie.get("vote_count") or 0),
                float(movie.get("popularity") or 0.0),
            )
        # Helper to select best from discover over up to 10 pages

        def _discover_pick(gen_ids: Optional[list[int]], tier: str) -> Optional[Dict]:
            best_item: Optional[Dict] = None
            best_score = (-1.0, -1, -1.0)
            ids_tuple = tuple(gen_ids) if gen_ids else None
            prov_tuple = tuple(prov_ids) if prov_ids else None
            for page in range(1, 11):
                for movie in _discover_page(ids_tuple, prov_tuple, page):
                    title = (movie.get("title") or movie.get(
                        "name") or "").strip()
                    if not title or title in used_titles:
                        continue
                    # Enforce our top-2 rules for tiers when genres provided
                    ids_list = movie.get("genre_ids") or []
                    try:
                        ids_set = set(int(i) for i in ids_list)
                        top2_set = set(int(i) for i in ids_list[:2])
                    except Exception:
                        ids_set = set()
                        top2_set = set()
                    ok = True
                    if sel_ids:
                        if tier == "both" and len(sel_ids) == 2:
                            ok = (sel_ids[0] in ids_set and sel_ids[1] in ids_set) and bool(
                                top2_set.intersection({sel_ids[0], sel_ids[1]}))
                        elif tier == "primary" and len(sel_ids) >= 1:
                            ok = sel_ids[0] in top2_set
                        elif tier == "secondary" and len(sel_ids) == 2:
                            ok = sel_ids[1] in top2_set
                    if not ok:
                        continue
                    sc = _score(movie)
                    if sc > best_score:
                        best_score = sc
                        mapped = _tmdb_map_item(movie, providers=list(
                            shared_providers) if shared_providers else None)
                        mapped["reason"] = f"tmdb:tier={tier if sel_ids else 'unrestricted'}"
                        best_item = mapped
            return best_item
        # Tiered attempts
        if len(sel_ids) == 2:
            pick = _discover_pick(sel_ids, "both")
            if pick:
                return pick
            pick = _discover_pick([sel_ids[0]], "primary")
            if pick:
                return pick
            pick = _discover_pick([sel_ids[1]], "secondary")
            if pick:
                return pick
        elif len(sel_ids) == 1:
            pick = _discover_pick([sel_ids[0]], "primary")
            if pick:
                return pick
        else:
            # No genres but provider prefilter available → pick unrestricted best by rating
            if prov_ids:
                pick = _discover_pick(None, "unrestricted")
                if pick:
                    return pick
    except Exception:
        # If discover flow fails, fall back to Popular loop below
        pass

    try:
        for page in range(1, 11):  # up to 10 pages for a decent pool
            for movie in _fetch_popular_page(page):
                title = (movie.get("title") or movie.get("name") or "").strip()
                if not title or title in used_titles:
                    continue
                # Provider intersection if required
                providers: Optional[list[str]] = None
                if shared_providers:
                    provs = _fetch_movie_providers(
                        int(movie.get("id")), _TMDb_REGION)
                    if not set(provs).intersection(shared_providers):
                        continue
                    providers = provs
                # If no genre constraints, collect unrestricted and continue
                if not sel_ids:
                    unrestricted.append(
                        {"movie": movie, "providers": providers})
                    continue
                ids = movie.get("genre_ids") or []
                try:
                    ids_set = set(int(i) for i in ids)
                    top2_list = [int(i) for i in ids[:2]]
                    top2_set = set(top2_list)
                except Exception:
                    ids_set = set()
                    top2_set = set()
                # Determine tier membership
                if len(sel_ids) == 2:
                    both_present_anywhere = sel_ids[0] in ids_set and sel_ids[1] in ids_set
                    at_least_one_in_top2 = bool(
                        top2_set.intersection({sel_ids[0], sel_ids[1]}))
                    if both_present_anywhere and at_least_one_in_top2:
                        both.append({"movie": movie, "providers": providers})
                        continue
                # Primary in top-2
                if len(sel_ids) >= 1 and sel_ids[0] in top2_set:
                    primary.append({"movie": movie, "providers": providers})
                    continue
                # Secondary in top-2
                if len(sel_ids) == 2 and sel_ids[1] in top2_set:
                    secondary.append({"movie": movie, "providers": providers})
                    continue
        # Helper to pick highest rated from a bucket

        def pick_best(bucket: list[dict]) -> Optional[Dict]:
            if not bucket:
                return None

            def score(entry: dict):
                m = entry["movie"]
                return (
                    float(m.get("vote_average") or 0.0),
                    int(m.get("vote_count") or 0),
                    float(m.get("popularity") or 0.0),
                )
            best = max(bucket, key=score)
            return _tmdb_map_item(best["movie"], providers=best.get("providers"))

        # Choose by priority and annotate reason
        best = pick_best(both)
        if best:
            best["reason"] = "tmdb:tier=both"
            return best
        best = pick_best(primary)
        if best:
            best["reason"] = "tmdb:tier=primary"
            return best
        best = pick_best(secondary)
        if best:
            best["reason"] = "tmdb:tier=secondary"
            return best
        if not sel_ids:
            best = pick_best(unrestricted)
            if best:
                best["reason"] = "tmdb:unrestricted"
                return best
        return None
    except Exception:
        return None


def get_next_candidate(
    used_titles: Set[str],
    shared_providers: Optional[Set[str]] = None,
    genres: Optional[Set[str]] = None,
) -> Optional[Dict]:
    """Primary candidate source (TMDb-only).

    If TMDb credentials are available via env (TMDB_READ_TOKEN preferred, or TMDB_API_KEY),
    we attempt to fetch from TMDb. We do NOT fall back to any in-process demo catalog.
    When TMDb is configured but a strict match is not found, we try progressively looser
    TMDb queries before giving up.

    Env vars:
      - TMDB_READ_TOKEN: v4 Read Access Token (starts with eyJ...)
      - TMDB_API_KEY: v3 API key (32 hex chars)
      - TMDB_REGION: region for watch providers (default US)
    """
    if _tmdb_is_configured():
        # Apply strict top-2 TMDb genre filtering when genres are provided
        item = _get_next_tmdb_candidate(
            used_titles=used_titles, shared_providers=shared_providers, genres=genres)
        if item:
            return item
        # Try unrestricted TMDb pick with same used/shared filters
        item = _get_next_tmdb_candidate(
            used_titles=used_titles, shared_providers=shared_providers, genres=None)
        if item:
            return item
        # Last-chance within TMDb: ignore used/providers/genres entirely
        item = _get_next_tmdb_candidate(
            used_titles=set(), shared_providers=None, genres=None)
        if item:
            return item
    # No TMDb candidate found or TMDb not configured
    return None


def get_candidate_queue(
    genres: Optional[Union[list[str], Set[str]]],
    shared_providers: Optional[Set[str]] = None,
    target_size: int = 100,
) -> list[Dict]:
    """Build an ordered queue of up to `target_size` candidates using TMDb Discover.

    Distribution when two genres are present (ordered primary, secondary):
      - Up to 50 items that include BOTH genres (AND); at least one must be in the movie's top-2
      - Remaining split evenly between primary-only and secondary-only buckets
    If only one genre is present, fill all slots with that genre.

    Provider prefilter is applied first; if insufficient results to fill quotas, the search
    is widened by relaxing the provider constraint. The function never uses the demo catalog.
    """
    # If TMDb not configured, return empty list (caller may decide how to handle)
    if not _tmdb_is_configured():
        return []

    # Map canonical names to TMDb ids (keep in sync with _get_next_tmdb_candidate)
    TMDB_GENRE_IDS = {
        "Action": 28,
        "Comedy": 35,
        "Drama": 18,
        "Thriller": 53,
        "Horror": 27,
        "Sci-Fi": 878,
        "Romance": 10749,
        "Animation": 16,
        "Family": 10751,
        "Adventure": 12,
        "Documentary": 99,
        "Fantasy": 14,
        "Mystery": 9648,
        "Crime": 80,
    }

    # Normalize genres order (as finalized order encodes vote priority)
    ordered: list[str] = []
    if genres:
        try:
            ordered = list(genres) if isinstance(
                genres, list) else sorted(list(genres))
        except Exception:
            ordered = []
    sel_ids = [TMDB_GENRE_IDS[g] for g in ordered if g in TMDB_GENRE_IDS][:2]

    # Desired distribution
    want_both = min(50, target_size)
    want_primary = 0
    want_secondary = 0
    if len(sel_ids) == 2:
        remainder = max(0, target_size - want_both)
        want_primary = remainder // 2
        want_secondary = remainder - want_primary
    elif len(sel_ids) == 1:
        want_both = 0
        want_primary = target_size
    else:
        # No genres: unrestricted by rating
        want_both = 0
        want_primary = target_size

    results: list[Dict] = []
    seen_titles: set[str] = set()

    def add_items(movies: list[dict], tier: str):
        for m in movies:
            title = (m.get("title") or m.get("name") or "").strip()
            if not title or title in seen_titles:
                continue
            item = _tmdb_map_item(m)
            item["source"] = "tmdb"
            item["reason"] = f"tmdb:queue:tier={tier}"
            results.append(item)
            seen_titles.add(title)

    def collect_discover(gen_ids: Optional[list[int]], needed: int, tier: str, prov_ids_pref: Optional[list[int]]):
        if needed <= 0:
            return []
        picked: list[dict] = []
        # First with provider filter
        for page in range(1, 21):  # up to 20 pages to widen coverage ~400 results window
            movies = _discover_page(tuple(gen_ids) if gen_ids else None,
                                    tuple(
                                        prov_ids_pref) if prov_ids_pref else None,
                                    page,
                                    vote_count_gte=100,
                                    sort_by="vote_average.desc")
            if not movies:
                break
            for movie in movies:
                title = (movie.get("title") or movie.get("name") or "").strip()
                if not title or title in seen_titles:
                    continue
                # Apply our top-2 logic for tiers when we have two genres
                ids_list = movie.get("genre_ids") or []
                try:
                    ids_set = set(int(i) for i in ids_list)
                    top2_set = set(int(i) for i in ids_list[:2])
                except Exception:
                    ids_set = set()
                    top2_set = set()
                ok = True
                if len(sel_ids) == 2:
                    if tier == "both":
                        ok = (sel_ids[0] in ids_set and sel_ids[1] in ids_set) and bool(
                            top2_set.intersection({sel_ids[0], sel_ids[1]}))
                    elif tier == "primary":
                        ok = sel_ids[0] in top2_set
                    elif tier == "secondary":
                        ok = sel_ids[1] in top2_set
                elif len(sel_ids) == 1 and tier == "primary":
                    ok = sel_ids[0] in ids_set
                if not ok:
                    continue
                picked.append(movie)
                if len(picked) >= needed:
                    break
            if len(picked) >= needed:
                break
        # If insufficient and provider filter was applied, relax providers
        if len(picked) < needed and prov_ids_pref:
            for page in range(1, 21):
                movies = _discover_page(tuple(gen_ids) if gen_ids else None,
                                        None,
                                        page,
                                        vote_count_gte=100,
                                        sort_by="vote_average.desc")
                if not movies:
                    break
                for movie in movies:
                    title = (movie.get("title") or movie.get(
                        "name") or "").strip()
                    if not title or title in seen_titles or movie in picked:
                        continue
                    ids_list = movie.get("genre_ids") or []
                    try:
                        ids_set = set(int(i) for i in ids_list)
                        top2_set = set(int(i) for i in ids_list[:2])
                    except Exception:
                        ids_set = set()
                        top2_set = set()
                    ok = True
                    if len(sel_ids) == 2:
                        if tier == "both":
                            ok = (sel_ids[0] in ids_set and sel_ids[1] in ids_set) and bool(
                                top2_set.intersection({sel_ids[0], sel_ids[1]}))
                        elif tier == "primary":
                            ok = sel_ids[0] in top2_set
                        elif tier == "secondary":
                            ok = sel_ids[1] in top2_set
                    elif len(sel_ids) == 1 and tier == "primary":
                        ok = sel_ids[0] in ids_set
                    if not ok:
                        continue
                    picked.append(movie)
                    if len(picked) >= needed:
                        break
                if len(picked) >= needed:
                    break
        return picked

    prov_ids = _provider_ids_for(shared_providers)

    # Fill BOTH bucket
    both_movies: list[dict] = []
    if len(sel_ids) == 2:
        both_movies = collect_discover(sel_ids, want_both, "both", prov_ids)
        add_items(both_movies, "both")
    # Compute remaining capacity
    remaining = max(0, target_size - len(results))

    # Split remainder evenly across primary and secondary
    if len(sel_ids) == 2 and remaining > 0:
        half = remaining // 2
        prim_needed = half
        sec_needed = remaining - half
        # Primary-only
        prim_movies = collect_discover(
            [sel_ids[0]], prim_needed, "primary", prov_ids)
        add_items(prim_movies, "primary")
        # Secondary-only
        sec_movies = collect_discover(
            [sel_ids[1]], sec_needed, "secondary", prov_ids)
        add_items(sec_movies, "secondary")
    elif len(sel_ids) == 1 and remaining > 0:
        prim_movies = collect_discover(
            [sel_ids[0]], remaining, "primary", prov_ids)
        add_items(prim_movies, "primary")
    elif remaining > 0:
        # No genres provided: unrestricted by rating (provider-pref then relaxed)
        any_movies = collect_discover(
            None, remaining, "unrestricted", prov_ids)
        add_items(any_movies, "unrestricted")

    # Ensure “Scary Movie” franchise inclusion for Comedy + (Thriller or Horror)
    try:
        from urllib.parse import quote

        def _search_titles(query: str) -> list[dict]:
            url = f"{_TMDb_BASE}/search/movie"
            with httpx.Client(timeout=7.0) as client:
                r = client.get(url, headers=_tmdb_headers(), params={
                               "query": query, **_tmdb_params()})
                r.raise_for_status()
                data = r.json()
            return data.get("results", []) if isinstance(data, dict) else []
        genres_lower = [g.lower() for g in ordered]
        if "comedy" in genres_lower and ("thriller" in genres_lower or "horror" in genres_lower):
            scary = _search_titles("Scary Movie")
            # Prepend any missing Scary Movie titles
            scary_sorted = sorted(scary, key=lambda m: (
                m.get("release_date") or ""))
            prepend: list[Dict] = []
            for m in scary_sorted:
                t = (m.get("title") or m.get("name") or "").strip()
                if not t or t in seen_titles:
                    continue
                item = _tmdb_map_item(m)
                item["source"] = "tmdb"
                item["reason"] = "tmdb:queue:seed=scary_movie"
                prepend.append(item)
                seen_titles.add(t)
            # Put seeds at the very front while keeping total size at target_size
            if prepend:
                results = (prepend + results)[:target_size]
    except Exception:
        pass

    # Truncate to target_size
    if len(results) > target_size:
        results = results[:target_size]

    return results
