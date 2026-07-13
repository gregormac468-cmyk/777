"""Хэндлеры /start и /help."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.messages import HELP, WELCOME

router = Router(name="start")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветственное сообщение при /start."""
    await message.answer(WELCOME, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Подсказка по командам."""
    await message.answer(HELP, parse_mode="HTML")
