"""
VPSPilot — Network Module
Network diagnostics, port scanning, firewall management, and DNS tools.
"""

from core.executor import execute


async def ping(host: str, count: int = 4) -> str:
    """Ping a host and return results."""
    result = await execute(f"ping -c {count} -W 5 {host}")

    if not result.success and not result.stdout:
        return f"❌ Ping failed for `{host}`:\n```\n{result.stderr}\n```"

    output = result.stdout
    if len(output) > 3000:
        output = output[:3000] + "\n... [truncated]"

    return (
        f"🏓 *Ping: {host}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )


async def traceroute(host: str) -> str:
    """Perform a traceroute to a host."""
    result = await execute(f"traceroute -m 30 -w 3 {host}", timeout=45)

    if not result.success and not result.stdout:
        return f"❌ Traceroute failed for `{host}`:\n```\n{result.stderr}\n```"

    output = result.stdout
    if len(output) > 3000:
        output = output[:3000] + "\n... [truncated]"

    return (
        f"🗺 *Traceroute: {host}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )


async def dns_lookup(domain: str, record_type: str = "A") -> str:
    """Perform a DNS lookup."""
    result = await execute(f"dig {domain} {record_type} +short")

    if not result.stdout.strip():
        # Try nslookup as fallback
        result = await execute(f"nslookup -type={record_type} {domain}")

    output = result.stdout or result.stderr
    if len(output) > 2000:
        output = output[:2000] + "\n... [truncated]"

    return (
        f"🌐 *DNS Lookup: {domain}* ({record_type})\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )


async def check_ports(target: str = "localhost", ports: str = "") -> str:
    """
    Check if specific ports are open.

    Args:
        target: Target host
        ports: Comma-separated port list, or common for well-known ports
    """
    if ports.lower() == "common":
        ports = "22,80,443,3306,5432,6379,8080,8443,27017"
    elif not ports:
        # Show listening ports instead
        result = await execute("ss -tlnp")
        if not result.success:
            return f"❌ Failed to list ports:\n```\n{result.stderr}\n```"
        return (
            f"🔌 *Listening Ports*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"```\n{result.stdout}\n```"
        )

    lines = [f"🔌 *Port Check: {target}*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    for port in ports.split(","):
        port = port.strip()
        result = await execute(f"timeout 3 bash -c 'echo >/dev/tcp/{target}/{port}' 2>/dev/null && echo OPEN || echo CLOSED")
        status = result.stdout.strip() if result.success else "CLOSED"
        emoji = "🟢" if status == "OPEN" else "🔴"
        lines.append(f"  {emoji} Port {port}: {status}")

    return "\n".join(lines)


async def firewall_status() -> str:
    """Show firewall status (UFW or iptables)."""
    # Try UFW first
    result = await execute("sudo ufw status verbose")

    if result.success and "command not found" not in result.stderr:
        output = result.stdout
        if len(output) > 3500:
            output = output[:3500] + "\n... [truncated]"

        return (
            f"🛡 *Firewall Status (UFW)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"```\n{output}\n```"
        )

    # Fallback to iptables
    result = await execute("sudo iptables -L -n -v --line-numbers")

    if result.success:
        output = result.stdout
        if len(output) > 3500:
            output = output[:3500] + "\n... [truncated]"

        return (
            f"🛡 *Firewall Status (iptables)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"```\n{output}\n```"
        )

    return "❌ Could not retrieve firewall status. Neither UFW nor iptables available."


async def firewall_action(action: str, rule: str = "") -> str:
    """
    Manage UFW firewall rules.

    Args:
        action: enable, disable, reload, allow, deny, delete, reset
        rule: Rule specification (e.g., "80/tcp", "from 1.2.3.4")
    """
    valid_actions = {"enable", "disable", "reload", "allow", "deny", "delete", "reset"}
    if action not in valid_actions:
        return f"❌ Invalid action: `{action}`. Valid: {', '.join(valid_actions)}"

    if action in ("allow", "deny", "delete") and not rule:
        return f"❌ Action `{action}` requires a rule. Example: `80/tcp`, `from 1.2.3.4`"

    if action in ("enable", "disable", "reload", "reset"):
        cmd = f"sudo ufw --force {action}"
    else:
        cmd = f"sudo ufw {action} {rule}"

    result = await execute(cmd)

    output = result.stdout or result.stderr
    status = "✅ Success" if result.success else "❌ Failed"

    return (
        f"🛡 *Firewall: {action.title()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"▸ Action: {action}\n"
        f"▸ Rule: {rule or 'N/A'}\n"
        f"▸ Status: {status}\n\n"
        f"```\n{output}\n```"
    )


async def http_check(url: str) -> str:
    """Check HTTP response code and timing for a URL."""
    result = await execute(f"curl -o /dev/null -s -w 'HTTP_CODE:%{{http_code}} TIME_TOTAL:%{{time_total}}s TIME_CONNECT:%{{time_connect}}s SIZE_DOWNLOAD:%{{size_download}}' '{url}'", timeout=15)

    if not result.success:
        return f"❌ HTTP check failed for `{url}`:\n```\n{result.stderr}\n```"

    output = result.stdout.strip()
    parts = {}
    for part in output.split():
        if ":" in part:
            key, value = part.split(":", 1)
            parts[key] = value

    http_code = parts.get("HTTP_CODE", "N/A")
    time_total = parts.get("TIME_TOTAL", "N/A")
    time_connect = parts.get("TIME_CONNECT", "N/A")
    size = parts.get("SIZE_DOWNLOAD", "N/A")

    code_emoji = "🟢" if http_code.startswith("2") else "🟡" if http_code.startswith("3") else "🔴"

    return (
        f"🌐 *HTTP Check: {url}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"  {code_emoji} Status: {http_code}\n"
        f"  ⏱ Total Time: {time_total}s\n"
        f"  🔗 Connect Time: {time_connect}s\n"
        f"  📦 Size: {size} bytes"
    )


async def connections_summary() -> str:
    """Show a summary of network connections by state."""
    result = await execute("ss -tunap")

    if not result.success:
        return f"❌ Failed to get connections:\n```\n{result.stderr}\n```"

    output = result.stdout
    if len(output) > 3500:
        output = output[:3500] + "\n... [truncated]"

    return (
        f"🔗 *Active Connections*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"```\n{output}\n```"
    )
