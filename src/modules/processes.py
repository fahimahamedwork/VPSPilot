"""
VPSPilot — Process Management Module
List, monitor, and manage running processes.
"""

import psutil

from core.executor import execute


async def list_processes(sort_by: str = "cpu", limit: int = 20) -> str:
    """
    List top processes sorted by CPU or memory usage.

    Args:
        sort_by: 'cpu' or 'memory'
        limit: Number of processes to show
    """
    processes = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort
    if sort_by == "memory":
        processes.sort(key=lambda p: p.get("memory_percent") or 0, reverse=True)
        sort_label = "Memory"
    else:
        processes.sort(key=lambda p: p.get("cpu_percent") or 0, reverse=True)
        sort_label = "CPU"

    lines = [
        f"⚙ *Top Processes (by {sort_label})*",
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        "```\n",
        f"{'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  {'STATUS':<8}  NAME\n",
        "─" * 55 + "\n",
    ]

    for proc in processes[:limit]:
        pid = proc.get("pid", "?")
        cpu = proc.get("cpu_percent", 0) or 0
        mem = proc.get("memory_percent", 0) or 0
        status = proc.get("status", "?") or "?"
        name = proc.get("name", "?") or "?"

        # Truncate long names
        if len(name) > 25:
            name = name[:22] + "..."

        lines.append(f"{pid:>7}  {cpu:>5.1f}%  {mem:>5.1f}%  {status:<8}  {name}\n")

    lines.append("```")
    return "".join(lines)


async def get_process_info(pid: int) -> str:
    """Get detailed information about a specific process."""
    try:
        proc = psutil.Process(pid)
        info = proc.as_dict([
            "pid", "name", "exe", "cmdline", "username", "status",
            "cpu_percent", "memory_percent", "create_time", "num_threads",
            "ppid",
        ])

        mem_info = proc.memory_info()
        mem_rss_mb = mem_info.rss / (1024 ** 2)
        mem_vms_mb = mem_info.vms / (1024 ** 2)

        cmdline = " ".join(info.get("cmdline") or []) or "N/A"
        if len(cmdline) > 200:
            cmdline = cmdline[:200] + "..."

        from datetime import datetime
        create_time = datetime.fromtimestamp(info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")

        return (
            f"🔍 *Process Detail*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"▸ PID: {info['pid']}\n"
            f"▸ Name: {info['name']}\n"
            f"▸ Parent PID: {info.get('ppid', 'N/A')}\n"
            f"▸ Status: {info['status']}\n"
            f"▸ User: {info.get('username', 'N/A')}\n"
            f"▸ CPU: {info.get('cpu_percent', 0):.1f}%\n"
            f"▸ Memory: {info.get('memory_percent', 0):.1f}%\n"
            f"▸ RSS: {mem_rss_mb:.1f}MB | VMS: {mem_vms_mb:.1f}MB\n"
            f"▸ Threads: {info.get('num_threads', 'N/A')}\n"
            f"▸ Started: {create_time}\n"
            f"▸ Executable: {info.get('exe', 'N/A')}\n"
            f"▸ Command: `{cmdline}`"
        )

    except psutil.NoSuchProcess:
        return f"❌ Process with PID {pid} not found."
    except psutil.AccessDenied:
        return f"🚫 Access denied for PID {pid}. Try running with higher privileges."


async def kill_process(pid: int, force: bool = False) -> str:
    """
    Kill a process by PID.

    Args:
        pid: Process ID to kill
        force: If True, use SIGKILL instead of SIGTERM
    """
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()

        if force:
            proc.kill()  # SIGKILL
            sig_name = "SIGKILL"
        else:
            proc.terminate()  # SIGTERM
            sig_name = "SIGTERM"

        return (
            f"✅ Process Terminated\n\n"
            f"▸ PID: {pid}\n"
            f"▸ Name: {proc_name}\n"
            f"▸ Signal: {sig_name}"
        )

    except psutil.NoSuchProcess:
        return f"❌ Process with PID {pid} not found."
    except psutil.AccessDenied:
        return f"🚫 Access denied for PID {pid}. Try running with higher privileges."


async def find_process(name: str) -> str:
    """Search for processes by name."""
    matches = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
        try:
            if name.lower() in (proc.info.get("name") or "").lower():
                matches.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not matches:
        return f"🔍 No processes found matching '{name}'."

    lines = [
        f"🔍 *Processes matching '{name}':*\n",
        "```\n",
        f"{'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  USER           NAME\n",
        "─" * 55 + "\n",
    ]

    for proc in matches[:20]:
        pid = proc.get("pid", "?")
        cpu = proc.get("cpu_percent", 0) or 0
        mem = proc.get("memory_percent", 0) or 0
        user = (proc.get("username") or "?")[:14]
        pname = proc.get("name", "?") or "?"
        lines.append(f"{pid:>7}  {cpu:>5.1f}%  {mem:>5.1f}%  {user:<14} {pname}\n")

    lines.append("```")
    return "".join(lines)
