"""
VPSPilot — Keyboard Builders
Interactive inline and reply keyboards for the Telegram bot UI.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


# ─── Main Menu Keyboard ──────────────────────────────────────

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the main navigation reply keyboard."""
    buttons = [
        [KeyboardButton("🖥 System"), KeyboardButton("⚙ Processes")],
        [KeyboardButton("🔧 Services"), KeyboardButton("📂 Files")],
        [KeyboardButton("🐳 Docker"), KeyboardButton("🌐 Network")],
        [KeyboardButton("⚡ Power"), KeyboardButton("🖥 Shell")],
        [KeyboardButton("❓ Help")],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=False)


# ─── System Submenu ──────────────────────────────────────────

def system_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for system monitoring actions."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Overview", callback_data="sys_overview"),
            InlineKeyboardButton("🖥 CPU", callback_data="sys_cpu"),
        ],
        [
            InlineKeyboardButton("💾 Memory", callback_data="sys_memory"),
            InlineKeyboardButton("📁 Disk", callback_data="sys_disk"),
        ],
        [
            InlineKeyboardButton("🌐 Interfaces", callback_data="sys_network"),
            InlineKeyboardButton("📦 Disk Usage", callback_data="sys_df"),
        ],
        [
            InlineKeyboardButton("◀ Back", callback_data="menu_back"),
        ],
    ])


# ─── Process Submenu ─────────────────────────────────────────

def processes_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for process management."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Top CPU", callback_data="proc_top_cpu"),
            InlineKeyboardButton("📊 Top Memory", callback_data="proc_top_mem"),
        ],
        [
            InlineKeyboardButton("🔍 Search Process", callback_data="proc_search"),
            InlineKeyboardButton("ℹ️ Process Info", callback_data="proc_info"),
        ],
        [
            InlineKeyboardButton("💀 Kill Process", callback_data="proc_kill"),
        ],
        [
            InlineKeyboardButton("◀ Back", callback_data="menu_back"),
        ],
    ])


# ─── Service Submenu ─────────────────────────────────────────

def services_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for service management."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Running Services", callback_data="svc_running"),
            InlineKeyboardButton("❌ Failed Services", callback_data="svc_failed"),
        ],
        [
            InlineKeyboardButton("🔍 Service Status", callback_data="svc_status"),
            InlineKeyboardButton("▶️ Start", callback_data="svc_start"),
        ],
        [
            InlineKeyboardButton("⏹ Stop", callback_data="svc_stop"),
            InlineKeyboardButton("🔄 Restart", callback_data="svc_restart"),
        ],
        [
            InlineKeyboardButton("📜 Service Logs", callback_data="svc_logs"),
        ],
        [
            InlineKeyboardButton("◀ Back", callback_data="menu_back"),
        ],
    ])


# ─── Files Submenu ───────────────────────────────────────────

def files_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for filesystem operations."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📂 List Dir", callback_data="fs_list"),
            InlineKeyboardButton("📄 Read File", callback_data="fs_read"),
        ],
        [
            InlineKeyboardButton("ℹ️ File Info", callback_data="fs_info"),
            InlineKeyboardButton("💾 Disk Usage", callback_data="fs_df"),
        ],
        [
            InlineKeyboardButton("🗑 Delete", callback_data="fs_delete"),
        ],
        [
            InlineKeyboardButton("◀ Back", callback_data="menu_back"),
        ],
    ])


# ─── Docker Submenu ──────────────────────────────────────────

def docker_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for Docker management."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Containers", callback_data="dkr_ps"),
            InlineKeyboardButton("📦 All Containers", callback_data="dkr_ps_all"),
        ],
        [
            InlineKeyboardButton("🖼 Images", callback_data="dkr_images"),
            InlineKeyboardButton("📊 Stats", callback_data="dkr_stats"),
        ],
        [
            InlineKeyboardButton("📜 Container Logs", callback_data="dkr_logs"),
            InlineKeyboardButton("💻 Exec", callback_data="dkr_exec"),
        ],
        [
            InlineKeyboardButton("▶️ Start", callback_data="dkr_start"),
            InlineKeyboardButton("⏹ Stop", callback_data="dkr_stop"),
            InlineKeyboardButton("🔄 Restart", callback_data="dkr_restart"),
        ],
        [
            InlineKeyboardButton("◀ Back", callback_data="menu_back"),
        ],
    ])


# ─── Network Submenu ─────────────────────────────────────────

def network_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for network diagnostics."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏓 Ping", callback_data="net_ping"),
            InlineKeyboardButton("🗺 Traceroute", callback_data="net_trace"),
        ],
        [
            InlineKeyboardButton("🌐 DNS Lookup", callback_data="net_dns"),
            InlineKeyboardButton("🔌 Ports", callback_data="net_ports"),
        ],
        [
            InlineKeyboardButton("🛡 Firewall", callback_data="net_fw"),
            InlineKeyboardButton("🔗 Connections", callback_data="net_conn"),
        ],
        [
            InlineKeyboardButton("🌐 HTTP Check", callback_data="net_http"),
        ],
        [
            InlineKeyboardButton("◀ Back", callback_data="menu_back"),
        ],
    ])


# ─── Power Submenu ───────────────────────────────────────────

def power_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for power and cron controls."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Reboot", callback_data="pwr_reboot"),
            InlineKeyboardButton("⏹ Shutdown", callback_data="pwr_shutdown"),
        ],
        [
            InlineKeyboardButton("❌ Cancel Shutdown", callback_data="pwr_cancel"),
        ],
        [
            InlineKeyboardButton("📋 Cron Jobs", callback_data="pwr_cron_list"),
            InlineKeyboardButton("➕ Add Cron", callback_data="pwr_cron_add"),
        ],
        [
            InlineKeyboardButton("📦 System Update", callback_data="pwr_update"),
            InlineKeyboardButton("📜 System Logs", callback_data="pwr_logs"),
        ],
        [
            InlineKeyboardButton("◀ Back", callback_data="menu_back"),
        ],
    ])
