"""Database engine."""

import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy_aio import ASYNCIO_STRATEGY
from sqlalchemy_aio.engine import AsyncioEngine

from ..settings import DbSettings
from .metadata import meta


async def make_db(settings: DbSettings):
    db_path = os.path.abspath(settings.path)

    db_url = URL('sqlite', database=db_path)
    db_engine: AsyncioEngine = create_engine(db_url, strategy=ASYNCIO_STRATEGY)

    logging.info(f'Using sqlite database "{db_url!r}"')

    if not os.path.isfile(db_path):
        logging.warning(f'Database file {db_path} does not exist.')
        open(settings.path, 'w').close()
        logging.warning(f'Database file {db_path} was created.')

    # FIXME: Using sync engine to create metadata
    meta.create_all(db_engine._engine, checkfirst=True)

    logging.info(f'Database configuration done.')
    return db_engine
