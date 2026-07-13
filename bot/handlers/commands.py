import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from config.settings import ADMIN_IDS, FAMILY_CHAT_ID
from bot.instance import bot

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Приветственное сообщение для администратора"""
    await message.answer(
        "👋 <b>Привет! Я твой бот-ассистент Flat Pulse.</b>\n\n"
        "🟢 Я в реальном времени мониторю Авито и Циан.\n"
        "🎯 Фильтр: квартиры строго до 15 минут пешком от метро.\n"
        "⭐️ Понравившиеся варианты ты можешь одной кнопкой отправлять в семейный чат!",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "delete_msg")
async def delete_msg_callback(callback: CallbackQuery):
    """🔥 ЮЗАБИЛИТИ: Вместо удаления полностью сворачивает карточку, сохраняя структуру чата"""
    try:
        old_text = callback.message.text or ""

        # Интеллектуально вытаскиваем источник и цену из старого сообщения для красивого лога
        source = "Авито" if "Авито" in old_text else "Циан"

        price = "Цена по запросу"
        for line in old_text.split("\n"):
            if "Стоимость:" in line:
                price = line.replace("Стоимость:", "").strip()
                break

        archived_text = f"⚪️ <b>Объявление скрыто</b> (<i>{source} / {price}</i>)"

        # Редактируем сообщение: меняем простыню текста на одну строку и убираем кнопки
        await callback.message.edit_text(
            text=archived_text, parse_mode="HTML", reply_markup=None
        )
        await callback.answer("Объявление отправлено в архив")
    except Exception as e:
        logging.error(f"[Bot] Ошибка архивации сообщения: {e}")
        # Если вдруг отредактировать не получилось (например, прошло много времени), просто удаляем
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.answer()


@router.callback_query(F.data == "share_family")
async def share_family_callback(callback: CallbackQuery):
    """Пересылка выбранного объявления в семейный чат"""
    if not FAMILY_CHAT_ID:
        await callback.answer("⚠️ Семейный чат не настроен в .env!", show_alert=True)
        return

    try:
        # Пересылаем копию сообщения с сохранением всего красивого HTML-форматирования
        # Но убираем кнопки управления (удалить/переслать), чтобы в семейном чате они не путались
        await bot.send_message(
            chat_id=FAMILY_CHAT_ID, text=callback.message.html_text, parse_mode="HTML"
        )
        await callback.answer("⭐️ Успешно отправлено в семейный чат!")
    except Exception as e:
        logging.error(f"[Bot] Ошибка пересылки в семейный чат: {e}")
        await callback.answer("❌ Не удалось переслать сообщение", show_alert=True)
