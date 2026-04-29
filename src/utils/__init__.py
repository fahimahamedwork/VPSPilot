"""
VPSPilot — Utility Helpers
Shared helper functions used across modules.
"""

import re


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
