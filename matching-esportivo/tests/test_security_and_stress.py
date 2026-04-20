from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from time import perf_counter

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from pydantic import ValidationError

from app.core.config import settings
from app.middleware.match_performance_rate_limit import MatchPerformanceRateLimitMiddleware
from app.models.player_stats import MatchPerformance
from app.schemas.club import ClubCreate
from app.schemas.user import PlayerStatsUpdate
from app.services.maintenance_service import apply_common_xp_with_cap
from app.services.overall_engine import OverallRequest, calculate_overall_async
from app.services.xp_service import process_match_performance


def _build_token(subject: str) -> str:
    payload = {
        "sub": subject,
        "exp": int((datetime.now(UTC) + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


@pytest.mark.asyncio
async def test_overall_engine_supports_all_modes() -> None:
    source = {
        "pace": 70,
        "shooting": 72,
        "passing": 74,
        "defense": 68,
        "physical": 75,
        "technique": 73,
        "short_finish": 72,
        "long_shot": 70,
        "free_kick": 67,
        "agility": 80,
        "ball_control": 78,
        "stamina": 76,
        "strength": 73,
        "shoot_long": 71,
        "shoot_mid": 70,
        "shoot_short": 72,
        "finishing": 75,
        "spike_power": 74,
        "spike_accuracy": 73,
        "serve_power": 72,
        "serve_tactical": 70,
        "block": 69,
        "reception": 71,
        "floor_defense": 72,
        "coverage": 70,
        "setting": 73,
        "creativity": 74,
        "game_vision": 72,
        "lateral_agility": 71,
        "reaction": 73,
        "coordination": 72,
        "sand_agility": 74,
        "jumping_endurance": 75,
    }

    requests = [
        OverallRequest(sport_type="football", position="meia", sub_type="futsal"),
        OverallRequest(sport_type="football", position="meia", sub_type="society"),
        OverallRequest(sport_type="basketball", position="ala", sub_type="3x3"),
        OverallRequest(sport_type="volleyball", position="ponteiro", sub_type="beach"),
        OverallRequest(sport_type="volleyball", position="ponteiro", sub_type="quadra"),
        OverallRequest(sport_type="football", position="meia", sub_type="flex"),
    ]

    for request in requests:
        overall = await calculate_overall_async(request=request, source=source)
        assert 0 <= overall <= 99


def test_rate_limit_rejects_missing_or_mismatched_jwt(monkeypatch) -> None:
    app = FastAPI()
    app.add_middleware(MatchPerformanceRateLimitMiddleware)

    @app.post("/api/ranked/box-score")
    async def endpoint() -> dict[str, str]:
        return {"status": "ok"}

    async def fake_is_admin(_user_id: str) -> bool:
        return False

    async def fake_last_submission(_user_id: str):
        return None

    monkeypatch.setattr(
        "app.middleware.match_performance_rate_limit._is_admin_arena_owner",
        fake_is_admin,
    )
    monkeypatch.setattr(
        "app.middleware.match_performance_rate_limit._get_last_submission",
        fake_last_submission,
    )

    with TestClient(app) as client:
        missing = client.post("/api/ranked/box-score", json={"user_id": "user-1", "sport_type": "football"})
        assert missing.status_code == 401

        token_other = _build_token("another-user")
        mismatch = client.post(
            "/api/ranked/box-score",
            json={"user_id": "user-1", "sport_type": "football"},
            headers={"Authorization": f"Bearer {token_other}"},
        )
        assert mismatch.status_code == 403

        token_ok = _build_token("user-1")
        ok = client.post(
            "/api/ranked/box-score",
            json={"user_id": "user-1", "sport_type": "football"},
            headers={"Authorization": f"Bearer {token_ok}"},
        )
        assert ok.status_code == 200


def test_reject_negative_attribute_injection() -> None:
    with pytest.raises(ValidationError):
        PlayerStatsUpdate(user_id="user-1", pace=-5)


def test_sanitize_xss_text_inputs() -> None:
    payload = ClubCreate(
        name="<script>alert('x')</script> Arena",
        description="<img src=x onerror=alert(1)>",
        owner_id="owner-1",
        sport_type="football",
        privacy_type="public",
        latitude=0,
        longitude=0,
    )

    assert "<" not in payload.name
    assert "<" not in (payload.description or "")


def test_stress_xp_prestige_integrity_1000_iterations() -> None:
    rng = random.Random(42)

    current_attribute = 50
    residual = 0
    total_prestige = 0

    for _ in range(1000):
        incoming = rng.randint(0, 300)
        result = apply_common_xp_with_cap(
            current_attribute_value=current_attribute,
            current_residual_xp=residual,
            incoming_xp=incoming,
        )

        current_attribute = min(99, current_attribute + result.applied_points)
        residual = result.residual_xp
        total_prestige += result.prestige_xp

        assert 0 <= current_attribute <= 99
        assert 0 <= residual <= 59
        assert total_prestige >= 0


def test_box_score_processing_under_100ms() -> None:
    performance = MatchPerformance(
        user_id="perf-user",
        sport_type="football",
        goals=2,
        assists=1,
        tackles=3,
        dribbles=4,
        defenses=2,
    )

    started = perf_counter()
    process_match_performance(performance, player_position="meia", player_overall=70)
    elapsed_ms = (perf_counter() - started) * 1000.0

    assert elapsed_ms < 100.0
