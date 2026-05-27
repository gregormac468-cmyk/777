"""
Модуль AI-анализа звонков — мультипровайдерный.
Поддержка: OpenAI, Google Gemini, DeepSeek, Anthropic (Claude), Qwen.
"""
import json
from typing import Any

import httpx


ANALYSIS_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_call_analysis",
        "description": "Возвращает структурированный анализ звонка",
        "parameters": {
            "type": "object",
            "properties": {
                "call_type": {"type": "string", "description": "Тип звонка: Результативный / Нерезультативный / Обеспечительный"},
                "overall_score": {"type": "number", "minimum": 0, "maximum": 10, "description": "Общая оценка от 0 до 10"},
                "summary": {"type": "string", "description": "Краткое резюме звонка"},
                "criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "score": {"type": "number", "minimum": 0, "maximum": 10},
                            "comment": {"type": "string"},
                        },
                        "required": ["name", "score", "comment"],
                    },
                },
                "strengths": {"type": "array", "items": {"type": "string"}},
                "weaknesses": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["call_type", "overall_score", "summary", "criteria", "strengths", "weaknesses", "recommendations"],
        },
    },
}

SCALE_RULE = (
    "\n\nВАЖНО: Все оценки используют шкалу строго от 0 до 10 (допускаются дробные значения, "
    "например 7.5). НЕ используй шкалу 0-100 и НЕ выставляй значения больше 10. "
    "overall_score — число от 0 до 10. Каждый criteria[].score — число от 0 до 10."
)

DEFAULT_SYSTEM = (
    "Ты — эксперт по контролю качества телефонных разговоров. "
    "Проанализируй транскрипт звонка отдела продаж и оцени его по основным критериям: "
    "приветствие, выявление потребностей, презентация, работа с возражениями, закрытие."
)


def build_system_prompt(instruction: str | None) -> str:
    if instruction and instruction.strip():
        base = (
            "Ты — эксперт по контролю качества телефонных разговоров отдела продаж. "
            "Используй следующую инструкцию для оценки:\n\n"
            f"{instruction}\n\n"
            "Проанализируй транскрипт звонка и верни структурированную оценку."
        )
    else:
        base = DEFAULT_SYSTEM
    return base + SCALE_RULE


def strip_additional_props(obj: Any) -> Any:
    """Удаляет additionalProperties для Gemini совместимости."""
    if isinstance(obj, list):
        return [strip_additional_props(x) for x in obj]
    if isinstance(obj, dict):
        return {k: strip_additional_props(v) for k, v in obj.items() if k != "additionalProperties"}
    return obj


# ===== OpenAI =====
def analyze_openai(api_key: str, system_prompt: str, transcript: str, model: str = "gpt-4o-mini") -> dict:
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Транскрипт звонка:\n\n{transcript}"},
            ],
            "tools": [ANALYSIS_TOOL],
            "tool_choice": {"type": "function", "function": {"name": "submit_call_analysis"}},
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise Exception(f"OpenAI ошибка {resp.status_code}: {resp.text}")
    j = resp.json()
    tc = j.get("choices", [{}])[0].get("message", {}).get("tool_calls", [{}])[0]
    if not tc:
        raise Exception("OpenAI не вернул структурированный анализ")
    return json.loads(tc["function"]["arguments"])


# ===== Google Gemini =====
def analyze_google(api_key: str, system_prompt: str, transcript: str, model: str = "gemini-2.5-flash") -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    func_decl = strip_additional_props(ANALYSIS_TOOL["function"])

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": f"Транскрипт звонка:\n\n{transcript}"}]}],
        "tools": [{"functionDeclarations": [func_decl]}],
        "toolConfig": {"functionCallingConfig": {"mode": "ANY", "allowedFunctionNames": ["submit_call_analysis"]}},
    }

    resp = httpx.post(url, json=payload, timeout=120)
    if resp.status_code != 200:
        raise Exception(f"Google Gemini ошибка {resp.status_code}: {resp.text}")

    j = resp.json()
    parts = j.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    fc = next((p.get("functionCall") for p in parts if p.get("functionCall")), None)
    if not fc or not fc.get("args"):
        raise Exception("Google Gemini не вернул структурированный анализ")
    return fc["args"]


# ===== DeepSeek (OpenAI-совместимый) =====
def analyze_deepseek(api_key: str, system_prompt: str, transcript: str, model: str = "deepseek-chat") -> dict:
    return _analyze_openai_compat(
        api_key, "https://api.deepseek.com/v1", model, system_prompt, transcript, "DeepSeek"
    )


# ===== Qwen (DashScope OpenAI-совместимый) =====
def analyze_qwen(api_key: str, system_prompt: str, transcript: str, model: str = "qwen-plus") -> dict:
    return _analyze_openai_compat(
        api_key, "https://dashscope-intl.aliyuncs.com/compatible-mode/v1", model, system_prompt, transcript, "Qwen"
    )


# ===== Anthropic (Claude) =====
def analyze_anthropic(api_key: str, system_prompt: str, transcript: str, model: str = "claude-3-5-sonnet-latest") -> dict:
    tool = {
        "name": ANALYSIS_TOOL["function"]["name"],
        "description": ANALYSIS_TOOL["function"]["description"],
        "input_schema": strip_additional_props(ANALYSIS_TOOL["function"]["parameters"]),
    }
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": f"Транскрипт звонка:\n\n{transcript}"}],
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": tool["name"]},
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise Exception(f"Anthropic ошибка {resp.status_code}: {resp.text}")
    j = resp.json()
    block = next((b for b in j.get("content", []) if b.get("type") == "tool_use"), None)
    if not block or not block.get("input"):
        raise Exception("Anthropic не вернул структурированный анализ")
    return block["input"]


# ===== Общий OpenAI-совместимый =====
def _analyze_openai_compat(
    api_key: str, base_url: str, model: str, system_prompt: str, transcript: str, label: str
) -> dict:
    resp = httpx.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Транскрипт звонка:\n\n{transcript}"},
            ],
            "tools": [ANALYSIS_TOOL],
            "tool_choice": {"type": "function", "function": {"name": "submit_call_analysis"}},
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise Exception(f"{label} ошибка {resp.status_code}: {resp.text}")
    j = resp.json()
    tc = j.get("choices", [{}])[0].get("message", {}).get("tool_calls", [{}])[0]
    if not tc:
        raise Exception(f"{label} не вернул структурированный анализ")
    return json.loads(tc["function"]["arguments"])


# ===== Универсальная функция =====
def analyze(provider: str, api_key: str, transcript: str, instruction: str | None, model: str) -> dict:
    """Анализ транскрипта через выбранного провайдера."""
    system_prompt = build_system_prompt(instruction)

    if provider == "openai":
        return analyze_openai(api_key, system_prompt, transcript, model or "gpt-4o-mini")
    elif provider == "google":
        return analyze_google(api_key, system_prompt, transcript, model or "gemini-2.5-flash")
    elif provider == "deepseek":
        return analyze_deepseek(api_key, system_prompt, transcript, model or "deepseek-chat")
    elif provider == "anthropic":
        return analyze_anthropic(api_key, system_prompt, transcript, model or "claude-3-5-sonnet-latest")
    elif provider == "qwen":
        return analyze_qwen(api_key, system_prompt, transcript, model or "qwen-plus")
    else:
        raise Exception(f"Неизвестный провайдер анализа: {provider}")
