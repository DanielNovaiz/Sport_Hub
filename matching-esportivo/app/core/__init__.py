"""Core da aplicação - Configurações e Database"""

from app.core.config import settings
from app.core.enums import SportType, FootballSubType, BasketballSubType, VolleyballSubType, SportSubType
from app.positions import POSITIONS_MAP, normalize_position_input


def get_session(*args, **kwargs):
    from app.core.database import get_session as _get_session

    return _get_session(*args, **kwargs)


async def init_db(*args, **kwargs):
    from app.core.database import init_db as _init_db

    return await _init_db(*args, **kwargs)


async def close_db(*args, **kwargs):
    from app.core.database import close_db as _close_db

    return await _close_db(*args, **kwargs)

__all__ = [
    "settings",
    "get_session",
    "init_db",
    "close_db",
    "SportType",
    "FootballSubType",
    "BasketballSubType",
    "VolleyballSubType",
    "SportSubType",
    "POSITIONS_MAP",
    "normalize_position_input",
]
