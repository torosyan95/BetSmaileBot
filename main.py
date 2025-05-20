import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TELEGRAM_TOKEN
from handlers import register_handlers
from admin import register_admin_handlers
from database import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    filename="bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting bot...")
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Инициализация базы данных
    init_db()
    logger.info("Database initialized")
    
    # Регистрация обработчиков
    register_handlers(dp)
    register_admin_handlers(dp)
    logger.info("Handlers registered")
    
    # Проверка подключения
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot connected successfully: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to connect to Telegram API: {e}")
        return
    
    # Запуск бота
    logger.info("Starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
