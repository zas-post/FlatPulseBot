import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config.settings import FAMILY_CHAT_ID
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
    """🔥 ЮЗАБИЛИТИ: Сворачивает карточку в красивую информативную строку с кнопкой восстановления"""
    try:
        old_html = callback.message.html_text or ""
        old_text = callback.message.text or ""

        # Определяем источник
        source = "Авито" if "Авито" in old_text else "Циан"

        # Извлекаем заголовок объекта (количество комнат и площадь) из третьей строки сообщения
        title = "Объект"
        price = "Цена по запросу"

        lines = old_text.split("\n")
        for line in lines:
            if "Объект:" in line:
                title = line.replace("Объект:", "").strip()
            if "Стоимость:" in line:
                price = line.replace("Стоимость:", "").strip()

        # Формируем компактный, но очень читаемый текст
        archived_text = (
            f"⚪️ <b>Объявление скрыто</b> (<i>{source} / {title} / {price}</i>)"
        )

        # Прячем старый HTML-текст прямо в callback_data кнопки восстановления!
        # Telegram ограничивает callback_data до 64 байт, поэтому весь текст туда не влезет.
        # Чтобы обойти это ограничение без баз данных, мы оставим оригинальный URL в кнопке,
        # изменив разметку, либо сделаем чистый инлайн-переключатель.

        # Самый надежный способ вернуть всё назад: извлекаем URL из первой кнопки старой клавиатуры
        original_url = ""
        if (
            callback.message.reply_markup
            and callback.message.reply_markup.inline_keyboard
        ):
            original_url = callback.message.reply_markup.inline_keyboard[0][0].url

        # Создаем кнопку «Восстановить», в которую зашьем только источник и цену, чтобы не перегрузить лимит
        inline_back = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    (
                        InlineKeyboardButton(text="🔗 Ссылка", url=original_url)
                        if original_url
                        else InlineKeyboardButton(
                            text="🚫 Нет ссылки", callback_data="none"
                        )
                    ),
                    InlineKeyboardButton(
                        text="↩️ Восстановить текст",
                        callback_data=f"restore_{source.lower()}",
                    ),
                ]
            ]
        )

        await callback.message.edit_text(
            text=archived_text, parse_mode="HTML", reply_markup=inline_back
        )
        await callback.answer("Объявление свернуто")
    except Exception as e:
        logging.error(f"[Bot] Ошибка архивации сообщения: {e}")
        await callback.answer()


@router.callback_query(F.data.startswith("restore_"))
async def restore_msg_callback(callback: CallbackQuery):
    """🔥 ЮЗАБИЛИТИ: Восстанавливает стандартный шаблон сообщения, если скрыли случайно"""
    try:
        # Из callback_data понимаем, какой это был источник
        source_type = callback.data.split("_")[1]
        source_title = "Новое на Авито" if source_type == "avito" else "Новое на Циан"
        emoji = "🟢" if source_type == "avito" else "🔷"

        # Вытаскиваем параметры из нашей же свернутой строчки
        current_text = callback.message.text or ""
        # Строка выглядит так: "Объявление скрыто (Авито / 2-к. квартира, 54 м² / 6 500 000 ₽)"
        try:
            parts = current_text.split("/")
            title = parts[1].strip()
            price = parts[2].replace(")", "").strip()
        except Exception:
            title = "Квартира"
            price = "Цена по запросу"

        # Извлекаем ссылку обратно из кнопки, которая сейчас на экране
        original_url = ""
        if (
            callback.message.reply_markup
            and callback.message.reply_markup.inline_keyboard
        ):
            original_url = callback.message.reply_markup.inline_keyboard[0][0].url

        # Собираем исходный красивый шаблон обратно
        restored_text = (
            f"{emoji} <b>[{source_title}]</b>\n"
            f"───────────────────\n"
            f"🏢 <b>Объект:</b> {title}\n"
            f"💰 <b>Стоимость:</b> <code>{price}</code>\n"
            f"───────────────────\n"
            f"🧭 <i>Статус: Восстановлено из архива</i>"
        )

        # Возвращаем стандартную клавиатуру управления
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🔗 На {source_title.split()[-1]}", url=original_url
                    ),
                    InlineKeyboardButton(text="❌ Удалить", callback_data="delete_msg"),
                ],
                [
                    InlineKeyboardButton(
                        text="⭐️ В семейный чат", callback_data="share_family"
                    )
                ],
            ]
        )

        await callback.message.edit_text(
            text=restored_text, parse_mode="HTML", reply_markup=keyboard
        )
        await callback.answer("Объявление восстановлено")
    except Exception as e:
        logging.error(f"[Bot] Ошибка восстановления сообщения: {e}")
        await callback.answer(
            "Не удалось полностью восстановить текст", show_alert=True
        )


@router.callback_query(F.data == "share_family")
async def share_family_callback(callback: CallbackQuery):
    """Пересылка выбранного объявления в семейный чат"""
    if not FAMILY_CHAT_ID:
        await callback.answer("⚠️ Семейный чат не настроен в .env!", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=FAMILY_CHAT_ID, text=callback.message.html_text, parse_mode="HTML"
        )
        await callback.answer("⭐️ Успешно отправлено в семейный чат!")
    except Exception as e:
        logging.error(f"[Bot] Ошибка пересылки в семейный чат: {e}")
        await callback.answer("❌ Не удалось переслать сообщение", show_alert=True)
