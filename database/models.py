from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, Float
from datetime import datetime
from database.core import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkoutProgram(Base):
    __tablename__ = 'workout_programs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=False) # Например: "Push/Pull/Legs"
    days = Column(String, nullable=True)

class ExerciseLog(Base):
    __tablename__ = 'exercise_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    exercise_name = Column(String, nullable=False) # "Жим штанги лежа"
    set_number = Column(Integer, nullable=False)   # Номер подхода (1, 2, 3...)
    weight = Column(Float, nullable=False)         # Вес (например, 62.5)
    reps = Column(Integer, nullable=False)         # Повторения
    date = Column(DateTime, default=datetime.utcnow)

# ... (твои существующие классы User, WorkoutProgram, ExerciseLog оставляем как есть) ...

# Добавляем новые таблицы для структуры программы:
class WorkoutDay(Base):
    __tablename__ = 'workout_days'
    id = Column(Integer, primary_key=True)
    day_name = Column(String, nullable=False) # "Monday", "Wednesday"
    program_id = Column(Integer, ForeignKey('workout_programs.id', ondelete='CASCADE'))

class Exercise(Base):
    __tablename__ = 'exercises'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False) # "Bench press"
    day_id = Column(Integer, ForeignKey('workout_days.id', ondelete='CASCADE'))

class ExerciseSet(Base):
    __tablename__ = 'exercise_sets'
    id = Column(Integer, primary_key=True)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    exercise_id = Column(Integer, ForeignKey('exercises.id', ondelete='CASCADE'))