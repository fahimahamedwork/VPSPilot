#!/usr/bin/env python3
"""
VPSPilot — Telegram VPS Control Bot
Full-featured Telegram bot for remote VPS management.

Usage:
    python bot.py

Set up your .env file first (see .env.example).
"""

import logging
import re
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import Config
from core.auth import authorized_only
from core.executor import execute
from ui.keyboards import (
    main_menu_keyboard,
    system_keyboard,
    processes_keyboard,
    services_keyboard,
    files_keyboard,
    docker_keyboard,
    network_keyboard,
    power_keyboard,
)
from ui.formatters import header, truncate
from modules import system, processes, services, filesystem, docker_m, network, power
from utils import sanitize_path, validate_command, parse_service_name

# ─── Logging Setup ───────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(Config.PROJECT_NAME)

# ─── Conversation States ─────────────────────────────────────
# Used for multi-step inputs (e.g., asking for a service name)

WAITING_SERVICE_NAME = 1
WAITING_SERVICE_LOGS = 2
WAITING_PROCESS_PID = 3
WAITING_PROCESS_KILL = 4
WAITING_PROCESS_SEARCH = 5
WAITING_DIR_PATH = 6
WAITING_FILE_PATH = 7
WAITING_FILE_DELETE = 8
WAITING_SHELL_COMMAND = 9
WAITING_DOCKER_CONTAINER = 10
WAITING_DOCKER_EXEC = 11
WAITING_DOCKER_LOGS = 12
WAITING_PING_HOST = 13
WAITING_TRACE_HOST = 14
WAITING_DNS_DOMAIN = 15
WAITING_PORT_CHECK = 16
WAITING_HTTP_URL = 17
WAITING_CRON_SCHEDULE = 18
WAITING_CRON_COMMAND = 19
WAITING_CRON_REMOVE = 20
WAITING_FW_ACTION = 21
WAITING_REBOOT_DELAY = 22
WAITING_SHUTDOWN_DELAY = 23
WAITING_SYSLOG_SERVICE = 24
WAITING_FS_INFO = 25


