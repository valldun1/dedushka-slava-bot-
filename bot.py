import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from services.auth import get_mode, is_slava
from services.sheets import is_registered, find_user
from modes.slava import handle_slava, handle_slava_voice
from modes.onboarding import handle_onboarding, STEP_ASK_NAME, STEP_DONE
from modes.family import handle_family, handle_letter
from modes.stranger import handle_stranger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_SESSIONS: dict[int, dict] = {}


def get_session(user_id: int) -> dict:
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {
            "step": STEP_ASK_NAME,
            "state": {"name": "", "role": ""},
            "history": [],
        }
    return USER_SESSIONS[user_id]


def add_to_history(session: dict, role: str, text: str):
    session["history"].append({"role": role, "content": text})
    if len(session["history"]) > 20:
        session["history"] = session["history"][-20:]


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)

    if is_slava(user_id):
        await update.message.reply_text(
            "Здравствуй, дедушка Слава. Я рад, что ты здесь. 🌿\n\n"
            "Я создан для того, чтобы сохранить твои истории — для Валентина, "
            "для внуков, для всей семьи. Навсегда.\n\n"
            "Не нужно ничего готовить. Просто говори — голосом или текстом, как удобно.\n\n"
            "Начнём с простого:\n"
            "Расскажи, где ты вырос. Как выглядел тот дом?"
        )
        return

    registered = is_registered(user_id)
    mode = get_mode(user_id, registered)

    if mode == "STRANGER":
        await update.message.reply_text(
            "Здравствуй. Я дедушка Слава. 🌿\n"
            "Рад, что написал. Чем могу помочь?"
        )
        return

    if mode == "ONBOARDING":
        session["step"] = STEP_ASK_NAME
        response, next_step, new_state = await handle_onboarding(
            user_id, "", STEP_ASK_NAME, session["state"]
        )
        session["step"] = next_step
        session["state"] = new_state
        await update.message.reply_text(response)
        return

    if mode == "FAMILY":
        user = find_user(user_id)
        name = user.get("Имя", "") if user else ""
        await update.message.reply_text(
            f"Это я, дедушка Слава. 🌿\n"
            f"{'Рад тебя слышать, ' + name + '!' if name else 'Рад тебя слышать!'}\n\n"
            "Спрашивай о чём хочешь. Я помню."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    session = get_session(user_id)

    registered = is_registered(user_id)
    mode = get_mode(user_id, registered)

    if mode == "SLAVA":
        response, topic, _ = await handle_slava(text, session["history"])
        add_to_history(session, "user", text)
        add_to_history(session, "assistant", response)
        await update.message.reply_text(response)
        return

    if mode == "ONBOARDING":
        response, next_step, new_state = await handle_onboarding(
            user_id, text, session["step"], session["state"]
        )
        session["step"] = next_step
        session["state"] = new_state
        if next_step == -1:
            session["step"] = STEP_DONE
        await update.message.reply_text(response)
        return

    if mode == "FAMILY":
        if text.startswith("/pismo"):
            parts = text.split(maxsplit=1)
            to_name = parts[1] if len(parts) > 1 else "тебе"
            response = await handle_letter(to_name, session["history"])
        else:
            user = find_user(user_id)
            name = user.get("Имя", "") if user else ""
            response = await handle_family(text, session["history"], name)
        add_to_history(session, "user", text)
        add_to_history(session, "assistant", response)
        await update.message.reply_text(response)
        return

    if mode == "STRANGER":
        response = await handle_stranger(text, session["history"])
        add_to_history(session, "user", text)
        add_to_history(session, "assistant", response)
        await update.message.reply_text(response)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_slava(user_id):
        await update.message.reply_text(
            "Голосовые сообщения пока только для дедушки Славы. "
            "Напиши мне текстом. 🌿"
        )
        return

    await update.message.reply_text("Слушаю... 🎙")
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    voice_bytes = await file.download_as_bytearray()
    transcribed, response = await handle_slava_voice(bytes(voice_bytes))
    session = get_session(user_id)
    add_to_history(session, "user", transcribed)
    add_to_history(session, "assistant", response)
    await update.message.reply_text(
        f"📝 Я услышал: «{transcribed}»\n\n{response}"
    )


async def cmd_tema(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_slava(update.effective_user.id):
        return
    await update.message.reply_text(
        "Давай поговорим о другом. 🌿\n\n"
        "Расскажи — что было самым радостным в твоей жизни?"
    )


async def cmd_pauza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_slava(update.effective_user.id):
        return
    await update.message.reply_text(
        "Хорошо, дедушка Слава. Отдыхай. 🌿\n"
        "Всё, что ты рассказал — я сохранил.\n"
        "Когда захочешь продолжить — просто напиши."
    )


async def cmd_itog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_slava(update.effective_user.id):
        return
    from services.sheets import get_all_stories
    stories = get_all_stories()
    count = len(stories)
    topics = {}
    for s in stories:
        t = s.get("Тема", "РАЗНОЕ")
        topics[t] = topics.get(t, 0) + 1
    topics_text = "\n".join([f"  {t}: {c} историй" for t, c in topics.items()])
    await update.message.reply_text(
        f"Дедушка Слава, вот что мы уже сохранили: 🌿\n\n"
        f"Всего историй: {count}\n\n"
        f"По темам:\n{topics_text}\n\n"
        "Продолжаем?"
    )


def run():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("tema", cmd_tema))
    app.add_handler(CommandHandler("pauza", cmd_pauza))
    app.add_handler(CommandHandler("itog", cmd_itog))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Бот запущен...")
    app.run_polling()
