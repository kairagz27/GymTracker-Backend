from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey,Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import DateTime
from datetime import datetime

# База данных для сервера
SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_u3rPdKtqxZB1@ep-damp-flower-ass3mr26.c-4.eu-central-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    programs = relationship("Program", back_populates="owner")

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # "Upper/Lower Split"
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="programs")
    days = relationship("WorkoutDay", back_populates="program", cascade="all, delete")

class WorkoutDay(Base):
    __tablename__ = "workout_days"
    id = Column(Integer, primary_key=True, index=True)
    day_name = Column(String) # "Monday"
    focus = Column(String, default="")
    program_id = Column(Integer, ForeignKey("programs.id"))
    program = relationship("Program", back_populates="days")
    exercises = relationship("Exercise", back_populates="day", cascade="all, delete")

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # "Bench Press"
    day_id = Column(Integer, ForeignKey("workout_days.id"))
    day = relationship("WorkoutDay", back_populates="exercises")
    sets = relationship("ExerciseSet", back_populates="exercise", cascade="all, delete")

class ExerciseSet(Base):
    __tablename__ = "exercise_sets"
    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float)
    reps = Column(Integer)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    exercise = relationship("Exercise", back_populates="sets")

class WorkoutHistory(Base):
    __tablename__ = "workout_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    day_name = Column(String) # Например, "Push Day"
    date = Column(DateTime, default=datetime.utcnow) # Дата выполнения

    total_volume = Column(Float, default=0.0) # Тоннаж за эту тренировку
    total_sets = Column(Integer, default=0)   # Количество выполненных подходов

class HistoryExercise(Base):
    __tablename__ = "history_exercises"

    id = Column(Integer, primary_key=True, index=True)
    history_id = Column(Integer, ForeignKey("workout_history.id"))
    exercise_name = Column(String)

    # Для поиска рекордов (Personal Records)
    max_weight = Column(Float, default=0.0)
    best_reps = Column(Integer, default=0)
    volume = Column(Float, default=0.0)

class HistorySet(Base):
    __tablename__ = "history_sets"

    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float)
    reps = Column(Integer)
    is_done = Column(Boolean, default=True)

    # Привязываем этот подход к конкретному выполненному упражнению в истории
    exercise_id = Column(Integer, ForeignKey("history_exercises.id"))

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

# 👇 ТА САМАЯ ФУНКЦИЯ ДЛЯ MAIN.PY 👇
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()