from telebot.types import InlineKeyboardButton, InlineQueryResultBase

from telebot_views.base import BaseMessageSender, BaseView, InlineQueryResultSender, Route, UserStatesManager


class DummyMessageSender(BaseMessageSender):
    """Dummy Message Sender"""

    async def get_keyboard(self) -> list[list[InlineKeyboardButton]]:
        return []

    async def get_keyboard_text(self) -> str:
        return ''


class DummyInlineQueryResultSender(InlineQueryResultSender):
    async def get_results(self) -> tuple[list[InlineQueryResultBase], str | None]:
        return [], None


class DummyUserStatesManager(UserStatesManager):
    """Dummy User States Manager"""

    async def init(self):
        user = await self.view.request.get_user()
        self.next_user_state = user.state


class DummyView(BaseView):
    """Отображение-заглушка"""

    view_name = 'DUMMY'
    edit_keyboard = False

    message_sender = DummyMessageSender
    user_states_manager = DummyUserStatesManager
    inline_sender = DummyInlineQueryResultSender

    async def dispatch(self) -> Route:
        await super().dispatch()
        user = await self.request.get_user()
        return self.route_resolver.routes_registry[user.state.view_name]
