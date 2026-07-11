import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from config.settings import FAMILY_CHAT_ID
from bot.instance import bot

# Инициализируем роутер, чтобы run.py мог его импортировать
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

    # 1. Извлекаем оригинальный текст с форматированием
    original_text = callback.message.html_text

    # 2. Ищем ссылку на квартиру в кнопках
    source_url = None
    if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
        for row in callback.message.reply_markup.inline_keyboard:
            for button in row:
                if button.url and ("На" in button.text or "🔗" in button.text):
                    source_url = button.url
                    break

    # 3. Добавляем ссылку в текст для пересылки
    if source_url:
        share_text = f"📢 <b>Выбор Александра:</b>\n\n{original_text}\n\n🔗 <a href='{source_url}'>Посмотреть объявление на сайте</a>"
    else:
        share_text = f"📢 <b>Выбор Александра:</b>\n\n{original_text}"

    try:
        await bot.send_message(
            chat_id=FAMILY_CHAT_ID,
            text=share_text,
            parse_mode="HTML",
            disable_web_page_preview=False,  # Позволяет Telegram подтянуть превью (картинку) объявления
        )
        await callback.answer("⭐️ Отправлено в семейный чат!")

    except Exception as e:
        logging.error(f"Ошибка отправки в семейный чат: {e}")
        error_msg = str(e)
        if "chat not found" in error_msg.lower():
            await callback.message.answer(
                "❌ <b>Ошибка отправки:</b> Бот не нашел семейный чат! Проверь .env и права бота.",
                parse_mode="HTML",
            )
        else:
            await callback.message.answer(f"❌ Ошибка отправки: {error_msg}")

        await callback.answer("Ошибка отправки", show_alert=False)
