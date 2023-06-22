from telebot.async_telebot import AsyncTeleBot
from telebot.types import CallbackQuery, Message

from telebot_views import bot
from telebot_views.base import Request, Route, RouteResolver
from telebot_views.dispatcher import ViewDispatcher
from telebot_views.dummy import DummyView


def set_bot(tele_bot: AsyncTeleBot):
    bot.bot = tele_bot


def init(tele_bot: AsyncTeleBot, routes: list[Route]):
    set_bot(tele_bot)

    for route in routes + [Route(DummyView)]:
        RouteResolver.register_route(route)

    @tele_bot.message_handler()
    async def message_handler(msg: Message):
        request = Request(msg=msg)
        await ViewDispatcher(request=request).dispatch()
        return

    @tele_bot.callback_query_handler(func=lambda call: True)
    async def callback_query(callback: CallbackQuery):
        request = Request(callback=callback)
        await ViewDispatcher(request=request).dispatch()
        return
