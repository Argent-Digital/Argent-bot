from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.config import settings

async_engine = create_async_engine(
    url=settings.DATABASE_URL_asynpg,
    echo=False,
    pool_size=5,
    max_overflow=10
)

sync_engine = create_async_engine(
    url=settings.DATABASE_URL_synpg,
    echo=False,
    pool_size=5,
    max_overflow=10
)

async_session_factory = async_sessionmaker(async_engine)
sync_session_factory = sessionmaker(sync_engine)

class Base(DeclarativeBase):
    pass