# ═══════════════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — display welcome message and main menu."""
    user = update.effective_user
    text = (
        f"🛩 *Welcome to VPSPilot!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Hello, *{user.first_name}*!\n\n"
        f"Your personal VPS command center is ready. "
        f"Use the menu buttons below or type commands directly.\n\n"
        f"🔑 *Your Telegram ID:* `{user.id}`\n"
        f"🖥 *Host:* `{update.effective_chat.id}`\n\n"
        f"💡 *Quick Commands:*\n"
        f"  /sys — System overview\n"
        f"  /shell <cmd> — Run a command\n"
        f"  /ps — Top processes\n"
        f"  /help — Full command list"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — show all available commands."""
    text = (
        f"📖 *VPSPilot Command Reference*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🖥 *System Monitoring*\n"
        f"  /sys — Full system overview\n"
        f"  /cpu — Detailed CPU info\n"
        f"  /mem — Detailed memory info\n"
        f"  /disk — Disk partition info\n"
        f"  /netif — Network interfaces\n"
        f"  /df — Disk usage summary\n\n"
        f"⚙ *Process Management*\n"
        f"  /ps — Top processes by CPU\n"
        f"  /psm — Top processes by memory\n"
        f"  /proc <pid> — Process details\n"
        f"  /find <name> — Find process\n"
        f"  /kill <pid> — Kill process (SIGTERM)\n"
        f"  /killf <pid> — Force kill (SIGKILL)\n\n"
        f"🔧 *Service Management*\n"
        f"  /svc <name> — Service status\n"
        f"  /svcr <name> — Restart service\n"
        f"  /svcs <name> — Stop service\n"
        f"  /svca <name> — Start service\n"
        f"  /svcl <name> — Service logs\n"
        f"  /svclist [running|failed|all] — List services\n\n"
        f"📂 *Filesystem*\n"
        f"  /ls <path> — List directory\n"
        f"  /cat <path> — Read file\n"
        f"  /finfo <path> — File info\n"
        f"  /rm <path> — Delete file\n"
        f"  /rmrf <path> — Delete directory\n\n"
        f"🐳 *Docker*\n"
        f"  /dps — Running containers\n"
        f"  /dpsa — All containers\n"
        f"  /dimg — Docker images\n"
        f"  /dstats — Container stats\n"
        f"  /dlog <container> — Container logs\n"
        f"  /dstart <container> — Start container\n"
        f"  /dstop <container> — Stop container\n"
        f"  /drestart <container> — Restart container\n"
        f"  /dexec <container> <cmd> — Exec in container\n\n"
        f"🌐 *Network*\n"
        f"  /ping <host> — Ping host\n"
        f"  /trace <host> — Traceroute\n"
        f"  /dns <domain> — DNS lookup\n"
        f"  /ports — Listening ports\n"
        f"  /fw — Firewall status\n"
        f"  /conn — Active connections\n"
        f"  /http <url> — HTTP check\n\n"
        f"⚡ *Power & Admin*\n"
        f"  /reboot [min] — Schedule reboot\n"
        f"  /shutdown [min] — Schedule shutdown\n"
        f"  /cancel — Cancel shutdown/reboot\n"
        f"  /cronl — List cron jobs\n"
        f"  /update — System update\n"
        f"  /syslog [service] — System logs\n\n"
        f"🖥 *Shell*\n"
        f"  /shell <command> — Execute shell command"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── System Commands ─────────────────────────────────────────


@authorized_only
async def sys_overview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """System overview with all key metrics."""
    msg = await _reply_loading(update)
    result = await system.get_overview()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def sys_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detailed CPU information."""
    msg = await _reply_loading(update)
    result = await system.get_cpu_detailed()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def sys_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detailed memory information."""
    msg = await _reply_loading(update)
    result = await system.get_memory_detailed()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def sys_disk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detailed disk partition information."""
    msg = await _reply_loading(update)
    result = await system.get_disk_detailed()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def sys_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Network interface information."""
    msg = await _reply_loading(update)
    result = await system.get_network_interfaces()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def sys_df(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Disk usage summary."""
    msg = await _reply_loading(update)
    result = await filesystem.disk_usage()
    await msg.edit_text(result, parse_mode="Markdown")


# ─── Process Commands ────────────────────────────────────────


@authorized_only
async def proc_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List top processes by CPU."""
    msg = await _reply_loading(update)
    result = await processes.list_processes(sort_by="cpu")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def proc_list_mem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List top processes by memory."""
    msg = await _reply_loading(update)
    result = await processes.list_processes(sort_by="memory")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def proc_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show process details by PID."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/proc <PID>`", parse_mode="Markdown")
        return

    pid = _safe_int(context.args[0])
    if pid == 0:
        await update.message.reply_text("❌ Invalid PID.")
        return

    msg = await _reply_loading(update)
    result = await processes.get_process_info(pid)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def proc_find(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for processes by name."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/find <name>`", parse_mode="Markdown")
        return

    name = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await processes.find_process(name)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def proc_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kill a process by PID (SIGTERM)."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/kill <PID>`", parse_mode="Markdown")
        return

    pid = _safe_int(context.args[0])
    if pid == 0:
        await update.message.reply_text("❌ Invalid PID.")
        return

    msg = await _reply_loading(update)
    result = await processes.kill_process(pid, force=False)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def proc_kill_force(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Force kill a process by PID (SIGKILL)."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/killf <PID>`", parse_mode="Markdown")
        return

    pid = _safe_int(context.args[0])
    if pid == 0:
        await update.message.reply_text("❌ Invalid PID.")
        return

    msg = await _reply_loading(update)
    result = await processes.kill_process(pid, force=True)
    await msg.edit_text(result, parse_mode="Markdown")


# ─── Service Commands ────────────────────────────────────────


