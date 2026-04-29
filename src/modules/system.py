"""
VPSPilot — System Monitor Module
Provides real-time system metrics: CPU, RAM, Disk, Network, Uptime, OS info.
"""

import platform
import time
from datetime import timedelta

import psutil

from core.executor import execute


async def get_overview() -> str:
    """Return a comprehensive system overview with all key metrics."""
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_cores = psutil.cpu_count(logical=True)
    cpu_physical = psutil.cpu_count(logical=False)
    cpu_freq = psutil.cpu_freq()
    freq_str = f"{cpu_freq.current:.0f}MHz" if cpu_freq else "N/A"

    # Memory
    mem = psutil.virtual_memory()
    mem_total_gb = mem.total / (1024 ** 3)
    mem_used_gb = mem.used / (1024 ** 3)
    mem_avail_gb = mem.available / (1024 ** 3)

    # Swap
    swap = psutil.swap_memory()
    swap_total_gb = swap.total / (1024 ** 3)
    swap_used_gb = swap.used / (1024 ** 3)

    # Disk
    disk = psutil.disk_usage("/")
    disk_total_gb = disk.total / (1024 ** 3)
    disk_used_gb = disk.used / (1024 ** 3)
    disk_free_gb = disk.free / (1024 ** 3)

    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    uptime_str = str(timedelta(seconds=uptime_seconds))

    # Load average (Linux only)
    load_avg = "N/A"
    if hasattr(platform, "freedesktop_os_release") or platform.system() == "Linux":
        try:
            load1, load5, load15 = psutil.getloadavg()
            load_avg = f"{load1:.2f} / {load5:.2f} / {load15:.2f}"
        except (AttributeError, OSError):
            pass

    # Network IO
    net = psutil.net_io_counters()
    net_sent_mb = net.bytes_sent / (1024 ** 2)
    net_recv_mb = net.bytes_recv / (1024 ** 2)

    return (
        f"🖥 *System Overview*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *Host:* {platform.node()}\n"
        f"📌 *OS:* {platform.system()} {platform.release()}\n"
        f"📌 *Arch:* {platform.machine()}\n"
        f"📌 *Uptime:* {uptime_str}\n\n"
        f"🔧 *CPU*\n"
        f"  ▸ Usage: {cpu_percent}%\n"
        f"  ▸ Cores: {cpu_physical}P / {cpu_cores}L\n"
        f"  ▸ Frequency: {freq_str}\n"
        f"  ▸ Load: {load_avg}\n\n"
        f"💾 *Memory*\n"
        f"  ▸ Used: {mem_used_gb:.1f}GB / {mem_total_gb:.1f}GB ({mem.percent}%)\n"
        f"  ▸ Available: {mem_avail_gb:.1f}GB\n"
        f"  ▸ Swap: {swap_used_gb:.1f}GB / {swap_total_gb:.1f}GB ({swap.percent}%)\n\n"
        f"📁 *Disk (/)*\n"
        f"  ▸ Used: {disk_used_gb:.1f}GB / {disk_total_gb:.1f}GB ({disk.percent}%)\n"
        f"  ▸ Free: {disk_free_gb:.1f}GB\n\n"
        f"🌐 *Network (total)*\n"
        f"  ▸ Sent: {net_sent_mb:.1f}MB\n"
        f"  ▸ Received: {net_recv_mb:.1f}MB"
    )


async def get_cpu_detailed() -> str:
    """Return detailed CPU information with per-core usage."""
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    cpu_cores = len(cpu_percent)
    cpu_freq = psutil.cpu_freq()

    lines = ["🖥 *CPU Detailed*\n━━━━━━━━━━━━━━━━━━━━━━━━━\n"]
    lines.append(f"Total Usage: {sum(cpu_percent) / cpu_cores:.1f}%")
    if cpu_freq:
        lines.append(f"Frequency: {cpu_freq.current:.0f}MHz (Max: {cpu_freq.max:.0f}MHz)")

    lines.append(f"\n*Per-Core Usage:*")
    for i, pct in enumerate(cpu_percent):
        bar_len = 20
        filled = int(pct / 100 * bar_len)
        bar = "█" * filled + "░" * (bar_len - filled)
        lines.append(f"  Core {i}: [{bar}] {pct:.0f}%")

    return "\n".join(lines)


