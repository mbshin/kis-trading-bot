from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

_engine = None
Session: async_sessionmaker[AsyncSession] | None = None

class Base(DeclarativeBase):
    pass

async def init_db(dsn: str):
    global _engine, Session
    _engine = create_async_engine(dsn, pool_size=5, max_overflow=10)
    Session = async_sessionmaker(_engine, expire_on_commit=False)