@authorized_only
async def svc_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get service status."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svc <service_name>`", parse_mode="Markdown")
        return

    service_name = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await services.service_status(service_name)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def svc_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart a service."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svcr <service_name>`", parse_mode="Markdown")
        return

    service_name = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await services.service_action(service_name, "restart")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def svc_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop a service."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svcs <service_name>`", parse_mode="Markdown")
        return

    service_name = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await services.service_action(service_name, "stop")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def svc_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a service."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svca <service_name>`", parse_mode="Markdown")
        return

    service_name = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await services.service_action(service_name, "start")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def svc_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get service logs."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svcl <service_name>`", parse_mode="Markdown")
        return

    service_name = " ".join(context.args)
    lines = 50
    if len(context.args) > 1 and context.args[-1].isdigit():
        lines = int(context.args[-1])
        service_name = " ".join(context.args[:-1])

    msg = await _reply_loading(update)
    result = await services.service_logs(service_name, lines)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def svc_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List services by state."""
    state = context.args[0] if context.args else "running"
    msg = await _reply_loading(update)
    result = await services.list_services(state)
    await msg.edit_text(result, parse_mode="Markdown")


# ─── Filesystem Commands ─────────────────────────────────────


@authorized_only
async def fs_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List directory contents."""
    path = context.args[0] if context.args else "/"
    try:
        path = sanitize_path(path)
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}")
        return

    msg = await _reply_loading(update)
    result = await filesystem.list_directory(path)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def fs_read(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Read a file's contents."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/cat <file_path>`", parse_mode="Markdown")
        return

    path = " ".join(context.args)
    try:
        path = sanitize_path(path)
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}")
        return

    msg = await _reply_loading(update)
    result = await filesystem.read_file(path)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def fs_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get file/directory info."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/finfo <path>`", parse_mode="Markdown")
        return

    path = " ".join(context.args)
    try:
        path = sanitize_path(path)
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}")
        return

    msg = await _reply_loading(update)
    result = await filesystem.file_info(path)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def fs_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a file."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/rm <file_path>`", parse_mode="Markdown")
        return

    path = " ".join(context.args)
    try:
        path = sanitize_path(path)
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}")
        return

    msg = await _reply_loading(update)
    result = await filesystem.remove_file(path, recursive=False)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def fs_remove_recursive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a directory recursively."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/rmrf <dir_path>`", parse_mode="Markdown")
        return

    path = " ".join(context.args)
    try:
        path = sanitize_path(path)
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}")
        return

    msg = await _reply_loading(update)
    result = await filesystem.remove_file(path, recursive=True)
    await msg.edit_text(result, parse_mode="Markdown")


# ─── Docker Commands ─────────────────────────────────────────


@authorized_only
async def dkr_ps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List running Docker containers."""
    msg = await _reply_loading(update)
    result = await docker_m.docker_ps(all_containers=False)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_ps_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all Docker containers."""
    msg = await _reply_loading(update)
    result = await docker_m.docker_ps(all_containers=True)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List Docker images."""
    msg = await _reply_loading(update)
    result = await docker_m.docker_images()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Docker container resource stats."""
    msg = await _reply_loading(update)
    result = await docker_m.docker_stats()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get Docker container logs."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/dlog <container>`", parse_mode="Markdown")
        return

    container = context.args[0]
    lines = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 50

    msg = await _reply_loading(update)
    result = await docker_m.docker_logs(container, lines)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a Docker container."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/dstart <container>`", parse_mode="Markdown")
        return

    container = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await docker_m.docker_action(container, "start")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop a Docker container."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/dstop <container>`", parse_mode="Markdown")
        return

    container = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await docker_m.docker_action(container, "stop")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart a Docker container."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/drestart <container>`", parse_mode="Markdown")
        return

    container = " ".join(context.args)
    msg = await _reply_loading(update)
    result = await docker_m.docker_action(container, "restart")
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def dkr_exec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute a command in a Docker container."""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: `/dexec <container> <command>`", parse_mode="Markdown")
        return

    container = context.args[0]
    command = " ".join(context.args[1:])

    msg = await _reply_loading(update)
    result = await docker_m.docker_exec(container, command)
    await msg.edit_text(result, parse_mode="Markdown")


# ─── Network Commands ────────────────────────────────────────


@authorized_only
async def net_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping a host."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/ping <host>`", parse_mode="Markdown")
        return

    host = context.args[0]
    count = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 4

    msg = await _reply_loading(update)
    result = await network.ping(host, count)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def net_trace(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Traceroute to a host."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/trace <host>`", parse_mode="Markdown")
        return

    host = context.args[0]
    msg = await _reply_loading(update)
    result = await network.traceroute(host)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def net_dns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """DNS lookup."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/dns <domain> [type]`", parse_mode="Markdown")
        return

    domain = context.args[0]
    record_type = context.args[1] if len(context.args) > 1 else "A"

    msg = await _reply_loading(update)
    result = await network.dns_lookup(domain, record_type)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def net_ports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check listening ports."""
    msg = await _reply_loading(update)
    target = context.args[0] if context.args else "localhost"
    ports = ",".join(context.args[1:]) if len(context.args) > 1 else ""
    result = await network.check_ports(target, ports)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def net_fw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Firewall status."""
    msg = await _reply_loading(update)
    result = await network.firewall_status()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def net_conn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Active connections."""
    msg = await _reply_loading(update)
    result = await network.connections_summary()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def net_http(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """HTTP check for a URL."""
    if not context.args:
        await update.message.reply_text("❌ Usage: `/http <url>`", parse_mode="Markdown")
        return

    url = context.args[0]
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    msg = await _reply_loading(update)
    result = await network.http_check(url)
    await msg.edit_text(result, parse_mode="Markdown")


# ─── Power & Admin Commands ──────────────────────────────────


@authorized_only
async def pwr_reboot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Schedule a system reboot."""
    delay = int(context.args[0]) if context.args and context.args[0].isdigit() else 1

    msg = await _reply_loading(update)
    result = await power.reboot_system(delay)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def pwr_shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Schedule a system shutdown."""
    delay = int(context.args[0]) if context.args and context.args[0].isdigit() else 1

    msg = await _reply_loading(update)
    result = await power.shutdown_system(delay)
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def pwr_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel pending shutdown/reboot."""
    msg = await _reply_loading(update)
    result = await power.cancel_shutdown()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def pwr_cron_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List cron jobs."""
    msg = await _reply_loading(update)
    result = await power.list_cron()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def pwr_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run system update."""
    msg = await _reply_loading(update)
    result = await power.update_system()
    await msg.edit_text(result, parse_mode="Markdown")


