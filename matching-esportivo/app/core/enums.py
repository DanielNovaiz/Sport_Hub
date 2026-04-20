"""Enumerações e tipos para domínios esportivos."""

from enum import Enum
from typing import Literal


class SportType(str, Enum):
    """Tipo de esporte."""

    FOOTBALL = "football"
    BASKETBALL = "basketball"
    VOLLEYBALL = "volleyball"


class FootballSubType(str, Enum):
    """Variações de futebol."""

    FUTSAL = "futsal"
    SOCIETY = "society"
    FIELD = "field"


class BasketballSubType(str, Enum):
    """Variações de basquete."""

    THREE_ON_THREE = "3x3"
    FIVE_ON_FIVE = "5x5"


class VolleyballSubType(str, Enum):
    """Variações de vôlei."""

    INDOOR = "indoor"
    BEACH = "beach"
    SITTING = "sitting"


# União dinâmica: qualquer sub_type de qualquer esporte
SportSubType = Literal[
    "futsal",
    "society",
    "field",
    "3x3",
    "5x5",
    "indoor",
    "beach",
    "sitting",
]
