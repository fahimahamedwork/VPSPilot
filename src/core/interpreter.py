"""
VPSPilot — Smart Command Interpreter
Translates natural language and shorthand commands into structured actions.

This is the brain of the hybrid terminal-first approach.
Any plain text that isn't a /slash command or menu button gets routed here.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Awaitable


class ActionType(Enum):
    """Types of actions the interpreter can resolve."""
    SHELL = "shell"              # Execute as raw shell command
    SYSTEM = "system"            # Pretty system monitoring
    PROCESS = "process"          # Process management
    SERVICE = "service"          # Service management
    FILESYSTEM = "filesystem"    # File operations
    DOCKER = "docker"            # Docker management
    NETWORK = "network"          # Network tools
    POWER = "power"              # Power & admin
    HELP = "help"                # Show help
    MENU = "menu"                # Show menu
    UNKNOWN = "unknown"          # Fallback to shell


@dataclass
class InterpretedCommand:
    """Structured result from command interpretation."""
    action: ActionType
    sub_action: str              # e.g., "restart", "logs", "overview"
    target: str                  # e.g., service name, container name, path
    extra: str                   # Additional args
    original: str                # The raw input text


# ─── Pattern Definitions ──────────────────────────────────────
# Each pattern maps a natural language / shorthand to an action.
# Patterns are checked in order — first match wins.

# Service patterns: restart nginx, start docker, stop ssh, status nginx, logs nginx
_SERVICE_ACTION_RE = re.compile(
    r"^(?:sudo\s+)?(?:systemctl\s+)?"
    r"(restart|start|stop|reload|enable|disable|status|logs|log)"
    r"\s+(\S+)$",
    re.IGNORECASE,
)

# Docker patterns: docker ps, docker restart x, docker logs x, etc.
_DOCKER_ACTION_RE = re.compile(
    r"^docker\s+"
    r"(ps|logs|start|stop|restart|exec|images|stats|rm|pause|unpause)"
    r"(?:\s+(.+))?$",
    re.IGNORECASE,
)

# Docker exec: docker exec <container> <command>
_DOCKER_EXEC_RE = re.compile(
    r"^docker\s+exec\s+(\S+)\s+(.+)$",
    re.IGNORECASE,
)

# Kill patterns: kill 1234, kill -9 1234, kill -15 1234
_KILL_RE = re.compile(
    r"^kill\s+(?:-(\d+)\s+)?(\d+)$",
    re.IGNORECASE,
)

# Process find: find nginx, ps nginx, pgrep nginx
_PROC_FIND_RE = re.compile(
    r"^(?:find|pgrep|ps\s+find)\s+(\S+)$",
    re.IGNORECASE,
)

# Ping: ping google.com, ping -c 10 google.com
_PING_RE = re.compile(
    r"^ping\s+(?:(?:-c\s+|-n\s+)(\d+)\s+)?(\S+)$",
    re.IGNORECASE,
)

# Traceroute: trace google.com, traceroute google.com
_TRACE_RE = re.compile(
    r"^(?:trace|traceroute)\s+(\S+)$",
    re.IGNORECASE,
)

# DNS: dns google.com, dig google.com, nslookup google.com
_DNS_RE = re.compile(
    r"^(?:dns|dig|nslookup)\s+(\S+)(?:\s+(\S+))?$",
    re.IGNORECASE,
)

# HTTP check: check https://example.com, curl check example.com
_HTTP_RE = re.compile(
    r"^(?:http(?:\s+check)?|check\s+http|curl\s+check)\s+(\S+)$",
    re.IGNORECASE,
)

# Firewall: firewall, ufw status, ufw allow 80
_FW_RE = re.compile(
    r"^(?:firewall|fw|ufw)(?:\s+(status|allow|deny|enable|disable|reload|reset)(?:\s+(.+))?)?$",
    re.IGNORECASE,
)

# Reboot / Shutdown: reboot, shutdown, reboot 5, shutdown now
_POWER_RE = re.compile(
    r"^(reboot|shutdown|poweroff|halt)(?:\s+(\d+|now))?$",
    re.IGNORECASE,
)

# Cancel: cancel shutdown, cancel reboot
_CANCEL_RE = re.compile(
    r"^cancel\s+(?:shutdown|reboot|poweroff)$",
    re.IGNORECASE,
)

# Cron: cron list, cron add, cron remove
_CRON_RE = re.compile(
    r"^cron\s+(list|ls|add|remove|rm)(?:\s+(.+))?$",
    re.IGNORECASE,
)

# Update: update, upgrade, apt update
_UPDATE_RE = re.compile(
    r"^(?:update|upgrade|apt\s+update|apt\s+upgrade|apt-get\s+update|yum\s+update)$",
    re.IGNORECASE,
)

# File read: cat /path, read /path, tail /path, head /path
_FILE_READ_RE = re.compile(
    r"^(?:cat|read|tail|head|less|more)\s+(\S+)$",
    re.IGNORECASE,
)

# File info: stat /path, info /path, file /path
_FILE_INFO_RE = re.compile(
    r"^(?:stat|fileinfo|finfo)\s+(\S+)$",
    re.IGNORECASE,
)

# List directory: ls /path, dir /path, ls
_LS_RE = re.compile(
    r"^(?:ls|dir|list)(?:\s+(\S.*))?$",
    re.IGNORECASE,
)

# Delete: rm /path, del /path
_RM_RE = re.compile(
    r"^(?:rm|del|delete)\s+(.+)$",
    re.IGNORECASE,
)

# Disk usage: df, du, disk, disks
_DISK_RE = re.compile(
    r"^(?:df|du|disk|disks|disk\s+usage)$",
    re.IGNORECASE,
)

# Connections: connections, netstat, ss
_CONN_RE = re.compile(
    r"^(?:connections|netstat|ss|active\s+connections)$",
    re.IGNORECASE,
)

# Ports: ports, listening ports, open ports
_PORTS_RE = re.compile(
    r"^(?:ports|listening|open\s+ports|listen)$",
    re.IGNORECASE,
)


# ─── Shortcut Map ─────────────────────────────────────────────
# Single-word shortcuts that map to pretty formatted /slash outputs

SHORTCUTS: dict[str, tuple[ActionType, str]] = {
    # System shortcuts
    "sys":       (ActionType.SYSTEM, "overview"),
    "system":    (ActionType.SYSTEM, "overview"),
    "cpu":       (ActionType.SYSTEM, "cpu"),
    "mem":       (ActionType.SYSTEM, "memory"),
    "memory":    (ActionType.SYSTEM, "memory"),
    "ram":       (ActionType.SYSTEM, "memory"),
    "disk":      (ActionType.SYSTEM, "disk"),
    "disks":     (ActionType.SYSTEM, "disk"),
    "netif":     (ActionType.SYSTEM, "network"),
    "interfaces":(ActionType.SYSTEM, "network"),
    "uptime":    (ActionType.SYSTEM, "overview"),

    # Process shortcuts
    "top":       (ActionType.PROCESS, "top_cpu"),
    "ps":        (ActionType.PROCESS, "top_cpu"),
    "psm":       (ActionType.PROCESS, "top_mem"),

    # Service shortcuts
    "services":  (ActionType.SERVICE, "list_running"),
    "svcs":      (ActionType.SERVICE, "list_running"),

    # Docker shortcuts
    "docker":    (ActionType.DOCKER, "ps"),
    "dps":       (ActionType.DOCKER, "ps"),
    "containers":(ActionType.DOCKER, "ps"),
    "dimg":      (ActionType.DOCKER, "images"),
    "dstats":    (ActionType.DOCKER, "stats"),

    # Network shortcuts
    "fw":        (ActionType.NETWORK, "firewall"),
    "firewall":  (ActionType.NETWORK, "firewall"),
    "conn":      (ActionType.NETWORK, "connections"),

    # Power shortcuts
    "cron":      (ActionType.POWER, "cron_list"),
    "cronl":     (ActionType.POWER, "cron_list"),

    # Help / Menu
    "help":      (ActionType.HELP, "show"),
    "menu":      (ActionType.MENU, "show"),
}


def interpret(text: str) -> InterpretedCommand:
    """
    Interpret a plain text message and return a structured command.

    Priority:
        1. Exact shortcut match (e.g., "top", "cpu")
        2. Pattern matching (e.g., "restart nginx", "docker ps")
        3. Fallback to raw shell execution
    """
    raw = text.strip()
    normalized = raw.lower()

    # ── 1. Exact shortcut match ──────────────────────────────
    if normalized in SHORTCUTS:
        action_type, sub = SHORTCUTS[normalized]
        return InterpretedCommand(
            action=action_type,
            sub_action=sub,
            target="",
            extra="",
            original=raw,
        )

    # ── 2. Pattern matching (most specific first) ────────────

    # Docker exec (must be before docker action)
    m = _DOCKER_EXEC_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.DOCKER,
            sub_action="exec",
            target=m.group(1),
            extra=m.group(2),
            original=raw,
        )

    # Docker action
    m = _DOCKER_ACTION_RE.match(normalized)
    if m:
        sub = m.group(1)
        target = m.group(2) or ""
        return InterpretedCommand(
            action=ActionType.DOCKER,
            sub_action=sub,
            target=target.strip(),
            extra="",
            original=raw,
        )

    # Service action
    m = _SERVICE_ACTION_RE.match(normalized)
    if m:
        action_word = m.group(1).lower()
        service_name = m.group(2)
        return InterpretedCommand(
            action=ActionType.SERVICE,
            sub_action=action_word,
            target=service_name,
            extra="",
            original=raw,
        )

    # Kill process
    m = _KILL_RE.match(normalized)
    if m:
        signal_num = m.group(1)
        pid = m.group(2)
        force = signal_num == "9"
        return InterpretedCommand(
            action=ActionType.PROCESS,
            sub_action="kill_force" if force else "kill",
            target=pid,
            extra="",
            original=raw,
        )

    # Process find
    m = _PROC_FIND_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.PROCESS,
            sub_action="find",
            target=m.group(1),
            extra="",
            original=raw,
        )

    # Ping
    m = _PING_RE.match(normalized)
    if m:
        count = m.group(1) or "4"
        host = m.group(2)
        return InterpretedCommand(
            action=ActionType.NETWORK,
            sub_action="ping",
            target=host,
            extra=count,
            original=raw,
        )

    # Traceroute
    m = _TRACE_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.NETWORK,
            sub_action="traceroute",
            target=m.group(1),
            extra="",
            original=raw,
        )

    # DNS
    m = _DNS_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.NETWORK,
            sub_action="dns",
            target=m.group(1),
            extra=m.group(2) or "A",
            original=raw,
        )

    # HTTP check
    m = _HTTP_RE.match(normalized)
    if m:
        url = m.group(1)
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return InterpretedCommand(
            action=ActionType.NETWORK,
            sub_action="http",
            target=url,
            extra="",
            original=raw,
        )

    # Firewall
    m = _FW_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.NETWORK,
            sub_action=m.group(1) or "status",
            target=m.group(2) or "",
            extra="",
            original=raw,
        )

    # Power (reboot/shutdown)
    m = _POWER_RE.match(normalized)
    if m:
        action_word = m.group(1).lower()
        delay = m.group(2) or "1"
        if delay == "now":
            delay = "0"
        return InterpretedCommand(
            action=ActionType.POWER,
            sub_action="reboot" if action_word in ("reboot",) else "shutdown",
            target=delay,
            extra="",
            original=raw,
        )

    # Cancel shutdown/reboot
    m = _CANCEL_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.POWER,
            sub_action="cancel",
            target="",
            extra="",
            original=raw,
        )

    # Cron
    m = _CRON_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.POWER,
            sub_action=f"cron_{m.group(1).lower().replace('ls', 'list')}",
            target=m.group(2) or "",
            extra="",
            original=raw,
        )

    # Update
    m = _UPDATE_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.POWER,
            sub_action="update",
            target="",
            extra="",
            original=raw,
        )

    # File read
    m = _FILE_READ_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.FILESYSTEM,
            sub_action="read",
            target=m.group(1),
            extra="",
            original=raw,
        )

    # File info
    m = _FILE_INFO_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.FILESYSTEM,
            sub_action="info",
            target=m.group(1),
            extra="",
            original=raw,
        )

    # List directory
    m = _LS_RE.match(normalized)
    if m:
        return InterpretedCommand(
            action=ActionType.FILESYSTEM,
            sub_action="list",
            target=m.group(1) or "/",
            extra="",
            original=raw,
        )

    # Delete
    m = _RM_RE.match(normalized)
    if m:
        path = m.group(1).strip()
        is_recursive = "-r" in path or "-rf" in path
        # Clean flags from path
        path = re.sub(r"^-\w+\s+", "", path).strip()
        return InterpretedCommand(
            action=ActionType.FILESYSTEM,
            sub_action="delete_recursive" if is_recursive else "delete",
            target=path,
            extra="",
            original=raw,
        )

    # Disk usage
    if _DISK_RE.match(normalized):
        return InterpretedCommand(
            action=ActionType.SYSTEM,
            sub_action="disk_usage",
            target="",
            extra="",
            original=raw,
        )

    # Connections
    if _CONN_RE.match(normalized):
        return InterpretedCommand(
            action=ActionType.NETWORK,
            sub_action="connections",
            target="",
            extra="",
            original=raw,
        )

    # Ports
    if _PORTS_RE.match(normalized):
        return InterpretedCommand(
            action=ActionType.NETWORK,
            sub_action="ports",
            target="",
            extra="",
            original=raw,
        )

    # ── 3. Fallback: raw shell command ───────────────────────
    return InterpretedCommand(
        action=ActionType.SHELL,
        sub_action="execute",
        target="",
        extra="",
        original=raw,
    )
