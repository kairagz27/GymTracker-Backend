import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from handlers.start import router as start_router
from handlers.program_setup import router as program_router

# 1. ДОБАВЛЯЕМ ИМПОРТ НОВОГО РОУТЕРА
from handlers.workout_entry import router as workout_router

from database.core import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(program_router)

    # 2. ПОДКЛЮЧАЕМ ЕГО К ДИСПЕТЧЕРУ
    dp.include_router(workout_router)

    await init_db()

    print("Бот успешно запущен и готов к работе! 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")