#!/usr/bin/env python3
"""
VPSPilot — Telegram VPS Control Bot (Hybrid Terminal-First)
Full-featured Telegram bot for remote VPS management.

Modes:
    Terminal — type any command directly (default)
    Pretty   — use /slash commands for formatted output
    Menu     — tap keyboard buttons for guided actions

Usage:
    python bot.py

Set up your .env file first (see .env.example).
"""

import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import Config
from core.auth import authorized_only
from core.executor import execute
from core.interpreter import interpret, ActionType, InterpretedCommand
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
from ui.formatters import truncate
from modules import system, processes, services, filesystem, docker_m, network, power
from utils import sanitize_path, validate_command

# ─── Logging Setup ───────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(Config.PROJECT_NAME)


# ═══════════════════════════════════════════════════════════════
#  /SLASH COMMAND HANDLERS (Pretty Formatted Output)
# ═══════════════════════════════════════════════════════════════


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — display welcome message and main menu."""
    user = update.effective_user
    text = (
        f"🛩 *Welcome to VPSPilot!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Hello, *{user.first_name}*!\n\n"
        f"Your VPS terminal is live. Just type commands naturally:\n\n"
        f"🖥 *Terminal Mode* (default):\n"
        f"  `ls /var/log` — list directory\n"
        f"  `restart nginx` — restart service\n"
        f"  `docker ps` — list containers\n"
        f"  `top` — show processes\n"
        f"  `ping google.com` — ping host\n"
        f"  `uptime` — system overview\n\n"
        f"📊 *Pretty Mode* (formatted output):\n"
        f"  /sys — System overview with bars\n"
        f"  /cpu — CPU details\n"
        f"  /mem — Memory details\n\n"
        f"🎛 *Menu Mode* (tap buttons):\n"
        f"  /menu — Interactive keyboard\n\n"
        f"🔑 *Your ID:* `{user.id}`"
    )
    await update.message.reply_text(
        text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — show all commands and shortcuts."""
    text = (
        f"📖 *VPSPilot Command Reference*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🖥 *Terminal Mode — Just Type!*\n"
        f"  Any text that isn't a /command or button is executed.\n"
        f"  Smart parsing handles common patterns:\n\n"
        f"  `ls /var/log` → list directory\n"
        f"  `cat /etc/hosts` → read file\n"
        f"  `restart nginx` → systemctl restart\n"
        f"  `status docker` → systemctl status\n"
        f"  `logs ssh` → journal logs\n"
        f"  `docker ps` → running containers\n"
        f"  `docker logs web` → container logs\n"
        f"  `docker restart web` → restart container\n"
        f"  `kill 1234` → kill process\n"
        f"  `kill -9 1234` → force kill\n"
        f"  `find nginx` → search processes\n"
        f"  `ping google.com` → ping\n"
        f"  `dns google.com` → DNS lookup\n"
        f"  `firewall` → UFW status\n"
        f"  `reboot` or `reboot 5` → schedule reboot\n"
        f"  `shutdown` or `shutdown now` → schedule shutdown\n"
        f"  `update` → system update\n"
        f"  `cron list` → list cron jobs\n"
        f"  `df` → disk usage\n"
        f"  `top` → top processes\n"
        f"  `uptime` → system overview\n"
        f"  `conn` → active connections\n"
        f"  `ports` → listening ports\n\n"
        f"  Anything else → executed as shell command\n\n"
        f"📊 *Pretty /Commands (Formatted Output)*\n"
        f"  /sys — Full system overview\n"
        f"  /cpu — Detailed CPU info\n"
        f"  /mem — Detailed memory info\n"
        f"  /disk — Disk partition info\n"
        f"  /netif — Network interfaces\n"
        f"  /ps — Top processes (CPU)\n"
        f"  /psm — Top processes (Memory)\n"
        f"  /svc <name> — Service status\n"
        f"  /svcr <name> — Restart service\n"
        f"  /dps — Docker containers\n"
        f"  /dlog <c> — Container logs\n"
        f"  /fw — Firewall status\n"
        f"  /ping <host> — Ping\n\n"
        f"🎛 *Menu*\n"
        f"  /menu — Interactive keyboard\n"
        f"  /start — Welcome screen"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu — show interactive keyboard menu."""
    await update.message.reply_text(
        "🎛 *VPSPilot Menu*\n\nTap a category to explore:",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


# ─── Pretty /Slash Commands ─────────────────────────────────


@authorized_only
async def sys_overview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await system.get_overview(), parse_mode="Markdown")

@authorized_only
async def sys_cpu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await system.get_cpu_detailed(), parse_mode="Markdown")

@authorized_only
async def sys_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await system.get_memory_detailed(), parse_mode="Markdown")

@authorized_only
async def sys_disk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await system.get_disk_detailed(), parse_mode="Markdown")

@authorized_only
async def sys_network(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await system.get_network_interfaces(), parse_mode="Markdown")

@authorized_only
async def sys_df(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await filesystem.disk_usage(), parse_mode="Markdown")

@authorized_only
async def proc_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await processes.list_processes("cpu"), parse_mode="Markdown")

@authorized_only
async def proc_list_mem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await processes.list_processes("memory"), parse_mode="Markdown")

@authorized_only
async def proc_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/proc <PID>`", parse_mode="Markdown"); return
    pid = _int(context.args[0])
    msg = await _loading(update)
    await msg.edit_text(await processes.get_process_info(pid), parse_mode="Markdown")

@authorized_only
async def proc_find(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/find <name>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await processes.find_process(" ".join(context.args)), parse_mode="Markdown")

@authorized_only
async def proc_kill(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/kill <PID>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await processes.kill_process(_int(context.args[0]), False), parse_mode="Markdown")

@authorized_only
async def proc_kill_force(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/killf <PID>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await processes.kill_process(_int(context.args[0]), True), parse_mode="Markdown")

@authorized_only
async def svc_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svc <name>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await services.service_status(" ".join(context.args)), parse_mode="Markdown")

@authorized_only
async def svc_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svcr <name>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await services.service_action(" ".join(context.args), "restart"), parse_mode="Markdown")

@authorized_only
async def svc_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svcs <name>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await services.service_action(" ".join(context.args), "stop"), parse_mode="Markdown")

@authorized_only
async def svc_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svca <name>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await services.service_action(" ".join(context.args), "start"), parse_mode="Markdown")

@authorized_only
async def svc_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Usage: `/svcl <name>`", parse_mode="Markdown"); return
    name = " ".join(context.args)
    lines = 50
    if len(context.args) > 1 and context.args[-1].isdigit():
        lines = int(context.args[-1]); name = " ".join(context.args[:-1])
    msg = await _loading(update)
    await msg.edit_text(await services.service_logs(name, lines), parse_mode="Markdown")

@authorized_only
async def svc_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await services.list_services(context.args[0] if context.args else "running"), parse_mode="Markdown")

@authorized_only
async def fs_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    path = context.args[0] if context.args else "/"
    try: path = sanitize_path(path)
    except ValueError as e: await update.message.reply_text(f"❌ {e}"); return
    msg = await _loading(update)
    await msg.edit_text(await filesystem.list_directory(path), parse_mode="Markdown")

@authorized_only
async def fs_read(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/cat <path>`", parse_mode="Markdown"); return
    path = " ".join(context.args)
    try: path = sanitize_path(path)
    except ValueError as e: await update.message.reply_text(f"❌ {e}"); return
    msg = await _loading(update)
    await msg.edit_text(await filesystem.read_file(path), parse_mode="Markdown")

@authorized_only
async def fs_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/finfo <path>`", parse_mode="Markdown"); return
    path = " ".join(context.args)
    try: path = sanitize_path(path)
    except ValueError as e: await update.message.reply_text(f"❌ {e}"); return
    msg = await _loading(update)
    await msg.edit_text(await filesystem.file_info(path), parse_mode="Markdown")

@authorized_only
async def fs_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/rm <path>`", parse_mode="Markdown"); return
    path = " ".join(context.args)
    try: path = sanitize_path(path)
    except ValueError as e: await update.message.reply_text(f"❌ {e}"); return
    msg = await _loading(update)
    await msg.edit_text(await filesystem.remove_file(path, False), parse_mode="Markdown")

@authorized_only
async def fs_remove_recursive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/rmrf <path>`", parse_mode="Markdown"); return
    path = " ".join(context.args)
    try: path = sanitize_path(path)
    except ValueError as e: await update.message.reply_text(f"❌ {e}"); return
    msg = await _loading(update)
    await msg.edit_text(await filesystem.remove_file(path, True), parse_mode="Markdown")

@authorized_only
async def dkr_ps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_ps(False), parse_mode="Markdown")

@authorized_only
async def dkr_ps_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_ps(True), parse_mode="Markdown")

@authorized_only
async def dkr_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_images(), parse_mode="Markdown")

@authorized_only
async def dkr_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_stats(), parse_mode="Markdown")

@authorized_only
async def dkr_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/dlog <container>`", parse_mode="Markdown"); return
    lines = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 50
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_logs(context.args[0], lines), parse_mode="Markdown")

@authorized_only
async def dkr_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/dstart <container>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_action(" ".join(context.args), "start"), parse_mode="Markdown")

@authorized_only
async def dkr_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/dstop <container>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_action(" ".join(context.args), "stop"), parse_mode="Markdown")

@authorized_only
async def dkr_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/drestart <container>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_action(" ".join(context.args), "restart"), parse_mode="Markdown")

@authorized_only
async def dkr_exec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2: await update.message.reply_text("❌ Usage: `/dexec <container> <cmd>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await docker_m.docker_exec(context.args[0], " ".join(context.args[1:])), parse_mode="Markdown")

@authorized_only
async def net_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/ping <host>`", parse_mode="Markdown"); return
    count = int(context.args[1]) if len(context.args) > 1 and context.args[1].isdigit() else 4
    msg = await _loading(update)
    await msg.edit_text(await network.ping(context.args[0], count), parse_mode="Markdown")

@authorized_only
async def net_trace(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/trace <host>`", parse_mode="Markdown"); return
    msg = await _loading(update)
    await msg.edit_text(await network.traceroute(context.args[0]), parse_mode="Markdown")

@authorized_only
async def net_dns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/dns <domain>`", parse_mode="Markdown"); return
    rtype = context.args[1] if len(context.args) > 1 else "A"
    msg = await _loading(update)
    await msg.edit_text(await network.dns_lookup(context.args[0], rtype), parse_mode="Markdown")

@authorized_only
async def net_ports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    target = context.args[0] if context.args else "localhost"
    ports = ",".join(context.args[1:]) if len(context.args) > 1 else ""
    await msg.edit_text(await network.check_ports(target, ports), parse_mode="Markdown")

@authorized_only
async def net_fw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await network.firewall_status(), parse_mode="Markdown")

@authorized_only
async def net_conn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await network.connections_summary(), parse_mode="Markdown")

@authorized_only
async def net_http(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args: await update.message.reply_text("❌ Usage: `/http <url>`", parse_mode="Markdown"); return
    url = context.args[0]
    if not url.startswith(("http://", "https://")): url = f"https://{url}"
    msg = await _loading(update)
    await msg.edit_text(await network.http_check(url), parse_mode="Markdown")

@authorized_only
async def pwr_reboot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    delay = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    msg = await _loading(update)
    await msg.edit_text(await power.reboot_system(delay), parse_mode="Markdown")

@authorized_only
async def pwr_shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    delay = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    msg = await _loading(update)
    await msg.edit_text(await power.shutdown_system(delay), parse_mode="Markdown")

@authorized_only
async def pwr_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await power.cancel_shutdown(), parse_mode="Markdown")

@authorized_only
async def pwr_cron_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await power.list_cron(), parse_mode="Markdown")

@authorized_only
async def pwr_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await _loading(update)
    await msg.edit_text(await power.update_system(), parse_mode="Markdown")

@authorized_only
async def pwr_syslog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    svc = context.args[0] if context.args else "syslog"
    msg = await _loading(update)
    await msg.edit_text(await power.system_logs(svc), parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  TERMINAL-FIRST TEXT HANDLER (The Heart of the Hybrid)
# ═══════════════════════════════════════════════════════════════


@authorized_only
async def terminal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle ALL plain text messages. This is the default mode.
    Routes through the smart interpreter, falls back to shell.
    """
    raw_text = update.message.text.strip()

    # ── Check if it's a menu button press ─────────────────────
    menu_entry = _get_menu_entry(raw_text)
    if menu_entry is not None:
        message, keyboard = menu_entry
        if keyboard:
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await update.message.reply_text(message, parse_mode="Markdown")
        return

    # ── Interpret the command ─────────────────────────────────
    cmd = interpret(raw_text)
    logger.info(f"Interpreted: '{raw_text}' → {cmd.action.value}/{cmd.sub_action} target={cmd.target}")

    # ── Route to appropriate handler ──────────────────────────
    msg = await update.message.reply_text("⏳ Processing...")

    try:
        result = await _route_command(cmd)
        await msg.edit_text(result, parse_mode="Markdown")
    except Exception as exc:
        await msg.edit_text(f"❌ Error: {exc}", parse_mode="Markdown")


async def _route_command(cmd) -> str:
    """Route an interpreted command to the right module and return result text."""

    # ── SHELL (fallback) ──────────────────────────────────────
    if cmd.action == ActionType.SHELL:
        try:
            validate_command(cmd.original)
        except ValueError as exc:
            return f"🚫 *Blocked:* {exc}"

        result = await execute(cmd.original)
        output = ""
        if result.stdout: output += result.stdout
        if result.stderr: output += ("\n" if output else "") + result.stderr
        if not output.strip(): output = "(no output)"
        output = truncate(output)

        emoji = "✅" if result.success else "❌"
        return (
            f"🖥 {emoji} `{cmd.original}`\n"
            f"Exit: {result.return_code}\n\n"
            f"```\n{output}\n```"
        )

    # ── SYSTEM ────────────────────────────────────────────────
    if cmd.action == ActionType.SYSTEM:
        if cmd.sub_action == "overview":
            return await system.get_overview()
        elif cmd.sub_action == "cpu":
            return await system.get_cpu_detailed()
        elif cmd.sub_action == "memory":
            return await system.get_memory_detailed()
        elif cmd.sub_action == "disk":
            return await system.get_disk_detailed()
        elif cmd.sub_action == "network":
            return await system.get_network_interfaces()
        elif cmd.sub_action == "disk_usage":
            return await filesystem.disk_usage()

    # ── PROCESS ───────────────────────────────────────────────
    if cmd.action == ActionType.PROCESS:
        if cmd.sub_action == "top_cpu":
            return await processes.list_processes("cpu")
        elif cmd.sub_action == "top_mem":
            return await processes.list_processes("memory")
        elif cmd.sub_action == "find":
            return await processes.find_process(cmd.target)
        elif cmd.sub_action == "kill":
            return await processes.kill_process(int(cmd.target), force=False)
        elif cmd.sub_action == "kill_force":
            return await processes.kill_process(int(cmd.target), force=True)

    # ── SERVICE ───────────────────────────────────────────────
    if cmd.action == ActionType.SERVICE:
        if cmd.sub_action == "status":
            return await services.service_status(cmd.target)
        elif cmd.sub_action == "logs" or cmd.sub_action == "log":
            return await services.service_logs(cmd.target, 50)
        elif cmd.sub_action in ("start", "stop", "restart", "reload", "enable", "disable"):
            return await services.service_action(cmd.target, cmd.sub_action)
        elif cmd.sub_action == "list_running":
            return await services.list_services("running")

    # ── FILESYSTEM ────────────────────────────────────────────
    if cmd.action == ActionType.FILESYSTEM:
        try:
            safe_path = sanitize_path(cmd.target)
        except ValueError as exc:
            return f"❌ {exc}"

        if cmd.sub_action == "list":
            return await filesystem.list_directory(safe_path or "/")
        elif cmd.sub_action == "read":
            return await filesystem.read_file(safe_path)
        elif cmd.sub_action == "info":
            return await filesystem.file_info(safe_path)
        elif cmd.sub_action == "delete":
            return await filesystem.remove_file(safe_path, recursive=False)
        elif cmd.sub_action == "delete_recursive":
            return await filesystem.remove_file(safe_path, recursive=True)

    # ── DOCKER ────────────────────────────────────────────────
    if cmd.action == ActionType.DOCKER:
        if cmd.sub_action == "ps":
            return await docker_m.docker_ps(all_containers=False)
        elif cmd.sub_action == "images":
            return await docker_m.docker_images()
        elif cmd.sub_action == "stats":
            return await docker_m.docker_stats()
        elif cmd.sub_action == "logs":
            return await docker_m.docker_logs(cmd.target, 50)
        elif cmd.sub_action in ("start", "stop", "restart", "pause", "unpause", "rm"):
            action = "remove" if cmd.sub_action == "rm" else cmd.sub_action
            return await docker_m.docker_action(cmd.target, action)
        elif cmd.sub_action == "exec":
            return await docker_m.docker_exec(cmd.target, cmd.extra)

    # ── NETWORK ───────────────────────────────────────────────
    if cmd.action == ActionType.NETWORK:
        if cmd.sub_action == "ping":
            return await network.ping(cmd.target, int(cmd.extra) if cmd.extra else 4)
        elif cmd.sub_action == "traceroute":
            return await network.traceroute(cmd.target)
        elif cmd.sub_action == "dns":
            return await network.dns_lookup(cmd.target, cmd.extra or "A")
        elif cmd.sub_action == "http":
            return await network.http_check(cmd.target)
        elif cmd.sub_action == "status":
            return await network.firewall_status()
        elif cmd.sub_action in ("allow", "deny", "enable", "disable", "reload", "reset"):
            return await network.firewall_action(cmd.sub_action, cmd.target)
        elif cmd.sub_action == "connections":
            return await network.connections_summary()
        elif cmd.sub_action == "ports":
            return await network.check_ports()

    # ── POWER ─────────────────────────────────────────────────
    if cmd.action == ActionType.POWER:
        if cmd.sub_action == "reboot":
            return await power.reboot_system(int(cmd.target) if cmd.target.isdigit() else 1)
        elif cmd.sub_action == "shutdown":
            return await power.shutdown_system(int(cmd.target) if cmd.target.isdigit() else 1)
        elif cmd.sub_action == "cancel":
            return await power.cancel_shutdown()
        elif cmd.sub_action == "cron_list":
            return await power.list_cron()
        elif cmd.sub_action == "cron_add":
            return "➕ Add cron via: `cron add \"0 3 * * *\" backup.sh`"
        elif cmd.sub_action == "cron_remove":
            return await power.remove_cron(int(cmd.target) if cmd.target.isdigit() else 0)
        elif cmd.sub_action == "update":
            return await power.update_system()

    # ── HELP / MENU ───────────────────────────────────────────
    if cmd.action == ActionType.HELP:
        return (
            "📖 *Quick Help*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Type commands naturally — they're auto-interpreted!\n\n"
            "Examples: `top`, `restart nginx`, `docker ps`, `ping google.com`\n\n"
            "Use /help for full reference."
        )

    if cmd.action == ActionType.MENU:
        return "🎛 Use /menu to open the interactive keyboard."

    # If we get here, action type wasn't handled — fallback to shell
    shell_cmd = InterpretedCommand(
        action=ActionType.SHELL, sub_action="execute", target="", extra="", original=cmd.original
    )
    return await _route_command(shell_cmd)


# ═══════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLERS (Inline Keyboard Buttons)
# ═══════════════════════════════════════════════════════════════


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id not in Config.AUTHORIZED_USERS:
        await query.answer("🚫 Unauthorized", show_alert=True)
        return

    data = query.data
    logger.info(f"Callback: {data}")

    # ─── System
    if data == "sys_overview":
        await query.edit_message_text(await system.get_overview(), parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_cpu":
        await query.edit_message_text(await system.get_cpu_detailed(), parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_memory":
        await query.edit_message_text(await system.get_memory_detailed(), parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_disk":
        await query.edit_message_text(await system.get_disk_detailed(), parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_network":
        await query.edit_message_text(await system.get_network_interfaces(), parse_mode="Markdown", reply_markup=system_keyboard())
    elif data == "sys_df":
        await query.edit_message_text(await filesystem.disk_usage(), parse_mode="Markdown", reply_markup=system_keyboard())

    # ─── Processes
    elif data == "proc_top_cpu":
        await query.edit_message_text(await processes.list_processes("cpu"), parse_mode="Markdown", reply_markup=processes_keyboard())
    elif data == "proc_top_mem":
        await query.edit_message_text(await processes.list_processes("memory"), parse_mode="Markdown", reply_markup=processes_keyboard())
    elif data in ("proc_search", "proc_info", "proc_kill"):
        prompts = {
            "proc_search": "🔍 *Search Process*\n\nJust type: `find <name>`\nExample: `find nginx`",
            "proc_info": "ℹ️ *Process Info*\n\nJust type: `proc <pid>` or use `/proc <pid>`",
            "proc_kill": "💀 *Kill Process*\n\nJust type: `kill <pid>` or `kill -9 <pid>` (force)",
        }
        await query.edit_message_text(prompts[data], parse_mode="Markdown", reply_markup=processes_keyboard())

    # ─── Services
    elif data == "svc_running":
        await query.edit_message_text(await services.list_services("running"), parse_mode="Markdown", reply_markup=services_keyboard())
    elif data == "svc_failed":
        await query.edit_message_text(await services.list_services("failed"), parse_mode="Markdown", reply_markup=services_keyboard())
    elif data in ("svc_status", "svc_start", "svc_stop", "svc_restart", "svc_logs"):
        if data == "svc_logs":
            await query.edit_message_text("📜 *Service Logs*\n\nJust type: `logs <service>`\nExample: `logs nginx`", parse_mode="Markdown", reply_markup=services_keyboard())
        else:
            action_map = {"svc_status": "status", "svc_start": "start", "svc_stop": "stop", "svc_restart": "restart"}
            action = action_map[data]
            await query.edit_message_text(
                f"🔧 *Service {action.title()}*\n\nJust type: `{action} <service>`\nExample: `{action} nginx`",
                parse_mode="Markdown", reply_markup=services_keyboard(),
            )

    # ─── Filesystem
    elif data == "fs_list":
        await query.edit_message_text("📂 *List Directory*\n\nJust type: `ls /path`\nExample: `ls /var/log`", parse_mode="Markdown", reply_markup=files_keyboard())
    elif data == "fs_read":
        await query.edit_message_text("📄 *Read File*\n\nJust type: `cat /path`\nExample: `cat /etc/hosts`", parse_mode="Markdown", reply_markup=files_keyboard())
    elif data == "fs_info":
        await query.edit_message_text("ℹ️ *File Info*\n\nJust type: `stat /path`\nExample: `stat /etc/hosts`", parse_mode="Markdown", reply_markup=files_keyboard())
    elif data == "fs_df":
        await query.edit_message_text(await filesystem.disk_usage(), parse_mode="Markdown", reply_markup=files_keyboard())
    elif data == "fs_delete":
        await query.edit_message_text("🗑 *Delete*\n\nJust type: `rm /path` or `rm -rf /dir`", parse_mode="Markdown", reply_markup=files_keyboard())

    # ─── Docker
    elif data == "dkr_ps":
        await query.edit_message_text(await docker_m.docker_ps(False), parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data == "dkr_ps_all":
        await query.edit_message_text(await docker_m.docker_ps(True), parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data == "dkr_images":
        await query.edit_message_text(await docker_m.docker_images(), parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data == "dkr_stats":
        await query.edit_message_text(await docker_m.docker_stats(), parse_mode="Markdown", reply_markup=docker_keyboard())
    elif data in ("dkr_logs", "dkr_exec", "dkr_start", "dkr_stop", "dkr_restart"):
        examples = {
            "dkr_logs": "📜 *Container Logs*\n\nJust type: `docker logs <container>`",
            "dkr_exec": "💻 *Exec in Container*\n\nJust type: `docker exec <container> <command>`",
            "dkr_start": "▶️ *Start Container*\n\nJust type: `docker start <container>`",
            "dkr_stop": "⏹ *Stop Container*\n\nJust type: `docker stop <container>`",
            "dkr_restart": "🔄 *Restart Container*\n\nJust type: `docker restart <container>`",
        }
        await query.edit_message_text(examples[data], parse_mode="Markdown", reply_markup=docker_keyboard())

    # ─── Network
    elif data == "net_ping":
        await query.edit_message_text("🏓 *Ping*\n\nJust type: `ping <host>`\nExample: `ping google.com`", parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_trace":
        await query.edit_message_text("🗺 *Traceroute*\n\nJust type: `trace <host>`\nExample: `trace google.com`", parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_dns":
        await query.edit_message_text("🌐 *DNS Lookup*\n\nJust type: `dns <domain>` or `dns <domain> MX`", parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_ports":
        await query.edit_message_text(await network.check_ports(), parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_fw":
        await query.edit_message_text(await network.firewall_status(), parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_conn":
        await query.edit_message_text(await network.connections_summary(), parse_mode="Markdown", reply_markup=network_keyboard())
    elif data == "net_http":
        await query.edit_message_text("🌐 *HTTP Check*\n\nJust type: `http <url>`\nExample: `http google.com`", parse_mode="Markdown", reply_markup=network_keyboard())

    # ─── Power
    elif data == "pwr_reboot":
        await query.edit_message_text("🔄 *Reboot*\n\nJust type: `reboot` or `reboot 5`", parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_shutdown":
        await query.edit_message_text("⏹ *Shutdown*\n\nJust type: `shutdown` or `shutdown now`", parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_cancel":
        await query.edit_message_text(await power.cancel_shutdown(), parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_cron_list":
        await query.edit_message_text(await power.list_cron(), parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_cron_add":
        await query.edit_message_text("➕ *Add Cron*\n\nJust type: `cron add \"0 3 * * *\" backup.sh`", parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_update":
        await query.edit_message_text(await power.update_system(), parse_mode="Markdown", reply_markup=power_keyboard())
    elif data == "pwr_logs":
        await query.edit_message_text(await power.system_logs("syslog"), parse_mode="Markdown", reply_markup=power_keyboard())

    # ─── Back
    elif data == "menu_back":
        await query.edit_message_text("🛩 *VPSPilot Control Panel*\n\nType commands or use /menu", parse_mode="Markdown")

    else:
        await query.edit_message_text("❓ Unknown action.")


# ═══════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════


def _get_menu_entry(text: str) -> tuple[str, Any] | None:
    """Check if text matches a main menu button. Returns (message, keyboard) or None."""
    menu_map = {
        "🖥 System": ("🖥 *System Monitor*\n\nSelect a metric:", system_keyboard()),
        "⚙ Processes": ("⚙ *Process Management*\n\nSelect an action:", processes_keyboard()),
        "🔧 Services": ("🔧 *Service Management*\n\nSelect an action:", services_keyboard()),
        "📂 Files": ("📂 *Filesystem*\n\nSelect an action:", files_keyboard()),
        "🐳 Docker": ("🐳 *Docker Management*\n\nSelect an action:", docker_keyboard()),
        "🌐 Network": ("🌐 *Network Tools*\n\nSelect an action:", network_keyboard()),
        "⚡ Power": ("⚡ *Power & Admin*\n\nSelect an action:", power_keyboard()),
        "🖥 Shell": ("🖥 *Terminal Mode*\n\nJust type any command — it executes directly!\n\nExamples: `ls /`, `uptime`, `docker ps`", None),
        "❓ Help": ("📖 *Help*\n\nType commands naturally or use /help for full reference.\n\nQuick: `top`, `restart nginx`, `docker ps`, `ping google.com`", None),
    }
    return menu_map.get(text)


async def _loading(update: Update) -> Any:
    """Send a loading indicator."""
    return await update.message.reply_text("⏳ Processing...")


def _int(value: str, default: int = 0) -> int:
    """Safely convert to int."""
    try: return int(value)
    except (ValueError, TypeError): return default


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Global error handler."""
    logger.error(f"Exception: {context.error}", exc_info=context.error)
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("⚠️ An error occurred. Check bot logs.", parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
#  APPLICATION SETUP
# ═══════════════════════════════════════════════════════════════


def build_application() -> Application:
    """Build and configure the Telegram bot application."""
    app = Application.builder().token(Config.BOT_TOKEN).build()

    # ─── Slash Commands (Pretty Formatted) ───────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu_command))

    # System
    for cmd, handler in [("sys", sys_overview), ("cpu", sys_cpu), ("mem", sys_memory),
                          ("disk", sys_disk), ("netif", sys_network), ("df", sys_df)]:
        app.add_handler(CommandHandler(cmd, handler))

    # Processes
    for cmd, handler in [("ps", proc_list), ("psm", proc_list_mem), ("proc", proc_info),
                          ("find", proc_find), ("kill", proc_kill), ("killf", proc_kill_force)]:
        app.add_handler(CommandHandler(cmd, handler))

    # Services
    for cmd, handler in [("svc", svc_status), ("svcr", svc_restart), ("svcs", svc_stop),
                          ("svca", svc_start), ("svcl", svc_logs), ("svclist", svc_list)]:
        app.add_handler(CommandHandler(cmd, handler))

    # Filesystem
    for cmd, handler in [("ls", fs_list), ("cat", fs_read), ("finfo", fs_info),
                          ("rm", fs_remove), ("rmrf", fs_remove_recursive)]:
        app.add_handler(CommandHandler(cmd, handler))

    # Docker
    for cmd, handler in [("dps", dkr_ps), ("dpsa", dkr_ps_all), ("dimg", dkr_images),
                          ("dstats", dkr_stats), ("dlog", dkr_logs), ("dstart", dkr_start),
                          ("dstop", dkr_stop), ("drestart", dkr_restart), ("dexec", dkr_exec)]:
        app.add_handler(CommandHandler(cmd, handler))

    # Network
    for cmd, handler in [("ping", net_ping), ("trace", net_trace), ("dns", net_dns),
                          ("ports", net_ports), ("fw", net_fw), ("conn", net_conn), ("http", net_http)]:
        app.add_handler(CommandHandler(cmd, handler))

    # Power
    for cmd, handler in [("reboot", pwr_reboot), ("shutdown", pwr_shutdown), ("cancel", pwr_cancel),
                          ("cronl", pwr_cron_list), ("update", pwr_update), ("syslog", pwr_syslog)]:
        app.add_handler(CommandHandler(cmd, handler))

    # ─── Terminal-First Text Handler (DEFAULT MODE) ──────────
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, terminal_handler))

    # ─── Error Handler ───────────────────────────────────────
    app.add_error_handler(error_handler)

    return app


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Start the VPSPilot bot."""
    logger.info(f"🛩 {Config.PROJECT_NAME} v{Config.VERSION} starting (Hybrid Terminal-First)...")
    logger.info(f"📋 Authorized users: {Config.AUTHORIZED_USERS}")

    app = build_application()

    logger.info("✅ Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
