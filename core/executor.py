"""
VPSPilot — Shell Command Executor
Safely executes shell commands with timeout, output truncation, and error handling.
"""

import asyncio
import subprocess
from typing import NamedTuple

from config import Config


class ExecutionResult(NamedTuple):
    """Structured result from a shell command execution."""
    stdout: str
    stderr: str
    return_code: int
    success: bool


async def execute(command: str, timeout: int | None = None) -> ExecutionResult:
    """
    Execute a shell command asynchronously and return structured results.

    Args:
        command: The shell command to run.
        timeout: Override the default timeout in seconds.

    Returns:
        ExecutionResult with stdout, stderr, return_code, and success flag.
    """
    effective_timeout = timeout or Config.SHELL_TIMEOUT

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=effective_timeout
        )

        stdout = _truncate(stdout_bytes.decode("utf-8", errors="replace"))
        stderr = _truncate(stderr_bytes.decode("utf-8", errors="replace"))

        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            return_code=process.returncode or 0,
            success=process.returncode == 0,
        )

    except asyncio.TimeoutError:
        return ExecutionResult(
            stdout="",
            stderr=f"⏱ Command timed out after {effective_timeout}s",
            return_code=-1,
            success=False,
        )
    except Exception as exc:
        return ExecutionResult(
            stdout="",
            stderr=f"❌ Execution error: {exc}",
            return_code=-1,
            success=False,
        )


def _truncate(text: str, max_length: int | None = None) -> str:
    """Truncate text to the maximum allowed output length."""
    limit = max_length or Config.MAX_OUTPUT_LENGTH
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n... [truncated, {len(text) - limit} more characters]"
