"""Persistência de telemetria em logs rotacionados JSONL."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
import json


class StructuredTelemetryRepository:
    """Escrita de telemetria fora do banco relacional principal."""

    def __init__(self, *, log_path: str | Path = "logs/telemetry.log", max_bytes: int = 5_242_880, backup_count: int = 10) -> None:
        self._logger = logging.getLogger("telemetry_events")
        if not self._logger.handlers:
            path = Path(log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)
            self._logger.propagate = False

    def emit(self, *, category: str, user_id: str, entries: list[str], extra: dict[str, Any] | None = None) -> None:
        payload = {
            "category": category,
            "user_id": user_id,
            "entries": entries,
            "entry_count": len(entries),
            **(extra or {}),
        }
        self._logger.info(json.dumps(payload, ensure_ascii=False))