@authorized_only
async def pwr_syslog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View system logs."""
    service = context.args[0] if context.args else "syslog"
    msg = await _reply_loading(update)
    result = await power.system_logs(service)
    await msg.edit_text(result, parse_mode="Markdown")


# ─── Shell Command ───────────────────────────────────────────


@authorized_only
async def shell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute an arbitrary shell command."""
    if not context.args:
        await update.message.reply_text(
            "🖥 *Shell Execution*\n\n"
            "Usage: `/shell <command>`\n\n"
            "Example: `/shell uptime`\n"
            "Example: `/shell df -h`",
            parse_mode="Markdown",
        )
        return

    command = " ".join(context.args)

    # Validate command for safety
    try:
        validate_command(command)
    except ValueError as exc:
        await update.message.reply_text(f"🚫 *Blocked:* {exc}", parse_mode="Markdown")
        return

    msg = await _reply_loading(update)
    result = await execute(command)

    output = ""
    if result.stdout:
        output += result.stdout
    if result.stderr:
        output += ("\n" if output else "") + result.stderr

    if not output.strip():
        output = "(no output)"

    output = truncate(output)

    status_emoji = "✅" if result.success else "❌"
    text = (
        f"🖥 *Shell Result* {status_emoji}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"▸ Command: `{command}`\n"
        f"▸ Exit Code: {result.return_code}\n\n"
        f"{header('Output')}\n```\n{output}\n```"
    )

    await msg.edit_text(text, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLERS (Inline Keyboard Buttons)
# ═══════════════════════════════════════════════════════════════


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if user_id not in Config.AUTHORIZED_USERS:
        await query.answer("🚫 Unauthorized", show_alert=True)
        return

    data = query.data
    logger.info(f"Callback: {data} from user {user_id}")

    # ─── Menu Navigation ─────────────────────────────────────
    if data == "menu_back":
        await query.edit_message_text(
            "🛩 *VPSPilot Main Menu*\n\nSelect a category:",
            parse_mode="Markdown",
            reply_markup=system_keyboard(),  # We'll use a dynamic approach below
        )
        # Actually, show main menu text
        await query.edit_message_text(
            "🛩 *VPSPilot Control Panel*\n\nUse the menu buttons or type commands.",
            parse_mode="Markdown",
        )
        return

    # ─── System Callbacks ────────────────────────────────────
    if data == "sys_overview":
        result = await system.get_overview()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_cpu":
        result = await system.get_cpu_detailed()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_memory":
        result = await system.get_memory_detailed()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_disk":
        result = await system.get_disk_detailed()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_network":
        result = await system.get_network_interfaces()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_df":
        result = await filesystem.disk_usage()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=system_keyboard())

    # ─── Process Callbacks ───────────────────────────────────
    elif data == "proc_top_cpu":
        result = await processes.list_processes("cpu")
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=processes_keyboard())
    elif data == "proc_top_mem":
        result = await processes.list_processes("memory")
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=processes_keyboard())
    elif data in ("proc_search", "proc_info", "proc_kill"):
        prompts = {
            "proc_search": "🔍 *Search Process*\n\nReply with process name:\n`/find <name>`",
            "proc_info": "ℹ️ *Process Info*\n\nReply with PID:\n`/proc <pid>`",
            "proc_kill": "💀 *Kill Process*\n\nReply with PID:\n`/kill <pid>` (or `/killf <pid>` for force)",
        }
        await query.edit_message_text(prompts[data], parse_mode="Markdown", reply_markup=processes_keyboard())

    # ─── Service Callbacks ───────────────────────────────────
    elif data == "svc_running":
        result = await services.list_services("running")
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=services_keyboard())
    elif data == "svc_failed":
        result = await services.list_services("failed")
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=services_keyboard())
    elif data in ("svc_status", "svc_start", "svc_stop", "svc_restart", "svc_logs"):
        action_map = {"svc_status": "status", "svc_start": "start", "svc_stop": "stop", "svc_restart": "restart"}
        if data == "svc_logs":
            await query.edit_message_text(
                "📜 *Service Logs*\n\nReply with service name:\n`/svcl <service_name>`",
                parse_mode="Markdown", reply_markup=services_keyboard(),
            )
        else:
            action = action_map[data]
            prefix_map = {"status": "/svc", "start": "/svca", "stop": "/svcs", "restart": "/svcr"}
            await query.edit_message_text(
                f"🔧 *Service {action.title()}*\n\nReply with service name:\n`{prefix_map[action]} <service_name>`",
                parse_mode="Markdown", reply_markup=services_keyboard(),
            )

    # ─── Filesystem Callbacks ────────────────────────────────
    elif data == "fs_list":
        await query.edit_message_text(
            "📂 *List Directory*\n\nReply with path:\n`/ls /path/to/dir`",
            parse_mode="Markdown", reply_markup=files_keyboard(),
        )
    elif data == "fs_read":
        await query.edit_message_text(
            "📄 *Read File*\n\nReply with file path:\n`/cat /path/to/file`",
            parse_mode="Markdown", reply_markup=files_keyboard(),
        )
    elif data == "fs_info":
        await query.edit_message_text(
            "ℹ️ *File Info*\n\nReply with path:\n`/finfo /path/to/file`",
            parse_mode="Markdown", reply_markup=files_keyboard(),
        )
    elif data == "fs_df":
        result = await filesystem.disk_usage()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=files_keyboard())
    elif data == "fs_delete":
        await query.edit_message_text(
            "🗑 *Delete File/Directory*\n\n"
            "Reply with path:\n`/rm /path/to/file`\n`/rmrf /path/to/dir`",
            parse_mode="Markdown", reply_markup=files_keyboard(),
        )

    # ─── Docker Callbacks ────────────────────────────────────
    elif data == "dkr_ps":
        result = await docker_m.docker_ps(False)
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data == "dkr_ps_all":
        result = await docker_m.docker_ps(True)
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data == "dkr_images":
        result = await docker_m.docker_images()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data == "dkr_stats":
        result = await docker_m.docker_stats()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data in ("dkr_logs", "dkr_exec", "dkr_start", "dkr_stop", "dkr_restart"):
        cmd_map = {
            "dkr_logs": "/dlog <container>",
            "dkr_exec": "/dexec <container> <command>",
            "dkr_start": "/dstart <container>",
            "dkr_stop": "/dstop <container>",
            "dkr_restart": "/drestart <container>",
        }
        labels = {
            "dkr_logs": "📜 Container Logs",
            "dkr_exec": "💻 Exec in Container",
            "dkr_start": "▶️ Start Container",
            "dkr_stop": "⏹ Stop Container",
            "dkr_restart": "🔄 Restart Container",
        }
        await query.edit_message_text(
            f"{labels[data]}\n\nReply with:\n`{cmd_map[data]}`",
            parse_mode="Markdown", reply_markup=docker_keyboard(),
        )

    # ─── Network Callbacks ───────────────────────────────────
    elif data == "net_ping":
        await query.edit_message_text(
            "🏓 *Ping*\n\nReply with:\n`/ping <host>`",
            parse_mode="Markdown", reply_markup=network_keyboard(),
        )
    elif data == "net_trace":
        await query.edit_message_text(
            "🗺 *Traceroute*\n\nReply with:\n`/trace <host>`",
            parse_mode="Markdown", reply_markup=network_keyboard(),
        )
    elif data == "net_dns":
        await query.edit_message_text(
            "🌐 *DNS Lookup*\n\nReply with:\n`/dns <domain> [A|AAAA|MX|NS|TXT]`",
            parse_mode="Markdown", reply_markup=network_keyboard(),
        )
    elif data == "net_ports":
        result = await network.check_ports()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_fw":
        result = await network.firewall_status()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_conn":
        result = await network.connections_summary()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_http":
        await query.edit_message_text(
            "🌐 *HTTP Check*\n\nReply with:\n`/http <url>`",
            parse_mode="Markdown", reply_markup=network_keyboard(),
        )

    # ─── Power Callbacks ─────────────────────────────────────
    elif data == "pwr_reboot":
        await query.edit_message_text(
            "🔄 *Reboot*\n\nReply with:\n`/reboot [delay_minutes]`",
            parse_mode="Markdown", reply_markup=power_keyboard(),
        )
    elif data == "pwr_shutdown":
        await query.edit_message_text(
            "⏹ *Shutdown*\n\nReply with:\n`/shutdown [delay_minutes]`",
            parse_mode="Markdown", reply_markup=power_keyboard(),
        )
    elif data == "pwr_cancel":
        result = await power.cancel_shutdown()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_cron_list":
        result = await power.list_cron()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_cron_add":
        await query.edit_message_text(
            "➕ *Add Cron Job*\n\nReply with schedule and command:\n"
            "`/cronadd <schedule> <command>`\n\n"
            "Example: `/cronadd \"0 3 * * *\" \"backup.sh\"`",
            parse_mode="Markdown", reply_markup=power_keyboard(),
        )
    elif data == "pwr_update":
        result = await power.update_system()
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_logs":
        result = await power.system_logs("syslog")
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=power_keyboard())

    else:
        await query.edit_message_text("❓ Unknown action.")


