"""
VPSPilot — Filesystem Module
Navigate, read, upload, download, and manage files on the VPS.
"""

import os
from pathlib import Path

import aiofiles

from core.executor import execute
from config import Config


async def list_directory(path: str = "/", show_hidden: bool = False) -> str:
    """
    List contents of a directory with file sizes and types.

    Args:
        path: Directory path to list
        show_hidden: Include hidden files
    """
    # Normalize path
    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return f"❌ `{path}` is not a valid directory."

    result = await execute(
        f"ls -lh{'a' if show_hidden else ''} --group-directories-first '{path}'"
    )

    if not result.success:
        return f"❌ Failed to list `{path}`:\n```\n{result.stderr}\n```"

    # Get disk usage for the directory
    du_result = await execute(f"du -sh '{path}'")
    du_info = du_result.stdout.strip() if du_result.success else ""

    output = result.stdout
    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    return (
        f"📂 *Directory: {path}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{'Size: ' + du_info if du_info else ''}\n\n"
        f"```\n{output}\n```"
    )


async def read_file(path: str, lines: int = 100) -> str:
    """
    Read and display the contents of a text file.

    Args:
        path: File path to read
        lines: Number of lines to read (from the end for large files)
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return f"❌ File not found: `{path}`"

    if os.path.isdir(path):
        return f"❌ `{path}` is a directory, not a file. Use /ls to list."

    # Check file size — skip very large files
    size = os.path.getsize(path)
    if size > 5 * 1024 * 1024:  # 5MB
        return f"❌ File too large ({size / (1024**2):.1f}MB). Use /shell `head` or `tail` instead."

    try:
        async with aiofiles.open(path, "r", errors="replace") as f:
            all_lines = await f.readlines()

        total_lines = len(all_lines)
        display_lines = all_lines[-lines:] if total_lines > lines else all_lines
        content = "".join(display_lines)

        if len(content) > Config.MAX_OUTPUT_LENGTH:
            content = content[: Config.MAX_OUTPUT_LENGTH] + "\n... [truncated]"

        header = f"📄 *File: {path}*\n"
        if total_lines > lines:
            header += f"Showing last {lines} of {total_lines} lines\n"

        return (
            f"{header}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"```\n{content}\n```"
        )

    except PermissionError:
        return f"🚫 Permission denied: `{path}`"
    except Exception as exc:
        return f"❌ Error reading file: {exc}"


async def file_info(path: str) -> str:
    """Get detailed file/directory information."""
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return f"❌ Path not found: `{path}`"

    stat = os.stat(path)
    import time
    from datetime import datetime

    size_str = _human_size(stat.st_size)
    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    access_time = datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")
    file_type = "Directory" if os.path.isdir(path) else "File"
    permissions = oct(stat.st_mode)[-3:]

    # Get owner info
    import pwd
    try:
        owner = pwd.getpwuid(stat.st_uid).pw_name
    except (KeyError, ImportError):
        owner = str(stat.st_uid)
    try:
        group = pwd.getpwgid(stat.st_gid).pw_name
    except (KeyError, ImportError):
        group = str(stat.st_gid)

    return (
        f"ℹ️ *File Info*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"▸ Path: `{path}`\n"
        f"▸ Type: {file_type}\n"
        f"▸ Size: {size_str}\n"
        f"▸ Permissions: {permissions}\n"
        f"▸ Owner: {owner}:{group}\n"
        f"▸ Modified: {mod_time}\n"
        f"▸ Accessed: {access_time}"
    )


async def remove_file(path: str, recursive: bool = False) -> str:
    """
    Remove a file or directory.

    Args:
        path: Path to remove
        recursive: Use -rf for directories
    """
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        return f"❌ Path not found: `{path}`"

    if os.path.isdir(path) and not recursive:
        return f"❌ `{path}` is a directory. Use recursive=True to delete."

    flag = "-rf" if recursive else "-f"
    result = await execute(f"rm {flag} '{path}'")

    if result.success:
        return f"✅ Deleted: `{path}`"

    return f"❌ Failed to delete `{path}`:\n```\n{result.stderr}\n```"


async def disk_usage() -> str:
    """Show disk usage for all mounted filesystems."""
    result = await execute("df -h --type=ext4 --type=xfs --type=btrfs --type=tmpfs --type=overlay 2>/dev/null || df -h")

    if not result.success:
        return f"❌ Failed to get disk usage:\n```\n{result.stderr}\n```"

    return (
        f"💾 *Disk Usage*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{result.stdout}\n```"
    )


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}PB"
