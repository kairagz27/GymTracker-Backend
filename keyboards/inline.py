from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        [InlineKeyboardButton(text="🛠 Создать программу", callback_data="create_program")],
        [InlineKeyboardButton(text="🏋️ Мои тренировки", callback_data="my_workouts")],
        [InlineKeyboardButton(text="📈 Статистика", callback_data="statistics")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)