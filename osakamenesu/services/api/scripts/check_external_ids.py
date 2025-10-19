#!/usr/bin/env python
"""Check for duplicate external_id values in reviews and diaries."""
from __future__ import annotations

import asyncio
from typing import Dict, List, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.settings import settings


DUPLICATE_QUERIES: Dict[str, str] = {
    "reviews": """
        SELECT profile_id, external_id, COUNT(*) AS count
        FROM reviews
        WHERE external_id IS NOT NULL AND external_id <> ''
        GROUP BY profile_id, external_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC, profile_id, external_id
    """,
    "diaries": """
        SELECT profile_id, external_id, COUNT(*) AS count
        FROM diaries
        WHERE external_id IS NOT NULL AND external_id <> ''
        GROUP BY profile_id, external_id
        HAVING COUNT(*) > 1
        ORDER BY count DESC, profile_id, external_id
    """,
}


async def fetch_duplicates(engine: AsyncEngine, name: str, query: str) -> List[Tuple[str, str, int]]:
    async with engine.connect() as conn:
        result = await conn.execute(text(query))
        return [(str(row.profile_id), row.external_id, int(row.count)) for row in result]


async def main() -> None:
    database_url = settings.database_url
    if not database_url:
        raise SystemExit("DATABASE_URL is not configured. Set it via environment or .env file.")

    engine = create_async_engine(database_url)

    has_error = False
    for name, query in DUPLICATE_QUERIES.items():
        rows = await fetch_duplicates(engine, name, query)
        if rows:
            has_error = True
            print(f"[dup-check] {name}: detected {len(rows)} duplicate external_id entries")
            for profile_id, external_id, count in rows:
                print(f"  - profile_id={profile_id} external_id={external_id} count={count}")
        else:
            print(f"[dup-check] {name}: OK (no duplicates)")

    await engine.dispose()

    if has_error:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
