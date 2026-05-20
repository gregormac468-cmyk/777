"""Точка входа: запуск Telegram-бота «Тихий вечер»."""

import asyncio
import sys

from aiogram import Bot, Dispatcher
from loguru import logger

from src.bot.handlers.start import router as start_router
from src.config import settings


def setup_logging() -> None:
    """Настройка логирования через loguru."""
    logger.remove()  # убираем дефолтный stderr
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
        "<level>{message}</level>",
    )
    logger.add(
        "data/bot.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )


async def main() -> None:
    """Запуск бота в режиме polling."""
    setup_logging()
    logger.info("Запуск бота «Тихий вечер»...")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(start_router)

    # TODO (Phase 2): dp.include_router(keywords_router)
    # TODO (Phase 6): dp.include_router(admin_router)

    logger.info("Бот запущен. Ожидание сообщений...")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())
