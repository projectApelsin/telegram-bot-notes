import config  
import firebase_admin
from firebase_admin import firestore

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

