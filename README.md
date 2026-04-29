# VPSPilot 🛩

**Terminal-first Telegram bot for remote VPS management.**

Three modes in one bot — type commands like SSH, get pretty formatted output with /commands, or tap buttons in the menu. Your VPS, your way.

---

## 🎯 Three Modes

| Mode | How | Example |
|---|---|---|
| 🖥 **Terminal** | Just type — default mode | `ls /var/log`, `restart nginx`, `docker ps` |
| 📊 **Pretty** | /slash commands for formatted output | `/sys`, `/cpu`, `/mem` |
| 🎛 **Menu** | Tap keyboard buttons | `/menu` → tap categories |

---

## ✨ Features

### 🖥 Terminal Mode (Default)
Just type naturally — the smart interpreter handles it:
- `ls /var/log` → list directory
- `cat /etc/hosts` → read file
- `restart nginx` → systemctl restart
- `status docker` → systemctl status
- `logs ssh` → journal logs
- `docker ps` → running containers
- `docker logs web` → container logs
- `docker restart web` → restart container
- `kill 1234` → kill process
- `kill -9 1234` → force kill
- `find nginx` → search processes
- `ping google.com` → ping host
- `dns google.com` → DNS lookup
- `firewall` → UFW status
- `reboot` or `reboot 5` → schedule reboot
- `shutdown` or `shutdown now` → schedule shutdown
- `update` → system update
- `cron list` → list cron jobs
- `top` → top processes
- `df` → disk usage
- `uptime` → system overview
- `conn` → active connections
- `ports` → listening ports
- Anything else → executed as shell command

### 📊 Pretty Mode (/Commands)
Formatted output with progress bars and visual indicators:
- `/sys` — Full system overview with bars
- `/cpu` — Per-core CPU usage
- `/mem` — Memory with progress indicators
- `/disk` — All disk partitions
- `/ps` — Top processes by CPU
- `/svc <name>` — Service status
- `/dps` — Docker containers
- `/fw` — Firewall status
- And 30+ more...

### 🎛 Menu Mode
Interactive keyboard for guided actions:
- `/menu` → Open category keyboard
- Tap System → Overview, CPU, Memory, Disk
- Tap Docker → Containers, Images, Stats, Logs
- Tap any category to explore

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
python3 src/bot.py
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

# Build and run (from project root)
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop
docker compose -f docker/docker-compose.yml down
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

## 📋 Terminal Quick Reference

Just type these — no /prefix needed:

| What you type | What happens |
|---|---|
| `top` | Top processes by CPU |
| `psm` | Top processes by memory |
| `find nginx` | Search processes |
| `kill 1234` | Kill process |
| `kill -9 1234` | Force kill |
| `restart nginx` | systemctl restart nginx |
| `status docker` | systemctl status docker |
| `logs ssh` | journalctl -u ssh |
| `ls /var/log` | List directory |
| `cat /etc/hosts` | Read file |
| `df` | Disk usage |
| `docker ps` | Running containers |
| `docker logs web` | Container logs |
| `docker restart web` | Restart container |
| `dimg` | Docker images |
| `ping google.com` | Ping host |
| `trace google.com` | Traceroute |
| `dns google.com` | DNS lookup |
| `firewall` | UFW status |
| `conn` | Active connections |
| `ports` | Listening ports |
| `reboot` | Schedule reboot |
| `shutdown now` | Shutdown immediately |
| `update` | System update |
| `cron list` | List cron jobs |
| `sys`, `cpu`, `mem` | System monitoring |
| `uptime` | System overview |
| Anything else | Executed as shell command |

## 📋 /Command Reference (Pretty Formatted)

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

---

## 🏗 Project Structure

```
vpspilot/
├── src/                    # Application source code
│   ├── bot.py              # Main entry point (hybrid terminal-first)
│   ├── config.py           # Configuration management
│   ├── core/               # Core infrastructure
│   │   ├── auth.py         # Authentication decorator
│   │   ├── executor.py     # Shell command executor
│   │   └── interpreter.py  # Smart command interpreter (brain)
│   ├── modules/            # Feature modules
│   │   ├── system.py       # System monitoring
│   │   ├── processes.py    # Process management
│   │   ├── services.py     # Service management
│   │   ├── filesystem.py   # File operations
│   │   ├── docker_m.py     # Docker management
│   │   ├── network.py      # Network tools
│   │   └── power.py        # Power control & cron
│   ├── ui/                 # User interface
│   │   ├── keyboards.py    # Inline & reply keyboards
│   │   └── formatters.py   # Output formatting
│   └── utils/              # Utilities
│       └── __init__.py    # Shared helper functions
├── docker/                 # Docker deployment files
│   ├── Dockerfile          # Multi-stage Docker build
│   └── docker-compose.yml  # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore              # Git ignore rules
├── start.sh                # Quick start script
└── README.md               # This file
```

---

## 🔒 Security

- **Authentication**: Only whitelisted Telegram user IDs can interact with the bot
- **Smart Interpreter**: Natural commands are parsed and routed safely
- **Command Validation**: Dangerous shell patterns (fork bombs, recursive root deletes, device writes) are blocked
- **Path Sanitization**: Directory traversal attacks (`..`) are prevented
- **Output Truncation**: Large outputs are truncated to prevent Telegram API errors
- **Timeout Protection**: Shell commands have configurable timeouts

### ⚠️ Important Security Notes

1. **Run as root** for full VPS control (systemctl, docker, iptables, etc.)
2. **Keep your .env secure** — never commit it to version control
3. **Limit authorized users** to only your own Telegram ID
4. **Review blocked patterns** in `src/utils/__init__.py` and add your own
5. **Use HTTPS** when connecting to external services

---

## 🛠 Requirements

- Python 3.10+
- Linux-based VPS (Ubuntu, Debian, CentOS, Arch)
- Telegram Bot Token
- System dependencies (auto-detected): `systemctl`, `docker`, `ufw`, `iptables`, `traceroute`, `dig`

---

## 📄 License

MIT License — Use freely, modify as needed, no warranties.
