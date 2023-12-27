from aiogram.types import Message, InlineKeyboardButton
from aiogram import Bot, Dispatcher
from tools import Settings
import asyncio
from os import getenv
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types, F, Router

router = Router()

class TestingBot():
    def __init__(self):
        self.bot = Bot(token=getenv('TG_TOKEN'), parse_mode=ParseMode.HTML)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp.include_router(router)

    async def Run(self):
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot, allowed_updates=self.dp.resolve_used_update_types())
