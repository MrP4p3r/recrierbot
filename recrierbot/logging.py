"""Logging configuration."""

import os
import logging


async def configure_logging():
    # Using environ variables directly because we need to configure logging
    # before doing other stuff (loading settings as well)

    log_level = os.environ.get('LOGGING_LEVEL', 'WARNING')
    if log_level.isnumeric():
        log_level = int(log_level)
    else:
        try:
            log_level = getattr(logging, log_level)
        except Exception:
            logging.exception(f'No such logging level: {log_level}. Using default: WARNING')
            log_level = logging.WARNING

    logging.getLogger().setLevel(log_level)
