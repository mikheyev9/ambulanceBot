from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .handlers import register_handlers

class PatientBot:
    def __init__(self, api_token: str, db):
        self.bot = Bot(token=api_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.db = db
        self.register_handlers()

    def register_handlers(self):
        register_handlers(self.dp, self.db)

    async def _start(self):
        await self.dp.start_polling(self.bot)

