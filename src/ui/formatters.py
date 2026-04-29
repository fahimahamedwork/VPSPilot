"""
VPSPilot — Output Formatters
Consistent message formatting and styling utilities.
"""


def header(title: str, emoji: str = "📌") -> str:
    """Create a styled section header."""
    return f"{emoji} *{title}*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"


def truncate(text: str, max_length: int = 4000, suffix: str = "\n... [truncated]") -> str:
    """Truncate text with a suffix indicator."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
