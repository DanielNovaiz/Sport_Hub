"""Runner de manutenção para Janitor Bot e migração de sub-atributos.

Uso:
    python scripts/database_janitor.py --mode cleanup
    python scripts/database_janitor.py --mode backfill
    python scripts/database_janitor.py --mode all
"""

from __future__ import annotations

import argparse
import asyncio

from app.core.database import async_session
from app.services.maintenance_service import (
    backfill_missing_sub_attributes,
    check_xp_consistency,
    cleanup_orphaned_matches,
)


async def _run(mode: str, batch_size: int) -> None:
    async with async_session() as session:
        if mode in {"cleanup", "all"}:
            cleanup_report = await cleanup_orphaned_matches(session, batch_size=batch_size)
            print(
                "cleanup_orphaned_matches",
                {
                    "scanned_rows": cleanup_report.scanned_rows,
                    "deleted_rows": cleanup_report.deleted_rows,
                },
            )

        if mode in {"backfill", "all"}:
            backfill_report = await backfill_missing_sub_attributes(session, batch_size=batch_size)
            print(
                "backfill_missing_sub_attributes",
                {
                    "scanned_profiles": backfill_report.scanned_profiles,
                    "updated_profiles": backfill_report.updated_profiles,
                },
            )

        if mode in {"xp", "all"}:
            xp_report = await check_xp_consistency(session)
            print(
                "check_xp_consistency",
                {
                    "scanned_rows": xp_report.scanned_rows,
                    "capped_rows": xp_report.capped_rows,
                    "prestige_rows_created": xp_report.prestige_rows_created,
                    "prestige_xp_moved": xp_report.prestige_xp_moved,
                },
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Database Janitor / Maintenance runner")
    parser.add_argument(
        "--mode",
        choices=["cleanup", "backfill", "xp", "all"],
        default="all",
        help="Seleciona rotina de manutenção",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Tamanho do lote para operações de manutenção",
    )
    args = parser.parse_args()

    asyncio.run(_run(args.mode, max(1, args.batch_size)))


if __name__ == "__main__":
    main()
