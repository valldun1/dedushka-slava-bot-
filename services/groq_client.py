import os
import tempfile
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

LLM_MODEL = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3-turbo"


def chat(system_prompt: str, messages: list[dict], max_tokens: int = 1024) -> str:
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def chat_simple(system_prompt: str, user_text: str, max_tokens: int = 1024) -> str:
    return chat(system_prompt, [{"role": "user", "content": user_text}], max_tokens)


async def transcribe_voice(voice_bytes: bytes, file_ext: str = "ogg") -> str:
    with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
        tmp.write(voice_bytes)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file,
            language="ru",
        )

    os.unlink(tmp_path)
    return transcription.text.strip()
