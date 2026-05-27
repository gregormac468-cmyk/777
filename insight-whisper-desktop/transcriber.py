"""
Модуль транскрибации аудио — поддержка OpenAI Whisper и Google Gemini.
"""
import base64
import json
import mimetypes
from pathlib import Path

import httpx


def guess_mime(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".oga": "audio/ogg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".webm": "audio/webm",
        ".flac": "audio/flac",
        ".aac": "audio/aac",
        ".opus": "audio/opus",
        ".amr": "audio/amr",
        ".3gp": "audio/3gpp",
    }
    return mime_map.get(ext, "audio/mpeg")


def file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


TRANSCRIBE_SYSTEM = (
    "Ты — точный транскрибатор. Верни ПОЛНЫЙ дословный транскрипт аудио на русском языке. "
    "Если в аудио есть несколько говорящих, обозначь их как 'Менеджер:' и 'Клиент:'. "
    "Не добавляй комментарии, только транскрипт."
)


def transcribe_openai(api_key: str, file_path: str, model: str = "whisper-1") -> str:
    """Транскрибация через OpenAI Whisper API."""
    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f, guess_mime(file_path))}
        data = {"model": model, "language": "ru", "response_format": "text"}
        resp = httpx.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
            timeout=300,
        )
    if resp.status_code != 200:
        raise Exception(f"OpenAI Whisper ошибка {resp.status_code}: {resp.text}")
    return resp.text.strip()


def transcribe_google(api_key: str, file_path: str, model: str = "gemini-2.5-flash") -> str:
    """Транскрибация через Google Gemini (audio inline)."""
    b64 = file_to_base64(file_path)
    mime = guess_mime(file_path)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": f"{TRANSCRIBE_SYSTEM}\n\nТранскрибируй этот звонок дословно."},
                {"inline_data": {"mime_type": mime, "data": b64}},
            ],
        }],
    }

    resp = httpx.post(url, json=payload, timeout=300)
    if resp.status_code != 200:
        raise Exception(f"Google Gemini ошибка {resp.status_code}: {resp.text}")

    j = resp.json()
    parts = j.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "\n".join(p.get("text", "") for p in parts if p.get("text"))
    if not text.strip():
        raise Exception("Пустой транскрипт от Google Gemini")
    return text.strip()


def transcribe(provider: str, api_key: str, file_path: str, model: str) -> str:
    """Универсальная функция транскрибации."""
    if provider == "openai":
        return transcribe_openai(api_key, file_path, model or "whisper-1")
    elif provider == "google":
        return transcribe_google(api_key, file_path, model or "gemini-2.5-flash")
    else:
        raise Exception(f"Неизвестный провайдер транскрибации: {provider}")
