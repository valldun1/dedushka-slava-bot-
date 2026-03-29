from services.groq_client import chat
from prompts.system import get_stranger_prompt


async def handle_stranger(text: str, history: list[dict]) -> str:
    system = get_stranger_prompt()
    messages = history + [{"role": "user", "content": text}]
    return chat(system, messages, max_tokens=300)
