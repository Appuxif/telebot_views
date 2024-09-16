from enum import Enum
from typing import Any, Union

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

dummy_bot: AsyncTeleBot = AsyncTeleBot('0:dummy_token')
bot: AsyncTeleBot = dummy_bot
reports_bot: AsyncTeleBot = dummy_bot
reports_chat_id: Union[str, int] = 0


async def bot_answer_message(msg: Message, text: str, **kwargs: Any) -> Message:
    kwargs.setdefault('business_connection_id', msg.business_connection_id)
    return await bot.send_message(msg.chat.id, text, **kwargs)


class ParseMode(str, Enum):
    """Parse Mode Enum"""

    NONE = ''
    MARKDOWN = 'Markdown'
    HTML = 'HTML'
    MARKDOWN_V2 = 'MarkdownV2'
