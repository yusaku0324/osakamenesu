from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .settings import settings
from . import models


engine = create_async_engine(settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables if they do not exist (dev convenience)."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
