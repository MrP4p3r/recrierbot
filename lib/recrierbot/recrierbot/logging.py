"""Logging configuration."""

import os
import sys
import logging


DEFAULT_LOGGING_LEVEL = logging.WARNING


async def configure_logging():
    # Using environ variables directly because we need to configure logging
    # before doing other stuff (loading settings as well)

    log_level = logging.WARNING
    log_level_str = os.environ.get('LOGGING_LEVEL', 'WARNING')

    if log_level_str.isnumeric():
        log_level = int(log_level_str)
    elif hasattr(logging, log_level_str):
        log_level = getattr(logging, log_level_str)
    elif log_level_str != '':
        logging.exception(f'No such logging level: {log_level}. Using default: WARNING')

    formatter = MyFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(handler)


class MyFormatter(logging.Formatter):

    def __init__(self):
        template = '[{asctime}] - [{levelname[0]}] [{module}:{lineno}] {message}'
        dtm_template = '%y%m%d %H:%M:%S'
        super().__init__(template, dtm_template, style='{')
