import os
import json
import firebase_admin
from firebase_admin import credentials

# Загружаем BOT_TOKEN из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables.")

# Загружаем Firebase credentials из переменной окружения
cred_json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not cred_json_str:
    raise ValueError("Google credentials not found in environment variable.")

cred_dict = json.loads(cred_json_str)
cred = credentials.Certificate(cred_dict)

# Инициализируем Firebase (гарантируем, что вызываем только один раз)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
