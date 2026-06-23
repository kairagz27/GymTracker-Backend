from aiogram import Router, types, F
from aiogram.filters import CommandStart
from keyboards.inline import get_main_menu_keyboard
# Импортируем именно ту функцию, которую мы обновили для WebApp
from keyboards.reply import get_reply_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработка команды /start"""

    # 1. Сначала отправляем короткое сообщение, чтобы прикрепить нижнюю клавиатуру с кнопкой WebApp
    await message.answer(
        "Добро пожаловать! Клавиатура добавлена вниз 👇",
        reply_markup=get_reply_menu(user_id=message.from_user.id)
    )

    # 2. Затем отправляем твое красивое главное меню
    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Я твой цифровой дневник тренировок. Помогу спланировать программу, "
        f"записать веса и отследить прогресс.\n\n"
        f"Выбери действие в меню ниже:"
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())


# Магический фильтр F.text ловит конкретный текст от пользователя
# (Убедись, что текст совпадает с тем, что написано на кнопке в reply.py)
@router.message(F.text == "🗄 Главное меню")
async def show_main_menu(message: types.Message):
    """Реакция на нажатие нижней кнопки"""
    text = "Главное меню:"
    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(lambda c: c.data in ["statistics", "settings"])
async def process_placeholders(callback: types.CallbackQuery):
    """Временная заглушка для кнопок главного меню"""
    await callback.answer("Эта функция появится на следующих этапах! 🚀", show_alert=True)