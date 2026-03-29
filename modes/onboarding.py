from services.groq_client import chat_simple
from services.sheets import register_user, save_personality
from prompts.system import get_onboarding_prompt

STEP_ASK_NAME     = 1
STEP_ASK_ROLE     = 2
STEP_Q1_CHARACTER = 31
STEP_Q2_PHRASES   = 32
STEP_Q3_STORY     = 33
STEP_Q4_ESSENCE   = 34
STEP_DONE         = 4


async def handle_onboarding(
    user_id: int,
    text: str,
    step: int,
    state: dict,
) -> tuple[str, int, dict]:

    if step == STEP_ASK_NAME:
        prompt = get_onboarding_prompt(1)
        response = chat_simple(prompt, "начать")
        return response, STEP_ASK_ROLE, state

    if step == STEP_ASK_ROLE:
        state["name"] = text.strip()
        prompt = get_onboarding_prompt(2, name=state["name"])
        response = chat_simple(prompt, text)
        return response, STEP_Q1_CHARACTER, state

    if step == STEP_Q1_CHARACTER:
        state["role"] = text.strip()
        register_user(user_id, state["name"], state["role"])
        prompt = get_onboarding_prompt(3, name=state["name"])
        response = chat_simple(prompt, "Задай вопрос 3а про характер дедушки Славы.")
        return response, STEP_Q2_PHRASES, state

    if step == STEP_Q2_PHRASES:
        save_personality("ХАРАКТЕР", text, state["name"])
        prompt = get_onboarding_prompt(3, name=state["name"])
        response = chat_simple(prompt, "Задай вопрос 3б про любимые фразы дедушки Славы.")
        return response, STEP_Q3_STORY, state

    if step == STEP_Q3_STORY:
        save_personality("ФРАЗЫ", text, state["name"])
        prompt = get_onboarding_prompt(3, name=state["name"])
        response = chat_simple(prompt, "Задай вопрос 3в про одну незабываемую историю о дедушке Славе.")
        return response, STEP_Q4_ESSENCE, state

    if step == STEP_Q4_ESSENCE:
        save_personality("ИСТОРИЯ_ОТ_СЕМЬИ", text, state["name"])
        prompt = get_onboarding_prompt(3, name=state["name"])
        response = chat_simple(prompt, "Задай вопрос 3г про самое главное в дедушке Славе.")
        return response, STEP_DONE, state

    if step == STEP_DONE:
        save_personality("СУТЬ", text, state["name"])
        prompt = get_onboarding_prompt(4, name=state["name"])
        response = chat_simple(prompt, "завершить онбординг")
        return response, -1, state

    return "Что-то пошло не так. Напиши /start", step, state
