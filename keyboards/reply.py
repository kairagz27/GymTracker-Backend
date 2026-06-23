from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo

def get_reply_menu(user_id: int) -> ReplyKeyboardMarkup:
    """Возвращает постоянную клавиатуру под полем ввода с кнопкой WebApp"""

    # Формируем ссылку на твой локальный Kotlin-фронтенд с ID пользователя
    web_app_url = f"https://e6a55e20e70964.lhr.life/?user_id={user_id}"

    keyboard = [
        # Верхняя кнопка - открывает наше Mini App
        [
            KeyboardButton(
                text="🏋️‍♂️ Открыть Дневник",
                web_app=WebAppInfo(url=web_app_url)
            )
        ],
        # Нижняя кнопка - возвращает инлайн-меню (ловится фильтром в start.py)
        [
            KeyboardButton(text="🗄 Главное меню")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True, # Делает кнопки аккуратными
        input_field_placeholder="Выбери действие..."
    )