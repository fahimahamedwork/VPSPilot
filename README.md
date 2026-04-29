# VPSPilot 🛩

**Full-featured Telegram bot for remote VPS management.**

Control your entire server from Telegram — system monitoring, process management, service control, Docker, filesystem, networking, power operations, and an interactive shell. All secured by user ID authentication.

---

## ✨ Features

### 🖥 System Monitoring
- Real-time CPU, RAM, Disk, and Network metrics
- Per-core CPU usage with visual bars
- Memory and swap details with progress indicators
- Disk partitions and filesystem usage
- Network interface information and IO stats

### ⚙ Process Management
- Top processes sorted by CPU or memory
- Detailed process information by PID
- Search processes by name
- Kill processes (SIGTERM or SIGKILL)

### 🔧 Service Management
- Systemd service status, start, stop, restart
- List running, failed, enabled, or all services
- Service journal logs

### 📂 Filesystem Operations
- List directory contents with details
- Read text files
- File/directory info and permissions
- Delete files and directories
- Disk usage summary

### 🐳 Docker Management
- List running/all containers
- Container stats (CPU, Memory, Network, Block IO)
- Container logs, start, stop, restart
- Execute commands inside containers
- List Docker images

### 🌐 Network Tools
- Ping with configurable count
- Traceroute
- DNS lookup (A, AAAA, MX, NS, TXT records)
- Port scanning and listening ports
- Firewall status (UFW/iptables)
- Active connections
- HTTP response code and timing checks

### ⚡ Power & Admin
- Schedule system reboot/shutdown
- Cancel pending shutdown
- Cron job management (list, add, remove)
- System package updates
- System logs

### 🖥 Interactive Shell
- Execute arbitrary shell commands
- Dangerous command pattern blocking
- Output truncation for large results
- Configurable timeout

---

## 🚀 Quick Start

### Option 1: Direct Installation

```bash
# Clone or download the project
cd vpspilot

# Copy and edit configuration
cp .env.example .env
nano .env

# Install dependencies
pip3 install -r requirements.txt

# Start the bot
python3 bot.py
```

### Option 2: Using the Setup Script

```bash
cd vpspilot
chmod +x start.sh
./start.sh
```

### Option 3: Docker Deployment

```bash
cd vpspilot

# Copy and edit configuration
cp .env.example .env
nano .env

# Build and run
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

---

## ⚙️ Configuration

Edit the `.env` file with your settings:

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `AUTHORIZED_USERS` | ✅ | — | Comma-separated Telegram user IDs |
| `SHELL_TIMEOUT` | ❌ | 30 | Shell command timeout in seconds |
| `MAX_OUTPUT_LENGTH` | ❌ | 4000 | Maximum output characters |
| `LOG_LEVEL` | ❌ | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Getting Your Credentials

1. **Bot Token**: Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → Follow instructions → Copy the token
2. **Your User ID**: Message [@userinfobot](https://t.me/userinfobot) → It replies with your ID

---

## 📋 Command Reference

### System Monitoring
| Command | Description |
|---|---|
| `/sys` | Full system overview |
| `/cpu` | Detailed CPU info |
| `/mem` | Detailed memory info |
| `/disk` | Disk partition info |
| `/netif` | Network interfaces |
| `/df` | Disk usage summary |

### Process Management
| Command | Description |
|---|---|
| `/ps` | Top processes by CPU |
| `/psm` | Top processes by memory |
| `/proc <pid>` | Process details |
| `/find <name>` | Find process by name |
| `/kill <pid>` | Kill process (SIGTERM) |
| `/killf <pid>` | Force kill (SIGKILL) |

### Service Management
| Command | Description |
|---|---|
| `/svc <name>` | Service status |
| `/svcr <name>` | Restart service |
| `/svcs <name>` | Stop service |
| `/svca <name>` | Start service |
| `/svcl <name>` | Service logs |
| `/svclist [state]` | List services (running/failed/all) |

### Filesystem
| Command | Description |
|---|---|
| `/ls [path]` | List directory |
| `/cat <path>` | Read file |
| `/finfo <path>` | File/directory info |
| `/rm <path>` | Delete file |
| `/rmrf <path>` | Delete directory |

### Docker
| Command | Description |
|---|---|
| `/dps` | Running containers |
| `/dpsa` | All containers |
| `/dimg` | Docker images |
| `/dstats` | Container stats |
| `/dlog <container>` | Container logs |
| `/dstart <container>` | Start container |
| `/dstop <container>` | Stop container |
| `/drestart <container>` | Restart container |
| `/dexec <container> <cmd>` | Exec in container |

### Network
| Command | Description |
|---|---|
| `/ping <host>` | Ping host |
| `/trace <host>` | Traceroute |
| `/dns <domain> [type]` | DNS lookup |
| `/ports [target]` | Check ports |
| `/fw` | Firewall status |
| `/conn` | Active connections |
| `/http <url>` | HTTP check |

### Power & Admin
| Command | Description |
|---|---|
| `/reboot [min]` | Schedule reboot |
| `/shutdown [min]` | Schedule shutdown |
| `/cancel` | Cancel shutdown/reboot |
| `/cronl` | List cron jobs |
| `/update` | System update |
| `/syslog [service]` | System logs |

### Shell
| Command | Description |
|---|---|
| `/shell <command>` | Execute shell command |

---

## 🏗 Project Structure

```
vpspilot/
├── bot.py              # Main entry point & command handlers
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── Dockerfile          # Docker build file
├── docker-compose.yml  # Docker Compose deployment
├── start.sh            # Quick start script
├── core/               # Core infrastructure
│   ├── auth.py         # Authentication decorator
│   ├── executor.py     # Shell command executor
│   └── router.py       # Command registry
├── modules/            # Feature modules
│   ├── system.py       # System monitoring
│   ├── processes.py    # Process management
│   ├── services.py     # Service management
│   ├── filesystem.py   # File operations
│   ├── docker_m.py     # Docker management
│   ├── network.py      # Network tools
│   └── power.py        # Power control & cron
├── ui/                 # User interface
│   ├── keyboards.py    # Inline & reply keyboards
│   └── formatters.py   # Output formatting
└── utils/              # Utilities
    └── helpers.py      # Shared helper functions
```

---

## 🔒 Security

- **Authentication**: Only whitelisted Telegram user IDs can interact with the bot
- **Command Validation**: Dangerous shell patterns (fork bombs, recursive root deletes, device writes) are blocked
- **Path Sanitization**: Directory traversal attacks (`..`) are prevented
- **Output Truncation**: Large outputs are truncated to prevent Telegram API errors
- **Timeout Protection**: Shell commands have configurable timeouts

### ⚠️ Important Security Notes

1. **Run as root** for full VPS control (systemctl, docker, iptables, etc.)
2. **Keep your .env secure** — never commit it to version control
3. **Limit authorized users** to only your own Telegram ID
4. **Review blocked patterns** in `utils/__init__.py` and add your own
5. **Use HTTPS** when connecting to external services

---

## 🛠 Requirements

- Python 3.10+
- Linux-based VPS (Ubuntu, Debian, CentOS, Arch)
- Telegram Bot Token
- System dependencies (auto-detected): `systemctl`, `docker`, `uff`, `iptables`, `traceroute`, `dig`

---

## 📄 License

MIT License — Use freely, modify as needed, no warranties.
