"""
VPSPilot — Utility Helpers
Shared helper functions used across modules.
"""

import re
from typing import Any


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int with a fallback default."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def sanitize_path(path: str) -> str:
    """
    Sanitize a file path to prevent directory traversal attacks.
    Blocks paths containing '..' components.
    """
    # Remove null bytes
    path = path.replace("\x00", "")

    # Block directory traversal
    parts = path.split("/")
    if ".." in parts:
        raise ValueError("Directory traversal ('..') is not allowed in paths.")

    return path


def validate_command(command: str) -> str:
    """
    Validate and sanitize a shell command.
    Blocks dangerous patterns that could compromise the system.
    """
    dangerous_patterns = [
        r"rm\s+-rf\s+/",           # Recursive force delete from root
        r":\(\)\{.*;\}\s*:",       # Fork bomb
        r"mkfs\.",                  # Format filesystem
        r"dd\s+if=.*of=/dev/",     # Direct device write
        r">\s*/dev/sd",            # Direct device write
        r"chmod\s+777\s+/",        # World-writable root
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            raise ValueError(f"Command contains a blocked pattern for safety: {pattern}")

    return command


def parse_service_name(text: str) -> str | None:
    """Extract a service name from user input text."""
    # Remove common prefixes like 'service', 'systemctl'
    text = text.strip()
    for prefix in ("service ", "systemctl ", "sudo "):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]

    # Remove action words
    for action in ("start ", "stop ", "restart ", "status ", "enable ", "disable ", "reload "):
        if text.lower().startswith(action):
            text = text[len(action):]

    return text.strip() if text.strip() else None


def parse_docker_name(text: str) -> str | None:
    """Extract a Docker container name or ID from user input."""
    text = text.strip()
    # Remove docker prefix
    for prefix in ("docker ", "container "):
        if text.lower().startswith(prefix):
            text = text[len(prefix):]

    return text.strip() if text.strip() else None


def format_uptime(seconds: int) -> str:
    """Format seconds into a human-readable uptime string."""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else f"{seconds}s"
