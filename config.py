import os
import json
import firebase_admin
from firebase_admin import credentials

# Получаем строку JSON из переменной окружения
cred_json_str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')

if cred_json_str is None:
    raise ValueError("Google credentials not found in environment variable.")

# Преобразуем строку JSON в словарь
cred_json = json.loads(cred_json_str)

# Инициализируем Firebase с использованием полученных данных
cred = credentials.Certificate(cred_json)
firebase_admin.initialize_app(cred)
