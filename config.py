import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='d:/projects/telegram-bot-notes/.env')

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

print(BOT_TOKEN)  # Перевір, чи правильно завантажено токен
print(GOOGLE_APPLICATION_CREDENTIALS) 