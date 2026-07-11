@router.callback_query(F.data == "share_family")
async def process_share_family(callback: CallbackQuery):
    if not FAMILY_CHAT_ID:
        await callback.answer("⚠️ В .env не настроен FAMILY_CHAT_ID!", show_alert=True)
        return

    # 1. Извлекаем оригинальный текст (с сохранением HTML-тегов вроде жирного шрифта)
    original_text = callback.message.html_text

    # 2. 🔥 Находим ссылку на квартиру внутри кнопок исходного сообщения
    source_url = None
    if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
        for row in callback.message.reply_markup.inline_keyboard:
            for button in row:
                # Ищем кнопку, у которой есть URL и текст которой начинается со знака ссылки или слова "На"
                if button.url and ("На" in button.text or "🔗" in button.text):
                    source_url = button.url
                    break

    # 3. Формируем красивый и информативный текст для семьи
    if source_url:
        # Вшиваем ссылку прямо в заголовок или добавляем её отдельной строкой снизу
        share_text = f"📢 <b>Выбор Александра:</b>\n\n{original_text}\n\n🔗 <a href='{source_url}'>Посмотреть объявление на сайте</a>"
    else:
        share_text = f"📢 <b>Выбор Александра:</b>\n\n{original_text}"

    try:
        # Отправляем в семейный чат
        await bot.send_message(
            chat_id=FAMILY_CHAT_ID,
            text=share_text,
            parse_mode="HTML",
            disable_web_page_preview=False,  # 🔥 Разрешаем Telegram показать красивое превью квартиры (картинку с сайта)
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
