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
        old_text = callback.message.text or ""
        source = "Авито" if "Авито" in old_text else "Циан"

        title = "Объект"
        price = "Цена по запросу"

        lines = old_text.split("\n")
        for line in lines:
            if "Объект:" in line:
                title = line.replace("Объект:", "").strip()
            if "Стоимость:" in line:
                price = line.replace("Стоимость:", "").strip()

        archived_text = (
            f"⚪️ <b>Объявление скрыто</b> (<i>{source} / {title} / {price}</i>)"
        )

        # Вытаскиваем оригинальную ссылку из кнопки "На Авито/Циан"
        original_url = ""
        if (
            callback.message.reply_markup
            and callback.message.reply_markup.inline_keyboard
        ):
            original_url = callback.message.reply_markup.inline_keyboard[0][0].url

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
        source_type = callback.data.split("_")[1]
        source_title = "Новое на Авито" if source_type == "avito" else "Новое на Циан"
        emoji = "🟢" if source_type == "avito" else "🔷"

        current_text = callback.message.text or ""
        try:
            parts = current_text.split("/")
            title = parts[1].strip()
            price = parts[2].replace(")", "").strip()
        except Exception:
            title = "Квартира"
            price = "Цена по запросу"

        original_url = ""
        if (
            callback.message.reply_markup
            and callback.message.reply_markup.inline_keyboard
        ):
            original_url = callback.message.reply_markup.inline_keyboard[0][0].url

        restored_text = (
            f"{emoji} <b>[{source_title}]</b>\n"
            f"───────────────────\n"
            f"🏢 <b>Объект:</b> {title}\n"
            f"💰 <b>Стоимость:</b> <code>{price}</code>\n"
            f"───────────────────\n"
            f"🧭 <i>Статус: Доступно для связи</i>"
        )

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
    """⭐️ ИСПРАВЛЕНО БЕЗ ИЗМЕНЕНИЯ СТРУКТУРЫ: Полная стабильная отправка сообщения со всеми ссылками"""
    if not FAMILY_CHAT_ID:
        await callback.answer("⚠️ Семейный чат не настроен в .env!", show_alert=True)
        return

    try:
        # Берём исходный HTML текст сообщения ОДНОЙ строкой (сохраняем регулярку площади на 100%)
        html_text = callback.message.html_text

        # Извлекаем ссылку на Авито/Циан из первой кнопки
        original_url = ""
        if (
            callback.message.reply_markup
            and callback.message.reply_markup.inline_keyboard
        ):
            original_url = callback.message.reply_markup.inline_keyboard[0][0].url

        # Ничего не режем и не сплитим! Просто добавляем ссылку новой строкой вниз
        if original_url:
            source_name = "Авито" if "Авито" in html_text else "Циан"
            html_text += (
                f"\n🔗 <b><a href='{original_url}'>Посмотреть на {source_name}</a></b>"
            )

        await bot.send_message(
            chat_id=FAMILY_CHAT_ID,
            text=html_text,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
        await callback.answer("⭐️ Успешно отправлено в семейный чат!")
    except Exception as e:
        logging.error(f"[Bot] Ошибка пересылки в семейный чат: {e}")
        await callback.answer("❌ Не удалось переслать сообщение", show_alert=True)
