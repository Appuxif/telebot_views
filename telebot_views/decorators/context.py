from logging import getLogger
from typing import Any, Callable, Coroutine, TypeVar

logger = getLogger(__name__)

R = TypeVar('R')
AsyncFuncType = Callable[..., Coroutine[Any, Any, R]]


def suppress_error_with_log(default: R = '') -> Callable[[AsyncFuncType], AsyncFuncType]:
    def decorator(
        func: AsyncFuncType,
    ) -> AsyncFuncType:
        async def wrapper(*args: Any, **kwargs: Any) -> R:
            try:
                return await func(*args, **kwargs)
            except Exception:  # pylint: disable=broad-except
                logger.exception('Error in `%s`', func.__name__)
            return default

        return wrapper

    return decorator
