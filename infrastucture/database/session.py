from typing import AsyncGenerator
from .base import async_session

async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise