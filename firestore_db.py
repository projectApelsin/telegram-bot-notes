import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# Завантаження облікових даних із змінної середовища
GOOGLE_APPLICATION_CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not GOOGLE_APPLICATION_CREDENTIALS_JSON:
    raise ValueError("Google credentials not found in environment variable.")

cred_dict = json.loads(GOOGLE_APPLICATION_CREDENTIALS_JSON)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()

def save_note(user_id, title, text):
    """Зберігає нотатку користувача в Firestore за заголовком"""
    doc_ref = db.collection("notes").document(str(user_id))
    doc = doc_ref.get()

    if doc.exists:
        notes = doc.to_dict().get("notes", {})
    else:
        notes = {}

    notes[title] = text  # Зберігаємо нотатку у форматі {заголовок: текст}
    doc_ref.set({"notes": notes})

def get_notes(user_id):
    """Отримує всі нотатки користувача у форматі {заголовок: текст}"""
    doc_ref = db.collection("notes").document(str(user_id))
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("notes", {})
    return {}

def delete_note(user_id, title):
    """Видаляє нотатку за заголовком"""
    doc_ref = db.collection("notes").document(str(user_id))
    doc = doc_ref.get()

    if doc.exists:
        notes = doc.to_dict().get("notes", {})
        if title in notes:
            del notes[title]
            doc_ref.set({"notes": notes})  # Оновлюємо документ після видалення
            return True
    return False

def update_note(user_id, title, new_text):
    """Оновлює текст нотатки за заголовком"""
    doc_ref = db.collection("notes").document(str(user_id))
    doc = doc_ref.get()

    if doc.exists:
        notes = doc.to_dict().get("notes", {})
        if title in notes:
            notes[title] = new_text
            doc_ref.set({"notes": notes})  # Оновлюємо документ
            return True
    return False
