"""Конфигурация бота из переменных окружения (.env файл)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения. Загружаются из .env файла."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === Telegram ===
    bot_token: str
    admin_telegram_id: int

    # === Database ===
    db_url: str = "sqlite+aiosqlite:///data/bot.db"

    # === Logging ===
    log_level: str = "INFO"

    # === Payments (Phase 4) ===
    yookassa_shop_id: str | None = None
    yookassa_secret_key: str | None = None
    tinkoff_terminal_key: str | None = None
    tinkoff_secret_key: str | None = None

    # === Telegram Channel (Phase 5) ===
    product_channel_id: int | None = None


# Singleton — импортируй settings из любого модуля
settings = Settings()  # type: ignore[call-arg]
