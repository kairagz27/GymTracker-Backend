from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.queries import get_or_create_user, get_user_program, save_exercise_set, get_todays_exercises # <-- Добавили новый импорт

router = Router()

# Состояния для пошагового ввода упражнения
class AddExercise(StatesGroup):
    waiting_for_name = State()
    waiting_for_sets_count = State()
    waiting_for_set_data = State()

@router.callback_query(F.data == "my_workouts")
async def show_my_workouts(callback: types.CallbackQuery):
    user = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    program = await get_user_program(user.id)

    if not program:
        await callback.answer("У тебя еще нет программы! Нажми «Создать программу».", show_alert=True)
        return

    # Достаем подходы за сегодня
    todays_logs = await get_todays_exercises(user.id)

    text = f"🏋️ Твоя программа: **{program.name}**\n📅 Дни: {program.days}\n\n"

    if not todays_logs:
        text += "Журнал на сегодня пуст. Самое время начать тренировку!"
    else:
        text += "📝 **Сегодняшняя тренировка:**\n"

        # Группируем подходы по названию упражнения, чтобы не писать его каждый раз
        exercises = {}
        for log in todays_logs:
            if log.exercise_name not in exercises:
                exercises[log.exercise_name] = []

            # Убираем лишние нули, если вес целое число (60.0 -> 60)
            weight_display = int(log.weight) if log.weight.is_integer() else log.weight

            exercises[log.exercise_name].append(
                f"  • Подход {log.set_number}: {weight_display} кг × {log.reps} раз"
            )

        # Собираем сгруппированные данные в текст
        for ex_name, sets in exercises.items():
            text += f"\n🔹 **{ex_name}**\n"
            text += "\n".join(sets)

        text += "\n\nЧто делаем дальше?"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить упражнение", callback_data="add_exercise")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    from keyboards.inline import get_main_menu_keyboard
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu_keyboard())


# ================= FSM ДОБАВЛЕНИЯ УПРАЖНЕНИЯ =================

@router.callback_query(F.data == "add_exercise")
async def start_add_exercise(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddExercise.waiting_for_name)
    await callback.message.edit_text("✍️ Напиши название упражнения (например: Жим штанги лежа):")

@router.message(AddExercise.waiting_for_name)
async def exercise_name_entered(message: types.Message, state: FSMContext):
    await state.update_data(exercise_name=message.text)
    await state.set_state(AddExercise.waiting_for_sets_count)
    await message.answer("🔢 Сколько подходов будешь делать? (Напиши просто число, например: 3)")

@router.message(AddExercise.waiting_for_sets_count)
async def sets_count_entered(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи число (например: 3).")
        return

    total_sets = int(message.text)
    # Сохраняем общее количество и ставим счетчик на 1-й подход
    await state.update_data(total_sets=total_sets, current_set=1)
    await state.set_state(AddExercise.waiting_for_set_data)

    await message.answer(
        f"Отлично! Начинаем записывать.\n\n"
        f"➡️ **Подход 1 из {total_sets}**\n"
        f"Напиши вес и количество повторений через пробел (например: `60 10`):"
    )

@router.message(AddExercise.waiting_for_set_data)
async def set_data_entered(message: types.Message, state: FSMContext):
    data = message.text.split()

    # Простая проверка, что ввели два числа
    if len(data) != 2:
        await message.answer("⚠️ Неверный формат. Напиши вес и повторения через пробел (например: `60 10`).")
        return

    try:
        weight = float(data[0])
        reps = int(data[1])
    except ValueError:
        await message.answer("⚠️ Вес и повторения должны быть числами. Попробуй еще раз (например: `60 10`).")
        return

    # Достаем данные из памяти
    user_data = await state.get_data()
    exercise_name = user_data['exercise_name']
    current_set = user_data['current_set']
    total_sets = user_data['total_sets']

    # Сохраняем в базу данных текущий подход
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await save_exercise_set(user.id, exercise_name, current_set, weight, reps)

    # Проверяем, остались ли еще подходы
    if current_set < total_sets:
        current_set += 1
        await state.update_data(current_set=current_set)
        await message.answer(
            f"✅ Записал!\n\n"
            f"➡️ **Подход {current_set} из {total_sets}**\n"
            f"Напиши вес и повторения (например: `65 8`):"
        )
    else:
        # Все подходы записаны
        await state.clear()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Еще упражнение", callback_data="add_exercise")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")]
        ])

        await message.answer(
            f"🎉 Упражнение **{exercise_name}** ({total_sets} подходов) успешно сохранено!\n\n"
            f"Продолжаем тренировку?",
            reply_markup=keyboard
        )