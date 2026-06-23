from sqlalchemy import select, func
from datetime import datetime
from database.core import async_session
from database.models import User, WorkoutProgram, ExerciseLog

async def get_or_create_user(telegram_id: int, username: str):
    """Находит пользователя или создает нового"""
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

async def get_user_program(user_id: int):
    """Достает программу тренировок пользователя из БД"""
    async with async_session() as session:
        stmt = select(WorkoutProgram).where(WorkoutProgram.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def save_program(user_id: int, split_name: str, days: str):
    """Сохраняет или обновляет программу пользователя"""
    async with async_session() as session:
        # Проверяем, есть ли уже программа у этого юзера
        stmt = select(WorkoutProgram).where(WorkoutProgram.user_id == user_id)
        result = await session.execute(stmt)
        program = result.scalar_one_or_none()

        if program:
            # Обновляем старую
            program.name = split_name
            program.days = days
        else:
            # Создаем новую
            program = WorkoutProgram(user_id=user_id, name=split_name, days=days)
            session.add(program)

        await session.commit()

async def save_exercise_set(user_id: int, exercise_name: str, set_number: int, weight: float, reps: int):
    """Сохраняет один подход упражнения в базу"""
    async with async_session() as session:
        log = ExerciseLog(
            user_id=user_id,
            exercise_name=exercise_name,
            set_number=set_number,
            weight=weight,
            reps=reps
        )
        session.add(log)
        await session.commit()

async def get_todays_exercises(user_id: int):
    """Получает список всех подходов пользователя за сегодняшний день"""
    async with async_session() as session:
        # func.date отсекает время и оставляет только год-месяц-день
        stmt = select(ExerciseLog).where(
            ExerciseLog.user_id == user_id,
            func.date(ExerciseLog.date) == func.date(datetime.utcnow())
        ).order_by(ExerciseLog.id) # Сортируем по порядку добавления

        result = await session.execute(stmt)
        return result.scalars().all()