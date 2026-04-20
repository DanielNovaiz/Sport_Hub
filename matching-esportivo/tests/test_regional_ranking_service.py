"""Tests para helpers do ranking regional."""

from app.services.ranked_service import _normalize_city_key, _resolve_city_center


def test_normalize_city_key_defaults_to_goiania() -> None:
    assert _normalize_city_key(None) == "goiânia"
    assert _normalize_city_key("   ") == "goiânia"


def test_resolve_city_center_accepts_goiania_variants() -> None:
    city_key, coords = _resolve_city_center("Goiânia")
    assert city_key == "goiânia"
    assert coords == (-49.2643, -16.6864)

    city_key_ascii, coords_ascii = _resolve_city_center("goiania")
    assert city_key_ascii == "goiania"
    assert coords_ascii == (-49.2643, -16.6864)


def test_resolve_city_center_falls_back_for_unknown_city() -> None:
    city_key, coords = _resolve_city_center("Campinas")
    assert city_key == "goiânia"
    assert coords == (-49.2643, -16.6864)
