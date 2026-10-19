"""Shop revenue bot: run with `uv run shop-revenue-bot`."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from .bot import make_router
from .config import load_config
from .db import SalesDB


async def run() -> None:
    config = load_config()
    db = SalesDB(config.db_path, config.tz)
    bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(make_router(db))
    await bot.set_my_commands([
        BotCommand(command="today", description="Виручка за сьогодні"),
        BotCommand(command="week", description="Звіт за 7 днів"),
        BotCommand(command="excel", description="Вивантажити в Excel"),
        BotCommand(command="undo", description="Скасувати останній продаж"),
        BotCommand(command="help", description="Як користуватися"),
    ])
    me = await bot.get_me()
    logging.info("Bot @%s is running", me.username)
    await dp.start_polling(bot)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run())
