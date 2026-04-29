"""
VPSPilot — Power Control & Scheduled Tasks Module
System reboot, shutdown, cron management, and scheduled commands.
"""

from core.executor import execute


async def reboot_system(delay: int = 1, message: str = "Rebooting via VPSPilot") -> str:
    """
    Schedule a system reboot.

    Args:
        delay: Delay in minutes before reboot
        message: Broadcast message to logged-in users
    """
    if delay <= 0:
        return "❌ Delay must be a positive number of minutes."

    if delay == 1:
        result = await execute(f"sudo shutdown -r +{delay} '{message}'")
    else:
        result = await execute(f"sudo shutdown -r +{delay} '{message}'")

    if result.success:
        return (
            f"🔄 *Reboot Scheduled*\n\n"
            f"▸ Delay: {delay} minute(s)\n"
            f"▸ Message: {message}\n\n"
            f"⚠️ Use /cancel_shutdown to abort."
        )

    return f"❌ Failed to schedule reboot:\n```\n{result.stderr}\n```"


async def shutdown_system(delay: int = 1, message: str = "Shutting down via VPSPilot") -> str:
    """
    Schedule a system shutdown.

    Args:
        delay: Delay in minutes before shutdown
        message: Broadcast message to logged-in users
    """
    if delay <= 0:
        return "❌ Delay must be a positive number of minutes."

    result = await execute(f"sudo shutdown -h +{delay} '{message}'")

    if result.success:
        return (
            f"⏹ *Shutdown Scheduled*\n\n"
            f"▸ Delay: {delay} minute(s)\n"
            f"▸ Message: {message}\n\n"
            f"⚠️ Use /cancel_shutdown to abort."
        )

    return f"❌ Failed to schedule shutdown:\n```\n{result.stderr}\n```"


async def cancel_shutdown() -> str:
    """Cancel a pending shutdown or reboot."""
    result = await execute("sudo shutdown -c")

    if result.success:
        return "✅ *Shutdown/Reboot Cancelled*"

    return f"❌ Failed to cancel shutdown:\n```\n{result.stderr}\n```"


async def list_cron() -> str:
    """List all cron jobs for the current user."""
    result = await execute("crontab -l")

    if not result.success:
        if "no crontab" in result.stderr.lower() or "no crontab" in result.stdout.lower():
            return "📋 No cron jobs configured for the current user."
        return f"❌ Failed to list cron jobs:\n```\n{result.stderr}\n```"

    return (
        f"📋 *Cron Jobs*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{result.stdout}\n```"
    )


async def add_cron(schedule: str, command: str) -> str:
    """
    Add a new cron job.

    Args:
        schedule: Cron schedule expression (e.g., "0 3 * * *")
        command: Command to execute
    """
    # Validate schedule format (5 fields)
    parts = schedule.strip().split()
    if len(parts) != 5:
        return (
            "❌ Invalid cron schedule format.\n\n"
            "Expected 5 fields: `min hour day month weekday`\n"
            "Example: `0 3 * * *` (daily at 3:00 AM)"
        )

    # Get existing crontab
    existing = await execute("crontab -l")
    existing_jobs = existing.stdout if existing.success and "no crontab" not in existing.stderr.lower() else ""

    # Add new job
    new_cron = f"{existing_jobs.rstrip()}\n{schedule} {command}\n" if existing_jobs.strip() else f"{schedule} {command}\n"

    result = await execute(f"echo '{new_cron}' | crontab -")

    if result.success:
        return (
            f"✅ *Cron Job Added*\n\n"
            f"▸ Schedule: `{schedule}`\n"
            f"▸ Command: `{command}`"
        )

    return f"❌ Failed to add cron job:\n```\n{result.stderr}\n```"


async def remove_cron(line_number: int) -> str:
    """Remove a cron job by line number."""
    # List current jobs
    existing = await execute("crontab -l")
    if not existing.success:
        return "❌ No cron jobs to remove."

    lines = existing.stdout.strip().split("\n")
    # Filter out comments and empty lines for display, but keep all for removal
    real_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]

    if line_number < 1 or line_number > len(real_lines):
        return f"❌ Invalid line number. Valid range: 1-{len(real_lines)}"

    # Remove the specified line
    removed = real_lines[line_number - 1]
    lines.remove(removed)

    new_cron = "\n".join(lines) + "\n" if lines else ""
    result = await execute(f"echo '{new_cron}' | crontab -")

    if result.success:
        return (
            f"✅ *Cron Job Removed*\n\n"
            f"▸ Removed: `{removed}`"
        )

    return f"❌ Failed to remove cron job:\n```\n{result.stderr}\n```"


async def system_logs(service: str = "syslog", lines: int = 50) -> str:
    """View system logs."""
    effective_lines = min(lines, 200)
    result = await execute(f"journalctl -u {service} -n {effective_lines} --no-pager")

    if not result.success:
        return f"❌ Failed to get logs:\n```\n{result.stderr}\n```"

    output = result.stdout
    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    return (
        f"📜 *System Logs: {service}* (last {effective_lines} lines)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )


async def update_system() -> str:
    """Run system package updates."""
    # Detect package manager
    result = await execute("which apt-get dnf yum pacman 2>/dev/null")

    if "apt-get" in result.stdout:
        result = await execute("sudo apt-get update && sudo apt-get upgrade -y", timeout=300)
    elif "dnf" in result.stdout:
        result = await execute("sudo dnf upgrade -y", timeout=300)
    elif "yum" in result.stdout:
        result = await execute("sudo yum update -y", timeout=300)
    elif "pacman" in result.stdout:
        result = await execute("sudo pacman -Syu --noconfirm", timeout=300)
    else:
        return "❌ No supported package manager found (apt-get, dnf, yum, pacman)."

    output = result.stdout or result.stderr
    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    status = "✅ Success" if result.success else "❌ Failed (or partial)"
    return (
        f"📦 *System Update*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"▸ Status: {status}\n\n"
        f"```\n{output}\n```"
    )
