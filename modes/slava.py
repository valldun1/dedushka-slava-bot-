from services.groq_client import chat_simple, transcribe_voice
from services.sheets import save_story
from prompts.system import get_slava_prompt


def detect_topic(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["дет", "дом", "мама", "папа", "школ", "игр", "двор"]):
        return "ДЕТСТВО"
    if any(w in text_lower for w in ["молод", "юност", "люб", "работ", "первый"]):
        return "ЮНОСТЬ"
    if any(w in text_lower for w in ["трудн", "тяжел", "горе", "потер", "война", "болез"]):
        return "ТРУДНОСТИ"
    if any(w in text_lower for w in ["горжус", "создал", "построил", "сделал", "достиг"]):
        return "ГОРДОСТЬ"
    if any(w in text_lower for w in ["мудр", "совет", "важн", "понял", "урок"]):
        return "МУДРОСТЬ"
    if any(w in text_lower for w in ["внук", "семь", "передать", "помнить"]):
        return "ДЛЯ СЕМЬИ"
    return "РАЗНОЕ"


def extract_keywords(text: str) -> str:
    words = text.split()
    keywords = [w for w in words if len(w) > 1 and w[0].isupper()]
    return ", ".join(set(keywords[:10]))


async def handle_slava(text: str, history: list[dict]) -> tuple[str, str, str]:
    system = get_slava_prompt()
    response = chat_simple(system, text)
    topic = detect_topic(text)
    keywords = extract_keywords(text)
    save_story(topic=topic, text=text, keywords=keywords)
    return response, topic, text


async def handle_slava_voice(voice_bytes: bytes) -> tuple[str, str]:
    text = await transcribe_voice(voice_bytes)
    response, topic, _ = await handle_slava(text, [])
    return text, response
