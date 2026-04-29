"""
VPSPilot — Configuration Management
Loads settings from environment variables and .env files.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root (one level up from src/)
load_dotenv(Path(__file__).parent.parent / ".env")


class Config:
    """Centralized configuration with sensible defaults and validation."""

    # ── Telegram ──────────────────────────────────────────────
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    AUTHORIZED_USERS: list[int] = [
        int(uid.strip())
        for uid in os.getenv("AUTHORIZED_USERS", "").split(",")
        if uid.strip().isdigit()
    ]

    # ── Shell Execution ──────────────────────────────────────
    SHELL_TIMEOUT: int = int(os.getenv("SHELL_TIMEOUT", "30"))
    MAX_OUTPUT_LENGTH: int = int(os.getenv("MAX_OUTPUT_LENGTH", "4000"))

    # ── Logging ──────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # ── Project Metadata ─────────────────────────────────────
    PROJECT_NAME: str = "VPSPilot"
    VERSION: str = "1.0.0"

    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration values are present."""
        errors: list[str] = []

        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required — get one from @BotFather")

        if not cls.AUTHORIZED_USERS:
            errors.append("AUTHORIZED_USERS is required — add your Telegram user ID")

        if errors:
            raise EnvironmentError(
                "Configuration errors:\n  • " + "\n  • ".join(errors)
            )


# Validate on import so we fail fast
Config.validate()
