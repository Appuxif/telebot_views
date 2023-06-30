from datetime import timedelta
from logging import getLogger

from telebot.asyncio_helper import ApiTelegramException
from telebot.types import ChatMemberAdministrator, ChatMemberMember, ChatMemberOwner, ChatMemberRestricted

from telebot_views import bot
from telebot_views.models.cache import CacheModel
from telebot_views.services.chats import get_chat
from telebot_views.utils import now_utc

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
    cache = await CacheModel.manager().by_key(cache_key).is_valid().find_one(raise_exception=False)

    if cache:
        logger.debug('Got cache for key `%s`', cache_key)
    else:
        logger.debug('Cache for key `%s` not found', cache_key)

    if force:
        logger.debug('Forcing subscription checking for `%s`', cache_key)

    if not cache or force:
        cache = cache or CacheModel(key=cache_key)

        subscription_result = await check_subscription(chat_id, user_id)
        data = {'subscription_result': subscription_result}

        if not subscription_result:
            chat = await get_chat(chat_id)
            data['chat_title'] = chat.title
            data['chat_username'] = chat.username

        cache.data = data
        cache.valid_until = now_utc() + timedelta(minutes=5)
        await cache.update(upsert=True)

    subscription_result = cache.data['subscription_result']
    if not subscription_result:
        chat_title = cache.data['chat_title']
        chat_username = cache.data['chat_username']
        await bot.bot.send_message(
            user_id,
            f'⛔ Чтобы продолжить, нужно подписаться на канал:\n{chat_title}\n@{chat_username}',
        )

    return subscription_result
