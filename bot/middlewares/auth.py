# Заменяем класс AuthMiddleware на этот вариант:
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from config.settings import ADMIN_IDS


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if (
                event.from_user.id not in ADMIN_IDS
            ):  # Теперь проверяем по всему списку семьи
                await event.answer("Доступ заблокирован. Этот бот приватный.")
                return
        return await handler(event, data)
