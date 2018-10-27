"""Database engine."""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy_aio import ASYNCIO_STRATEGY
from sqlalchemy_aio.engine import AsyncioEngine

from ..settings import DbSettings
from .metadata import meta


async def make_db(settings: DbSettings):
    db_url = URL('sqlite', database=settings.path)
    db_engine: AsyncioEngine = create_engine(db_url, strategy=ASYNCIO_STRATEGY)

    if not os.path.isfile(settings.path):
        open(settings.path, 'w').close()

    # FIXME: Using sync engine to create metadata
    meta.create_all(db_engine._engine, checkfirst=True)
    return db_engine
