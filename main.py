from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from sqlalchemy import func
from datetime import timedelta, datetime


# Импортируем твои обновленные модели
from fastapi_db import get_db, User, Program, WorkoutDay, Exercise, ExerciseSet,HistorySet
from fastapi_db import WorkoutHistory, HistoryExercise

# --- СХЕМЫ PYDANTIC ---

class ApiSet(BaseModel):
    weight: float
    reps: int

class ApiExercise(BaseModel):
    name: str
    sets: List[ApiSet]

class ApiWorkoutDay(BaseModel):
    day_name: str
    focus: str = ""  # <-- НОВОЕ ПОЛЕ ДЛЯ ПРИЕМА/ОТДАЧИ ФОКУСА
    exercises: List[ApiExercise]

class ProgramCreate(BaseModel):
    telegram_id: int
    program_name: str
    days: List[ApiWorkoutDay]

class ProgramResponse(BaseModel):
    program_name: str
    days: List[ApiWorkoutDay]

class UserProgramsResponse(BaseModel):
    telegram_id: int
    programs: List[ProgramResponse]

# Схемы для сохранения выполненной тренировки
class ApiHistorySet(BaseModel):
    weight: float
    reps: int
    is_done: bool

class ApiHistoryExercise(BaseModel):
    name: str
    sets: List[ApiHistorySet]

class FinishWorkoutRequest(BaseModel):
    telegram_id: int
    day_name: str
    exercises: List[ApiHistoryExercise]

class PRResponse(BaseModel):
    name: str
    result: str
    date: str
    diff: str

class ProgressionData(BaseModel):
    exercise: str
    weights: List[float] = [] # <-- Убедись, что это поле есть!

class HistoryLogItem(BaseModel):
    date: str
    day_name: str
    total_volume: float
    total_sets: int
    exercises: List[str] = []

# Схема для возврата статистики
class StatisticsResponse(BaseModel):
    workouts_logged: int
    current_streak: int
    weekly_volume: float
    total_volume: float
    personal_records: List[PRResponse] = []
    weekly_activity_volume: List[float] = [] # <-- НОВОЕ: Массив тоннажа за 7 дней
    weekly_activity_sets: List[int] = []
    weekly_activity_labels: List[str] = []
    weight_progression: List[ProgressionData] = []


# --- ИНИЦИАЛИЗАЦИЯ ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- ЭНДПОИНТЫ API ---

