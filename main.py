import asyncio
import os

from dotenv import load_dotenv

from database import Database
from telegram import PatientBot
from logger import logger

load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')

async def main():
    logger.info('Запуск приложения')
    db = Database()
    await db.init_db()
    bot = PatientBot(API_TOKEN, db)
    await bot._start()

if __name__ == '__main__':
    asyncio.run(main())