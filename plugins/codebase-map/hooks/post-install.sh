#!/usr/bin/env bash
# HC-AI | ticket: FDD-TOOL-CODEMAP
# Post-install hook for codebase-map Claude plugin.
# Installs codebase-map[mcp] via pipx (S2 v2.4.0 tested path).

set -euo pipefail

echo "[codebase-map plugin] Installing CLI + MCP server..."

# 1. Ensure pipx is available
if ! command -v pipx > /dev/null 2>&1; then
    echo "[codebase-map plugin] pipx not found. Installing via pip..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    # Re-source PATH so pipx is visible in this shell
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Install or upgrade codebase-map with MCP extra
# This is the exact command verified in S2 PR #131 on macOS + Python 3.14.3
if pipx list 2>/dev/null | grep -q 'codebase-map'; then
    echo "[codebase-map plugin] Upgrading existing install..."
    pipx upgrade 'codebase-map' --pip-args='-U' || pipx install --force 'codebase-map[mcp]>=2.4.0'
else
    echo "[codebase-map plugin] Fresh install..."
    pipx install 'codebase-map[mcp]>=2.4.0'
fi

# 3. Verify entry points
if ! command -v codebase-map > /dev/null 2>&1; then
    echo "[codebase-map plugin] ERROR: codebase-map CLI not on PATH after install."
    echo "[codebase-map plugin] Check: run 'pipx ensurepath' then restart shell."
    exit 1
fi

if ! command -v cbm-mcp > /dev/null 2>&1; then
    echo "[codebase-map plugin] WARNING: cbm-mcp entry not on PATH (MCP server may not work)."
fi

echo "[codebase-map plugin] ✅ Installed successfully."
echo "[codebase-map plugin]    codebase-map $(codebase-map --version 2>&1 | awk '{print $2}')"
echo "[codebase-map plugin]    cbm-mcp: $(which cbm-mcp 2>&1 || echo 'not found')"
echo ""
echo "[codebase-map plugin] Try: /cbm-onboard"
