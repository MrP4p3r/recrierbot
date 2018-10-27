"""Initialization root."""

import aiohttp.web

from .logging import configure_logging
from .settings import Settings
from .db import make_db
from .domain import DomainRoot
from .bot import make_bot
from .routes import make_aiohttp_routes


def run_app():
    settings = Settings()
    aiohttp.web.run_app(make_app(settings), host=settings.web.bind, port=settings.web.port)


async def make_app(settings: Settings) -> aiohttp.web.Application:
    await configure_logging()

    db = await make_db(settings.db)
    domain = DomainRoot(db.connect, settings.domain)
    bot = await make_bot(settings.bot, domain)

    app = aiohttp.web.Application()
    make_aiohttp_routes(app, bot, domain)

    return app