@app.post("/save_program/")
def save_program(program_data: ProgramCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == program_data.telegram_id).first()
    if not user:
        user = User(telegram_id=program_data.telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    old_program = db.query(Program).filter(Program.user_id == user.id, Program.name == program_data.program_name).first()
    if old_program:
        db.delete(old_program)
        db.commit()

    new_program = Program(user_id=user.id, name=program_data.program_name)
    db.add(new_program)
    db.commit()
    db.refresh(new_program)

    for day in program_data.days:
        # <-- ТЕПЕРЬ ПЕРЕДАЕМ focus ПРИ СОХРАНЕНИИ ДНЯ В БАЗУ
        new_day = WorkoutDay(day_name=day.day_name, focus=day.focus, program_id=new_program.id)
        db.add(new_day)
        db.commit()
        db.refresh(new_day)

        for ex in day.exercises:
            new_ex = Exercise(name=ex.name, day_id=new_day.id)
            db.add(new_ex)
            db.commit()
            db.refresh(new_ex)

            for s in ex.sets:
                new_set = ExerciseSet(weight=s.weight, reps=s.reps, exercise_id=new_ex.id)
                db.add(new_set)
            db.commit()

    return {"message": f"Программа '{program_data.program_name}' успешно сохранена!"}


@app.get("/get_programs/{telegram_id}", response_model=UserProgramsResponse)
def get_programs(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {"telegram_id": telegram_id, "programs": []}

    api_programs = []
    user_programs = db.query(Program).filter(Program.user_id == user.id).all()

    for prog in user_programs:
        api_days = []
        days = db.query(WorkoutDay).filter(WorkoutDay.program_id == prog.id).all()

        for day in days:
            exercises_list = []
            exercises = db.query(Exercise).filter(Exercise.day_id == day.id).all()

            for ex in exercises:
                sets_list = []
                sets = db.query(ExerciseSet).filter(ExerciseSet.exercise_id == ex.id).all()
                for s in sets:
                    sets_list.append({
                        "weight": float(s.weight) if s.weight else 0.0,
                        "reps": int(s.reps) if s.reps else 0
                    })
                exercises_list.append({"name": ex.name, "sets": sets_list})

            # <-- ТЕПЕРЬ ВОЗВРАЩАЕМ focus ОБРАТНО ВО ФРОНТЕНД
            api_days.append({
                "day_name": day.day_name,
                "focus": day.focus,
                "exercises": exercises_list
            })

        api_programs.append({
            "program_name": prog.name,
            "days": api_days
        })

    return {
        "telegram_id": telegram_id,
        "programs": api_programs
    }

@app.post("/finish_workout/")
def finish_workout(data: FinishWorkoutRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == data.telegram_id).first()
    if not user:
        return {"error": "User not found"}

    # Считаем общий тоннаж и подходы за тренировку
    total_vol = 0.0
    total_done_sets = 0

    history_record = WorkoutHistory(user_id=user.id, day_name=data.day_name)
    db.add(history_record)
    db.commit()
    db.refresh(history_record)

    for ex in data.exercises:
        ex_vol = 0.0
        max_w = 0.0
        best_r = 0

        for s in ex.sets:
            if s.is_done: # Учитываем только те подходы, где стоит галочка!
                total_done_sets += 1
                vol = s.weight * s.reps
                ex_vol += vol
                total_vol += vol

                if s.weight > max_w:
                    max_w = s.weight
                    best_r = s.reps

        # Сохраняем упражнение в историю (даже если выполнили 0 подходов, чтобы было)
        if total_done_sets > 0:
            h_ex = HistoryExercise(
                history_id=history_record.id,
                exercise_name=ex.name,
                max_weight=max_w,
                best_reps=best_r,
                volume=ex_vol
            )
            db.add(h_ex)

    # Обновляем общую стату тренировки
    history_record.total_volume = total_vol
    history_record.total_sets = total_done_sets
    db.commit()

    return {"message": "Тренировка успешно завершена и записана в историю!", "volume": total_vol}


@app.get("/get_statistics/{telegram_id}", response_model=StatisticsResponse)
def get_statistics(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return StatisticsResponse(workouts_logged=0, current_streak=0, weekly_volume=0.0, total_volume=0.0)

    workouts_logged = db.query(WorkoutHistory).filter(WorkoutHistory.user_id == user.id).count()
    total_volume = db.query(func.sum(WorkoutHistory.total_volume)).filter(WorkoutHistory.user_id == user.id).scalar() or 0.0

    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    weekly_volume = db.query(func.sum(WorkoutHistory.total_volume)).filter(
        WorkoutHistory.user_id == user.id,
        WorkoutHistory.date >= seven_days_ago
    ).scalar() or 0.0

    current_streak = 1 if workouts_logged > 0 else 0

    # === ВЫЧИСЛЕНИЕ ЛИЧНЫХ РЕКОРДОВ (PR) ===
    history_records = db.query(WorkoutHistory).filter(WorkoutHistory.user_id == user.id).all()

    pr_dict = {}
    for hr in history_records:
        exercises = db.query(HistoryExercise).filter(HistoryExercise.history_id == hr.id).all()
        for ex in exercises:
            if ex.max_weight > 0:
                # Если упражнения еще нет в словаре ИЛИ новый вес больше старого рекорда
                if ex.exercise_name not in pr_dict or ex.max_weight > pr_dict[ex.exercise_name]['weight']:
                    pr_dict[ex.exercise_name] = {
                        'weight': ex.max_weight,
                        'reps': ex.best_reps,
                        'date': hr.date.strftime("%b %d") # Формат "Jun 14"
                    }

    pr_list = []
    for name, data in pr_dict.items():
        # Убираем ".0" если вес целый (например 70.0 -> 70)
        weight_str = f"{int(data['weight'])}" if data['weight'].is_integer() else f"{data['weight']}"
        pr_list.append(PRResponse(
            name=name,
            result=f"{weight_str} kg × {data['reps']}",
            date=data['date'],
            diff="PR 🏆" # Пока ставим красивую заглушку для прогресса
        ))

    # === ВЫЧИСЛЕНИЕ АКТИВНОСТИ ЗА 7 ДНЕЙ ===
    today = datetime.utcnow().date()
    weekly_vol_list = [0.0] * 7
    weekly_sets_list = [0] * 7
    weekly_labels = [""] * 7
    days_map = {0: "M", 1: "T", 2: "W", 3: "T", 4: "F", 5: "S", 6: "S"}

    for i in range(7):
        # Идем от 6 дней назад до сегодня
        target_date = today - timedelta(days=6 - i)
        weekly_labels[i] = days_map[target_date.weekday()] # Вычисляем букву дня

        day_vol = 0.0
        day_sets = 0
        for hr in history_records:
            if hr.date.date() == target_date:
                day_vol += hr.total_volume
                day_sets += hr.total_sets

        weekly_vol_list[i] = day_vol
        weekly_sets_list[i] = day_sets

    # === ЛИНЕЙНЫЙ ГРАФИК ПРОГРЕССИИ (ЗА 8 НЕДЕЛЬ) ===
    target_exercises = ["Bench Press", "Squat", "Deadlift"]
    progression_list = []

    # Находим понедельник текущей недели
    start_of_current_week = today - timedelta(days=today.weekday())

    # Вытаскиваем все упражнения пользователя одним запросом (для скорости)
    all_history_exercises = db.query(HistoryExercise, WorkoutHistory.date) \
        .join(WorkoutHistory, HistoryExercise.history_id == WorkoutHistory.id) \
        .filter(WorkoutHistory.user_id == user.id) \
        .all()

    for ex_name in target_exercises:
        weekly_maxes = [0.0] * 8

        for w in range(8):
            # w=7 это текущая неделя, w=0 это 7 недель назад
            weeks_ago = 7 - w
            start_of_week = start_of_current_week - timedelta(weeks=weeks_ago)
            end_of_week = start_of_week + timedelta(days=6)

            max_in_week = 0.0
            for ex_item, date_val in all_history_exercises:
                # Игнорируем регистр (Bench Press == bench press)
                if ex_item.exercise_name.lower() == ex_name.lower():
                    if start_of_week <= date_val.date() <= end_of_week:
                        if ex_item.max_weight > max_in_week:
                            max_in_week = ex_item.max_weight

            weekly_maxes[w] = max_in_week

        # Если мы не делали жим на 5-й неделе, график не должен падать в ноль.
        # Мы просто "протягиваем" рекорд 4-й недели вперед.
        for w in range(1, 8):
            if weekly_maxes[w] == 0.0:
                weekly_maxes[w] = weekly_maxes[w-1]

        progression_list.append(ProgressionData(exercise=ex_name, weights=weekly_maxes))


    # Обновляем финальный return!
    return StatisticsResponse(
        workouts_logged=workouts_logged,
        current_streak=current_streak,
        weekly_volume=weekly_volume,
        total_volume=total_volume,
        personal_records=pr_list,
        weekly_activity_volume=weekly_vol_list,
        weekly_activity_sets=weekly_sets_list,
        weekly_activity_labels=weekly_labels,
        weight_progression=progression_list # <-- ОТПРАВЛЯЕМ ДАННЫЕ ПРОГРЕССИИ
    )

@app.get("/get_history/{telegram_id}", response_model=List[HistoryLogItem])
def get_history(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return []

    # Достаем все тренировки, сортируем по убыванию даты (сначала новые)
    history_records = db.query(WorkoutHistory).filter(
        WorkoutHistory.user_id == user.id
    ).order_by(WorkoutHistory.date.desc()).all()

    history_list = []
    for hr in history_records:
        # Достаем упражнения для каждой конкретной тренировки
        exercises = db.query(HistoryExercise).filter(HistoryExercise.history_id == hr.id).all()
        ex_names = [ex.exercise_name for ex in exercises]

        history_list.append(HistoryLogItem(
            date=hr.date.strftime("%Y-%m-%d"), # Формат "2026-06-23" для календаря
            day_name=hr.day_name,
            total_volume=hr.total_volume,
            total_sets=hr.total_sets,
            exercises=ex_names
        ))

    return history_list


@app.get("/export_history/{telegram_id}")
def export_history(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return {"error": "User not found"}

    # Достаем всю историю
    history_records = db.query(WorkoutHistory).filter(
        WorkoutHistory.user_id == user.id
    ).order_by(WorkoutHistory.date.desc()).all()

    export_data = []
    for hr in history_records:
        exercises = db.query(HistoryExercise).filter(HistoryExercise.history_id == hr.id).all()
        ex_data = []
        for ex in exercises:
            sets = db.query(HistorySet).filter(HistorySet.exercise_id == ex.id).all()
            sets_data = [{"weight": s.weight, "reps": s.reps, "is_done": s.is_done} for s in sets]
            ex_data.append({"name": ex.exercise_name, "sets": sets_data})

        export_data.append({
            "date": hr.date.strftime("%Y-%m-%d"),
            "day_name": hr.day_name,
            "total_volume": hr.total_volume,
            "total_sets": hr.total_sets,
            "exercises": ex_data
        })

    return {
        "telegram_id": telegram_id,
        "export_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "total_workouts": len(export_data),
        "workouts": export_data
    }