from enum import Enum

from telebot.async_telebot import AsyncTeleBot

dummy_bot: AsyncTeleBot = AsyncTeleBot('dummy_token')
bot: AsyncTeleBot = dummy_bot
reports_bot: AsyncTeleBot = dummy_bot
reports_chat_id: int = 0


class ParseMode(str, Enum):
    """Parse Mode Enum"""

    NONE = ''
    MARKDOWN = 'Markdown'
    HTML = 'HTML'
    MARKDOWN_V2 = 'MarkdownV2'
