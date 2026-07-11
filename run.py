import asyncio
import logging
import sys
import random

from config.settings import (
    TARGET_AVITO_URL,
    AVITO_CHECK_INTERVAL,
    TARGET_CYAN_URL,
    CYAN_CHECK_INTERVAL,
    ADMIN_IDS,
)
from database.connection import init_db, filter_new_listings
from scrapers.avito import AvitoScraper
from scrapers.cyan import CyanScraper
from bot.instance import bot, dp
from bot.middlewares.auth import AuthMiddleware
from bot.handlers.commands import router as commands_router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логов
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
    """Фоновый воркер для периодического парсинга Авито со случайным интервалом"""
    scraper = AvitoScraper()
    while True:
        if TARGET_AVITO_URL:
            logging.info("[Worker] Запуск плановой проверки Авито...")
            for attempt in range(1, 4):
                try:
                    raw_listings = await asyncio.to_thread(
                        scraper.parse, TARGET_AVITO_URL
                    )
                    if raw_listings:
                        new_items = filter_new_listings(raw_listings, source="avito")
                        if new_items:
                            logging.info(
                                f"[Worker] Авито: найдено {len(new_items)} новых объявлений!"
                            )
                            for item in new_items:
                                msg = f"🔥 <b>[Авито] {item['title']}</b>\n💰 Цена: {item['price']} руб."
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
                                for user_id in ADMIN_IDS:
                                    try:
                                        await bot.send_message(
                                            chat_id=user_id,
                                            text=msg,
                                            parse_mode="HTML",
                                            reply_markup=keyboard,
                                        )
                                    except TelegramForbiddenError:
                                        pass
                                    except Exception as e:
                                        logging.error(
                                            f"[Worker] Ошибка отправки Авито пользователю {user_id}: {e}"
                                        )
                        else:
                            logging.info("[Worker] Авито: новых объявлений не найдено.")
                    break
                except Exception as e:
                    logging.error(f"[Worker] Авито: Ошибка на попытке {attempt}: {e}")
                    if attempt < 3:
                        await asyncio.sleep(10)

        avito_sleep = AVITO_CHECK_INTERVAL + random.randint(-120, 120)
        avito_sleep = max(60, avito_sleep)
        logging.info(
            f"[Worker] Авито уходит в сон на {avito_sleep} сек (~{round(avito_sleep/60, 1)} min)..."
        )
        await asyncio.sleep(avito_sleep)


async def cyan_parser_worker():
    """Фоновый воркер для периодического парсинга Циан со случайным интервалом"""
    # 🔥 ОПТИМИЗАЦИЯ: Даем Авито 15 секунд, чтобы захватить драйвер первым при холодном старте контейнера
    logging.info("[Worker] Ожидание разделения потоков на старте для Циан...")
    await asyncio.sleep(15)

    scraper = CyanScraper()
    while True:
        if TARGET_CYAN_URL:
            logging.info("[Worker] Запуск плановой проверки Циан...")
            for attempt in range(1, 4):
                try:
                    raw_listings = await asyncio.to_thread(
                        scraper.parse, TARGET_CYAN_URL
                    )
                    if raw_listings:
                        new_items = filter_new_listings(raw_listings, source="cyan")
                        if new_items:
                            logging.info(
                                f"[Worker] Циан: найдено {len(new_items)} новых объявлений!"
                            )
                            for item in new_items:
                                msg = f"🔷 <b>[Циан] {item['title']}</b>\n💰 Цена: {item['price']} руб."
                                keyboard = InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [
                                            InlineKeyboardButton(
                                                text="🔗 На Циан", url=item["url"]
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
                                for user_id in ADMIN_IDS:
                                    try:
                                        await bot.send_message(
                                            chat_id=user_id,
                                            text=msg,
                                            parse_mode="HTML",
                                            reply_markup=keyboard,
                                        )
                                    except TelegramForbiddenError:
                                        pass
                                    except Exception as e:
                                        logging.error(
                                            f"[Worker] Ошибка отправки Циан пользователю {user_id}: {e}"
                                        )
                        else:
                            logging.info("[Worker] Циан: новых объявлений не найдено.")
                    break
                except Exception as e:
                    logging.error(f"[Worker] Циан: Ошибка на попытке {attempt}: {e}")
                    if attempt < 3:
                        logging.info(
                            "[Worker] Ожидание 10 секунд перед повторной попыткой Циан..."
                        )
                        await asyncio.sleep(10)

        cyan_sleep = CYAN_CHECK_INTERVAL + random.randint(-120, 120)
        cyan_sleep = max(60, cyan_sleep)
        logging.info(
            f"[Worker] Циан уходит в сон на {cyan_sleep} сек (~{round(cyan_sleep/60, 1)} min)..."
        )
        await asyncio.sleep(cyan_sleep)


async def main():
    init_db()
    dp.message.middleware(AuthMiddleware())
    dp.include_router(commands_router)

    asyncio.create_task(avito_parser_worker())
    asyncio.create_task(cyan_parser_worker())

    logging.info("Запуск лонг-поллинга Telegram бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Приложение остановлено пользователем.")
