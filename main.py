import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TELEGRAM_TOKEN
from handlers import register_handlers
from admin import register_admin_handlers
from database import init_db

# Настройка логирования
logging.basicConfig(level=logging.INFO, filename="bot.log", filemode="a",
                    format="%(asctime)s - %(levelname)s - %(message)s")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    init_db()
    
    # Регистрация обработчиков
    register_handlers(dp)
    register_admin_handlers(dp)
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
