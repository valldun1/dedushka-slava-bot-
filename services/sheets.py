import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")


def get_client():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheets():
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    return {
        "семья":    spreadsheet.worksheet("СЕМЬЯ"),
        "истории":  spreadsheet.worksheet("ИСТОРИИ"),
        "личность": spreadsheet.worksheet("ЛИЧНОСТЬ"),
    }


def find_user(user_id: int) -> dict | None:
    ws = get_sheets()["семья"]
    records = ws.get_all_records()
    for row in records:
        if str(row.get("TG_ID")) == str(user_id):
            return row
    return None


def register_user(user_id: int, name: str, role: str):
    ws = get_sheets()["семья"]
    ws.append_row([
        str(user_id),
        name,
        role,
        "TRUE",
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ])


def is_registered(user_id: int) -> bool:
    user = find_user(user_id)
    return bool(user and str(user.get("Зарегистрирован", "")).upper() == "TRUE")


def save_story(topic: str, text: str, keywords: str = ""):
    ws = get_sheets()["истории"]
    ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        topic,
        text,
        keywords,
    ])


def get_all_stories() -> list[dict]:
    ws = get_sheets()["истории"]
    return ws.get_all_records()


def get_stories_by_keyword(keyword: str) -> list[dict]:
    stories = get_all_stories()
    keyword_lower = keyword.lower()
    return [
        s for s in stories
        if keyword_lower in str(s.get("Ключевые_слова", "")).lower()
        or keyword_lower in str(s.get("Тема", "")).lower()
        or keyword_lower in str(s.get("Текст", "")).lower()
    ]


def save_personality(category: str, text: str, from_who: str):
    ws = get_sheets()["личность"]
    ws.append_row([
        category,
        text,
        from_who,
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    ])


def get_personality() -> list[dict]:
    ws = get_sheets()["личность"]
    return ws.get_all_records()


def get_personality_by_category(category: str) -> list[dict]:
    all_rows = get_personality()
    return [r for r in all_rows if r.get("Категория", "").upper() == category.upper()]
