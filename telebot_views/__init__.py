from logging import getLogger
from typing import Optional

from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, Message

from telebot_views import bot
from telebot_views.base import Request, Route, RouteResolver
from telebot_views.dispatcher import ViewDispatcher
from telebot_views.dummy import DummyView

logger = getLogger('telebot_views')


def set_bot(tele_bot: AsyncTeleBot):
    bot.bot = tele_bot


def set_reports_bot(tele_bot: AsyncTeleBot, reports_chat_id: int):
    bot.reports_bot = tele_bot
    bot.reports_chat_id = reports_chat_id


def init(
    tele_bot: AsyncTeleBot,
    routes: list[Route],
    skip_non_private: bool = False,
    reports_bot: Optional[AsyncTeleBot] = bot.reports_bot,
    reports_chat_id: int = bot.reports_chat_id,
):
    set_bot(tele_bot)
    set_reports_bot(reports_bot, reports_chat_id)

    for route in routes + [Route(DummyView)]:
        RouteResolver.register_route(route)

    @tele_bot.message_handler()
    async def message_handler(msg: Message):
        try:
            if skip_non_private and msg.chat.type != 'private':
                return
            if msg.from_user.id == tele_bot.token.split(':', 1)[0]:
                return

            request = Request(msg=msg)
            await ViewDispatcher(request=request).dispatch()
        except Exception:
            logger.exception('message_handler error')
            raise

    @tele_bot.callback_query_handler(func=lambda call: True)
    async def callback_query(callback: CallbackQuery):
        try:
            if skip_non_private and callback.message.chat.type != 'private':
                return

            request = Request(callback=callback)
            await ViewDispatcher(request=request).dispatch()
        except Exception:
            logger.exception('callback_query error')
            raise
