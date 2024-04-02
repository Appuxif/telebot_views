import asyncio
from copy import deepcopy
from logging import Handler, LogRecord, getLogger
from logging.config import dictConfig
from typing import Any

from telebot_views import bot

base_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'common': {
            'format': '%(asctime)s %(levelname)7s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'common',
            'level': 'DEBUG',
        },
        'telegram-reports': {
            'class': 'project.core.logging.TelegramReportsHandler',
            'formatter': 'common',
            'level': 'ERROR',
        },
    },
    'loggers': {
        '__main__': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'project': {
            'level': 'DEBUG',
            'handlers': ['console', 'telegram-reports'],
            'propagate': False,
        },
        **{
            name: {
                'level': 'DEBUG',
                'handlers': ['console', 'telegram-reports'],
                'propagate': True,
            }
            for name in ['telebot_views']
        },
        'TeleBot': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
        },
    },
}


def configure_logging(loggers: dict[Any, Any]) -> None:
    config = deepcopy(base_config)
    config['loggers'].update(loggers)
    dictConfig(config)


class TelegramReportsHandler(Handler):
    """Telegram Reports Handler"""

    def filter(self, record: LogRecord) -> bool:
        result = super().filter(record)
        return (
            result
            and bool(bot.reports_bot.token and bot.reports_bot.token != bot.dummy_bot.token)
            and bool(bot.reports_chat_id > 0)
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
