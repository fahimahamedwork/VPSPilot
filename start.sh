#!/bin/bash
# ─── VPSPilot Quick Start Script ─────────────────────────────
# Run this script to set up and start VPSPilot

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║          VPSPilot Setup              ║"
echo "  ║   Telegram VPS Control Bot v1.0.0    ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"

# Check Python version
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python $PY_VERSION found"
else
    echo -e "${RED}✗${NC} Python 3.10+ required. Install it first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}!${NC} No .env file found. Creating from template..."
    cp .env.example .env
    echo -e "${YELLOW}!${NC} Please edit .env with your bot token and user ID:"
    echo -e "    ${GREEN}nano .env${NC}"
    echo ""
    echo -e "  1. Get a bot token from ${GREEN}@BotFather${NC} on Telegram"
    echo -e "  2. Get your user ID from ${GREEN}@userinfobot${NC}"
    echo ""
    read -p "  Press Enter to open .env for editing (or Ctrl+C to exit)..."
    ${EDITOR:-nano} .env
fi

# Install dependencies
echo -e "${GREEN}→${NC} Installing Python dependencies..."
pip3 install -r requirements.txt

# Validate configuration
echo -e "${GREEN}→${NC} Validating configuration..."
python3 -c "from config import Config; Config.validate()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}✗${NC} Configuration validation failed. Check your .env file."
    exit 1
fi
echo -e "${GREEN}✓${NC} Configuration valid"

# Start the bot
echo -e "${GREEN}→${NC} Starting VPSPilot..."
python3 bot.py
