import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


from firestore_db import save_note, get_notes, delete_note, update_note
from config import BOT_TOKEN

# Включаємо логування
logging.basicConfig(level=logging.INFO)

# Створюємо бота і диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Глобальний словник для зберігання стану користувачів
user_states = {}

# --- Клавіатура головного меню ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Нова заметка")],
        [KeyboardButton(text="📖 Переглянути заметку")],
        [KeyboardButton(text="✏️ Змінити заметку")],
        [KeyboardButton(text="🗑 Видалити заметку")]
    ],
    resize_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Скасувати")]
    ],
    resize_keyboard=True
)

# --- Команда /start ---
@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer("Привіт! Виберіть дію з меню:", reply_markup=main_menu)

@dp.message(lambda message: message.text == "❌ Скасувати")
async def cancel_action(message: types.Message):
    """Скидає стан і повертає головне меню"""
    user_states.pop(message.from_user.id, None)
    await message.answer("Дію скасовано. Ви повернулися в головне меню.", reply_markup=main_menu)

def create_notes_keyboard(notes, action):
    """Створює InlineKeyboardMarkup з заголовками заміток"""
    keyboard = InlineKeyboardBuilder()
    for title in notes.keys():
        keyboard.button(text=title, callback_data=f"{action}:{title}")
    keyboard.adjust(1)  # Кожна кнопка в окремому рядку
    return keyboard.as_markup()


# --- Створення нової замітки ---
@dp.message(lambda message: message.text == "📝 Нова заметка")
async def new_note_step1(message: types.Message):
    user_states[message.from_user.id] = {"state": "awaiting_title"}
    await message.answer("Введіть заголовок замітки:", reply_markup=cancel_keyboard)

@dp.message(lambda message: user_states.get(message.from_user.id, {}).get("state") == "awaiting_title")
async def new_note_step2(message: types.Message):
    user_states[message.from_user.id]["title"] = message.text
    user_states[message.from_user.id]["state"] = "awaiting_text"
    await message.answer("Тепер введіть текст замітки:", reply_markup=cancel_keyboard)

@dp.message(lambda message: user_states.get(message.from_user.id, {}).get("state") == "awaiting_text")
async def new_note_step3(message: types.Message):
    user_id = message.from_user.id
    title = user_states[user_id]["title"]
    text = message.text
    save_note(user_id, title, text)
    user_states.pop(user_id, None)
    await message.answer(f"Замітка '{title}' збережена!", reply_markup=main_menu)

# --- Перегляд замітки ---
@dp.message(lambda message: message.text == "📖 Переглянути замітку")
async def view_notes_step1(message: types.Message):
    notes = get_notes(message.from_user.id)
    if notes:
        keyboard = create_notes_keyboard(notes, "view_note")
        await message.answer("Виберіть замітку:", reply_markup=keyboard)
    else:
        await message.answer("У вас немає заміток.", reply_markup=main_menu)

@dp.callback_query(lambda c: c.data.startswith("view_note:"))
async def view_notes_step2(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    notes = get_notes(user_id)
    
    title = callback.data.split("view_note:")[1]  # Отримуємо заголовок
    if title in notes:
        await callback.message.answer(f"📖 <b>{title}</b>\n\n{notes[title]}", reply_markup=main_menu)
    else:
        await callback.message.answer("Замітка не знайдена.", reply_markup=main_menu)
    
    await callback.answer()  # Закриває спливаюче повідомлення        

@dp.message(lambda message: user_states.get(message.from_user.id, {}).get("state") == "awaiting_note_view")
async def view_notes_step2(message: types.Message):
    notes = get_notes(message.from_user.id)
    title = message.text
    if title in notes:
        await message.answer(f"📖 {title}\n\n{notes[title]}", reply_markup=main_menu)
    else:
        await message.answer("Замітка не знайдена. Спробуйте ще раз.")
    user_states.pop(message.from_user.id, None)

# --- Зміна замітки ---
@dp.message(lambda message: message.text == "✏️ Змінити замітку")
async def edit_notes_step1(message: types.Message):
    notes = get_notes(message.from_user.id)
    if notes:
        keyboard = create_notes_keyboard(notes, "edit_note")
        await message.answer("Виберіть замітку для редагування:", reply_markup=keyboard)
    else:
        await message.answer("У вас немає заміток.", reply_markup=main_menu)

@dp.callback_query(lambda c: c.data.startswith("edit_note:"))
async def edit_notes_step2(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    title = callback.data.split("edit_note:")[1]  # Отримуємо заголовок

    user_states[user_id] = {"state": "awaiting_new_text", "title": title}
    await callback.message.answer(f"Введіть новий текст для замітки '{title}':", reply_markup=cancel_keyboard)
    await callback.answer()

@dp.message(lambda message: user_states.get(message.from_user.id, {}).get("state") == "awaiting_new_text")
async def edit_notes_step3(message: types.Message):
    user_id = message.from_user.id
    title = user_states[user_id]["title"]
    new_text = message.text

    update_note(user_id, title, new_text)
    user_states.pop(user_id, None)

    await message.answer(f"Замітка '{title}' оновлена!", reply_markup=main_menu)

@dp.message(lambda message: message.text == "🗑 Видалити замітку")
async def delete_notes_step1(message: types.Message):
    notes = get_notes(message.from_user.id)
    if notes:
        keyboard = create_notes_keyboard(notes, "delete_note")
        await message.answer("Виберіть замітку для видалення:", reply_markup=keyboard)
    else:
        await message.answer("У вас немає заміток.", reply_markup=main_menu)

@dp.callback_query(lambda c: c.data.startswith("delete_note:"))
async def delete_notes_step2(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    title = callback.data.split("delete_note:")[1]  # Отримуємо заголовок

    delete_note(user_id, title)
    await callback.message.answer(f"Замітка '{title}' видалена.", reply_markup=main_menu)
    await callback.answer()

# --- Запуск бота ---
async def main() -> None:
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
