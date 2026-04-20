"""Tests para court service (validação de schemas)."""

import pytest
from datetime import datetime, timedelta, UTC

from app.schemas.court import CourtCreate, BookingCreate, CourtRead


def test_court_create_validation():
    """CourtCreate deve validar campos."""
    valid = CourtCreate(
        owner_id="owner-1",
        name="Quadra Centro",
        sport_type="basketball",
        latitude=-23.5505,
        longitude=-46.6333,
        price_per_hour=150.0,
    )
    assert valid.name == "Quadra Centro"
    assert valid.sport_type == "basketball"
    assert valid.price_per_hour == 150.0


def test_court_create_rejects_invalid_coords():
    """CourtCreate deve validar latitude/longitude."""
    with pytest.raises(ValueError):
        CourtCreate(
            owner_id="owner-1",
            name="Bad Court",
            sport_type="tennis",
            latitude=91.0,  # > 90
            longitude=0.0,
            price_per_hour=100.0,
        )


def test_booking_create_validation():
    """BookingCreate deve validar times."""
    now = datetime.now(UTC)
    start = now + timedelta(hours=1)
    end = start + timedelta(hours=2)

    valid = BookingCreate(
        court_id="court-1",
        user_id="user-1",
        start_time=start,
        end_time=end,
    )
    assert valid.court_id == "court-1"
    assert valid.start_time < valid.end_time


def test_court_read_from_attributes():
    """CourtRead deve desserializar de ORM."""
    data = {
        "id": "court-123",
        "owner_id": "owner-1",
        "name": "Test Court",
        "description": None,
        "sport_type": "volleyball",
        "price_per_hour": 200.0,
        "photos_url": ["https://example.com/photo1.jpg"],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    court = CourtRead(**data)
    assert court.sport_type == "volleyball"
    assert len(court.photos_url) == 1
