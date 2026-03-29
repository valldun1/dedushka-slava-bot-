from services.groq_client import chat
from services.sheets import get_all_stories, get_personality
from prompts.system import get_family_prompt

COMMANDS = {
    "/istoria":     "Расскажи яркую историю из своей жизни.",
    "/sovet":       "Дай мудрый совет как дедушка Слава.",
    "/vospominanie":"Вспомни что-нибудь интересное.",
    "/chtopomnish": "Расскажи что ты знаешь и помнишь о нашей семье.",
}


async def handle_family(text: str, history: list[dict], user_name: str = "") -> str:
    stories = get_all_stories()
    personality = get_personality()
    system = get_family_prompt(stories, personality)
    user_input = COMMANDS.get(text.strip(), text)
    if user_name:
        user_input = f"[Говорит с тобой: {user_name}]\n{user_input}"
    messages = history + [{"role": "user", "content": user_input}]
    return chat(system, messages, max_tokens=800)


async def handle_letter(to_name: str, history: list[dict]) -> str:
    stories = get_all_stories()
    personality = get_personality()
    system = get_family_prompt(stories, personality)
    prompt = f"Напиши тёплое личное письмо от дедушки Славы для {to_name}. От первого лица, с воспоминаниями и мудростью."
    messages = history + [{"role": "user", "content": prompt}]
    return chat(system, messages, max_tokens=1000)
