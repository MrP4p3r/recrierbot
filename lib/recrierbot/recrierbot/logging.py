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

    default_loglevel_warning = False
    if log_level_str.isnumeric():
        log_level = int(log_level_str)
    elif hasattr(logging, log_level_str):
        log_level = getattr(logging, log_level_str)
    elif log_level_str != '':
        default_loglevel_warning = True

    formatter = MyFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers = []
    logger.addHandler(handler)

    if default_loglevel_warning:
        logging.warning(f'No such logging level: {log_level}.')

    logging.warning(f'Using logging level: {log_level}')


class MyFormatter(logging.Formatter):

    def __init__(self):
        template = '[ {asctime} {levelname} - {module}:{lineno}] {message}'
        dtm_template = '%y.%m.%d %H:%M:%S'
        super().__init__(template, dtm_template, style='{')
