import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from firestore_db import save_note, get_notes, delete_note, update_note
from config import BOT_TOKEN


logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_states = {}

# --- Главное меню ---
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Нова заметка")],
        [KeyboardButton(text="📖 Переглянути заметку")],
        [KeyboardButton(text="✏️ Змінити заметку")],
        [KeyboardButton(text="🗑 Видалити замітку")]
    ],
    resize_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Скасувати")]],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer("Привіт! Виберіть дію з меню:", reply_markup=main_menu)

@dp.message(F.text == "❌ Скасувати")
async def cancel_action(message: types.Message):
    user_states.pop(message.from_user.id, None)
    await message.answer("Дію скасовано. Ви повернулися в головне меню.", reply_markup=main_menu)

def create_notes_keyboard(notes, action):
    keyboard = InlineKeyboardBuilder()
    for title in notes.keys():
        callback_data = f"{action}:{title}"
        keyboard.button(text=title, callback_data=callback_data)
    keyboard.adjust(1)
    return keyboard.as_markup()

# --- Создание новой заметки ---
@dp.message(F.text == "📝 Нова заметка")
async def new_note_step1(message: types.Message):
    user_states[message.from_user.id] = {"state": "awaiting_title"}
    await message.answer("Введіть заголовок замітки:", reply_markup=cancel_keyboard)

@dp.message(lambda msg: user_states.get(msg.from_user.id, {}).get("state") == "awaiting_title")
async def new_note_step2(message: types.Message):
    user_states[message.from_user.id] = {"state": "awaiting_text", "title": message.text}
    await message.answer("Тепер введіть текст замітки:", reply_markup=cancel_keyboard)

@dp.message(lambda msg: user_states.get(msg.from_user.id, {}).get("state") == "awaiting_text")
async def new_note_step3(message: types.Message):
    user_id = message.from_user.id
    title = user_states[user_id]["title"]
    save_note(user_id, title, message.text)
    user_states.pop(user_id, None)
    await message.answer(f"Замітка '{title}' збережена!", reply_markup=main_menu)

# --- Просмотр заметки ---
@dp.message(F.text == "📖 Переглянути заметку")
async def view_notes_step1(message: types.Message):
    notes = get_notes(message.from_user.id)
    if notes:
        await message.answer("Виберіть замітку:", reply_markup=create_notes_keyboard(notes, "view_note"))
    else:
        await message.answer("У вас немає заміток.", reply_markup=main_menu)

@dp.callback_query(F.data.startswith("view_note:"))
async def view_notes_step2(callback: types.CallbackQuery):
    _, _, title = callback.data.partition(":")
    notes = get_notes(callback.from_user.id)
    text = notes.get(title, "Замітка не знайдена.")
    await callback.message.answer(f"📖 <b>{title}</b>\n\n{text}", reply_markup=main_menu)
    await callback.answer()
# --- Изменение заметки ---
@dp.message(F.text == "✏️ Змінити замітку")
async def edit_notes_step1(message: types.Message):
    notes = get_notes(message.from_user.id)
    logging.info(f"Notes for user {message.from_user.id}: {notes}")  # Лог
    if notes:
        await message.answer("Виберіть замітку для редагування:", reply_markup=create_notes_keyboard(notes, "edit_note"))
    else:
        await message.answer("У вас немає заміток.", reply_markup=main_menu)


@dp.callback_query(F.data.startswith("edit_note:"))
async def edit_notes_step2(callback: types.CallbackQuery):
    _, title = callback.data.split(":", 1)  # Разбиваем корректно
    user_states[callback.from_user.id] = {"state": "awaiting_new_text", "title": title}

    # Изменяем сообщение кнопки на ввод нового текста
    await callback.message.edit_text(f"Введіть новий текст для замітки '{title}':", reply_markup=cancel_keyboard)
    await callback.answer()


@dp.message(lambda msg: user_states.get(msg.from_user.id, {}).get("state") == "awaiting_new_text")
async def edit_notes_step3(message: types.Message):
    user_id = message.from_user.id
    title = user_states[user_id]["title"]
    update_note(user_id, title, message.text)
    user_states.pop(user_id, None)

    # Отвечаем пользователю о завершении редактирования
    await message.answer(f"Замітка '{title}' оновлена!", reply_markup=main_menu)


# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
