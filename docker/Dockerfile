# ─── VPSPilot Dockerfile ─────────────────────────────────────
# Multi-stage build for a lean production image
# Build context: project root (docker compose runs from project root)

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

LABEL maintainer="VPSPilot"
LABEL description="Telegram bot for full VPS control"
LABEL version="1.0.0"

# Install system dependencies for VPS management
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dnsutils \
    iproute2 \
    iptables \
    procps \
    traceroute \
    ufw \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Create non-root user (optional — some commands need root)
RUN groupadd -r vpspilot && useradd -r -g vpspilot -m vpspilot

WORKDIR /app

# Copy application source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run as root for full VPS access (required for systemctl, docker, etc.)
# USER vpspilot

ENTRYPOINT ["python", "src/bot.py"]
