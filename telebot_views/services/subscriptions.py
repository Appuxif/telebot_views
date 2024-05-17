from logging import getLogger

from telebot.asyncio_helper import ApiTelegramException
from telebot.types import ChatMemberAdministrator, ChatMemberMember, ChatMemberOwner, ChatMemberRestricted

from telebot_views import bot
from telebot_views.models.cache import with_cache
from telebot_views.services.chats import get_chat

logger = getLogger(__name__)


async def check_subscription(chat_id: int, user_id: int) -> bool:
    """Проверяет подписку пользователя на канал"""

    try:
        member = await bot.bot.get_chat_member(chat_id, user_id)
        if isinstance(member, (ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember)):
            result = True
            reason = 'He is member: '
        elif isinstance(member, ChatMemberRestricted) and member.is_member:
            result = True
            reason = 'He is restricted member: '
        else:
            result = False
            reason = 'He is unexpected member: '
        reason += member.__class__.__name__
    except ApiTelegramException as err:
        result = False
        reason = str(err.description)

    logger.debug('Check subscription for user: %s\nresult: %s\nreason: %s', user_id, result, reason)
    return result


async def ensure_subscription(chat_id: int, user_id: int, force: bool = False) -> bool:
    """Проверяет подписку пользователя на канал в кэше.
    Если валидный кэш отсутствует, то записывает результат в кэш.

    Если подписки нет, то отправляет уведомление с необходимостью подписаться на канал.
    """

    cache_key = f'chat:{chat_id}:user:{user_id}:sub'

    @with_cache(cache_key, 60 * 5, force=force)
    async def _inner() -> dict[str, bool]:
        subscription_result = await check_subscription(chat_id, user_id)
        result = {'subscription_result': subscription_result}
        if not subscription_result:
            chat = await get_chat(chat_id)
            result['chat_title'] = chat.title
            result['chat_username'] = chat.username
        return result

    data = await _inner()

    if not data['subscription_result']:
        chat_title = data['chat_title']
        chat_username = data['chat_username']
        await bot.bot.send_message(
            user_id,
            f'⛔ Чтобы продолжить, нужно подписаться на канал:\n{chat_title}\n@{chat_username}',
        )

    return data['subscription_result']
