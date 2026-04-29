"""
VPSPilot — Output Formatters
Consistent message formatting and styling utilities.
"""

import html
from datetime import datetime
from typing import Any


def header(title: str, emoji: str = "📌") -> str:
    """Create a styled section header."""
    return f"{emoji} *{title}*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"


def key_value(data: dict[str, Any], indent: int = 0) -> str:
    """Format a dictionary as a styled key-value list."""
    prefix = "  " * indent
    lines = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}▸ *{key}:*")
            lines.append(key_value(value, indent + 1))
        else:
            lines.append(f"{prefix}▸ {key}: `{value}`")
    return "\n".join(lines)


def code_block(content: str, language: str = "") -> str:
    """Wrap content in a Markdown code block."""
    return f"```{language}\n{content}\n```"


def progress_bar(percent: float, length: int = 20, fill: str = "█", empty: str = "░") -> str:
    """Create a visual progress bar."""
    filled = int(percent / 100 * length)
    return f"{fill * filled}{empty * (length - filled)}"


def timestamp() -> str:
    """Return current timestamp as a formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def size_human(bytes_size: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(bytes_size) < 1024:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f}PB"


def truncate(text: str, max_length: int = 4000, suffix: str = "\n... [truncated]") -> str:
    """Truncate text with a suffix indicator."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def escape_markdown(text: str) -> str:
    """Escape special MarkdownV2 characters."""
    special = "_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)