# ─── Menu Text Handler ───────────────────────────────────────

async def menu_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text button presses from the main reply keyboard."""
    text = update.message.text.strip()

    menu_map = {
        "🖥 System": ("🖥 *System Monitor*\n\nSelect a metric:", system_keyboard()),
        "⚙ Processes": ("⚙ *Process Management*\n\nSelect an action:", processes_keyboard()),
        "🔧 Services": ("🔧 *Service Management*\n\nSelect an action:", services_keyboard()),
        "📂 Files": ("📂 *Filesystem*\n\nSelect an action:", files_keyboard()),
        "🐳 Docker": ("🐳 *Docker Management*\n\nSelect an action:", docker_keyboard()),
        "🌐 Network": ("🌐 *Network Tools*\n\nSelect an action:", network_keyboard()),
        "⚡ Power": ("⚡ *Power & Admin*\n\nSelect an action:", power_keyboard()),
        "🖥 Shell": ("🖥 *Shell Execution*\n\nType: `/shell <command>`\n\nExample: `/shell uptime`", None),
        "❓ Help": None,
    }

    if text == "❓ Help":
        await help_command(update, context)
        return

    entry = menu_map.get(text)
    if entry:
        message, keyboard = entry
        if keyboard:
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await update.message.reply_text(message, parse_mode="Markdown")
    else:
        # Unknown text — ignore
        pass


# ═══════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════


async def _reply_loading(update: Update) -> Any:
    """Send a loading indicator and return the message for editing."""
    return await update.message.reply_text("⏳ Processing...")


def _safe_int(value: str) -> int:
    """Safely convert a string to int, returning 0 on failure."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


