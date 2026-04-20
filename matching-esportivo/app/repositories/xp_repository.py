"""Repositório SQLAlchemy para leitura/escrita de XP e conquistas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player_stats import PlayerStats, UserAchievement, UserXP
from app.services.xp_constants import ALL_PROGRESS_ATTRIBUTES


@dataclass(frozen=True)
class AchievementTriggerLike:
    code: str
    title: str
    execution_bonus: int
    bonus_attributes: dict[str, int]


class XpRepository(Protocol):
    async def get_user_xp_rows(self, user_id: str) -> list[UserXP]: ...
    async def ensure_user_xp_rows(self, user_id: str) -> list[UserXP]: ...
    async def get_player_stats(self, user_id: str) -> PlayerStats | None: ...
    async def ensure_player_stats(self, user_id: str, default_position: str) -> PlayerStats: ...
    async def upsert_user_achievements(self, user_id: str, triggers: list[AchievementTriggerLike]) -> list[UserAchievement]: ...


class SqlAlchemyXpRepository:
    """Implementação SQLAlchemy do repositório de XP."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_xp_rows(self, user_id: str) -> list[UserXP]:
        result = await self._session.execute(
            select(UserXP).where(UserXP.user_id == user_id).with_for_update()
        )
        return result.scalars().all()

    async def ensure_user_xp_rows(self, user_id: str) -> list[UserXP]:
        xp_rows = await self.get_user_xp_rows(user_id)
        existing_attributes = {row.attribute_name for row in xp_rows}
        missing_rows = [
            UserXP(user_id=user_id, attribute_name=attribute_name)
            for attribute_name in ALL_PROGRESS_ATTRIBUTES
            if attribute_name not in existing_attributes
        ]
        if missing_rows:
            for row in missing_rows:
                self._session.add(row)
            await self._session.flush()
            xp_rows.extend(missing_rows)
        xp_rows.sort(key=lambda row: ALL_PROGRESS_ATTRIBUTES.index(row.attribute_name) if row.attribute_name in ALL_PROGRESS_ATTRIBUTES else 999)
        return xp_rows

    async def get_player_stats(self, user_id: str) -> PlayerStats | None:
        result = await self._session.execute(select(PlayerStats).where(PlayerStats.user_id == user_id))
        return result.scalars().first()

    async def ensure_player_stats(self, user_id: str, default_position: str) -> PlayerStats:
        stats = await self.get_player_stats(user_id)
        if stats:
            return stats
        stats = PlayerStats(user_id=user_id, position=default_position)
        self._session.add(stats)
        await self._session.flush()
        return stats

    async def upsert_user_achievements(self, user_id: str, triggers: list[AchievementTriggerLike]) -> list[UserAchievement]:
        persisted: list[UserAchievement] = []

        for trigger in triggers:
            query = select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.code == trigger.code,
            )
            result = await self._session.execute(query)
            achievement = result.scalars().first()
            code_count_result = await self._session.execute(
                select(func.count(UserAchievement.id)).where(UserAchievement.code == trigger.code)
            )
            total_count_result = await self._session.execute(select(func.count(UserAchievement.id)))
            code_count = int(code_count_result.scalar_one() or 0)
            total_count = int(total_count_result.scalar_one() or 0)

            from app.services.achievement_service import apply_achievement_rarity_bonus, resolve_achievement_rarity

            rarity_tier = resolve_achievement_rarity(code_count, total_count)
            base_bonus_value = max(trigger.bonus_attributes.values(), default=0)
            rarity_bonus_value = apply_achievement_rarity_bonus(base_bonus_value, rarity_tier)

            if not achievement:
                achievement = UserAchievement(
                    user_id=user_id,
                    code=trigger.code,
                    title=trigger.title,
                    tier=rarity_tier,
                    execution_count=1,
                    bonus_attribute=max(trigger.bonus_attributes, key=trigger.bonus_attributes.get, default=None),
                    bonus_value=rarity_bonus_value,
                    last_triggered_at=datetime.now(UTC),
                )
                self._session.add(achievement)
            else:
                achievement.title = trigger.title
                achievement.execution_count += max(1, trigger.execution_bonus)
                achievement.tier = rarity_tier
                achievement.bonus_attribute = max(trigger.bonus_attributes, key=trigger.bonus_attributes.get, default=achievement.bonus_attribute)
                achievement.bonus_value = max(achievement.bonus_value, rarity_bonus_value)
                achievement.last_triggered_at = datetime.now(UTC)

            persisted.append(achievement)

        if persisted:
            await self._session.flush()

        return persisted
