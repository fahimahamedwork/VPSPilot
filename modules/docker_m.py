"""
VPSPilot — Docker Management Module
Manage Docker containers: list, logs, restart, stop, start, exec, images.
"""

from core.executor import execute


async def docker_ps(all_containers: bool = False) -> str:
    """List Docker containers."""
    flag = "-a" if all_containers else ""
    result = await execute(f"docker ps {flag} --format 'table {{{{.ID}}}}\t{{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Image}}}}\t{{{{.Ports}}}}'")

    if not result.success:
        return f"❌ Failed to list containers:\n```\n{result.stderr}\n```"

    if not result.stdout.strip():
        return "📦 No Docker containers found."

    return (
        f"📦 *Docker Containers*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{result.stdout}\n```"
    )


async def docker_logs(container: str, lines: int = 50) -> str:
    """Get recent logs from a Docker container."""
    effective_lines = min(lines, 200)
    result = await execute(f"docker logs --tail {effective_lines} {container}")

    output = result.stdout
    if result.stderr and "warning" not in result.stderr.lower():
        output += "\n" + result.stderr

    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    return (
        f"📜 *Docker Logs: {container}* (last {effective_lines} lines)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )


async def docker_action(container: str, action: str) -> str:
    """
    Perform an action on a Docker container.

    Args:
        container: Container name or ID
        action: start, stop, restart, pause, unpause, remove
    """
    valid_actions = {"start", "stop", "restart", "pause", "unpause", "remove"}
    if action not in valid_actions:
        return f"❌ Invalid action: `{action}`. Valid: {', '.join(valid_actions)}"

    remove_flag = "-f" if action == "remove" else ""
    result = await execute(f"docker {action} {remove_flag} {container}")

    if result.success:
        action_emoji = {
            "start": "▶️", "stop": "⏹", "restart": "🔄",
            "pause": "⏸", "unpause": "▶️", "remove": "🗑",
        }
        return (
            f"{action_emoji.get(action, '✅')} *Container {action.title()}*\n\n"
            f"▸ Container: `{container}`\n"
            f"▸ Action: {action}\n"
            f"▸ Status: Success"
        )

    return (
        f"❌ *Container {action.title()} Failed*\n\n"
        f"▸ Container: `{container}`\n"
        f"▸ Action: {action}\n"
        f"▸ Error: `{result.stderr}`"
    )


async def docker_exec(container: str, command: str) -> str:
    """Execute a command inside a Docker container."""
    result = await execute(f"docker exec {container} {command}")

    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += ("\n" if output else "") + result.stderr

    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    if not result.success and not result.stdout:
        return f"❌ *Exec Failed*\n\n▸ Container: `{container}`\n▸ Command: `{command}`\n▸ Error: `{result.stderr}`"

    return (
        f"💻 *Docker Exec*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"▸ Container: `{container}`\n"
        f"▸ Command: `{command}`\n"
        f"▸ Exit Code: {result.return_code}\n\n"
        f"```\n{output}\n```"
    )


async def docker_images() -> str:
    """List Docker images."""
    result = await execute("docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}'")

    if not result.success:
        return f"❌ Failed to list images:\n```\n{result.stderr}\n```"

    if not result.stdout.strip():
        return "📦 No Docker images found."

    return (
        f"🖼 *Docker Images*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{result.stdout}\n```"
    )


async def docker_stats() -> str:
    """Get real-time resource usage stats for running containers."""
    result = await execute("docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'")

    if not result.success:
        return f"❌ Failed to get stats:\n```\n{result.stderr}\n```"

    return (
        f"📊 *Docker Stats*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{result.stdout}\n```"
    )


async def docker_compose_action(path: str, action: str) -> str:
    """
    Run docker compose commands.

    Args:
        path: Path to docker-compose.yml directory
        action: up, down, restart, ps, logs
    """
    valid_actions = {"up", "down", "restart", "ps", "logs", "pull"}
    if action not in valid_actions:
        return f"❌ Invalid action: `{action}`. Valid: {', '.join(valid_actions)}"

    detached = "-d" if action == "up" else ""
    result = await execute(f"cd '{path}' && docker compose {action} {detached}")

    output = result.stdout or result.stderr
    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    status = "✅ Success" if result.success else "❌ Failed"
    return (
        f"🐳 *Docker Compose {action.title()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"▸ Path: `{path}`\n"
        f"▸ Action: {action}\n"
        f"▸ Status: {status}\n\n"
        f"```\n{output}\n```"
    )
