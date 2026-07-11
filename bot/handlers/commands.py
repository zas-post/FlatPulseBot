from aiogram import Router, html, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramBadRequest
from config.settings import FAMILY_CHAT_ID
from bot.instance import bot

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 {html.bold('FlatPulseBot')} успешно запущен!\n\n"
        f"🎯 Фильтры Питера активны.\n"
        f"🚀 Кнопка «⭐️ В семейный чат» добавлена и готова к работе."
    )


# Хэндлер удаления сообщения
@router.callback_query(F.data == "delete_msg")
async def process_delete_message(callback: CallbackQuery):
    try:
        await callback.message.delete()
        await callback.answer("Сообщение удалено")
    except TelegramBadRequest as e:
        if "query is too old" in e.message:
            # Если клик устарел, просто молча удаляем сообщение, не забивая логи
            try:
                await callback.message.delete()
            except Exception:
                pass
        else:
            await callback.answer(
                "Не удалось удалить старое сообщение (старше 48 часов)", show_alert=True
            )
    except Exception:
        pass


# Пересылка квартиры в общий семейный чат
@router.callback_query(F.data == "share_family")
async def process_share_family(callback: CallbackQuery):
    if not FAMILY_CHAT_ID:
        try:
            await callback.answer(
                "Ошибка: ID семейного чата не настроен в .env!", show_alert=True
            )
        except TelegramBadRequest:
            pass
        return

    avito_url = None
    if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
        for row in callback.message.reply_markup.inline_keyboard:
            for button in row:
                if button.url:
                    avito_url = button.url
                    break

    user_name = callback.from_user.first_name

    group_msg = (
        f"⭐️ <b>{user_name} предлагает вариант:</b>\n\n"
        f"{callback.message.text}\n\n"
        f"🔗 <a href='{avito_url}'>Смотреть объявление на Авито</a>"
        if avito_url
        else callback.message.text
    )

    try:
        await bot.send_message(
            chat_id=FAMILY_CHAT_ID, text=group_msg, parse_mode="HTML"
        )

        updated_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    (
                        InlineKeyboardButton(text="🔗 На Авито", url=avito_url)
                        if avito_url
                        else InlineKeyboardButton(
                            text="🔗 На Авито", callback_data="none"
                        )
                    ),
                    InlineKeyboardButton(text="❌ Удалить", callback_data="delete_msg"),
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Отправлено в чат семьи", callback_data="already_shared"
                    )
                ],
            ]
        )

        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
        await callback.answer("Отправлено в семейный чат!")

    except TelegramBadRequest as e:
        # Если клик устарел при отправке, мы не упадем
        logging.warning(
            f"[Bot] Не удалось ответить на устаревший callback: {e.message}"
        )
    except Exception as e:
        try:
            await callback.answer(
                f"Не удалось отправить в группу. Проверь, есть ли бот в чате.",
                show_alert=True,
            )
        except TelegramBadRequest:
            pass


@router.callback_query(F.data == "already_shared")
async def process_already_shared(callback: CallbackQuery):
    try:
        await callback.answer(
            "Этот вариант уже находится в семейном чате!", show_alert=False
        )
    except TelegramBadRequest:
        pass
