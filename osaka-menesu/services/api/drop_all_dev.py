#!/usr/bin/env python3
import asyncio
from app.db import engine
from app.models import Base


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


if __name__ == "__main__":
    asyncio.run(main())
    print("dropped all tables")

