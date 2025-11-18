from app.services.recommendations import _normalize_provider_names


def test_normalize_provider_names_maps_common_variants():
    raw = [
        'Amazon Prime Video', 'Prime Video', 'Amazon Video',
        'Netflix', 'Hulu', 'HBO Max', 'Max', 'Unknown Provider'
    ]
    out = _normalize_provider_names(raw)
    # Deduplicated and normalized keys
    assert 'amazon' in out
    assert 'netflix' in out
    assert 'hulu' in out
    assert 'hbo' in out
    # Unknowns are dropped
    assert 'Unknown Provider' not in out
