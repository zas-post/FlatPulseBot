# bot/instance.py
from aiogram import Bot, Dispatcher
from config.settings import TELEGRAM_TOKEN

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
