"""Initialization root."""

import logging
import aiohttp.web

from .logging import configure_logging
from .settings import Settings
from .db import make_db
from .domain import DomainRoot
from .bot import make_bot
from .routes import make_aiohttp_routes


def run_app():
    settings = Settings()

    logging.warning(f'Using {settings.web.bind}:{settings.web.port}')
    aiohttp.web.run_app(
        make_app(settings),
        host=settings.web.bind,
        port=settings.web.port,
        print=None,
    )


async def make_app(settings: Settings) -> aiohttp.web.Application:
    await configure_logging()

    db = await make_db(settings.db)
    domain = DomainRoot(db.connect, settings.domain)
    bot = await make_bot(settings.bot, domain)

    app = aiohttp.web.Application()
    make_aiohttp_routes(app, bot, domain)

    @app.on_startup.append
    async def on_app_startup(_):
        logging.warning('App was started.')

    return app
