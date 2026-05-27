"""
Модуль конфигурации — загрузка/сохранение настроек в JSON файл.
"""
import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.path.expanduser("~")) / ".insight-whisper"
CONFIG_FILE = CONFIG_DIR / "config.json"
INSTRUCTIONS_DIR = CONFIG_DIR / "instructions"
RESULTS_DIR = CONFIG_DIR / "results"

DEFAULT_CONFIG = {
    "transcription_provider": "google",  # google, openai
    "transcription_model": "gemini-2.5-flash",
    "analysis_provider": "google",  # google, openai, deepseek, anthropic, qwen
    "analysis_model": "gemini-2.5-flash",
    "openai_api_key": "",
    "google_api_key": "",
    "deepseek_api_key": "",
    "anthropic_api_key": "",
    "qwen_api_key": "",
    "active_instruction": "",
    "delay_between_files": 15,
    "theme": "dark",
}


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    INSTRUCTIONS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Merge with defaults for new keys
            merged = {**DEFAULT_CONFIG, **data}
            return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def list_instructions() -> list[str]:
    ensure_dirs()
    return [f.stem for f in INSTRUCTIONS_DIR.glob("*.txt")]


def load_instruction(name: str) -> str:
    path = INSTRUCTIONS_DIR / f"{name}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def save_instruction(name: str, content: str):
    ensure_dirs()
    path = INSTRUCTIONS_DIR / f"{name}.txt"
    path.write_text(content, encoding="utf-8")


def delete_instruction(name: str):
    path = INSTRUCTIONS_DIR / f"{name}.txt"
    if path.exists():
        path.unlink()
