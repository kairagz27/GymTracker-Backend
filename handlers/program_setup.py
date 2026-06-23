from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.queries import get_or_create_user, save_program

router = Router()

# 1. Описываем шаги (состояния) нашего диалога
class SetupProgram(StatesGroup):
    choosing_split = State()
    choosing_days = State()

# Клавиатура для выбора программы
def get_splits_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Full Body", callback_data="split_fullbody")],
        [InlineKeyboardButton(text="Upper/Lower Split", callback_data="split_upperlower")],
        [InlineKeyboardButton(text="Push/Pull/Legs (PPL)", callback_data="split_ppl")],
        [InlineKeyboardButton(text="Classic Split", callback_data="split_classic")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# 2. Ловим нажатие на кнопку "Создать программу" из главного меню
@router.callback_query(F.data == "create_program")
async def start_program_setup(callback: types.CallbackQuery, state: FSMContext):
    # Переводим пользователя в состояние выбора сплита
    await state.set_state(SetupProgram.choosing_split)

    await callback.message.edit_text(
        "Отлично! Давай выберем программу тренировок.\nКакой сплит будем использовать?",
        reply_markup=get_splits_keyboard()
    )

# 3. Ловим выбор конкретного сплита
@router.callback_query(SetupProgram.choosing_split, F.data.startswith("split_"))
async def split_chosen(callback: types.CallbackQuery, state: FSMContext):
    # Словарь для красивого отображения названий
    split_dict = {
        "split_fullbody": "Full Body",
        "split_upperlower": "Upper/Lower Split",
        "split_ppl": "Push/Pull/Legs (PPL)",
        "split_classic": "Classic Split"
    }
    chosen_split = split_dict[callback.data]

    # Сохраняем выбор во временную память FSM
    await state.update_data(split=chosen_split)

    # Переводим на следующий шаг
    await state.set_state(SetupProgram.choosing_days)

    await callback.message.edit_text(
        f"✅ Выбран сплит: **{chosen_split}**\n\n"
        f"Теперь напиши дни недели, в которые планируешь тренироваться "
        f"(например: Понедельник, Среда, Пятница):"
    )

@router.message(SetupProgram.choosing_days)
async def days_chosen(message: types.Message, state: FSMContext):
    training_days = message.text

    # Достаем то, что сохранили на предыдущем шаге (название сплита)
    user_data = await state.get_data()
    chosen_split = user_data['split']

    # === РАБОТА С БАЗОЙ ДАННЫХ ===
    # 1. Получаем внутренний ID пользователя в нашей БД
    user = await get_or_create_user(message.from_user.id, message.from_user.username)

    # 2. Сохраняем программу
    await save_program(user.id, chosen_split, training_days)
    # ==============================

    # Очищаем состояние
    await state.clear()

    text = (
        f"🎉 Настройки успешно сохранены в Базу Данных!\n\n"
        f"🏋️ Программа: {chosen_split}\n"
        f"📅 Дни: {training_days}\n\n"
        f"Теперь ты можешь добавлять упражнения в разделе «Мои тренировки»."
    )
    from keyboards.inline import get_main_menu_keyboard
    await message.answer(text, reply_markup=get_main_menu_keyboard())