# ═══════════════════════════════════════════════════════════════
#  ERROR HANDLER
# ═══════════════════════════════════════════════════════════════


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler — logs errors and notifies the user."""
    logger.error(f"Exception: {context.error}", exc_info=context.error)

    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ *An error occurred while processing your request.*\n\n"
            "Check the bot logs for details.",
            parse_mode="Markdown",
        )


# ═══════════════════════════════════════════════════════════════
#  APPLICATION SETUP
# ═══════════════════════════════════════════════════════════════


def build_application() -> Application:
    """Build and configure the Telegram bot application."""
    app = Application.builder().token(Config.BOT_TOKEN).build()

    # ─── Command Handlers ────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # System
    app.add_handler(CommandHandler("sys", sys_overview))
    app.add_handler(CommandHandler("cpu", sys_cpu))
    app.add_handler(CommandHandler("mem", sys_memory))
    app.add_handler(CommandHandler("disk", sys_disk))
    app.add_handler(CommandHandler("netif", sys_network))
    app.add_handler(CommandHandler("df", sys_df))

    # Processes
    app.add_handler(CommandHandler("ps", proc_list))
    app.add_handler(CommandHandler("psm", proc_list_mem))
    app.add_handler(CommandHandler("proc", proc_info))
    app.add_handler(CommandHandler("find", proc_find))
    app.add_handler(CommandHandler("kill", proc_kill))
    app.add_handler(CommandHandler("killf", proc_kill_force))

    # Services
    app.add_handler(CommandHandler("svc", svc_status))
    app.add_handler(CommandHandler("svcr", svc_restart))
    app.add_handler(CommandHandler("svcs", svc_stop))
    app.add_handler(CommandHandler("svca", svc_start))
    app.add_handler(CommandHandler("svcl", svc_logs))
    app.add_handler(CommandHandler("svclist", svc_list))

    # Filesystem
    app.add_handler(CommandHandler("ls", fs_list))
    app.add_handler(CommandHandler("cat", fs_read))
    app.add_handler(CommandHandler("finfo", fs_info))
    app.add_handler(CommandHandler("rm", fs_remove))
    app.add_handler(CommandHandler("rmrf", fs_remove_recursive))

    # Docker
    app.add_handler(CommandHandler("dps", dkr_ps))
    app.add_handler(CommandHandler("dpsa", dkr_ps_all))
    app.add_handler(CommandHandler("dimg", dkr_images))
    app.add_handler(CommandHandler("dstats", dkr_stats))
    app.add_handler(CommandHandler("dlog", dkr_logs))
    app.add_handler(CommandHandler("dstart", dkr_start))
    app.add_handler(CommandHandler("dstop", dkr_stop))
    app.add_handler(CommandHandler("drestart", dkr_restart))
    app.add_handler(CommandHandler("dexec", dkr_exec))

    # Network
    app.add_handler(CommandHandler("ping", net_ping))
    app.add_handler(CommandHandler("trace", net_trace))
    app.add_handler(CommandHandler("dns", net_dns))
    app.add_handler(CommandHandler("ports", net_ports))
    app.add_handler(CommandHandler("fw", net_fw))
    app.add_handler(CommandHandler("conn", net_conn))
    app.add_handler(CommandHandler("http", net_http))

    # Power & Admin
    app.add_handler(CommandHandler("reboot", pwr_reboot))
    app.add_handler(CommandHandler("shutdown", pwr_shutdown))
    app.add_handler(CommandHandler("cancel", pwr_cancel))
    app.add_handler(CommandHandler("cronl", pwr_cron_list))
    app.add_handler(CommandHandler("update", pwr_update))
    app.add_handler(CommandHandler("syslog", pwr_syslog))

    # Shell
    app.add_handler(CommandHandler("shell", shell_command))

    # ─── Callback & Text Handlers ────────────────────────────
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_text_handler))

    # ─── Error Handler ───────────────────────────────────────
    app.add_error_handler(error_handler)

    return app


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Start the VPSPilot bot."""
    logger.info(f"🛩 {Config.PROJECT_NAME} v{Config.VERSION} starting...")
    logger.info(f"📋 Authorized users: {Config.AUTHORIZED_USERS}")

    app = build_application()

    logger.info("✅ Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
