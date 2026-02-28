#!/usr/bin/env bash
# First-time Raspberry Pi setup for Emiglio Robot.
#
# Usage:
#   curl -sSL <this-script-url> | bash
#   # or after cloning the repo:
#   bash deploy/setup-pi.sh
#
# Assumes: Raspberry Pi OS (bookworm), user "pi", network connected.

set -euo pipefail

echo "=== Emiglio Pi Setup ==="

# System packages
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3 python3-dev \
    libportaudio2 portaudio19-dev \
    libopencv-dev \
    git

# Install uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clone repo if not already present
REPO_DIR="$HOME/emiglio-robot"
if [ ! -d "$REPO_DIR" ]; then
    echo "Cloning repository..."
    echo "Please clone the repo to $REPO_DIR manually or set up your git remote."
    echo "  git clone <your-repo-url> $REPO_DIR"
else
    echo "Repository found at $REPO_DIR"
fi

# Install Python dependencies
if [ -d "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    echo "Installing Python dependencies..."
    uv sync

    # Test that it starts
    echo "Testing Emiglio in mock mode..."
    timeout 5 uv run python -m emiglio 2>&1 || true
    echo ""
fi

# Install systemd service
echo "Installing systemd service..."
sudo cp "$REPO_DIR/deploy/emiglio.service" /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Before starting, edit the service file to set your server URLs:"
echo "  sudo systemctl edit emiglio"
echo ""
echo "Then enable and start:"
echo "  sudo systemctl enable emiglio"
echo "  sudo systemctl start emiglio"
echo ""
echo "View logs:"
echo "  journalctl -u emiglio -f"
echo ""
echo "Quick test (mock mode):"
echo "  cd $REPO_DIR && uv run python -m emiglio"
