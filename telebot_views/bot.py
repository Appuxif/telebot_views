from enum import Enum

from telebot.async_telebot import AsyncTeleBot

bot: AsyncTeleBot = AsyncTeleBot('dummy_token')


class ParseMode(str, Enum):
    """Parse Mode Enum"""

    NONE = ''
    MARKDOWN = 'Markdown'
    HTML = 'HTML'
    MARKDOWN_V2 = 'MarkdownV2'