async def get_memory_detailed() -> str:
    """Return detailed memory and swap information."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    def _bar(percent: float, length: int = 20) -> str:
        filled = int(percent / 100 * length)
        return "█" * filled + "░" * (length - filled)

    mem_total_gb = mem.total / (1024 ** 3)
    mem_used_gb = mem.used / (1024 ** 3)
    mem_cached_gb = mem.cached / (1024 ** 3) if hasattr(mem, "cached") else 0
    swap_total_gb = swap.total / (1024 ** 3)
    swap_used_gb = swap.used / (1024 ** 3)

    return (
        f"💾 *Memory Detailed*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*RAM*\n"
        f"  [{_bar(mem.percent)}] {mem.percent}%\n"
        f"  ▸ Total: {mem_total_gb:.1f}GB\n"
        f"  ▸ Used: {mem_used_gb:.1f}GB\n"
        f"  ▸ Available: {mem.available / (1024**3):.1f}GB\n"
        f"  ▸ Cached: {mem_cached_gb:.1f}GB\n\n"
        f"*Swap*\n"
        f"  [{_bar(swap.percent)}] {swap.percent}%\n"
        f"  ▸ Total: {swap_total_gb:.1f}GB\n"
        f"  ▸ Used: {swap_used_gb:.1f}GB\n"
        f"  ▸ Free: {(swap.total - swap.used) / (1024**3):.1f}GB"
    )


async def get_disk_detailed() -> str:
    """Return detailed disk usage for all mounted partitions."""
    lines = ["📁 *Disk Partitions*", "━━━━━━━━━━━━━━━━━━━━━━━━━\n"]

    partitions = psutil.disk_partitions()
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)

            bar_len = 20
            filled = int(usage.percent / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)

            lines.append(
                f"*{part.mountpoint}* ({part.fstype})\n"
                f"  [{bar}] {usage.percent}%\n"
                f"  ▸ Used: {used_gb:.1f}GB / {total_gb:.1f}GB\n"
                f"  ▸ Free: {free_gb:.1f}GB\n"
                f"  ▸ Device: {part.device}\n"
            )
        except PermissionError:
            lines.append(f"*{part.mountpoint}* — Permission denied\n")

    return "\n".join(lines)


async def get_network_interfaces() -> str:
    """Return information about network interfaces."""
    lines = ["🌐 *Network Interfaces*", "━━━━━━━━━━━━━━━━━━━━━━━━━\n"]

    # IO counters
    net_io = psutil.net_io_counters(pernic=True)
    # Addresses
    net_addrs = psutil.net_if_addrs()
    # Stats
    net_stats = psutil.net_if_stats()

    for iface, addrs in net_addrs.items():
        stats = net_stats.get(iface)
        io = net_io.get(iface)

        status = "🟢 UP" if stats and stats.isup else "🔴 DOWN"
        lines.append(f"*{iface}* — {status}")

        for addr in addrs:
            if addr.family.name in ("AF_INET", "AF_INET6"):
                family = "IPv4" if addr.family.name == "AF_INET" else "IPv6"
                lines.append(f"  ▸ {family}: {addr.address}")

        if io:
            sent_mb = io.bytes_sent / (1024 ** 2)
            recv_mb = io.bytes_recv / (1024 ** 2)
            lines.append(f"  ▸ Sent: {sent_mb:.1f}MB | Recv: {recv_mb:.1f}MB")

        if stats:
            lines.append(f"  ▸ Speed: {stats.speed}Mbps")

        lines.append("")

    return "\n".join(lines)
