import asyncio
import os
from copy import deepcopy
from logging import Handler, LogRecord, getLogger
from logging.config import dictConfig
from typing import Any

from telebot_views import bot

DEFAULT_COMMON_FORMAT = '%(asctime)s %(levelname)7s %(name)s: %(message)s'


def configure_logging(loggers: dict[Any, Any]) -> None:
    loggers.setdefault(
        'TeleBot',
        {
            'level': LOGGER.TELEBOT_LIB_LEVEL,
            'handlers': ['console'],
            'propagate': True,
        },
    )
    config = deepcopy(base_config)
    config['loggers'].update(loggers)
    dictConfig(config)


class LOGGER:
    """Settings for logger"""

    LOG_LEVEL: str = str(os.environ.get('LOGGER_LOG_LEVEL', 'DEBUG'))
    CONSOLE_HANDLER_LEVEL: str = str(os.environ.get('LOGGER_CONSOLE_HANDLER_LEVEL', 'DEBUG'))
    TELEGRAM_REPORTS_LEVEL: str = str(os.environ.get('LOGGER_TELEGRAM_REPORTS_LEVEL', 'ERROR'))
    TELEBOT_LIB_LEVEL: str = str(os.environ.get('LOGGER_TELEBOT_LIB_LEVEL', 'INFO'))
    COMMON_FORMAT: str = str(os.environ.get('LOGGER_COMMON_FORMAT', DEFAULT_COMMON_FORMAT))


base_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'common': {
            'format': LOGGER.COMMON_FORMAT,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'common',
            'level': LOGGER.CONSOLE_HANDLER_LEVEL,
        },
        'telegram-reports': {
            'class': 'telebot_views.log.TelegramReportsHandler',
            'formatter': 'common',
            'level': LOGGER.TELEGRAM_REPORTS_LEVEL,
        },
    },
    'root': {
        'level': LOGGER.LOG_LEVEL,
        'handlers': ['console', 'telegram-reports'],
        'propagate': False,
    },
    'loggers': {
        '__main__': {
            'level': LOGGER.LOG_LEVEL,
            'handlers': ['console'],
            'propagate': False,
        },
        'project': {
            'level': LOGGER.LOG_LEVEL,
            'handlers': ['console', 'telegram-reports'],
            'propagate': False,
        },
        **{
            name: {
                'level': LOGGER.LOG_LEVEL,
                'handlers': ['console', 'telegram-reports'],
                'propagate': True,
            }
            for name in ['telebot_views', 'telebot_models']
        },
        '': {
            'level': LOGGER.LOG_LEVEL,
            'handlers': ['console', 'telegram-reports'],
            'propagate': False,
        },
    },
}


class TelegramReportsHandler(Handler):
    """Telegram Reports Handler"""

    def filter(self, record: LogRecord) -> bool:
        result = super().filter(record)
        return (
            result
            and bool(bot.reports_bot.token and bot.reports_bot.token != bot.dummy_bot.token)
            and bool(bot.reports_chat_id)
        )

    def emit(self, record: LogRecord) -> None:
        coro = self.async_emit(record)
        try:
            asyncio.create_task(coro)
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(coro)

    async def async_emit(self, record: LogRecord) -> None:
        logger = getLogger(__name__)
        if record.exc_info and len(record.exc_info) >= 2:
            record.exc_text = f'{record.exc_info[0].__name__}: {record.exc_info[1]}'
        record.exc_info = None
        msg = self.format(record)
        try:
            await bot.reports_bot.send_message(bot.reports_chat_id, msg[:3000])
        except Exception:  # pylint: disable=broad-except
            logger.warning('Log error')
