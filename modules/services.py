"""
VPSPilot — Service Management Module
Manage systemd services: start, stop, restart, status, enable, disable.
"""

from core.executor import execute


async def service_status(service_name: str) -> str:
    """Get the status of a systemd service."""
    result = await execute(f"systemctl status {service_name} --no-pager -l")

    if result.success or result.return_code in (3, 4):
        # Return code 3 = inactive, 4 = not found — both have useful output
        output = result.stdout or result.stderr
        # Trim very long outputs
        if len(output) > 3000:
            output = output[:3000] + "\n... [truncated]"

        return f"📋 *Service Status: {service_name}*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n```\n{output}\n```"

    return f"❌ Failed to get status for `{service_name}`\n```\n{result.stderr}\n```"


async def service_action(service_name: str, action: str) -> str:
    """
    Perform an action on a systemd service.

    Args:
        service_name: Name of the service
        action: start, stop, restart, reload, enable, disable
    """
    valid_actions = {"start", "stop", "restart", "reload", "enable", "disable"}
    if action not in valid_actions:
        return f"❌ Invalid action: `{action}`. Valid: {', '.join(valid_actions)}"

    result = await execute(f"sudo systemctl {action} {service_name} --no-pager")

    if result.success:
        # Check status after action
        status_result = await execute(f"systemctl is-active {service_name}")
        active_status = status_result.stdout.strip() if status_result.success else "unknown"

        action_emoji = {
            "start": "▶️", "stop": "⏹", "restart": "🔄",
            "reload": "🔃", "enable": "✅", "disable": "⛔",
        }

        return (
            f"{action_emoji.get(action, '✅')} *Service {action.title()}*\n\n"
            f"▸ Service: `{service_name}`\n"
            f"▸ Action: {action}\n"
            f"▸ Current Status: {active_status}"
        )

    return (
        f"❌ *Service {action.title()} Failed*\n\n"
        f"▸ Service: `{service_name}`\n"
        f"▸ Action: {action}\n"
        f"▸ Error: `{result.stderr}`"
    )


async def list_services(state: str = "running") -> str:
    """
    List systemd services filtered by state.

    Args:
        state: running, failed, enabled, disabled, all
    """
    if state == "all":
        result = await execute("systemctl list-units --type=service --no-pager --no-legend")
    elif state == "failed":
        result = await execute("systemctl list-units --type=service --state=failed --no-pager --no-legend")
    elif state == "enabled":
        result = await execute("systemctl list-unit-files --type=service --state=enabled --no-pager --no-legend")
    elif state == "disabled":
        result = await execute("systemctl list-unit-files --type=service --state=disabled --no-pager --no-legend")
    else:
        result = await execute("systemctl list-units --type=service --state=running --no-pager --no-legend")

    if not result.success:
        return f"❌ Failed to list services:\n```\n{result.stderr}\n```"

    output = result.stdout
    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    return (
        f"📋 *Services ({state})*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )


async def service_logs(service_name: str, lines: int = 50, follow: bool = False) -> str:
    """
    Get recent journal logs for a service.

    Args:
        service_name: Name of the service
        lines: Number of log lines to retrieve
        follow: If True, would stream (not supported in Telegram — just gets more lines)
    """
    effective_lines = min(lines, 200)  # Cap at 200 lines
    result = await execute(f"journalctl -u {service_name} -n {effective_lines} --no-pager")

    if not result.success:
        return f"❌ Failed to get logs for `{service_name}`\n```\n{result.stderr}\n```"

    output = result.stdout
    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    return (
        f"📜 *Logs: {service_name}* (last {effective_lines} lines)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )
