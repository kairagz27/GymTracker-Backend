from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Создаем файл базы данных прямо в папке проекта
DATABASE_URL = "sqlite+aiosqlite:///gym_bot.db"

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика сессий для запросов к БД
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для всех таблиц
class Base(DeclarativeBase):
    pass

async def init_db():
    """Создает все таблицы, если их еще нет"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)