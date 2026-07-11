import asyncio
import logging
import sys

from config.settings import TARGET_AVITO_URL, AVITO_CHECK_INTERVAL, ADMIN_IDS
from database.connection import init_db, filter_new_listings
from scrapers.avito import AvitoScraper
from bot.instance import bot, dp
from bot.middlewares.auth import AuthMiddleware
from bot.handlers.commands import router as commands_router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка хэндлеров логирования
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler("errors.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.ERROR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[stdout_handler, file_handler],
)


async def avito_parser_worker():
    """Фоновый воркер для периодического парсинга Авито с рассылкой по семье"""
    scraper = AvitoScraper()

    while True:
        if TARGET_AVITO_URL:
            logging.info("[Worker] Запуск плановой проверки Авито...")
            try:
                raw_listings = await asyncio.to_thread(scraper.parse, TARGET_AVITO_URL)

                if raw_listings:
                    new_items = filter_new_listings(raw_listings, source="avito")

                    if new_items:
                        logging.info(
                            f"[Worker] Найдено {len(new_items)} новых объявлений!"
                        )
                        for item in new_items:
                            msg = (
                                f"🔥 <b>{item['title']}</b>\n"
                                f"💰 Цена: {item['price']} руб."
                            )

                            # Красивая сетка кнопок
                            keyboard = InlineKeyboardMarkup(
                                inline_keyboard=[
                                    [
                                        InlineKeyboardButton(
                                            text="🔗 На Авито", url=item["url"]
                                        ),
                                        InlineKeyboardButton(
                                            text="❌ Удалить",
                                            callback_data="delete_msg",
                                        ),
                                    ],
                                    [
                                        InlineKeyboardButton(
                                            text="⭐️ В семейный чат",
                                            callback_data="share_family",
                                        )
                                    ],
                                ]
                            )

                            # Рассылаем каждому члену семьи лично
                            for user_id in ADMIN_IDS:
                                try:
                                    await bot.send_message(
                                        chat_id=user_id,
                                        text=msg,
                                        parse_mode="HTML",
                                        reply_markup=keyboard,
                                    )
                                except TelegramForbiddenError:
                                    logging.warning(
                                        f"[Worker] Пользователь {user_id} заблокировал бота."
                                    )
                                except Exception as e:
                                    logging.error(
                                        f"[Worker] Ошибка отправки пользователю {user_id}: {e}"
                                    )
                    else:
                        logging.info("[Worker] Новых объявлений не найдено.")
            except Exception as e:
                logging.error(f"[Worker] Критическая ошибка в воркере Авито: {e}")

        await asyncio.sleep(AVITO_CHECK_INTERVAL)


async def main():
    # 1. Инициализация Базы Данных
    init_db()

    # 2. Регистрация кастомных Middleware для безопасности
    dp.message.middleware(AuthMiddleware())

    # 3. Подключение обработчиков команд
    dp.include_router(commands_router)

    # 4. Запуск фоновых задач
    asyncio.create_task(avito_parser_worker())

    # 5. Старт лонг-поллинга бота
    logging.info("Запуск лонг-поллинга Telegram бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Приложение остановлено пользователем.")
