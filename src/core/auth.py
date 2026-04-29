"""
VPSPilot — Authentication & Authorization
Ensures only approved Telegram users can interact with the bot.
"""

from functools import wraps
from typing import Callable, Any

from telegram import Update
from telegram.ext import ContextTypes

from config import Config


def authorized_only(func: Callable) -> Callable:
    """
    Decorator that restricts bot access to authorized users only.
    Unauthorized users receive a brief denial message.
    """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        if not update.effective_user:
            return

        user_id = update.effective_user.id

        if user_id not in Config.AUTHORIZED_USERS:
            if update.message:
                await update.message.reply_text(
                    "🚫 Access Denied\n\n"
                    f"Your Telegram ID: `{user_id}`\n"
                    "You are not authorized to use this bot.\n"
                    "Add your ID to AUTHORIZED_USERS in .env",
                    parse_mode="Markdown",
                )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper
