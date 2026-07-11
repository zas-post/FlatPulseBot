import logging  # 🔥 Добавили пропущенный импорт
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from config.settings import FAMILY_CHAT_ID, ADMIN_IDS
from bot.instance import bot

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я твой бронированный поисковик квартир.\n"
        "Я работаю в фоне на сервере и буду присылать сюда новые варианты с Авито и Циан."
    )


@router.message(Command("status"))
async def cmd_status(message: Message):
    await message.answer("🤖 Бот работает в штатном режиме, фоновые воркеры активны.")


@router.callback_query(F.data == "delete_msg")
async def process_delete_msg(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.answer("Удалено")
    except Exception as e:
        logging.error(f"Ошибка удаления сообщения: {e}")
        await callback.answer("Не удалось удалить", show_alert=True)


@router.callback_query(F.data == "share_family")
async def process_share_family(callback: CallbackQuery):
    if not FAMILY_CHAT_ID:
        await callback.answer("⚠️ В .env не настроен FAMILY_CHAT_ID!", show_alert=True)
        return

    # Извлекаем текст объявления без лишних кнопок
    original_text = callback.message.text or callback.message.html_text

    try:
        # Отправляем в семейный чат
        await bot.send_message(
            chat_id=FAMILY_CHAT_ID,
            text=f"📢 <b>Выбор Александра:</b>\n\n{original_text}",
            parse_mode="HTML",
        )
        await callback.answer("⭐️ Отправлено в семейный чат!")

    except Exception as e:
        # Теперь logging импортирован и код тут не упадет!
        logging.error(f"Ошибка отправки в семейный чат: {e}")

        # Выводим человеческую подсказку вместо падения
        error_msg = str(e)
        if "chat not found" in error_msg.lower():
            await callback.message.answer(
                "❌ <b>Ошибка отправки:</b> Бот не нашел семейный чат!\n"
                "1. Проверь FAMILY_CHAT_ID в файле <code>.env</code> на сервере.\n"
                "2. <b>Обязательно</b> добавь этого бота в твой семейный чат как участника!",
                parse_mode="HTML",
            )
        else:
            await callback.message.answer(f"❌ Ошибка отправки: {error_msg}")

        await callback.answer("Ошибка отправки", show_alert=False)
